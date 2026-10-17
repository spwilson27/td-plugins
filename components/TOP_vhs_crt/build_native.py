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

# ======================= tape + CRT as a native network =======================
tape_on = "%sMode.menuIndex in (0, 2)" % P
crt_on = "%sMode.menuIndex in (1, 2)" % P
ev = c.create(td.constantCHOP, 'events')
ev.comment = 'frame-rate values: frame index (30 fps) and the interlace field'
for k, (n, e) in enumerate([('frame', "int(absTime.seconds*30)"), ('field', "int(absTime.seconds*30) % 2"), ('P', TP)]):
    getattr(ev.par, 'name%d' % k).val = n; getattr(ev.par, 'value%d' % k).expr = e
E = lambda n: "op('events')['%s']" % n
def stage(name, a, b, on):
    s = nat(c, 'switchTOP', name, a, b); s.par.index.expr = "(1 if (%s) else 0)%s" % (on, F); return s
def rows(o, w="2", h=None):          # low-res "one value per scanline" map: 2 px wide, as tall as the picture
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = w; o.par.resolutionh.expr = h or RH; return o
def scale(o, name, gain):
    return nat(c, 'mathTOP', name, o, gain="=" + gain)
def up(o, name, filt='linear'):
    return nat(c, 'resolutionTOP', name, o, outputresolution='custom', resolutionw="=" + RW, resolutionh="=" + RH, inputfiltertype=filt, filtertype=filt)

# ---- A. horizontal offset per scanline (all in one tiny map, then one Displace TOP) ----
wob = rows(nat(c, 'noiseTOP', 'wobble_noise', type='simplex3d', period=0.45, harmon=2, amp=1, offset=0, mono=True, sx=0.001, tz="=%s*0.25" % T))
wob_s = scale(wob, 'wobble', "%sWobble*%s*0.006*1.2" % (P, A))
jit_n = rows(nat(c, 'noiseTOP', 'jitter_noise', type='randomgpu', mono=True, seed="=" + E('frame'), amp=1, offset=0))
jit_p = rows(nat(c, 'noiseTOP', 'jitter_pick', type='randomgpu', mono=True, seed="=%s+3" % E('frame'), amp=1, offset=0))
jit_m = nat(c, 'thresholdTOP', 'jitter_rows', jit_p, rgb='red', comparator='less', threshold=0.2)      # ~40 % of the lines
jit_x = nat(c, 'compositeTOP', 'jitter_masked', jit_n, jit_m, operand='multiply')
jit_s = scale(jit_x, 'jitter', "%sJitter*%s*0.0015" % (P, A))
par = rows(nat(c, 'rampTOP', 'odd_rows_ramp', type='vertical', period="=2.0/" + RH, extendleft='repeat', extendright='sameasleft'))
par_m = nat(c, 'thresholdTOP', 'odd_rows', par, threshold=0.5, comparator='less')
comb = scale(par_m, 'interlace_comb', "%sInterlace*%s*0.0015*math.sin(2*math.pi*%s*4)" % (P, A, TP))
# tracking bands: 3 soft bands rolling up the picture at 1x, 2x, 3x speed, each torn by per-line noise
bands = []
for k in range(3):
    bands.append(rows(nat(c, 'rectangleTOP', 'track_band%d' % k, sizex=1, sizey="=%f" % (2 * (0.03 + 0.05 * (0.2 + 0.2 * k))), sizeunit='fraction',
                          centery="=((%s*%d+%f) %% 1)-0.5" % (TP, 1 + k, k * 0.37), softness="=%f" % (0.03 + 0.05 * (0.2 + 0.2 * k)),
                          fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False)))
band = nat(c, 'compositeTOP', 'track_bands', *bands, operand='maximum')
trk_n = rows(nat(c, 'noiseTOP', 'tracking_noise', type='randomgpu', mono=True, seed="=%s+9" % E('frame'), amp=1, offset=0))
trk_x = nat(c, 'compositeTOP', 'tracking_torn', trk_n, band, operand='multiply')
trk_s = scale(trk_x, 'tracking', "%sTracking*%s*0.05*1.5" % (P, A))
# head switching: a band at the bottom that drags the lines sideways
head = rows(nat(c, 'rectangleTOP', 'head_band', sizex=1, sizey=0.14, sizeunit='fraction', centery=-0.5, softness=0.07,
                fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False))
