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
# ---- shared helpers (pasted at top of each build.py; self-contained) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def fresh(name):
    b = op('/build') or op('/').create(td.containerCOMP, 'build')
    o = b.op(name)
    if o: o.destroy()
    c = b.create(td.baseCOMP, name)
    return c

def readf(name, fn):
    return open(os.path.join(ROOT, 'components', name, fn)).read()

def mkdat(c, nm, text):
    d = c.create(td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    """spec: {page: [(kind, name, label, default, opts)]} kind: f,i,t,m,p,rgb,wh,xy,s"""
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            if kind == 'f': ps = pg.appendFloat(nm, label=lab)
            elif kind == 'i': ps = pg.appendInt(nm, label=lab)
            elif kind == 't': ps = pg.appendToggle(nm, label=lab)
            elif kind == 'p': ps = pg.appendPulse(nm, label=lab)
            elif kind == 's': ps = pg.appendStr(nm, label=lab)
            elif kind == 'm': ps = pg.appendMenu(nm, label=lab)
            elif kind == 'rgb': ps = pg.appendRGB(nm, label=lab)
            elif kind == 'wh': ps = pg.appendWH(nm, label=lab)
            elif kind == 'xy': ps = pg.appendXY(nm, label=lab)
            p0 = ps[0]
            if kind == 'm':
                p0.menuNames = [m[0] for m in o['menu']]; p0.menuLabels = [m[1] for m in o['menu']]
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                p.default = v; p.val = v
                if 'min' in o: p.min = o['min']; p.normMin = o['min']; p.clampMin = o.get('clamp', False)
                if 'max' in o: p.max = o['max']; p.normMax = o['max']; p.clampMax = o.get('clamp', False)
    return c

def uni(g, items):
    """items: list of (name, [4 values or expr strings]); sets vecN on a GLSL TOP"""
    for i, (nm, vs) in enumerate(items):
        getattr(g.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', vs):
            p = getattr(g.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v

def glsl(c, nm, code, items, res=True, fmt=None, mode=None):
    d = mkdat(c, nm + '_code', code)
    g = c.create(td.glslTOP, nm)
    g.par.pixeldat = d
    if res:
        g.par.outputresolution = 'custom'
        g.par.resolutionw.expr = "parent().par.Resolutionw"
        g.par.resolutionh.expr = "parent().par.Resolutionh"
    if fmt: g.par.format = fmt
    uni(g, items)
    return g

def ios(c, src):
    o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(src); return o

def report(c):
    errs = []
    for o in [c] + c.findChildren():
        for s in (o.errors(), o.warnings(), o.scriptErrors()):
            if s: errs.append((o.path, s[:300]))
    print('ERRS', errs)
# ---- end helpers ----
# ---- loop helpers ----
P = "parent().par."
LOOP_PAGE = [
  ('m','Timesource','Time Source','abstime',{'menu':[('abstime','Abs Time'),('phase','Phase (external)')]}),
  ('f','Phase','Phase',0.0,{'min':0,'max':1}),
  ('f','Loopseconds','Loop Seconds',8.0,{'min':0.5,'max':120}),
  ('f','Loopbeats','Loop Beats (0=use seconds)',0.0,{'min':0,'max':64}),
  ('f','Bpm','BPM',120.0,{'min':20,'max':300}),
]
# loop length in seconds
LOOPLEN = "(%sLoopbeats*60.0/%sBpm if %sLoopbeats>0 else %sLoopseconds)" % (P,P,P,P)
# unwrapped loop phase: 1.0 == one full loop. phase mode -> Phase par, else absTime/looplen*Speed
def PEXPR(speed=True):
    sp = ("*"+P+"Speed") if speed else ""
    return "(%sPhase if %sTimesource=='phase' else absTime.seconds%s/%s)" % (P,P,sp,LOOPLEN)
def addloop(c, speed=True):
    pars(c, {'Loop': LOOP_PAGE})
# ---- end loop helpers ----
name = 'GEN_kinetic_type'
c = fresh(name)
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('s','Text','Text','KINETIC TYPE'),
  ('m','Mode','Mode','scatter',{'menu':[('scatter','Scatter on beat'),('slit','Slit stretch'),('noise','Noise warp'),('extrude','Extrude / depth stack')]}),
  ('f','Speed','Speed',1.0,{'min':0,'max':8}),
  ('p','Trigger','Trigger',0),
  ('t','Autobeat','Auto Beat',True),
  ('i','Beatsperloop','Beats Per Loop',4,{'min':1,'max':32}),
  ('f','Amount','Amount',1.0,{'min':0,'max':3}),
  ('f','Decay','Beat Decay',3.0,{'min':0.2,'max':12}),
  ('f','Stretch','Slit Stretch',5.0,{'min':0,'max':20}),
  ('i','Layers','Layers (extrude)',12,{'min':1,'max':32}),
  ('f','Depth','Depth',6.0,{'min':0,'max':20}),
 ],
 'Render': [
  ('s','Fontname','Font','Courier New'),
  ('f','Size','Glyph Size',1.0,{'min':0.2,'max':4}),
  ('f','Spacing','Spacing',1.0,{'min':0.7,'max':2}),
  ('rgb','Tint','Tint',[0.92,0.92,0.88]),
  ('rgb','Accent','Accent',[1.0,0.08,0.05]),
  ('f','Accentamt','Accent Amount',0.1,{'min':0,'max':1}),
  ('i','Seed','Seed',3,{'min':0,'max':999}),
 ],
 'Camera': [
  ('f','Sway','Sway',0.25,{'min':0,'max':1.5}),
  ('f','Fit','Fit Distance',1.0,{'min':0.3,'max':3}),
  ('f','Fov','FOV',40,{'min':15,'max':100}),
  ('f','Elevation','Elevation',0.0,{'min':-2,'max':4}),
 ]})
