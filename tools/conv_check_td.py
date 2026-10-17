# Runs inside TD. Expects `c` = component COMP. Prints JSON list of convention violations.
import json
fam = c.name.split('_')[0]
conv = []
REAL_OUT = ('outTOP','outPOP','outCHOP','outSOP','outDAT','outMAT')
realouts = sorted([o for o in c.children if o.OPType in REAL_OUT], key=lambda o: o.name)
if fam not in ('TOP','POP','SOP','CHOP','GEN','MAT','UTIL','SDF'): conv.append('name must start with TOP_/POP_/SOP_/CHOP_/GEN_/MAT_/UTIL_/SDF_')
want1 = ('outMAT',) if fam == 'MAT' else (('outTOP', 'outPOP') if fam in ('GEN', 'POP') else (('outDAT', 'outTOP') if fam == 'UTIL' else (('outDAT', 'outTOP', 'outPOP', 'outMAT') if fam == 'SDF' else ('outTOP',))))
if not realouts or realouts[0].name != 'out1' or realouts[0].OPType not in want1: conv.append('out1 must be a real ' + '/'.join(want1))
pv = c.op('preview')
if fam != 'UTIL' and realouts and realouts[0].OPType != 'outTOP' and not (pv is not None and pv.isTOP): conv.append('out1 is not a TOP: an internal preview TOP named preview is required')
vw = c.par.opviewer.eval()
want_v = pv if (pv is not None and pv.isTOP) else c.op('out1')
if vw is None or want_v is None or vw.path != want_v.path: conv.append('node viewer must show %s (got %s)' % (want_v.name if want_v else '?', vw.path if vw else None))
elif not vw.isTOP and fam != 'UTIL': conv.append('node viewer must show a TOP preview')
if fam == 'MAT':
    pv = c.op('preview')
    if pv is None or not pv.isTOP: conv.append('MAT_ needs an internal preview TOP named preview')
    mp = [pg for pg in c.customPages if pg.name == 'Material']
    if not hasattr(c.par, 'Applyto'): conv.append('MAT_ missing Applyto')
    elif mp and mp[0].pars[0].name != 'Applyto': conv.append('Applyto must be the first Material parameter')
    for dn in ('applyto_callbacks', 'applyto_watch'):
        if c.op(dn) is None: conv.append('MAT_ missing ' + dn)
if len(c.outputConnectors) < 1: conv.append('no output connectors')
fakes = [o.name for o in c.children if o.name.startswith('out') and o.OPType not in REAL_OUT]
if fakes: conv.append('out* ops that are not Out OPs: ' + str(fakes))
nolabel = [o.name for o in realouts if not (hasattr(o.par,'label') and o.par.label.eval())]
if nolabel: conv.append('Out OPs without label: ' + str(nolabel))
generic = [o.name for o in realouts if o.par.label.eval() in ('result',) and False or o.par.label.eval().startswith('output')]
if generic: conv.append('Out OPs with generic labels: ' + str(generic))
ins = sorted([o for o in c.children if o.OPType in ('inTOP','inPOP','inCHOP','inSOP','inDAT')], key=lambda o: o.name)
inolabel = [o.name for o in sorted([o for o in c.children if o.OPType in ('inTOP','inPOP','inCHOP','inSOP','inDAT')], key=lambda o: o.name) if not o.par.label.eval()]
if inolabel: conv.append('In OPs without label: ' + str(inolabel))
need = {'TOP':'inTOP','POP':'inPOP','SOP':'inSOP','CHOP':'inCHOP'}.get(fam)
if need and (not ins or ins[0].OPType != need): conv.append('primary input in1 must be ' + need)
chops = [i for i,o in enumerate(ins) if o.OPType == 'inCHOP']
if chops and fam != 'CHOP' and chops[-1] != len(ins)-1: conv.append('modulation inCHOP must be the last input')
pages = [pg.name for pg in c.customPages]
if pages and pages[-1] != 'About': conv.append('About must be the last page')
first = 'Material' if fam == 'MAT' else 'Controls'
if pages and pages[0] != first: conv.append(first + ' must be the first page (got %s)' % pages[0])
for a, b in (('Look','Loop'), ('Loop','About'), ('Look','About')):
    if a in pages and b in pages and pages.index(a) > pages.index(b): conv.append(a + ' must come before ' + b)
for pn in ('Version','Description','Family','Libraryroot','Help','Snippets'):
    if not hasattr(c.par, pn): conv.append('About page missing ' + pn)
if 'Loop' in pages: conv.append('Loop page is not allowed (v3: animation is preview-only)')
for pn in ('Timesource', 'Phase', 'Clock', 'Loopseconds', 'Loopbeats', 'Loopreset'):
    if hasattr(c.par, pn): conv.append('loop parameter not allowed: ' + pn)
if fam == 'TOP':
    for pn in ('Mix','Bypass','Resolutionmode'):
        if not hasattr(c.par, pn): conv.append('TOP_ effect missing ' + pn)
if fam == 'MAT' and not (c.op('mat') and c.op('mat').family == 'MAT'): conv.append('MAT_ needs <comp>/mat')
if [o for o in c.findChildren(type=executeDAT) if 'keepalive' in o.name.lower()]: conv.append('keepalive Execute DAT present')
_ns = {}
exec(open(__import__('os').path.join(__import__('os').path.expanduser(__import__('os').environ.get('TD_PLUGINS_HOME', '~/software/td-plugins')), 'td_organize', 'td_runtime.py')).read(), _ns)
_ov = _ns['check'](c)
if _ov: conv.append('overlapping nodes (%d): %s' % (len(_ov), str(_ov[:4])))
if fam in ('TOP', 'POP') and ins and c.op('demo') is None:
    conv.append('preview-only demo sources must live in a Base COMP named demo (gated off when inputs are connected)')
print(json.dumps(conv))
