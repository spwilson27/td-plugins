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
    return "(op('modlib').module.phase() if %sTimesource=='phase' else absTime.seconds%s/%s)" % (P,sp,LOOPLEN)
def addloop(c, speed=True):
    pars(c, {'Loop': LOOP_PAGE})
# ---- end loop helpers ----
# ---- retroB helpers (batch-1 -> batch-2 retrofit); needs _helpers.py + _loop.py above ----
PP = "parent().par."
ISPH = "(1 if %sTimesource=='phase' else 0)" % PP
PH01 = "(op('modlib').module.phase() if %sTimesource=='phase' else (absTime.seconds/%s) %% 1.0)" % (PP, LOOPLEN)
def CYC(speed):
    """integer cycles per loop for a speed value (phase mode)"""
    return "(0 if %s<=0 else max(1,round(%s)))" % (speed, speed)
def TEXPR(speed='parent().par.Speed'):
    """seconds-like time: absTime*speed in abstime mode; 2pi*phase*cycles in phase mode (periodic)"""
    return "(6.283185307*op('modlib').module.phase()*%s if %sTimesource=='phase' else absTime.seconds*%s)" % (CYC(speed), PP, speed)
def ORBIT(sp='Orbitspeed', off='Orbitangle'):
    """angle: abstime = absTime*speed+offset ; phase = offset + 2pi*phase*integer cycles (rate-matched)"""
    S=PP+sp; O=PP+off
    return "(%s + 6.283185307*op('modlib').module.phase()*(0 if abs(%s)<1e-4 else (1 if %s>0 else -1)*max(1,round(abs(%s)*%s/6.283185))) if %sTimesource=='phase' else absTime.seconds*%s+%s)" % (O,S,S,S,LOOPLEN,PP,S,O)
def look_page(c, accent=True):
    items = [('m','Look','Look','original',{'menu':[('original','Original'),('mono','Mono')]})]
    if accent: items.append(('f','Accent','Accent (red, Mono)',0.0,{'min':0,'max':1}))
    pars(c, {'Look': items})
LOOKI = PP + "Look.menuIndex"
# ---- end retroB helpers ----
name = 'GEN_voronoi'
c = fresh(name)
P = "parent().par."
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('t','Active','Active',True),
  ('m','Mode','Mode',1,{'menu':[('0','Flat cells'),('1','Edge glow'),('2','Cracked glass'),('3','Stained glass')]}),
  ('i','Seeds','Seeds',40,{'min':2,'max':128,'clamp':True}),
  ('f','Speed','Speed',0.6,{'min':0,'max':4}),
  ('f','Motion','Motion',1.0,{'min':0,'max':4}),
  ('f','Jitter','Jitter (grid to random)',1.0,{'min':0,'max':1,'clamp':True}),
  ('f','Borderwidth','Border Width (px)',3.0,{'min':0.5,'max':30}),
  ('f','Glow','Glow',1.0,{'min':0,'max':3}),
  ('t','Delaunay','Delaunay Overlay',False),
  ('f','Linewidth','Delaunay Line Width (px)',1.5,{'min':0.5,'max':8}),
  ('m','Palette','Palette',3,{'menu':[('0','Rainbow'),('1','Sunset'),('2','Ocean'),('3','Neon'),('4','Mono')]}),
  ('f','Hue','Hue Shift',0.0,{'min':0,'max':1}),
  ('i','Seed','Random Seed',1,{'min':0,'max':1000}),
 ]})
addloop(c); look_page(c)
c.create(td.inTOP,'in1')
nz = c.create(td.noiseTOP,'default_src')
nz.par.outputresolution='custom'; nz.par.resolutionw=512; nz.par.resolutionh=512
nz.par.mono=False; nz.par.period=0.6; nz.par.amp=0.7; nz.par.offset=0.5; nz.par.harmon=2
nz.par.tz.expr="absTime.seconds*0.1"
nz4 = c.create(td.noiseTOP,'default_src_loop')   # phase-periodic: 4D noise on a circle
nz4.par.outputresolution='custom'; nz4.par.resolutionw=512; nz4.par.resolutionh=512
nz4.par.type='perlin4d'; nz4.par.mono=False; nz4.par.period=0.6; nz4.par.amp=0.7; nz4.par.offset=0.5; nz4.par.harmon=2
nz4.par.tz.expr="0.35*math.cos(6.283185307*%s)" % PH01
nz4.par.t4d.expr="0.35*math.sin(6.283185307*%s)" % PH01
nsw = c.create(td.switchTOP,'noise_mode'); nsw.inputConnectors[0].connect(nz); nsw.inputConnectors[1].connect(nz4)
nsw.par.index.expr = ISPH
sw = c.create(td.switchTOP,'src_switch')
sw.inputConnectors[0].connect(nsw); sw.inputConnectors[1].connect(c.op('in1'))
sw.par.index.expr="1 if parent().inputConnectors[0].connections else 0"
common = readf(name,'common.glsl')
tm = TEXPR(P+"Speed*"+P+"Active")
U = [('uA',[tm, P+"Seeds", P+"Mode", "1 if "+P+"Delaunay else 0"]),
     ('uB',[P+"Borderwidth", P+"Jitter", P+"Motion*(1+op('modlib').module.m('band1'))", P+"Seed"]),
     ('uC',[P+"Palette", P+"Hue", P+"Glow*(1+op('modlib').module.m('beat'))", P+"Linewidth"]),
     ('uD',[ISPH, LOOKI, P+"Accent", 0])]
adj = glsl(c,'adj', common+readf(name,'adj.glsl'), [('uA',[tm,P+"Seeds",0,P+"Resolutionw/"+P+"Resolutionh"]),U[1],U[2],U[3]], res=False, fmt='rgba16float')
adj.par.outputresolution='custom'; adj.par.resolutionw=128; adj.par.resolutionh=128
main = glsl(c,'vor', common+readf(name,'main.glsl'), U, fmt='rgba8fixed')
main.inputConnectors[0].connect(sw); main.inputConnectors[1].connect(adj)
ios(c, main)
MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat, phase) of the optional In CHOP, else default
def _ins():
    return [o for o in parent().children if o.OPType == 'inCHOP']
def m(n, d=0.0):
    i = _ins()
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
def clk():
    # phase 0..1 from the Clock CHOP's 'phase' channel (None if no Clock set / channel missing)
    c = parent().par.Clock.eval()
    if c is None: return None
    ch = c['phase']
    return ch.eval() if ch is not None else None
def phase():
    c = clk()
    return (c if c is not None else parent().par.Phase.eval()) % 1.0
'''

lp = [p for p in c.customPages if p.name == 'Loop'][0]
lp.appendCHOP('Clock', label='Clock CHOP (phase)')
nin = len([o for o in c.children if o.OPType in ('inTOP', 'inPOP', 'inSOP', 'inCHOP', 'inDAT')])
c.create(td.inCHOP, 'in%d' % (nin + 1))
c.create(td.textDAT, 'modlib').text = MODLIB
c.op('out1').comment = 'render'
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c); print('saved')
