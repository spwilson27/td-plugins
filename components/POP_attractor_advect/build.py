import os, td
NAME = 'POP_attractor_advect'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')
P = 'parent().par.'

MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else default
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i or not i[0].inputs: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
def rd(f): return open(D + f).read()
root = op('/build') or op('/').create(td.baseCOMP, 'build')
old = root.op(NAME)
if old: old.destroy()
c = root.create(td.baseCOMP, NAME)

def dat(name, text):
    d = c.create(td.textDAT, name); d.text = text; return d
def setvec(o, i, name, *vals):
    getattr(o.par, 'vec%dname' % i).val = name
    getattr(o.par, 'vec%dtype' % i).val = 'vec4' if len(vals) == 4 else 'vec3'
    for k, v in zip('xyzw', vals):
        p = getattr(o.par, 'vec%dvalue%s' % (i, k))
        if isinstance(v, str): p.expr = v
        else: p.val = v
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False):
    p = (page.appendInt if isint else page.appendFloat)(name, label=label)[0]
    p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
def menu(page, name, label, names, labels, default=0):
    p = page.appendMenu(name, label=label)[0]; p.menuNames = names; p.menuLabels = labels
    p.val = names[default]; p.default = names[default]
def rgb(page, name, label, vals):
    for p, v in zip(page.appendRGB(name, label=label), vals): p.default = v; p.val = v; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1

AN = ['lorenz', 'aizawa', 'thomas', 'halvorsen', 'dadras']
AL = ['Lorenz', 'Aizawa', 'Thomas', 'Halvorsen', 'Dadras']
pg = c.appendCustomPage('Controls')
menu(pg, 'Attractor', 'Attractor A', AN, AL, 0)
menu(pg, 'Attractorb', 'Attractor B', AN, AL, 1)
num(pg, 'Morph', 'Morph A>B', 0.0, 0, 1)
num(pg, 'Speed', 'Speed', 1.0, 0.0, 4, True, False)
pg.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
pg.appendPulse('Reset', label='Reset (recapture input)')
num(pg, 'Fieldscale', 'Field Size', 1.0, 0.01, 100, True, False)
for a, v in zip('xyz', (0.0, 0.0, 0.0)):
    num(pg, 'Center' + a, 'Center ' + a.upper(), v, -10, 10, False, False)
num(pg, 'Coefmod', 'Coef Animate', 0.0, 0, 1)
num(pg, 'Coefspeed', 'Coef Rate (rad/s)', 0.5, 0, 6)
num(pg, 'Substeps', 'Substeps / Frame', 6, 1, 24, isint=True)
num(pg, 'Rebirth', 'Rebirth (re-seed/frame)', 0.0, 0, 0.2)
num(pg, 'Seed', 'Seed', 1, 0, 1000, isint=True)
num(pg, 'Preroll', 'Preroll (frames)', 90, 0, 600, isint=True)
pg = c.appendCustomPage('Trails')
pg.appendToggle('Trails', label='Trails (lines)')
num(pg, 'Traillength', 'Trail Length (s)', 0.6, 0.05, 6, True, False)
pg = c.appendCustomPage('Demo')
menu(pg, 'Demoshape', 'Demo Shape (no input)', ['sphere', 'box'], ['Sphere', 'Box'], 0)
num(pg, 'Demopoints', 'Demo Points', 6000, 100, 50000, isint=True)
pg = c.appendCustomPage('Look')
num(pg, 'Colormix', 'Color Mix', 1.0, 0, 1)
rgb(pg, 'Color1', 'Color Slow', (0.1, 0.4, 1.0))
rgb(pg, 'Color2', 'Color Fast', (1.0, 0.45, 0.15))
num(pg, 'Colorspeed', 'Color Speed Scale', 12.0, 0.1, 200, True, False)
num(pg, 'Pointsize', 'Preview Point Size', 2.5, 1, 16, True, False)

# ---- modulation input + helper
inp = c.create(td.inPOP, 'in1')
inm = c.create(td.inCHOP, 'in2')
dat('modlib', MODLIB)
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)

# ---- gated demo points
demo = c.create(td.baseCOMP, 'demo')
dsp = demo.create(td.spherePOP, 'sphere'); dsp.par.type = 'geodesic'; dsp.par.freq = 6; dsp.par.radx = dsp.par.rady = dsp.par.radz = 0.9
dbx = demo.create(td.boxPOP, 'box'); dbx.par.sizex = dbx.par.sizey = dbx.par.sizez = 1.3
dsw = demo.create(td.switchPOP, 'shape')
dsw.inputConnectors[0].connect(dsp); dsw.inputConnectors[1].connect(dbx)
dsw.par.index.expr = "0 if parent(2).par.Demoshape == 'sphere' else 1"
dsc = demo.create(td.sprinklePOP, 'scatter'); dsc.inputConnectors[0].connect(dsw)
dsc.par.method = 'total'; dsc.par.numpoints.expr = "parent(2).par.Demopoints"
dout = demo.create(td.outPOP, 'out1'); dout.inputConnectors[0].connect(dsc)

