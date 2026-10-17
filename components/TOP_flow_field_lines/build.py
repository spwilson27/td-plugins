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
# ---- retroB helpers (batch-1 -> batch-2 retrofit); needs _helpers.py + _loop.py above ----
PP = "parent().par."
ISPH = "(1 if %sTimesource=='phase' else 0)" % PP
PH01 = "((%sPhase) %% 1.0 if %sTimesource=='phase' else (absTime.seconds/%s) %% 1.0)" % (PP, PP, LOOPLEN)
def CYC(speed):
    """integer cycles per loop for a speed value (phase mode)"""
    return "(0 if %s<=0 else max(1,round(%s)))" % (speed, speed)
def TEXPR(speed='parent().par.Speed'):
    """seconds-like time: absTime*speed in abstime mode; 2pi*phase*cycles in phase mode (periodic)"""
    return "(6.283185307*%sPhase*%s if %sTimesource=='phase' else absTime.seconds*%s)" % (PP, CYC(speed), PP, speed)
def ORBIT(sp='Orbitspeed', off='Orbitangle'):
    """angle: abstime = absTime*speed+offset ; phase = offset + 2pi*phase*integer cycles (rate-matched)"""
    S=PP+sp; O=PP+off
    return "(%s + 6.283185307*%sPhase*(0 if abs(%s)<1e-4 else (1 if %s>0 else -1)*max(1,round(abs(%s)*%s/6.283185))) if %sTimesource=='phase' else absTime.seconds*%s+%s)" % (O,PP,S,S,S,LOOPLEN,PP,S,O)
def look_page(c, accent=True):
    items = [('m','Look','Look','original',{'menu':[('original','Original'),('mono','Mono')]})]
    if accent: items.append(('f','Accent','Accent (red, Mono)',0.0,{'min':0,'max':1}))
    pars(c, {'Look': items})
LOOKI = PP + "Look.menuIndex"
# ---- end retroB helpers ----

def add_loopreset(c, resets, default=False):
    """Loopreset toggle on Loop page + frame-start DAT pulsing reset pulses when loop phase wraps.
    resets: list of (opname, parname) pulse pars to fire."""
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendToggle('Loopreset', label='Reset Stateful Sim At Loop Start')[0]; p.default = default; p.val = default
    k = c.create(td.constantCHOP, 'loopclock'); k.par.name0 = 'ph'; k.par.value0.expr = PH01
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("RESETS = %r\n"
              "def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    ph = op('loopclock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if c.par.Loopreset.eval() and ph < prev - 0.5:\n"
              "        for o, n in RESETS:\n"
              "            op(o).par[n].pulse()\n"
              "    return\n" % (list(resets),))
    e.par.framestart = True; e.par.active = True
name = 'GEN_flow_field_lines'
c = fresh(name)
P = "parent().par."
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('t','Active','Active',True),
  ('p','Reset','Reset',False),
  ('f','Speed','Speed',1.0,{'min':0,'max':4}),
  ('i','Count','Count',40000,{'min':100,'max':262144}),
  ('f','Fieldscale','Field Scale',1.2,{'min':0.1,'max':8}),
  ('f','Fieldspeed','Field Speed',0.08,{'min':0,'max':2}),
  ('m','Fieldtype','Field Type',0,{'menu':[('0','Curl noise'),('1','Angle noise')]}),
  ('f','Turbulence','Turbulence',0.4,{'min':0,'max':2}),
  ('f','Stepsize','Step Size',0.004,{'min':0.0005,'max':0.03}),
  ('f','Lifetime','Lifetime (frames)',240,{'min':10,'max':2000}),
  ('f','Fade','Fade',0.985,{'min':0.8,'max':0.9995}),
  ('f','Inputamt','Input Angle Amount',1.0,{'min':0,'max':4}),
 ],
 'Render': [
  ('f','Linewidth','Line Width (px)',1.3,{'min':0.5,'max':8}),
  ('f','Trail','Segment Length (steps)',2.5,{'min':0.5,'max':20}),
  ('f','Intensity','Intensity',0.35,{'min':0,'max':3}),
  ('f','Exposure','Exposure',1.6,{'min':0.1,'max':8}),
  ('m','Colormode','Color Mode',1,{'menu':[('0','Line color'),('1','Palette by direction'),('2','Palette by age'),('3','Palette per particle')]}),
  ('rgb','Linecolor','Line Color',[0.9,0.7,0.35]),
  ('f','Hue','Palette Hue Shift',0.0,{'min':0,'max':1}),
  ('rgb','Bgcolor','Background',[0.01,0.01,0.02]),
 ]})
addloop(c); look_page(c)
c.create(td.inTOP,'in1')
side = "int(math.ceil(math.sqrt(max(1,%sCount))))" % P
gray = c.create(td.constantTOP,'no_input'); gray.par.colorr=gray.par.colorg=gray.par.colorb=0.5
gray.par.outputresolution='custom'; gray.par.resolutionw=256; gray.par.resolutionh=256
sw = c.create(td.switchTOP,'in_switch'); sw.inputConnectors[0].connect(gray); sw.inputConnectors[1].connect(c.op('in1'))
sw.par.index.expr="1 if parent().inputs else 0"
common = readf(name,'common.glsl')
tm = TEXPR("%sSpeed*%sFieldspeed"%(P,P))
U = [('uA',[tm, P+"Fieldscale", P+"Stepsize*"+P+"Speed", P+"Fieldtype"]),
     ('uB',[P+"Trail", "1 if parent().inputs else 0", P+"Inputamt", P+"Turbulence"]),
     ('uC',[P+"Active", P+"Lifetime", P+"Resolutionw/"+P+"Resolutionh", "absTime.frame"]),
     ('uD',[P+"Linewidth/"+P+"Resolutionh", P+"Intensity", P+"Colormode", P+"Hue"]),
     ('uE',[0, P+"Linecolorr", P+"Linecolorg", P+"Linecolorb"]),
     ('uF',[LOOKI, P+"Accent", ISPH, 0])]
