import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read())
import math
# ---- native-build helpers (natB) ----
import math
def mk(par, typ, name, ins=(), **kw):
    """create op, set params. value str starting with '=' -> expression; tuple/list for menus not needed."""
    o = par.create(typ, name)
    for k, v in kw.items():
        p = getattr(o.par, k)
        if isinstance(v, str) and v.startswith('='):
            p.expr = v[1:]
        else:
            p.val = v
    for i, s in enumerate(ins):
        if s is not None:
            o.inputConnectors[i].connect(s.outputConnectors[0] if getattr(s, 'isCOMP', False) else s)
    return o
def resx(o, par_expr_w="op('res')['w']", par_expr_h="op('res')['h']"):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = par_expr_w; o.par.resolutionh.expr = par_expr_h
    return o
def keys_dat(par, name, rows):
    d = par.create(td.tableDAT, name)
    d.clear(); d.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for r in rows: d.appendRow([('%.5g' % x) for x in r])
    return d
def ramp_from(par, name, rows, w=1024, h=1, typ='horizontal', **kw):
    d = keys_dat(par, name + '_keys', rows)
    r = par.create(td.rampTOP, name)
    r.par.dat = d; r.par.type = typ
    r.par.extendleft = 'hold'; r.par.extendright = 'hold'
    r.par.outputresolution = 'custom'; r.par.resolutionw = w; r.par.resolutionh = h
    r.par.format = 'rgba16float'
    for k, v in kw.items():
        p = getattr(r.par, k)
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        else: p.val = v
    return r
