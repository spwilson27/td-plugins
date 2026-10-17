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
    sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"   # in1.width: re-evaluate when a TOP is plugged in
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
        setres(x, _RW, _RH)
        res = x
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(res); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "(1 if (parent().par.Bypass and len(parent().inputConnectors[0].connections)) else 0) + 0*absTime.frame"
    o1.inputConnectors[0].connect(bp)
    o1.comment = 'result'
    for k, v in (outlabels or {}).items(): c.op(k).comment = v
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)
# ---- end helpers ----
COMP = 'TOP_flow_field_lines'
c = new_comp(COMP)
P = 'parent().par.'
add_pars(c, [
    ('Play', 'toggle', 1),
    ('Reset', 'pulse'),
    ('Speed', 'float', 1.0, 0, 4),
    ('Compose', 'menu', [('over', 'Strokes over input'), ('add', 'Add to input'), ('bg', 'On background')], 0),
    ('Inputdim', 'float', 0.3, 0, 1),
    ('Bgcolor', 'rgb', (0.01, 0.01, 0.02)),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
add_pars(c, [
    ('Fieldmode', 'menu', [('contour', 'Along edges (perp. to gradient)'), ('gradient', 'Along luminance gradient'), ('luma', 'Angle from luminance'), ('hue', 'Angle from hue')], 0),
    ('Inputamt', 'float', 1.0, 0, 4),
    ('Smooth', 'float', 2.0, 0.5, 16),
    ('Rotate', 'float', 0.0, -180, 180),
    ('Fieldscale', 'float', 1.2, 0.1, 8),
    ('Fieldspeed', 'float', 0.08, 0, 2),
    ('Turbulence', 'float', 0.4, 0, 2),
    ('Speedbymag', 'float', 0.5, 0, 1),
], page='Field')
add_pars(c, [
    ('Count', 'int', 40000, 100, 262144),
    ('Stepsize', 'float', 0.004, 0.0005, 0.03),
    ('Lifetime', 'float', 240, 10, 2000),
    ('Linewidth', 'float', 1.3, 0.5, 8),
    ('Trail', 'float', 2.5, 0.5, 20),
    ('Intensity', 'float', 0.6, 0, 3),
    ('Exposure', 'float', 1.6, 0.1, 8),
    ('Fade', 'float', 0.985, 0.8, 0.9995),
    ('Colormode', 'menu', [('image', 'Input image'), ('direction', 'Palette by direction'), ('age', 'Palette by age'), ('line', 'Line colour')], 0),
    ('Saturation', 'float', 1.4, 0, 3),
    ('Linecolor', 'rgb', (0.9, 0.7, 0.35)),
], page='Strokes')

# ---- input + gated demo ----
i = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
dg = glsl(d, 'pattern', rd(COMP, 'demo.glsl'), vecs=[('uT', ['absTime.seconds', 'parent(2).par.Resolutionw/parent(2).par.Resolutionh', 0, 0])])
setres(dg, 'parent(2).par.Resolutionw', 'parent(2).par.Resolutionh')
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(dg); do.par.label = 'demo source'
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
setres(src); src.par.format = 'rgba16float'

ASP = "(parent().par.Resolutionw/parent().par.Resolutionh)"
STEP = P + "Stepsize*" + P + "Speed"
side = "int(math.ceil(math.sqrt(max(1,%sCount))))" % P
def sq(g):
    g.par.outputresolution = 'custom'; g.par.resolutionw.expr = side; g.par.resolutionh.expr = side

# ---- field ----
field = glsl(c, 'field', rd(COMP, 'field.glsl'), inputs=[src], res=True, vecs=[
    ('uA', [P + 'Fieldmode.menuIndex', P + 'Inputamt', P + 'Turbulence', P + 'Fieldscale']),
    ('uB', ['absTime.seconds*' + P + 'Fieldspeed', ASP, P + 'Smooth', P + 'Rotate*0.0174533']),
])

# ---- particle state (feedback) ----
common = rd(COMP, 'common.glsl')
zs = c.create(td.constantTOP, 'zero_state'); zs.par.colorr = zs.par.colorg = zs.par.colorb = 0; zs.par.alpha = 0; zs.par.format = 'rgba32float'; sq(zs)
fbs = c.create(td.feedbackTOP, 'fb_state'); fbs.inputConnectors[0].connect(zs); fbs.par.format = 'rgba32float'; sq(fbs)
st = glsl(c, 'state', common + rd(COMP, 'state.glsl'), inputs=[fbs, field], fmt='rgba32float', vecs=[
    ('uA', [STEP, P + 'Speedbymag', ASP, 'absTime.frame']),
    ('uB', [P + 'Play', P + 'Lifetime', 0, 0]),
]); sq(st)
fbs.par.top = st

# ---- instance data ----
G = {}
for k, nm in enumerate(['inst_t', 'inst_r', 'inst_s', 'inst_c']):
    g = glsl(c, nm, common + rd(COMP, 'inst.glsl'), inputs=[st, field, src], fmt='rgba32float', vecs=[
        ('uA', [STEP, P + 'Speedbymag', ASP, P + 'Trail']),
        ('uB', [P + 'Linewidth/' + P + 'Resolutionh', P + 'Colormode.menuIndex', P + 'Saturation', k]),
        ('uC', [P + 'Linecolorr', P + 'Linecolorg', P + 'Linecolorb', 0]),
    ]); sq(g)
    G[nm] = g
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
bx = geo.create(td.boxSOP, 'seg'); bx.par.sizex = 1; bx.par.sizey = 1; bx.par.sizez = 0.001
bx.display = True; bx.render = True
mat = c.create(td.constantMAT, 'mat'); mat.par.applypointcolor = True
geo.par.material = mat
geo.par.instancing = True; geo.par.instancecountmode = 'oplength'
geo.par.instanceop = G['inst_t']; geo.par.instancetop = G['inst_t']
geo.par.instancetx = 'r'; geo.par.instancety = 'g'; geo.par.instancetz = 'b'
geo.par.instancerop = G['inst_r']; geo.par.instancerx = 'r'; geo.par.instancery = 'g'; geo.par.instancerz = 'b'
geo.par.instancesop = G['inst_s']; geo.par.instancesx = 'r'; geo.par.instancesy = 'g'; geo.par.instancesz = 'b'
geo.par.instancecolorop = G['inst_c']; geo.par.instancer = 'r'; geo.par.instanceg = 'g'; geo.par.instanceb = 'b'
cam = c.create(td.cameraCOMP, 'cam'); cam.par.projection = 'ortho'; cam.par.tz = 5
cam.par.orthowidth.expr = ASP
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = ''
setres(rt); rt.par.bgcolora = 0; rt.par.antialias = 'aa2'; rt.par.format = 'rgba16float'

# ---- long-exposure accumulation (feedback) ----
za = c.create(td.constantTOP, 'zero_accum'); za.par.colorr = za.par.colorg = za.par.colorb = 0; za.par.alpha = 1; za.par.format = 'rgba32float'; setres(za)
fba = c.create(td.feedbackTOP, 'fb_accum'); fba.inputConnectors[0].connect(za); fba.par.format = 'rgba32float'; setres(fba)
ac = glsl(c, 'accum', rd(COMP, 'accum.glsl'), inputs=[fba, rt], fmt='rgba32float', res=True, vecs=[
    ('uA', [P + 'Fade', P + 'Play', P + 'Intensity', 0]),
])
fba.par.top = ac

# ---- composite ----
fin = glsl(c, 'final', rd(COMP, 'final.glsl'), inputs=[ac, src], res=True, vecs=[
    ('uA', [P + 'Exposure', P + 'Compose.menuIndex', P + 'Inputdim', 0]),
])
fin.par.color0name = 'uBg'
fin.par.color0rgbr.expr = P + 'Bgcolorr'; fin.par.color0rgbg.expr = P + 'Bgcolorg'; fin.par.color0rgbb.expr = P + 'Bgcolorb'
o1 = c.create(td.outTOP, 'out1'); o1.inputConnectors[0].connect(fin)
o2 = c.create(td.outTOP, 'out2'); o2.inputConnectors[0].connect(field)

pe = c.create(td.parameterexecuteDAT, 'pexec'); pe.text = rd(COMP, 'pexec.py')
pe.par.op = c; pe.par.pars = 'Reset'; pe.par.valuechange = False; pe.par.onpulse = True; pe.par.executeloc = 'op'

v3_finish(c, COMP, mod=[
    ('Speed', '({v}*(1+{b1}))'),
    ('Turbulence', '({v}+{b2}*0.6)'),
    ('Intensity', '({v}*(1+{b3}*2))'),
    ('Linewidth', '({v}*(1+{b4}))'),
    ('Rotate', '({v}+{beat}*60)'),
])
report(c)
