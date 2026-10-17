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
        for g in c.findChildren():
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
COMP = 'TOP_optical_flow'
import colorsys
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('smear', 'Smear / advect feedback'), ('warp', 'Warp by flow'), ('viz', 'Flow visualization (HSV)')], 0),
    ('Gain', 'float', 1.5, 0, 10),
    ('Persistence', 'float', 0.93, 0, 0.995),
    ('Smoothing', 'float', 0.3, 0, 0.95),
    ('Iterations', 'int', 2, 1, 3),
    ('Regularization', 'float', 0.004, 0.0001, 0.1),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [
    ('Resolution', 'wh', (1280, 720)),
    ('Flowscale', 'float', 0.25, 0.0625, 1),
], page='Render')
look_pg(c)

# ---------------------------------------------------------------- demo source (native)
def hsv_rgb(h, s, v): return colorsys.hsv_to_rgb(h % 1.0, s, v)
def mono_rgb(h, v):
    g = v * (0.35 + 0.65 * ((h * 3) % 1.0)) * 0.9
    return (g * .96, g * .94, g * .89)
LOOK = 'parent(2).par.Look.menuIndex'
ACC = 'parent(2).par.Accent'
RES_H = 'parent(2).par.Resolutionh'
RES_W = 'parent(2).par.Resolutionw'
def colexpr(orig, mono, accent=None):
    """3 expressions: orig colour, or (mono colour mixed with red by Accent)."""
    out = []
    for k in range(3):
        m = '%r' % mono[k]
        if accent is not None:
            m = '(%s*(1-%s)+%r*%s)' % (m, ACC, accent[k], ACC)
        out.append('(%r if %s==0 else %s)' % (orig[k], LOOK, m))
    return out
def setcol(o, prefix, exprs, alpha=None):
    for ch, e in zip('rgb', exprs):
        o.par[prefix + ch].expr = e
    if alpha is not None: o.par[prefix[:-0 or None] + 'alpha'] = alpha

d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
def dres(o):
    if 'justifyh' in o.par.__dir__() or hasattr(o.par, 'justifyh'):
        o.par.justifyh = 'center'; o.par.justifyv = 'center'
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RES_W; o.par.resolutionh.expr = RES_H
    o.par.format = 'rgba16float'
# background: flat grey + hue ramp + soft noise, desaturated and dimmed for Mono
b_const = d.create(td.constantTOP, 'bg_flat'); dres(b_const)
for ch in 'rgb': b_const.par['color' + ch] = 0.10
b_const.par.alpha = 1
keys = d.create(td.tableDAT, 'bg_keys'); keys.appendRow(['pos', 'r', 'g', 'b', 'a'])
for i in range(9):
    h = 0.5 * i / 8
    keys.appendRow([i / 8] + [x * 0.10 for x in hsv_rgb(h, .6, 1.0)] + [1])
b_ramp = d.create(td.rampTOP, 'bg_hue'); b_ramp.par.type = 'horizontal'; b_ramp.par.dat = keys; dres(b_ramp)
b_noise = d.create(td.noiseTOP, 'bg_noise'); b_noise.par.type = 'simplex2d'; b_noise.par.period = 0.14
b_noise.par.amp = 0.05; b_noise.par.offset = 0.05; b_noise.par.mono = True; b_noise.par.aspectcorrect = True; dres(b_noise)
b_sum = d.create(td.compositeTOP, 'bg_sum'); b_sum.par.operand = 'add'
for i, s in enumerate((b_const, b_ramp, b_noise)): b_sum.inputConnectors[0].connect(s) if i == 0 else b_sum.inputConnectors[i].connect(s)
b_sum.par.format = 'rgba16float'
b_dim = d.create(td.levelTOP, 'bg_dim'); b_dim.inputConnectors[0].connect(b_sum); b_dim.par.brightness1.expr = '1 if %s==0 else 0.12' % LOOK
b_sat = d.create(td.hsvadjustTOP, 'bg_sat'); b_sat.inputConnectors[0].connect(b_dim); b_sat.par.saturationmult.expr = '1 if %s==0 else 0' % LOOK
b_opq = d.create(td.reorderTOP, 'bg_opaque'); b_opq.inputConnectors[0].connect(b_sat)
for _ch in ('red', 'green', 'blue'):
    b_opq.par['output' + _ch + 'chan'] = _ch
