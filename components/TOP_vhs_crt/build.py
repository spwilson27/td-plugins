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

# ---- signal_lib: loop params + periodic default source (appended after lib.py) ----
LENEXPR = "max(0.25,(parent().par.Loopseconds if parent().par.Loopseconds>0 else parent().par.Loopbeats*60.0/max(1.0,parent().par.Bpm)))"
PEXPR = "((parent().par.Phase if parent().par.Timesource=='phase' else absTime.seconds/%s) %% 1.0)" % LENEXPR
FREXPR = "max(2,2*round(%s*15))" % LENEXPR
def uP(extra=0):
    return ('uP', [PEXPR, LENEXPR, FREXPR, extra])

def loop_pars(c, beats=8):
    add_pars(c, [
        ('Timesource', 'menu', [('abstime', 'Abs Time'), ('phase', 'Phase')], 0),
        ('Phase', 'float', 0, 0, 1),
        ('Loopbeats', 'float', beats, 1, 64),
        ('Bpm', 'float', 120, 30, 300),
        ('Loopseconds', 'float', 0, 0, 60),
    ], page='Loop')

def sig_input(c):
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read(), vecs=[uP()], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw); sw.par.format = 'rgba16float'
    return sw
# ---- end signal_lib ----




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

COMP = 'TOP_vhs_crt'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('vhs', 'VHS'), ('crt', 'CRT'), ('both', 'Both')], 2),
    ('Amount', 'float', 1.0, 0, 2),
    ('Wobble', 'float', 0.6, 0, 2),
    ('Jitter', 'float', 0.5, 0, 2),
    ('Chromableed', 'float', 1.0, 0, 4),
    ('Chromashift', 'float', 3.0, -20, 20),
    ('Tracking', 'float', 0.6, 0, 2),
    ('Headswitch', 'float', 0.7, 0, 2),
    ('Noise', 'float', 0.5, 0, 2),
    ('Softness', 'float', 1.0, 0, 4),
    ('Interlace', 'float', 0.5, 0, 1),
    ('Curvature', 'float', 0.5, 0, 2),
    ('Scanlines', 'float', 0.6, 0, 1.5),
    ('Scanlinecount', 'int', 360, 60, 1080),
    ('Maskstrength', 'float', 0.5, 0, 1),
    ('Glow', 'float', 0.5, 0, 2),
    ('Vignette', 'float', 0.6, 0, 2),
    ('Flicker', 'float', 0.5, 0, 2),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
loop_pars(c, beats=8)
src = sig_input(c)
mi = "parent().par.Mode.menuIndex"
tape = glsl(c, 'tape', rd(COMP, 'tape.glsl'), inputs=[src], res=True, vecs=[
    uP(),
    ('uA', ['parent().par.Wobble', 'parent().par.Jitter', 'parent().par.Chromableed', 'parent().par.Chromashift']),
    ('uB', ['parent().par.Tracking', 'parent().par.Headswitch', 'parent().par.Noise', 'parent().par.Softness']),
    ('uC', ['1 if %s in (0,2) else 0' % mi, 'parent().par.Amount', 'parent().par.Interlace', 0]),
])
tape.par.inputextenduv = 'mirror'
crt = glsl(c, 'crt', rd(COMP, 'crt.glsl'), inputs=[tape], res=True, vecs=[
    uP(),
    ('uA', ['parent().par.Curvature', 'parent().par.Scanlines', 'parent().par.Maskstrength', 'parent().par.Glow']),
    ('uB', ['parent().par.Vignette', 'parent().par.Flicker', 'parent().par.Interlace', 'parent().par.Scanlinecount']),
    ('uC', ['1 if %s in (1,2) else 0' % mi, 'parent().par.Amount', 0, 0]),
])
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(crt)
v2_finish(c, COMP, mod=[('Tracking','({v}+{b1})'),('Jitter','({v}+{beat})')])
report(c)
