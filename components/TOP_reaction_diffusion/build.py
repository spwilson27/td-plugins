import os, td, math

NAME = 'TOP_reaction_diffusion'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
ROOT = os.path.expanduser('~/software/td-plugins')
def rd(f): return open(os.path.join(HERE, f)).read()

bld = op('/build') or op('/').create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

# simulation / output resolution: follows the image (or the demo image) unless Resolutionmode = custom
RW = "(parent().op('src').width if parent().par.Resolutionmode=='input' else parent().par.Resolutionw)"
RH = "(parent().op('src').height if parent().par.Resolutionmode=='input' else parent().par.Resolutionh)"
CH = lambda n: "parent().op('mod')['%s'].eval()" % n

def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t

def glsl(name, dat, fmt='rgba32float', inputs=(), vecs=(), passes=None, parent_=None):
    g = (parent_ or c).create(td.glslTOP, name)
    g.par.pixeldat = dat
    g.par.format = fmt
    g.par.outputresolution = 'custom'
    g.par.resolutionw.expr = RW
    g.par.resolutionh.expr = RH
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = str(e)
    if passes: g.par.npasses.expr = passes
    return g

def fpar(page, name, label, default, lo, hi, nlo=None, nhi=None, clamp=False):
    q = page.appendFloat(name, label=label)[0]
    q.min = lo; q.max = hi; q.normMin = lo if nlo is None else nlo; q.normMax = hi if nhi is None else nhi
    q.default = default; q.val = default
    if clamp: q.clampMin = q.clampMax = True
    return q

# ---------- parameters ----------
p = c.appendCustomPage('Controls')
fpar(p, 'Mix', 'Mix', 1.0, 0, 1, clamp=True)
p.appendToggle('Bypass', label='Bypass')
m = p.appendMenu('Resolutionmode', label='Resolution Mode')[0]
m.menuNames = ['input', 'custom']; m.menuLabels = ['Follow input', 'Custom']; m.default = 'input'; m.val = 'input'
q = p.appendWH('Resolution', label='Resolution')
for x, d in zip(q, (1280, 720)):
    x.default = d; x.val = d; x.min = 16; x.max = 8192; x.normMin = 16; x.normMax = 4096; x.clampMin = True
m = p.appendMenu('Preset', label='Preset')[0]
names = ['custom', 'coral', 'mitosis', 'labyrinth', 'spots', 'worms']
m.menuNames = names; m.menuLabels = [n.capitalize() for n in names]; m.default = 'coral'; m.val = 'coral'
fpar(p, 'Feed', 'Feed', 0.0545, 0, 0.1, 0.01, 0.09)
fpar(p, 'Kill', 'Kill', 0.062, 0, 0.1, 0.04, 0.08)
q = p.appendInt('Steps', label='Steps'); q = q[0]; q.min = 1; q.max = 100; q.normMin = 1; q.normMax = 40; q.default = 16; q.val = 16
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')

p = c.appendCustomPage('Drive')
fpar(p, 'Feedmod', 'Feed Influence', 2.0, -3, 3)
fpar(p, 'Killmod', 'Kill Influence', 1.0, -3, 3)
fpar(p, 'Inject', 'Continuous Injection', 0.0, 0, 1, 0, 0.3)
fpar(p, 'Seedamount', 'Reset Seed Amount', 1.0, 0, 1, clamp=True)
fpar(p, 'Seedthreshold', 'Seed Threshold', 0.4, 0, 1, clamp=True)
p.appendToggle('Invert', label='Invert (Dark Drives)')
fpar(p, 'Sprinkle', 'Random Blobs', 0.7, 0, 1, clamp=True)

