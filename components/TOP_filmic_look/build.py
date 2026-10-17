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
COMP = 'TOP_filmic_look'
c = new_comp(COMP)
add_pars(c, [
    ('Exposure', 'float', 0.0, -4, 4),
    ('Tonemap', 'menu', [('none', 'None'), ('aces', 'ACES'), ('filmic', 'Filmic (Hable)'), ('reinhard', 'Reinhard')], 1),
    ('Bloomamount', 'float', 0.6, 0, 3),
    ('Bloomthreshold', 'float', 0.8, 0, 4),
    ('Bloomknee', 'float', 0.5, 0, 1),
    ('Bloomsize', 'float', 1.0, 0.25, 3),
    ('Glareamount', 'float', 0.5, 0, 3),
    ('Glarelength', 'float', 0.35, 0.02, 1),
    ('Glaretint', 'rgb', (0.6, 0.8, 1.0)),
    ('Chromatic', 'float', 0.5, 0, 3),
    ('Vignette', 'float', 0.45, 0, 1),
    ('Vignettesoft', 'float', 0.6, 0, 1),
    ('Grain', 'float', 0.06, 0, 0.5),
    ('Grainsize', 'float', 1.5, 1, 6),
    ('Gamma', 'float', 1.0, 0.5, 2.5),
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



# ---------------- the grade (built-in nodes) ----------------
RES = lambda o_: (setres(o_), setattr(o_.par, 'format', 'rgba16float'))
def mkn(typ, name, inputs=(), **kw):
    o_ = c.create(typ, name)
    for k_, s_ in enumerate(inputs): o_.inputConnectors[k_].connect(s_)
    RES(o_)
    for k_, v_ in kw.items():
        p_ = getattr(o_.par, k_)
        if isinstance(v_, str) and not p_.isMenu: p_.expr = v_
        else: p_.val = v_
    return o_
P_ = lambda n_: 'parent().par.' + n_

# 1. chromatic aberration: red and blue are scaled in opposite directions, green stays; Reorder picks one channel per input
kca = P_('Chromatic') + '*0.0168'
ca_r = mkn(td.transformTOP, 'ca_red', [src], sx='1/(1+%s)' % kca, sy='1/(1+%s)' % kca, extend='hold')
ca_b = mkn(td.transformTOP, 'ca_blue', [src], sx='1/(1-%s)' % kca, sy='1/(1-%s)' % kca, extend='hold')
ca = mkn(td.reorderTOP, 'chromatic', [ca_r, src, ca_b], outputred='input1', outputredchan='red', outputgreen='input2', outputgreenchan='green',
         outputblue='input3', outputbluechan='blue', outputalpha='input2', outputalphachan='one')

# 2. bright pass with a soft knee: max( x - threshold , k*u^2 ) where u runs 0..1 across the knee (two Level TOPs and a Composite maximum)
KN = '(%s*%s+0.0001)' % (P_('Bloomthreshold'), P_('Bloomknee'))
bpa = mkn(td.levelTOP, 'bright_linear', [src], inlow=P_('Bloomthreshold'), inhigh=P_('Bloomthreshold') + '+1', outlow=0, outhigh=1)
bpa.par.clamp = True; bpa.par.clamplow2 = 0; bpa.par.clamphigh2 = 1000
bpk = mkn(td.levelTOP, 'bright_knee', [src], inlow='%s-%s' % (P_('Bloomthreshold'), KN), inhigh='%s+%s' % (P_('Bloomthreshold'), KN), outlow=0, outhigh=1, gamma2=0.5, brightness2=KN)
bpk.par.clamp = True; bpk.par.clamplow2 = 0; bpk.par.clamphigh2.expr = KN
bp = mkn(td.compositeTOP, 'bright_pass', [bpa, bpk], operand='maximum')

# 3. bloom: five Gaussian Blur TOPs of growing size. Each wider blur runs on a half-size copy of the one before (cheap), a Level sets its weight
levels = []          # (blurred, factor)
prevd = bp
for k_, (fac, sz) in enumerate([(1, 5.0), (2, 10.3), (4, 20.0), (8, 39.7), (16, 50.0)]):
    if fac > 1:      # half-size copy (Level with a smaller custom resolution, bilinear = 2x2 average)
        dn = c.create(td.levelTOP, 'half%d' % fac); dn.inputConnectors[0].connect(prevd)
        dn.par.outputresolution = 'custom'
        dn.par.resolutionw.expr = 'max(1, parent().par.Resolutionw//%d)' % fac; dn.par.resolutionh.expr = 'max(1, parent().par.Resolutionh//%d)' % fac
        dn.par.format = 'rgba16float'; dn.par.inputfiltertype = 'linear'
        prevd = dn
    else:
        dn = bp
    bk = c.create(td.blurTOP, 'blur%d' % (k_ + 1)); bk.inputConnectors[0].connect(dn)
    bk.par.type = 'gaussian'; bk.par.size.expr = 'max(0.5, %s*%s)' % (sz, P_('Bloomsize')); bk.par.format = 'rgba16float'
    bk.par.outputresolution = 'useinput'
    wt = c.create(td.channelmixTOP, 'weight%d' % (k_ + 1)); wt.inputConnectors[0].connect(bk)   # Channel Mix: gain on rgb, alpha 0 so the additive sum keeps the picture's alpha
    wt.par.outputresolution = 'useinput'; wt.par.format = 'rgba16float'
    for ch_ in ('red', 'green', 'blue', 'alpha'):
        for j_ in range(1, 5): getattr(wt.par, ch_ + str(j_)).val = 0
    gexp = '%s*2*(1+%s*2)*%.3f' % (P_('Bloomamount'), _CH('band1'), (1 + 0.6 * k_) / 5.0)
    wt.par.red1.expr = gexp; wt.par.green2.expr = gexp; wt.par.blue3.expr = gexp
    levels.append(wt)

# 4. anamorphic glare: the bright pass is smeared sideways (horizontal-only Blur TOPs) at three widths -- a thin core at full size,
#    a medium streak on a quarter-size copy and a long soft tail on an eighth-size copy -- and a Channel Mix applies tint, amount and each weight
def tint(name, src_, w_):
    t_ = c.create(td.channelmixTOP, name); t_.inputConnectors[0].connect(src_)
    t_.par.outputresolution = 'useinput'; t_.par.format = 'rgba16float'
    for ch_ in ('red', 'green', 'blue', 'alpha'):
        for j_ in range(1, 5): getattr(t_.par, ch_ + str(j_)).val = 0
    for ch_, j_, col_ in (('red', 1, 'r'), ('green', 2, 'g'), ('blue', 3, 'b')):
        getattr(t_.par, ch_ + str(j_)).expr = '%s*4*%s*%s' % (P_('Glaretint' + col_), P_('Glareamount'), w_)
    return t_
def streak(name, src_, f_):
    g_ = c.create(td.blurTOP, name); g_.inputConnectors[0].connect(src_)
    g_.par.type = 'gaussian'; g_.par.filterscalex = 1; g_.par.filterscaley = 0; g_.par.extend = 'hold'; g_.par.format = 'rgba16float'
    g_.par.outputresolution = 'useinput'
    return g_
g_core = tint('glare_core', bp, 0.25)
g_mid = streak('glare_mid', c.op('half4'), 4)
g_mid.par.size.expr = 'max(0.5, %s*parent().par.Resolutionw*0.0701)' % P_('Glarelength')
g_mid_t = tint('glare_mid_tint', g_mid, 0.37)
g_wide = streak('glare_wide', c.op('half8'), 8)
g_wide.par.size.expr = 'max(0.5, %s*parent().par.Resolutionw*0.204)' % P_('Glarelength')
g_wide_t = tint('glare_wide_tint', g_wide, 0.37)

# 4. add everything, apply exposure
tot = mkn(td.compositeTOP, 'add_bloom_glare', [ca] + levels + [g_core, g_mid_t, g_wide_t], operand='add')
EXPO = '2**(%s+%s*0.8)' % (P_('Exposure'), _CH('beat'))
ex = mkn(td.levelTOP, 'exposure', [tot], brightness1=EXPO)
ex8 = mkn(td.levelTOP, 'exposure_eighth', [tot], brightness1=EXPO + '/8')   # same, scaled to 1/8 so HDR values 0-8 fit the Lookup input range 0-1

# 5. tonemap: Lookup TOP through a baked curve (Ramp TOP from a Table DAT); Switch picks None / ACES / Filmic / Reinhard
import math as _m
def _aces(x): return max(0., min(1., (x * (2.51 * x + .03)) / (x * (2.43 * x + .59) + .14)))
def _hable(x): return ((x * (.15 * x + .05) + .004) / (x * (.15 * x + .5) + .06)) - .02 / .3
curves = {'aces': _aces, 'filmic': lambda x: _hable(2 * x) / _hable(11.2), 'reinhard': lambda x: x / (1 + x)}
tmops = [ex]
for nm, fn in curves.items():
    t_ = c.create(td.tableDAT, 'curve_' + nm)
    t_.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for i in range(256):
        p_ = (i / 255.0) ** 2; v_ = fn(8 * p_)
        t_.appendRow([round(p_, 6), v_, v_, v_, 1])
    r_ = c.create(td.rampTOP, 'ramp_' + nm); r_.par.dat = t_
    r_.par.type = 'horizontal'; r_.par.extendleft = 'hold'; r_.par.interpnotches = 'linear'
    r_.par.outputresolution = 'custom'; r_.par.resolutionw = 2048; r_.par.resolutionh = 1; r_.par.format = 'rgba32float'; r_.par.premultrgbbyalpha = False
    lk = c.create(td.lookupTOP, 'tone_' + nm); lk.inputConnectors[0].connect(ex8); lk.inputConnectors[1].connect(r_)
    lk.par.channel = 'independent'   # the curve spans 0..8 (HDR); the input is pre-scaled by 1/8
    RES(lk); tmops.append(lk)
tm = mkn(td.switchTOP, 'tonemap', tmops, index=P_('Tonemap') + '.menuIndex')

# 6. gamma
gm = mkn(td.levelTOP, 'gamma', [tm], gamma1=P_('Gamma'))

# 7. vignette: elliptical circular Ramp -> Level (bright centre, dark corners) -> multiply
vr = c.create(td.rampTOP, 'vignette_ramp')
vr.par.type = 'circular'; vr.par.fitaspect = 'fill'; vr.par.extendleft = 'hold'; vr.par.period = 2.0; vr.par.premultrgbbyalpha = False
vt = c.create(td.tableDAT, 'vignette_keys'); vt.appendRow(['pos', 'r', 'g', 'b', 'a']); vt.appendRow([0, 0, 0, 0, 1]); vt.appendRow([1, 1, 1, 1, 1])
vr.par.dat = vt; RES(vr)
vw = '(%s*0.6+0.05)' % P_('Vignettesoft')
vl = mkn(td.levelTOP, 'vignette_curve', [vr], inlow='(0.75-%s)/1.2' % vw, inhigh='0.75/1.2', outlow=1, outhigh='1-' + P_('Vignette'))
vl.par.clamp = True; vl.par.clamphigh2 = 1
vl.par.clamplow2.expr = '1-' + P_('Vignette')
vg = mkn(td.compositeTOP, 'vignette', [gm, vl], operand='multiply')

# 7. grain: random Noise TOP at 1/Grainsize resolution (new pattern 24x a second), scaled by Level (stretched to full size without smoothing), added
gn = c.create(td.noiseTOP, 'grain_noise')
gn.par.outputresolution = 'custom'
gn.par.resolutionw.expr = "max(1, int(parent().par.Resolutionw/max(%s,1)))" % P_('Grainsize')
gn.par.resolutionh.expr = "max(1, int(parent().par.Resolutionh/max(%s,1)))" % P_('Grainsize')
gn.par.type = 'randomgpu'; gn.par.mono = True; gn.par.format = 'rgba16float'
gn.par.seed.expr = 'int(absTime.seconds*24)'
gl_ = mkn(td.levelTOP, 'grain_amount', [gn], outlow='-%s/2' % P_('Grain'), outhigh='%s/2' % P_('Grain'), inputfiltertype='nearest')
# grain is weaker in the highlights: multiply by (1 - 0.5 * luminance of the picture), made with a Channel Mix
lm = mkn(td.channelmixTOP, 'grain_highlight_fade', [vg], red1=-0.15, red2=-0.295, red3=-0.055, red4=0, green1=0, green2=0, green3=0, green4=0,
         blue1=0, blue2=0, blue3=0, blue4=0, alpha1=0, alpha2=0, alpha3=0, alpha4=0, constant1=1, constant2=0, constant3=0, constant4=0)
lm.par.green1 = lm.par.red1.eval(); lm.par.green2 = lm.par.red2.eval(); lm.par.green3 = lm.par.red3.eval(); lm.par.constant2 = 1
lm.par.blue1 = lm.par.red1.eval(); lm.par.blue2 = lm.par.red2.eval(); lm.par.blue3 = lm.par.red3.eval(); lm.par.constant3 = 1
gm2 = mkn(td.compositeTOP, 'grain_scaled', [gl_, lm], operand='multiply')
gr = mkn(td.compositeTOP, 'grain', [vg, gm2], operand='add')
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(gr)
v3_finish(c, COMP)
report(c)
