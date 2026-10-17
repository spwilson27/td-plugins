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
COMP = 'TOP_glitch'
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
    ('Amount', 'float', 1.0, 0, 2),
    ('Seed', 'float', 1.0, 0, 100),
    ('Rate', 'float', 3.0, 0, 30),
    ('Rgbsplit', 'float', 0.5, 0, 1),
    ('Blockdisplace', 'float', 0.5, 0, 1),
    ('Scanlinetear', 'float', 0.4, 0, 1),
    ('Pixelsort', 'float', 0.35, 0, 1),
    ('Smear', 'float', 0.35, 0, 1),
    ('Sortthreshold', 'float', 0.45, 0, 2),
    ('Sortaxis', 'menu', [('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 0),
    ('Smearthreshold', 'float', 0.08, 0.001, 1),
    ('Smearblock', 'float', 16, 2, 64),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
look_pg(c)
P = 'parent().par.'
F = ' + 0*absTime.frame'
AMT = "(%sAmount*(1+%s+%s))" % (P, _CH('band1'), _CH('beat'))     # modulation CHOP: band1 and beat add to Amount
RES = "parent().par.Resolutionw", "parent().par.Resolutionh"      # v3_finish turns these into the real output size

# ---------------- demo (preview only): bar + five discs on a noisy grid, all native TOPs ----------------
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
LOOKM = "parent(2).par.Look.menuIndex"; ACC = "parent(2).par.Accent"
def dres(o):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = 'parent(2).par.Resolutionw'; o.par.resolutionh.expr = 'parent(2).par.Resolutionh'; return o
def dn(typ, name, *ins, **kw): return dres(nat(d, typ, name, *ins, **kw))
bg0 = dn('noiseTOP', 'bg_noise', type='simplex3d', period=0.6, amp=0.03, offset=0.07, mono=False, tz="=absTime.seconds*0.03")
def stripes(name, kind):
    r = dn('rampTOP', name + '_ramp', type=kind, period=1 / 14.0, extendleft='repeat', extendright='sameasleft')
    return dn('thresholdTOP', name, r, threshold=0.5, comparator='less')
sx, sy = stripes('stripes_x', 'horizontal'), stripes('stripes_y', 'vertical')
chk0 = dn('compositeTOP', 'checker', sx, sy, operand='difference')
chk = dn('levelTOP', 'grid_level', chk0, brightness1=0.06)
tint = dn('compositeTOP', 'bg', bg0, chk, operand='add')
tint.par.format = 'rgba16float'
def hue(h):   # python expression string of an rgb tuple member in TD expression language
    return h
layers = [tint]
def colr(i, base_h, sat, val, ch):
    # hue to rgb channel in an expression; mono look gives bone-white greys
    off = {'r': 0.0, 'g': 2.0/3.0, 'b': 1.0/3.0}[ch]
    k = "max(0,min(1,abs(((%s+%f)%%1)*6-3)-1))" % (base_h, off)
    colv = "(%f*(1-%f+%f*%s))" % (val, sat, sat, k)
    grey = "(%f*0.9*%s)" % (val * (0.35 + 0.65 * ((base_h_val(i)*3) % 1)), {'r': '0.96', 'g': '0.94', 'b': '0.89'}[ch])
    return "=(%s if %s else %s)" % (grey, LOOKM + '==1', colv)
def base_h_val(i): return 0.12 * i
bar = dn('rectangleTOP', 'bar', sizex=0.47, sizey=0.06, sizeunit='fractionaspect' if False else 'fraction', centery=-0.18, rotate="=-absTime.seconds*0.7*57.2958",
         fillcolorr="=(3*(0.96*(1-%s)+%s) if %s==1 else 0.9)" % (ACC, ACC, LOOKM), fillcolorg="=(3*(0.94*(1-%s)+0.04*%s) if %s==1 else 2.7)" % (ACC, ACC, LOOKM),
         fillcolorb="=(3*(0.89*(1-%s)+0.04*%s) if %s==1 else 3.0)" % (ACC, ACC, LOOKM), fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=0)
layers.append(bar)
for i in range(5):
    t = "absTime.seconds"
    cx = "=math.sin(%s*(0.35+0.11*%d)+%d*1.7)*0.44" % (t, i, i)
    cy = "=math.cos(%s*(0.27+0.09*%d)+%d*2.3)*0.33" % (t, i, i)
    r = (0.11 + 0.025 * i) * 0.5625      # circle radii are fractions of the width (720/1280 of the height)
    hh = "(%f+%s*0.03)" % (0.12 * i, t)
    ring = dn('circleTOP', 'disc%d' % i, radiusx=r, radiusy=r, softness=0.004, centerx=cx, centery=cy, bgalpha=0,
              fillcolorr=colr(i, hh, 0.85, 0.6, 'r'), fillcolorg=colr(i, hh, 0.85, 0.6, 'g'), fillcolorb=colr(i, hh, 0.85, 0.6, 'b'), fillalpha=1,
              bgcolorr=0, bgcolorg=0, bgcolorb=0)
    core = dn('circleTOP', 'core%d' % i, radiusx=r * 0.45, radiusy=r * 0.45, softness=r * 0.45, centerx=cx, centery=cy,
              fillcolorr=3.0, fillcolorg=2.7, fillcolorb=2.1, fillalpha=1, bgalpha=0, bgcolorr=0, bgcolorg=0, bgcolorb=0)
    layers += [ring, core]
dem = dn('compositeTOP', 'objects', *reversed(layers[1:]), operand='over')      # first input is on top
demsum = dn('compositeTOP', 'scene', dem, tint, operand='over')
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(demsum); do.par.label = 'demo source'
src = nat(c, 'switchTOP', 'src', d.outputConnectors[0], i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(src)

# ---------------- glitch events: one value set per "beat" (Rate per second), re-rolled with Seed ----------------
TB = "absTime.seconds*%sRate" % P
BEAT = "(math.floor(%s)+%sSeed*13.37)" % (TB, P)
ev = c.create(td.constantCHOP, 'events')
ev.comment = 'per-beat random values: tdu.rand(beat) for grid sizes, tear rows, split angle...'
EVS = [
    ('beat', BEAT),
    ('env', "(1-(lambda x: x*x*(3-2*x))(min(1,(%s %% 1)/0.6)))" % TB),          # decays after each beat
    ('gridx', "(6+22*tdu.rand(%s*1.3))" % BEAT), ('gridy', "(4+12*tdu.rand(%s*2.1))" % BEAT),
    ('rows', "(40+120*tdu.rand(%s*0.71))" % BEAT),
    ('ang', "(tdu.rand(%s*3.3)*6.2831853)" % BEAT),
    ('bandy', "((%s*0.37+%s*0.1) %% 1)" % (BEAT, TB)),
    ('key', "(1 if tdu.rand(%s*9.1)<0.08 else 0)" % BEAT),
    ('seedA', "(%s*7.7)" % BEAT), ('seedB', "(%s*3.1+11)" % BEAT), ('seedC', "(%s*5.3+23)" % BEAT), ('seedD', "(%s*1.9+37)" % BEAT),
]
for k, (n, e) in enumerate(EVS):
    getattr(ev.par, 'name%d' % k).val = n
    getattr(ev.par, 'value%d' % k).expr = e
E = lambda n: "op('events')['%s']" % n
G = AMT
BA = "(%sBlockdisplace*%s)" % (P, G); TA = "(%sScanlinetear*%s)" % (P, G); SA = "(%sRgbsplit*%s)" % (P, G)
PA = "(%sPixelsort*%s)" % (P, G); MA = "(%sSmear*%s)" % (P, G)
def lowres(o, w, h):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = w.lstrip('='); o.par.resolutionh.expr = h.lstrip('='); return o
def upres(o, name):   # nearest-neighbour up-scale to the output size (blocky maps)
    return nat(c, 'resolutionTOP', name, o, outputresolution='custom', resolutionw="=" + RES[0], resolutionh="=" + RES[1],
               inputfiltertype='nearest', filtertype='nearest')
def stage(name, a, b, on):
    """Switch TOP: index 1 (the effect b) only while `on` is true, otherwise a passes straight through and b does not cook."""
    s = nat(c, 'switchTOP', name, a, b); s.par.index.expr = "(1 if (%s) else 0)%s" % (on, F); return s

# ---------------- 1. block displacement: low-res random cells -> nearest up-scale -> Displace TOP ----------------
bd_xy = lowres(nat(c, 'noiseTOP', 'block_offsets', type='randomgpu', mono=False, seed="=" + E('seedA'), amp=1, offset=0),
               "=int(%s)" % E('gridx'), "=int(%s)" % E('gridy'))
bd_pick = lowres(nat(c, 'noiseTOP', 'block_pick', type='randomgpu', mono=True, seed="=" + E('seedB'), amp=1, offset=0),
                 "=int(%s)" % E('gridx'), "=int(%s)" % E('gridy'))
bd_on = nat(c, 'thresholdTOP', 'blocks_chosen', bd_pick, rgb='red', comparator='less', threshold="=1-1.2*%s" % BA)   # ~60 % * amount of the cells
bd_map = nat(c, 'compositeTOP', 'block_map', bd_xy, bd_on, operand='multiply')
bd_up = upres(bd_map, 'block_map_up')
w_ = "=0.0875*%s*(0.7+0.6*%s)" % (BA, E('env'))
bd = nat(c, 'displaceTOP', 'displace_blocks', src, bd_up, horzsource='red', vertsource='green', midpointx=0, midpointy=0,
         displaceweightx=w_, displaceweighty=w_, extend='mirror')
s1 = stage('blocks_on', src, bd, "%s>0" % BA)

# ---------------- 2. scanline tear: one random value per row + a rolling band ----------------
ROWS = "=int(%s)" % E('rows')
tr_pick = lowres(nat(c, 'noiseTOP', 'tear_pick', type='randomgpu', mono=True, seed="=" + E('seedC'), amp=1, offset=0), "=2", ROWS)
tr_on = nat(c, 'thresholdTOP', 'rows_chosen', tr_pick, rgb='red', comparator='less', threshold="=1-0.7*%s" % TA)
tr_amt = lowres(nat(c, 'noiseTOP', 'tear_amount', type='randomgpu', mono=True, seed="=" + E('seedD'), amp=1, offset=0), "=2", ROWS)
tr_amt2 = nat(c, 'mathTOP', 'tear_scale', tr_amt, gain="=%s*0.25" % TA)
tr_rows = nat(c, 'compositeTOP', 'torn_rows', tr_amt2, tr_on, operand='multiply')
band = lowres(nat(c, 'rectangleTOP', 'tear_band', sizex=1, sizey="=0.04+0.1*%s" % TA, sizeunit='fraction', centery="=%s-0.5" % E('bandy'),
                  fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, antialias=False), "=2", ROWS)
band_n = lowres(nat(c, 'noiseTOP', 'band_jitter', type='randomgpu', mono=True, seed="=" + E('seedB') + "+5", amp=1, offset=0), "=2", ROWS)
band_amt = nat(c, 'compositeTOP', 'band_shift', band_n, band, operand='multiply')
band_amt2 = nat(c, 'mathTOP', 'band_scale', band_amt, gain="=%s*0.15" % TA)
tr_sum = nat(c, 'compositeTOP', 'tear_map', tr_rows, band_amt2, operand='add')
tr_up = upres(tr_sum, 'tear_map_up')
tr = nat(c, 'displaceTOP', 'displace_rows', s1, tr_up, horzsource='red', vertsource='none', midpointx=0, midpointy=0,
         displaceweightx=0.5, displaceweighty=0, extend='mirror')
s2 = stage('tear_on', s1, tr, "%s>0" % TA)

# ---------------- 3. RGB split: Reorder TOP takes R, G, B from three shifted copies ----------------
DX = "math.cos(%s)*%s*0.03*(0.5+%s)" % (E('ang'), SA, E('env'))
DY = "math.sin(%s)*%s*0.03*(0.5+%s)" % (E('ang'), SA, E('env'))
shr = nat(c, 'transformTOP', 'shift_red', s2, tx="=-" + DX, ty="=-" + DY, extend='mirror')
shb = nat(c, 'transformTOP', 'shift_blue', s2, tx="=" + DX, ty="=" + DY, extend='mirror')
split = nat(c, 'reorderTOP', 'rgb_split', shr, s2, shb, outputred='input1', outputredchan='red', outputgreen='input2', outputgreenchan='green',
            outputblue='input3', outputbluechan='blue', outputalpha='input2', outputalphachan='alpha')
s3 = stage('split_on', s2, split, "%s>0" % SA)

# ---------------- 4. pixel-sort streaks (approximation): the one small GLSL core ----------------
streak = glsl(c, 'streaks', rd(COMP, 'streak.glsl'), inputs=[s3], res=True, vecs=[
    ('uS', [PA, P + 'Sortthreshold', P + 'Sortaxis.menuIndex', E('beat')]),
])
streak.par.inputextenduv = 'mirror'
s4 = stage('streaks_on', s3, streak, "%s>0" % PA)

# ---------------- 5. compression hold: where a block barely changed, keep the previous output ----------------
fb = nat(c, 'feedbackTOP', 'feedback', src, reset="=" + P + 'Reset'); setres(fb)
BW = "=max(2,int(%s/%sSmearblock))" % (RES[0], P); BH = "=max(2,int(%s/%sSmearblock))" % (RES[1], P)
def blocks(o, name): return lowres(nat(c, 'resolutionTOP', name, o, inputfiltertype='nearest', filtertype='nearest'), BW, BH)
cur_blk = blocks(src, 'block_now'); old_blk = blocks(fb, 'block_before')
diff = nat(c, 'compositeTOP', 'block_change', cur_blk, old_blk, operand='difference')
dlen = nat(c, 'mathTOP', 'change_size', diff, chanop='len', inputmask=7)
THR = P + 'Smearthreshold'
M_ = "min(1,%s)*(1-%s)" % (MA, E('key'))        # hold strength, 0 on keyframe refresh beats
hold = nat(c, 'levelTOP', 'hold_amount', dlen, inlow="=%s*0.5" % THR, inhigh="=%s" % THR, outlow="=%s" % M_, outhigh=0)
prev_a = nat(c, 'reorderTOP', 'previous_with_hold_alpha', fb, hold, outputalpha='input2', outputalphachan='red')
prev_a.par.inputfiltertype = 'nearest'
prev_p = nat(c, 'levelTOP', 'previous_premultiplied', prev_a, premultrgbbyalpha=True)   # Composite 'over' expects premultiplied colour
held = nat(c, 'compositeTOP', 'hold_previous', prev_p, s4, operand='over')   # previous output over the glitched frame
s5 = stage('hold_on', s4, held, "%s>0" % MA)

# ---------------- feedback loop + Active (off freezes the output) ----------------
act = nat(c, 'switchTOP', 'active', fb, s5); act.par.index.expr = "(1 if %sActive else 0)%s" % (P, F)
nul = nat(c, 'nullTOP', 'fb_out', act)
fb.par.top = nul
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(nul)
v3_finish(c, COMP)
report(c)