b_opq.par.outputalphachan = 'one'; b_opq.par.format = 'rgba16float'
layers = [b_opq]
# five textured discs with a hot core, each drifting on a Lissajous path
for i in range(5):
    r_ = .11 + .025 * i
    circ = d.create(td.circleTOP, 'disc%d_shape' % i); dres(circ)
    circ.par.radiusunit = 'pixels'; circ.par.radiusx.expr = circ.par.radiusy.expr = '%r*%s' % (r_, RES_H)
    circ.par.centerunit = 'fraction'; circ.par.centerx = 0; circ.par.centery = 0
    circ.par.antialias = True; circ.par.bgalpha = 0
    acc = (1.0, 0.04, 0.04) if i == 2 else None
    ce = colexpr(hsv_rgb(.12 * i, .85, 1.0), mono_rgb(.12 * i, 1.0), (0.9, 0.04, 0.04) if acc else None)
    for ch, e in zip('rgb', ce): circ.par['fillcolor' + ch].expr = e
    circ.par.fillalpha = 1
    tex = d.create(td.noiseTOP, 'disc%d_tex' % i); tex.par.type = 'simplex2d'; tex.par.seed = i * 7 + 1
    tex.par.period = 0.05; tex.par.amp = 0.325; tex.par.offset = 0.675; tex.par.mono = True; tex.par.alpha = 'one'; dres(tex)
    tex.par.aspectcorrect = True
    mul = d.create(td.compositeTOP, 'disc%d_tx' % i); mul.par.operand = 'multiply'
    mul.inputConnectors[0].connect(circ); mul.inputConnectors[1].connect(tex); mul.par.format = 'rgba16float'
    core = d.create(td.circleTOP, 'disc%d_core' % i); dres(core)
    core.par.radiusunit = 'pixels'; core.par.radiusx.expr = core.par.radiusy.expr = '%r*%s' % (r_ * .55, RES_H)
    core.par.centerunit = 'fraction'; core.par.centerx = 0; core.par.centery = 0
    core.par.softness = 0.08; core.par.softnessunit = 'fraction'; core.par.bgalpha = 0
    for ch in 'rgb': core.par['fillcolor' + ch] = 1.0
    core.par.fillcolorg = 0.9; core.par.fillcolorb = 0.7; core.par.fillalpha = 0.8
    ov = d.create(td.compositeTOP, 'disc%d_hot' % i); ov.par.operand = 'over'
    ov.inputConnectors[0].connect(core); ov.inputConnectors[1].connect(mul); ov.par.format = 'rgba16float'
    tr = d.create(td.transformTOP, 'disc%d_move' % i); tr.inputConnectors[0].connect(ov)
    tr.par.tunit = 'pixels'
    tr.par.tx.expr = "math.sin(absTime.seconds*%r+%r)*.55*(%s/%s)*.8*%s" % (.35 + .11 * i, i * 1.7, RES_W, RES_H, RES_H)
    tr.par.ty.expr = "math.cos(absTime.seconds*%r+%r)*.33*%s" % (.27 + .09 * i, i * 2.3, RES_H)
    tr.par.extend = 'zero'; tr.par.format = 'rgba16float'; dres(tr)
    layers.append(tr)
