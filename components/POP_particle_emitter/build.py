import os, td

NAME = 'POP_particle_emitter'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

MODLIB = '''# modulation helper: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else the default
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)

bld = op('/').op('build') or op('/').create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

def addf(page, name, label, d, lo=None, hi=None, nlo=None, nhi=None):
    q = page.appendFloat(name, label=label)[0]
    q.default = d; q.val = d
    if lo is not None: q.min = lo; q.clampMin = True
    if hi is not None: q.max = hi; q.clampMax = True
    if nlo is not None: q.normMin = nlo
    if nhi is not None: q.normMax = nhi
def addxyz(page, name, label, d):
    q = page.appendXYZ(name, label=label)
    for par, v in zip(q, d): par.default = v; par.val = v
    return q

# ---------------- custom pars ----------------
p = c.appendCustomPage('Controls')
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')
q = p.appendInt('Count', label='Max Particles')[0]; q.default = q.val = 200000; q.min = 100; q.clampMin = True; q.normMax = 1000000
addf(p, 'Lifetime', 'Lifetime', 5.0, 0.05, None, 0.1, 20)
addf(p, 'Emitrate', 'Emit Rate', 40000, 0, None, 0, 200000)
addf(p, 'Emitvelocity', 'Emit Velocity (up)', 1.5, None, None, -5, 5)
addf(p, 'Speed', 'Speed', 1.0, 0, 5, 0, 2)
q = p.appendInt('Seed', label='Seed')[0]; q.default = q.val = 0; q.min = 0; q.clampMin = True; q.normMax = 100

p = c.appendCustomPage('Forces')
addf(p, 'Curlstrength', 'Curl Strength', 0.5, None, None, 0, 3)
addf(p, 'Curlscale', 'Curl Scale', 0.6, 0.01, None, 0.05, 3)
addf(p, 'Curlspeed', 'Curl Speed', 0.15, None, None, 0, 1)
addf(p, 'Gravity', 'Gravity', 0.3, None, None, -5, 5)
addf(p, 'Damping', 'Damping', 0.25, 0, 1, 0, 0.5)
addf(p, 'Attrradius', 'Attractor Radius', 3.0, 0.05, None, 0.5, 8)
addxyz(p, 'Attr1pos', 'Attractor 1 Position', (1.5, 1.0, 0))
addf(p, 'Attr1strength', 'Attractor 1 Strength', 2.0, None, None, -10, 10)
addxyz(p, 'Attr2pos', 'Attractor 2 Position', (-1.5, 1.0, 0))
addf(p, 'Attr2strength', 'Attractor 2 Strength', 0.0, None, None, -10, 10)

p = c.appendCustomPage('Look')
for n, d in (('Color', (1.0, 0.45, 0.12)), ('Colorend', (0.1, 0.35, 1.0))):
    q = p.appendRGB(n, label=n)
    for par, v in zip(q, d): par.default = v; par.val = v
addf(p, 'Pointsize', 'Preview Point Size', 2.5, 0.1, None, 0.5, 12)
addf(p, 'Brightness', 'Preview Brightness', 0.6, 0, 1, 0, 1)
addf(p, 'Camdist', 'Preview Camera Distance', 8.0, 0.5, None, 2, 20)

# ---------------- inputs ----------------
pin = c.create(td.inPOP, 'in1'); pin.par.connectorder = 1
cin = c.create(td.inCHOP, 'in2'); cin.par.connectorder = 2
ml = c.create(td.textDAT, 'modlib'); ml.text = MODLIB

# ---------------- demo emitter geometry (gated) ----------------
demo = c.create(td.baseCOMP, 'demo')
tor = demo.create(td.torusPOP, 'torus')
tor.par.surftype = 'triangles'
tor.par.radx = 1.0; tor.par.rady = 0.35
tor.par.cols = 64; tor.par.rows = 24
tor.par.ty = -1.0
dout = demo.create(td.outPOP, 'out1')
dout.inputConnectors[0].connect(tor)

sw = c.create(td.switchPOP, 'emitter_src')
sw.inputConnectors[0].connect(demo.outputConnectors[0])
sw.inputConnectors[1].connect(pin)
sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

# ---------------- particle system ----------------
null_loop = c.create(td.nullPOP, 'null_loop')
pp = c.create(td.particlePOP, 'particles')
pp.inputConnectors[0].connect(sw)
pp.par.targetpop = null_loop
pp.par.maxparticles.expr = "parent().par.Count"
pp.par.birthrate.expr = "parent().par.Emitrate*(1+3*%s)" % MOD('beat')
pp.par.life.expr = "parent().par.Lifetime"
pp.par.lifevariance = 0.25
pp.par.randomseed.expr = "parent().par.Seed"
pp.par.pointidreuse = 'loop'
pp.par.initvelocityy.expr = "parent().par.Emitvelocity"
pp.par.damping.expr = "parent().par.Damping"
pp.par.speed.expr = "parent().par.Speed"
pp.par.play.expr = "parent().par.Play"
pp.par.rndinputpts = True

fr1 = c.create(td.forceradialPOP, 'force_gravity_attr1')
fr1.inputConnectors[0].connect(pp)
fr1.par.globforcey.expr = "-parent().par.Gravity"
fr1.par.globforcemult = 1
fr1.par.radial = True
fr1.par.falloffradius.expr = "parent().par.Attrradius"
fr1.par.radialstrength.expr = "-parent().par.Attr1strength"   # positive strength attracts
for a in 'xyz': getattr(fr1.par, 'pos' + a).expr = f"parent().par.Attr1pos{a}"
fr2 = c.create(td.forceradialPOP, 'force_attr2')
fr2.inputConnectors[0].connect(fr1)
fr2.par.radial = True
fr2.par.falloffradius.expr = "parent().par.Attrradius"
fr2.par.radialstrength.expr = "-parent().par.Attr2strength"
for a in 'xyz': getattr(fr2.par, 'pos' + a).expr = f"parent().par.Attr2pos{a}"

nz = c.create(td.noisePOP, 'curl_noise')
nz.inputConnectors[0].connect(fr2)
nz.par.noise = False
nz.par.curl3d = True
nz.par.curl3doutputattrscope = 'PartForce'
nz.par.combineop = 'add'
nz.par.combineentity = 'curl3d'
nz.par.combineattrscope = 'PartForce'
nz.par.amp0.expr = "parent().par.Curlstrength*(1+2*%s)" % MOD('band1')
nz.par.period.expr = "1.0 / max(parent().par.Curlscale, 1e-3)"
nz.par.harmon = 0
nz.par.t4d.expr = "absTime.seconds*parent().par.Curlspeed"

cd = c.create(td.textDAT, 'color_glsl'); cd.text = rd('color.glsl')
gl = c.create(td.glslPOP, 'color')
gl.inputConnectors[0].connect(nz)
gl.par.computedat = cd
gl.par.outputattrs = ''
gl.par.attr0name = 'color'
gl.seq.vec.numBlocks = 2
gl.par.vec0name = 'uColor'
gl.par.vec1name = 'uColorEnd'
gl.par.vec0type = 'vec4'; gl.par.vec1type = 'vec4'
for i, n in enumerate(('Color', 'Colorend')):
    for j, ch in enumerate('rgb'):
        getattr(gl.par, f'vec{i}value' + 'xyz'[j]).expr = f"parent().par.{n}{ch}"
    getattr(gl.par, f'vec{i}valuew').val = 1
null_loop.inputConnectors[0].connect(gl)

o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(null_loop)

# ---------------- internal preview (not an output) ----------------
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select')
sel.par.pop = null_loop
sel.display = True; sel.render = True
mat = c.create(td.pointspriteMAT, 'sprite_mat')
mat.par.pointsize.expr = "parent().par.Pointsize"
mat.par.blending = True
mat.par.srcblend = 'sa'; mat.par.destblend = 'one'
mat.par.depthwriting = False
mat.par.alpha.expr = "parent().par.Brightness"
geo.par.material = mat

cam = c.create(td.cameraCOMP, 'cam')
cam.par.tx.expr = "parent().par.Camdist * math.sin(math.radians(absTime.seconds*8))"
cam.par.tz.expr = "parent().par.Camdist * math.cos(math.radians(absTime.seconds*8))"
cam.par.ry.expr = "absTime.seconds*8"
cam.par.ty = 0

r = c.create(td.renderTOP, 'preview')
r.par.camera = cam; r.par.geometry = geo; r.par.lights = ''
r.par.outputresolution = 'custom'
r.par.resolutionw = 960; r.par.resolutionh = 540
r.par.bgcolorr = 0; r.par.bgcolorg = 0; r.par.bgcolorb = 0; r.par.bgcolora = 1
r.par.format = 'rgba16float'

# ---------------- callbacks ----------------
pe = c.create(td.parameterexecuteDAT, 'parexec')
pe.par.op = '..'; pe.par.pars = 'Reset'; pe.par.valuechange = False; pe.par.onpulse = True
pe.par.custom = True; pe.par.builtin = False; pe.par.active = True
pe.text = '''
def onPulse(par):
    if par.name == 'Reset':
        p = par.owner.op('particles')
        p.par.initializepulse.pulse()
        p.par.startpulse.pulse()
'''

for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = r
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
