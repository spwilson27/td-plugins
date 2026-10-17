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

COMP = 'TOP_slit_scan'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('hgradient', 'Horizontal gradient'), ('vgradient', 'Vertical gradient'), ('radial', 'Radial'),
                     ('noise', 'Noise'), ('in2', 'In2 TOP map')], 0),
    ('Frames', 'float', 40, 1, 126),
    ('Direction', 'menu', [('forward', 'Forward'), ('reverse', 'Reverse')], 0),
    ('Speed', 'float', 0.15, -2, 2),
    ('Smooth', 'toggle', 1),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [
    ('Resolution', 'wh', (1280, 720)),
    ('Buffersize', 'int', 64, 8, 128),
    ('Bufferscale', 'float', 0.5, 0.125, 1),
], page='Render')
look_pg(c)
P = 'parent().par.'
# ------------------------------------------------------------------ demo source (native, gated)
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
DW = 'parent(2).par.Resolutionw'; DH = 'parent(2).par.Resolutionh'
LK = 'parent(2).par.Look.menuIndex'; AC = 'parent(2).par.Accent'
T = 'absTime.seconds'
def dres(o): return setres(o, DW, DH)
def disc_col(i, ch, v=0.74):
    h_ = '(0.12*%d+%s*0.03)' % (i, T)
    orig = "__import__('colorsys').hsv_to_rgb(%s%%1.0,.85,%s)[%d]" % (h_, v, ch)
    mono = "%s*(.35+.65*((%s*3)%%1.0))*%s*.9" % (v, h_, (.96, .94, .89)[ch])
    base = "(%s if %s==1 else %s)" % (mono, LK, orig)
    if i == 2:
        red = (1.0, .04, .04)[ch] * .9
        base = "(%s*(1-%s)+%s*%s if %s==1 else %s)" % (mono, AC, red, AC, LK, orig)
    return '=' + base
bg = mk(d, td.noiseTOP, 'bg_noise', type='simplex3d', period=0.4, mono=True, amp=0.5, offset=0.5, tz='=%s*0.1' % T, format='rgba16float'); dres(bg)
bg_l = mk(d, td.mathTOP, 'bg_level', [bg], gain='=0.02 if %s==1 else 0.10' % LK, postoff='=0.0 if %s==1 else 0.10' % LK, format='rgba16float')
cell = mk(d, td.rectangleTOP, 'grid_cell', sizeunit='fraction', centerunit='fraction', sizex=0.5, sizey=0.5, centerx=-0.25, centery=-0.25,
          bgalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, borderwidth=0, softness=0, format='rgba16float')
cell.par.outputresolution = 'custom'; cell.par.resolutionw.expr = DH + '/14'; cell.par.resolutionh.expr = DH + '/14'
grid = mk(d, td.tileTOP, 'grid', [cell], repeatx='=14*%s/%s' % (DW, DH), repeaty=14, format='rgba16float'); dres(grid)
grid_l = mk(d, td.mathTOP, 'grid_level', [grid], gain='=0.012 if %s==1 else 0.06' % LK, format='rgba16float')
bgs = mk(d, td.compositeTOP, 'bg_sum', [bg_l, grid_l], operand='add', format='rgba16float')
x = mk(d, td.reorderTOP, 'bg', [bgs], outputalphachan='one', format='rgba16float')
# rotating bar: centre piece and two bright ends
BA = '(%s*0.7)' % T
def bar(name, inp, off, w, rgb):
    o = mk(d, td.rectangleTOP, name, [inp], sizeunit='fractionaspect', centerunit='fractionaspect',
           sizex='=%s*%s/%s' % (w, DH, DW), sizey='=.06*%s/%s' % (DH, DW),
           centerx='=%s*%s*math.cos(%s)/%s' % (off, DH, BA, DW), centery='=(-.18*%s+%s*%s*math.sin(%s))/%s' % (DH, off, DH, BA, DW),
           rotate='=math.degrees(%s)' % BA, bgalpha=0, borderwidth=0, softness=0, format='rgba16float')
    for k, ch in zip('rgb', range(3)):
        getattr(o.par, 'fillcolor' + k).expr = rgb[ch]
    dres(o); return o
def barcol(scale):
    out = []
    for ch in range(3):
        orig = "__import__('colorsys').hsv_to_rgb((.55+.1*math.sin(%s))%%1.0,.7,1.0)[%d]*%s" % (T, ch, scale)
        mono = "%s*%s" % ((.96, .94, .89)[ch] * .9 * 0.8 * scale, 1)
        red = (1.0, .04, .04)[ch] * scale
        out.append("(%s*(1-%s)+%s*%s if %s==1 else %s)" % (mono, AC, red, AC, LK, orig))
    return out
x = bar('bar', x, '0', '.84', barcol(1.0))
x = bar('bar_end_a', x, '.36', '.12', barcol(2.2))
x = bar('bar_end_b', x, '-.36', '.12', barcol(2.2))
for i in range(5):
    cx = "math.sin(%s*%.2f+%.2f)*.44*%s" % (T, .35 + .11 * i, i * 1.7, DW); cy = "math.cos(%s*%.2f+%.2f)*.33*%s" % (T, .27 + .09 * i, i * 2.3, DH)
    r = '%.3f*%s' % (.11 + .025 * i, DH)
    def circ(name, inp, rad, **kw):
        o = mk(d, td.circleTOP, name, [inp], radiusunit='pixels', centerunit='pixels', radiusx='=' + rad, radiusy='=' + rad,
               centerx='=' + cx, centery='=' + cy, bgalpha=0, borderwidth=0, format='rgba16float', **kw); dres(o); return o
    x = circ('disc%d' % i, x, r, fillalpha=1, softness=0, fillcolorr=disc_col(i, 0), fillcolorg=disc_col(i, 1), fillcolorb=disc_col(i, 2))
    x = circ('core%d' % i, x, r + '*.8', fillalpha=1, softnessunit='pixels', softness='=' + r + '*.8', softnesstype='halfcosine', operand='add',
             fillcolorr=2.4, fillcolorg=2.1, fillcolorb=1.6)