p = c.appendCustomPage('Render')
m = p.appendMenu('Colormode', label='Colour Mode')[0]
m.menuNames = ['tint', 'multiply', 'emboss', 'ramp', 'field', 'warp']
m.menuLabels = ['Tint', 'Multiply', 'Emboss', 'Pattern ramp', 'Field (grey)', 'Warp']
m.default = 'tint'; m.val = 'tint'
fpar(p, 'Strength', 'Strength', 1.0, 0, 3, 0, 2)
fpar(p, 'Contrast', 'Contrast', 1.7, 0, 8, 0, 6)
fpar(p, 'Bump', 'Bump', 6.0, 0, 30, 0, 20)
defs = {'Color1': (0.02, 0.02, 0.10), 'Color2': (0.05, 0.35, 0.55), 'Color3': (0.95, 0.55, 0.15), 'Color4': (1.0, 0.97, 0.85)}
for n, d in defs.items():
    for par, v in zip(p.appendRGB(n, label=n), d): par.default = v; par.val = v; par.min = 0; par.max = 1

p = c.appendCustomPage('Sim')
fpar(p, 'Diffa', 'Diffusion A', 1.0, 0, 1.2, 0, 1.2)
fpar(p, 'Diffb', 'Diffusion B', 0.5, 0, 1.2, 0, 1.2)
fpar(p, 'Dt', 'Time Step', 1.0, 0.01, 1.5)
q = p.appendInt('Seed', label='Seed')[0]; q.default = 1; q.val = 1; q.min = 0; q.normMax = 100

# ---------- inputs, demo, source switch ----------
inn = c.create(td.inTOP, 'in1')
imod = c.create(td.inCHOP, 'in2')

demo = c.create(td.baseCOMP, 'demo')
demo.comment = 'preview-only test image, not cooked when in1 is connected'
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
    W, H, T = "parent(2).par.Resolutionw", "parent(2).par.Resolutionh", "absTime.seconds"
    lo, hi = (0.35, 0.20, 0.10), (1.0, 0.9, 0.7)
    shade = lambda v: [a + (b - a) * v for a, b in zip(lo, hi)]
    # grey ground with a gentle horizontal swell, soft blobs and a pulsing ring: gives the sim a luminance landscape
    ground = nd_ramp(demo, 'ground', W, H, [(k / 6.0, shade(0.30 + 0.12 * math.sin(((k / 6.0) - 0.5) * 1.7778 * 3.0))) for k in range(7)], kind='horizontal')
    lay = [ground]
    for i in range(4):
        cx = "=0.42*math.sin(%s*0.23+%d*1.9)" % (T, i); cy = "=0.42*math.cos(%s*0.31+%d*2.7)" % (T, i)
        lay.append(nd_circle(demo, 'blob%d' % i, W, H, cx, cy, 0.17 - 0.03 * ((i * 0.37) % 1.0), shade(0.85), soft=0.12 - 0.03 * ((i * 0.37) % 1.0)))
    lay.append(nd_circle(demo, 'ring', W, H, 0, 0, "=0.30+0.05*math.sin(%s*0.5)" % T, shade(0.9), ring=0.015, soft=0.004))
    return nd_over(demo, 'comp', W, H, lay)
dg = _nd_demo(demo)
do = demo.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(dg)

src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(demo.outputConnectors[0])
src.inputConnectors[1].connect(inn)
src.par.index.expr = "1 if len(parent().inputConnectors[0].connections) else 0"
src.par.format = 'rgba16float'

# modulation: in2 merged over zero defaults
mz = c.create(td.constantCHOP, 'modzero')
for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
    setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(imod); mg.inputConnectors[0].connect(mz)
mg.par.duplicate = 'first'; mg.par.align = 'start'

