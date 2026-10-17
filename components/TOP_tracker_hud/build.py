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

COMP = 'TOP_tracker_hud'
import math as _m
P = lambda n: 'parent().par.' + n
c = new_comp(COMP)
add_pars(c, [
    ('Points', 'int', 28, 1, 64),
    ('Labelmode', 'menu', [('id', 'ID'), ('coords', 'Coords'), ('both', 'Both')], 0),
    ('Labelcolor', 'menu', [('red', 'Red'), ('white', 'White')], 0),
    ('Fontsize', 'int', 14, 7, 42),
    ('Boxsize', 'float', 16, 4, 64),
    ('Linecount', 'int', 10, 0, 64),
    ('Gridsize', 'float', 80, 16, 400),
    ('Threshold', 'float', 0.35, 0, 1),
    ('Refresh', 'int', 4, 0, 64),
    ('Jitter', 'float', 0.5, 0, 3),
    ('Dim', 'float', 0.8, 0, 1.5),
    ('Scanlines', 'float', 0.5, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
res_chop(c)
RW = "op('res')['w']"; RH = "op('res')['h']"

# ---------------------------------------------------------------- demo source (native): silhouette blobs, rings and bars
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
DW = "op('../res')['w']"; DH = "op('../res')['h']"
TH = "(absTime.seconds/8.0*6.28318)"
def dres(o, fmt='rgba16float'):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = DW; o.par.resolutionh.expr = DH; o.par.format = fmt
    if hasattr(o.par, 'justifyh'): o.par.justifyh = 'center'; o.par.justifyv = 'center'
# blob field f = sum r^2/d^2: a ramp of 1/d^2 (circular ramp, position = distance / half width of the 512 px tile) scaled per blob by a Transform TOP
T0 = 0.25
kt = d.create(td.tableDAT, 'blob_keys'); kt.appendRow(['pos', 'r', 'g', 'b', 'a'])
for k in range(0, 65):
    t = k / 64.0
    f = min(30.0, (T0 / max(t, 1e-3)) ** 2) / 4.0          # stored /4 so that the 0..1 ramp range holds f up to 4 (clamped)
    kt.appendRow([t, min(f, 1.0), min(f, 1.0), min(f, 1.0), 1])
blob = d.create(td.rampTOP, 'blob'); blob.par.type = 'circular'; blob.par.dat = kt; blob.par.extendright = 'hold'
blob.par.outputresolution = 'custom'; blob.par.resolutionw = 512; blob.par.resolutionh = 512; blob.par.format = 'rgba32float'
fields = []
for i in range(5):
    r_ = .07 + .02 * i
    tr = d.create(td.transformTOP, 'blob%d' % i); tr.inputConnectors[0].connect(blob)
    tr.par.tunit = 'pixels'
    tr.par.sx.expr = tr.par.sy.expr = '%r*%s/64.0' % (r_, DH)
    tr.par.tx.expr = '(math.sin(%s*%d+%r)*0.5)*%s' % (TH, 1 + i % 2, i * 1.9, DH)
    tr.par.ty.expr = '(math.cos(%s*%d+%r)*0.28)*%s' % (TH, 1 + (i + 1) % 2, i * 2.7, DH)
    tr.par.extend = 'hold'; dres(tr, 'rgba32float')
    fields.append(tr)
fsum = d.create(td.compositeTOP, 'field_sum'); fsum.par.operand = 'add'; fsum.par.format = 'rgba32float'
for k, f_ in enumerate(fields): fsum.inputConnectors[k].connect(f_)
# silhouette (smoothstep .9..1.1) and bright contour (|f-1| < .02) from one 1D look-up
sk = d.create(td.tableDAT, 'sil_keys'); sk.appendRow(['pos', 'r', 'g', 'b', 'a'])
def _ss(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a))); return t * t * (3 - 2 * t)
for k in range(0, 129):
    fv = 4.0 * k / 128.0
    sk.appendRow([k / 128.0, _ss(0.9, 1.1, fv), 0.5 * 0.9 * _ss(0.02, 0.0, abs(fv - 1.0)), 0, 1])
silr = d.create(td.rampTOP, 'sil_curve'); silr.par.type = 'horizontal'; silr.par.dat = sk
silr.par.outputresolution = 'custom'; silr.par.resolutionw = 1024; silr.par.resolutionh = 4; silr.par.format = 'rgba32float'
silr.par.interpnotches = 'linear'
sil = d.create(td.lookupTOP, 'silhouette'); sil.inputConnectors[0].connect(fsum); sil.inputConnectors[1].connect(silr)
dres(sil, 'rgba32float')
# base background and textured interior
bgn = d.create(td.noiseTOP, 'bg_noise'); bgn.par.type = 'simplex3d'; bgn.par.period = 0.18; bgn.par.amp = 0.025; bgn.par.offset = 0.055; bgn.par.mono = True; bgn.par.aspectcorrect = True
bgn.par.tz.expr = TH + '*0.12'; dres(bgn)
tex = d.create(td.noiseTOP, 'blob_texture'); tex.par.type = 'simplex3d'; tex.par.period = 0.05; tex.par.amp = 0.25; tex.par.offset = 0.6; tex.par.mono = True; tex.par.aspectcorrect = True
tex.par.tz.expr = TH + '*0.3'; dres(tex)
inner = d.create(td.matteTOP, 'blob_interior'); inner.inputConnectors[0].connect(tex); inner.inputConnectors[1].connect(bgn); inner.inputConnectors[2].connect(sil)
inner.par.mattechannel = 'red'; dres(inner)
glow = d.create(td.reorderTOP, 'contour_glow'); glow.inputConnectors[0].connect(sil)
glow.par.outputredchan = 'green'; glow.par.outputgreenchan = 'green'; glow.par.outputbluechan = 'green'; glow.par.outputalphachan = 'one'; glow.par.format = 'rgba16float'
# rings and bars
ring_a = d.create(td.circleTOP, 'ring_a'); ring_b = d.create(td.circleTOP, 'ring_b')
for rg, rr in ((ring_a, .12), (ring_b, .17)):
    dres(rg)
    rg.par.radiusunit = 'pixels'; rg.par.radiusx.expr = rg.par.radiusy.expr = '%r*%s' % (rr, DH)
    rg.par.centerunit = 'pixels'; rg.par.centerx.expr = 'math.cos(%s)*0.55*%s' % (TH, DH); rg.par.centery.expr = 'math.sin(%s)*0.2*%s' % (TH, DH)
    rg.par.fillalpha = 0; rg.par.bgalpha = 0
    for ch in 'rgb': rg.par['border' + ch] = 0.8
    rg.par.borderalpha = 1; rg.par.borderwidthunit = 'pixels'; rg.par.borderwidth.expr = '0.008*%s' % DH
    rg.par.softnessunit = 'pixels'; rg.par.softness = 0.5
bar_h = d.create(td.rectangleTOP, 'bar_h'); bar_v = d.create(td.rectangleTOP, 'bar_v')
for br, (sx_, sy_, lv) in ((bar_h, (0.6, 0.024, 0.9)), (bar_v, (0.024, 0.4, 0.6))):
    dres(br)
    br.par.sizeunit = 'pixels'; br.par.sizex.expr = '%r*%s' % (sx_, DH); br.par.sizey.expr = '%r*%s' % (sy_, DH)
    br.par.centerunit = 'pixels'; br.par.centerx = 0; br.par.centery = 0
    for ch in 'rgb': br.par['fillcolor' + ch] = lv
    br.par.fillalpha = 1; br.par.bgalpha = 0
bars = d.create(td.compositeTOP, 'bars'); bars.par.operand = 'add'; bars.inputConnectors[0].connect(bar_h); bars.inputConnectors[1].connect(bar_v); bars.par.format = 'rgba16float'
barm = d.create(td.transformTOP, 'bars_move'); barm.inputConnectors[0].connect(bars)
barm.par.tunit = 'pixels'; barm.par.ty.expr = '-0.3*%s' % DH; barm.par.rotate.expr = TH + '*57.29578'; barm.par.extend = 'zero'; dres(barm)
scene = d.create(td.compositeTOP, 'scene'); scene.par.operand = 'add'; scene.par.format = 'rgba16float'
for k, s_ in enumerate((inner, glow, ring_a, ring_b, barm)): scene.inputConnectors[k].connect(s_)
opq = d.create(td.reorderTOP, 'opaque'); opq.inputConnectors[0].connect(scene)
for ch in ('red', 'green', 'blue'): opq.par['output' + ch + 'chan'] = ch
opq.par.outputalphachan = 'one'; opq.par.format = 'rgba16float'
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(opq); do.par.label = 'demo source'
sw = c.create(td.switchTOP, 'src')
sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = HASIN
setres(sw); sw.par.format = 'rgba16float'
add_mod(c, 'in2')

# ---------------------------------------------------------------- pass A: feature points (GLSL: hashed candidates + hill climb) -> 64x1 float texture (x, y, id, valid)
pa = glsl(c, 'points', rd(COMP, 'pts.glsl'), inputs=[sw], fmt='rgba32float', vecs=[
    ('uA', [PEXPR, P('Points'), P('Threshold'), P('Refresh')]), ('uB', ["%s+%s*%s*2" % (P('Jitter'), P('Modamount'), MOD('band1')), 0, 0, 0])])
pa.par.outputresolution = 'custom'; pa.par.resolutionw = 64; pa.par.resolutionh = 1
pa.par.inputextenduv = 'hold'

# ---------------------------------------------------------------- the HUD as geometry: points -> POP attributes -> instanced lines / boxes
def mcomb(name, inp, vecs=(), combs=(), unit='deg'):
    m = c.create(td.mathcombinePOP, name)
    if inp is not None: m.inputConnectors[0].connect(inp)
    if vecs:
        m.seq.vec.numBlocks = len(vecs)
        for k, (n, t, vals) in enumerate(vecs):
            m.par['vec%dname' % k] = n; m.par['vec%dtype' % k] = t
            for j, v in enumerate(vals):
                p_ = m.par['vec%dvalue%d' % (k, j)]
                if isinstance(v, str): p_.expr = v
                else: p_.val = v
    if combs:
        m.seq.comb.numBlocks = len(combs)
        for k, (op_, a, b, cc, rs) in enumerate(combs):
            m.par['comb%doper' % k] = op_; m.par['comb%dscopea' % k] = a
            if b: m.par['comb%dscopeb' % k] = b
            if cc: m.par['comb%dscopec' % k] = cc
            m.par['comb%dresult' % k] = rs
    m.par.angleunit = unit
    return m
t2p = c.create(td.toptoPOP, 'points_pop'); t2p.par.input0top = pa      # 64 points, Color = (x, y, id, valid)
BOX = '%s*(1+%s*%s)' % (P('Boxsize'), P('Modamount'), MOD('band2'))
hp = mcomb('hud_points', t2p,
    vecs=[('resv', 'float3', [RW, RH, 0]), ('halfv', 'float3', [RW + '/2', RH + '/2', 0]), ('boxs', 'float', [BOX]),
          ('ex', 'float3', [1, 0, 0]), ('eyz', 'float3', [0, 1, 1]), ('exy', 'float3', [1, 1, 0]), ('ez', 'float3', [0, 0, 1]),
          ('half1', 'float', [0.5]), ('n63', 'float', [63.0]), ('one', 'float', [1.0]), ('three', 'float', [3.0]), ('five', 'float', [5.0]),
          ('npts', 'float', ['max(%s,1)' % P('Points')]), ('nlines', 'float', [P('Linecount')])],
    combs=[('mult', 'Color.rgb', 'resv', '', 'Cpx'),
           ('asubb', 'Cpx', 'halfv', '', 'Pw'),                      # point position in pixels from the image centre
           ('copya', 'Color(3)', '', '', 'Valid'),
           ('add', 'P(0)', 'half1', '', 'Kx'),
           ('mult', 'Kx', 'n63', '', 'Kf'),
           ('round', 'Kf', '', '', 'Kidx'),                          # point number 0..63
           ('mult', 'Valid', 'boxs', '', 'Bs'),
           ('mult', 'exy', 'Bs', '', 'Bxy'),
           ('add', 'Bxy', 'ez', '', 'Sbox'),                         # box scale
           ('mult', 'Kidx', 'five', '', 'K5'),
           ('add', 'K5', 'three', '', 'K53'),
           ('mod', 'K53', 'npts', '', 'Jraw'),
           ('add', 'Kidx', 'one', '', 'K1'),
           ('mod', 'K1', 'npts', '', 'Jalt'),
           ('eq', 'Jraw', 'Kidx', '', 'Jsame'),
           ('asubb', 'Jalt', 'Jraw', '', 'Jd'),
           ('mult', 'Jd', 'Jsame', '', 'Jm'),
           ('add', 'Jraw', 'Jm', '', 'Jidx')])                        # partner of this point for its connecting line (k*5+3) mod N, or k+1

# partner positions through Lookup Attribute POP (position and validity of point Jidx)
pl = c.create(td.lookupattributePOP, 'partner'); pl.inputConnectors[0].connect(hp); pl.inputConnectors[1].connect(hp)
pl.par.lookupindexattr = 'Jidx'; pl.par.indexunit = 'pointindex'
pl.seq.lookup.numBlocks = 2
pl.par.lookup0valueattr = 'Pw'; pl.par.lookup0outputattrscope = 'PwB'
pl.par.lookup1valueattr = 'Valid'; pl.par.lookup1outputattrscope = 'ValidB'
hl = mcomb('hud_lines', pl,
    vecs=[('ex', 'float3', [1, 0, 0]), ('eyz', 'float3', [0, 1, 1]), ('ez', 'float3', [0, 0, 1]),
          ('npts', 'float', ['max(%s,1)' % P('Points')]), ('nlines', 'float', [P('Linecount')])],
    combs=[('asubb', 'PwB', 'Pw', '', 'Dl'),
           ('length', 'Dl', '', '', 'Ll'),
           ('atan2', 'Dl(1)', 'Dl(0)', '', 'Angl'),
           ('lt', 'Kidx', 'nlines', '', 'InL'),
           ('lt', 'Kidx', 'npts', '', 'InN'),
           ('mult', 'Valid', 'ValidB', '', 'V2'),
           ('mult', 'InL', 'InN', '', 'V3'),
           ('mult', 'V2', 'V3', '', 'Vis'),
           ('mult', 'Ll', 'Vis', '', 'Lv'),
           ('mult', 'ex', 'Lv', '', 'Slx'),
           ('add', 'Slx', 'eyz', '', 'Slin'),                        # line scale: (length or 0, 1, 1)
           ('mult', 'ez', 'Angl', '', 'Rotl')])                      # line rotation about z

# ---- render: orthographic camera in pixel units (1 world unit = 1 px, origin at the image centre)
def geo_for(name, shape_fn, pop, color, tr=None, sc=None, rt=None, select=False, z=0.0):
    g = c.create(td.geometryCOMP, name); g.par.tz = z      # draw order (towards the camera) so that coplanar lines do not z-fight
    for o in list(g.children): o.destroy()
    shape_fn(g)
    m = c.create(td.constantMAT, name + '_mat')
    for ch, v in zip('rgb', color):
        if isinstance(v, str): m.par['color' + ch].expr = v
        else: m.par['color' + ch] = v
    g.par.material = m
    if not select:
        g.par.instancing = True; g.par.instancecountmode = 'oplength'; g.par.instanceop = pop
        g.par.instancetx = tr + '(0)'; g.par.instancety = tr + '(1)'; g.par.instancetz = tr + '(2)'
        if sc: g.par.instancesx = sc + '(0)'; g.par.instancesy = sc + '(1)'; g.par.instancesz = sc + '(2)'
        if rt: g.par.instancerx = rt + '(0)'; g.par.instancery = rt + '(1)'; g.par.instancerz = rt + '(2)'
    return g, m
def rect_shape(g):
    r = g.create(td.rectangleSOP, 'box'); r.par.sizex = 1; r.par.sizey = 1; r.display = True; r.render = True
def line_shape(g):
    l = g.create(td.lineSOP, 'seg'); l.par.pax = 0; l.par.pay = 0; l.par.paz = 0; l.par.pbx = 1; l.par.pby = 0; l.par.pbz = 0; l.display = True; l.render = True
WHITE = (0.93, 0.92, 0.88)
g_box, m_box = geo_for('geo_boxes', rect_shape, hp, WHITE, tr='Pw', sc='Sbox', z=0.4)
m_box.par.wireframe = 'topology'; m_box.par.wirewidth = 1
g_lin, m_lin = geo_for('geo_links', line_shape, hl, [x * 0.55 for x in WHITE], tr='Pw', sc='Slin', rt='Rotl', z=0.3)
cam = c.create(td.cameraCOMP, 'cam'); cam.par.projection = 'ortho'; cam.par.tz = 5
cam.par.orthowidth.expr = RW
hudr = c.create(td.renderTOP, 'hud_render'); hudr.par.camera = cam; hudr.par.geometry = 'geo_boxes geo_links'; hudr.par.lights = ''
setres(hudr); hudr.par.bgcolora = 1; hudr.par.antialias = 'aa2'; hudr.par.format = 'rgba16float'

# ---- grid lines, crosses at the intersections and edge ticks (all geometry, drawn by the same Render TOP)
GS = P('Gridsize')
NX = "(int(%s/%s)+2)" % (RW, GS); NY = "(int(%s/%s)+2)" % (RH, GS)
gl = c.create(td.gridPOP, 'grid_lines'); gl.par.surftype = 'lines'
gl.par.cols.expr = NX; gl.par.rows.expr = NY
gl.par.sizex.expr = "(%s-1)*%s" % (NX, GS); gl.par.sizey.expr = "(%s-1)*%s" % (NY, GS)
gl.par.tx.expr = "-%s/2+(%s-1)*%s/2" % (RW, NX, GS); gl.par.ty.expr = "-%s/2+(%s-1)*%s/2" % (RH, NY, GS)
gp = c.create(td.gridPOP, 'grid_nodes'); gp.par.surftype = 'points'
for pn in ('cols', 'rows', 'sizex', 'sizey', 'tx', 'ty'): gp.par[pn].expr = gl.par[pn].expr
def sel_shape(pop):
    def f(g):
        s_ = g.create(td.selectPOP, 'select'); s_.par.pop = pop; s_.display = True; s_.render = True
    return f
def cross_h_shape(g):
    a = g.create(td.lineSOP, 'arm'); a.par.pax = -4; a.par.pbx = 4; a.par.pay = a.par.pby = 0; a.par.paz = a.par.pbz = 0; a.display = True; a.render = True
def cross_v_shape(g):
    b = g.create(td.lineSOP, 'arm'); b.par.pay = -4; b.par.pby = 4; b.par.pax = b.par.pbx = 0; b.par.paz = b.par.pbz = 0; b.display = True; b.render = True
g_grid, m_grid = geo_for('geo_grid', sel_shape(gl), None, [x * 0.10 for x in WHITE], select=True)
g_cross_h, m_cross_h = geo_for('geo_cross_h', cross_h_shape, gp, [x * 0.5 for x in WHITE], tr='P', z=0.1)
g_cross_v, m_cross_v = geo_for('geo_cross_v', cross_v_shape, gp, [x * 0.5 for x in WHITE], tr='P', z=0.1)
tx_ = c.create(td.gridPOP, 'ticks_bottom'); tx_.par.surftype = 'points'
tx_.par.cols.expr = "(int(4*%s/%s)+2)" % (RW, GS); tx_.par.rows = 1
tx_.par.sizex.expr = "(%s-1)*%s/4" % (tx_.par.cols.expr, GS); tx_.par.sizey = 0
tx_.par.tx.expr = "-%s/2+%s/2" % (RW, tx_.par.sizex.expr); tx_.par.ty.expr = "-%s/2" % RH
ty_ = c.create(td.gridPOP, 'ticks_left'); ty_.par.surftype = 'points'
ty_.par.rows.expr = "(int(4*%s/%s)+2)" % (RH, GS); ty_.par.cols = 1
ty_.par.sizey.expr = "(%s-1)*%s/4" % (ty_.par.rows.expr, GS); ty_.par.sizex = 0
ty_.par.ty.expr = "-%s/2+%s/2" % (RH, ty_.par.sizey.expr); ty_.par.tx.expr = "-%s/2" % RW
def vtick_shape(g):
    l = g.create(td.lineSOP, 'tick'); l.par.pax = l.par.pbx = 0; l.par.pay = 0; l.par.pby = 8; l.par.paz = l.par.pbz = 0; l.display = True; l.render = True
def htick_shape(g):
    l = g.create(td.lineSOP, 'tick'); l.par.pay = l.par.pby = 0; l.par.pax = 0; l.par.pbx = 8; l.par.paz = l.par.pbz = 0; l.display = True; l.render = True
g_tb, m_tb = geo_for('geo_ticks_bottom', vtick_shape, tx_, [x * 0.7 for x in WHITE], tr='P', z=0.2)
g_tl, m_tl = geo_for('geo_ticks_left', htick_shape, ty_, [x * 0.7 for x in WHITE], tr='P', z=0.2)

# ---------------------------------------------------------------- labels: glyph quads instanced from a digit atlas (Text TOPs), one slot grid copied onto every point
glyph_tops = []
for i_, ch_ in enumerate('0123456789./'):
    t_ = c.create(td.textTOP, 'glyph_%d' % i_)
    t_.par.text = ch_; t_.par.font = 'Menlo'; t_.par.outputresolution = 'custom'; t_.par.resolutionw = 64; t_.par.resolutionh = 96
    t_.par.fontsizex = 84; t_.par.fontcolorr = t_.par.fontcolorg = t_.par.fontcolorb = 1; t_.par.bgalpha = 0
    t_.par.alignx = 'center'; t_.par.aligny = 'center'; t_.par.format = 'rgba16float'; t_.par.filtertype = 'mipmap'
    glyph_tops.append(t_)
# slot template: 17 columns x 2 lines (line 0 = id, 5 digits; line 1 = "%7.2f / %7.2f", 17 characters)
slots = c.create(td.gridPOP, 'glyph_slots'); slots.par.surftype = 'points'; slots.par.cols = 17; slots.par.rows = 2
slots.par.sizex = 16; slots.par.sizey = 1; slots.par.tx = 8; slots.par.ty = 0.5
st = mcomb('glyph_slot_info', slots,
    vecs=[('half1', 'float', [0.5]), ('one', 'float', [1.0]), ('zero', 'float', [0.0]), ('four', 'float', [4.0]), ('five', 'float', [5.0]), ('six', 'float', [6.0]),
          ('seven', 'float', [7.0]), ('eight', 'float', [8.0]), ('nine', 'float', [9.0]), ('ten', 'float', [10.0]), ('seventeen', 'float', [17.0]),
          ('eleven', 'float', [11.0]), ('twelve', 'float', [12.0]), ('two', 'float', [2.0]), ('three', 'float', [3.0]), ('ex', 'float3', [1, 0, 0]), ('ey', 'float3', [0, 1, 0]), ('ez', 'float3', [0, 0, 1])],
    combs=[('round', 'P(0)', '', '', 'Col'),
           ('asubb', 'one', 'P(1)', '', 'Ln1'), ('round', 'Ln1', '', '', 'Ln'),                  # 0 = id line, 1 = coordinates line
           ('lt', 'Col', 'five', '', 'ColLt5'),
           ('lt', 'Col', 'seventeen', '', 'ColLt17'),
           ('eq', 'Ln', 'zero', '', 'IsId'),
           ('eq', 'Ln', 'one', '', 'IsCo'),
           ('mult', 'IsId', 'ColLt5', '', 'SlotId'),
           ('mult', 'IsCo', 'ColLt17', '', 'SlotCo'),
           ('add', 'SlotId', 'SlotCo', '', 'Slot'),                                              # 1 on glyph cells that exist
           # coordinate line: numbers in columns 0-6 (x) and 10-16 (y), '.' at 4 / 14, '/' at 8
           ('lt', 'Col', 'seven', '', 'XNum'),
           ('lt', 'Col', 'ten', '', 'NotY'),
           ('asubb', 'one', 'NotY', '', 'YNum0'),
           ('asubb', 'Col', 'ten', '', 'YCol'),
           ('mult', 'YNum0', 'ColLt17', '', 'YNum'),
           ('mult', 'YNum', 'YCol', '', 'YColSel'),
           ('mult', 'XNum', 'Col', '', 'XColSel'),
           ('add', 'XColSel', 'YColSel', '', 'NCol'),                                           # column inside its number (0..6)
           ('lt', 'NCol', 'four', '', 'NLt4'),
           ('asubb', 'five', 'NCol', '', 'KLow'),
           ('asubb', 'six', 'NCol', '', 'KHigh'),
           ('asubb', 'KLow', 'KHigh', '', 'Kd'),
           ('mult', 'NLt4', 'Kd', '', 'KdSel'),
           ('add', 'KHigh', 'KdSel', '', 'KCo'),                                                # 10^k place for coordinate digits
           ('asubb', 'four', 'Col', '', 'KId'),                                                 # 10^k place for the id digits
           ('mult', 'IsId', 'KId', '', 'KIdSel'),
           ('mult', 'IsCo', 'KCo', '', 'KCoSel'),
           ('add', 'KIdSel', 'KCoSel', '', 'K'),
           ('exp10', 'K', '', '', 'P10'),
           ('add', 'XNum', 'YNum', '', 'IsNum'),
           ('mult', 'IsCo', 'IsNum', '', 'CoNum'),
           ('eq', 'NCol', 'four', '', 'IsDotCol'),
           ('mult', 'CoNum', 'IsDotCol', '', 'IsDot'),                                          # decimal point
           ('eq', 'Col', 'eight', '', 'IsSl0'),
           ('mult', 'IsCo', 'IsSl0', '', 'IsSlash'),
           ('add', 'IsDot', 'IsSlash', '', 'IsSym'),
           ('mult', 'IsDot', 'ten', '', 'DotCode'),
           ('mult', 'IsSlash', 'eleven', '', 'SlashCode'),
           ('add', 'DotCode', 'SlashCode', '', 'SymCode'),                                      # 10 '.', 11 '/'
           ('add', 'SlotId', 'CoNum', '', 'DigA'),
           ('asubb', 'DigA', 'IsDot', '', 'IsDigit'),                                           # cells that show a digit
           ('add', 'IsDigit', 'IsSym', '', 'Show'),                                             # cells that show anything
           ('mult', 'IsId', 'one', '', 'SrcIdw'),
           ('mult', 'CoNum', 'XNum', '', 'SrcXw'),
           ('mult', 'CoNum', 'YNum', '', 'SrcYw'),
           ('mult', 'ex', 'SrcIdw', '', 'SrcA'),
           ('mult', 'ey', 'SrcXw', '', 'SrcB'),
           ('mult', 'ez', 'SrcYw', '', 'SrcC'),
           ('add', 'SrcA', 'SrcB', '', 'SrcAB'),
           ('add', 'SrcAB', 'SrcC', '', 'Src'),                                                 # one-hot (id, x, y) selector
           ('lt', 'K', 'three', '', 'KLow3'),
           ('asubb', 'one', 'KLow3', '', 'KGt2'),
           ('mult', 'KGt2', 'CoNum', '', 'LeadBlank')])                                         # leading digits of the coordinates blank out zeros
st.par.angleunit = 'deg'
cp = c.create(td.copyPOP, 'glyphs_per_point'); cp.inputConnectors[0].connect(hp); cp.inputConnectors[1].connect(st)
cp.par.doattr = True; cp.par.templateattr0names = 'Col Ln IsId IsCo IsDigit Show SymCode P10 Src LeadBlank'
FS = 'max(int(%s/7.0+0.5),1)' % P('Fontsize')
MODE = '%s.menuIndex' % P('Labelmode')
gt = mcomb('glyph_text', cp,
    vecs=[('hundred', 'float', [100.0]), ('half', 'float', [0.5]), ('onep', 'float', [1.0]), ('zero', 'float', [0.0]), ('ten', 'float', [10.0]), ('twelve', 'float', [12.0]), ('invtw', 'float', [1 / 12.0]),
          ('mIsId', 'float', ['1 if %s==0 else 0' % MODE]), ('mIsCo', 'float', ['1 if %s==1 else 0' % MODE]), ('mBoth', 'float', ['1 if %s==2 else 0' % MODE]),
          ('cw', 'float', ['6*' + FS]), ('chh', 'float', ['8*' + FS]), ('hx', 'float', ['2.5*' + FS]), ('hy', 'float', ['3.5*' + FS]), ('gw', 'float', ['5*' + FS]), ('gh', 'float', ['7*' + FS]),
          ('six', 'float', [6.0]), ('two', 'float', [2.0]),
          ('ex', 'float3', [1, 0, 0]), ('ey', 'float3', [0, 1, 0]), ('ez', 'float3', [0, 0, 1])],
    combs=[('copya', 'Color(2)', '', '', 'IdS'),
           ('mult', 'Cpx(0)', 'hundred', '', 'X100a'), ('floor', 'X100a', '', '', 'X100'),
           ('mult', 'Cpx(1)', 'hundred', '', 'Y100a'), ('floor', 'Y100a', '', '', 'Y100'),
           ('mult', 'Src(0)', 'IdS', '', 'VA'), ('mult', 'Src(1)', 'X100', '', 'VB'), ('mult', 'Src(2)', 'Y100', '', 'VC'),
           ('add', 'VA', 'VB', '', 'VAB'), ('add', 'VAB', 'VC', '', 'V'),                       # the number this glyph belongs to
           ('add', 'V', 'half', '', 'Vh'),
           ('adivb', 'Vh', 'P10', '', 'Q'), ('floor', 'Q', '', '', 'Qf'), ('mod', 'Qf', 'ten', '', 'Dig'),
           ('lt', 'V', 'P10', '', 'Small'), ('mult', 'LeadBlank', 'Small', '', 'Blank'),
           ('mult', 'IsDigit', 'Dig', '', 'DigC'), ('add', 'DigC', 'SymCode', '', 'Code'),    # character 0-9, 10 '.', 11 '/'
           ('mult', 'mIsId', 'IsId', '', 'ActA'), ('mult', 'mIsCo', 'IsCo', '', 'ActB'),
           ('add', 'ActA', 'ActB', '', 'ActAB'), ('add', 'ActAB', 'mBoth', '', 'Act'),
           ('asubb', 'onep', 'Blank', '', 'NotBlank'),
           ('mult', 'Show', 'Act', '', 'VisA'), ('mult', 'VisA', 'NotBlank', '', 'VisB'), ('mult', 'VisB', 'Valid', '', 'Vis'),
           ('mult', 'Ln', 'mBoth', '', 'Bl'),
           ('mult', 'Bs', 'half', '', 'Bh'),
           ('add', 'Pw(0)', 'Bh', '', 'Ox0'), ('add', 'Ox0', 'six', '', 'Ox'),
           ('mult', 'Col', 'cw', '', 'CxO'), ('add', 'Ox', 'CxO', '', 'Gx0'), ('add', 'Gx0', 'hx', '', 'Gx'),
           ('add', 'Pw(1)', 'Bh', '', 'Oy0'), ('add', 'Oy0', 'two', '', 'Oy'),
           ('mult', 'Bl', 'chh', '', 'ByO'), ('asubb', 'Oy', 'ByO', '', 'Gy0'), ('asubb', 'Gy0', 'hy', '', 'Gy'),
           ('mult', 'ex', 'Gx', '', 'GPx'), ('mult', 'ey', 'Gy', '', 'GPy'), ('add', 'GPx', 'GPy', '', 'Gpos'),
           ('mult', 'gw', 'Vis', '', 'GwV'), ('mult', 'gh', 'Vis', '', 'GhV'),
           ('mult', 'ex', 'GwV', '', 'GSx'), ('mult', 'ey', 'GhV', '', 'GSy'), ('add', 'GSx', 'GSy', '', 'GSxy'), ('add', 'GSxy', 'ez', '', 'Gsc'),
           ('copya', 'Code', '', '', 'Glyph')])                                                # which glyph TOP (0-9, '.', '/') this quad shows
def glyph_shape(g):
    r = g.create(td.rectangleSOP, 'quad'); r.par.sizex = 1; r.par.sizey = 1; r.par.texture = 'face'; r.display = True; r.render = True
g_txt, m_txt = geo_for('geo_labels', glyph_shape, gt, [1, 1, 1], tr='Gpos', sc='Gsc', z=0.5)
g_txt.par.instancetexmode = 'replace'
g_txt.par.instancetexs = ' '.join(t_.name for t_ in glyph_tops)      # one texture per character, picked per instance
g_txt.par.instancetexindexop = gt; g_txt.par.instancetexindex = 'Glyph'
m_txt.par.colorr.expr = "%s if %s.menuIndex==1 else 1.0" % (WHITE[0], P('Labelcolor'))
m_txt.par.colorg.expr = "%s if %s.menuIndex==1 else 0.08" % (WHITE[1], P('Labelcolor'))
m_txt.par.colorb.expr = "%s if %s.menuIndex==1 else 0.06" % (WHITE[2], P('Labelcolor'))
m_txt.par.blending = True; m_txt.par.srcblend = 'sa'; m_txt.par.destblend = 'omsa'
m_txt.par.depthtest = False

# the picture itself is drawn by the same Render TOP (a pixel-exact textured quad, brightness = Dim) and every HUD element is added on top of it
def image_shape(g):
    r = g.create(td.rectangleSOP, 'quad'); r.par.sizex.expr = "op('../res')['w']"; r.par.sizey.expr = "op('../res')['h']"; r.par.texture = 'face'; r.display = True; r.render = True
g_img, m_img = geo_for('geo_image', image_shape, None, [P('Dim')] * 3, select=True, z=-0.2)
g_img.par.tx = -0.5; g_img.par.ty = -0.5
m_img.par.colormap = sw; m_img.par.colormapfilter = 'nearest'
for m_ in (m_img, m_box, m_lin, m_grid, m_cross_h, m_cross_v, m_tb, m_tl, m_txt):
    m_.par.depthtest = False; m_.par.blending = True
    m_.par.srcblend = 'one'; m_.par.destblend = 'one'          # everything adds onto the black background (the picture is just the first thing added)
    m_.par.separatealphafunc = True; m_.par.srcblenda = 'zero'; m_.par.destblenda = 'one'     # alpha stays 1
    m_.par.depthwriting = False
m_txt.par.srcblend = 'sa'
hudr.par.geometry = 'geo_image geo_grid geo_cross_h geo_cross_v geo_ticks_bottom geo_ticks_left geo_links geo_boxes geo_labels'
hudr.par.bgcolora = 1
cam.par.tx = -0.5; cam.par.ty = -0.5       # half a pixel: one-pixel lines land on pixel centres

# ---------------------------------------------------------------- scanlines: multiply by a 1x2 pixel tile (static texture)
sck = c.create(td.tableDAT, 'scan_keys'); sck.appendRow(['pos', 'r', 'g', 'b', 'a']); sck.appendRow([0, 0, 0, 0, 1]); sck.appendRow([0.5, 1, 1, 1, 1])
scr = c.create(td.rampTOP, 'scan_cell'); scr.par.type = 'vertical'; scr.par.dat = sck; scr.par.interpnotches = 'step'
scr.par.outputresolution = 'custom'; scr.par.resolutionw = 1; scr.par.resolutionh = 2; scr.par.format = 'rgba16float'
scl = c.create(td.levelTOP, 'scan_strength'); scl.inputConnectors[0].connect(scr)
scl.par.outlow.expr = '1-%s*0.35' % P('Scanlines'); scl.par.outhigh = 1; scl.par.format = 'rgba16float'
sct = c.create(td.tileTOP, 'scan_tile'); sct.inputConnectors[0].connect(scl)
sct.par.repeatx.expr = RW; sct.par.repeaty.expr = RH + '/2.0'; setres(sct); sct.par.format = 'rgba16float'; sct.par.extend = 'repeat'
scm = c.create(td.compositeTOP, 'scanlines'); scm.par.operand = 'multiply'; scm.inputConnectors[0].connect(hudr); scm.inputConnectors[1].connect(sct)
setres(scm); scm.par.format = 'rgba16float'
finish_v2(c, COMP, scm, sw)
report(c)
