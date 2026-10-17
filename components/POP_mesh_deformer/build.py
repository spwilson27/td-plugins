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

def mcomb(c, name, src, consts, steps, angle='rad', delete=''):
    """Math Combine POP built from plain data.  consts: [(name, 'float'|'float3', [number or expression string, ...])]
    steps: [(operation, A, B, C, result attribute)]: each step reads attributes/constants and writes one attribute."""
    mc = c.create(td.mathcombinePOP, name)
    if src is not None: mc.inputConnectors[0].connect(src)
    mc.par.angleunit = angle
    mc.seq.vec.numBlocks = len(consts)
    for k, (nm, ty, vals) in enumerate(consts):
        getattr(mc.par, 'vec%dname' % k).val = nm; getattr(mc.par, 'vec%dtype' % k).val = ty
        for q, v in enumerate(vals):
            p_ = getattr(mc.par, 'vec%dvalue%d' % (k, q))
            if isinstance(v, str): p_.expr = v
            else: p_.val = v
    mc.seq.comb.numBlocks = len(steps)
    for k, (op_, a_, b_, c_, res) in enumerate(steps):
        getattr(mc.par, 'comb%doper' % k).val = op_
        getattr(mc.par, 'comb%dscopea' % k).val = a_; getattr(mc.par, 'comb%dscopeb' % k).val = b_
        getattr(mc.par, 'comb%dscopec' % k).val = c_; getattr(mc.par, 'comb%dresult' % k).val = res
    if delete: mc.par.delattrs = delete
    return mc

COMP = 'POP_mesh_deformer'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Twist','float',0.6,-4,4),
 ('Bend','float',0.35,-2,2),
 ('Inflate','float',0.12,-1,1.5),
 ('Noiseshell','float',0.25,0,1.5),
 ('Noisefreq','float',1.6,0.2,6),
 ('Ripple','float',0.35,0,2),
 ('Ripplefreq','float',9.0,1,30),
 ('Ripplecycles','int',2,0,8),
 ('Noisecycles','int',1,0,4),
 ('Modgain','float',1.0,0,3),
])
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Demoshape','menu',[('sphere','Sphere'),('torus','Torus')],1),
 ('Detail','int',160,24,400),
 ('Metallic','float',1.0,0,1),
 ('Roughness','float',0.28,0.02,1),
 ('Basecolor','rgb',(0.86,0.86,0.88)),
 ('Envintensity','float',1.0,0,4),
 ('Redaccent','float',0.7,0,1),
 ('Keyintensity','float',0.6,0,4),
 ('Camdist','float',6.0,1,20),
 ('Camheight','float',0.6,-4,6),
 ('Orbitturns','int',1,0,4),
 ('Fov','float',50,10,90),
 ('Bgcolor','rgb',(0.006,0.006,0.008)),
], page='Preview')
P = 'parent().par.'
PH = "(absTime.seconds/12.0)"      # internal preview animation (no loop parameters)
ang = "2*math.pi*"+PH

# ---- inputs: in1 POP, in2 modulation CHOP (band1..band4, beat)
inp = c.create(td.inPOP, 'in1'); inp.par.connectorder = 1
inc = c.create(td.inCHOP, 'in2'); inc.par.connectorder = 2
CON = "(len(parent().inputConnectors[0].connections)+0*absTime.frame)>0"
CONM = "(len(parent().inputConnectors[1].connections)+0*absTime.frame)>0"

# ---- demo COMP: preview-only sources (demo shape + fake audio bands); not selected when in1 is connected
demo = c.create(td.baseCOMP, 'demo')
PP = 'parent(2).par.'
sp = demo.create(td.spherePOP, 'src_sphere'); sp.par.type = 'sharedpoles'; sp.par.surftype = 'triangles'
sp.par.radx = 1; sp.par.rady = 1; sp.par.radz = 1; sp.par.normal = True
sp.par.cols.expr = PP+'Detail*2'; sp.par.rows.expr = PP+'Detail'
tr = demo.create(td.torusPOP, 'src_torus'); tr.par.surftype = 'triangles'
tr.par.radx = 0.9; tr.par.rady = 0.38; tr.par.normal = True
tr.par.cols.expr = PP+'Detail*2'; tr.par.rows.expr = PP+'Detail'
dsw = demo.create(td.switchPOP, 'shape'); dsw.inputConnectors[0].connect(sp); dsw.inputConnectors[1].connect(tr)
dsw.par.index.expr = "1 if %sDemoshape=='torus' else 0" % PP
dshape = demo.create(td.outPOP, 'out1'); dshape.inputConnectors[0].connect(dsw)
fake = demo.create(td.constantCHOP, 'fakemod')
T = "(absTime.seconds/12.0)"
fk = ["abs(math.sin(math.pi*4*%s))**6" % T,
      "(0.5+0.5*math.sin(2*math.pi*(1*%s)))**1.5" % T,
      "(0.5+0.5*math.sin(2*math.pi*(3*%s+0.2)))**3" % T,
      "(0.5+0.5*math.sin(2*math.pi*(2*%s+0.6)))*(0.5+0.5*math.sin(2*math.pi*5*%s))" % (T, T)]
