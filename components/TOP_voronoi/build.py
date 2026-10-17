import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
NAME = 'TOP_voronoi'

def readf(fn): return open(os.path.join(ROOT, 'components', NAME, fn)).read()
def mkdat(c, nm, text):
    d = c.create(td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            ps = {'f': pg.appendFloat, 'i': pg.appendInt, 't': pg.appendToggle, 'p': pg.appendPulse, 'm': pg.appendMenu,
                  'rgb': pg.appendRGB, 'wh': pg.appendWH}[kind](nm, label=lab)
            if kind == 'm':
                ps[0].menuNames = [m[0] for m in o['menu']]; ps[0].menuLabels = [m[1] for m in o['menu']]
            if kind == 'p': continue
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                p.default = v; p.val = v
                if 'min' in o: p.min = o['min']; p.normMin = o['min']; p.clampMin = o.get('clamp', False)
                if 'max' in o: p.max = o['max']; p.normMax = o['max']; p.clampMax = o.get('clamp', False)

def uni(g, items):
    for i, (nm, vs) in enumerate(items):
        getattr(g.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', vs):
            p = getattr(g.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v

def glsl(c, nm, code, ins, items, fmt, size=None, tops=None):
    g = c.create(td.glslTOP, nm)
    g.par.pixeldat = mkdat(c, nm + '_code', code)
    for i, s in enumerate(ins): g.inputConnectors[i].connect(s)
    if tops: g.par.tops = tops
    if size:
        g.par.outputresolution = 'custom'; g.par.resolutionw = size[0]; g.par.resolutionh = size[1]
    g.par.format = fmt
    uni(g, items)
    return g

b = op('/build') or op('/').create(td.baseCOMP, 'build')
if b.op(NAME): b.op(NAME).destroy()
c = b.create(td.baseCOMP, NAME)
P = "parent().par."

pars(c, {
 'Controls': [
  ('f', 'Mix', 'Mix', 1.0, {'min': 0, 'max': 1, 'clamp': True}),
  ('t', 'Bypass', 'Bypass', False),
  ('m', 'Style', 'Style', 'cells', {'menu': [('cells', 'Cells'), ('edges', 'Edges'), ('cracked', 'Cracked glass'), ('stained', 'Stained glass')]}),
  ('i', 'Seeds', 'Seeds', 70, {'min': 2, 'max': 128, 'clamp': True}),
  ('f', 'Jitter', 'Jitter (grid to random)', 1.0, {'min': 0, 'max': 1, 'clamp': True}),
  ('f', 'Speed', 'Drift Speed', 0.3, {'min': 0, 'max': 4}),
  ('f', 'Motion', 'Drift Amount', 1.0, {'min': 0, 'max': 4}),
  ('i', 'Seed', 'Random Seed', 1, {'min': 0, 'max': 1000}),
 ],
 'Cells': [
  ('f', 'Borderwidth', 'Border Width (px)', 3.0, {'min': 0.5, 'max': 30}),
  ('f', 'Glow', 'Edge Glow', 1.0, {'min': 0, 'max': 3}),
  ('rgb', 'Edgecolor', 'Edge Colour', [1.0, 0.95, 0.85]),
  ('f', 'Edgetint', 'Edge Tint from Input', 0.7, {'min': 0, 'max': 1, 'clamp': True}),
  ('f', 'Displace', 'Shard Displacement', 0.25, {'min': 0, 'max': 1}),
  ('t', 'Delaunay', 'Delaunay Overlay', False),
  ('f', 'Linewidth', 'Delaunay Line Width (px)', 1.5, {'min': 0.5, 'max': 8}),
 ],
 'Density': [
  ('m', 'Densitymode', 'Density Follows', 'uniform', {'menu': [('uniform', 'Uniform'), ('bright', 'Bright areas'), ('dark', 'Dark areas'), ('edges', 'Edges')]}),
  ('f', 'Densityamount', 'Density Amount', 0.6, {'min': 0, 'max': 1, 'clamp': True}),
 ],
 'Output': [
  ('m', 'Resolutionmode', 'Resolution Mode', 'input', {'menu': [('input', 'Input'), ('custom', 'Custom')]}),
  ('wh', 'Resolution', 'Resolution', [1280, 720], {'min': 16, 'max': 8192}),
 ],
 'Look': [
  ('m', 'Look', 'Look', 'original', {'menu': [('original', 'Original'), ('mono', 'Mono')]}),
  ('f', 'Accent', 'Accent (red, Mono)', 0.0, {'min': 0, 'max': 1, 'clamp': True}),
 ],
})

# ---- input + gated demo ----
i1 = c.create(td.inTOP, 'in1')
demo = c.create(td.baseCOMP, 'demo')
dg = glsl(demo, 'defsrc', readf('src.glsl'), [], [('uP', ['absTime.seconds', 0, 0, 0])], 'rgba16float', size=(1280, 720))
do = demo.create(td.outTOP, 'demo_out'); do.inputConnectors[0].connect(dg)
sw = c.create(td.switchTOP, 'src_switch')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
rs = c.create(td.resolutionTOP, 'srcres'); rs.inputConnectors[0].connect(sw)
rs.par.outputresolution.expr = "'custom' if parent().par.Resolutionmode == 'custom' else 'useinput'"
rs.par.resolutionw.expr = P + 'Resolutionw'; rs.par.resolutionh.expr = P + 'Resolutionh'
rs.par.fillmode = 'fill'
rs.par.format = 'rgba16float'

# ---- modulation ----
MODLIB = '''# m(name): channel of the optional modulation In CHOP (band1-4, beat); default when absent
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
c.create(td.inCHOP, 'in2')
mk = c.create(td.textDAT, 'modlib'); mk.text = MODLIB
M = lambda n: "op('modlib').module.m('%s')" % n

# ---- passes ----
cnt = P + 'Seeds'
seeds = glsl(c, 'seeds', readf('seeds.glsl'), [rs], [
    ('uA', ['absTime.seconds*' + P + 'Speed', cnt, P + 'Jitter', P + 'Seed']),
    ('uB', [P + 'Motion*(1+2*' + M('band2') + ')', P + 'Densitymode.menuIndex', P + 'Densityamount', 0])],
    'rgba32float', size=(128, 2))
cells = glsl(c, 'cells', readf('cells.glsl'), [rs, seeds], [('uA', [cnt, 0, 0, 0])], 'rgba32float')
adj = glsl(c, 'adj', readf('adj.glsl'), [seeds], [('uA', [cnt, 0, 0, 0])], 'rgba16float', size=(128, 128))
style = glsl(c, 'style', readf('style.glsl'), [rs, seeds, cells], [
    ('uA', [P + 'Style.menuIndex', P + 'Borderwidth', P + 'Glow*(1+2*' + M('band1') + ')', P + 'Displace*(1+2*' + M('band3') + ')']),
    ('uB', ['1 if ' + P + 'Delaunay else 0', P + 'Linewidth', P + 'Mix', M('beat')]),
    ('uC', [P + 'Look.menuIndex', P + 'Accent', cnt, P + 'Edgetint']),
    ('uD', [P + 'Edgecolorr', P + 'Edgecolorg', P + 'Edgecolorb', 0])],
    'rgba16float', tops='adj')
mp = glsl(c, 'map', readf('map.glsl'), [cells, seeds], [('uA', [cnt, 0, 0, 0])], 'rgba16float')

byp = c.create(td.switchTOP, 'bypass'); byp.inputConnectors[0].connect(style); byp.inputConnectors[1].connect(rs)
byp.par.index.expr = '1 if ' + P + 'Bypass else 0'
o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(byp); o1.comment = 'stylised image'
o2 = c.create(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(mp); o2.comment = 'cell id + edge map'

c.save(os.path.join(ROOT, 'tox/_raw/%s.tox' % NAME))
for o in [c] + c.findChildren():
    for s in (o.errors(), o.warnings(), o.scriptErrors()):
        if s: print('ERR', o.path, s[:300])
print('saved')
