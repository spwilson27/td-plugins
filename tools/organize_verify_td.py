#!/usr/bin/env python3
"""Real-TD verification: verify_td.py <inst> tox1 [tox2 ...]
Loads each tox into /orgtest, check -> organize -> check, compares errors and wiring."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path.home() / "software/td-plugins/tools"))
import tdctl  # noqa
from td_mcp.client import call, load_connection
from td_organize.cli import run

conn_file = tdctl.d(sys.argv[1]) / "connection.json"
conn = load_connection(conn_file)

def ex(code):
    r = call("execute_python", {"code": code}, connection=conn, timeout=100)
    if not r.get("ok"):
        raise SystemExit(str(r.get("traceback") or r)[-2500:])
    return r["stdout"]

SNAP = '''
import json
def snap(root):
    out = {}
    for o in [root] + root.findChildren():
        if o.type == "annotate": continue
        ins = [[c.owner.path for c in cn.connections] for cn in o.inputConnectors]
        pars = {p.name: (p.expr if p.mode == ParMode.EXPRESSION else str(p.val)) for p in o.pars()}
        out[o.path] = (ins, pars)
    return out
def errs(root):
    return sorted(o.path + ":" + str(o.errors())[:80] for o in [root] + root.findChildren() if o.errors())
def sketch(c, W=78, H=22):
    ns = [o for o in c.children if o.type != "annotate"]
    if not ns: return ""
    x0 = min(o.nodeX for o in ns); x1 = max(o.nodeX + o.nodeWidth for o in ns)
    y0 = min(o.nodeY for o in ns); y1 = max(o.nodeY + o.nodeHeight for o in ns)
    g = [[" "] * W for _ in range(H)]
    for o in ns:
        cx = int((o.nodeX - x0) / max(x1 - x0, 1) * (W - 1)); cy = int((y1 - o.nodeY - o.nodeHeight) / max(y1 - y0, 1) * (H - 1))
        ex_ = int((o.nodeX + o.nodeWidth - x0) / max(x1 - x0, 1) * (W - 1)); ey = int((y1 - o.nodeY) / max(y1 - y0, 1) * (H - 1))
        for yy in range(cy, min(ey, H - 1) + 1):
            for xx in range(cx, min(ex_, W - 1) + 1):
                g[yy][xx] = "#" if yy in (cy, ey) or xx in (cx, ex_) else "."
    return "\\n".join("".join(r) for r in g) + "\\n  bbox %dx%d, %d nodes" % (x1 - x0, y1 - y0, len(ns))
'''
ex("s = op('/orgtest') or op('/').create(containerCOMP, 'orgtest')")
for tox in sys.argv[2:]:
    name = Path(tox).stem
    ex(SNAP + f"""
s = op('/orgtest'); old = s.op({name!r})
if old: old.destroy()
c = s.loadTox({str(Path(tox).expanduser())!r}); c.name = {name!r}
op('/').store('snap_' + {name!r}, (snap(c), errs(c)))
""")
    path = f"/orgtest/{name}"
    pre = run("check", conn_file, path)
    ex(SNAP + f"print(sketch(op({path!r})))")  # warm
    print(f"=== {name}: BEFORE sketch")
    print(ex(SNAP + f"print(sketch(op({path!r})))"))
    st = run("organize", conn_file, path)
    post = run("check", conn_file, path)
    print(f"=== {name}: AFTER sketch")
    print(ex(SNAP + f"print(sketch(op({path!r})))"))
    out = ex(SNAP + f"""
a, e0 = op('/').fetch('snap_' + {name!r}); b = snap(op({path!r}))
print(json.dumps(dict(wiring_pars_same=(a == b), errors_before=e0, errors_after=errs(op({path!r})))))
""")
    d = json.loads(out.strip().splitlines()[-1])
    per = {p: (s["overlaps_before"], s["overlaps_after"]) for p, s in st.items()}
    print(f"RESULT {name}: check before={len(pre)} after={len(post)}  per-comp(before,after)={per}")
    print(f"        wiring+pars unchanged={d['wiring_pars_same']} errors before={len(d['errors_before'])} after={len(d['errors_after'])} same={d['errors_before']==d['errors_after']}")
    if post:
        print("   remaining:", post[:5])