for i, e in enumerate(fk):
    getattr(fake.par, 'name%d' % i).val = 'band%d' % (i+1)
    getattr(fake.par, 'value%d' % i).expr = e
dmod = demo.create(td.outCHOP, 'out2'); dmod.inputConnectors[0].connect(fake)

src = c.create(td.switchPOP, 'src_switch')
src.inputConnectors[0].connect(demo.outputConnectors[0]); src.inputConnectors[1].connect(inp)
src.par.index.expr = "1 if %s else 0" % CON
n0 = c.create(td.normalPOP, 'normals_in'); n0.inputConnectors[0].connect(src)

zero = c.create(td.constantCHOP, 'mod_zero')
for i in range(4):
    getattr(zero.par, 'name%d' % i).val = 'band%d' % (i+1); getattr(zero.par, 'value%d' % i).val = 0
msw = c.create(td.switchCHOP, 'modsw')
msw.inputConnectors[0].connect(zero); msw.inputConnectors[1].connect(inc); msw.inputConnectors[2].connect(demo.outputConnectors[1])
msw.par.index.expr = "1 if %s else (0 if %s else 2)" % (CONM, CON)   # demo bands only when nothing is connected
fin = c.create(td.constantCHOP, 'final')
def band(i): return "(op('modsw')['band%d'] or 0)" % i
G = P + 'Modgain'
amts = [('twist', P+'Twist', "%s*%s"%(G,band(2))),
        ('bend', P+'Bend', "%s*%s*0.5"%(G,band(1))),
        ('inflate', P+'Inflate', "%s*%s*0.35"%(G,band(1))),
        ('noise', P+'Noiseshell', "%s*%s*0.5"%(G,band(4))),
        ('ripple', P+'Ripple', "%s*%s*0.8"%(G,band(3)))]
for i, (nm, base, md) in enumerate(amts):
    getattr(fin.par, 'name%d' % i).val = nm
    getattr(fin.par, 'value%d' % i).expr = "%s + %s" % (base, md)
def F(n): return "op('final')['%s']" % n

# ---- deform: built from native POPs (noise/ripple/inflate, then twist, bend)
# noise shell: 3D noise (2 octaves) written to the point attribute 'nv'. It travels on a circle in noise space so it loops.
nz = c.create(td.noisePOP, 'noise_shell'); nz.inputConnectors[0].connect(n0)
nz.par.type = 'simplex3d'; nz.par.harmon = 2; nz.par.spread = 2.1; nz.par.gain = 0.5
nz.par.period.expr = "2.0/%sNoisefreq" % P
nz.par.amp0 = 1; nz.par.combineop = 'none'; nz.par.noise = True; nz.par.noiseoutputattrscope = 'nv'
nth = "%s*%sNoisecycles" % (ang, P)
nz.par.tx.expr = "0.45*math.cos(%s)" % nth; nz.par.ty.expr = "0.45*math.sin(%s)" % nth
nz.par.tz.expr = "0.45*0.37*math.cos(2*%s)" % nth
# one Math Combine POP does all the arithmetic, as a list of steps:
#  1. ripples (sin of the distance from the top pole, fading out), inflate and noise, summed into one push along the normal:
#     P += N * (ripple wave * fade * Ripple*0.25 + Inflate*0.5 + noise attr * 0.44 * Noiseshell)
#  2. twist about Y:  rotate (x, z) by Twist * y
#  3. bend: rotate (x, y) by Bend * x, so the shape curls
mc = mcomb(c, 'deform', nz,
  [('pole', 'float3', [0, 1, 0]), ('ripplefreq', 'float', [P+'Ripplefreq']),
   ('ripplephase', 'float', ["-%s*%sRipplecycles" % (ang, P)]), ('ripplefade', 'float', [-0.25]),
   ('rippleamp', 'float', [F('ripple') + "*0.25"]), ('inflateamt', 'float', [F('inflate') + "*0.5"]),
   ('noiseamp', 'float', ["0.44*" + F('noise')]),
   ('twistamt', 'float', [F('twist')]), ('bendamt', 'float', [F('bend')])],
  [('asubb', 'P', 'pole', '', 'fromPole'),          # vector from the pole to the point
   ('length', 'fromPole', '', '', 'dist'),          # distance to the pole
   ('amultbaddc', 'dist', 'ripplefreq', 'ripplephase', 'wavearg'),
   ('sin', 'wavearg', '', '', 'wave'),
   ('mult', 'dist', 'ripplefade', '', 'fadearg'),
   ('exp', 'fadearg', '', '', 'fade'),
   ('mult', 'wave', 'fade', '', 'ripple'),
   ('amultbaddc', 'ripple', 'rippleamp', 'inflateamt', 'pushA'),
   ('amultbaddc', 'nv', 'noiseamp', 'pushA', 'push'),
   ('aaddbmultc', 'P', 'N', 'push', 'P'),
   # twist: angle = Twist * y;  x' = x cos a + z sin a,  z' = z cos a - x sin a
   ('mult', 'P.y', 'twistamt', '', 'tangle'), ('cos', 'tangle', '', '', 'tc'), ('sin', 'tangle', '', '', 'ts'), ('negatea', 'ts', '', '', 'nts'),
   ('mult', 'P.x', 'tc', '', 'xtc'), ('aaddbmultc', 'xtc', 'P.z', 'ts', 'twx'),
   ('mult', 'P.z', 'tc', '', 'ztc'), ('aaddbmultc', 'ztc', 'P.x', 'nts', 'twz'),
   ('copya', 'twx', '', '', 'P.x'), ('copya', 'twz', '', '', 'P.z'),
   # bend: angle = Bend * x;  x' = x cos b + y sin b,  y' = y cos b - x sin b
   ('mult', 'P.x', 'bendamt', '', 'bangle'), ('cos', 'bangle', '', '', 'bc'), ('sin', 'bangle', '', '', 'bs'), ('negatea', 'bs', '', '', 'nbs'),
   ('mult', 'P.x', 'bc', '', 'xbc'), ('aaddbmultc', 'xbc', 'P.y', 'bs', 'bnx'),
   ('mult', 'P.y', 'bc', '', 'ybc'), ('aaddbmultc', 'ybc', 'P.x', 'nbs', 'bny'),
   ('copya', 'bnx', '', '', 'P.x'), ('copya', 'bny', '', '', 'P.y')],
  delete='fromPole dist wavearg wave fadearg fade ripple pushA push tangle tc ts nts xtc twx ztc twz bangle bc bs nbs xbc bnx ybc bny nv')
