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
        for g in c.findChildren():
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
import colorsys
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

ASP = "(parent().par.Resolutionw/parent().par.Resolutionh)"
RATE = "project.cookRate"

# ---------------------------------------------------------------- demo source (native)
def hsv_rgb(h, s, v): return colorsys.hsv_to_rgb(h % 1.0, s, v)
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
RES_W = 'parent(2).par.Resolutionw'; RES_H = 'parent(2).par.Resolutionh'
def dres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RES_W; o.par.resolutionh.expr = RES_H
    o.par.format = 'rgba16float'
    if hasattr(o.par, 'justifyh'):
        o.par.justifyh = 'center'; o.par.justifyv = 'center'
bgk = d.create(td.tableDAT, 'bg_keys'); bgk.appendRow(['pos', 'r', 'g', 'b', 'a'])
bgk.appendRow([0, 0.03, 0.04, 0.10, 1]); bgk.appendRow([1, 0.12, 0.06, 0.10, 1])
bg = d.create(td.rampTOP, 'bg'); bg.par.type = 'vertical'; bg.par.dat = bgk; dres(bg)
parts = [bg]
for i in range(6):
    r_ = .10 + .03 * i
    col = hsv_rgb(i * 0.17 + 0.05, 1.0, 1.0)
    cx = "math.sin(absTime.seconds*0.21+%r)*0.62*%s" % (i * 1.9, RES_H)
    cy = "math.cos(absTime.seconds*0.17+%r)*0.30*%s" % (i * 2.7, RES_H)
    ds = d.create(td.circleTOP, 'disc%d' % i); dres(ds)
    ds.par.radiusunit = 'pixels'; ds.par.radiusx.expr = ds.par.radiusy.expr = '%r*%s' % (r_, RES_H)
    ds.par.centerunit = 'pixels'; ds.par.centerx.expr = cx; ds.par.centery.expr = cy
    for ch, v in zip('rgb', col): ds.par['fillcolor' + ch] = v * 0.9
    ds.par.fillalpha = 1; ds.par.bgalpha = 0; ds.par.softnessunit = 'pixels'; ds.par.softness.expr = '%r*%s' % (r_ * 0.85, RES_H)
    rg = d.create(td.circleTOP, 'ring%d' % i); dres(rg)
    rg.par.radiusunit = 'pixels'; rg.par.radiusx.expr = rg.par.radiusy.expr = '%r*%s' % (r_ * 1.7, RES_H)
    rg.par.centerunit = 'pixels'; rg.par.centerx.expr = cx; rg.par.centery.expr = cy
    rg.par.fillalpha = 0; rg.par.bgalpha = 0
    for ch, v in zip('rgb', col): rg.par['border' + ch] = v * 0.7
    rg.par.borderalpha = 1; rg.par.borderwidthunit = 'pixels'; rg.par.borderwidth.expr = '0.06*%s' % RES_H
    rg.par.softnessunit = 'pixels'; rg.par.softness.expr = '0.04*%s' % RES_H
    parts += [ds, rg]
scene = d.create(td.compositeTOP, 'scene'); scene.par.operand = 'add'; scene.par.format = 'rgba16float'
for k, s_ in enumerate(parts): scene.inputConnectors[k].connect(s_)
opq = d.create(td.reorderTOP, 'opaque'); opq.inputConnectors[0].connect(scene)
for ch in ('red', 'green', 'blue'): opq.par['output' + ch + 'chan'] = ch
opq.par.outputalphachan = 'one'; opq.par.format = 'rgba16float'
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(opq); do.par.label = 'demo source'
i1 = c.create(td.inTOP, 'in1')
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
setres(src); src.par.format = 'rgba16float'

# ---------------------------------------------------------------- field (GLSL: gradient / curl-noise maths)
field = glsl(c, 'field', rd(COMP, 'field.glsl'), inputs=[src], res=True, vecs=[
    ('uA', [P + 'Fieldmode.menuIndex', P + 'Inputamt', P + 'Turbulence', P + 'Fieldscale']),
    ('uB', ['absTime.seconds*' + P + 'Fieldspeed', ASP, P + 'Smooth', P + 'Rotate*0.0174533']),
])

