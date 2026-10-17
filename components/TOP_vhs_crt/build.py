# ---- v3 shared helpers (pasted at top of each build.py) ----
import os, re, td
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
    """vecs: list of (uniformName, [4 values/exprs]); exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:
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

def look_pg(c):
    add_pars(c, [('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
                 ('Accent', 'float', 0.0, 0, 1)], page='Look')

LOOK_VECS = [('uM', [0, 'parent(2).par.Look.menuIndex', 'parent(2).par.Accent', 0])]

def demo_src(c, comp, fn='src.glsl', bg=1.0, vecs=None, fmt='rgba16float'):
    """in1 + gated `demo` COMP (preview-only source) -> Switch TOP 'src'.
    The switch picks the demo only while in1 is unconnected, so the demo does not cook otherwise."""
    i = c.create(td.inTOP, 'in1')
    d = c.create(td.baseCOMP, 'demo')
    d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
    if vecs is None:
        vecs = [('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])] + LOOK_VECS
    g = glsl(d, 'defsrc', rd(comp, fn), vecs=vecs, fmt=fmt)
    setres(g, 'parent(2).par.Resolutionw', 'parent(2).par.Resolutionh')
    o = d.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(g); o.par.label = 'demo source'
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"   # in1.width: re-evaluate when a TOP is plugged in
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

_RW = "[parent().op('in1').width, parent().par.Resolutionw][0 if (parent().par.Resolutionmode=='input' and len(parent().inputConnectors[0].connections)) else 1]"
_RH = "[parent().op('in1').height, parent().par.Resolutionh][0 if (parent().par.Resolutionmode=='input' and len(parent().inputConnectors[0].connections)) else 1]"
_CH = lambda n: "parent().op('mod')['%s'].eval()" % n

def _subexpr(c, pat, fn):
    rx = re.compile(pat)
    for o in [c] + c.findChildren():
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                p.expr = rx.sub(fn, p.expr)

def v3_finish(c, name, dry='src', mod=(), selfmix=False, outlabels=None):
    ctl = c.appendCustomPage('Controls')
    if not hasattr(c.par, 'Mix'):
        p = ctl.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    ctl.appendToggle('Bypass')
    p = ctl.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"
    nin = len([o for o in c.children if o.OPType in ('inTOP', 'inSOP', 'inPOP')])
    im = c.create(td.inCHOP, 'in%d' % (nin + 1))
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im)
    mg.inputConnectors[1].connect(mz); mg.par.duplicate = 'first'; mg.par.align = 'start'
    _subexpr(c, r"parent\(\)\.par\.Resolutionw\b", lambda m: _RW)
    _subexpr(c, r"parent\(\)\.par\.Resolutionh\b", lambda m: _RH)
    for pn, tmpl in mod:
        rx = re.compile(r"parent\(\)\.par\.%s\b" % pn)
        hit = 0
        for g in c.findChildren(type=td.glslTOP):
            for p in g.pars():
                if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                    p.expr = rx.sub(lambda m: tmpl.format(v=m.group(0), b1=_CH('band1'), b2=_CH('band2'), b3=_CH('band3'), b4=_CH('band4'), beat=_CH('beat')), p.expr); hit += 1
        assert hit, 'mod target not found: ' + pn
    o1 = c.op('out1')
    res = o1.inputConnectors[0].connections[0].owner
    d = c.op(dry)
    if not selfmix:
        x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(d); x.inputConnectors[1].connect(res)
        x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'
        x.par.outputresolution = 'useinput'
        res = x
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(res); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "(1 if (parent().par.Bypass and len(parent().inputConnectors[0].connections)) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
    o1.inputConnectors[0].connect(bp)
    o1.comment = 'result'
    for k, v in (outlabels or {}).items(): c.op(k).comment = v
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)
# ---- end helpers ----
# time uniform: P = seconds/8 (unwrapped), 8, frame index rate = 30 fps (P*240)
def uP(extra=0):
    return ('uP', ['absTime.seconds/8.0', 8.0, 240.0, extra])
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
# --- native-node helper (pasted into the body of native build.py files) ---
def nat(c, typ, name, *ins, fmt='rgba16float', **kw):
    """Create a native op, wire inputs, set pars. A str value starting with '=' is an expression."""
    o = c.create(getattr(td, typ), name)
    for i, s in enumerate(ins):
        if s is not None: o.inputConnectors[i].connect(s)
    if fmt and hasattr(o.par, 'format'): o.par.format = fmt
    for k, v in kw.items():
        p = o.par[k]
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        elif isinstance(v, str): p.val = v
        else: p.val = v
    return o

P = 'parent().par.'
F = ' + 0*absTime.frame'
A = P + 'Amount'
RW, RH = "parent().par.Resolutionw", "parent().par.Resolutionh"        # v3_finish turns these into the real output size
T = "absTime.seconds"
TP = "(absTime.seconds/8.0)"                      # 8 s units, like the old uP.x

# ---------------- demo (preview only): periodic 8 s test picture, all native TOPs ----------------
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
def dres(o):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = 'parent(2).par.Resolutionw'; o.par.resolutionh.expr = 'parent(2).par.Resolutionh'; return o
def dn(typ, name, *ins, **kw): return dres(nat(d, typ, name, *ins, **kw))
AA = "(2*math.pi*%s)" % TP
nz0 = dn('noiseTOP', 'bg_noise', type='simplex3d', period=0.35, amp=0.05, offset=0.05, mono=True, harmon=3,
         tx="=0.3*math.cos(%s)" % AA, ty="=0.3*math.sin(%s)" % AA)          # moves on a circle in noise space: loops every 8 s
def stripes(name, kind, per):
    r = dn('rampTOP', name + '_ramp', type=kind, period=per, extendleft='repeat', extendright='sameasleft')
    return dn('thresholdTOP', name, r, threshold=0.5, comparator='less')
sx, sy = stripes('stripes_x', 'horizontal', 1 / 12.0), stripes('stripes_y', 'vertical', 1 / 12.0)
chk = dn('levelTOP', 'checker', dn('compositeTOP', 'checker_xor', sx, sy, operand='difference'), brightness1=0.05)
vl = dn('levelTOP', 'vlines', stripes('stripes_v', 'horizontal', 1 / 6.0), brightness1=0.03)
base = dn('compositeTOP', 'base', nz0, chk, vl, operand='add')
layers = []
for i in range(6):
    k1 = 1 + i % 2; k2 = 1 + i // 3
    r = (0.10 + 0.025 * i) * 0.5625
    cx = "=math.sin(%s*%d+%d*1.7)*0.4" % (AA, k1, i); cy = "=math.cos(%s*%d+%d*2.3)*0.30" % (AA, k2, i)
    tone = (1.0, 0.08, 0.05) if i == 2 else (0.92, 0.9, 0.84)
    grad = dn('circleTOP', 'grad%d' % i, radiusx=r, radiusy=r, softness=r, centerx=cx, centery=cy, softnesstype='halfcosine',
              fillcolorr=tone[0] * 1.25, fillcolorg=tone[1] * 1.25, fillcolorb=tone[2] * 1.25, fillalpha=1,
              bgcolorr=tone[0] * 0.15, bgcolorg=tone[1] * 0.15, bgcolorb=tone[2] * 0.15, bgalpha=1)
    edge = dn('circleTOP', 'edge%d' % i, radiusx=r, radiusy=r, softness=0.003, centerx=cx, centery=cy, fillcolorr=1, fillcolorg=1, fillcolorb=1,
              fillalpha=1, bgalpha=0, bgcolorr=0, bgcolorg=0, bgcolorb=0)
    body = dn('compositeTOP', 'disc%d' % i, grad, edge, operand='inside')
    ring = dn('circleTOP', 'ring%d' % i, radiusx=r * 1.35, radiusy=r * 1.35, softness=0.001, centerx=cx, centery=cy, fillalpha=0, bgalpha=0,
              borderwidth=0.003, borderr=tone[0] * 0.7, borderg=tone[1] * 0.7, borderb=tone[2] * 0.7, borderalpha="=0.5+0.5*math.sin(%s*3+%d)" % (AA, i))
    layers += [ring, body]
bar = dn('rectangleTOP', 'bar', sizex=0.8 * 0.5625, sizey=0.05, centerx=0, centery=-0.2, rotate="=-%s*57.2958" % AA,
         fillcolorr=0.9, fillcolorg=0.9, fillcolorb=0.85, fillalpha=1, bgalpha=0, bgcolorr=0, bgcolorg=0, bgcolorb=0)
sweep = dn('rectangleTOP', 'sweep', sizex=1, sizey=0.012, centery="=(%s %% 1)-0.5" % TP, fillcolorr=0.4, fillcolorg=0.4, fillcolorb=0.4, fillalpha=1,
           bgalpha=0, bgcolorr=0, bgcolorb=0, bgcolorg=0)
strip = dn('rampTOP', 'range_strip', type='horizontal')
stripm = dn('rectangleTOP', 'strip_area', sizex=1, sizey=0.07, centery=0.465, fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgalpha=0,
            bgcolorr=0, bgcolorg=0, bgcolorb=0)
stripc = dn('compositeTOP', 'strip_rgb', strip, stripm, operand='inside')
objs = dn('compositeTOP', 'objects', sweep, bar, *reversed(layers), operand='over')
sc = dn('compositeTOP', 'scene', stripc, objs, base, operand='over')
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(sc); do.par.label = 'demo source'
src = nat(c, 'switchTOP', 'src', d.outputConnectors[0], i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(src)
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
v3_finish(c, COMP, mod=[('Tracking','({v}+{b1})'),('Jitter','({v}+{beat})')])
report(c)