def sq(g):
    g.par.outputresolution='custom'; g.par.resolutionw.expr=side; g.par.resolutionh.expr=side
# state loop
fbs = c.create(td.feedbackTOP,'fb_state')
st = glsl(c,'state', common+readf(name,'state.glsl'), U, res=False, fmt='rgba32float'); sq(st)
st.inputConnectors[0].connect(fbs); st.inputConnectors[1].connect(sw)
fbs.par.top = st
z1 = c.create(td.constantTOP,'zero_state'); z1.par.colorr=z1.par.colorg=z1.par.colorb=0; z1.par.alpha=0; z1.par.format='rgba32float'
z1.par.outputresolution='custom'; z1.par.resolutionw.expr=side; z1.par.resolutionh.expr=side
fbs.inputConnectors[0].connect(z1)
fbs.par.format='rgba32float'
fbs.par.outputresolution='custom'; fbs.par.resolutionw.expr=side; fbs.par.resolutionh.expr=side
# instance data
G = {}
for i,nm in enumerate(['inst_t','inst_r','inst_s','inst_c']):
    uu = [list(x) for x in U]; uu[4] = ('uE',[i]+uu[4][1][1:])
    g = glsl(c,nm, common+readf(name,'inst.glsl'), [(a,b) for a,b in uu], res=False, fmt='rgba32float'); sq(g)
    g.inputConnectors[0].connect(st); g.inputConnectors[1].connect(sw)
    G[nm]=g
geo = c.create(td.geometryCOMP,'geo')
for o in list(geo.children): o.destroy()
bx = geo.create(td.boxSOP,'seg'); bx.par.sizex=1; bx.par.sizey=1; bx.par.sizez=0.001
bx.display=True; bx.render=True
mat = c.create(td.constantMAT,'mat'); mat.par.applypointcolor=True
geo.par.material = mat
geo.par.instancing=True; geo.par.instancecountmode='oplength'
geo.par.instanceop=G['inst_t']; geo.par.instancetop=G['inst_t']
geo.par.instancetx='r'; geo.par.instancety='g'; geo.par.instancetz='b'
geo.par.instancerop=G['inst_r']; geo.par.instancerx='r'; geo.par.instancery='g'; geo.par.instancerz='b'
geo.par.instancesop=G['inst_s']; geo.par.instancesx='r'; geo.par.instancesy='g'; geo.par.instancesz='b'
geo.par.instancecolorop=G['inst_c']; geo.par.instancer='r'; geo.par.instanceg='g'; geo.par.instanceb='b'
cam = c.create(td.cameraCOMP,'cam'); cam.par.projection='ortho'; cam.par.tz=5
cam.par.orthowidth.expr = "%sResolutionw/%sResolutionh" % (P,P)
rt = c.create(td.renderTOP,'render'); rt.par.camera=cam; rt.par.geometry=geo; rt.par.lights=''
rt.par.outputresolution='custom'; rt.par.resolutionw.expr=P+"Resolutionw"; rt.par.resolutionh.expr=P+"Resolutionh"
rt.par.bgcolora=0; rt.par.antialias='aa2'; rt.par.format='rgba16float'
# accumulation loop
fba = c.create(td.feedbackTOP,'fb_accum')
ac = glsl(c,'accum', readf(name,'accum.glsl'), [('uA',[P+"Fade",P+"Active",0,0])], fmt='rgba32float')
ac.inputConnectors[0].connect(fba); ac.inputConnectors[1].connect(rt)
z2 = c.create(td.constantTOP,'zero_accum'); z2.par.colorr=z2.par.colorg=z2.par.colorb=0; z2.par.alpha=1; z2.par.format='rgba32float'
z2.par.outputresolution='custom'; z2.par.resolutionw.expr=P+"Resolutionw"; z2.par.resolutionh.expr=P+"Resolutionh"
fba.inputConnectors[0].connect(z2)
fba.par.top = ac; fba.par.format='rgba32float'
fba.par.outputresolution='custom'; fba.par.resolutionw.expr=P+"Resolutionw"; fba.par.resolutionh.expr=P+"Resolutionh"
fin = glsl(c,'final', readf(name,'final.glsl'), [('uA',[P+"Exposure",0,0,0])], fmt='rgba16float')
fin.inputConnectors[0].connect(ac)
# bg color uniform via color page
fin.par.color0name='uBg'
fin.par.color0rgbr.expr="0 if %s else %sBgcolorr"%(LOOKI,P); fin.par.color0rgbg.expr="0 if %s else %sBgcolorg"%(LOOKI,P); fin.par.color0rgbb.expr="0 if %s else %sBgcolorb"%(LOOKI,P)
ios(c, fin).comment = 'lines'
pe = c.create(td.parameterexecuteDAT,'pexec'); pe.text = readf(name,'pexec.py')
pe.par.op=c; pe.par.pars='Reset'; pe.par.valuechange=False; pe.par.onpulse=True; pe.par.executeloc='op'
add_loopreset(c, [('fb_state','resetpulse'),('fb_accum','resetpulse')])
add_clock(c)
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c); print('saved')
