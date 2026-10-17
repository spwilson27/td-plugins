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
name = 'GEN_glyph_tunnel'
c = fresh(name)
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('m','Mode','Mode','tunnel',{'menu':[('tunnel','Tunnel'),('wall','Wall'),('rain','Rain')]}),
  ('s','Charset','Charset','01<>/\\|[]{}#$%&*+=-:;ABCDEFXYZ'),
  ('f','Speed','Speed',1.0,{'min':0,'max':8}),
  ('i','Cols','Columns',36,{'min':6,'max':96}),
  ('i','Looprows','Rows Per Loop',24,{'min':4,'max':64}),
  ('f','Fog','Depth Fog',1.2,{'min':0,'max':4}),
  ('f','Density','Lit Density',0.55,{'min':0.05,'max':1}),
  ('i','Flickersteps','Flicker Steps / Loop',48,{'min':1,'max':240}),
  ('p','Refresh','Refresh Glyphs',0),
  ('i','Seed','Seed',1,{'min':0,'max':999}),
 ],
 'Render': [
  ('rgb','Tint','Tint',[0.9,0.92,0.88]),
  ('rgb','Accent','Accent',[1.0,0.1,0.06]),
  ('f','Accentamt','Accent Amount',0.04,{'min':0,'max':1}),
  ('f','Brightness','Brightness',2.4,{'min':0,'max':5}),
  ('f','Trail','Rain Trail',0.6,{'min':0,'max':1}),
  ('s','Fontname','Font','Courier New'),
 ],
 'Camera': [
  ('f','Sway','Sway',1.0,{'min':0,'max':3}),
  ('i','Rollturns','Roll Turns / Loop',0,{'min':-4,'max':4}),
  ('f','Fov','FOV',75,{'min':30,'max':140}),
 ]})
addloop(c)
PH = PEXPR()
pe = c.create(td.parameterexecuteDAT, 'refresh_exec')
pe.par.op = c; pe.par.pars = 'Refresh'; pe.par.onpulse = True
pe.text = "def onPulse(par):\n\tparent().store('rseed', tdu.rand(absTime.frame)*100)\n"
c.store('rseed', 0.0)
tx = c.create(td.textTOP, 'atlas')
NEXP = "max(len(%sCharset.eval()),1)" % P
tx.par.text.expr = P+"Charset"
tx.par.font.expr = P+"Fontname"
tx.par.fontautosize = 'nofit'
tx.par.fontsizexunit = 'pixels'; tx.par.fontsizeyunit = 'pixels'
tx.par.fontsizex = 100
tx.par.outputresolution = 'custom'
tx.par.resolutionw.expr = "min(%s*60, 16000)" % NEXP
tx.par.resolutionh = 120
tx.par.fontcolorr = tx.par.fontcolorg = tx.par.fontcolorb = 1
tx.par.bgcolorr = tx.par.bgcolorg = tx.par.bgcolorb = 0; tx.par.bgalpha = 1
tx.par.alignx = 'center'; tx.par.aligny = 'center'
tx.par.format = 'rgba8fixed'
g = glsl(c, 'tunnel', readf(name, 'tunnel.glsl'), [
 ('uA',[NEXP, P+"Mode.menuIndex", PH, P+"Cols"]),
 ('uB',[P+"Looprows", P+"Flickersteps", P+"Fog", P+"Rollturns"]),
 ('uC',[P+"Sway", P+"Density", P+"Accentamt", P+"Seed+parent().fetch('rseed',0)"]),
 ('uD',[P+"Tintr", P+"Tintg", P+"Tintb", P+"Brightness"]),
 ('uE',[P+"Accentr", P+"Accentg", P+"Accentb", P+"Trail"]),
 ('uF',[P+"Fov",0,0,0]),
], fmt='rgba16float')
g.inputConnectors[0].connect(tx)
ios(c, g).comment = 'render'
add_clock(c)
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c)
print('saved')
