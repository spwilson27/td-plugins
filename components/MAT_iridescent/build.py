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
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
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

# ---- loop helper (matl) ----
def add_loop(c):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]; p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute time', 'Phase (loop)']
    p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1
    pg.appendCHOP('Clock')
    p = pg.appendFloat('Loopseconds')[0]; p.default = 8; p.val = 8; p.min = 0.1; p.max = 120; p.normMin = 0.1; p.normMax = 60; p.clampMin = True
    p = pg.appendInt('Loopbeats')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 128; p.normMin = 0; p.normMax = 32; p.clampMin = True
    p = pg.appendFloat('Bpm')[0]; p.default = 120; p.val = 120; p.min = 20; p.max = 300; p.normMin = 20; p.normMax = 300
PH = ("((float(parent().par.Clock.eval()['phase']) if parent().par.Clock.eval() else parent().par.Phase) if parent().par.Timesource=='phase' else absTime.seconds/"
      "(parent().par.Loopseconds if parent().par.Loopbeats==0 else parent().par.Loopbeats*60.0/parent().par.Bpm))")
def P(n): return 'parent().par.' + n

COMP = 'MAT_iridescent'; c = new_comp(COMP)
add_pars(c, [
    ('Preview', 'menu', [('torus', 'Torus'), ('fat', 'Fat torus')], 0),
    ('Filmthickness', 'float', 380, 50, 1200),
    ('Filmvariation', 'float', 220, 0, 800),
    ('Filmior', 'float', 1.45, 1.05, 2.6),
    ('Substrateior', 'float', 1.9, 1.05, 4),
    ('Iridescence', 'float', 1.0, 0, 1),
    ('Fresnelpower', 'float', 2.5, 0.5, 8),
    ('Sheen', 'float', 0.9, 0, 3),
    ('Anisotropy', 'float', 0.8, 0, 1),
    ('Sheenexp', 'float', 40, 2, 300),
    ('Brushangle', 'float', 0.0, 0, 1),
    ('Oilscale', 'float', 1.2, 0.1, 6),
    ('Oilmotion', 'float', 0.8, 0, 3),
    ('Basecolor', 'rgb', (0.02, 0.02, 0.025)),
    ('Roughness', 'float', 0.1, 0, 1),
    ('Envrotation', 'float', 0.0, -1, 1),
    ('Envintensity', 'float', 1.0, 0, 4),
    ('Spin', 'int', 1, 0, 4),
    ('Camdistance', 'float', 6.0, 2, 12),
    ('Resolution', 'wh', (1280, 720)),
], page='Material')
add_loop(c)
envin = c.create(td.inTOP, 'in1')
dflt = c.create(td.constantTOP, 'defenv'); dflt.par.outputresolution = 'custom'; dflt.par.resolutionw = 64; dflt.par.resolutionh = 32
envsw = c.create(td.switchTOP, 'envsrc'); envsw.inputConnectors[0].connect(dflt); envsw.inputConnectors[1].connect(envin)
envsw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
envsw.par.format = 'rgba16float'
vd = mkdat(c, 'vert', rd(COMP, 'vert.glsl')); pd = mkdat(c, 'pix', rd(COMP, 'pix.glsl'))
m = c.create(td.glslMAT, 'mat'); m.par.vdat = vd; m.par.pdat = pd
m.par.sampler0name = 'sEnv'; m.par.sampler0top = envsw
m.par.sampler0filter = 'mipmaplinear'
vecs = [
    ('uFilm', [P('Filmthickness'), P('Filmvariation'), P('Filmior'), P('Iridescence')]),
    ('uOil', [P('Oilscale'), P('Oilmotion'), PH, 0]),
    ('uSheen', [P('Sheen'), P('Anisotropy'), P('Sheenexp'), P('Fresnelpower')]),
    ('uEnv', [P('Envrotation'), "1 if parent().inputConnectors[0].connections else 0", P('Envintensity'), P('Roughness')]),
    ('uBase', [P('Basecolorr'), P('Basecolorg'), P('Basecolorb'), P('Substrateior')]),
    ('uExtra', [P('Brushangle'), 0, 0, 0]),
]
m.seq.vec.numBlocks = len(vecs)
for i, (n, vs) in enumerate(vecs):
    m.par['vec%dname' % i] = n
    for j, v in enumerate(vs):
        p = m.par['vec%dvalue%s' % (i, 'xyzw'[j])]
        if isinstance(v, str): p.expr = v
        else: p.val = v
# preview geometry
tor = c.create(td.torusSOP, 'torus'); tor.par.rows = 96; tor.par.cols = 192; tor.par.radx = 1.1; tor.par.rady = 0.45
sph = c.create(td.torusSOP, 'fat'); sph.par.rows = 96; sph.par.cols = 192; sph.par.radx = 0.8; sph.par.rady = 0.7
sws = c.create(td.switchSOP, 'shape'); sws.inputConnectors[0].connect(tor); sws.inputConnectors[1].connect(sph)
sws.par.input.expr = "parent().par.Preview.menuIndex"
geo = c.create(td.geometryCOMP, 'geo'); 
for ch in list(geo.children): ch.destroy()
sn = geo.create(td.inSOP, 'in1') if False else None
geo.par.material = m
# put SOP inside geo via object reference: use a Select SOP inside geo
sel = geo.create(td.selectSOP, 'sel'); sel.par.sops = sws
sel.display = True; sel.render = True
geo.par.ry.expr = "360*" + PH + "*parent().par.Spin"
geo.par.rx.val = 25
cam = c.create(td.cameraCOMP, 'cam'); cam.par.tz.expr = "parent().par.Camdistance"; cam.par.ty = 0.0
r = c.create(td.renderTOP, 'render'); r.par.camera = cam; r.par.geometry = geo; r.par.lights = ''
r.par.outputresolution = 'custom'; r.par.resolutionw.expr = P('Resolutionw'); r.par.resolutionh.expr = P('Resolutionh')
r.par.bgcolorr = 0.0; r.par.bgcolorg = 0.0; r.par.bgcolorb = 0.0; r.par.bgcolora = 1
r.par.antialias = 'aa4' if 'aa4' in r.par.antialias.menuNames else r.par.antialias.eval()
o = c.create(td.outTOP, 'out1'); o.comment = 'preview'; o.inputConnectors[0].connect(r)
finish(c, COMP)
report(c)
print('menu aa', r.par.antialias.menuNames, m.par.sampler0filter.menuNames)
