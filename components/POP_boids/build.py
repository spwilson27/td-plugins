import os, td

NAME = 'POP_boids'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

bld = op('/').op('build') or op('/').create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else default
def _ins():
    return [o for o in parent().children if o.OPType == 'inCHOP']
def m(n, d=0.0):
    i = _ins()
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
def MOD(n): return "op('modlib').module.m('%s')" % n

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
def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t
def P(n): return f"parent().par.{n}"

# ---------------- inputs / gated demo ----------------
inpop = c.create(td.inPOP, 'in1'); inpop.par.connectorder = 1
inmod = c.create(td.inCHOP, 'in2'); inmod.par.connectorder = 2
ml = c.create(td.textDAT, 'modlib'); ml.text = MODLIB

demo = c.create(td.baseCOMP, 'demo')
dpg = demo.create(td.pointgeneratorPOP, 'scatter')
dpg.par.shape = 'sphere'; dpg.par.distribution = 'volume'; dpg.par.numpoints = 3000
dpg.par.radiusx = dpg.par.radiusy = dpg.par.radiusz = 3.0
dpg.par.seed = 3
dout = demo.create(td.outPOP, 'out1'); dout.inputConnectors[0].connect(dpg)
dout.comment = 'demo flock points'
src = c.create(td.switchPOP, 'src_switch')
src.inputConnectors[0].connect(demo.outputConnectors[0])
src.inputConnectors[1].connect(inpop)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
# flock size: input point count, capped by Maxboids
N = "max(1, min(int(parent().par.Maxboids), int(op('src_switch').numPoints())))"
SIDE = "max(2, int(math.ceil(math.sqrt(%s))))" % N.replace('parent()', 'parent()')

# ---------------- custom pars ----------------
p = c.appendCustomPage('Controls')
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset (re-seed from input points)')
q = p.appendInt('Maxboids', label='Max Boids')[0]; q.default = q.val = 8192; q.min = 16; q.max = 65536
q.clampMin = q.clampMax = True; q.normMin = 256; q.normMax = 16384
addf(p, 'Speed', 'Speed', 1.0, 0, 5, 0, 2)
q = p.appendInt('Seed', label='Seed')[0]; q.default = q.val = 1; q.min = 0

p = c.appendCustomPage('Flocking')
addf(p, 'Separation', 'Separation', 1.5, 0, None, 0, 5)
addf(p, 'Alignment', 'Alignment', 1.2, 0, None, 0, 5)
addf(p, 'Cohesion', 'Cohesion', 0.8, 0, None, 0, 5)
addf(p, 'Sepradius', 'Separation Radius', 0.5, 0.01, None, 0.1, 3)
addf(p, 'Aliradius', 'Alignment Radius', 1.2, 0.01, None, 0.1, 5)
addf(p, 'Cohradius', 'Cohesion Radius', 1.6, 0.01, None, 0.1, 5)
addf(p, 'Maxspeed', 'Max Speed', 4.0, 0.01, None, 0.5, 10)
addf(p, 'Minspeed', 'Min Speed', 1.5, 0.0, None, 0, 5)
addf(p, 'Maxforce', 'Max Force', 10.0, 0.01, None, 1, 40)
addf(p, 'Wander', 'Wander', 0.6, 0, None, 0, 3)

p = c.appendCustomPage('Bounds')
addf(p, 'Boundsize', 'Bounds Half-Size', 5.0, 0.5, None, 1, 20)
m = p.appendMenu('Boundmode', label='Bounds Mode')[0]
m.menuNames = ['wrap', 'bounce']; m.menuLabels = ['Wrap', 'Bounce']; m.default = 'wrap'; m.val = 'wrap'
q = p.appendToggle('Obstacle', label='Obstacle')[0]; q.default = 1; q.val = 1
addxyz(p, 'Obstaclepos', 'Obstacle Position', (0, 0, 0))
addf(p, 'Obstacleradius', 'Obstacle Radius', 1.3, 0.05, None, 0.2, 4)

p = c.appendCustomPage('Look')
addf(p, 'Boidsize', 'Boid Size', 0.5, 0.01, None, 0.2, 4)
for n, d in (('Color1', (0.1, 0.45, 1.0)), ('Color2', (1.0, 0.55, 0.15))):
    q = p.appendRGB(n, label=n)
    for par, v in zip(q, d): par.default = v; par.val = v

# ---------------- simulation ----------------
def glsl(name, fname, inputs=(), vecs=()):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = text(name + '_glsl', rd(fname))
    g.par.format = 'rgba32float'
    g.par.outputresolution = 'custom'
    g.par.resolutionw.expr = SIDE; g.par.resolutionh.expr = SIDE
    g.par.inputfiltertype = 'nearest'
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = e
    return g
def V(name, par): return (name, [P(par)])

