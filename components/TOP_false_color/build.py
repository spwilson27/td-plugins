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

# ---- native-build helpers (natB) ----
import math
def mk(par, typ, name, ins=(), **kw):
    """create op, set params. value str starting with '=' -> expression; tuple/list for menus not needed."""
    o = par.create(typ, name)
    for k, v in kw.items():
        p = getattr(o.par, k)
        if isinstance(v, str) and v.startswith('='):
            p.expr = v[1:]
        else:
            p.val = v
    for i, s in enumerate(ins):
        if s is not None:
            o.inputConnectors[i].connect(s.outputConnectors[0] if getattr(s, 'isCOMP', False) else s)
    return o
def resx(o, par_expr_w="op('res')['w']", par_expr_h="op('res')['h']"):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = par_expr_w; o.par.resolutionh.expr = par_expr_h
    return o
def keys_dat(par, name, rows):
    d = par.create(td.tableDAT, name)
    d.clear(); d.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for r in rows: d.appendRow([('%.5g' % x) for x in r])
    return d
def ramp_from(par, name, rows, w=1024, h=1, typ='horizontal', **kw):
    d = keys_dat(par, name + '_keys', rows)
    r = par.create(td.rampTOP, name)
    r.par.dat = d; r.par.type = typ
    r.par.extendleft = 'hold'; r.par.extendright = 'hold'
    r.par.outputresolution = 'custom'; r.par.resolutionw = w; r.par.resolutionh = h
    r.par.format = 'rgba16float'
    for k, v in kw.items():
        p = getattr(r.par, k)
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        else: p.val = v
    return r