# rotating bar with bright ends
bar = d.create(td.rectangleTOP, 'bar_body'); dres(bar)
bar.par.sizeunit = 'pixels'; bar.par.sizex.expr = '0.84*%s' % RES_H; bar.par.sizey.expr = '0.06*%s' % RES_H
bar.par.centerunit = 'fraction'; bar.par.centerx = 0; bar.par.centery = 0
be = colexpr(tuple(x * .85 for x in hsv_rgb(.55, .7, 1.0)), tuple(x * .85 for x in mono_rgb(.55, 1.0)), (0.8, 0.03, 0.03))
for ch, e in zip('rgb', be): bar.par['fillcolor' + ch].expr = e
bar.par.fillalpha = 1; bar.par.bgalpha = 0
barparts = [bar]
for sgn in (-1, 1):
    cap = d.create(td.rectangleTOP, 'bar_cap%d' % (1 if sgn > 0 else 0)); dres(cap)
    cap.par.sizeunit = 'pixels'; cap.par.sizex.expr = '0.12*%s' % RES_H; cap.par.sizey.expr = '0.06*%s' % RES_H
    cap.par.centerunit = 'pixels'; cap.par.centerx.expr = '%d*0.36*%s' % (sgn, RES_H); cap.par.centery = 0
    ce2 = colexpr(tuple(x * 3 for x in hsv_rgb(.55, .7, 1.0)), tuple(x * 3 for x in mono_rgb(.55, 1.0)), (2.4, 0.1, 0.1))
    for ch, e in zip('rgb', ce2): cap.par['fillcolor' + ch].expr = e
    cap.par.fillalpha = 1; cap.par.bgalpha = 0
    barparts.append(cap)
bsum = d.create(td.compositeTOP, 'bar_sum'); bsum.par.operand = 'over'; bsum.par.format = 'rgba16float'
for i, s in enumerate(reversed(barparts)): bsum.inputConnectors[i].connect(s)
bmove = d.create(td.transformTOP, 'bar_move'); bmove.inputConnectors[0].connect(bsum)
bmove.par.tunit = 'pixels'; bmove.par.ty.expr = '-0.18*%s' % RES_H; bmove.par.rotate.expr = 'absTime.seconds*0.7*57.29578'
bmove.par.extend = 'zero'; bmove.par.format = 'rgba16float'; dres(bmove)
layers.append(bmove)
scene = d.create(td.compositeTOP, 'scene'); scene.par.operand = 'over'; scene.par.format = 'rgba16float'
for i, s in enumerate(reversed(layers)): scene.inputConnectors[i].connect(s)
o = d.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(scene); o.par.label = 'demo source'
i1 = c.create(td.inTOP, 'in1')
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(src); src.par.format = 'rgba16float'

# ---------------------------------------------------------------- optical flow (Lucas-Kanade, GLSL) at reduced resolution
FW = 'max(16,int(parent().par.Resolutionw*parent().par.Flowscale))'
FH = 'max(16,int(parent().par.Resolutionh*parent().par.Flowscale))'
def flowres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = FW; o.par.resolutionh.expr = FH
cur = c.create(td.nullTOP, 'cur'); cur.inputConnectors[0].connect(src); flowres(cur)
cur.par.format = 'rgba16float'
cur.par.filtertype = 'mipmap' if 'mipmap' in cur.par.filtertype.menuNames else cur.par.filtertype.val
prv = c.create(td.feedbackTOP, 'prev'); prv.inputConnectors[0].connect(cur); prv.par.top = cur
flowres(prv); prv.par.format = 'rgba16float'; prv.par.reset.expr = 'parent().par.Reset'
zero = c.create(td.constantTOP, 'zero'); flowres(zero); zero.par.format = 'rgba32float'
zero.par.colorr = 0; zero.par.colorg = 0; zero.par.colorb = 0; zero.par.alpha = 1
ffb = c.create(td.feedbackTOP, 'flowfb'); ffb.inputConnectors[0].connect(zero); flowres(ffb); ffb.par.format = 'rgba32float'
ffb.par.reset.expr = 'parent().par.Reset'
fl = glsl(c, 'flow', rd(COMP, 'flow.glsl'), inputs=[cur, prv, ffb], fmt='rgba32float', vecs=[
    ('uP', ['parent().par.Regularization', 'parent().par.Smoothing', 'parent().par.Iterations', 12])])
