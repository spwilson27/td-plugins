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

# ---- loop helpers (batch 2) ----
def loop_page(c, seconds=8.0, beats=16):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]
    p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute Time', 'Phase (external)']
    p.default = 'abstime'; p.val = 'abstime'
    pg.appendCHOP('Clock')
    p = pg.appendFloat('Phase')[0]; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.default = 0; p.val = 0
    p = pg.appendFloat('Loopseconds')[0]; p.min = 0.5; p.max = 120; p.normMin = 1; p.normMax = 60; p.default = seconds; p.val = seconds
    p = pg.appendInt('Loopbeats')[0]; p.min = 1; p.max = 256; p.normMin = 1; p.normMax = 64; p.default = beats; p.val = beats
    p = pg.appendFloat('Bpm')[0]; p.min = 20; p.max = 300; p.normMin = 60; p.normMax = 200; p.default = 120; p.val = 120
    p = pg.appendToggle('Usebeats')[0]; p.default = False; p.val = False
    return pg

def make_clock(c):
    """constant CHOP 'clock': len (loop seconds), ph (0-1 phase), t (seconds, = ph*len in phase mode)"""
    k = c.create(td.constantCHOP, 'clock')
    P = 'parent().par.'
    PHS = "(float(parent().par.Clock.eval()['phase']) if parent().par.Clock.eval() else parent().par.Phase)"
    L = "((%sLoopbeats*60.0/%sBpm) if %sUsebeats else %sLoopseconds)" % (P, P, P, P)
    exprs = [('len', L),
             ('ph', "((absTime.seconds/%s)%%1.0) if %sTimesource=='abstime' else %s" % (L, P, PHS)),
             ('t', "absTime.seconds if %sTimesource=='abstime' else %s*%s" % (P, PHS, L))]
    k.par.name0 = 'len'; k.par.value0.expr = exprs[0][1]
    k.par.name1 = 'ph'; k.par.value1.expr = exprs[1][1]
    k.par.name2 = 't'; k.par.value2.expr = exprs[2][1]
    return k
CLK_PH = "op('clock')['ph']"
CLK_T = "op('clock')['t']"

COMP = 'POP_mesh_deformer'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Source','menu',[('sphere','Sphere'),('torus','Torus'),('input','Input POP (in1)')],2),
 ('Detail','int',160,24,400),
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
], page='Render')
loop_page(c, 12.0, 24)
clk = make_clock(c)
P = 'parent().par.'
PH = CLK_PH
ang = "2*math.pi*"+PH

# ---- modulation inputs
inc = c.create(td.inCHOP, 'in3'); inc.par.connectorder = 3
inp = c.create(td.inPOP, 'in1'); inp.par.connectorder = 1
fake = c.create(td.constantCHOP, 'fakemod')
fk = [("0.5+0.5*math.cos(2*math.pi*4*%s)" % PH),                       # kick-ish
      ("(0.5+0.5*math.sin(2*math.pi*(1*%s)))**1.5" % PH),
      ("(0.5+0.5*math.sin(2*math.pi*(3*%s+0.2)))**3" % PH),
      ("(0.5+0.5*math.sin(2*math.pi*(2*%s+0.6)))*(0.5+0.5*math.sin(2*math.pi*5*%s))" % (PH, PH))]
fk[0] = "abs(math.sin(math.pi*4*%s))**6" % PH
for i, e in enumerate(fk):
    getattr(fake.par, 'name%d' % i).val = 'band%d' % (i+1)
    getattr(fake.par, 'value%d' % i).expr = e
msw = c.create(td.switchCHOP, 'modsw')
msw.inputConnectors[0].connect(fake); msw.inputConnectors[1].connect(inc)
msw.par.index.expr = "1 if parent().inputConnectors[2].connections else 0"
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

# ---- source geometry
sp = c.create(td.spherePOP, 'src_sphere'); sp.par.type = 'sharedpoles'; sp.par.surftype = 'triangles'
sp.par.radx = 1; sp.par.rady = 1; sp.par.radz = 1; sp.par.normal = True
sp.par.cols.expr = P+'Detail*2'; sp.par.rows.expr = P+'Detail'
tr = c.create(td.torusPOP, 'src_torus'); tr.par.surftype = 'triangles'
tr.par.radx = 0.9; tr.par.rady = 0.38; tr.par.normal = True
tr.par.cols.expr = P+'Detail*2'; tr.par.rows.expr = P+'Detail'
sw = c.create(td.switchPOP, 'src_switch')
sw.inputConnectors[0].connect(sp); sw.inputConnectors[1].connect(tr); sw.inputConnectors[2].connect(inp)
sw.par.index.expr = "(2 if parent().inputConnectors[0].connections else 0) if %sSource=='input' else (1 if %sSource=='torus' else 0)" % (P, P)
n0 = c.create(td.normalPOP, 'normals_in'); n0.inputConnectors[0].connect(sw)

# ---- deform
dd = mkdat(c, 'deform_code', rd(name, 'deform.glsl'))
g = c.create(td.glslPOP, 'deform'); g.inputConnectors[0].connect(n0)
g.par.computedat = dd; g.par.outputattrs = 'P'
g.seq.vec.numBlocks = 3
for i, (nm, vals) in enumerate([('uA',[F('twist'),F('bend'),F('inflate'),F('noise')]),
                                ('uB',[F('ripple'), ang, P+'Noisefreq', P+'Ripplefreq']),
                                ('uC',[P+'Ripplecycles', P+'Noisecycles', 0, 0])]):
    getattr(g.par, 'vec%dname' % i).val = nm
    getattr(g.par, 'vec%dtype' % i).val = 'vec4'
    for j, v in enumerate(vals):
        p = getattr(g.par, 'vec%dvalue%s' % (i, 'xyzw'[j]))
        if isinstance(v, str): p.expr = v
        else: p.val = v
n1 = c.create(td.normalPOP, 'normals_out'); n1.inputConnectors[0].connect(g)
o2 = c.create(td.nullPOP, 'out2'); o2.comment = 'deformed mesh'; o2.inputConnectors[0].connect(n1)

# ---- studio look
env = glsl(c, 'envmap', open(os.path.join(ROOT,'components','_lib','env.glsl')).read(),
           vecs=[('uA',[P+'Envintensity', P+'Redaccent', 0, 0])], fmt='rgba16float')
env.par.outputresolution = 'custom'; env.par.resolutionw = 1024; env.par.resolutionh = 512
inenv = c.create(td.inTOP, 'in2'); inenv.par.connectorder = 2
esw = c.create(td.switchTOP, 'env_switch'); esw.inputConnectors[0].connect(env); esw.inputConnectors[1].connect(inenv)
esw.par.index.expr = "1 if parent().inputConnectors[1].connections else 0"

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = o2
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
el = c.create(td.environmentlightCOMP, 'envlight'); el.par.envlightmap = esw
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
o = c.create(td.nullTOP, 'out1'); o.comment = 'render'; o.inputConnectors[0].connect(rt)
finish(c, name)
report(c)
