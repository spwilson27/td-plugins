# ---- v2: Clock CHOP parameter (Loop page) ----
import td as _td
CLOCK_CB = '''def sync(c):
    clk = c.par.Clock.eval()
    if clk:
        c.par.Phase.expr = "me.par.Clock.eval()['phase'].eval() if me.par.Clock.eval() and me.par.Clock.eval()['phase'] is not None else 0"
    elif c.par.Phase.mode == ParMode.EXPRESSION:
        c.par.Phase.expr = ''
        c.par.Phase.mode = ParMode.CONSTANT
        c.par.Phase.val = 0.0

def onValueChange(par, prev):
    sync(par.owner)
    return
'''
def add_clock(c):
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendCHOP('Clock', label='Clock (CHOP, phase channel)')[0]
    cb = c.create(_td.parameterexecuteDAT, 'clock_exec')
    cb.text = CLOCK_CB
    cb.par.op = '..'; cb.par.pars = 'Clock'; cb.par.valuechange = True; cb.par.onpulse = False
    cb.par.custom = True; cb.par.builtin = False
# ---- end v2 clock ----
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
    L = "((%sLoopbeats*60.0/%sBpm) if %sUsebeats else %sLoopseconds)" % (P, P, P, P)
    exprs = [('len', L),
             ('ph', "((absTime.seconds/%s)%%1.0) if %sTimesource=='abstime' else %sPhase" % (L, P, P)),
             ('t', "absTime.seconds if %sTimesource=='abstime' else %sPhase*%s" % (P, P, L))]
    k.par.name0 = 'len'; k.par.value0.expr = exprs[0][1]
    k.par.name1 = 'ph'; k.par.value1.expr = exprs[1][1]
    k.par.name2 = 't'; k.par.value2.expr = exprs[2][1]
    return k
CLK_PH = "op('clock')['ph']"
CLK_T = "op('clock')['t']"

COMP = 'GEN_tentacles'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Count','int',48,4,300),
 ('Length','float',2.2,0.3,8),
 ('Grow','float',1.0,0,1),
 ('Autogrow','toggle',False),
 ('Segments','int',64,8,200),
 ('Sides','int',12,4,32),
 ('Thickness','float',0.075,0.005,0.4),
 ('Taper','float',0.8,0.1,3),
 ('Tipmin','float',0.04,0,0.5),
 ('Wiggle','float',0.35,0,1.5),
 ('Noisefreq','float',1.3,0.2,5),
 ('Noisecycles','int',1,0,4),
 ('Wave','float',0.07,0,0.5),
 ('Wavefreq','float',2.0,0.5,8),
 ('Wavecycles','int',1,0,4),
 ('Pulse','float',0.18,0,0.8),
 ('Pulsefreq','float',6.0,1,20),
 ('Rootradius','float',0.45,0.05,2),
 ('Core','toggle',True),
])
add_pars(c, [
 ('Metallic','float',1.0,0,1),
 ('Roughness','float',0.22,0.02,1),
 ('Basecolor','rgb',(0.82,0.82,0.85)),
 ('Envintensity','float',1.0,0,4),
 ('Redaccent','float',0.7,0,1),
 ('Keyintensity','float',0.6,0,4),
 ('Camdist','float',9.5,2,30),
 ('Camheight','float',1.2,-8,10),
 ('Orbitturns','int',1,0,4),
 ('Fov','float',50,10,90),
 ('Bgcolor','rgb',(0.006,0.006,0.008)),
], page='Render')
loop_page(c, 12.0, 24)
clk = make_clock(c)
P = 'parent().par.'
PH = CLK_PH
ang = "2*math.pi*"+PH

