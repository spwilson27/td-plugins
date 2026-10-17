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

def setres(o, w=None, h=None):
    pre = "op('../res')" if o.parent().name == 'demo' else "op('res')"
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w or pre + "['w']"; o.par.resolutionh.expr = h or pre + "['h']"

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

def finish_old(c, name):
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ======================= v2 additions (td-plugins CONVENTIONS v2) =======================
P_ = 'parent().par.'
# Standard Controls entries every TOP_ effect has. Append `*COMMON` to your Controls spec list
# (do NOT add your own Resolution / Mix / Bypass).
COMMON = [
    ('Mix', 'float', 1.0, 0, 1, True),
    ('Bypass', 'toggle', 0),
    ('Resolutionmode', 'menu', [('input', 'Follow Input'), ('custom', 'Custom')], 0),
    ('Resolution', 'wh', (1280, 720)),
]

# --- animation: absTime only (makes the preview example move; there is no Loop page) ---
PEXPR = "((absTime.seconds/8.0) % 1.0)"     # 0..1 over 8 s
LENEXPR = "8"
FREXPR = "240"
def uP(extra=0):
    return ('uP', [PEXPR, 8, 240, extra])

# --- resolution: Resolutionmode 'input' follows in1 (or Resolutionw/h when unconnected), 'custom' uses Resolutionw/h ---
def res_chop(c):
    k = c.create(td.constantCHOP, 'res')
    conn = "parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections and op('in1').width>0"
    k.par.name0 = 'w'; k.par.value0.expr = "(op('in1').width if (%s) else parent().par.Resolutionw)" % conn
    k.par.name1 = 'h'; k.par.value1.expr = "(op('in1').height if (%s) else parent().par.Resolutionh)" % conn
    return k

def new_demo(c):
    """Base COMP 'demo': holds every preview-only source. Not selected (so not cooking) when in1 is connected."""
    return c.create(td.baseCOMP, 'demo')

def demo_out(d, top, name='demo_out'):
    o = d.create(td.outTOP, name); o.inputConnectors[0].connect(top); return o

HASIN = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"

def v2_input(c, comp=None, srcfile='src.glsl', extra_vecs=()):
    """in1 (In TOP) + demo COMP (animated default source) -> Switch 'src' sized by 'res'."""
    res_chop(c)
    i = c.create(td.inTOP, 'in1')
    d = new_demo(c)
    code = (rd(comp, srcfile) if comp else open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read())
    g = glsl(d, 'defsrc', code, vecs=[uP()] + list(extra_vecs), res=True)
    demo_out(d, g)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = HASIN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

# --- optional modulation In CHOP (must be the LAST input). channels band1-4, beat ---
def add_mod(c, name):
    """name e.g. 'in3'. Creates In CHOP + Null 'modin'. Use MOD('band1') in expressions."""
    i = c.create(td.inCHOP, name); n = c.create(td.nullCHOP, 'modin'); n.inputConnectors[0].connect(i)
    return n
def MOD(ch, default=0):
    return "(op('modin')['%s'].eval() if (op('modin') and op('modin').numChans and op('modin')['%s'] is not None) else %s)" % (ch, ch, default)

# ---- native demo helpers: Constant / Ramp / Noise / Circle / Rectangle / Composite TOPs (no GLSL) ----
def nd_set(o, **kw):
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): o.par[k].expr = v[1:]
        else: o.par[k] = v
    return o
def nd_res(o, W, H):
    o.par.outputresolution = 'custom'; o.par.format = 'rgba16float'
    for k, v in (('resolutionw', W), ('resolutionh', H)):
        if isinstance(v, str): o.par[k].expr = v
        else: o.par[k] = v
    return o
def nd_s(v, W, H):
    """Lengths below are in units of the picture HEIGHT (centre = 0); Circle/Rectangle 'fractionaspect' units are relative to the WIDTH, so scale by H/W."""
    if not isinstance(W, str) and not isinstance(H, str): return v * H / W if not isinstance(v, str) else '=(%s)*%s' % (v[1:], H / W)
    return '=(%s)*(%s)/(%s)' % (v[1:] if isinstance(v, str) else repr(v), H, W)
def nd_const(d, name, W, H, col, alpha=1):
    o = d.create(td.constantTOP, name); nd_res(o, W, H)
    return nd_set(o, colorr=col[0], colorg=col[1], colorb=col[2], alpha=alpha)
def nd_ramp(d, name, W, H, stops, kind='vertical'):
    """stops: [(pos, (r,g,b)), ...]"""
    t = d.create(td.tableDAT, name + '_stops'); t.clear()
    t.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for p, c in stops: t.appendRow([p, c[0], c[1], c[2], 1])
    o = d.create(td.rampTOP, name); nd_res(o, W, H); o.par.type = kind; o.par.dat = t
    return o
