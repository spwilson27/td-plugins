#!/usr/bin/env python3
"""conform.py <inst> <NAME> [raw.tox]

Apply the mechanical library conventions (CONVENTIONS.md) to a built component and save it as
tox/<FAMILY>/<NAME>.tox. Input is tox/_raw/<NAME>.tox (what build.py saves) unless a path is given.

What it does (inside TD):
  - renames the COMP to NAME, records version/family/description from components.json
  - converts any out* operator that is not a real Out OP into one (Null kept as `null_<old>`),
    renumbers outputs out1..outN (out1 = the final TOP), sets Out OP `label` and `connectorder`
  - sets connectorder on In OPs (by name), removes per-frame `keepalive` Execute DATs
  - adds the About page (Version, Description, Family, Help, Snippets, Libraryroot) + its callbacks
  - orders pages: Controls, <component pages>, Look, Loop, About
  - node colour by family, node viewer shows out1
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import tdctl  # noqa
from td_mcp.client import call, load_connection

ROOT = Path(__file__).resolve().parent.parent

TD_CODE = r'''
import td, os, json
spec = json.loads(SPEC)
NAME, FAM = spec['name'], spec['family']
h = op('/conform') or op('/').create(td.baseCOMP, 'conform')
for ch in list(h.children): ch.destroy()
c = h.loadTox(spec['raw'])
c.name = NAME
log = []

OUT_TYPES = {'TOP': td.outTOP, 'POP': td.outPOP, 'CHOP': td.outCHOP, 'SOP': td.outSOP, 'DAT': td.outDAT, 'MAT': td.outMAT}
REAL_OUT = ('outTOP', 'outPOP', 'outCHOP', 'outSOP', 'outDAT', 'outMAT')
IN_TYPES = ('inTOP', 'inPOP', 'inCHOP', 'inSOP', 'inDAT')

# --- outputs -------------------------------------------------------------
LBL = spec.get('labels') or {}
OUTL, INL = LBL.get('outputs', {}), LBL.get('inputs', {})
cands = [o for o in c.children if o.name.startswith('out') and o.family in OUT_TYPES]
def okey(o):
    # out1 first, then other TOPs by name, then POP/SOP/CHOP/DAT
    return (o.name != 'out1', ['TOP', 'POP', 'SOP', 'CHOP', 'DAT', 'MAT'].index(o.family), o.name)
cands.sort(key=okey)
assert cands and cands[0].name == 'out1', 'component needs an out1'
assert cands[0].family == 'TOP' or (cands[0].family == 'POP' and FAM in ('GEN', 'POP')) or (cands[0].family == 'DAT' and FAM == 'UTIL') or FAM == 'SDF', 'out1 must be a TOP (a POP for GEN_/POP_, a DAT for UTIL_; SDF_ any)'
if cands[0].family != 'TOP' and FAM not in ('MAT', 'UTIL'):
    assert c.op('preview') is not None and c.op('preview').isTOP, 'components whose out1 is not a TOP need an internal preview TOP'
final = []
if FAM == 'MAT':
    # MAT components: the material is out1; the preview render becomes an internal 'preview' TOP
    pv = cands.pop(0)
    if pv.OPType == 'outTOP':
        src = pv.inputs[0] if pv.inputs else None
        nn = c.create(td.nullTOP, 'preview_tmp'); nn.nodeX, nn.nodeY = pv.nodeX, pv.nodeY
        if src is not None: nn.inputConnectors[0].connect(src)
        pv.destroy(); pv = nn
    pv.name = 'preview'
    pv.comment = 'material preview render (shown in the node viewer; not an output)'
    mat = c.op('mat'); assert mat is not None and mat.family == 'MAT', 'MAT_ component needs <comp>/mat'
    om = c.create(td.outMAT, 'tmp_outmat'); om.nodeX, om.nodeY = mat.nodeX + 200, mat.nodeY
    om.inputConnectors[0].connect(mat)
    final.append((om, 'material')); log.append('MAT: out1 = Out MAT, preview -> internal')
for o in cands:
    # fallback label: the op's comment, else name-derived (io_labels.json overrides below)
    label = (o.comment or '').strip() or {'out1': 'result'}.get(o.name, o.name.replace('out_', '').replace('out', 'output'))
    if o.OPType in REAL_OUT:
        final.append((o, label)); continue
    old = o.name
    o.name = 'null_' + old
    n = c.create(OUT_TYPES[o.family], 'tmp_' + old)
    n.nodeX, n.nodeY = o.nodeX + 200, o.nodeY
    n.inputConnectors[0].connect(o)
    final.append((n, label)); log.append('null->out: ' + old)
for i, (o, label) in enumerate(final):
    o.name = 'tmpx_%d' % i
for i, (o, label) in enumerate(final):
    o.name = 'out%d' % (i + 1)
    lab = OUTL.get(o.name, label)
    if hasattr(o.par, 'label'): o.par.label = lab
    if hasattr(o.par, 'connectorder'): o.par.connectorder = i
    o.comment = lab
# --- inputs --------------------------------------------------------------
ins = sorted([o for o in c.children if o.OPType in IN_TYPES], key=lambda o: o.name)
for i, o in enumerate(ins):
    if hasattr(o.par, 'connectorder'): o.par.connectorder = i
    lab = INL.get(o.name) or (o.par.label.eval() if hasattr(o.par, 'label') else '') or (o.comment or '').strip()
    if lab:
        o.par.label = lab; o.comment = lab
# --- MAT: Apply To field ---------------------------------------------------
if FAM == 'MAT':
    pg = [x for x in c.customPages if x.name == 'Material']
    pg = pg[0] if pg else c.appendCustomPage('Material')
    if not hasattr(c.par, 'Applyto'):
        ap = pg.appendOP('Applyto', label='Apply To')[0]
        ap.help = 'Drag Geometry COMPs and/or Render TOPs here. Geometry: sets its Material; Render TOP: sets its Override Material. Removing an op from this field clears it again.'
        tn = []
        for x in pg.pars:
            if x.tupletName != 'Applyto' and x.tupletName not in tn: tn.append(x.tupletName)
        pg.sort('Applyto', *tn)
    ac = c.op('applyto_callbacks') or c.create(td.parameterexecuteDAT, 'applyto_callbacks')
    ac.text = APPLY_CB
    ac.par.op = '..'
    ac.par.pars = 'Applyto'
    ac.par.valuechange = True
    ac.par.onpulse = False
    ac.par.custom = True
    ac.par.builtin = False
    ac.nodeX, ac.nodeY = -400, -560
    # re-apply when this component is renamed or moved, so targets keep pointing at <comp>/mat
    aw = c.op('applyto_watch') or c.create(td.opexecuteDAT, 'applyto_watch')
    aw.text = "def onNameChange(changeOp):\n    op('applyto_callbacks').module.apply(changeOp)\n    return\n\ndef onPathChange(changeOp):\n    op('applyto_callbacks').module.apply(changeOp)\n    return\n"
    aw.par.op = '..'
    for pn in ('precook', 'postcook', 'flagchange', 'wirechange', 'uichange', 'numchildrenchange', 'childrename', 'currentchildchange', 'extensionchange'):
        if hasattr(aw.par, pn): setattr(aw.par, pn, False)
    aw.par.namechange = True
    aw.par.pathchange = True
    aw.nodeX, aw.nodeY = -400, -720
# --- remove keepalives ---------------------------------------------------
for o in c.findChildren(type=executeDAT):
    if 'keepalive' in o.name.lower() or o.name.lower() in ('alwayscook', 'cookdriver'):
        log.append('removed ' + o.path); o.destroy()

# --- About page ----------------------------------------------------------
for pg in c.customPages:
    if pg.name == 'About': pg.destroy()
ab = c.appendCustomPage('About')
p = ab.appendStr('Version', label='Version')[0]; p.val = spec['version']; p.default = spec['version']; p.readOnly = True
p = ab.appendStr('Description', label='Description')[0]; p.val = spec['description']; p.default = spec['description']; p.readOnly = True
p = ab.appendStr('Family', label='Input Family')[0]; p.val = FAM; p.default = FAM; p.readOnly = True
p = ab.appendStr('Libraryroot', label='Library Root')[0]
p.expr = "__import__('os').environ.get('TD_PLUGINS_HOME') or __import__('os').path.expanduser('~/software/td-plugins')"
ab.appendPulse('Help', label='Open Help (README)')
ab.appendPulse('Snippets', label='Open Snippets')
cb = c.op('about_callbacks') or c.create(td.parameterexecuteDAT, 'about_callbacks')
cb.text = ABOUT_CB
cb.par.op = c.path if False else '..'
cb.par.pars = 'Help Snippets'
cb.par.valuechange = False
cb.par.onpulse = True
cb.par.custom = True
cb.par.builtin = False
cb.nodeX, cb.nodeY = -400, -400

# --- page order -----------------------------------------------------------
names = [pg.name for pg in c.customPages]
head = [n for n in (('Material',) if FAM == 'MAT' else ('Controls',)) if n in names]
tail = [n for n in ('Look', 'About') if n in names]
mid = [n for n in names if n not in head + tail]
c.sortCustomPages(*(head + mid + tail))

# --- node appearance ------------------------------------------------------
COL = {'TOP': (0.25, 0.42, 0.75), 'GEN': (0.25, 0.6, 0.35), 'POP': (0.55, 0.35, 0.7),
       'SOP': (0.3, 0.55, 0.65), 'CHOP': (0.7, 0.6, 0.25), 'MAT': (0.8, 0.5, 0.2), 'UTIL': (0.45, 0.45, 0.45), 'SDF': (0.75, 0.3, 0.45)}
c.color = COL.get(FAM, (0.5, 0.5, 0.5))
c.par.opviewer = './preview' if (c.op('preview') is not None and c.op('preview').isTOP) else './out1'   # OP refs resolve from the parent; ./ = inside
c.viewer = True
c.comment = spec['description']

# --- layout: no overlapping nodes, left->right data flow (td-organize) -----------
_ns = {}
exec(open(__import__('os').path.join(__import__('os').path.expanduser(__import__('os').environ.get('TD_PLUGINS_HOME', '~/software/td-plugins')), 'td_organize', 'td_runtime.py')).read(), _ns)
_ns['organize'](c)
_left = _ns['check'](c)
assert not _left, 'td-organize left overlaps: %s' % _left[:5]
os.makedirs(os.path.dirname(spec['out']), exist_ok=True)
c.save(spec['out'])
print(json.dumps(dict(log=log, outs=[(o.name, o.OPType, getattr(o.par, 'label', None) and o.par.label.eval()) for o in sorted([x for x in c.children if x.OPType in REAL_OUT], key=lambda x: x.name)],
                      ins=[(o.name, o.OPType) for o in ins], pages=[pg.name for pg in c.customPages])))
'''

APPLY_CB = r"""# Apply To: assign this component's material to the Geometry COMPs / Render TOPs dropped on the Applyto field.
# Targets get a constant reference to <comp>/mat (TouchDesigner keeps constant op references valid on rename/move).

