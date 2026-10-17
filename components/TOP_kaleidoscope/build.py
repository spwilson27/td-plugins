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


# ---- v2 conventions tail (Mix/Bypass/Resolutionmode, Clock, mod In CHOP, labels, raw save) ----
import re
_RW = "(parent().op('in1').width if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionw)"
_RH = "(parent().op('in1').height if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionh)"
_PHE = "(parent().par.Clock.eval()['phase'].eval() if (parent().par.Timesource=='phase' and parent().par.Clock.eval()) else parent().par.Phase)"
_CH = lambda n: "parent().op('mod')['%s'].eval()" % n

def _subexpr(c, pat, fn):
    rx = re.compile(pat)
    for o in [c] + c.findChildren():
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                p.expr = rx.sub(fn, p.expr)

def v2_finish(c, name, dry='src', mod=(), selfmix=False, outlabels=None):
    # --- parameters
    ctl = c.appendCustomPage('Controls')
    if not hasattr(c.par, 'Mix'):
        p = ctl.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    ctl.appendToggle('Bypass')
    p = ctl.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    lp = c.appendCustomPage('Loop')
    lp.appendCHOP('Clock', label='Clock (CHOP, phase channel)')
    c.par.Resolutionw.enableExpr = "parent().par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "parent().par.Resolutionmode=='custom'"
    # --- modulation input (last In, optional)
    nin = len([o for o in c.children if o.OPType in ('inTOP', 'inSOP', 'inPOP')])
    im = c.create(td.inCHOP, 'in%d' % (nin + 1))
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat', 'phase']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im); mg.inputConnectors[0].connect(im)
    mg.inputConnectors[1].connect(mz); mg.par.duplicate = 'first'; mg.par.align = 'start'
    # --- expression patches: resolution, phase/clock
    _subexpr(c, r"parent\(\)\.par\.Resolutionw\b", lambda m: _RW)
    _subexpr(c, r"parent\(\)\.par\.Resolutionh\b", lambda m: _RH)
    _subexpr(c, r"parent\(\)\.par\.Phase\b", lambda m: _PHE)
    # modulation: wrap parameter references inside GLSL uniforms
    for pn, tmpl in mod:
        rx = re.compile(r"parent\(\)\.par\.%s\b" % pn)
        hit = 0
        for g in c.findChildren(type=td.glslTOP):
            for p in g.pars():
                if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                    p.expr = rx.sub(lambda m: tmpl.format(v=m.group(0), b1=_CH('band1'), b2=_CH('band2'), b3=_CH('band3'), b4=_CH('band4'), beat=_CH('beat')), p.expr); hit += 1
        assert hit, 'mod target not found: ' + pn
    # --- mix + bypass
    o1 = c.op('out1')
    res = o1.inputConnectors[0].connections[0].owner
    d = c.op(dry)
    if not selfmix:
        x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(d); x.inputConnectors[1].connect(res)
        x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'
        x.par.outputresolution = 'useinput'
        res = x
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(res); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "1 if (parent().par.Bypass and parent().inputConnectors[0].connections) else 0"
    o1.inputConnectors[0].connect(bp)
    o1.comment = 'result'
    for k, v in (outlabels or {}).items(): c.op(k).comment = v
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)

name = 'TOP_kaleidoscope'
c = fresh(name)
P = "parent().par."
pars(c, {
 'Controls': [
  ('wh','Resolution','Resolution',[1280,720]),
  ('m','Mode','Mode',0,{'menu':[('0','N-fold radial'),('1','Mirror tiles (square)'),('2','Mirror tiles (triangle)'),('3','Mirror tiles (hex)'),('4','Hyperbolic (Poincare disk)')]}),
  ('i','Segments','Segments / P',8,{'min':1,'max':24}),
  ('i','Hyperq','Hyperbolic Q',4,{'min':3,'max':12}),
  ('f','Tiles','Tile Count',3.0,{'min':0.5,'max':16}),
  ('f','Rotation','Rotation (deg)',0.0,{'min':-360,'max':360}),
  ('f','Zoom','Zoom',1.0,{'min':0.2,'max':6}),
  ('f','Srczoom','Source Zoom',1.0,{'min':0.2,'max':6}),
  ('xy','Center','Center',[0.0,0.0]),
  ('t','Animate','Animate',True),
  ('f','Speed','Speed',1.0,{'min':0,'max':4}),
  ('f','Noisespeed','Default Source Speed',0.15,{'min':0,'max':2}),
 ]})
addloop(c); look_page(c)
c.create(td.inTOP,'in1')
nz = c.create(td.noiseTOP,'default_src')
nz.par.outputresolution='custom'; nz.par.resolutionw=1024; nz.par.resolutionh=1024
nz.par.mono=False; nz.par.period=0.7; nz.par.amp=0.55; nz.par.offset=0.5; nz.par.harmon=1
nz.par.tz.expr="absTime.seconds*"+P+"Noisespeed*2"
# sharpen blobs with a few bold shapes so symmetry is readable
lv = c.create(td.levelTOP,'default_contrast'); lv.par.contrast=1.15; lv.par.brightness1=1.0
nz4 = c.create(td.noiseTOP,'default_src_loop')   # phase-periodic: 4D noise on a circle
nz4.par.outputresolution='custom'; nz4.par.resolutionw=1024; nz4.par.resolutionh=1024
nz4.par.type='perlin4d'; nz4.par.mono=False; nz4.par.period=0.7; nz4.par.amp=0.55; nz4.par.offset=0.5; nz4.par.harmon=1
nz4.par.tz.expr="0.45*math.cos(6.283185307*%s)" % PH01
nz4.par.t4d.expr="0.45*math.sin(6.283185307*%s)" % PH01
nsw = c.create(td.switchTOP,'noise_mode'); nsw.inputConnectors[0].connect(nz); nsw.inputConnectors[1].connect(nz4)
nsw.par.index.expr = ISPH
lv.inputConnectors[0].connect(nsw)
sw = c.create(td.switchTOP,'src_switch')
sw.inputConnectors[0].connect(lv); sw.inputConnectors[1].connect(c.op('in1'))
sw.par.index.expr="1 if parent().inputConnectors[0].connections else 0"
g = glsl(c,'kaleido', readf(name,'kaleido.glsl'), [
 ('uA',[P+"Mode", P+"Segments", "math.radians("+P+"Rotation)", P+"Zoom"]),
 ('uB',[P+"Centerx", P+"Centery", TEXPR(P+"Speed"), P+"Tiles"]),
 ('uC',[P+"Hyperq", P+"Srczoom", "1 if "+P+"Animate else 0", 0]),
 ('uD',[ISPH, LOOKI, P+"Accent", 0])], fmt='rgba8fixed')
g.par.inputextenduv = 'mirror'
g.inputConnectors[0].connect(sw)
ios(c, g)
v2_finish(c, name, dry='src_switch', mod=[('Zoom','({v}*(1+{beat}*0.25))'),('Rotation','({v}+{b1}*45)')])
report(c); print('saved')