# ---------------------------------------------------------------- particles (Particle POP, steered by the field)
def mcomb(name, inp, vecs=(), combs=()):
    """Math Combine POP. vecs: (name, type, [values/exprs]); combs: (oper, a, b, c, result)."""
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
        for k, (op_, a, b, cc, res) in enumerate(combs):
            m.par['comb%doper' % k] = op_
            m.par['comb%dscopea' % k] = a
            if b: m.par['comb%dscopeb' % k] = b
            if cc: m.par['comb%dscopec' % k] = cc
            m.par['comb%dresult' % k] = res
    return m

gen = c.create(td.pointgeneratorPOP, 'spawn_points')   # pool of spawn positions inside the image; the Particle POP picks random ones for each birth
gen.par.shape = 'rectangle'; gen.par.sizex = 1; gen.par.sizey = 1; gen.par.tx = 0.5; gen.par.ty = 0.5
gen.par.distribution = 'surface'; gen.par.createpointprim = False
gen.par.numpoints = 65536
loop = c.create(td.nullPOP, 'null_loop')
pp = c.create(td.particlePOP, 'particles'); pp.inputConnectors[0].connect(gen)
pp.par.targetpop = loop
pp.par.maxparticles.expr = P + 'Count'
pp.par.birthrateunit = 'frames'; pp.par.birthrate.expr = '4*%sCount/%sLifetime' % (P, P)   # oversupply: births only fill free slots up to Count
pp.par.lifevariance = 0.5
pp.par.life.expr = P + 'Lifetime'; pp.par.lifeunit = 'frames'
pp.par.play.expr = P + 'Play'
pp.par.speed.expr = '1/(project.cookRate*max(absTime.stepSeconds, 1e-4))'   # one simulation step of 1/cookRate s per cooked frame, whatever the frame time
pp.par.rndinputpts = True
pp.par.createpointprim = False
STEP = '%sStepsize*%sSpeed*%s' % (P, P, RATE)       # field units per second (per frame x frame rate)
# velocity from the field texture: rg = direction*0.5+0.5 -> +-step (x scaled by 1/aspect), z = 0
lk1 = c.create(td.lookuptexturePOP, 'field_to_velocity'); lk1.inputConnectors[0].connect(pp)
lk1.par.top = field
lk1.par.lookupindexattr0 = 'P(0)'; lk1.par.lookupindexattr1 = 'P(1)'
lk1.par.outputattrscope = 'PartVel'; lk1.par.attrnumcomps = 3; lk1.par.channelmask = '7'
for k, hi in enumerate(('%s/%s' % (STEP, ASP), STEP, '0')):
    lk1.par['fromlow%d' % k] = 0; lk1.par['fromhigh%d' % k] = 1
    lk1.par['tolow%d' % k].expr = '-(%s)' % hi; lk1.par['tohigh%d' % k].expr = hi
# speed by field magnitude: sp = mix(1, max(mag, 0.15), Speedbymag); the Lookup Texture range maps the blue channel (index 2)
lk2 = c.create(td.lookuptexturePOP, 'field_magnitude'); lk2.inputConnectors[0].connect(lk1)
lk2.par.top = field
lk2.par.lookupindexattr0 = 'P(0)'; lk2.par.lookupindexattr1 = 'P(1)'
lk2.par.channelmask = '4'
lk2.par.outputattrscope = 'FieldMag'; lk2.par.attrnumcomps = 1
lk2.par.fromlow2 = 0.15; lk2.par.fromhigh2 = 1
lk2.par.tolow2.expr = '1-%sSpeedbymag*0.85' % P; lk2.par.tohigh2 = 1
# velocity *= sp (floored: the magnitude is clamped to >= 0.15);  particles that left the picture are aged out so they respawn
spd = mcomb('speed_and_bounds', lk2,
    vecs=[('spfloor', 'float', ['1-%sSpeedbymag*0.85' % P]), ('zero3', 'float3', [0, 0, 0]), ('one3', 'float3', [1, 1, 1]), ('big', 'float', [1000000.0])],
    combs=[('max', 'FieldMag', 'spfloor', '', 'Sp'),
           ('mult', 'PartVel', 'Sp', '', 'PartVel'),
           ('clamp', 'P', 'zero3', 'one3', 'Pin'),
           ('ne', 'P', 'Pin', '', 'Outv'),
           ('compmax', 'Outv', '', '', 'Out'),
           ('aaddbmultc', 'PartAge', 'big', 'Out', 'PartAge')])
