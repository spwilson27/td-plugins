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
    p = os.path.join(ROOT, 'tox', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ---- retroB helpers for the 'effects' group (lib.py based). Prepend after _lib/lib.py ----
PP = "parent().par."
RL = "(%sLoopbeats*60.0/%sBpm if %sLoopbeats>0 else %sLoopseconds)" % (PP, PP, PP, PP)   # loop length (s)
ISPH = "(1 if %sTimesource=='phase' else 0)" % PP
PH01 = "((%sPhase) %% 1.0 if %sTimesource=='phase' else (absTime.seconds/%s) %% 1.0)" % (PP, PP, RL)
# source clock: seconds in abstime, 2*pi*phase in phase mode
TSRC = "(6.283185307*%sPhase if %sTimesource=='phase' else absTime.seconds)" % (PP, PP)
def look_pg(c):
    add_pars(c, [('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
                 ('Accent', 'float', 0.0, 0, 1)], page='Look')
LOOKI = PP + "Look.menuIndex"
def input_stage_rb(c, comp, bg=1.0):
    """like lib.input_stage but with phase-periodic + Mono-capable default source (_lib/rb_src.glsl)"""
    i = c.create(td.inTOP, 'in1')
    code = open(os.path.join(ROOT, 'components', '_lib', 'rb_src.glsl')).read()
    d = glsl(c, 'defsrc', code, vecs=[('uTime', [TSRC, 0, 0, 0]), ('uBg', [bg, 0, 0, 0]), ('uM', [ISPH, LOOKI, PP + 'Accent', 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw
def add_loopreset2(c, reset_par='Reset'):
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendToggle('Loopreset', label='Reset Feedback At Loop Start')[0]; p.default = False; p.val = False
    k = c.create(td.constantCHOP, 'loopclock'); k.par.name0 = 'ph'; k.par.value0.expr = PH01
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    ph = op('loopclock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if c.par.Loopreset.eval() and ph < prev - 0.5:\n"
              "        c.par.%s.pulse()\n"
              "    return\n" % reset_par)
    e.par.framestart = True; e.par.active = True
def CYC(speed):
    return "(0 if %s<=0 else max(1,round(%s)))" % (speed, speed)
def TEXPR(speed):
    """abstime: absTime*speed ; phase: 2pi*phase*integer cycles"""
    return "(6.283185307*%sPhase*%s if %sTimesource=='phase' else absTime.seconds*%s)" % (PP, CYC(speed), PP, speed)
def add_loop(c):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]; p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute time', 'Phase (loop)']
    p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1
    p = pg.appendFloat('Loopseconds')[0]; p.default = 8; p.val = 8; p.min = 0.1; p.max = 120; p.normMin = 0.1; p.normMax = 60; p.clampMin = True
    p = pg.appendInt('Loopbeats')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 128; p.normMin = 0; p.normMax = 32; p.clampMin = True
    p = pg.appendFloat('Bpm')[0]; p.default = 120; p.val = 120; p.min = 20; p.max = 300; p.normMin = 20; p.normMax = 300





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

COMP = 'TOP_slit_scan'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('hgradient', 'Horizontal gradient'), ('vgradient', 'Vertical gradient'), ('radial', 'Radial'),
                     ('noise', 'Noise'), ('in2', 'In2 TOP map')], 0),
    ('Frames', 'float', 40, 1, 126),
    ('Direction', 'menu', [('forward', 'Forward'), ('reverse', 'Reverse')], 0),
    ('Speed', 'float', 0.15, -2, 2),
    ('Smooth', 'toggle', 1),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [
    ('Resolution', 'wh', (1280, 720)),
    ('Buffersize', 'int', 64, 8, 128),
    ('Bufferscale', 'float', 0.5, 0.125, 1),
], page='Render')
add_loop(c); look_pg(c)
src = input_stage_rb(c, COMP, bg=1.0)
i2 = c.create(td.inTOP, 'in2')
rp = c.create(td.rampTOP, 'defmap'); setres(rp)
mp = c.create(td.switchTOP, 'map'); mp.inputConnectors[0].connect(rp); mp.inputConnectors[1].connect(i2)
mp.par.index.expr = "1 if parent().inputConnectors[1].connections else 0"; setres(mp)
bi = c.create(td.nullTOP, 'bufin'); bi.inputConnectors[0].connect(src)
bi.par.outputresolution = 'custom'
bi.par.resolutionw.expr = 'int(parent().par.Resolutionw*parent().par.Bufferscale)'
bi.par.resolutionh.expr = 'int(parent().par.Resolutionh*parent().par.Bufferscale)'
bi.par.format = 'rgba8fixed'
t3 = c.create(td.texture3dTOP, 'ring'); t3.inputConnectors[0].connect(bi)
t3.par.cachesize.expr = 'parent().par.Buffersize'
t3.par.active.expr = 'parent().par.Active'   # rolling cache: slice N-1 = newest cook, slice 0 = oldest (no gaps if frames drop)
t3.par.prefill.expr = 'parent().par.Reset or parent().time.frame < 5'   # fill the ring with the first frames so there are no black slices
g = glsl(c, 'slit', rd(COMP, 'slit.glsl'), inputs=[t3, mp], res=True, fmt='rgba16float', vecs=[
    ('uA', ['parent().par.Frames', 'parent().par.Mode.menuIndex', '1 if parent().par.Direction.menuIndex==0 else -1', '(2.0*parent().par.Phase*(0 if abs(parent().par.Speed)<1e-4 else (1 if parent().par.Speed>0 else -1)*max(1,round(abs(parent().par.Speed)*'+RL+'/2.0))) if '+ISPH+' else parent().par.Speed*absTime.seconds)']),
    ('uB', ['parent().par.Buffersize', 'absTime.frame', '(6.283185307*parent().par.Phase if '+ISPH+' else absTime.seconds*0.4)', 'parent().par.Smooth']),
    ('uC', [ISPH, 0, 0, 0]),
])
g.par.inputextenduv = 'hold'
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(g)
add_loopreset2(c)
v2_finish(c, COMP, mod=[('Frames','({v}*(1+{b1}*0.7))')])
report(c)