flowres(fl); fl.par.inputextenduv = 'hold'
fnull = c.create(td.nullTOP, 'flow_final'); fnull.inputConnectors[0].connect(fl); fnull.par.format = 'rgba32float'
ffb.par.top = fnull

def reorder(name, srcs, chans, res=flowres, fmt='rgba32float'):
    r = c.create(td.reorderTOP, name)
    for k, s in enumerate(srcs): r.inputConnectors[k].connect(s)
    for ch, (inp, chan) in zip(('red', 'green', 'blue', 'alpha'), chans):
        r.par['output' + ch] = 'input%d' % inp; r.par['output' + ch + 'chan'] = chan
    if res: res(r)
    r.par.format = fmt
    return r

# ---------------------------------------------------------------- effects (native)
OUTRES = lambda o: setres(o)
# pixels moved per frame at OUTPUT resolution = speed_px * out width / flow width
SC = "(parent().par.Resolutionw/(%s))" % FW
# --- smear: previous output dragged along the flow, re-injected with the source
ofb = c.create(td.feedbackTOP, 'fxfb'); ofb.inputConnectors[0].connect(src); setres(ofb); ofb.par.format = 'rgba16float'
ofb.par.reset.expr = 'parent().par.Reset'
adv = c.create(td.displaceTOP, 'smear_advect'); adv.inputConnectors[0].connect(ofb); adv.inputConnectors[1].connect(fnull)
adv.par.midpointx = 0; adv.par.midpointy = 0
adv.par.displaceweightx.expr = '-parent().par.Gain/2'; adv.par.displaceweighty.expr = '-parent().par.Gain/2'
adv.par.extend = 'hold'; setres(adv); adv.par.format = 'rgba16float'
w3 = c.create(td.levelTOP, 'smear_keep'); w3.inputConnectors[0].connect(fnull); w3.par.format = 'rgba32float'   # speed (B) -> keep weight
w3.par.clampinput = 'unclamped'; w3.par.clamp = True; w3.par.clamplow2 = 0; w3.par.clamphigh2.expr = 'parent().par.Persistence'
w3.par.inlow = 0; w3.par.inhigh.expr = '0.5/' + SC
w3.par.outlow.expr = '0.5*parent().par.Persistence'; w3.par.outhigh.expr = 'parent().par.Persistence'
flowres(w3)
# Matte TOP: advected history (in1) over the source (in2) through the keep weight (blue channel of in3)
smear = c.create(td.matteTOP, 'smear'); smear.inputConnectors[0].connect(adv); smear.inputConnectors[1].connect(src); smear.inputConnectors[2].connect(w3)
smear.par.mattechannel = 'blue'; setres(smear); smear.par.format = 'rgba16float'
# --- warp: source displaced by the flow
warp = c.create(td.displaceTOP, 'warp'); warp.inputConnectors[0].connect(src); warp.inputConnectors[1].connect(fnull)
warp.par.midpointx = 0; warp.par.midpointy = 0
warp.par.displaceweightx.expr = '-4*parent().par.Gain'; warp.par.displaceweighty.expr = '-4*parent().par.Gain'
warp.par.extend = 'hold'; setres(warp); warp.par.format = 'rgba16float'
# --- viz: hue = direction (colour wheel looked up with the unit flow vector), brightness = 1-exp(-speed*gain)
rg1 = reorder('viz_rg', [fnull], [(1, 'red'), (1, 'green'), (1, 'zero'), (1, 'zero')])
ln = c.create(td.mathTOP, 'viz_len'); ln.inputConnectors[0].connect(rg1); ln.par.chanop = 'len'; flowres(ln); ln.par.format = 'rgba32float'
lnn = reorder('viz_len4', [ln], [(1, 'red')] * 4)
lne = c.create(td.mathTOP, 'viz_len_eps'); lne.inputConnectors[0].connect(lnn); lne.par.postoff = 1e-9; flowres(lne); lne.par.format = 'rgba32float'
unit = c.create(td.compositeTOP, 'viz_unit'); unit.par.operand = 'divide'; unit.inputConnectors[0].connect(rg1); unit.inputConnectors[1].connect(lne)
flowres(unit); unit.par.format = 'rgba32float'
dmap = c.create(td.mathTOP, 'viz_dirmap'); dmap.inputConnectors[0].connect(unit); dmap.par.gain = 0.5; dmap.par.postoff = 0.5; flowres(dmap); dmap.par.format = 'rgba32float'
wk = c.create(td.tableDAT, 'wheel_keys'); wk.appendRow(['pos', 'r', 'g', 'b', 'a'])
N = 36
for i in range(N + 1):
    wk.appendRow([i / N] + list(hsv_rgb(i / N + 0.5, 1, 1)) + [1])
