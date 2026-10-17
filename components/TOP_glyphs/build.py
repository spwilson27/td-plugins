# ---- v3 helpers (self-contained; copy into each build.py) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
COMP = 'TOP_glyphs'

def rd(comp, fn): return open(os.path.join(ROOT, 'components', comp, fn)).read()
def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)
def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

# resolution of the effect: follows in1 when connected and Resolutionmode == input, else custom
RW = "((0*absTime.frame)+parent().op('in1').width if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionw)"
RH = "((0*absTime.frame)+parent().op('in1').height if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionh)"
CONN = "(len(parent().inputConnectors[0].connections) + 0*absTime.frame)"
def setres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RW; o.par.resolutionh.expr = RH
def CH(n): return "parent().op('mod')['%s'].eval()" % n

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=True):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    return g

def add_pars(c, specs, page='Controls'):
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse': pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]; p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            for q, v in zip(pg.appendWH(n), s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'rgb':
            for q, v in zip(pg.appendRGB(n), s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def std_top_pars(c):
    """Mix / Bypass / Resolutionmode / Resolution on the Controls page (call after the component pars)."""
    pg = [p for p in c.customPages if p.name == 'Controls'][0]
    p = pg.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    pg.appendToggle('Bypass')
    p = pg.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    for q, v in zip(pg.appendWH('Resolution'), (1280, 720)):
        q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
    c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"

def mod_chop(c, name):
    """optional modulation In CHOP (band1..4, beat) merged over zeros so every channel always exists"""
    im = c.create(td.inCHOP, name)
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im); mg.inputConnectors[1].connect(mz)
    mg.par.duplicate = 'first'; mg.par.align = 'start'
    return mg

def demo_switch(c, demo_out, name='src', in1='in1'):
    """Switch TOP: index 0 = demo (gated), 1 = in1. Index is 1 when in1 is connected."""
    sw = c.create(td.switchTOP, name)
    sw.inputConnectors[0].connect(demo_out); sw.inputConnectors[1].connect(c.op(in1))
    sw.par.index.expr = "1 if %s else 0" % CONN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

def mix_bypass(c, dry, wet, out_name='out1'):
    x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(dry); x.inputConnectors[1].connect(wet)
    x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'; x.par.outputresolution = 'useinput'
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(x); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "1 if (parent().par.Bypass and %s) else 0" % CONN
    o = c.create(td.outTOP, out_name); o.inputConnectors[0].connect(bp)
    return o

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
# ---- end helpers ----