HS = "(%sHeadswitch*%s)" % (P, A)
head_amt = nat(c, 'levelTOP', 'head_strength', head, brightness1="=%s" % HS)
head_sq = nat(c, 'mathTOP', 'head_drag', head_amt, preop='square', gain="=0.12*(1+0.5*math.sin(2*math.pi*%s*3))" % TP)
head_n = rows(nat(c, 'noiseTOP', 'head_noise', type='randomgpu', mono=True, seed="=%s+11" % E('frame'), amp=1, offset=0))
head_j = nat(c, 'compositeTOP', 'head_jitter_raw', head_n, head_amt, operand='multiply')
head_js = scale(head_j, 'head_jitter', "0.06")
dxmap = nat(c, 'compositeTOP', 'line_offsets', wob_s, jit_s, comb, trk_s, head_sq, head_js, operand='add')
dx_up = up(dxmap, 'line_offsets_up')
t1 = nat(c, 'displaceTOP', 'displace_lines', src, dx_up, horzsource='red', vertsource='none', midpointx=0, midpointy=0, displaceweightx=0.5, displaceweighty=0, extend='mirror')

# ---- B. luma softness + chroma bleed in YIQ ----
yiq = nat(c, 'channelmixTOP', 'rgb_to_yiq', t1,
          red1=0.299, red2=0.587, red3=0.114, green1=0.596, green2=-0.274, green3=-0.322, blue1=0.211, blue2=-0.523, blue3=0.312)
ysoft = nat(c, 'blurTOP', 'luma_soften', yiq, type='gaussian', size="=max(0.01,%sSoftness*1.6)" % P, filterscalex=1, filterscaley=0, extend='hold')
cb = "(max(%sChromableed,0.001)*%s+1)" % (P, A)
cblur = nat(c, 'blurTOP', 'chroma_bleed', yiq, type='gaussian', size="=%s*4" % cb, filterscalex=1, filterscaley=0, extend='hold')
cshift = nat(c, 'transformTOP', 'chroma_shift', cblur, tx="=%sChromashift*%s/%s" % (P, A, RW), extend='hold')
yiq2 = nat(c, 'reorderTOP', 'luma_plus_chroma', ysoft, cshift, outputred='input1', outputredchan='red', outputgreen='input2', outputgreenchan='green',
           outputblue='input2', outputbluechan='blue', outputalpha='input1', outputalphachan='alpha')
t2 = nat(c, 'channelmixTOP', 'yiq_to_rgb', yiq2,
         red1=1, red2=0.956, red3=0.621, green1=1, green2=-0.272, green3=-0.647, blue1=1, blue2=-1.106, blue3=1.703)

