#!/usr/bin/env python3
"""Rebuild + validate the whole library in parallel, skipping components whose sources haven't changed.

    build_all.py [-j N] [--force] [--only NAME ...] [--prefix final]

- Starts N private scratch TouchDesigner instances (<prefix>_1..N, via tdctl) and stops them at the end.
- Phase 1 builds + conforms + validates every component in parallel; phase 2 builds + validates every
  snippet (snippets load other components' tox files, e.g. SDF chains, so they run after phase 1).
- A component is skipped when the hash of its inputs (component folder, snippet source, and the shared
  tooling that shapes the result) matches validation/final/<NAME>.hash from its last passing build and
  both shipped files exist. --force rebuilds everything.
Exit status 1 if anything failed. Summary lines: PASS / SKIP / FAIL.
"""
import argparse, hashlib, json, os, queue, subprocess, sys, threading, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
PY = os.environ.get("PY") or str(Path(os.environ.get("TD_MCP_HOME", Path.home() / "software/td-mcp")) / ".venv/bin/python")

# shared inputs that change every component's output when they change
SHARED = ["tools/conform.py", "tools/conv_check_td.py", "tools/validate.py", "tools/validate_snippet.py",
          "tools/tdwait.py", "snippets/src/_snip.py", "td_organize/td_runtime.py", "io_labels.json", "components.json",
          "tools/fixtures"]


def files_under(p):
    p = ROOT / p
    if p.is_file():
        return [p]
    return sorted(x for x in p.rglob("*") if x.is_file() and "__pycache__" not in x.parts)


def source_hash(name):
    h = hashlib.sha256()
    paths = files_under(f"components/{name}")
    snip = ROOT / "snippets" / "src" / f"{name}.py"
    if snip.exists():
        paths.append(snip)
    for s in SHARED:
        if (ROOT / s).exists():
            paths += files_under(s)
    # shared component helpers (components/_*) a build may read at build time
    for d in sorted((ROOT / "components").glob("_*")):
        paths += files_under(d.relative_to(ROOT))
    for p in paths:
        h.update(str(p.relative_to(ROOT)).encode()); h.update(b"\0"); h.update(p.read_bytes())
    return h.hexdigest()


def shipped(name):
    fam = name.split("_")[0]
    return (ROOT / "tox" / fam / f"{name}.tox").exists() and (ROOT / "snippets" / f"{name}.tox").exists()


def run(cmd, timeout):
    try:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr)
    except subprocess.TimeoutExpired as e:
        return 124, f"TIMEOUT after {timeout}s\n" + (e.stdout or "")


def tail(s, n=6):
    return " ".join(s.strip().splitlines()[-n:])[:600]


def component_job(inst, name):
    rc, out = run([PY, str(TOOLS / "tdctl.py"), "exec", inst, f"components/{name}/build.py", "120"], 300)
    if rc != 0 or '"ok": true' not in out:
        return False, "build.py: " + tail(out)
    if not (ROOT / "tox" / "_raw" / f"{name}.tox").exists():
        return False, f"build.py must save tox/_raw/{name}.tox"
    rc, out = run([PY, str(TOOLS / "conform.py"), inst, name], 300)
    if rc != 0:
        return False, "conform: " + tail(out)
    rc, out = run([PY, str(TOOLS / "validate.py"), inst, name], 300)
    (ROOT / "validation" / "final" / f"{name}.json").write_text(out)
    if rc != 0:
        return False, "validate: " + tail(out, 12)
    return True, ""


def snippet_job(inst, name):
    if not (ROOT / "snippets" / "src" / f"{name}.py").exists():
        return False, "no snippet source"
    rc, out = run([PY, str(TOOLS / "tdctl.py"), "exec", inst, f"snippets/src/{name}.py", "120"], 300)
    if rc != 0 or '"ok": true' not in out:
        return False, "snippet build: " + tail(out)
    rc, out = run([PY, str(TOOLS / "validate_snippet.py"), inst, name], 300)
    (ROOT / "validation" / "final" / f"{name}_snippet.json").write_text(out)
    if rc != 0:
        return False, "snippet validate: " + tail(out, 12)
    return True, ""


def alive(inst):
    """True if the scratch instance answers td_status (cheap)."""
    try:
        sys.path.insert(0, str(TOOLS))
        import tdctl  # noqa
        from td_mcp.client import call, load_connection
        r = call("td_status", connection=load_connection(tdctl.d(inst) / "connection.json"), timeout=10)
        return "error" not in r
    except Exception:
        return False


