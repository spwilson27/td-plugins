#!/usr/bin/env python3
"""bench.py <inst> <NAME> [--tox path] [--frames 120] [--out file.json] [--against old.tox] [--repeats 3]

Preferred for native-vs-GLSL decisions:  bench.py <inst> <NAME> --against <old GLSL tox>
  runs old and new alternately (A,B,A,B,...) on the same instance and compares medians, so system
  load hits both equally (single runs vary by up to ~25 % at 1080p). Exit 1 if the new version's
  median GPU cost is more than 20 % above the old one at either resolution.

GPU/CPU cost of a component under a standard load, for "native nodes vs GLSL" decisions.
- Loads the tox (default tox/<FAMILY>/<NAME>.tox) into /bench, connects standard inputs
  (TOP: animated noise at 1280x720 and again at 1920x1080; POP: 200x200 grid; CHOP: band1..4/beat),
  pulls the outputs every frame (frame-end Execute DAT) and accumulates the summed gpuCookTime and
  cookTime (CPU) of every op inside the component.
- Saves one PNG per resolution (validation/bench/<NAME>_<res>[_<tag>].png) for a side-by-side look.
- --compare prints the % change against a previous run and exits 1 if GPU cost rose by more than 20 %.
"""
import argparse, json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tdctl  # noqa
from tdwait import wait_frames
from td_mcp.client import call, load_connection

ROOT = Path(__file__).resolve().parent.parent


def run(conn, code):
    r = call("execute_python", {"code": code}, connection=conn, timeout=90)
    if not r.get("ok"):
        raise SystemExit("TD error: " + str(r.get("traceback") or r.get("error"))[-1500:])
    return r["stdout"].strip().splitlines()[-1] if r["stdout"].strip() else ""


SETUP = r'''
import td, json
b = op('/bench') or op('/').create(td.baseCOMP, 'bench')
for ch in list(b.children): ch.destroy()
c = b.loadTox(TOX); c.name = 'c'
ins = sorted([o for o in c.children if o.OPType in ('inTOP','inPOP','inCHOP','inSOP')], key=lambda o: o.name)
for i, o in enumerate(ins):
    t = o.OPType
    if t == 'inTOP':
        s = b.create(td.noiseTOP, 'src%d' % i); s.par.outputresolution = 'custom'
        s.par.resolutionw.expr = "parent().fetch('resw', 1280)"; s.par.resolutionh.expr = "parent().fetch('resh', 720)"
        s.par.tz.expr = 'absTime.seconds * 0.3'; s.par.mono = False
    elif t == 'inPOP':
        s = b.create(td.gridPOP, 'src%d' % i)
        for pn, v in (('rows', 200), ('cols', 200)):
            if hasattr(s.par, pn): setattr(s.par, pn, v)
    elif t == 'inSOP':
        s = b.create(td.gridSOP, 'src%d' % i); s.par.rows = 200; s.par.cols = 200
    else:
        s = b.create(td.constantCHOP, 'src%d' % i)
        for k, ch in enumerate(('band1', 'band2', 'band3', 'band4', 'beat')):
            getattr(s.par, 'name%d' % k).val = ch; getattr(s.par, 'value%d' % k).val = 0.5
    c.inputConnectors[i].connect(s)
d = b.create(td.executeDAT, 'acc')
d.text = """def onFrameEnd(frame):
    b = op('/bench'); c = b.op('c')
    for o in c.findChildren(depth=1):
        if o.name.startswith('out') or o.name == 'preview':
            try: o.cook(force=True)
            except Exception: pass
    if not b.fetch('on', False): return
    # count only ops that actually cooked this frame (a static op keeps its last, often first-cook, time)
    last = b.fetch('cooks', {})
    g = p = 0.0
    for o in c.findChildren():
        tc = o.totalCooks
        if last.get(o.path) != tc:
            g += getattr(o, 'gpuCookTime', 0) or 0
            p += getattr(o, 'cookTime', 0) or 0
            last[o.path] = tc
    b.store('cooks', last)
    b.store('g', b.fetch('g', 0.0) + g); b.store('p', b.fetch('p', 0.0) + p); b.store('n', b.fetch('n', 0) + 1)
    return
"""
d.par.frameend = 1; d.par.active = 1
print(json.dumps([o.OPType for o in ins]))
'''