def nd_circle(d, name, W, H, cx, cy, r, col, soft=0.003, ring=0, alpha=1.0, **kw):
    """cx, cy, r in 'fraction (aspect)' units (screen height = 1, centre = 0); ring > 0 draws an outline instead of a disc."""
    o = d.create(td.circleTOP, name); nd_res(o, W, H)
    nd_set(o, centerunit='fractionaspect', radiusunit='fractionaspect', softnessunit='fractionaspect', borderwidthunit='fractionaspect',
           centerx=nd_s(cx, W, H), centery=nd_s(cy, W, H), radiusx=nd_s(r, W, H), radiusy=nd_s(r, W, H), softness=nd_s(soft, W, H), bgalpha=0, **kw)
    if ring:
        nd_set(o, fillalpha=0, borderwidth=nd_s(ring, W, H), borderr=col[0], borderg=col[1], borderb=col[2], borderalpha=alpha)
    else:
        nd_set(o, fillcolorr=col[0], fillcolorg=col[1], fillcolorb=col[2], fillalpha=alpha, borderalpha=0)
    return o
def nd_rect(d, name, W, H, cx, cy, sx, sy, col, rot=0, soft=0.002, alpha=1.0, **kw):
    o = d.create(td.rectangleTOP, name); nd_res(o, W, H)
    return nd_set(o, centerunit='fractionaspect', sizeunit='fractionaspect', softnessunit='fractionaspect', centerx=nd_s(cx, W, H), centery=nd_s(cy, W, H), sizex=nd_s(sx, W, H), sizey=nd_s(sy, W, H), rotate=rot,
                  softness=nd_s(soft, W, H), bgalpha=0, fillcolorr=col[0], fillcolorg=col[1], fillcolorb=col[2], fillalpha=alpha, borderalpha=0, **kw)
def nd_over(d, name, W, H, layers, operand='over'):
    o = d.create(td.compositeTOP, name); nd_res(o, W, H); o.par.operand = operand
    for l in reversed(layers): l.outputConnectors[0].connect(o)   # Composite: first input is on top, so connect the topmost layer first
    return o
def nd_pick(a, b, cond):
    """per-channel expression: colour a when cond == 0, colour b when cond == 1 (cond is a 0..1 expression string)"""
    return ['=%r+(%r-%r)*(%s)' % (x, y, x, cond) for x, y in zip(a, b)]