def ensure(inst):
    """Make sure `inst` is up; (re)start it if not. Returns False if it can't be brought up."""
    if alive(inst):
        return True
    run([PY, str(TOOLS / "tdctl.py"), "stop", inst], 60)
    rc, out = run([PY, str(TOOLS / "tdctl.py"), "start", inst], 200)
    return rc == 0 and alive(inst)


def pool(insts, names, job, label, results, lock):
    q = queue.Queue()
    for n in names:
        q.put(n)

    def worker(inst):
        while True:
            try:
                n = q.get_nowait()
            except queue.Empty:
                return
            if not ensure(inst):
                # this instance is dead and won't restart: hand the job back and retire the worker
                q.put(n)
                with lock:
                    print(f"WARN {inst} unavailable, worker retired", flush=True)
                return
            t0 = time.time()
            ok, msg = job(inst, n)
            if not ok and not alive(inst):
                # the instance died during the job: restart and retry once
                if ensure(inst):
                    ok, msg = job(inst, n)
            with lock:
                results.setdefault(n, []).append((label, ok, msg))
                print(f"{'ok  ' if ok else 'FAIL'} {label:9s} {n:28s} {time.time() - t0:5.1f}s [{inst}]" + ("" if ok else "  " + msg), flush=True)

    ts = [threading.Thread(target=worker, args=(i,)) for i in insts]
    for t in ts:
        t.start()
    for t in ts:
        t.join()
    # anything left (all workers retired) is reported as not run
    while not q.empty():
        n = q.get_nowait()
        results.setdefault(n, []).append((label, False, "not run: no TouchDesigner instance available"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-j", type=int, default=max(1, min(6, (os.cpu_count() or 4) // 2)))
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--only", nargs="*")
    ap.add_argument("--prefix", default="ball")
    a = ap.parse_args()

    names = subprocess.run([sys.executable, str(TOOLS / "list_components.py")], cwd=ROOT, capture_output=True, text=True).stdout.split()
    if a.only:
        names = [n for n in names if n in a.only]
    (ROOT / "validation" / "final").mkdir(parents=True, exist_ok=True)
    (ROOT / "tox" / "_raw").mkdir(parents=True, exist_ok=True)

    todo, skipped, hashes = [], [], {}
    for n in names:
        hashes[n] = source_hash(n)
        hf = ROOT / "validation" / "final" / f"{n}.hash"
        if not a.force and shipped(n) and hf.exists() and hf.read_text().strip() == hashes[n]:
            skipped.append(n)
        else:
            todo.append(n)
    for n in skipped:
        print(f"SKIP {n} (unchanged)")
    if not todo:
        print(f"TOTAL pass=0 skip={len(skipped)} fail=0"); return 0

    j = max(1, min(a.j, len(todo)))
    insts = [f"{a.prefix}_{i + 1}" for i in range(j)]
    t0 = time.time()
    starters = [subprocess.Popen([PY, str(TOOLS / "tdctl.py"), "start", i], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT) for i in insts]
    for s in starters:
        s.wait()
    print(f"started {j} TouchDesigner instance(s) in {time.time() - t0:.0f}s", flush=True)

    results, lock = {}, threading.Lock()
    try:
        pool(insts, todo, component_job, "component", results, lock)
        ok_components = [n for n in todo if results[n][-1][1]]
        pool(insts, ok_components, snippet_job, "snippet", results, lock)
    finally:
        for i in insts:
            subprocess.run([PY, str(TOOLS / "tdctl.py"), "stop", i], cwd=ROOT, capture_output=True)

    passed = [n for n in todo if len(results.get(n, [])) == 2 and all(r[1] for r in results[n])]
    for n in passed:
        (ROOT / "validation" / "final" / f"{n}.hash").write_text(hashes[n])
    failed = [n for n in todo if n not in passed]
    for n in passed:
        print(f"PASS {n}")
    for n in failed:
        print(f"FAIL {n} :: " + "; ".join(f"{lbl}: {m}" for lbl, ok, m in results.get(n, []) if not ok))
    print(f"TOTAL pass={len(passed)} skip={len(skipped)} fail={len(failed)}  ({time.time() - t0:.0f}s, -j {j})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