def measure(conn, frames, resw, resh):
    run(conn, f"b = op('/bench'); b.store('resw', {resw}); b.store('resh', {resh}); b.store('on', False)")
    wait_frames(conn, 30)   # settle / compile at this resolution
    run(conn, "b = op('/bench'); b.store('g', 0.0); b.store('p', 0.0); b.store('n', 0); b.store('on', True)")
    wait_frames(conn, frames)
    out = run(conn, "import json\nb = op('/bench'); b.store('on', False)\nprint(json.dumps([b.fetch('g'), b.fetch('p'), b.fetch('n')]))")
    g, p, n = json.loads(out)
    return dict(gpu_ms=round(g / max(n, 1), 4), cpu_ms=round(p / max(n, 1), 4), frames=n)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inst"); ap.add_argument("name")
    ap.add_argument("--tox"); ap.add_argument("--frames", type=int, default=120)
    ap.add_argument("--out"); ap.add_argument("--compare"); ap.add_argument("--tag", default="")
    ap.add_argument("--against", help="old tox to compare against, run interleaved"); ap.add_argument("--repeats", type=int, default=5)
    a = ap.parse_args()
    conn = load_connection(tdctl.d(a.inst) / "connection.json")
    fam = a.name.split("_")[0]
    tox = Path(a.tox).resolve() if a.tox else ROOT / "tox" / fam / f"{a.name}.tox"
    if a.against:
        return interleaved(conn, a, Path(a.against).resolve(), tox.resolve())
    ins = json.loads(run(conn, f"TOX = {str(tox)!r}\n" + SETUP))
    outdir = ROOT / "validation" / "bench"; outdir.mkdir(parents=True, exist_ok=True)
    res = {}
    for (w, h) in ((1280, 720), (1920, 1080)):
        key = f"{w}x{h}"
        res[key] = measure(conn, a.frames, w, h)
        png = outdir / f"{a.name}_{key}{('_' + a.tag) if a.tag else ''}.png"
        run(conn, f"""c = op('/bench/c')
o = c.op('preview') if (c.op('preview') is not None and c.op('preview').isTOP) else c.op('out1')
if o is not None and o.isTOP: o.save({str(png)!r})
print('ok')""")
        res[key]["png"] = str(png)
        if not ins:   # no inputs: resolution of the source doesn't change anything, one run is enough
            break
    rep = dict(name=a.name, tox=str(tox), inputs=ins, results=res)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(rep, indent=1))
    worse = False
    if a.compare:
        base = json.loads(Path(a.compare).read_text())["results"]
        for k, v in res.items():
            if k in base and base[k]["gpu_ms"] > 0:
                d = 100.0 * (v["gpu_ms"] - base[k]["gpu_ms"]) / base[k]["gpu_ms"]
                v["gpu_change_pct"] = round(d, 1)
                worse = worse or d > 20.0
        rep["over_budget"] = worse
    print(json.dumps(rep, indent=1))
    sys.exit(1 if worse else 0)


def interleaved(conn, a, old, new):
    import statistics
    runs = {"old": {}, "new": {}}
    ins = []
    for r in range(a.repeats):
        for label, tox in (("old", old), ("new", new)):
            ins = json.loads(run(conn, f"TOX = {str(tox)!r}\n" + SETUP))
            for (w, h) in ((1280, 720), (1920, 1080)):
                key = f"{w}x{h}"
                runs[label].setdefault(key, []).append(measure(conn, a.frames, w, h)["gpu_ms"])
                if r == 0:
                    png = ROOT / "validation" / "bench" / f"{a.name}_{key}_{label}.png"
                    png.parent.mkdir(parents=True, exist_ok=True)
                    run(conn, f"""c = op('/bench/c')
o = c.op('preview') if (c.op('preview') is not None and c.op('preview').isTOP) else c.op('out1')
if o is not None and o.isTOP: o.save({str(png)!r})
print('ok')""")
                if not ins:
                    break
    rep = dict(name=a.name, old=str(old), new=str(new), repeats=a.repeats, frames=a.frames, results={})
    over = False
    for key in runs["new"]:
        mo, mn = statistics.median(runs["old"][key]), statistics.median(runs["new"][key])
        d = 100.0 * (mn - mo) / mo if mo > 0 else 0.0
        over = over or d > 20.0
        rep["results"][key] = dict(old_gpu_ms=round(mo, 4), new_gpu_ms=round(mn, 4), change_pct=round(d, 1),
                                   old_runs=runs["old"][key], new_runs=runs["new"][key],
                                   png_old=str(ROOT / "validation" / "bench" / f"{a.name}_{key}_old.png"),
                                   png_new=str(ROOT / "validation" / "bench" / f"{a.name}_{key}_new.png"))
    rep["over_budget"] = over
    if a.out:
        Path(a.out).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))
    return 1 if over else 0


if __name__ == "__main__":
    main()