n1 = c.create(td.normalPOP, 'normals_out'); n1.inputConnectors[0].connect(mc)
o1 = c.create(td.nullPOP, 'out1'); o1.comment = 'deformed mesh'; o1.inputConnectors[0].connect(n1)

# ---- internal preview render (studio chrome)
env = glsl(c, 'envmap', open(os.path.join(ROOT,'components','_lib','env.glsl')).read(),
           vecs=[('uA',[P+'Envintensity', P+'Redaccent', 0, 0])], fmt='rgba16float')
env.par.outputresolution = 'custom'; env.par.resolutionw = 1024; env.par.resolutionh = 512

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = o1
sel.display = True; sel.render = True
mat = c.create(td.pbrMAT, 'mat')
mat.par.basecolorr.expr = P+'Basecolorr'; mat.par.basecolorg.expr = P+'Basecolorg'; mat.par.basecolorb.expr = P+'Basecolorb'
mat.par.metallic.expr = P+'Metallic'; mat.par.roughness.expr = P+'Roughness'
geo.par.material = mat

cam = c.create(td.cameraCOMP, 'cam')
tgt = c.create(td.nullCOMP, 'target')
cam.par.tx.expr = "math.sin(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.tz.expr = "math.cos(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.ty.expr = P+'Camheight'
cam.par.fov.expr = P+'Fov'
cam.par.lookat = tgt
el = c.create(td.environmentlightCOMP, 'envlight'); el.par.envlightmap = env
el.par.dimmer = 1
key = c.create(td.lightCOMP, 'key'); key.par.tx = -3; key.par.ty = 4; key.par.tz = 3; key.par.lookat = tgt
key.par.dimmer.expr = P+'Keyintensity'; key.par.shadowtype = 'off'
rim = c.create(td.lightCOMP, 'rim'); rim.par.tx = 3.5; rim.par.ty = 1.5; rim.par.tz = -4; rim.par.lookat = tgt
rim.par.cr = 1; rim.par.cg = 0.15; rim.par.cb = 0.1; rim.par.dimmer.expr = P+'Redaccent*0.8'; rim.par.shadowtype = 'off'
rt = c.create(td.renderTOP, 'render')
rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = 'envlight key rim'
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr.expr = P+'Bgcolorr'; rt.par.bgcolorg.expr = P+'Bgcolorg'; rt.par.bgcolorb.expr = P+'Bgcolorb'; rt.par.bgcolora = 1
rt.par.antialias = 'aa4'; rt.par.format = 'rgba16float'
o = c.create(td.nullTOP, 'preview'); o.comment = 'preview render'; o.inputConnectors[0].connect(rt)
finish(c, name)
report(c)