wheel = c.create(td.rampTOP, 'viz_wheel'); wheel.par.type = 'radial'; wheel.par.dat = wk
wheel.par.outputresolution = 'custom'; wheel.par.resolutionw = 256; wheel.par.resolutionh = 256; wheel.par.format = 'rgba16float'
hue = c.create(td.remapTOP, 'viz_hue'); hue.inputConnectors[0].connect(wheel); hue.inputConnectors[1].connect(dmap)
hue.par.resolutionsource = 'input2'; hue.par.horzsource = 'red'; hue.par.vertsource = 'green'; hue.par.extend = 'hold'; hue.par.format = 'rgba16float'
sp2 = reorder('viz_speed', [fnull], [(1, 'blue')] * 4, res=None)
sp2.par.format = 'rgba32float'
e1 = c.create(td.mathTOP, 'viz_scale'); e1.inputConnectors[0].connect(sp2); e1.par.gain.expr = '-0.6*parent().par.Gain*' + SC; e1.par.format = 'rgba32float'
e2 = c.create(td.functionTOP, 'viz_exp'); e2.inputConnectors[0].connect(e1); e2.par.funcrgba = 'exp'; e2.par.format = 'rgba32float'
e3 = c.create(td.mathTOP, 'viz_value'); e3.inputConnectors[0].connect(e2); e3.par.gain = -1; e3.par.postoff = 1; e3.par.format = 'rgba32float'
vcol = c.create(td.compositeTOP, 'viz_color'); vcol.par.operand = 'multiply'; vcol.inputConnectors[0].connect(hue); vcol.inputConnectors[1].connect(e3)
vcol.par.size = 'input1'; vcol.par.format = 'rgba16float'
vup = c.create(td.resolutionTOP, 'viz_up'); vup.inputConnectors[0].connect(vcol); setres(vup); vup.par.format = 'rgba16float'
vsrc = c.create(td.levelTOP, 'viz_src'); vsrc.inputConnectors[0].connect(src); vsrc.par.brightness1 = 0.12; setres(vsrc); vsrc.par.format = 'rgba16float'
vadd = c.create(td.compositeTOP, 'viz_add'); vadd.par.operand = 'add'; vadd.inputConnectors[0].connect(vup); vadd.inputConnectors[1].connect(vsrc)
setres(vadd); vadd.par.format = 'rgba16float'
vopq = reorder('viz_opaque', [vadd], [(1, 'red'), (1, 'green'), (1, 'blue'), (1, 'one')], res=OUTRES, fmt='rgba16float')
# --- pick the mode, force alpha 1, freeze when Active is off
modesw = c.create(td.switchTOP, 'mode_active')
for i_, s_ in enumerate((smear, warp, vopq, ofb)): modesw.inputConnectors[i_].connect(s_)
modesw.par.index.expr = 'parent().par.Mode.menuIndex if parent().par.Active else 3'; setres(modesw)
fxn = c.create(td.nullTOP, 'fx_out'); fxn.inputConnectors[0].connect(modesw)
ofb.par.top = fxn
o1 = c.create(td.outTOP, 'out1'); o1.inputConnectors[0].connect(fxn)
o2 = c.create(td.outTOP, 'out2'); o2.inputConnectors[0].connect(fnull)
v3_finish(c, COMP, mod=[('Gain', '({v}*(1+{b1}*2))')], outlabels={'out2': 'flow'})
report(c)