def smooth(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

COMP = 'TOP_depth_fog'
c = new_comp(COMP)
add_pars(c, [
    ('Depthmode', 'menu', [('linear', 'Linear eye-space z'), ('nonlinear', 'Render TOP depth (0-1)')], 0),
    ('Near', 'float', 0.5, 0.001, 100),
    ('Far', 'float', 100, 1, 10000),
    ('Depthscale', 'float', 1.0, 0.0001, 1000),
    ('Fogmode', 'menu', [('exp', 'Exponential'), ('exp2', 'Exponential squared'), ('linear', 'Linear')], 1),
    ('Density', 'float', 0.03, 0, 1),
    ('Start', 'float', 8, 0, 500),
    ('End', 'float', 60, 0.1, 1000),
    ('Fogamount', 'float', 1.0, 0, 1, True),
    ('Fov', 'float', 40, 1, 170),
    *COMMON,
])
add_pars(c, [
    ('Fogcolor', 'rgb', (0.42, 0.47, 0.56)),
    ('Heightfog', 'toggle', 1),
    ('Heightbase', 'float', -1.3, -100, 100),
    ('Heightfalloff', 'float', 0.25, 0.001, 5),
    ('Heightdensity', 'float', 0.06, 0, 2),
    ('Camheight', 'float', 3.2, -100, 100),
    ('Campitch', 'float', 14.0, -89, 89),
], page='Fog')
add_pars(c, [
    ('Glow', 'float', 0.55, 0, 5),
    ('Glowwidth', 'float', 0.09, 0.01, 1),
    ('Glowcolor', 'rgb', (1.0, 0.62, 0.35)),
    ('Skyblend', 'float', 1.0, 0, 1, True),
], page='Look')
P = 'parent().par.'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2')

# ------------------------------------------------------------------ demo scene (native, gated): Phong shapes + sky, depth from a Depth TOP
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only G-buffer scene (used while in1 is unconnected; does not cook otherwise)'
R = ("op('../res')['w']", "op('../res')['h']")
mats = {}
for nm, col in (('floor', (0.62, 0.6, 0.56)), ('sphere', (0.85, 0.25, 0.2)), ('torus', (0.2, 0.55, 0.85)), ('box', (0.9, 0.8, 0.3))):
    m = d.create(td.phongMAT, 'mat_' + nm)
    m.par.diffr, m.par.diffg, m.par.diffb = col
    m.par.ambr, m.par.ambg, m.par.ambb = [v * 0.25 for v in col]
    m.par.specr = m.par.specg = m.par.specb = 0.25; m.par.shininess = 40
    mats[nm] = m
geos = []
def geo(nm, mkpop, setup, mat, tx, ty, tz, rx=0, ry=0, rz=0):
    g = d.create(td.geometryCOMP, 'geo_' + nm)
    for ch in list(g.children): ch.destroy()
    s = g.create(mkpop, 'shape'); setup(s)
    s.display = True; s.render = True
    g.par.material = mat
    for k, e in (('tx', tx), ('ty', ty), ('tz', tz), ('rx', rx), ('ry', ry), ('rz', rz)):
        if isinstance(e, str): g.par[k].expr = e
        else: g.par[k] = e
    geos.append(g)
T = 'absTime.seconds'
def sph(s): s.par.type = 'sharedpoles'; s.par.rows = 40; s.par.cols = 64; s.par.normal = 'pointNormals'; s.par.radx = s.par.rady = s.par.radz = 1.2
def tor(s): s.par.rows = 36; s.par.cols = 72; s.par.normal = 'pointNormals'; s.par.radx = 1.25; s.par.rady = 0.5
def bx(s): s.par.sizex = s.par.sizey = s.par.sizez = 1.7; s.par.uniquepoints = True; s.par.normal = 'pointNormals'
def fl(s): s.par.sizex = 80; s.par.sizey = 0.2; s.par.sizez = 80; s.par.uniquepoints = True; s.par.normal = 'pointNormals'
geo('floor', td.boxPOP, fl, mats['floor'], 0, -1.3, 0)
geo('sphere', td.spherePOP, sph, mats['sphere'], -2.4, 'math.sin(%s*0.9)*0.25' % T, -0.5)
geo('torus', td.torusPOP, tor, mats['torus'], 0.3, 'math.cos(%s*0.7)*0.2-0.1' % T, 1.4, rx='62+%s*18' % T, ry='%s*25' % T)
geo('box', td.boxPOP, bx, mats['box'], 2.7, -0.3, -1.6, ry='%s*30+20' % T, rx='%s*12' % T)
cam = d.create(td.cameraCOMP, 'cam')
cam.par.tz = 13.0; cam.par.ty = 3.2; cam.par.rx = -math.degrees(math.atan2(3.2, 13.0)) * 0.8
cam.par.fov = 40; cam.par.near = 0.5; cam.par.far = 100
lt = d.create(td.lightCOMP, 'light'); lt.par.tx = -5; lt.par.ty = 8; lt.par.tz = 6
rnd = d.create(td.renderTOP, 'render')
rnd.par.camera = cam; rnd.par.geometry = ' '.join(g.name for g in geos); rnd.par.lights = lt
rnd.par.outputresolution = 'custom'; rnd.par.resolutionw.expr = R[0]; rnd.par.resolutionh.expr = R[1]
rnd.par.format = 'rgba16float'; rnd.par.bgcolorr = rnd.par.bgcolorg = rnd.par.bgcolorb = rnd.par.bgcolora = 0
def smooth(a, b, x):
    t_ = min(1, max(0, (x - a) / (b - a))); return t_ * t_ * (3 - 2 * t_)
sk_keys = []
for k in range(13):
    y = k / 12; h = smooth(0.5, 0.86, y)
    sk_keys.append((y,) + tuple((1 - h) * a_ + h * b_ for a_, b_ in zip((0.5, 0.46, 0.46), (0.08, 0.14, 0.30))) + (1,))
kd = d.create(td.tableDAT, 'sky_keys'); kd.clear(); kd.appendRow(['pos', 'r', 'g', 'b', 'a'])
for r_ in sk_keys: kd.appendRow(['%.4g' % v for v in r_])
sky = d.create(td.rampTOP, 'sky'); sky.par.dat = kd; sky.par.type = 'vertical'; sky.par.extendleft = 'hold'; sky.par.extendright = 'hold'
sky.par.outputresolution = 'custom'; sky.par.resolutionw.expr = R[0]; sky.par.resolutionh.expr = R[1]; sky.par.format = 'rgba16float'
col = d.create(td.compositeTOP, 'color'); col.par.operand = 'over'; col.par.format = 'rgba16float'
col.inputConnectors[0].connect(rnd); col.inputConnectors[1].connect(sky)
dep = d.create(td.depthTOP, 'depth'); dep.par.op = rnd; dep.par.pixelformat = 'r32float'; dep.par.depthspace = 'cameraspace'
dep.par.outputresolution = 'useinput'
for i, (nm, tp) in enumerate((('o_color', col), ('o_depth', dep))):
    o = d.create(td.outTOP, nm); o.inputConnectors[0].connect(tp)
    if hasattr(o.par, 'connectorder'): o.par.connectorder = i
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = '(1 if %s else 0) + 0*absTime.frame' % HAS1
setres(src); src.par.format = 'rgba16float'
fb = c.create(td.constantTOP, 'defdepth')   # in1 connected but no depth: a flat mid-distance depth
setres(fb); fb.par.format = 'rgba16float'
fb.par.colorr.expr = "(%sFar*0.25 if %sDepthmode=='linear' else 0.995)" % (P, P)
fb.par.colorg.expr = fb.par.colorb.expr = fb.par.colorr.expr
fb.par.alpha = 1
dsrc = c.create(td.switchTOP, 'depthsrc')
dsrc.inputConnectors[0].connect(d.outputConnectors[1]); dsrc.inputConnectors[1].connect(fb); dsrc.inputConnectors[2].connect(i2)
dsrc.par.index.expr = "(2 if len(parent().inputConnectors[1].connections) else (1 if %s else 0)) + 0*absTime.frame" % HAS1
setres(dsrc); dsrc.par.format = 'rgba32float'

# ------------------------------------------------------------------ fog falloff curve (native CHOP network, no GPU cost)
# 128 samples of the fog amount f(t) for t = 0 .. Far along the view ray; the three Fogmode branches meet in a Switch CHOP
N = 128
cv = c.create(td.baseCOMP, 'fog_curve')
cv.comment = 'fog amount f(t) for t = 0..Far: exp / exp2 / linear, picked by Fogmode'
pu = cv.create(td.patternCHOP, 'distance')           # u = 0..1 along the ray
pu.par.wavetype = 'ramp'; pu.par.length = N; pu.par.channelname = 'f'
DEN = 'parent(2).par.Density'; FAR = 'parent(2).par.Far'
def mathc(name, src_, **kw):
    m = cv.create(td.mathCHOP, name); m.inputConnectors[0].connect(src_)
    for k, v in kw.items():
        p = getattr(m.par, k)
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        else: p.val = v
    return m
def func(name, src_, fn):
    f = cv.create(td.functionCHOP, name); f.inputConnectors[0].connect(src_); f.par.func = fn; return f
# exp:   f = 1 - exp(-Density * t)
e1 = mathc('exp_arg', pu, gain='=-%s*%s' % (DEN, FAR)); e2 = func('exp_e', e1, 'exp'); e3 = mathc('exp_fog', e2, gain=-1.0, postoff=1.0)
# exp2:  f = 1 - exp(-(Density * t)^2)
q1 = mathc('exp2_arg', pu, gain='=%s*%s' % (DEN, FAR), postop='square'); q1b = mathc('exp2_neg', q1, gain=-1.0)
q2 = func('exp2_e', q1b, 'exp'); q3 = mathc('exp2_fog', q2, gain=-1.0, postoff=1.0)
# linear: f = clamp((t - Start) / (End - Start))
l1 = mathc('lin_arg', pu, preoff='=-parent(2).par.Start/%s' % FAR, gain='=%s/max(parent(2).par.End-parent(2).par.Start,0.0001)' % FAR)
l2 = cv.create(td.limitCHOP, 'lin_fog'); l2.inputConnectors[0].connect(l1); l2.par.type = 'clamp'; l2.par.min = 0; l2.par.max = 1
swc = cv.create(td.switchCHOP, 'curve'); 
for i_, s_ in enumerate((e3, q3, l2)): swc.inputConnectors[i_].connect(s_)
swc.par.index.expr = 'parent(2).par.Fogmode.menuIndex'
cv.create(td.outCHOP, 'out1').inputConnectors[0].connect(swc)

# ------------------------------------------------------------------ GLSL core: depth decode, view rays, height fog, horizon glow, final mix
fog = c.create(td.glslTOP, 'fog')
fog.par.pixeldat = mkdat(c, 'fog_code', rd(COMP, 'fog.glsl'))
fog.inputConnectors[0].connect(src); fog.inputConnectors[1].connect(dsrc)
vecs = [
    ('uA', [P + 'Depthmode.menuIndex', P + 'Near', P + 'Far', P + 'Depthscale']),
    ('uC', [P + 'Fogcolorr', P + 'Fogcolorg', P + 'Fogcolorb', P + 'Fogamount']),
    ('uD', [P + 'Fov', P + 'Camheight', P + 'Campitch', P + 'Skyblend']),
    ('uE', ['1 if %sHeightfog else 0' % P, P + 'Heightbase', P + 'Heightfalloff', P + 'Heightdensity']),
    ('uF', [P + 'Glow', P + 'Glowwidth', 0, 0]),
    ('uG', [P + 'Glowcolorr', P + 'Glowcolorg', P + 'Glowcolorb', 0]),
]
fog.seq.vec.numBlocks = len(vecs)
for i_, (n_, vals) in enumerate(vecs):
    fog.par['vec%dname' % i_] = n_
    for j_, v_ in enumerate(vals):
        q_ = fog.par['vec%dvalue%s' % (i_, 'xyzw'[j_])]
        if isinstance(v_, str): q_.expr = v_
        else: q_.val = v_
fog.seq.array.numBlocks = 1
fog.par.array0name = 'uCurve'; fog.par.array0type = 'float'; fog.par.array0chop = cv.op('curve')
fog.par.format = 'rgba16float'; setres(fog)
finish_v2(c, COMP, fog, src)
report(c)
