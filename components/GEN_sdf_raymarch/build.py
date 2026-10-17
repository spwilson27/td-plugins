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
name = 'GEN_sdf_raymarch'
c = fresh(name)
SH = [('0','Sphere'),('1','Box'),('2','Torus'),('3','Capsule'),('4','Gyroid')]
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('t','Active','Active',True),
  ('f','Speed','Speed',1.0,{'min':0,'max':4}),
  ('m','Shape1','Shape A',0,{'menu':SH}),
  ('m','Shape2','Shape B',2,{'menu':SH}),
  ('m','Combine','Combine',0,{'menu':[('0','Smooth union'),('1','Smooth subtract'),('2','Smooth intersect')]}),
  ('f','K','Smooth K',0.35,{'min':0.001,'max':1.5}),
  ('f','Scale','Scale',1.0,{'min':0.2,'max':3}),
  ('t','Repeat','Domain Repeat',False),
  ('f','Repeatsize','Repeat Size',3.0,{'min':1.5,'max':8}),
  ('f','Thickness','Gyroid Thickness',0.05,{'min':0.01,'max':0.3}),
  ('m','Palette','Palette',3,{'menu':[('0','Rainbow'),('1','Sunset'),('2','Ocean'),('3','Neon'),('4','Mono')]}),
  ('f','Hue','Hue Shift',0.0,{'min':0,'max':1}),
  ('i','Steps','Max Steps',90,{'min':20,'max':200}),
 ],
 'Camera': [
  ('f','Orbitspeed','Orbit Speed',0.3,{'min':-2,'max':2}),
  ('f','Orbitangle','Orbit Offset',0.6,{'min':-6.28,'max':6.28}),
  ('f','Distance','Distance',4.2,{'min':1.5,'max':20}),
  ('f','Height','Height',1.6,{'min':-3,'max':8}),
  ('f','Fov','FOV',45,{'min':15,'max':100}),
 ],
 'Light': [
  ('f','Lightazimuth','Light Azimuth',0.9,{'min':-6.28,'max':6.28}),
  ('f','Lightelevation','Light Elevation',0.8,{'min':0.05,'max':1.5}),
  ('f','Shadowsoft','Shadow Hardness',8.0,{'min':1,'max':32}),
  ('f','Ao','AO Strength',1.0,{'min':0,'max':1}),
  ('f','Fog','Fog Density',0.5,{'min':0,'max':3}),
  ('rgb','Fogcolor','Fog Color',[0.05,0.06,0.1]),
 ]})
addloop(c); look_page(c)
P = "parent().par."
TT = TEXPR(P+"Speed*"+P+"Active")
OA = ORBIT()
g = glsl(c, 'sdf', readf(name,'sdf.glsl'), [
 ('uA', [TT+"*"+P+"Active", P+"K+0.3*op('modlib').module.m('band1')", "1 if "+P+"Repeat else 0", P+"Repeatsize"]),
 ('uB', [P+"Shape1", P+"Shape2", P+"Combine", P+"Scale*(1+0.25*op('modlib').module.m('beat'))"]),
 ('uC', [OA, P+"Distance", P+"Height", P+"Fov"]),
 ('uD', [P+"Lightazimuth", P+"Lightelevation", P+"Shadowsoft", P+"Ao"]),
 ('uE', [P+"Fog", P+"Palette", P+"Hue", P+"Thickness"]),
 ('uF', [P+"Fogcolorr", P+"Fogcolorg", P+"Fogcolorb", P+"Steps"]),
 ('uG', [ISPH, LOOKI, P+"Accent", 0]),
], fmt='rgba8fixed')
g.par.pixeldat.val = c.op('sdf_code')
ios(c, g)
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
report(c)
print('saved')