def _nd_demo(demo, W, H):
    """Looping preview source from native TOPs: noisy dark ground, six discs with glow rings, a rotating bar,
    a sweeping scan line and a black-to-white strip along the top (gives the effect a full tonal range)."""
    import math
    PH = "((absTime.seconds/8.0) % 1.0)"; a = "(2*math.pi*%s)" % PH
    A = "(%s)/(%s)" % (W, H)
    nz = demo.create(td.noiseTOP, 'ground'); nd_res(nz, W, H)   # dark, softly looping grain
    nd_set(nz, type='simplex3d', mono=True, period=0.2, amp=0.06, offset=0.06, harmon=2, aspectcorrect=True)
    nz.par.tx.expr = "math.sin(%s)*1.5" % a; nz.par.ty.expr = "math.cos(%s)*1.5" % a
    lay = [nz]
    for i in range(6):
        k1 = 1 + i % 2; k2 = 1 + (i // 3)
        cx = "=%s*math.sin(%s*%d+%d*1.7)*0.4" % (A, a, k1, i); cy = "=0.30*math.cos(%s*%d+%d*2.3)" % (a, k2, i)
        r = 0.10 + 0.025 * i; tone = (1.0, 0.08, 0.05) if i == 2 else (0.92, 0.9, 0.84)
        lay.append(nd_circle(demo, 'disc%d' % i, W, H, cx, cy, r, [t * 0.35 for t in tone], soft=0.004))
        lay.append(nd_circle(demo, 'light%d' % i, W, H, cx, cy, r * 0.6, [t * 0.95 for t in tone], soft=r * 0.5, alpha=0.9))
        lay.append(nd_circle(demo, 'halo%d' % i, W, H, cx, cy, r * 1.35, tone, ring=0.004, soft=0.003, alpha=0.6))
    lay.append(nd_rect(demo, 'bar', W, H, 0, -0.2, 0.8, 0.05, (0.8, 0.8, 0.76), rot="=-math.degrees(%s)" % a))
    lay.append(nd_rect(demo, 'scan', W, H, 0, "=%s-0.5" % PH, 3.0, 0.01, (1, 1, 1), alpha=0.4))
    ramp = nd_ramp(demo, 'range', W, H, [(0.0, (0, 0, 0)), (1.0, (1, 0.98, 0.95))], kind='horizontal')
    band = nd_rect(demo, 'range_band', W, H, 0, 0.465, 3.0, 0.07, (1, 1, 1), soft=0.0005)
    lay.append(nd_over(demo, 'range_strip', W, H, [band, ramp], operand='inside'))   # ramp shown only inside the top band
    return nd_over(demo, 'comp', W, H, lay)

def native_input(c, make):
    """in1 (In TOP) + gated demo COMP (native-TOP source built by make(demo, W, H)) -> Switch 'src' sized by 'res'."""
    res_chop(c)
    i = c.create(td.inTOP, 'in1')
    d = new_demo(c)
    demo_out(d, make(d, "op('../res')['w']", "op('../res')['h']"))
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = HASIN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

# --- tail: Mix (dry/wet vs src), Bypass, out1 ---
def finish_v2(c, name, result, src, label='result', extra_outs=()):
    """result = effect TOP, src = dry input switch. Adds Mix cross, Bypass switch, out1 (+ extra_outs=[(top,'label'),..] as out2..)."""
    mx = c.create(td.crossTOP, 'mixer')
    mx.inputConnectors[0].connect(src); mx.inputConnectors[1].connect(result)
    mx.par.cross.expr = 'parent().par.Mix'
    setres(mx); mx.par.format = 'rgba16float'
    bp = c.create(td.switchTOP, 'bypass')
    bp.inputConnectors[0].connect(mx); bp.inputConnectors[1].connect(src)
    bp.par.index.expr = 'parent().par.Bypass'
    setres(bp); bp.par.format = 'rgba16float'
    o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(bp); o.comment = label
    for k, (t, lab) in enumerate(extra_outs):
        n = c.create(td.nullTOP, 'out%d' % (k + 2)); n.inputConnectors[0].connect(t); n.comment = lab
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c.save(p)
    print('saved', p)
# ======================= end v2 additions =======================

COMP = 'TOP_pixel_sort'
c = new_comp(COMP)
MAXP = 16
add_pars(c, [
    ('Direction', 'menu', [('right', 'Right'), ('left', 'Left'), ('up', 'Up'), ('down', 'Down')], 0),
    ('Key', 'menu', [('luma', 'Luminance'), ('hue', 'Hue'), ('sat', 'Saturation'), ('red', 'Red')], 0),
    ('Thresholdlow', 'float', 0.15, 0, 1),
    ('Thresholdhigh', 'float', 0.9, 0, 1),
    ('Passes', 'int', 8, 0, MAXP),
    ('Sortamount', 'float', 1.0, 0, 1),
    ('Refresh', 'float', 0.02, 0, 1),
    ('Bytebeat', 'float', 0.25, 0, 1),
    ('Bandsize', 'float', 1.0, 0.2, 4),
    ('Bandholdframes', 'int', 3, 1, 30),
    ('Shuffle', 'float', 0.3, 0, 1),
    ('Seed', 'float', 1, 0, 100),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
src = native_input(c, _nd_demo)
add_mod(c, 'in2')
p = lambda n: 'parent().par.' + n
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(src)
fb.par.format = 'rgba16float'; setres(fb); fb.par.reset.expr = p('Reset')
sortcode = rd(COMP, 'sort.glsl')
prev = fb
hard = 0
for i in range(MAXP):
    g = glsl(c, 'sort%d' % i, sortcode, inputs=[prev, src], res=True, fmt='rgba16float', vecs=[
        uP(),
        ('uS', [p('Direction') + '.menuIndex', p('Thresholdlow'), p('Thresholdhigh'), p('Key') + '.menuIndex']),
        ('uT', ['1 if (%s and %d < %s) else 0' % (p('Active'), i, p('Passes')), i, 'absFrame' if False else 'absTime.frame', p('Refresh')]),
        ('uU', [hard, 1 if i == 0 else 0, 0, 0]),
    ])
    prev = g
nul = c.create(td.nullTOP, 'state'); nul.inputConnectors[0].connect(prev)
fb.par.top = nul
cor = glsl(c, 'corrupt', rd(COMP, 'corrupt.glsl'), inputs=[nul, src], res=True, vecs=[
    uP(),
    ('uA', [p('Sortamount'), 'min(1,%s+%s*%s)' % (p('Bytebeat'), p('Modamount'), MOD('band1')), p('Shuffle'), 0]),
    ('uB', [0.5, p('Bandsize'), p('Seed'), p('Bandholdframes')]),
])
finish_v2(c, COMP, cor, src)
report(c)