def apply(comp):
    mat = comp.op('mat')
    prev = comp.fetch('applied_to', [])
    cur = []
    for t in comp.par.Applyto.evalOPs():
        if t is None or t == comp:
            continue
        if t.OPType == 'renderTOP':
            t.par.overridemat = mat
        elif t.isCOMP and hasattr(t.par, 'material'):
            t.par.material = mat
        else:
            debug('Apply To: %s is not a Geometry COMP or Render TOP' % t.path); continue
        cur.append(t.path)
    for p in prev:
        t = op(p)
        if p in cur or t is None:
            continue
        for pn in ('material', 'overridemat'):
            if hasattr(t.par, pn) and t.par[pn].eval() == mat:
                t.par[pn] = ''
    comp.store('applied_to', cur)

def onValueChange(par, prev):
    apply(par.owner)
    return
"""

ABOUT_CB = r"""# About page actions: Help opens the README, Snippets opens the example network(s).
import os

def _root(comp):
    return comp.par.Libraryroot.eval()

def onPulse(par):
    comp = par.owner
    root = _root(comp)
    name = comp.name
    if par.name == 'Help':
        readme = os.path.join(root, 'components', name, 'README.md')
        if os.path.exists(readme):
            ui.viewFile(readme)
        else:
            debug('README not found: ' + readme)
    elif par.name == 'Snippets':
        path = os.path.join(root, 'snippets', name + '.tox')
        if not os.path.exists(path):
            debug('snippet not found: ' + path); return
        host = op('/local') if op('/local') else op('/')
        holder = host.op('td_plugins_snippets') or host.create(baseCOMP, 'td_plugins_snippets')
        holder.comment = 'Example networks opened from td-plugins components. Safe to delete.'
        old = holder.op(name + '_snippet')
        if old: old.destroy()
        s = holder.loadTox(path)
        s.name = name + '_snippet'
        pane = ui.panes.createFloating(type=PaneType.NETWORKEDITOR, name=name + ' snippets')
        pane.owner = s
        pane.home()
    return
