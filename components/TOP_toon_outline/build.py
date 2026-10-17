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
COMP = 'TOP_toon_outline'
c = new_comp(COMP)
add_pars(c, [
    ('Style', 'menu', [('ink', 'Ink line'), ('neon', 'Neon glow')], 0),
    ('Levels', 'int', 4, 2, 16),
    ('Posterizesoft', 'float', 0.08, 0, 0.5),
    ('Edgecolor', 'rgb', (0.02, 0.02, 0.05)),
    ('Edgewidth', 'float', 1.5, 0.5, 6),
    ('Threshold', 'float', 0.25, 0, 2),
    ('Edgesoft', 'float', 0.2, 0.01, 1),
    ('Colorweight', 'float', 0.5, 0, 1),
    ('Glowsize', 'int', 12, 1, 80),
    ('Glowamount', 'float', 1.0, 0, 4),
    ('Dim', 'float', 0.25, 0, 1),
    ('Mix', 'float', 1.0, 0, 1, True),
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
# background: dim rainbow gradient + soft noise + faint checker (original look) or near-black checker + noise (mono)
import colorsys as _cs
LOOK = 'parent(2).par.Look.menuIndex'
RWx = 'parent(2).par.Resolutionw'
def keytable(name, rows):
    t = d.create(td.tableDAT, name)
    t.clear(); t.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for r_ in rows: t.appendRow(r_)
    return t
def ramp(name, typ, rows, period, phase, inp=None, operand='multiply'):
    r_ = d.create(td.rampTOP, name)
    r_.par.dat = keytable(name + '_keys', rows)
    shape(r_, type=typ, period=period, phase=phase, extendleft='repeat', fitaspect='fithorz', interpnotches='linear')
    if inp is not None:
        r_.par.combineinput = 'compres'; r_.par.operand = operand; r_.inputConnectors[0].connect(inp)
    return r_
NB = 12
hue = ramp('bg_hue', 'horizontal', [[i / NB] + [0.1 * x + 0.1 for x in _cs.hsv_to_rgb(i / NB, 0.6, 1.0)] + [1] for i in range(NB + 1)], 2.0, '0.02*' + T)
hue_l = shape(d.create(td.levelTOP, 'bg_hue_amount'), brightness1='0 if %s else 1' % LOOK); hue_l.inputConnectors[0].connect(hue)
nz = shape(d.create(td.noiseTOP, 'bg_noise'), type='perlin2d', mono=True, period=0.15, harmon=0, amp='0.01 if %s else 0.05' % LOOK, offset='0.02 if %s else 0.05' % LOOK, aspectcorrect=True)
chk_x = ramp('chk_x', 'horizontal', [[0, 0, 0, 0, 1], [.49999, 0, 0, 0, 1], [.5, 1, 1, 1, 1], [1, 1, 1, 1, 1]], 'parent(2).par.Resolutionh/14/' + RWx, 0)
chk = ramp('chk_y', 'vertical', [[0, 0, 0, 0, 1], [.49999, 0, 0, 0, 1], [.5, 1, 1, 1, 1], [1, 1, 1, 1, 1]], 1 / 14.0, 0, inp=chk_x)
chk_l = shape(d.create(td.levelTOP, 'bg_checker_amount'), brightness1='0.012 if %s else 0.06' % LOOK); chk_l.inputConnectors[0].connect(chk)
bg = shape(d.create(td.compositeTOP, 'bg'), operand='add')
bg.par.tops = ''
for k_, s_ in enumerate((hue_l, nz, chk_l)): bg.inputConnectors[k_].connect(s_)
body = shape(d.create(td.rectangleTOP, 'bar_body'), sizeunit='pixels', sizex=H+'*0.84', sizey=H+'*0.06',
             fillcolorr="op('colors').module.bar(%s,0,0)" % T, fillcolorg="op('colors').module.bar(%s,1,0)" % T, fillcolorb="op('colors').module.bar(%s,2,0)" % T, fillalpha=1,
             bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
clr = shape(d.create(td.constantTOP, 'clear'), colorr=0, colorg=0, colorb=0, alpha=0)
body.inputConnectors[0].connect(clr)
last = body
for nm, cx in (('cap_l', -0.36), ('cap_r', 0.36)):
    cp = shape(d.create(td.rectangleTOP, nm), sizeunit='pixels', sizex=H+'*0.12', sizey=H+'*0.06', centerunit='pixels', centerx='%s*%s' % (H, cx), centery=0,
               fillcolorr="op('colors').module.bar(%s,0,1)" % T, fillcolorg="op('colors').module.bar(%s,1,1)" % T, fillcolorb="op('colors').module.bar(%s,2,1)" % T, fillalpha=1,
               bgalpha=0, borderalpha=0, combineinput='compres', operand='over')
    cp.inputConnectors[0].connect(last); last = cp
xf = shape(d.create(td.transformTOP, 'bar_move'), rotate=T + '*0.7*57.2958', ty=-0.18, tunit='fraction')
xf.par.bgcolora = 0
xf.inputConnectors[0].connect(last)
under = shape(d.create(td.compositeTOP, 'bar_over_bg'), operand='over'); under.inputConnectors[0].connect(xf); under.inputConnectors[1].connect(bg)   # Composite: input 1 is on top
prev = under
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




# ---------------- toon + outline (built-in nodes) ----------------
import math as _m2
RES = lambda o_: (setres(o_), setattr(o_.par, 'format', 'rgba16float'))
P_ = lambda n_: 'parent().par.' + n_
def mkn(typ, name, inputs=(), **kw):
    o_ = c.create(typ, name)
    for k_, s_ in enumerate(inputs): o_.inputConnectors[k_].connect(s_)
    RES(o_)
    for k_, v_ in kw.items():
        p_ = getattr(o_.par, k_)
        if isinstance(v_, str) and not p_.isMenu: p_.expr = v_
        else: p_.val = v_
    return o_
def zero_mix(o_):
    for ch_ in ('red', 'green', 'blue', 'alpha'):
        for j_ in range(1, 5): getattr(o_.par, ch_ + str(j_)).val = 0
def reduced(o_, fac):
    o_.par.outputresolution = 'custom'
    o_.par.resolutionw.expr = 'max(1, int(round(parent().par.Resolutionw/%s)))' % fac
    o_.par.resolutionh.expr = 'max(1, int(round(parent().par.Resolutionh/%s)))' % fac
    o_.par.format = 'rgba16float'

# 1. edges: one small GLSL pass (Sobel on luma and colour, blended by Colorweight, then smoothstep threshold). Kept as GLSL: a native Convolve/Math
#    network (Sobel kernels, vector lengths, threshold curve) measured 2-3x slower on the GPU (see README).
EW = 'parent().par.Edgewidth*(1+%s*2)' % _CH('band1')
ed = glsl(c, 'edges', rd(COMP, 'sobel.glsl'), inputs=[src], res=True, vecs=[
    ('uP', [EW, P_('Threshold'), P_('Edgesoft'), P_('Colorweight')])])
ed.par.inputextenduv = 'hold'

def curve_chop(name, expr, n=4096):
    p_ = c.create(td.patternCHOP, name + '_ramp'); p_.par.wavetype = 'ramp'; p_.par.length = n; p_.par.rate = n; p_.par.channelname = 'r g b'
    e_ = c.create(td.expressionCHOP, name); e_.inputConnectors[0].connect(p_); e_.par.expr0expr.expr = expr
    return e_

# 3. toon posterize: a Lookup reads max(r,g,b) and returns (posterized value / value), a Composite multiply applies it, so hue and saturation are kept
mkdat(c, 'toon_curve', """import math
def ratio(v, L, k):
    L = max(int(round(L)), 2); k = max(k, 0.001)
    if v < 1e-4: return 1.0
    vl = v * L; fl = math.floor(vl); fr = vl - fl
    t = min(max((fr - (0.5 - k)) / (2 * k), 0.0), 1.0); s = t * t * (3 - 2 * t)
    return ((fl + s) / L) / v
""")
ratio = curve_chop('posterize_curve', "op('toon_curve').module.ratio(me.inputVal, %s, %s)" % (P_('Levels'), P_('Posterizesoft')))
rtex = c.create(td.choptoTOP, 'posterize_curve_image'); rtex.par.chop = ratio     # the curve as a 4096 x 1 image
rtex.par.dataformat = 'rgb'; rtex.par.format = 'rgba32float'
rt = c.create(td.lookupTOP, 'posterize_ratio'); rt.inputConnectors[0].connect(src); rt.inputConnectors[1].connect(rtex); rt.par.channel = 'rgbmax'; RES(rt)
toon = mkn(td.compositeTOP, 'toon', [src, rt], operand='multiply')

# 4a. ink: edge colour laid over the toon image (Channel Mix makes a premultiplied edge-colour layer, alpha = edge strength)
ecol = c.create(td.channelmixTOP, 'edge_layer'); ecol.inputConnectors[0].connect(ed); zero_mix(ecol)
ecol.par.red1.expr = P_('Edgecolorr'); ecol.par.green1.expr = P_('Edgecolorg'); ecol.par.blue1.expr = P_('Edgecolorb'); ecol.par.alpha1 = 1; RES(ecol)
ink = mkn(td.compositeTOP, 'ink', [ecol, toon], operand='over')   # first input is on top

# 4b. neon: dimmed image + coloured (edge*1.5 + glow*Glowamount*2) + a hot white core (edge^2*0.6). Blur TOP for the glow, then one small GLSL pass for the sum
#     (the same sum built from Level / Reorder / Channel Mix / Composite TOPs was 2x slower than the old shader in this style). Neither cooks unless Style = neon.
glow = mkn(td.blurTOP, 'glow', [ed], type='gaussian', size='max(1,%s)' % P_('Glowsize'))
neon = glsl(c, 'neon', rd(COMP, 'neon.glsl'), inputs=[src, ed, glow, rt], res=True, vecs=[
    ('uA', [P_('Edgecolorr'), P_('Edgecolorg'), P_('Edgecolorb'), '%s*2*(1+%s*2)' % (P_('Glowamount'), _CH('beat'))]),
    ('uC', [P_('Dim'), 0, 0, 0])])

sty = c.create(td.switchTOP, 'style'); sty.inputConnectors[0].connect(ink); sty.inputConnectors[1].connect(neon); sty.par.index.expr = P_('Style') + '.menuIndex'
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(sty)
o2 = c.create(td.outTOP, 'out2'); o2.inputConnectors[0].connect(ed)
v3_finish(c, COMP, outlabels={'out2': 'edges'})
report(c)