# ---------- sim ----------
d_init = text('init_glsl', rd('init.glsl'))
d_sim = text('sim_glsl', rd('sim.glsl'))
d_col = text('color_glsl', rd('color.glsl'))
P = 'parent().par.'
init = glsl('init', d_init, inputs=[src], vecs=[
    ('uSeedA', [P+'Seedamount', P+'Seedthreshold', "1 if %sInvert else 0" % P, P+'Sprinkle']),
    ('uRes', [RW, RH]),
    ('uSeed', [P+'Seed']),
])
fb = c.create(td.feedbackTOP, 'feedback')
fb.par.format = 'rgba32float'
fb.inputConnectors[0].connect(init)
sim = glsl('sim', d_sim, inputs=[fb, src], vecs=[
    ('uRate', [P+'Feed' + '+ 0.01*' + CH('band1'), P+'Kill' + '+ 0.004*' + CH('band2'), P+'Diffa', P+'Diffb']),
    ('uDrive', [P+'Feedmod', P+'Killmod', "(%sInject + %s*0.5)*0.02" % (P, CH('beat')), P+'Seedthreshold']),
    ('uMisc', [P+'Dt', P+'Play', "1 if %sInvert else 0" % P, 0]),
], passes="max(1, int(parent().par.Steps))")
state = c.create(td.nullTOP, 'state'); state.par.format = 'rgba32float'
state.inputConnectors[0].connect(sim)
fb.par.top = state

def col(n): return [f"parent().par.{n}r", f"parent().par.{n}g", f"parent().par.{n}b"]
color = glsl('color', d_col, fmt='rgba16float', inputs=[state, src], vecs=[
    ('uC0', col('Color1')), ('uC1', col('Color2')), ('uC2', col('Color3')), ('uC3', col('Color4')),
    ('uStyle', ["parent().par.Colormode.menuIndex", P+'Strength', P+'Contrast', P+'Bump'+' * (1 + %s*0.5)' % CH('band3')]),
])

# ---------- mix / bypass / outputs ----------
mix = c.create(td.crossTOP, 'mixfx')
mix.inputConnectors[0].connect(src); mix.inputConnectors[1].connect(color)
mix.par.cross.expr = 'parent().par.Mix'
mix.par.outputresolution = 'custom'; mix.par.resolutionw.expr = RW; mix.par.resolutionh.expr = RH
mix.par.format = 'rgba16float'
byp = c.create(td.switchTOP, 'bypass')
byp.inputConnectors[0].connect(mix); byp.inputConnectors[1].connect(src)
byp.par.index.expr = "1 if parent().par.Bypass else 0"
o1 = c.create(td.outTOP, 'out1'); o1.inputConnectors[0].connect(byp)
o2 = c.create(td.outTOP, 'out2'); o2.inputConnectors[0].connect(state)
o1.viewer = True

# ---------- callbacks ----------
cb = text('callbacks', '''
PRESETS = {'coral': (0.0545, 0.062), 'mitosis': (0.0367, 0.0649), 'labyrinth': (0.029, 0.057),
           'spots': (0.03, 0.0625), 'worms': (0.078, 0.061)}
def onValueChange(par, prev):
    if par.name == 'Preset' and par.eval() in PRESETS:
        fe, ki = PRESETS[par.eval()]
        par.owner.par.Feed = fe
        par.owner.par.Kill = ki
    elif par.name in ('Feed', 'Kill') and par.owner.par.Preset.eval() != 'custom':
        fe, ki = PRESETS[par.owner.par.Preset.eval()]
        if abs(par.owner.par.Feed.eval() - fe) > 1e-6 or abs(par.owner.par.Kill.eval() - ki) > 1e-6:
            par.owner.par.Preset = 'custom'
def onPulse(par):
    if par.name == 'Reset':
        par.owner.op('feedback').par.resetpulse.pulse()
''')
pe = c.create(td.parameterexecuteDAT, 'parexec')
pe.par.op = '..'
pe.par.pars = 'Preset Reset Feed Kill'
pe.par.valuechange = True; pe.par.onpulse = True
pe.par.custom = True; pe.par.builtin = False
pe.par.active = True
pe.text = cb.text

o1.comment = 'stylised image'; o2.comment = 'A/B field'
c.par.opviewer = o1
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 6); o.nodeY = -150 * (i // 6)
c.save(os.path.join(ROOT, 'tox', '_raw', NAME + '.tox'))
print('saved')