addloop(c)
PH = PEXPR()
NEXP = "max(len(%sText.eval()),1)" % P
# trigger storage
pe = c.create(td.parameterexecuteDAT, 'trig_exec')
pe.par.op = c; pe.par.pars = 'Trigger'; pe.par.onpulse = True
pe.text = "def onPulse(par):\n\tparent().store('t0', absTime.seconds)\n\treturn\n"
c.store('t0', -1000.0)
TRIG = "math.exp(-(absTime.seconds-parent().fetch('t0',-1000.0))*%sDecay)" % P

# atlas
tx = c.create(td.textTOP, 'atlas')
tx.par.text.expr = P+"Text"
tx.par.font.expr = P+"Fontname"
tx.par.fontautosize = 'fixed' if 'fixed' in tx.par.fontautosize.menuNames else tx.par.fontautosize.val
tx.par.fontsizex = 100; tx.par.fontsizexunit = 'pixels' if 'pixels' in tx.par.fontsizexunit.menuNames else tx.par.fontsizexunit.val
tx.par.outputresolution = 'custom'
tx.par.resolutionw.expr = "min(%s*60, 16000)" % NEXP
tx.par.resolutionh = 120
tx.par.fontcolorr = 1; tx.par.fontcolorg = 1; tx.par.fontcolorb = 1
tx.par.bgcolorr = 0; tx.par.bgcolorg = 0; tx.par.bgcolorb = 0; tx.par.bgalpha = 0
tx.par.alignx = 'center'; tx.par.aligny = 'center'
tx.par.format = 'rgba8fixed'

code = readf(name, 'inst.glsl')
d = mkdat(c, 'inst_code', code)
EFFL = "(%sLayers if %sMode=='extrude' else 1)" % (P,P)
inst = {}
for ch, nm in enumerate(['inst_t','inst_r','inst_s','inst_c','inst_uo']):
    g = c.create(td.glslTOP, nm)
    g.par.pixeldat = d
    g.par.outputresolution = 'custom'
    g.par.resolutionw.expr = "min(%s*%s, 8192)" % (NEXP, EFFL)
    g.par.resolutionh = 1
    g.par.format = 'rgba32float'
    uni(g, [('uA',[NEXP, EFFL, "%sMode.menuIndex" % P, PH]),
            ('uB',[P+"Size", P+"Spacing", P+"Amount", P+"Stretch"]),
            ('uC',[P+"Beatsperloop", "1 if %sAutobeat else 0" % P, TRIG, P+"Depth"]),
            ('uD',[ch, P+"Accentamt", P+"Decay", P+"Seed"]),
            ('uE',[P+"Tintr", P+"Tintg", P+"Tintb", 0]),
            ('uF',[P+"Accentr", P+"Accentg", P+"Accentb", 0])])
    inst[nm] = g

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
rc = geo.create(td.rectangleSOP, 'rect1')
rc.par.sizex = 0.5; rc.par.sizey = 1.0
rc.display = True; rc.render = True
mat = c.create(td.constantMAT, 'mat')
mat.par.colormap = tx
mat.par.blending = 'on'
for k, v in (('srcblend','one'),('destblend','one')):
    try: setattr(mat.par, k, v)
    except Exception as e: print('blend', k, e, getattr(mat.par,k).menuNames)
mat.par.depthwriting = False
mat.par.applypointcolor = False
geo.par.material = mat
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = inst['inst_t']
geo.par.instancetx='r'; geo.par.instancety='g'; geo.par.instancetz='b'
geo.par.instancerop = inst['inst_r']
geo.par.instancerx='r'; geo.par.instancery='g'; geo.par.instancerz='b'
geo.par.instancesop = inst['inst_s']
geo.par.instancesx='r'; geo.par.instancesy='g'; geo.par.instancesz='b'
geo.par.instancecolorop = inst['inst_c']
geo.par.instancecolormode = 'multiply'
geo.par.instancer='r'; geo.par.instanceg='g'; geo.par.instanceb='b'
try:
    geo.par.instancetexmode = 'transform'
    geo.par.instancetexcoordop = inst['inst_uo']
    geo.par.instanceu='r'; geo.par.instancev='g'; geo.par.instancew='b'
    geo.par.instancescaleu='b'; geo.par.instancescalev='a'
    print('scale op?', [p.name for p in geo.pars() if 'tex' in p.name])
except Exception as e:
    print('uv err', e)

tgt = c.create(td.nullCOMP, 'target')
cam = c.create(td.cameraCOMP, 'cam')
W = "(%s*0.5*%sSize*%sSpacing)" % (NEXP, P, P)
cam.par.tz.expr = "max(%s/(2*math.tan(math.radians(%sFov/2)))*1.08, 3)*%sFit" % (W,P,P)
cam.par.tx.expr = "math.sin(2*math.pi*%s)*%sSway*%s*0.15" % (PH,P,W)
cam.par.ty.expr = "%sElevation + math.cos(2*math.pi*%s)*%sSway*0.3" % (P,PH,P)
cam.par.fov.expr = P+"Fov"
cam.par.lookat = tgt
rt = c.create(td.renderTOP, 'render')
rt.par.camera = cam; rt.par.geometry = geo
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+"Resolutionw"; rt.par.resolutionh.expr = P+"Resolutionh"
rt.par.bgcolorr = 0; rt.par.bgcolorg = 0; rt.par.bgcolorb = 0; rt.par.bgcolora = 1
rt.par.antialias = 'aa4'
ios(c, rt).comment = 'render'
add_clock(c)
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c)
print('saved', [p.name for p in geo.pars() if p.name.startswith('instancetex') or 'scale' in p.name])