# ---- C. grain, speckle in the tracking bands, snow in the head-switch band ----
NZ = "(%sNoise*%s)" % (P, A)
def full(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RW; o.par.resolutionh.expr = RH; return o
grain = full(nat(c, 'noiseTOP', 'grain_noise', type='randomgpu', mono=True, seed="=%s+17" % E('frame'), amp=1, offset=0))
grain_s = scale(grain, 'grain', "%s*0.09" % NZ)
speck = nat(c, 'noiseTOP', 'speckle_noise', type='randomgpu', mono=True, seed="=%s+23" % E('frame'), amp=1, offset=0)
speck.par.outputresolution = 'custom'; speck.par.resolutionw.expr = "max(2,int(%s/6))" % RW; speck.par.resolutionh.expr = RH
speck_on = nat(c, 'thresholdTOP', 'speckles', speck, rgb='red', comparator='less', threshold=0.84)
speck_up = up(speck_on, 'speckles_up', 'nearest')
band_up = up(band, 'bands_up')
bandm = nat(c, 'levelTOP', 'band_strength', band_up, brightness1="=min(1,%sTracking*%s)*0.8" % (P, A))
fac = nat(c, 'levelTOP', 'band_dim_factor', bandm, outlow=1, outhigh=0.4)
speck_m = nat(c, 'compositeTOP', 'band_speckle', speck_up, bandm, operand='multiply')
speck_s = scale(speck_m, 'band_speckle_gain', "0.85")
glare = scale(bandm, 'band_glare', "0.1")
t3 = nat(c, 'compositeTOP', 'tape_grain', t2, grain_s, operand='add')
t3b = nat(c, 'compositeTOP', 'bands_dim', t3, fac, operand='multiply')
t4 = nat(c, 'compositeTOP', 'bands_speckle', t3b, speck_s, glare, operand='add')
hn = rows(nat(c, 'rectangleTOP', 'snow_band', sizex=1, sizey=0.14, sizeunit='fraction', centery=-0.5, softness=0.02,
              fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False))
snow = nat(c, 'noiseTOP', 'snow_noise', type='randomgpu', mono=True, seed="=%s+29" % E('frame'), amp=0.5, offset=0.5)
snow.par.outputresolution = 'custom'; snow.par.resolutionw.expr = "max(2,int(%s/3))" % RW; snow.par.resolutionh.expr = RH
snow_up = up(snow, 'snow_up', 'nearest')
hn_up = up(hn, 'snow_band_up')
hn_a = nat(c, 'levelTOP', 'snow_strength', hn_up, brightness1="=%s*0.6" % HS)
snow_a = nat(c, 'reorderTOP', 'snow_with_alpha', snow_up, hn_a, outputalpha='input2', outputalphachan='red')
snow_p = nat(c, 'levelTOP', 'snow_premultiply', snow_a, premultrgbbyalpha=True)       # Composite 'over' expects premultiplied colour
t5 = nat(c, 'compositeTOP', 'tape_snow', snow_p, t4, operand='over')
tape = stage('tape_on', src, t5, tape_on)

# ---- D. CRT: curvature, glow, scanlines, shadow mask, vignette, flicker ----
cur = "(%sCurvature*%s)" % (P, A)
lens = nat(c, 'lensdistortTOP', 'curvature', tape, k1="=0.05*%s" % cur, extendmode='zero')
glow_b = nat(c, 'blurTOP', 'glow_blur', lens, type='gaussian', size=14, filterscalex=1, filterscaley=1)
glow = nat(c, 'levelTOP', 'glow_gain', glow_b, brightness1="=%sGlow*%s*0.8" % (P, A))
lit = nat(c, 'compositeTOP', 'glowing_picture', lens, glow, operand='add')
LINES = "%sScanlinecount" % P
S_ = "(%sScanlines*%s)" % (P, A)
# scanline profile: one cosine bump per line (a 3-stop Ramp), every other line dimmed (interlace); all at 2 x H
ramp_t = c.create(td.tableDAT, 'scanline_profile')
ramp_t.text = "pos\tr\tg\tb\ta\n0\t0\t0\t0\t1\n0.5\t1\t1\t1\t1\n1\t0\t0\t0\t1\n"
sl_r = rows(nat(c, 'rampTOP', 'scanline_ramp', type='vertical', dat=ramp_t, period="=1.0/%s" % LINES, extendleft='repeat', extendright='sameasleft'))
sl_p = nat(c, 'levelTOP', 'line_profile', sl_r, outlow=0.35, outhigh=1)
fld_r = rows(nat(c, 'rampTOP', 'field_ramp', type='vertical', period="=2.0/%s" % LINES, phase="=%s*0.5" % E('field'), extendleft='repeat', extendright='sameasleft'))
fld_m = nat(c, 'thresholdTOP', 'field_lines', fld_r, threshold=0.5, comparator='less')
fld_l = nat(c, 'levelTOP', 'field_dim', fld_m, outlow="=1-0.55*%sInterlace" % P, outhigh=1)
hum = rows(nat(c, 'rectangleTOP', 'hum_bar', sizex=1, sizey=0.24, sizeunit='fraction', centery="=((%s*2) %% 1)-0.5" % TP, softness=0.12,
               fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False))
hum_l = nat(c, 'levelTOP', 'hum_dim', hum, outlow=1, outhigh="=1-%sFlicker*%s*0.03" % (P, A))
sl_all = nat(c, 'compositeTOP', 'scanline_pattern', sl_p, fld_l, hum_l, operand='multiply')
sl_amt = nat(c, 'levelTOP', 'scanline_strength', sl_all, outlow="=1-min(%s,1.2)" % S_, outhigh=1, brightness1="=1+%s*0.35" % S_)
sl_up = up(sl_amt, 'scanlines_up')
# shadow mask: a 3 x 4 pixel RGB-triad texture (one Rectangle TOP per colour), repeated 1:1 over the picture
def cell(name, cx, rgb):
    r = nat(c, 'rectangleTOP', name, sizex=1.0 / 3, sizey=1, sizeunit='fraction', centerx=cx, fillcolorr=rgb[0], fillcolorg=rgb[1], fillcolorb=rgb[2],
            fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False)
    r.par.outputresolution = 'custom'; r.par.resolutionw = 3; r.par.resolutionh = 4; return r
tri = nat(c, 'compositeTOP', 'triad', cell('triad_r', -1.0 / 3, (1, 0, 0)), cell('triad_g', 0.0, (0, 1, 0)), cell('triad_b', 1.0 / 3, (0, 0, 1)), operand='add')
slot = nat(c, 'rectangleTOP', 'slot_rows', sizex=1.0 / 3, sizey=0.5, sizeunit='fraction', centerx=1.0 / 3, centery=-0.25, fillcolorr=0.8, fillcolorg=0.8,
           fillcolorb=0.8, fillalpha=1, bgcolorr=1, bgcolorg=1, bgcolorb=1, bgalpha=1, antialias=False)
slot.par.outputresolution = 'custom'; slot.par.resolutionw = 3; slot.par.resolutionh = 4
tri2 = nat(c, 'compositeTOP', 'triad_slot', tri, slot, operand='multiply')
MK = "%sMaskstrength*%s" % (P, A)
tri3 = nat(c, 'levelTOP', 'triad_strength', tri2, outlow=0.35, outhigh=1, brightness2="=1")     # dark phosphor 0.35, lit 1
tri4 = nat(c, 'levelTOP', 'triad_mix', tri3, outlow="=1-%s" % MK, outhigh="=1-%s+1.5*%s" % (MK, MK))
tile = nat(c, 'transformTOP', 'mask_tiles', tri4, outputresolution='custom', resolutionw="=" + RW, resolutionh="=" + RH, extend='repeat', inputfiltertype='nearest',
            sx="=3.0/%s" % RW, sy="=4.0/%s" % RH)
# vignette + rounded screen corners + flicker, all at low resolution
vg = nat(c, 'rectangleTOP', 'vignette_shape', sizex=1, sizey=1, sizeunit='fraction', softness=0.5,
         fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False)
vg.par.outputresolution = 'custom'; vg.par.resolutionw = 256; vg.par.resolutionh = 144
VG = "(%sVignette*%s)" % (P, A)
vg2 = nat(c, 'levelTOP', 'vignette_curve', vg, gamma1="=1/(%s*0.6+0.001)" % VG, outlow="=1-min(1,%s)" % VG, outhigh=1)
FK = "(1+%sFlicker*%s*0.04*math.sin(2*math.pi*%s*50))" % (P, A, T)
vg3 = nat(c, 'levelTOP', 'flicker', vg2, brightness1="=" + FK)
inside = nat(c, 'rectangleTOP', 'screen_corners', sizex=1, sizey=1, sizeunit='fraction', cornerradius=0.03, softness=0.004, fillcolorr=1, fillcolorg=1,
             fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=True)
inside.par.outputresolution = 'custom'; inside.par.resolutionw = 1024; inside.par.resolutionh = 576
screen = nat(c, 'compositeTOP', 'screen_shape', up(vg3, 'vignette_up'), inside, operand='multiply')
crt = nat(c, 'compositeTOP', 'crt_overlay', lit, sl_up, tile, screen, operand='multiply')
res_ = stage('crt_on', tape, crt, crt_on)
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(res_)
_subexpr(c, r"parent\(\)\.par\.Tracking\b", lambda m: "(%s+%s)" % (m.group(0), _CH('band1')))     # modulation CHOP: band1 adds to Tracking
_subexpr(c, r"parent\(\)\.par\.Jitter\b", lambda m: "(%s+%s)" % (m.group(0), _CH('beat')))      # beat adds to Jitter
v3_finish(c, COMP)
report(c)