o = d.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(x); o.par.label = 'demo source'
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(src); src.par.format = 'rgba16float'

# ------------------------------------------------------------------ time-displacement map
i2 = c.create(td.inTOP, 'in2')
defmap = ramp_from(c, 'defmap', [(0, 0, 0, 0, 1), (1, 1, 1, 1, 1)], w=64, h=64)   # unconnected in2: horizontal ramp
mp = mk(c, td.switchTOP, 'map_in2', [defmap, i2], index="=1 if parent().inputConnectors[1].connections else 0", format='rgba16float'); setres(mp)
m_luma = mk(c, td.monochromeTOP, 'in2_luma', [mp], format='rgba16float')
MW, MH = 64, 36    # the map is smooth, so it lives at a small fixed size (the Time Machine samples it per pixel)
def small(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw = 256; o.par.resolutionh = 256
    return o
# the scroll: a triangle-wave profile slides back and forth with Speed (seamless). For the two gradients the profile is built straight into the
# Ramp TOP (periodic keys, animated Phase); for the other maps a Lookup TOP applies the same sliding triangle Ramp to the map's value.
SPD = "(%sSpeed*absTime.seconds*(1 if %sDirection.menuIndex==0 else -1))" % (P, P)
tri_keys = [(0, 1, 1, 1, 1), (0.5, 0, 0, 0, 1), (1, 1, 1, 1, 1)]
m_h = small(ramp_from(c, 'map_horizontal', tri_keys, w=256, h=256, typ='horizontal', period=2.0, phase='=-%s' % SPD, extendleft='repeat', extendright='repeat'))
m_v = small(ramp_from(c, 'map_vertical', tri_keys, w=256, h=256, typ='vertical', period=2.0, phase='=-%s' % SPD, extendleft='repeat', extendright='repeat'))
# radial: a soft Circle TOP is 1 in the centre and 0 on its rim; invert it so d = 0 centre .. 1 corner
rad = mk(c, td.circleTOP, 'map_radial_disc', radiusunit='pixels', radiusx=128 * 1.4142, radiusy=128 * 1.4142, softnessunit='pixels', softness=128 * 1.4142,
         softnesstype='linear', fillalpha=1, bgalpha=0, borderwidth=0, format='rgba16float', outputresolution='custom', resolutionw=256, resolutionh=256, rotate=0)
m_r = mk(c, td.mathTOP, 'map_radial', [rad], gain=-1.0, postoff=1.0, format='rgba16float')
nz = mk(c, td.noiseTOP, 'map_noise_src', type='simplex3d', period=0.45, harmon=2, mono=True, amp=0.5, offset=0.5, tz='=absTime.seconds*0.4',
        format='rgba16float', outputresolution='custom', resolutionw=256, resolutionh=256)
m_n = mk(c, td.mathTOP, 'map_noise', [nz], gain=1.6, postoff=-0.32, format='rgba16float')
others = mk(c, td.switchTOP, 'map_other', [m_r, m_n, m_luma], index='=max(0,%sMode.menuIndex-2)' % P, format='rgba16float')
tri = ramp_from(c, 'triangle_wave', tri_keys, w=1024, h=1, period=2.0, phase='=-%s' % SPD, extendleft='repeat', extendright='repeat')
scroll = mk(c, td.lookupTOP, 'scroll', [others, tri], channel='luminance', darkuv1='=0.5/1024', lightuv1='=1-0.5/1024', format='rgba16float')
maps = mk(c, td.switchTOP, 'map_mode', [m_h, m_v, scroll], index='=min(2,%sMode.menuIndex)' % P, format='rgba16float')

# ------------------------------------------------------------------ frame history + Time Machine
bi = c.create(td.nullTOP, 'bufin'); bi.inputConnectors[0].connect(src)
bi.par.outputresolution = 'custom'
bi.par.resolutionw.expr = 'int(parent().par.Resolutionw*parent().par.Bufferscale)'
bi.par.resolutionh.expr = 'int(parent().par.Resolutionh*parent().par.Bufferscale)'
bi.par.format = 'rgba8fixed'
t3 = c.create(td.texture3dTOP, 'ring'); t3.inputConnectors[0].connect(bi)
t3.par.cachesize.expr = 'parent().par.Buffersize'
t3.par.active.expr = 'parent().par.Active'   # rolling cache: newest cook = last slice
t3.par.prefill.expr = 'parent().par.Reset or parent().time.frame < 5'   # fill the history with the first frames so there are no black slices
FR = "min(%sFrames*(1+%s), %sBuffersize-2)" % (P, '0.7*' + "parent().op('mod')['band1'].eval()", P)
tm = c.create(td.timemachineTOP, 'time_machine'); tm.inputConnectors[0].connect(t3); tm.inputConnectors[1].connect(maps)
tm.par.blackoffsetunit = 'indices'; tm.par.whiteoffsetunit = 'indices'
tm.par.blackoffset.expr = "(0 if %sDirection.menuIndex==0 else -%s)" % (P, FR)   # forward: map value 0 = now ...
tm.par.whiteoffset.expr = "(-%s if %sDirection.menuIndex==0 else 0)" % (FR, P)   # ... map value 1 = Frames back in time (reverse swaps them)
tm.par.filtertype.expr = "'linear' if %sSmooth else 'nearest'" % P
tm.par.format = 'rgba16float'
setres(tm)
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(tm)
v3_finish(c, COMP, mod=())
report(c)