loop.inputConnectors[0].connect(spd)

# ---------------------------------------------------------------- stroke geometry: one instanced quad per particle (Math Combine POP derives the instance data)
th = '%sLinewidth/%s' % (P, 'parent().par.Resolutionh')
trT = '%sTrail/%s' % (P, RATE)
prep = mcomb('stroke_transform', loop,
    vecs=[('aspv', 'float3', [ASP, 1, 0]), ('cen', 'float3', [0.5, 0.5, 0]), ('trT', 'float', [trT]),
          ('htT', 'float', [trT + '*0.5']), ('thick', 'float', [th]), ('lo', 'float', [0.0]), ('hi', 'float', [0.12]),
          ('lo2', 'float', [1.0]), ('hi2', 'float', [0.8]), ('minlife', 'float', [1e-4]), ('ex', 'float3', [1, 0, 0]), ('ey', 'float3', [0, 1, 0]), ('ez', 'float3', [0, 0, 1])],
    combs=[('mult', 'PartVel', 'aspv', '', 'Vw'),               # velocity in world units (height = 1)
           ('length', 'Vw', '', '', 'VL'),
           ('mult', 'VL', 'trT', '', 'SegLen'),                 # stroke length = distance travelled in `Trail` frames
           ('add', 'SegLen', 'thick', '', 'Sx'),
           ('atan2', 'Vw(1)', 'Vw(0)', '', 'Ang'),                # stroke direction (degrees)
           ('mult', 'ez', 'Ang', '', 'Rot'),
           ('mult', 'ex', 'Sx', '', 'Scx'),                    # instance scale = (length, thickness, 1)
           ('mult', 'ey', 'thick', '', 'Scy'),
           ('add', 'Scx', 'Scy', '', 'Scxy'),
           ('add', 'Scxy', 'ez', '', 'Sc'),
           ('asubb', 'P', 'cen', '', 'Pc'),
           ('mult', 'Pc', 'aspv', '', 'Pa'),
           ('mult', 'Vw', 'htT', '', 'Back'),
           ('asubb', 'Pa', 'Back', '', 'Pw'),                   # stroke centre = half a stroke behind the particle
           ('max', 'PartLifeSpan', 'minlife', '', 'LifeSafe'),
           ('adivb', 'PartAge', 'LifeSafe', '', 'AgeFrac'),
           ('smoothstep', 'lo', 'hi', 'AgeFrac', 'FadeIn'),
           ('smoothstep', 'lo2', 'hi2', 'AgeFrac', 'FadeOut'),
           ('mult', 'FadeIn', 'FadeOut', '', 'AgeFade')])

prep.par.angleunit = 'deg'

# ---- colour: one texture per Colormode, looked up at the particle (image / direction / line by position, age by age)
satsrc = c.create(td.hsvadjustTOP, 'image_saturation'); satsrc.inputConnectors[0].connect(src)
satsrc.par.saturationmult.expr = P + 'Saturation'; setres(satsrc); satsrc.par.format = 'rgba16float'
N = 64
pal = c.create(td.tableDAT, 'palette_keys'); pal.appendRow(['pos', 'r', 'g', 'b', 'a'])
import math as _m
for i in range(N + 1):
    t = i / N
    pal.appendRow([t] + [0.5 + 0.5 * _m.cos(6.28318 * (t + o)) for o in (0.0, 0.33, 0.67)] + [1])
