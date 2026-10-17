#!/usr/bin/env python3
"""validate_snippet.py <inst> <NAME> [seconds=4]
Loads snippets/<NAME>.tox into /snipval, lets it run (force-cooking every `example*` TOP each frame),
checks: no errors/warnings anywhere (incl. the component instances), >=1 example, every example has a
Null TOP named exampleN, >=1 instance of the component whose externaltox points at tox/<FAM>/<NAME>.tox,
an annotation per example. Saves validation/snippets/<NAME>_exampleN.png and prints a JSON report."""
import json, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tdctl  # noqa
from tdwait import wait_frames
from td_mcp.client import call, load_connection
ROOT = Path(__file__).resolve().parent.parent

def run(conn, code):
    r = call("execute_python", {"code": code}, connection=conn, timeout=90)
    if not r.get("ok"):
        raise SystemExit("TD error: " + str(r.get("traceback") or r.get("error"))[-2000:])
    return r

def main():
    inst, name = sys.argv[1], sys.argv[2]
    frames = int(float(sys.argv[3])) if len(sys.argv) > 3 else 150   # cooked frames before capture
    conn = load_connection(tdctl.d(inst) / "connection.json")
    tox = ROOT / "snippets" / f"{name}.tox"
    assert tox.exists(), tox
    run(conn, f"""
import td
v = op('/snipval') or op('/').create(td.baseCOMP, 'snipval')
for ch in list(v.children): ch.destroy()
s = v.loadTox({str(tox)!r})
d = v.create(td.executeDAT, 'driver')
d.text = '''def onFrameEnd(frame):
    for o in op('/snipval').findChildren(type=TOP):
        if o.name.startswith('example'):
            o.cook(force=True)
    return
'''
d.par.frameend = 1
d.par.active = 1
""")
    wait_frames(conn, frames)
    # adaptive: heavy examples (e.g. long SDF chains) compile their shaders asynchronously after load;
    # keep cooking in 60-frame steps (up to 600 extra) while any exampleN output is still blank
    probe = """
import json
s = [c for c in op('/snipval').children if c.isCOMP and c.name != 'driver'][0]
out = []
for o in s.findChildren(type=nullTOP):
    if o.name.startswith('example'):
        a = o.numpyArray()
        out.append(float(a[...,:3].std()) if a is not None else 0.0)
print(json.dumps(out))
"""
    for _ in range(10):
        stds = json.loads(run(conn, probe)["stdout"].strip().splitlines()[-1])
        if stds and min(stds) >= 0.002:
            break
        wait_frames(conn, 60)
    outdir = ROOT / "validation" / "snippets"; outdir.mkdir(parents=True, exist_ok=True)
    r = run(conn, f"""
import json, td
v = op('/snipval'); s = [c for c in v.children if c.isCOMP and c.name != 'driver'][0]
errs = []
for o in [s] + s.findChildren():
    for kind, m in (('error', o.errors()), ('warning', o.warnings()), ('script', o.scriptErrors())):
        if m: errs.append([kind, o.path, m[:250]])
fam = {name!r}.split('_')[0]
inst = [c for c in s.findChildren(type=COMP) if str(c.par.externaltox.eval()).replace('\\\\','/').endswith('/tox/' + fam + '/' + {name!r} + '.tox')]
ex = sorted([o for o in s.findChildren(type=nullTOP) if o.name.startswith('example')], key=lambda o: o.name)
ann = [o for o in s.findChildren(type=annotateCOMP)]
enclosed = set()
for a in ann:
    try: enclosed |= set(x.path for x in a.enclosedOPs)
    except Exception: pass
outside = [o.name for o in ex if o.path not in enclosed]
shots = []
import numpy as np
for o in ex:
    p = {str(outdir)!r} + '/' + {name!r} + '_' + o.name + '.png'
    o.save(p); a = o.numpyArray()
    shots.append([o.name, p, round(float(a[...,:3].std()), 4) if a is not None else 0])
_ns = {{}}
exec(open(__import__('os').path.join(__import__('os').path.expanduser(__import__('os').environ.get('TD_PLUGINS_HOME', '~/software/td-plugins')), 'td_organize', 'td_runtime.py')).read(), _ns)
_ov = _ns['check'](s)
print(json.dumps(dict(overlaps=[str(x) for x in _ov[:6]], noverlaps=len(_ov), snippet=s.name, instances=[c.path for c in inst], examples=shots, annotations=len(ann), outside=outside, problems=errs)))
""")
    rep = json.loads(r["stdout"].strip().splitlines()[-1])
    conv = []
    if not rep["instances"]: conv.append("no component instance with externaltox -> tox/<FAM>/<NAME>.tox")
    if not rep["examples"]: conv.append("no exampleN Null TOP")
    if rep["annotations"] < len(rep["examples"]): conv.append("each example needs an Annotate COMP")
    if rep.get("noverlaps"): conv.append("overlapping nodes (%d): %s" % (rep["noverlaps"], rep["overlaps"]))
    if rep.get("outside"): conv.append("example outputs not inside an Annotate box: " + str(rep["outside"]))
    blank = [e[0] for e in rep["examples"] if e[2] < 0.002]
    if blank: conv.append("blank example output: " + str(blank))
    rep["conventions"] = conv
    rep["pass"] = not conv and not [p for p in rep["problems"] if p[0] in ("error", "script")] and not [p for p in rep["problems"] if p[0] == "warning"]
    print(json.dumps(rep, indent=1))
    sys.exit(0 if rep["pass"] else 1)

if __name__ == "__main__":
    main()