src = c.create(td.switchPOP, 'source')
src.inputConnectors[0].connect(demo.outputConnectors[0]); src.inputConnectors[1].connect(inp)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
seed = c.create(td.nullPOP, 'seed'); seed.inputConnectors[0].connect(src)

# ---- stateful advection: feedback POP <-> GLSL POP step
fb = c.create(td.feedbackPOP, 'fb_state')
fb.inputConnectors[0].connect(seed)
step = c.create(td.glslPOP, 'step')
step.inputConnectors[0].connect(fb); step.inputConnectors[1].connect(seed)
step.par.computedat = dat('step_code', rd('step.glsl'))
step.par.outputattrs = 'P'
step.seq.attr.numBlocks = 1
step.par.attr0name = 'color'
step.seq.vec.numBlocks = 6
setvec(step, 0, 'uA', P + "Attractor.menuIndex", P + "Attractorb.menuIndex", P + "Morph", P + "Fieldscale")
setvec(step, 1, 'uB', P + "Speed * (1 if " + P + "Play else 0) * (1 + 0.5*" + MOD('band2') + " + 1.5*" + MOD('beat') + ")",
       "absTime.seconds * " + P + "Coefspeed", P + "Substeps", "(" + P + "Seed + absTime.frame * 0.618) % 977")
setvec(step, 2, 'uC', P + "Coefmod + 0.5*" + MOD('band1'), P + "Rebirth", P + "Colorspeed", P + "Colormix")
setvec(step, 3, 'uD', P + "Centerx", P + "Centery", P + "Centerz", 0)
setvec(step, 4, 'uC1', *[P + 'Color1' + a for a in 'rgb'])
setvec(step, 5, 'uC2', *[P + 'Color2' + a for a in 'rgb'])
fb.par.targetpop = step
fb.par.prerollunit = 'frames'; fb.par.preroll.expr = P + "Preroll"
fb.par.initializepulse.expr = "len(parent().inputConnectors[0].connections) + 0*absTime.frame"
adv = c.create(td.nullPOP, 'advected'); adv.inputConnectors[0].connect(step)

# ---- trails
tr = c.create(td.trailPOP, 'trail'); tr.inputConnectors[0].connect(adv)
tr.par.length.expr = P + "Traillength"
tpick = c.create(td.switchPOP, 'trailpick')
tpick.inputConnectors[0].connect(adv); tpick.inputConnectors[1].connect(tr)
tpick.par.index.expr = "1 if " + P + "Trails else 0"
o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(tpick)
o1.comment = 'advected points'

# ---- internal preview render (not an output)
geo = c.create(td.geometryCOMP, 'pts_geo')
for ch in list(geo.children): ch.destroy()
cv = c.create(td.convertPOP, 'points_only'); cv.par.convert = 'topointprims'; cv.inputConnectors[0].connect(tpick)
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = cv; sel.display = True; sel.render = True
mat = c.create(td.pointspriteMAT, 'sprite_mat'); mat.par.pointsize.expr = P + 'Pointsize'
mat.par.blending = True; mat.par.srcblend = 'sa'; mat.par.destblend = 'one'; mat.par.depthwriting = False
geo.par.material = mat
lgeo = c.create(td.geometryCOMP, 'line_geo')
for ch in list(lgeo.children): ch.destroy()
lsel = lgeo.create(td.selectPOP, 'select'); lsel.par.pop = tpick; lsel.display = True; lsel.render = True
lmat = c.create(td.constantMAT, 'line_mat'); lmat.par.applypointcolor = True
lmat.par.blending = True; lmat.par.srcblend = 'sa'; lmat.par.destblend = 'one'; lmat.par.depthwriting = False
lmat.par.alpha = 0.6; lgeo.par.material = lmat
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target'); cam.par.lookat = tgt
cam.par.tx.expr = P + "Fieldscale*3.2*math.sin(absTime.seconds*0.15)"
cam.par.tz.expr = P + "Fieldscale*3.2*math.cos(absTime.seconds*0.15)"
cam.par.ty.expr = P + "Fieldscale*0.6"
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry.expr = "'pts_geo line_geo' if " + P + "Trails else 'pts_geo'"; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw = 640; rt.par.resolutionh = 360; rt.par.format = 'rgba16float'
rt.par.bgcolorr = rt.par.bgcolorg = 0; rt.par.bgcolorb = 0.012; rt.par.bgcolora = 1
pv = c.create(td.nullTOP, 'preview'); pv.inputConnectors[0].connect(rt)
c.save(OUT); print('saved')
