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

def _nd_demo(demo):
    """Preview source from native TOPs: a rotating bar and five drifting discs with bright cores, on a dark ground.
    Look = Mono swaps the palette to bone-white greys, and Accent turns one disc and the bar red."""
    import math
    W, H, T = "parent(2).par.Resolutionw", "parent(2).par.Resolutionh", "absTime.seconds"
    A = "(%s)/(%s)" % (W, H)
    M = "(parent(2).par.Look.menuIndex)"; ACC = "(parent(2).par.Accent)"
    hsv = lambda h, s_, v: [v * (1 - s_ + s_ * max(0.0, min(1.0, abs(((h + k) % 1.0) * 6 - 3) - 1))) for k in (0.0, 2 / 3.0, 1 / 3.0)]
    lay = [nd_const(demo, 'ground', W, H, (0.0, 0.0, 0.0), alpha=0)]
    lay[0].par.colorr.expr = "0.16*(1-%s)+0.01*%s" % (M, M); lay[0].par.colorg.expr = lay[0].par.colorr.expr; lay[0].par.colorb.expr = lay[0].par.colorr.expr
    bar_col = [nd_pick(hsv(0.55, 0.7, 1.0), (0.86, 0.84, 0.8), M)[k] for k in range(3)]
    bar_col = ['=(%s)*(1-%s*%s)+%s*%s*%f' % (bar_col[k][1:], M, ACC, M, ACC, (1.0, 0.04, 0.04)[k]) for k in range(3)]
    lay.append(nd_rect(demo, 'bar', W, H, 0, -0.18, 0.84, 0.06, bar_col, rot="=-%s*0.7*57.2958" % T, soft=0.002))
    for i in range(5):
        cx = "=%s*math.sin(%s*(0.35+0.11*%d)+%d*1.7)*0.44" % (A, T, i, i); cy = "=0.33*math.cos(%s*(0.27+0.09*%d)+%d*2.3)" % (T, i, i)
        r = 0.11 + 0.025 * i
        col = hsv(0.12 * i, 0.85, 0.7); mono = [0.7 * (0.35 + 0.65 * ((0.12 * i * 3) % 1.0)) * k for k in (0.96, 0.94, 0.89)]
        dc = nd_pick(col, mono, M)
        if i == 2: dc = ['=(%s)*(1-%s*%s)+%s*%s*%f' % (dc[k][1:], M, ACC, M, ACC, (1.0, 0.04, 0.04)[k]) for k in range(3)]
        lay.append(nd_circle(demo, 'disc%d' % i, W, H, cx, cy, r, dc, soft=0.004))
        lay.append(nd_circle(demo, 'core%d' % i, W, H, cx, cy, r * 0.45, (2.5, 2.2, 1.7), soft=r * 0.4, alpha=0.8))
    return nd_over(demo, 'comp', W, H, lay)

def demo_src(c, comp, fn='src.glsl', bg=1.0, vecs=None, fmt='rgba16float'):
    """in1 + gated `demo` COMP (preview-only source) -> Switch TOP 'src'.
    The switch picks the demo only while in1 is unconnected, so the demo does not cook otherwise."""
    i = c.create(td.inTOP, 'in1')
    d = c.create(td.baseCOMP, 'demo')
    d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
    g = _nd_demo(d)
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
COMP = 'TOP_halftone'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('halftone', 'Halftone'), ('dither', 'Dither'), ('ascii', 'ASCII')], 0),
    ('Halftonetype', 'menu', [('cmyk', 'CMYK'), ('mono', 'Mono')], 0),
    ('Dithertype', 'menu', [('bayer2', 'Bayer 2x2'), ('bayer4', 'Bayer 4x4'), ('bayer8', 'Bayer 8x8'),
                           ('blue', 'Blue noise (interleaved gradient)'), ('diffusion', 'Pseudo error diffusion (R2)')], 1),
    ('Cellsize', 'float', 12, 2, 64),
    ('Angle', 'float', 15, -90, 90),
    ('Softness', 'float', 0.3, 0.02, 1),
    ('Levels', 'int', 3, 2, 16),
    ('Dithermono', 'toggle', 0),
    ('Keepcolor', 'toggle', 0),
    ('Invert', 'toggle', 0),
    ('Ramp', 'str', ' .:-=+*#%@'),
    ('Ink', 'rgb', (0.05, 0.05, 0.08)),
    ('Paper', 'rgb', (0.96, 0.94, 0.88)),
    ('Mix', 'float', 1.0, 0, 1, True),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
look_pg(c)
src = demo_src(c, COMP, bg=1.0)
glyphs = []
for i in range(10):
    t = c.create(td.textTOP, 'glyph%d' % i)
    t.par.outputresolution = 'custom'; t.par.resolutionw = 32; t.par.resolutionh = 32
    t.par.text.expr = "(parent().par.Ramp.eval()+' '*10)[%d]" % i
    t.par.font = 'Menlo'
    t.par.fontautosize = 'off'; t.par.fontsizex = 26
    t.par.alignx = 'center'; t.par.aligny = 'center'
    t.par.fontcolorr = t.par.fontcolorg = t.par.fontcolorb = 1
    t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0; t.par.bgalpha = 1
    glyphs.append(t)
at = glsl(c, 'atlas', rd(COMP, 'atlas.glsl'), inputs=glyphs, fmt='rgba8fixed')
at.par.outputresolution = 'custom'; at.par.resolutionw = 320; at.par.resolutionh = 32
at.par.inputfiltertype = 'nearest' if 'nearest' in at.par.inputfiltertype.menuNames else at.par.inputfiltertype.val
st = glsl(c, 'style', rd(COMP, 'style.glsl'), inputs=[src, at], res=True, fmt='rgba16float', vecs=[
    ('uA', ['parent().par.Mode.menuIndex', "parent().par.Halftonetype.menuIndex if parent().par.Mode.menuIndex==0 else parent().par.Dithertype.menuIndex", 'parent().par.Cellsize', 'parent().par.Angle*0.0174533']),
    ('uB', ['parent().par.Softness', 'parent().par.Levels', 'parent().par.Keepcolor', 'parent().par.Mix']),
    ('uC', ['parent().par.Inkr', 'parent().par.Inkg', 'parent().par.Inkb', 'parent().par.Invert']),
    ('uD', ['parent().par.Paperr', 'parent().par.Paperg', 'parent().par.Paperb', 'parent().par.Dithermono']),
])
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(st)
v3_finish(c, COMP, mod=[('Cellsize','({v}*(1+{b1}*0.8))'),('Angle','({v}+{beat}*20)')], selfmix=True)
report(c)
