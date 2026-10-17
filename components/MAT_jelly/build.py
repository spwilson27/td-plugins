# ---- shared helpers (pasted at top of each build.py by components/_lib/mk.sh) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

def setres(o, w='parent().par.Resolutionw', h='parent().par.Resolutionh'):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w; o.par.resolutionh.expr = h

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=False, filt=None):
    """vecs: list of (uniformName, [4 values/exprs]) ; exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:   # inputs beyond the 3 wire connectors go through the TOPs parameter (index 3..)
        g.par.tops = ' '.join(s.name for s in inputs[3:])
    if vecs:
        g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    if filt: g.par.filtertype = filt
    return g

def add_pars(c, specs, page='Controls'):
    """spec tuples: (name, kind, ...)
      ('Amount','float',default,min,max)   ('Count','int',def,min,max)  ('On','toggle',def)
      ('Reset','pulse')  ('Mode','menu',[(id,label),..],default_index)  ('Res','wh',(w,h))
      ('Col','rgb',(r,g,b))  ('Txt','str',default)  ('Xy','xy',(x,y))"""
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse':
            pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]
            p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            ps = pg.appendWH(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'xy':
            ps = pg.appendXY(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.normMin = -1; q.normMax = 1
        elif k == 'rgb':
            ps = pg.appendRGB(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def input_stage(c, comp, bg=1.0):
    """in1 + animated default source -> switch 'src' (resolution = Resolution par). Returns src TOP."""
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', rd(comp, 'src.glsl'), vecs=[('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

PH = "(absTime.seconds/8.0)"   # internal preview animation (no loop parameters)
def P(n): return 'parent().par.' + n

COMP = 'MAT_jelly'; c = new_comp(COMP)
add_pars(c, [
    ('Preview', 'menu', [('torus', 'Torus'), ('fat', 'Fat torus')], 1),
    ('Tint', 'rgb', (1.0, 0.18, 0.12)),
    ('Deepcolor', 'rgb', (0.9, 0.05, 0.03)),
    ('Wrap', 'float', 0.6, 0, 1.5),
    ('Translucency', 'float', 1.8, 0, 3),
    ('Rimglow', 'float', 0.7, 0, 3),
    ('Absorption', 'float', 0.9, 0, 4),
    ('Thickness', 'float', 1.0, 0.1, 3),
    ('Innernoise', 'float', 0.6, 0, 1),
    ('Noisescale', 'float', 2.0, 0.2, 8),
    ('Specpower', 'float', 90, 5, 400),
    ('Envintensity', 'float', 1.0, 0, 3),
    ('Jiggle', 'float', 0.12, 0, 0.5),
    ('Jigglefreq', 'float', 3.0, 0.5, 10),
    ('Jigglespeed', 'int', 2, 0, 8),
    ('Spin', 'int', 1, 0, 4),
    ('Camdistance', 'float', 6.0, 2, 12),
    ('Resolution', 'wh', (1280, 720)),
], page='Material')
vd = mkdat(c, 'vert', rd(COMP, 'vert.glsl')); pd = mkdat(c, 'pix', rd(COMP, 'pix.glsl'))
m = c.create(td.glslMAT, 'mat'); m.par.vdat = vd; m.par.pdat = pd
vecs = [
    ('uJig', [P('Jiggle'), P('Jigglefreq'), P('Jigglespeed'), PH]),
    ('uJelly', [P('Wrap'), P('Translucency'), P('Rimglow'), P('Absorption')]),
    ('uCol', [P('Tintr'), P('Tintg'), P('Tintb'), P('Thickness')]),
    ('uCol2', [P('Deepcolorr'), P('Deepcolorg'), P('Deepcolorb'), P('Specpower')]),
    ('uEnv', [P('Envintensity'), P('Innernoise'), PH, P('Noisescale')]),
]
m.seq.vec.numBlocks = len(vecs)
for i, (n, vs) in enumerate(vecs):
    m.par['vec%dname' % i] = n
    for j, v in enumerate(vs):
        p = m.par['vec%dvalue%s' % (i, 'xyzw'[j])]
        if isinstance(v, str): p.expr = v
        else: p.val = v
tor = c.create(td.torusSOP, 'torus'); tor.par.rows = 96; tor.par.cols = 192; tor.par.radx = 1.1; tor.par.rady = 0.45
fat = c.create(td.torusSOP, 'fat'); fat.par.rows = 96; fat.par.cols = 192; fat.par.radx = 0.8; fat.par.rady = 0.7
sws = c.create(td.switchSOP, 'shape'); sws.inputConnectors[0].connect(tor); sws.inputConnectors[1].connect(fat)
sws.par.input.expr = "parent().par.Preview.menuIndex"
geo = c.create(td.geometryCOMP, 'geo')
for ch in list(geo.children): ch.destroy()
geo.par.material = m
sel = geo.create(td.selectSOP, 'sel'); sel.par.sops = sws; sel.display = True; sel.render = True
geo.par.ry.expr = "360*" + PH + "*parent().par.Spin"
geo.par.rx.val = 25
cam = c.create(td.cameraCOMP, 'cam'); cam.par.tz.expr = "parent().par.Camdistance"
r = c.create(td.renderTOP, 'render'); r.par.camera = cam; r.par.geometry = geo; r.par.lights = ''
r.par.outputresolution = 'custom'; r.par.resolutionw.expr = P('Resolutionw'); r.par.resolutionh.expr = P('Resolutionh')
r.par.bgcolorr = 0.0; r.par.bgcolorg = 0.0; r.par.bgcolorb = 0.0; r.par.bgcolora = 1
r.par.antialias = 'aa4'
o = c.create(td.outTOP, 'out1'); o.comment = 'preview'; o.inputConnectors[0].connect(r)
finish(c, COMP)
report(c)
