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
    # ---- phase 2: supported configuration = every input connected to a test source ----
    rep["connected"] = connected_phase(conn, name, secs, only_primary=True)
    rep["connected_all"] = connected_phase(conn, name, secs, only_primary=False)
    rep["png"] = str(png) if png.exists() else None
    util = name.startswith("UTIL_")   # utilities output DATs: no image/animation requirement
    cps = (rep["connected"], rep["connected_all"])
    rep["pass"] = (not rep["problems"] and not rep.get("conventions")
                   and not any(cp.get("problems") or cp.get("demo_cooking") for cp in cps)
                   and (util or (bool(rep["outs"]) and rep.get("std", 0) > 0.002)))
    print(json.dumps(rep, indent=1))
    sys.exit(0 if rep["pass"] else 1)

FIXTURE_DAT = ROOT / "tools" / "fixtures" / "SDF_input.txt"   # what an SDF_ wire carries (written by the SDF_ components)


def connected_phase(conn, name, secs, only_primary=False):
    """Connect a test source to every In op, run, and report errors/warnings plus whether the
    component's `demo` COMP (preview-only sources) still cooks. Inputs are disconnected afterwards."""
    sdf = FIXTURE_DAT.read_text() if FIXTURE_DAT.exists() else ""
    r = run(conn, f"""
import json, td
c = op('/validate/{name}'); v = op('/validate')
fx = v.op('fx_{name}')
if fx: fx.destroy()
fx = v.create(td.baseCOMP, 'fx_{name}')
ins = sorted([o for o in c.children if o.OPType in ('inTOP','inPOP','inCHOP','inSOP','inDAT')], key=lambda o: o.name)
made = []
for i, o in enumerate(ins[:1] if {only_primary} else ins):
    t = o.OPType
    if t == 'inTOP':
        s = fx.create(td.noiseTOP, 'top%d' % i); s.par.outputresolution = 'custom'; s.par.resolutionw = 1280; s.par.resolutionh = 720
        s.par.tz.expr = 'absTime.seconds * 0.3'; s.par.mono = False
    elif t == 'inPOP':
        s = fx.create(td.spherePOP, 'pop%d' % i)
    elif t == 'inSOP':
        s = fx.create(td.sphereSOP, 'sop%d' % i)
    elif t == 'inCHOP':
        s = fx.create(td.constantCHOP, 'chop%d' % i)
        for k, ch in enumerate(('band1', 'band2', 'band3', 'band4', 'beat', 'phase')):
            getattr(s.par, 'name%d' % k).val = ch; getattr(s.par, 'value%d' % k).val = 0.5
    else:
        s = fx.create(td.textDAT, 'dat%d' % i); s.text = {sdf!r}
    c.inputConnectors[i].connect(s); made.append([o.name, t])
print(json.dumps(made))
""")
    made = json.loads(r["stdout"].strip().splitlines()[-1])
    time.sleep(max(1.0, secs / 2))
    # cook counts of preview-only demo ops, sampled twice
    snap = f"""
import json
c = op('/validate/{name}'); d = c.op('demo')
print(json.dumps({{o.path: o.totalCooks for o in d.findChildren()}} if d else {{}}))
"""
    a = json.loads(run(conn, snap)["stdout"].strip().splitlines()[-1])
    time.sleep(1.0)
    b = json.loads(run(conn, snap)["stdout"].strip().splitlines()[-1])
    cooking = sorted(p for p in b if b[p] != a.get(p))
    r = run(conn, f"""
import json
c = op('/validate/{name}')
errs = []
for o in [c] + c.findChildren():
    for kind, s in (('error', o.errors()), ('warning', o.warnings()), ('script', o.scriptErrors())):
        if s: errs.append([kind, o.path, s[:300]])
for i in range(len(c.inputConnectors)):
    c.inputConnectors[i].disconnect()
op('/validate/fx_{name}').destroy()
print(json.dumps(errs))
""")
    errs = json.loads(r["stdout"].strip().splitlines()[-1])
    return dict(inputs=made, problems=errs, demo_cooking=cooking[:10], has_demo=bool(a or b))


if __name__ == "__main__":
    main()
