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
COMP = 'TOP_feedback_trails'
c = new_comp(COMP)
add_pars(c, [
    ('Blend', 'menu', [('over', 'Over'), ('add', 'Add'), ('max', 'Max')], 0),
    ('Decay', 'float', 0.965, 0.8, 1.0, True),
    ('Scale', 'float', 1.012, 0.9, 1.1),
    ('Rotate', 'float', 0.4, -10, 10),
    ('Translate', 'xy', (0.0, 0.0)),
    ('Huedrift', 'float', 2.0, -30, 30),
    ('Noiseamount', 'float', 0.4, 0, 3),
    ('Noisescale', 'float', 3.0, 0.1, 30),
    ('Noisespeed', 'float', 0.3, 0, 5),
    ('Inject', 'float', 1.0, 0, 4),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
look_pg(c)

# ---------------- demo source (native ops, preview only) ----------------
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
mkdat(d, 'colors', """import colorsys
def hsv(h, s, v):
    return colorsys.hsv_to_rgb(h % 1.0, s, v)
def mono(h, v):
    g = v * (0.35 + 0.65 * ((h * 3.0) % 1.0)) * 0.9
    return (g * 0.96, g * 0.94, g * 0.89)
def disc(i, t, ch):
    look = parent(2).par.Look.menuIndex; acc = parent(2).par.Accent.eval()
    h = 0.12 * i + t * 0.03
    c = mono(h, 0.7) if look else hsv(h, 0.85, 0.7)
    if look and i == 2:
        c = tuple(a * (1 - acc) + b * acc for a, b in zip(c, (1.0, 0.04, 0.04)))
    return c[ch]
def core(i, t, ch):
    look = parent(2).par.Look.menuIndex; acc = parent(2).par.Accent.eval()
    c = list(disc(i, t, k) + (3.0, 2.7, 2.1)[k] for k in range(3))
    if look and i == 2:
        c = [a * (1 - acc) + b * acc for a, b in zip(c, (3.0, 0.1, 0.1))]
    return c[ch]
def bar(t, ch, hot):
    look = parent(2).par.Look.menuIndex; acc = parent(2).par.Accent.eval()
    import math
    c = mono(0.55, 1.0) if look else hsv(0.55 + 0.1 * math.sin(t), 0.7, 1.0)
    c = [x * (3.0 if hot else 1.0) for x in c]
    if look:
        c = [a * (1 - acc) + b * acc for a, b in zip(c, (1.0 * (3 if hot else 1), 0.04, 0.04))]
    return c[ch]
""")
T = 'absTime.seconds'
H = 'parent(2).par.Resolutionh'
def shape(top, **kw):
    top.par.outputresolution = 'custom'
    top.par.resolutionw.expr = 'parent(2).par.Resolutionw'; top.par.resolutionh.expr = 'parent(2).par.Resolutionh'
    top.par.format = 'rgba16float'
    if hasattr(top.par, 'borderwidth'): top.par.borderwidth = 0
    if hasattr(top.par, 'premultrgbbyalpha'): top.par.premultrgbbyalpha = False
    for k, v in kw.items():
        p = getattr(top.par, k)
        if isinstance(v, str) and not p.isMenu: p.expr = v
        else: p.val = v
    return top
prev = None
# rotating bar: body + two hot end caps, drawn centred then rotated/translated as one image
bg = shape(d.create(td.constantTOP, 'clear'), colorr=0, colorg=0, colorb=0, alpha=0)
body = shape(d.create(td.rectangleTOP, 'bar_body'), sizeunit='pixels', sizex=H+'*0.84', sizey=H+'*0.06',
             fillcolorr="op('colors').module.bar(%s,0,0)" % T, fillcolorg="op('colors').module.bar(%s,1,0)" % T, fillcolorb="op('colors').module.bar(%s,2,0)" % T, fillalpha=1,
             bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
body.inputConnectors[0].connect(bg)
last = body
for nm, cx in (('cap_l', -0.36), ('cap_r', 0.36)):
    cp = shape(d.create(td.rectangleTOP, nm), sizeunit='pixels', sizex=H+'*0.12', sizey=H+'*0.06', centerunit='pixels', centerx='%s*%s' % (H, cx), centery=0,
               fillcolorr="op('colors').module.bar(%s,0,1)" % T, fillcolorg="op('colors').module.bar(%s,1,1)" % T, fillcolorb="op('colors').module.bar(%s,2,1)" % T, fillalpha=1,
               bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
    cp.inputConnectors[0].connect(last); last = cp
xf = shape(d.create(td.transformTOP, 'bar_move'), rotate=T + '*0.7*57.2958', ty=-0.18, tunit='fraction')
xf.par.bgcolora = 0
xf.inputConnectors[0].connect(last)
prev = xf
for k in range(5):
    r = 0.11 + 0.025 * k
    cx = "math.sin(%s*(0.35+0.11*%d)+%d*1.7)*0.55*0.8*parent(2).par.Resolutionw" % (T, k, k)
    cy = "math.cos(%s*(0.27+0.09*%d)+%d*2.3)*0.33*%s" % (T, k, k, H)
    dc = shape(d.create(td.circleTOP, 'disc%d' % k), radiusunit='pixels', radiusx='%s*%s' % (r, H), radiusy='%s*%s' % (r, H), centerunit='pixels',
               centerx=cx, centery=cy, softness=H+'*0.006', softnessunit='pixels',
               fillcolorr="op('colors').module.disc(%d,%s,0)" % (k, T), fillcolorg="op('colors').module.disc(%d,%s,1)" % (k, T), fillcolorb="op('colors').module.disc(%d,%s,2)" % (k, T), fillalpha=1,
               bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
    dc.inputConnectors[0].connect(prev)
    co = shape(d.create(td.circleTOP, 'core%d' % k), radiusunit='pixels', radiusx='%s*%s' % (r * 0.45, H), radiusy='%s*%s' % (r * 0.45, H), centerunit='pixels',
               centerx=cx, centery=cy, softness='%s*%s' % (r * 0.35, H), softnessunit='pixels',
               fillcolorr="op('colors').module.core(%d,%s,0)" % (k, T), fillcolorg="op('colors').module.core(%d,%s,1)" % (k, T), fillcolorb="op('colors').module.core(%d,%s,2)" % (k, T), fillalpha=1,
               bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
    co.inputConnectors[0].connect(dc); prev = co
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(prev); do.par.label = 'demo source'
sw = c.create(td.switchTOP, 'src')
sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(sw); sw.par.format = 'rgba16float'
src = sw

# ---------------- trail loop ----------------
# Kept as ONE GLSL pass (fb.glsl): the native chain (Transform -> Noise/Displace -> HSV Adjust -> Level/Reorder matte ->
# Composite) measured 3x slower on the GPU (see README), so the loop itself stays a single shader.
blk = c.create(td.constantTOP, 'blank'); setres(blk); blk.par.format = 'rgba16float'
blk.par.colorr = 0; blk.par.colorg = 0; blk.par.colorb = 0; blk.par.alpha = 1
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(blk)
fb.par.format = 'rgba16float'; setres(fb)
fb.par.reset.expr = 'parent().par.Reset'
g = glsl(c, 'trails', rd(COMP, 'fb.glsl'), inputs=[fb, src], res=True, vecs=[
    ('uXf', ['parent().par.Scale', 'parent().par.Rotate*0.0174533', 'parent().par.Translatex*0.01', 'parent().par.Translatey*0.01']),
    ('uCol', ['parent().par.Huedrift', 'parent().par.Decay', 'parent().par.Inject', 'parent().par.Active']),
    ('uNz', ['parent().par.Noiseamount', 'parent().par.Noisescale', 'absTime.seconds*parent().par.Noisespeed', 'parent().par.Blend.menuIndex']),
])
g.par.inputextenduv = 'hold'
nul = c.create(td.nullTOP, 'fb_out'); nul.inputConnectors[0].connect(g)
fb.par.top = nul
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(nul)
v3_finish(c, COMP, mod=[('Inject','({v}*(1+{b1}*2))'),('Rotate','({v}+{beat}*8)')])
report(c)
