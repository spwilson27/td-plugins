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
name = 'GEN_text_fluid'
c = fresh(name)
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('s','Text','Text','DISSOLVE'),
  ('t','Play','Play',True),
  ('p','Reset','Reset',0),
  ('f','Speed','Speed',1.0,{'min':0,'max':4}),
  ('f','Fontsize','Font Size',0.12,{'min':0.05,'max':1}),
  ('s','Fontname','Font','Courier New'),
  ('f','Inject','Inject Amount',16.0,{'min':0,'max':20}),
  ('f','Push','Inject Velocity',0.15,{'min':0,'max':20}),
  ('f','Cycles','Re-injections / Loop',2,{'min':0.25,'max':16}),
  ('f','Injectfrac','Inject Window',0.08,{'min':0.01,'max':1}),
  ('f','Smear','Smear Force',0.7,{'min':0,'max':30}),
  ('i','Emitters','Smear Emitters',2,{'min':0,'max':6}),
  ('f','Vorticity','Vorticity',0.6,{'min':0,'max':5}),
  ('f','Dissipation','Dye Dissipation',0.003,{'min':0,'max':0.5}),
  ('f','Exposure','Exposure',6.0,{'min':0,'max':10}),
  ('rgb','Tint','Tint',[1.0,0.97,0.9]),
 ]})
addloop(c)
PH = PEXPR()
tx = c.create(td.textTOP, 'mask')
tx.par.text.expr = P+"Text"
tx.par.font.expr = P+"Fontname"
tx.par.fontautosize = 'fitiffat'
tx.par.fontsizexunit = 'fract'; tx.par.fontsizeyunit = 'fract'
tx.par.fontsizex.expr = P+"Fontsize"
tx.par.outputresolution = 'custom'
tx.par.resolutionw.expr = P+"Resolutionw"; tx.par.resolutionh.expr = P+"Resolutionh"
tx.par.fontcolorr = tx.par.fontcolorg = tx.par.fontcolorb = 1
tx.par.bgcolorr = tx.par.bgcolorg = tx.par.bgcolorb = 0; tx.par.bgalpha = 1
tx.par.alignx = 'center'; tx.par.aligny = 'center'
tx.par.format = 'rgba16float'
bl = c.create(td.blurTOP, 'soften'); bl.inputConnectors[0].connect(tx)
bl.par.size = 3
env = c.create(td.mathTOP, 'envelope'); env.inputConnectors[0].connect(bl)
env.par.gain.expr = ("%sInject*(1 if ((%s*%sCycles)%%1.0 < %sInjectfrac or parent().time.seconds-parent().fetch('rt',0.0) < 0.4) else 0)*%sPlay"
                     % (P, PH, P, P, P))
env.par.format = 'rgba16float'
fl = c.loadTox(os.path.expanduser('~/software/td-plugins/tox/GEN/GEN_fluid_2d.tox'))
fl.name = 'fluid'
fl.inputConnectors[0].connect(env)
fl.par.Resolutionw.expr = P+"Resolutionw"; fl.par.Resolutionh.expr = P+"Resolutionh"
fl.par.Play.expr = P+"Play"
fl.par.Speed.expr = P+"Speed"
fl.par.Inputdensity.expr = "1.0"
fl.par.Inputvelocity.expr = P+"Push"
fl.par.Emitters.expr = P+"Emitters"
fl.par.Force.expr = P+"Smear"
fl.par.Density.val = 0.0            # emitters push only, no dye
fl.par.Vorticity.expr = P+"Vorticity"
fl.par.Dyedissipation.expr = P+"Dissipation"
fl.par.Exposure.expr = P+"Exposure"
fl.par.Saturation.val = 0.0
fl.par.Backgroundr = 0; fl.par.Backgroundg = 0; fl.par.Backgroundb = 0
tint = c.create(td.glslTOP, 'tint')
tint.par.pixeldat = mkdat(c, 'tint_code', """out vec4 fragColor;
uniform vec3 uTint;
void main(){ vec3 c = texture(sTD2DInputs[0], vUV.st).rgb; float l = dot(c, vec3(0.333));
  fragColor = TDOutputSwizzle(vec4(vec3(l) * uTint, 1.0)); }
""")
tint.par.outputresolution = 'custom'; tint.par.resolutionw.expr = P+"Resolutionw"; tint.par.resolutionh.expr = P+"Resolutionh"
tint.par.format = 'rgba16float'
uni(tint, [('uTint', [P+"Tintr", P+"Tintg", P+"Tintb", 0])])
sel = c.create(td.selectTOP, 'fluid_out'); sel.par.top = fl.op('out1')
tint.inputConnectors[0].connect(sel)
ios(c, tint).comment = 'render'
rp = c.create(td.parameterexecuteDAT, 'reset_exec')
rp.par.op = c; rp.par.pars = 'Reset'; rp.par.onpulse = True
rp.text = "def onPulse(par):\n\tparent().store('rt', parent().time.seconds)\n\tparent().op('fluid').par.Reset.pulse()\n"
c.store('rt', 0.0)
add_clock(c)
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c)
print('saved')
