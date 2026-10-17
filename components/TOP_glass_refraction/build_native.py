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

COMP = 'TOP_glass_refraction'
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
    ('Shape', 'menu', [('morph', 'Morph blob/cube'), ('torus', 'Torus'), ('cube', 'Rounded cube')], 0),
    ('Ior', 'float', 1.45, 1.0, 2.4),
    ('Dispersion', 'float', 0.12, 0, 0.5),
    ('Frost', 'float', 0.0, 0, 1),
    ('Size', 'float', 1.0, 0.3, 2),
    ('Morphspeed', 'int', 1, 0, 6),
    ('Spin', 'int', 1, 0, 4),
    ('Highlights', 'float', 1.0, 0, 3),
    ('Absorption', 'float', 0.6, 0, 3),
    ('Camdistance', 'float', 4.0, 2, 10),
    ('Bgscale', 'float', 1.0, 0.3, 3),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
P = 'parent().par.'
F = ' + 0*absTime.frame'
res_chop(c)
RWe = "op('res')['w']"; RHe = "op('res')['h']"
ASP = "(%s/%s)" % (RWe, RHe)
def sres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RWe; o.par.resolutionh.expr = RHe; return o
add_mod(c, 'in2')

# ---------------- demo (preview only): scrolling bars + grid + orbiting red dot, all native ----------------
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
def dres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = "op('../res')['w']"; o.par.resolutionh.expr = "op('../res')['h']"; return o
def dn(typ, name, *ins, **kw): return dres(nat(d, typ, name, *ins, **kw))
PH = "((absTime.seconds/8.0) % 1.0)"
TH = "(%s*2*math.pi)" % PH
# bars: 8 x 14 random cells; each row scrolls at its own whole-cycle speed (Displace TOP driven by a 14-value CHOP)
cells = nat(d, 'noiseTOP', 'bar_cells', type='randomgpu', mono=True, seed=3, amp=0.5, offset=0.5)
cells.par.outputresolution = 'custom'; cells.par.resolutionw = 8; cells.par.resolutionh = 14
on = nat(d, 'thresholdTOP', 'bars_on', cells, threshold=0.35, comparator='less')
cells_up = dn('resolutionTOP', 'bar_cells_up', on, inputfiltertype='nearest', filtertype='nearest')
def stripes(name, kind, per, thr, cmpn='less'):
    r = dn('rampTOP', name + '_ramp', type=kind, period=per, extendleft='repeat', extendright='sameasleft')
    return dn('thresholdTOP', name, r, threshold=thr, comparator=cmpn)
seg_x = stripes('bar_length', 'horizontal', 1 / 8.0, 0.2)            # 80 % of each cell is bar
bars_x = dn('compositeTOP', 'bars_along_row', cells_up, seg_x, operand='multiply')
speeds = d.create(td.constantCHOP, 'row_speeds')
for r_ in range(14):
    getattr(speeds.par, 'name%d' % r_).val = 'r%d' % r_
    getattr(speeds.par, 'value%d' % r_).val = (1 if r_ % 2 == 0 else -1) * (1 + r_ % 3)
spd_top = nat(d, 'choptoTOP', 'row_speed_map', chop=speeds)
spd_up = dn('resolutionTOP', 'row_speed_up', spd_top, inputfiltertype='nearest', filtertype='nearest')
scroll = dn('displaceTOP', 'scroll_rows', bars_x, spd_up, horzsource='red', vertsource='none', midpointx=0, midpointy=0,
            displaceweightx="=%s/2" % PH, displaceweighty=0, extend='repeat')
row_lo = stripes('row_gap_lo', 'vertical', 1 / 14.0, 0.18)
row_hi = stripes('row_gap_hi', 'vertical', 1 / 14.0, 0.82, 'greater')
rowm = dn('compositeTOP', 'row_mask', row_lo, row_hi, operand='multiply')
bars = dn('compositeTOP', 'bars', scroll, rowm, operand='multiply')
barcol = dn('levelTOP', 'bar_color', bars, brightness1=0.78)
grid_x = stripes('grid_x', 'horizontal', 1 / 40.0, 0.97); grid_y = stripes('grid_y', 'vertical', 1 / 22.0, 0.97)
grid = dn('levelTOP', 'grid_lines', dn('compositeTOP', 'grid_sum', grid_x, grid_y, operand='maximum'), brightness1=0.12)
dotx = "=math.cos(%s)*0.27" % TH; doty = "=math.sin(%s*2)*0.28" % TH
dot = dn('circleTOP', 'red_dot', radiusx=0.07 * 0.5625, radiusy=0.07 * 0.5625, softness=0.003, centerx=dotx, centery=doty, fillcolorr=2.0, fillcolorg=0.16,
         fillcolorb=0.1, fillalpha=1, bgalpha=0, bgcolorr=0, bgcolorg=0, bgcolorb=0)