# template: straight tube, root points
tube = c.create(td.tubePOP, 'tube'); tube.par.orient = 'y'; tube.par.height = 1.0
tube.par.radx = 0.5; tube.par.rady = 0.5; tube.par.endcaps = False
tube.par.cols.expr = P+'Sides'; tube.par.rows.expr = P+'Segments'
roots = c.create(td.pointgeneratorPOP, 'roots'); roots.par.shape = 'sphere'; roots.par.distribution = 'surface'
roots.par.numpoints.expr = P+'Count'
for a in 'xyz': getattr(roots.par, 'radius'+a).expr = P+'Rootradius'
rcol = mkdat(c, 'rootcolor_code', "void main(){ const uint id=TDIndex(); if(id>=TDNumElements()) return; Color[id]=vec4(TDIn_P(),1.0); }")
rg = c.create(td.glslPOP, 'rootattr'); rg.inputConnectors[0].connect(roots); rg.par.computedat = rcol
rg.par.outputattrs = ''; rg.par.attr0name = 'color'
cp = c.create(td.copyPOP, 'copy')
cp.inputConnectors[0].connect(tube); cp.inputConnectors[1].connect(rg)
cp.par.dotemplatetranslate = False
cp.par.doattr = True; cp.par.templateattr0names = 'Color'
dd = mkdat(c, 'tentacle_code', rd(name, 'tentacle.glsl'))
g = c.create(td.glslPOP, 'tentacle'); g.inputConnectors[0].connect(cp)
g.par.computedat = dd; g.par.outputattrs = 'P'
g.seq.vec.numBlocks = 4
grow = "((0.5-0.5*math.cos(%s))**0.7 if %sAutogrow else %sGrow)" % (ang, P, P)
vecs = [('uA',[P+'Length', P+'Wiggle', P+'Thickness', P+'Taper']),
        ('uB',[ang, P+'Noisefreq', P+'Pulse', P+'Pulsefreq']),
        ('uC',[grow, P+'Tipmin', P+'Wavefreq', P+'Wave']),
        ('uD',[P+'Rootradius', P+'Noisecycles', P+'Wavecycles', 0])]
for i,(n2,vals) in enumerate(vecs):
    getattr(g.par,'vec%dname'%i).val = n2
    getattr(g.par,'vec%dtype'%i).val = 'vec4'
    for j,v in enumerate(vals):
        p = getattr(g.par,'vec%dvalue%s'%(i,'xyzw'[j]))
        if isinstance(v,str): p.expr = v
        else: p.val = v
nr = c.create(td.normalPOP, 'normals'); nr.inputConnectors[0].connect(g)
o2 = c.create(td.nullPOP, 'out2'); o2.inputConnectors[0].connect(nr)

# studio look (shared env)
env = glsl(c, 'envmap', open(os.path.join(ROOT,'components','_lib','env.glsl')).read(),
           vecs=[('uA',[P+'Envintensity', P+'Redaccent', 0, 0])], fmt='rgba16float')
env.par.outputresolution = 'custom'; env.par.resolutionw = 1024; env.par.resolutionh = 512
inenv = c.create(td.inTOP, 'in1'); inenv.par.connectorder = 1
esw = c.create(td.switchTOP, 'env_switch'); esw.inputConnectors[0].connect(env); esw.inputConnectors[1].connect(inenv)
esw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = o2
sel.display = True; sel.render = True
mat = c.create(td.pbrMAT, 'mat')
mat.par.basecolorr.expr = P+'Basecolorr'; mat.par.basecolorg.expr = P+'Basecolorg'; mat.par.basecolorb.expr = P+'Basecolorb'
mat.par.applypointcolor = False
mat.par.metallic.expr = P+'Metallic'; mat.par.roughness.expr = P+'Roughness'
geo.par.material = mat
core = c.create(td.geometryCOMP, 'core_geo')
for o in list(core.children): o.destroy()
sp = core.create(td.sphereSOP, 'sphere'); sp.par.type = 'polymesh' if 'polymesh' in sp.par.type.menuNames else sp.par.type.val
sp.par.rows = 30; sp.par.cols = 40; sp.display = True; sp.render = True
for a in 'xyz': getattr(core.par, 's'+a).expr = P+'Rootradius*0.98'
core.par.material = mat
core.par.render.expr = P+'Core'

cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
cam.par.tx.expr = "math.sin(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.tz.expr = "math.cos(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov.expr = P+'Fov'; cam.par.lookat = tgt
el = c.create(td.environmentlightCOMP, 'envlight'); el.par.envlightmap = esw
key = c.create(td.lightCOMP, 'key'); key.par.tx = -4; key.par.ty = 5; key.par.tz = 4; key.par.lookat = tgt
key.par.dimmer.expr = P+'Keyintensity'; key.par.shadowtype = 'off'
rim = c.create(td.lightCOMP, 'rim'); rim.par.tx = 4.5; rim.par.ty = 2; rim.par.tz = -5; rim.par.lookat = tgt
rim.par.cr = 1; rim.par.cg = 0.15; rim.par.cb = 0.1; rim.par.dimmer.expr = P+'Redaccent*0.8'; rim.par.shadowtype = 'off'
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = 'geo core_geo'; rt.par.lights = 'envlight key rim'
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr.expr = P+'Bgcolorr'; rt.par.bgcolorg.expr = P+'Bgcolorg'; rt.par.bgcolorb.expr = P+'Bgcolorb'; rt.par.bgcolora = 1
rt.par.antialias = 'aa4'; rt.par.format = 'rgba16float'
o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(rt); o.comment = 'render'; o2.comment = 'tentacles'
add_clock(c)
finish(c, name)
report(c)