"""


def main():
    inst, name = sys.argv[1], sys.argv[2]
    man = {m['name']: m for m in json.loads((ROOT / 'components.json').read_text())}
    meta = ROOT / 'components' / name / 'meta.json'   # per-component override (new components before they're merged in)
    m = dict(man.get(name, {}), **(json.loads(meta.read_text()) if meta.exists() else {}))
    m.setdefault('name', name); m.setdefault('family', name.split('_')[0]); m.setdefault('version', '1.0.0'); m.setdefault('description', '')
    raw = sys.argv[3] if len(sys.argv) > 3 else str(ROOT / 'tox' / '_raw' / f'{name}.tox')
    labels = {}
    lf = ROOT / 'io_labels.json'
    if lf.exists():
        labels = json.loads(lf.read_text()).get(name, {})
    lc = ROOT / 'components' / name / 'labels.json'
    if lc.exists():
        labels = json.loads(lc.read_text())
    spec = dict(m, raw=raw, out=str(ROOT / 'tox' / m['family'] / f'{name}.tox'), labels=labels)
    code = f"SPEC = {json.dumps(json.dumps(spec))}\nABOUT_CB = {ABOUT_CB!r}\nAPPLY_CB = {APPLY_CB!r}\n" + TD_CODE
    conn = load_connection(tdctl.d(inst) / 'connection.json')
    r = call('execute_python', {'code': code}, connection=conn, timeout=90)
    if not r.get('ok'):
        sys.exit('conform failed: ' + str(r.get('traceback') or r.get('error'))[-2000:])
    print(r['stdout'].strip())


if __name__ == '__main__':
    main()