ageramp = c.create(td.rampTOP, 'palette_by_age'); ageramp.par.type = 'horizontal'; ageramp.par.dat = pal
ageramp.par.outputresolution = 'custom'; ageramp.par.resolutionw = 256; ageramp.par.resolutionh = 4; ageramp.par.format = 'rgba16float'
wheelramp = c.create(td.rampTOP, 'palette_wheel'); wheelramp.par.type = 'radial'; wheelramp.par.dat = pal
wheelramp.par.phase = 0.5   # hue = angle/2pi + 0.5, as in the direction palette
wheelramp.par.outputresolution = 'custom'; wheelramp.par.resolutionw = 256; wheelramp.par.resolutionh = 256; wheelramp.par.format = 'rgba16float'
dircol = c.create(td.remapTOP, 'palette_by_direction'); dircol.inputConnectors[0].connect(wheelramp); dircol.inputConnectors[1].connect(field)
dircol.par.resolutionsource = 'input2'; dircol.par.horzsource = 'red'; dircol.par.vertsource = 'green'; dircol.par.format = 'rgba16float'
linecol = c.create(td.constantTOP, 'line_colour'); linecol.par.alpha = 1
for ch in 'rgb': linecol.par['color' + ch].expr = P + 'Linecolor' + ch
linecol.par.outputresolution = 'custom'; linecol.par.resolutionw = 4; linecol.par.resolutionh = 4; linecol.par.format = 'rgba16float'
colsw = c.create(td.switchTOP, 'colour_source')
for k, s_ in enumerate((satsrc, dircol, ageramp, linecol)): colsw.inputConnectors[k].connect(s_)
colsw.par.index.expr = P + 'Colormode.menuIndex'
lk3 = c.create(td.lookuptexturePOP, 'colour_from_texture'); lk3.inputConnectors[0].connect(prep)
lk3.par.top = colsw
lk3.par.lookupindexattr0.expr = "'AgeFrac' if %sColormode.menuIndex==2 else 'P(0)'" % P
lk3.par.lookupindexattr1 = 'P(1)'
lk3.par.inputextend0 = 'hold'; lk3.par.inputextend1 = 'hold'
lk3.par.outputattrscope = 'Color'; lk3.par.attrtype = 'color'; lk3.par.attrnumcomps = 4
tint = mcomb('colour_fade', lk3, combs=[('mult', 'Color.rgb', 'AgeFade', '', 'Color.rgb')])
sel_ = c.create(td.nullPOP, 'strokes'); sel_.inputConnectors[0].connect(tint)

# ---------------------------------------------------------------- render the strokes (Geometry COMP instancing the POP -> Render TOP)
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
bx = geo.create(td.boxSOP, 'seg'); bx.par.sizex = 1; bx.par.sizey = 1; bx.par.sizez = 0.001
bx.display = True; bx.render = True
mat = c.create(td.constantMAT, 'mat')
geo.par.material = mat
geo.par.instancing = True; geo.par.instancecountmode = 'oplength'
geo.par.instanceop = sel_
geo.par.instancetx = 'Pw(0)'; geo.par.instancety = 'Pw(1)'; geo.par.instancetz = 'Pw(2)'
geo.par.instancer = 'Color(0)'; geo.par.instanceg = 'Color(1)'; geo.par.instanceb = 'Color(2)'; geo.par.instancea = 'Color(3)'
geo.par.instancerx = 'Rot(0)'; geo.par.instancery = 'Rot(1)'; geo.par.instancerz = 'Rot(2)'
geo.par.instancesx = 'Sc(0)'; geo.par.instancesy = 'Sc(1)'; geo.par.instancesz = 'Sc(2)'
cam = c.create(td.cameraCOMP, 'cam'); cam.par.projection = 'ortho'; cam.par.tz = 5
cam.par.orthowidth.expr = ASP
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = ''
setres(rt); rt.par.bgcolora = 0; rt.par.antialias = 'aa2'; rt.par.format = 'rgba16float'

# ---------------------------------------------------------------- long-exposure accumulation (feedback): acc = acc*Fade + strokes
# ---------------------------------------------------------------- accumulation and composite stay GLSL (see README: a native version measured >40 % slower)
za = c.create(td.constantTOP, 'zero_accum'); za.par.colorr = za.par.colorg = za.par.colorb = 0; za.par.alpha = 1; za.par.format = 'rgba32float'; setres(za)
fba = c.create(td.feedbackTOP, 'fb_accum'); fba.inputConnectors[0].connect(za); fba.par.format = 'rgba32float'; setres(fba)
ac = glsl(c, 'accum', rd(COMP, 'accum.glsl'), inputs=[fba, rt], fmt='rgba32float', res=True, vecs=[
    ('uA', [P + 'Fade', P + 'Play', P + 'Intensity', 0]),
])
fba.par.top = ac

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
