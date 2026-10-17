#!/usr/bin/env python3
"""Validate a component tox in a scratch TD:  validate.py <instance> <name> [seconds=3]
Loads tox/<name>.tox into /validate/<name>, lets it run, checks errors recursively,
checks custom params + out1 TOP, saves validation/<name>.png and prints a JSON report."""
import json, subprocess, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tdctl  # noqa
from td_mcp.client import call, load_connection

ROOT = Path(__file__).resolve().parent.parent

def run(conn, code):
    r = call("execute_python", {"code": code}, connection=conn, timeout=60)
    if not r.get("ok"):
        raise SystemExit("TD error: " + str(r.get("traceback") or r.get("error"))[-2000:])
    return r

def main():
    inst, name = sys.argv[1], sys.argv[2]
    secs = float(sys.argv[3]) if len(sys.argv) > 3 else 3
    conn = load_connection(tdctl.d(inst) / "connection.json")
    fam = name.split("_")[0]
    tox = ROOT / "tox" / fam / f"{name}.tox"
    if not tox.exists():
        tox = ROOT / "tox" / f"{name}.tox"   # legacy flat layout
    assert tox.exists(), tox
    run(conn, f"""
import td
v = op('/validate') or op('/').create(td.containerCOMP, 'validate')
old = v.op({name!r})
if old: old.destroy()
c = v.loadTox({str(tox)!r})
c.name = {name!r}
c.allowCooking = True
# frame-end driver: force-cook every out* TOP under /validate (headless TD only cooks what is pulled)
d = v.op('driver') or v.create(td.executeDAT, 'driver')
d.text = '''def onFrameEnd(frame):
    for c in op('/validate').children:
        if c.isCOMP:
            for o in c.children:
                if o.isTOP and (o.name.startswith('out') or o.name == 'preview'):
                    o.cook(force=True)
    return
'''
d.par.frameend = 1
d.par.active = 1
""")
    time.sleep(secs)
    png = ROOT / "validation" / f"{name}.png"
    r = run(conn, f"""
import json, td
c = op('/validate/{name}')
errs = []
for o in [c] + c.findChildren():
    for kind, s in (('error', o.errors()), ('warning', o.warnings()), ('script', o.scriptErrors())):
        if s: errs.append([kind, o.path, s[:300]])
    # GLSL compile errors live in the shader _info DATs / compile log, not always in errors()
    if o.type in ('glsl', 'glslmulti') and o.isTOP or o.OPType in ('glslPOP','glsladvancedPOP','glslMAT'):
        try:
            log = str(getattr(o, 'compileResult', '') or '')
        except Exception:
            log = ''
        if 'error' in log.lower(): errs.append(['error', o.path, 'GLSL: ' + log[:300]])
    # stale absolute references to the build location
    for p in o.pars():
        txt = (p.expr if p.mode == ParMode.EXPRESSION else str(p.val))
        if '/build/' in txt: errs.append(['error', o.path, 'absolute /build/ ref in ' + p.name + ': ' + txt[:120]])
    # parameter expression errors
    for p in o.pars():
        if p.mode == ParMode.EXPRESSION and 'me.input' not in p.expr:
            try: p.eval()
            except Exception as e: errs.append(['error', o.path, 'expr ' + p.name + ': ' + str(e)[:200]])
outs = [c.op('preview')] if (c.op('preview') is not None and c.op('preview').isTOP) else sorted([o for o in c.findChildren(depth=1) if o.isTOP and o.name.startswith('out')], key=lambda o: o.name)
info = dict(path=c.path, custom_pages=[p.name for p in c.customPages],
            custom_pars=[p.name for p in c.customPars], outs=[o.name for o in outs],
            cpu_ms=round(c.cookTime if hasattr(c,'cookTime') else 0,3),
            gpu_ms=round(sum(getattr(o,'gpuCookTime',0) for o in c.findChildren()),3),
            fps=round(project.cookRate,1), problems=errs)
if outs:
    o = outs[0]
    info['res'] = [o.width, o.height]
    o.save({str(png)!r})
    # simple stats: is the image non-empty / non-constant?
    import numpy as np
    a = o.numpyArray()
    if a is not None:
        info['mean'] = [round(float(x),4) for x in a[...,:3].mean(axis=(0,1))]
        info['std'] = round(float(a[...,:3].std()),4)
        c.store('_vframe', a[::4, ::4, :3].copy())
print(json.dumps(info))
""")
    rep = json.loads(r["stdout"].strip().splitlines()[-1])
    conv_code = f"c = op('/validate/{name}')\n" + (ROOT / "tools" / "conv_check_td.py").read_text()
    rep["conventions"] = json.loads(run(conn, conv_code)["stdout"].strip().splitlines()[-1])
    time.sleep(0.7)
    r2 = run(conn, f"""
c = op('/validate/{name}')
_tops = [c.op('preview')] if (c.op('preview') is not None and c.op('preview').isTOP) else sorted([o for o in c.findChildren(depth=1) if o.isTOP and o.name.startswith('out')], key=lambda o: o.name)
o = _tops[0] if _tops else None
a = o.numpyArray() if o is not None else None
b = c.fetch('_vframe', None)
print(float(abs(a[::4, ::4, :3] - b).mean()) if (a is not None and b is not None) else 0.0)
""")
    m2 = float(r2["stdout"].strip().splitlines()[-1])
    rep["frame_diff"] = round(m2, 5)
    rep["animating"] = m2 > 1e-4
    rep["png"] = str(png) if png.exists() else None
    util = name.startswith("UTIL_")   # utilities output DATs: no image/animation requirement
    rep["pass"] = (not [p for p in rep["problems"] if p[0] in ("error", "script")] and not rep.get("conventions")
                   and (util or (bool(rep["outs"]) and rep.get("std", 0) > 0.002)))
    print(json.dumps(rep, indent=1))
    sys.exit(0 if rep["pass"] else 1)

if __name__ == "__main__":
    main()
