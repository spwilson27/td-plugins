# usage: set NAME and CHANGES before exec: placeholder replaced by wrapper
import json
c = op('/validate/%s' % NAME)
out = []
for k, v in CHANGES:
    try:
        if v == 'PULSE': c.par[k].pulse()
        else: c.par[k] = v
    except Exception as e:
        out.append('SETFAIL %s %s' % (k, e))
    # force cook
    for o in c.children:
        if o.isTOP and o.name.startswith('out'): o.cook(force=True)
    errs = []
    for o in [c] + c.findChildren():
        for s in (o.errors(), o.warnings(), o.scriptErrors()):
            if s: errs.append((o.path, s[:200]))
    out.append((k, v, c.par[k].eval() if k in c.par else None, errs))
print(json.dumps(out, indent=0))