ring = dn('circleTOP', 'red_ring', radiusx=0.14 * 0.5625, radiusy=0.14 * 0.5625, softness=0.001, centerx=dotx, centery=doty, fillalpha=0, bgalpha=0,
          borderwidth=0.004, borderr=0.8, borderg=0.08, borderb=0.04, borderalpha=1)
base = dn('constantTOP', 'dark', colorr=0.02, colorg=0.02, colorb=0.02, alpha=1)
barc = dn('compositeTOP', 'bars_tinted', barcol, dn('constantTOP', 'bone', colorr=0.92, colorg=0.9, colorb=0.85, alpha=1), operand='multiply')
sc_base = dn('compositeTOP', 'bars_and_grid', base, barc, grid, operand='add')
sc2 = dn('compositeTOP', 'scene', dot, ring, sc_base, operand='over')      # first input is on top
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(sc2); do.par.label = 'demo source'
src = nat(c, 'switchTOP', 'src', d.outputConnectors[0], i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
sres(src); src.par.format = 'rgba16float'

# ======================= refraction as a native network =======================
TAU2 = "(2*math.pi)"
PHm = "((absTime.seconds/8.0) % 1.0)"
THm = "(%s*2*math.pi)" % PHm
SZ = P + 'Size'; CD = P + 'Camdistance'
HH = RHe
UNIT = "(%s*%s/%s)" % (SZ, HH, CD)             # one world unit of the shape, in pixels (0.85 world units radius at Size 1, camera distance 4)
M_ = "(0.5+0.5*math.sin(%s*%sMorphspeed))" % (THm, P)
# --- shape masks (white on black, in pixels so the proportions do not depend on the aspect ratio) ---
def shp(typ, name, **kw):
    o = nat(c, typ, name, **kw); sres(o); return o
BGK = dict(bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1)
FIL = dict(fillcolorr=1, fillcolorg=1, fillcolorb=1, fillalpha=1)
morph = shp('rectangleTOP', 'shape_morph', sizeunit='pixels', antialias=True,
            sizex="=2*0.55*%s*%s*2/1.0" % (M_, UNIT) if False else "=2*0.55*%s*%s" % (M_, UNIT), sizey="=2*0.55*%s*%s" % (M_, UNIT),
            cornerradius="=(0.85-0.55*%s)*%s" % (M_, UNIT), cornerradiusunit='pixels', **FIL, **BGK)
cube = shp('rectangleTOP', 'shape_cube', sizeunit='pixels', antialias=True, sizex="=2*0.55*%s" % UNIT, sizey="=2*0.55*%s" % UNIT,
           cornerradius="=(0.12+0.25*%s)*%s" % (M_, UNIT), cornerradiusunit='pixels', **FIL, **BGK)
t_out = shp('circleTOP', 'torus_outer', radiusunit='pixels', radiusx="=(0.7+0.3+0.12*%s)*%s" % (M_, UNIT), radiusy="=(0.7+0.3+0.12*%s)*%s" % (M_, UNIT), softness=1,
            softnessunit='pixels', **FIL, **BGK)
t_in = shp('circleTOP', 'torus_inner', radiusunit='pixels', radiusx="=(0.7-0.3-0.12*%s)*%s" % (M_, UNIT), radiusy="=(0.7-0.3-0.12*%s)*%s" % (M_, UNIT), softness=1,
           softnessunit='pixels', **FIL, **BGK)
torus = nat(c, 'compositeTOP', 'shape_torus', t_out, t_in, operand='subtract')
pick = nat(c, 'switchTOP', 'shape', morph, torus, cube); pick.par.index.expr = P + 'Shape.menuIndex' + F
SPIN = "%sSpin*360*%s" % (P, PHm)
spun = nat(c, 'transformTOP', 'spin', pick, rotate="=" + SPIN, sy="=abs(math.cos(0.5+0.3*math.sin(%s)))" % THm, extend='zero')
# --- height = blurred mask, normals from it ---
hgt = nat(c, 'blurTOP', 'height', spun, type='gaussian', size="=0.45*%s" % UNIT, filterscalex=1, filterscaley=1)
hgt_c = nat(c, 'levelTOP', 'height_curve', hgt, gamma1=1.6)
nmap = nat(c, 'normalmapTOP', 'normal_map', hgt_c, source='red', zscale="=%s*0.012" % ("(720.0/%s)" % HH))
nsig = nat(c, 'channelmixTOP', 'normals_signed', nmap, red1=2, red2=0, red3=0, constant1=-1, green1=0, green2=2, green3=0, constant2=-1,
           blue1=0, blue2=0, blue3=2, constant3=-1)
inside = nat(c, 'thresholdTOP', 'inside_shape', hgt, threshold=0.01, comparator='less')
# --- refraction strength (thicker glass bends more) and per-channel IOR ---
thick = nat(c, 'mathTOP', 'thickness', hgt_c, gain="=1.7*%s" % SZ)
stren = nat(c, 'mathTOP', 'bend_strength', thick, gain="=0.07*%s" % SZ, postoff="=0.05*%s" % SZ)
ior = "(%sIor+%sModamount*%s*0.5)" % (P, P, MOD('band1'))
def eta(k): return "(1/(%s+%sDispersion*%s*0.5))" % (ior, P, k)
dmap = nat(c, 'compositeTOP', 'bend_vectors', nsig, stren, operand='multiply')
chans = []
for k, ch in ((-1, 'red'), (0, 'green'), (1, 'blue')):
    w = "=(%s-1)/(2*%sBgscale)" % (eta(k), P)
    chans.append(nat(c, 'displaceTOP', 'refract_' + ch, src, dmap, horzsource='red', vertsource='green', midpointx=0, midpointy=0,
                     displaceweightx=w + "/" + ASP, displaceweighty=w, extend='mirror'))
refr = nat(c, 'reorderTOP', 'dispersion', chans[0], chans[1], chans[2], outputred='input1', outputredchan='red', outputgreen='input2',
           outputgreenchan='green', outputblue='input3', outputbluechan='blue', outputalpha='input2', outputalphachan='alpha')
frost = nat(c, 'blurTOP', 'frost', refr, type='gaussian', size="=%sFrost*0.05*%s*2*(1+0.3*1.0)" % (P, HH), filterscalex=1, filterscaley=1)
frost_on = nat(c, 'switchTOP', 'frost_on', refr, frost); frost_on.par.index.expr = "(1 if %sFrost>0.003 else 0)%s" % (P, F)
# --- absorption: thicker = darker and warmer ---
A_ = P + 'Absorption'
absf = nat(c, 'channelmixTOP', 'absorption_tint', thick, red1="=-%s*0.12" % A_, red2=0, red3=0, constant1=1, green1="=-%s*0.07" % A_, green2=0, green3=0,
           constant2=1, blue1="=-%s*0.04" % A_, blue2=0, blue3=0, constant3=1)
absf2 = nat(c, 'levelTOP', 'absorption_floor', absf, clamp=True, clamplow2=0, clamphigh2=1)
tinted = nat(c, 'compositeTOP', 'absorbed', frost_on, absf2, operand='multiply')
# --- highlights: two spec lights + fresnel rim, dot products with Channel Mix ---
def hv(l):
    n = math.sqrt(l[0] ** 2 + l[1] ** 2 + l[2] ** 2); lx, ly, lz = l[0] / n, l[1] / n, l[2] / n + 1
    m = math.sqrt(lx * lx + ly * ly + lz * lz); return lx / m, ly / m, lz / m
def dotmap(name, v):
    return nat(c, 'channelmixTOP', name, nsig, **{'%s%d' % (ch, i + 1): v[i] for ch in ('red', 'green', 'blue') for i in range(3)},
               constant1=0, constant2=0, constant3=0)
h1 = hv((-.5, .8, .6)); h2 = hv((.7, .3, .5))
sp1 = nat(c, 'levelTOP', 'spec_key', dotmap('n_dot_h1', h1), clamp=True, clamplow2=0, clamphigh2=1, gamma1=1 / 600.0, brightness2=5)
sp2 = nat(c, 'levelTOP', 'spec_fill', dotmap('n_dot_h2', h2), clamp=True, clamplow2=0, clamphigh2=1, gamma1=1 / 250.0, brightness2=1.5)
nz1 = nat(c, 'channelmixTOP', 'one_minus_nz', nsig, red1=0, red2=0, red3=-1, constant1=1, green1=0, green2=0, green3=-1, constant2=1, blue1=0, blue2=0, blue3=-1, constant3=1)
fres = nat(c, 'levelTOP', 'fresnel', nz1, clamp=True, clamplow2=0, clamphigh2=1, gamma1=0.25, brightness2=0.7)
hl = nat(c, 'compositeTOP', 'highlights_sum', sp1, sp2, fres, operand='add')
hl2 = nat(c, 'levelTOP', 'highlights_gain', hl, brightness1="=" + P + 'Highlights')
hl3 = nat(c, 'compositeTOP', 'highlights_tint', hl2, nat(c, 'constantTOP', 'warm_white', colorr=1, colorg=0.97, colorb=0.92, alpha=1), operand='multiply')
lit = nat(c, 'compositeTOP', 'glass_color', tinted, hl3, operand='add')
sres(lit)
# --- put the glass over the untouched background ---
gl_m = nat(c, 'compositeTOP', 'glass_only', lit, inside, operand='multiply')
gl_a = nat(c, 'reorderTOP', 'glass_alpha', gl_m, inside, outputalpha='input2', outputalphachan='red')
gl_p = nat(c, 'levelTOP', 'glass_premultiply', gl_a, premultrgbbyalpha=True)
res_ = nat(c, 'compositeTOP', 'glass_over_background', gl_p, src, operand='over'); sres(res_)
finish_v2(c, COMP, res_, src)
report(c)