c = new_comp(COMP)
add_pars(c, [
    ('Layout', 'menu', [('grid', 'Grid'), ('rain', 'Rain'), ('tunnel', 'Tunnel')], 0),
    ('Charset', 'str', ' .:-=+*#%@'),
    ('Fontname', 'str', 'Menlo'),
    ('Cols', 'int', 100, 16, 300),
    ('Speed', 'float', 1.0, 0, 8),
    ('Contrast', 'float', 1.2, 0.2, 4),
    ('Invert', 'toggle', 0),
    ('Brightness', 'float', 1.6, 0, 5),
    ('Background', 'float', 0.12, 0, 1),
    ('Tail', 'float', 8, 1, 40),
    ('Trailfloor', 'float', 0.18, 0, 1),
    ('Twist', 'float', 0.0, -2, 2),
    ('Seed', 'int', 1, 0, 999),
])
std_top_pars(c)
add_pars(c, [
    ('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
    ('Accent', 'float', 0.0, 0, 1),
], page='Look')

i1 = c.create(td.inTOP, 'in1')
mod_chop(c, 'in2')

# ---- demo (preview only): gated off by the Switch whenever in1 is connected
demo = c.create(td.baseCOMP, 'demo')
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
def nd_const(d, name, W, H, col):
    o = d.create(td.constantTOP, name); nd_res(o, W, H)
    return nd_set(o, colorr=col[0], colorg=col[1], colorb=col[2], alpha=1)
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

def _nd_demo(demo):
    import math
    W, H, T = 1280, 720, "absTime.seconds"
    sky = nd_ramp(demo, 'sky', W, H, [(0.0, (0.08, 0.10, 0.20)), (1.0, (0.45, 0.60, 0.85))])
    lay = [sky]
    for i in range(3):   # three drifting shaded balls (dark disc + soft highlight toward the light)
        r = 0.2 + 0.05 * i
        cx = "=0.45*math.sin(%s*0.4+%d*2.1)" % (T, i); cy = "=0.2*math.cos(%s*0.5+%d*1.7)" % (T, i)
        base = [0.5 + 0.5 * math.cos(k + i * 1.9 + 1.0) for k in (0.0, 2.1, 4.2)]
        lay.append(nd_circle(demo, 'ball%d' % i, W, H, cx, cy, r, [b * 0.4 for b in base], soft=0.006))
        hx = "=0.45*math.sin(%s*0.4+%d*2.1)-%f" % (T, i, 0.3 * r); hy = "=0.2*math.cos(%s*0.5+%d*1.7)+%f" % (T, i, 0.4 * r)
        lay.append(nd_circle(demo, 'shine%d' % i, W, H, hx, hy, 0.55 * r, [min(b * 1.1, 1.0) for b in base], soft=0.5 * r, alpha=0.9))
    lay.append(nd_rect(demo, 'wave', W, H, 0, "=-0.3+0.05*math.sin(%s)" % T, 1.9, 0.012, (0.35, 0.28, 0.18), rot="=2*math.sin(%s*0.7)" % T))
    return nd_over(demo, 'comp', W, H, lay)
dg = _nd_demo(demo)
do = demo.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(dg)
src = demo_switch(c, demo.outputConnectors[0], 'src')

# ---- glyph atlas: Charset laid out left to right, one 64x128 slot per character
NEXP = "max(len(parent().par.Charset.eval()),1)"
at = c.create(td.textTOP, 'atlas')
at.par.text.expr = 'parent().par.Charset'
at.par.font.expr = 'parent().par.Fontname'
at.par.fontautosize = 'nofit'
at.par.fontsizexunit = 'pixels'; at.par.fontsizeyunit = 'pixels'
at.par.fontsizex = 106
at.par.outputresolution = 'custom'; at.par.resolutionw.expr = "min(%s*64, 16000)" % NEXP; at.par.resolutionh = 128
at.par.fontcolorr = at.par.fontcolorg = at.par.fontcolorb = 1
at.par.bgcolorr = at.par.bgcolorg = at.par.bgcolorb = 0; at.par.bgalpha = 1
at.par.alignx = 'center'; at.par.aligny = 'center'
at.par.format = 'rgba8fixed'

P = 'parent().par.'
common = [
    ('uA', [NEXP, P + 'Layout.menuIndex', P + 'Cols', 'absTime.seconds*' + P + 'Speed']),
    ('uB', [P + 'Contrast+0.6*' + CH('band1'), P + 'Invert', P + 'Brightness*(1+0.6*' + CH('band2') + ')', P + 'Background']),
    ('uC', [P + 'Tail*(1+' + CH('band3') + ')', P + 'Trailfloor', P + 'Twist', P + 'Seed']),
]
gl = glsl(c, 'glyphs', rd(COMP, 'glyphs.glsl'), inputs=[src, at], vecs=common + [
    ('uD', [P + 'Look.menuIndex', P + 'Accent', 0, CH('beat')])])
fld = glsl(c, 'field', rd(COMP, 'glyphs.glsl'), inputs=[src, at], vecs=common + [
    ('uD', [P + 'Look.menuIndex', P + 'Accent', 1, CH('beat')])], fmt='rgba16float')
o1 = mix_bypass(c, src, gl)
o2 = c.create(td.outTOP, 'out2'); o2.inputConnectors[0].connect(fld)
finish(c, COMP)
report(c)