def smooth(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

COMP = 'TOP_false_color'
c = new_comp(COMP)
add_pars(c, [
    ('Map', 'menu', [('thermal', 'Thermal'), ('xray', 'X-Ray'), ('night', 'Night Vision'), ('custom', 'Custom Gradient')], 0),
    ('Driver', 'menu', [('luma', 'Luminance'), ('in2', 'In2 (depth)')], 0),
    ('Gain', 'float', 1.3, 0, 4),
    ('Bias', 'float', 0.0, -1, 1),
    ('Invert', 'toggle', 0),
    ('Edges', 'float', 0.4, 0, 1),
    ('Edgecolor', 'rgb', (0.93, 0.91, 0.85)),
    ('Noise', 'float', 0.3, 0, 1),
    ('Isotherms', 'float', 0.0, 0, 1),
    ('Mixoriginal', 'float', 0.0, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    ('Crosshair', 'toggle', 1),
    ('Legend', 'toggle', 1),
    ('Target', 'xy', (0.5, 0.5)),
    ('Hudcolor', 'rgb', (0.93, 0.91, 0.85)),
    ('Colora', 'rgb', (0.0, 0.0, 0.0)),
    ('Colorb', 'rgb', (0.9, 0.05, 0.05)),
    ('Colorc', 'rgb', (0.93, 0.91, 0.85)),
    *COMMON,
])
P = 'parent().par.'
PP = 'parent(2).par.'
# ---------------- input + demo ----------------
res_chop(c)
i1 = c.create(td.inTOP, 'in1')
dm = new_demo(c)
src = c.create(td.switchTOP, 'src')
src.par.index.expr = HASIN
setres(src); src.par.format = 'rgba16float'
in2 = c.create(td.inTOP, 'in2')
add_mod(c, 'in3')
drv = mk(c, td.switchTOP, 'driver', [src, in2],
         index="=1 if (parent().par.Driver=='in2' and len(parent().inputConnectors)>1 and parent().inputConnectors[1].connections) else 0",
         format='rgba16float')
setres(drv)

# ---------------- palettes: one Ramp TOP per map, picked by a Switch ----------------
def rk(f, n=33): return [(i / (n - 1),) + tuple(f(i / (n - 1))) + (1,) for i in range(n)]
pal = c.create(td.baseCOMP, 'palettes')
therm = [(0, 0, 0, 0), (.25, .18, 0, .35), (.5, .85, .05, .1), (.75, 1, .65, .05), (1, 1, 1, .9)]
r_th = ramp_from(pal, 'thermal', [t + (1,) for t in therm])
def xray(l):
    x = l ** .8; a = smooth(0, .5, x); b = smooth(.45, 1, x)
    return (.12 * a + .6 * b, .3 * a + .8 * b, .45 * a + .95 * b)
r_xr = ramp_from(pal, 'xray', rk(xray))
def night(l):
    return (.04 * l ** .75 + .03 * l, 1. * l ** .75 + .2 * l, .22 * l ** .75 + .05 * l)
r_nv = ramp_from(pal, 'night', rk(night))
# custom 3-stop gradient: Constant CHOPs (driven by Colora/b/c) -> Join -> CHOP to DAT -> Ramp keys
cc = []
for k, (nm, pos) in enumerate((('Colora', 0), ('Colorb', 0.5), ('Colorc', 1))):
    kc = pal.create(td.constantCHOP, 'stop_' + nm.lower())
    for j, (ch, ex) in enumerate((('pos', str(pos)), ('r', 'parent(2).par.%sr' % nm), ('g', 'parent(2).par.%sg' % nm),
                                  ('b', 'parent(2).par.%sb' % nm), ('a', '1'))):
        setattr(kc.par, 'name%d' % j, ch); getattr(kc.par, 'value%d' % j).expr = ex
    cc.append(kc)
jn = pal.create(td.joinCHOP, 'stops')
for i, kc in enumerate(cc): jn.inputConnectors[i].connect(kc)
jd = pal.create(td.choptoDAT, 'stops_table'); jd.par.chop = jn; jd.par.names = True; jd.par.output = 'colperchan'
r_cu = pal.create(td.rampTOP, 'custom'); r_cu.par.dat = jd; r_cu.par.type = 'horizontal'
r_cu.par.extendleft = 'hold'; r_cu.par.extendright = 'hold'
r_cu.par.outputresolution = 'custom'; r_cu.par.resolutionw = 1024; r_cu.par.resolutionh = 1; r_cu.par.format = 'rgba16float'
palsw = pal.create(td.switchTOP, 'palette')
for i, r in enumerate((r_th, r_xr, r_nv, r_cu)): palsw.inputConnectors[i].connect(r)
palsw.par.index.expr = 'parent(2).par.Map.menuIndex'
po = pal.create(td.outTOP, 'palette_out'); po.inputConnectors[0].connect(palsw)

# ---------------- one GLSL core: grain, gain/bias, palette lookup, edges, isotherms, night post, HUD ----------------
uP_ = uP()
gl = c.create(td.glslTOP, 'falsecolor')
gl.par.pixeldat = mkdat(c, 'falsecolor_code', rd(COMP, 'fc.glsl'))
gl.inputConnectors[0].connect(src); gl.inputConnectors[1].connect(drv); gl.inputConnectors[2].connect(pal.outputConnectors[0])
vecs = [
    ('uP', [PEXPR, 8, 240, 0]),
    ('uA', [P + 'Map.menuIndex', "%s+%s*%s" % (P + 'Gain', P + 'Modamount', MOD('band1')), P + 'Bias', P + 'Invert']),
    ('uB', [P + 'Edges', P + 'Noise', P + 'Isotherms', P + 'Mixoriginal']),
    ('uC', [P + 'Crosshair', P + 'Legend', P + 'Targetx', P + 'Targety']),
    ('uD', [P + 'Hudcolorr', P + 'Hudcolorg', P + 'Hudcolorb', 1]),
    ('uE', [P + 'Edgecolorr', P + 'Edgecolorg', P + 'Edgecolorb', 1]),
]
gl.seq.vec.numBlocks = len(vecs)
for i, (n, vals) in enumerate(vecs):
    gl.par['vec%dname' % i] = n
    for j, v in enumerate(vals):
        q = gl.par['vec%dvalue%s' % (i, 'xyzw'[j])]
        if isinstance(v, str): q.expr = v
        else: q.val = v
gl.par.format = 'rgba16float'; setres(gl)
# ---------------- demo source (native): discs, bar, scan line, ramp strip ----------------
DH = "op('../res')['h']"; DW = "op('../res')['w']"
A = "(6.2831853*((absTime.seconds/8.0)%1.0))"
def dres(o): return resx(o, DW, DH)
bg = mk(dm, td.noiseTOP, 'bg_noise', type='simplex3d', period=0.45, mono=True, amp=0.5, offset=0.5, tz='=absTime.seconds*0.12', format='rgba16float'); dres(bg)
bg_l = mk(dm, td.mathTOP, 'bg_level', [bg], gain=0.10, postoff=0.025, format='rgba16float')
cell = mk(dm, td.rectangleTOP, 'grid_cell', sizeunit='fraction', centerunit='fraction', sizex=0.5, sizey=0.5, centerx=-0.25, centery=-0.25,
          bgalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, borderwidth=0, softness=0, format='rgba16float')
cell.par.outputresolution = 'custom'; cell.par.resolutionw.expr = DH + '/12'; cell.par.resolutionh.expr = DH + '/12'
grid = mk(dm, td.tileTOP, 'grid', [cell], repeatx='=12*%s/%s' % (DW, DH), repeaty=12, format='rgba16float'); dres(grid)
grid_l = mk(dm, td.mathTOP, 'grid_level', [grid], gain=0.05, format='rgba16float')
bg_sum = mk(dm, td.compositeTOP, 'bg_sum', [bg_l, grid_l], operand='add', format='rgba16float')
x = mk(dm, td.reorderTOP, 'bg', [bg_sum], outputalphachan='one', format='rgba16float')
for i in range(6):
    k1 = 1 + i % 2; k2 = 1 + i // 3
    cx = "math.sin(%s*%d+%.2f)*.4*%s" % (A, k1, i * 1.7, DW); cy = "math.cos(%s*%d+%.2f)*.30*%s" % (A, k2, i * 2.3, DH)
    r = '%.3f*%s' % (.10 + .025 * i, DH)
    tone = (1, .08, .05) if i == 2 else (.92, .9, .84)
    def circ(name, inp, rad, **kw):
        o = mk(dm, td.circleTOP, name, [inp], radiusunit='pixels', centerunit='pixels', radiusx='=' + rad, radiusy='=' + rad,
               centerx='=' + cx, centery='=' + cy, bgalpha=0, format='rgba16float', **kw); dres(o); return o
    x = circ('disc%d' % i, x, r, fillcolorr=tone[0] * .15, fillcolorg=tone[1] * .15, fillcolorb=tone[2] * .15, fillalpha=1,
             borderwidth=0, softness=0)
    x = circ('glow%d' % i, x, r, fillcolorr=tone[0] * 1.2, fillcolorg=tone[1] * 1.2, fillcolorb=tone[2] * 1.2, fillalpha=1,
             borderwidth=0, softnessunit='pixels', softness='=' + r, softnesstype='halfcosine')
    x = circ('ring%d' % i, x, r + '*1.35', fillalpha=0, borderwidthunit='pixels', borderwidth=2.4,
             borderr=tone[0] * .7, borderg=tone[1] * .7, borderb=tone[2] * .7, borderalpha='=.5+.5*math.sin(%s*3+%.2f)' % (A, i * 1.0))
# rotating bar: dim base + 8 bright segments
ROT = "math.degrees(%s)" % A
def barrect(name, inp, ox, w, v):
    off = '(%s)*%s' % (ox, DH)
    o = mk(dm, td.rectangleTOP, name, [inp], sizeunit='fractionaspect', centerunit='fractionaspect', sizex='=%s*%s/%s' % (w, DH, DW), sizey='=.05*%s/%s' % (DH, DW),
           centerx='=%s*math.cos(%s)/%s' % (off, A, DW), centery='=(-.2*%s+%s*math.sin(%s))/%s' % (DH, off, A, DW), rotate='=' + ROT,
           fillcolorr=v, fillcolorg=v, fillcolorb=v * .95, fillalpha=1, bgalpha=0, borderwidth=0, softness=0, format='rgba16float'); dres(o); return o
x = barrect('bar', x, '0', '.8', 0.4)
for j in range(8):
    x = barrect('bar_seg%d' % j, x, '%.3f' % (-.325 + .1 * j), '.05', 1.26)
# sweeping scan line (additive)
x = mk(dm, td.rectangleTOP, 'scanline', [x], sizeunit='pixels', centerunit='pixels', sizex='=' + DW, sizey=2.0, centerx=0,
       centery="=(((absTime.seconds/8.0)%%1.0)-0.5)*%s" % DH, fillcolorr=.4, fillcolorg=.4, fillcolorb=.4, fillalpha=1, bgalpha=0,
       borderwidth=0, softness=0, operand='add', format='rgba16float'); dres(x)
# range strip at the top
strip = ramp_from(dm, 'range_strip', [(0, 0, 0, 0, 1), (1, 1, .98, .95, 1)], w=1280, h=64)
strip.par.resolutionw.expr = DW; strip.par.resolutionh.expr = '%s*0.07' % DH
x = mk(dm, td.compositeTOP, 'with_strip', [strip, x], operand='over', prefit='nativeres', justifyv='top', size='input2', format='rgba16float')
demo_out(dm, x)
src.inputConnectors[0].connect(dm.outputConnectors[0]); src.inputConnectors[1].connect(i1)
result = gl
finish_v2(c, COMP, result, src)
report(c)