zero = c.create(td.constantTOP, 'size_ref')
zero.par.format = 'rgba32float'; zero.par.outputresolution = 'custom'
zero.par.resolutionw.expr = SIDE; zero.par.resolutionh.expr = SIDE

# input points' P -> square texture (index i = y*width+x)
pt = c.create(td.poptoTOP, 'input_pos')
pt.par.pop = src
pt.par.extract = 'point'; pt.par.attribscope = 'P'; pt.par.layout = 'square'
pt.par.outputresolution = 'useinput'; pt.par.format = 'rgba32float'

init_pos = glsl('init_pos', 'init_pos.glsl', inputs=[zero, pt], vecs=[('uSide', [SIDE]), ('uCount', [N])])
init_vel = glsl('init_vel', 'init_vel.glsl', inputs=[zero], vecs=[V('uSeed', 'Seed'), ('uSpeed', [P('Maxspeed') + ' * 0.6']), ('uSide', [SIDE])])
def fbk(name, srcop):
    f = c.create(td.feedbackTOP, name); f.par.format = 'rgba32float'
    f.par.outputresolution = 'custom'; f.par.resolutionw.expr = SIDE; f.par.resolutionh.expr = SIDE
    f.inputConnectors[0].connect(srcop); return f
fb_pos = fbk('fb_pos', init_pos); fb_vel = fbk('fb_vel', init_vel)

DT = ('uDt', [f"{P('Speed')} * {P('Play')} / 60.0"])
OBS = [V('uObsOn', 'Obstacle'), V('uObsR', 'Obstacleradius'),
       ('uObsPos', [P('Obstacleposx'), P('Obstacleposy'), P('Obstacleposz')])]
WRAP = ('uWrap', ["1 if parent().par.Boundmode == 'wrap' else 0"])
UC = ('uCount', [N])
vel_new = glsl('vel_update', 'vel.glsl', inputs=[fb_pos, fb_vel], vecs=[
    UC, DT, V('uSepW', 'Separation'), V('uAliW', 'Alignment'), ('uCohW', [P('Cohesion') + "*(1+3*" + MOD('band1') + ")"]),
    V('uSepR', 'Sepradius'), V('uAliR', 'Aliradius'), V('uCohR', 'Cohradius'),
    V('uMaxSpeed', 'Maxspeed'), V('uMinSpeed', 'Minspeed'), V('uMaxForce', 'Maxforce'),
    V('uBound', 'Boundsize'), WRAP, ('uWander', [P('Wander') + "*(1+4*" + MOD('beat') + ")"]),
    ('uTime', ["absTime.seconds * 0.7"])] + OBS)
vel = c.create(td.nullTOP, 'vel'); vel.par.format = 'rgba32float'; vel.inputConnectors[0].connect(vel_new)
pos_new = glsl('pos_update', 'pos.glsl', inputs=[fb_pos, vel], vecs=[DT, V('uBound', 'Boundsize'), WRAP, UC] + OBS)
pos = c.create(td.nullTOP, 'pos'); pos.par.format = 'rgba32float'; pos.inputConnectors[0].connect(pos_new)
fb_pos.par.top = pos; fb_vel.par.top = vel

colr = glsl('color', 'color.glsl', inputs=[vel], vecs=[
    ('uColA', [P('Color1r'), P('Color1g'), P('Color1b')]), ('uColB', [P('Color2r'), P('Color2g'), P('Color2b')]),
    V('uMaxSpeed', 'Maxspeed')])
head = glsl('heading', 'heading.glsl', inputs=[vel])

# ---------------- TOP -> POP: out1 = boid points ----------------
tp = c.create(td.toptoPOP, 'instance_data')
tp.par.rgba = 'custom'
tp.seq.input.numBlocks = 3
tp.par.input0top = pos; tp.par.input0chanscope = 'r g b'; tp.par.input0attrscope = 'P'
tp.par.input1top = head; tp.par.input1chanscope = 'r g b'; tp.par.input1attrscope = 'N'
tp.par.input2top = colr; tp.par.input2chanscope = 'r g b a'; tp.par.input2attrscope = 'Color'
tp.par.maxpointsenable = True
tp.par.maxpoints.expr = N
out_pop = c.create(td.nullPOP, 'out1'); out_pop.inputConnectors[0].connect(tp)

# ---------------- out2: instanced cone mesh ----------------
tube = c.create(td.tubePOP, 'cone_tube')
tube.par.orient = 'y'; tube.par.height = 1.0; tube.par.cols = 10; tube.par.rows = 2
tube.par.radx = 0.5; tube.par.rady = 0.5; tube.par.endcaps = True
taper_dat = text('taper_glsl', """void main() {
	const uint id = TDIndex();
	if (id >= TDNumElements())
		return;
	vec3 p = TDIn_P();
	float k = clamp(0.5 - p.y, 0.0, 1.0);   // radius tapers to 0 at the +Y tip
	P[id] = vec3(p.x * k * 0.2, p.y * 0.6, p.z * k * 0.2) * uSize;
}
""")
taper = c.create(td.glslPOP, 'cone_taper')
taper.inputConnectors[0].connect(tube)
taper.par.computedat = taper_dat
taper.par.outputattrs = 'P'
taper.seq.vec.numBlocks = 1
taper.par.vec0name = 'uSize'
taper.par.vec0valuex.expr = P('Boidsize')
nrm = c.create(td.normalPOP, 'cone_normals'); nrm.inputConnectors[0].connect(taper)
cp = c.create(td.copyPOP, 'copy_to_boids')
cp.inputConnectors[0].connect(nrm); cp.inputConnectors[1].connect(tp)
cp.par.dotemplatetranslate = True
cp.par.dotemplaterotateto = True
cp.par.vecattr = 'N'
cp.par.instanceforward = 'posy'
cp.par.doattr = True
cp.par.templateattr0names = 'Color'
out2 = c.create(td.nullPOP, 'out2'); out2.inputConnectors[0].connect(cp)

# ---------------- internal preview (node viewer only) ----------------
geo = c.create(td.geometryCOMP, 'boid_geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'cones'); sel.par.pop = out2
sel.display = True; sel.render = True
mat = c.create(td.phongMAT, 'boid_mat')
mat.par.diffr = 1; mat.par.diffg = 1; mat.par.diffb = 1
mat.par.ambr = 0.6; mat.par.ambg = 0.6; mat.par.ambb = 0.6
geo.par.material = mat

og = c.create(td.geometryCOMP, 'obstacle_geo')
for o in list(og.children): o.destroy()
sph = og.create(td.sphereSOP, 'sphere'); sph.display = True; sph.render = True
og.par.tx.expr = P('Obstacleposx'); og.par.ty.expr = P('Obstacleposy'); og.par.tz.expr = P('Obstacleposz')
for a in 'xyz': getattr(og.par, 's' + a).expr = P('Obstacleradius') + ' * 0.97'
og.par.render.expr = P('Obstacle')
omat = c.create(td.phongMAT, 'obstacle_mat')
omat.par.diffr = omat.par.diffg = omat.par.diffb = 0.22
omat.par.ambr = omat.par.ambg = omat.par.ambb = 0.25
og.par.material = omat

CD = P('Boundsize') + " * 3.4"
cam = c.create(td.cameraCOMP, 'cam')
cam.par.tx.expr = CD + " * math.sin(math.radians(absTime.seconds * 10))"
cam.par.tz.expr = CD + " * math.cos(math.radians(absTime.seconds * 10))"
cam.par.ry.expr = "absTime.seconds * 10"
cam.par.ty.expr = CD + " * 0.25"
cam.par.rx.expr = "-math.degrees(math.atan2(0.25, 1.0))"
cam.par.far = 500
light = c.create(td.lightCOMP, 'light')
light.par.tx = 8; light.par.ty = 14; light.par.tz = 10
light.par.dimmer = 1.5

r = c.create(td.renderTOP, 'render')
r.par.camera = cam; r.par.geometry = '*geo'; r.par.lights = light
r.par.outputresolution = 'custom'; r.par.resolutionw = 960; r.par.resolutionh = 540
r.par.bgcolorr = 0.01; r.par.bgcolorg = 0.012; r.par.bgcolorb = 0.025; r.par.bgcolora = 1
pv = c.create(td.nullTOP, 'preview'); pv.inputConnectors[0].connect(r)

# ---------------- callbacks ----------------
pe = c.create(td.parameterexecuteDAT, 'parexec')
pe.par.op = '..'; pe.par.pars = 'Reset'; pe.par.valuechange = False; pe.par.onpulse = True
pe.par.custom = True; pe.par.builtin = False; pe.par.active = True
pe.text = '''
def onPulse(par):
    if par.name == 'Reset':
        for n in ('fb_pos', 'fb_vel'):
            par.owner.op(n).par.resetpulse.pulse()
'''
# re-seed when the flock size changes (e.g. an input gets connected)
cn = c.create(td.constantCHOP, 'count_watch'); cn.par.name0 = 'n'; cn.par.value0.expr = N
ce = c.create(td.chopexecuteDAT, 'count_exec'); ce.par.chop = cn
ce.par.valuechange = True; ce.par.active = True
ce.text = '''
def onValueChange(channel, sampleIndex, val, prev):
    for n in ('fb_pos', 'fb_vel'):
        parent().op(n).par.resetpulse.pulse()
'''

c.op('out1').comment = 'boid points (POP)'
c.op('out2').comment = 'boid cones (POP)'
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = pv
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
