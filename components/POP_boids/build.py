import os, td

# RETRO BEGIN (v2: Loop page + Clock CHOP + optional modulation In CHOP + Look menu)
MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat, phase) of the optional In CHOP, else default
def _ins():
    return [o for o in parent().children if o.OPType == 'inCHOP']
def m(n, d=0.0):
    i = _ins()
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
def clk():
    # phase 0..1 from the Clock CHOP's 'phase' channel (None if no Clock set / channel missing)
    c = parent().par.Clock.eval()
    if c is None: return None
    ch = c['phase']
    return ch.eval() if ch is not None else None
def phase():
    c = clk()
    return (c if c is not None else parent().par.Phase.eval()) % 1.0
'''
LOOKGLSL = open(os.path.expanduser('~/software/td-plugins/components/_retro/look.glsl')).read()
def retro(c, accmode=0, gain=1.0, out='out1', rst='Reset', looksrc=None):
    import math
    ctl = [p for p in c.customPages if p.name == 'Controls'][0]
    m = ctl.appendMenu('Look', label='Look')[0]
    m.menuNames = ['original', 'mono']; m.menuLabels = ['Original', 'Mono (Rendah)']
    m.default = 'original'; m.val = 'original'
    t = ctl.appendToggle('Accent', label='Red Accent (Mono)')[0]; t.default = 0; t.val = 0
    g = ctl.appendFloat('Monogain', label='Mono Gain')[0]; g.default = g.val = gain; g.min = 0.05; g.max = 8; g.normMin = 0.2; g.normMax = 4
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]
    p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute Time', 'Phase (external)']; p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.default = 0; p.val = 0
    pg.appendCHOP('Clock', label='Clock CHOP (phase)')
    p = pg.appendFloat('Loopseconds')[0]; p.min = 0.5; p.max = 120; p.normMin = 1; p.normMax = 60; p.clampMin = True; p.default = 8.0; p.val = 8.0
    p = pg.appendInt('Loopbeats')[0]; p.min = 0; p.max = 256; p.normMin = 0; p.normMax = 64; p.clampMin = True; p.default = 0; p.val = 0
    p = pg.appendFloat('Bpm')[0]; p.min = 20; p.max = 300; p.normMin = 60; p.normMax = 200; p.default = 120; p.val = 120
    p = pg.appendToggle('Loopreset')[0]; p.default = 0; p.val = 0
    # modulation In CHOP: last input
    nin = len([o for o in c.children if o.OPType in ('inTOP', 'inPOP', 'inSOP', 'inCHOP', 'inDAT')])
    mi = c.create(td.inCHOP, 'in%d' % (nin + 1))
    ml = c.create(td.textDAT, 'modlib'); ml.text = MODLIB
    P = 'parent().par.'
    L = "(%sLoopbeats*60.0/%sBpm if %sLoopbeats>0 else %sLoopseconds)" % (P, P, P, P)
    k = c.create(td.constantCHOP, 'clock')
    k.par.name0 = 'len'; k.par.value0.expr = L
    k.par.name1 = 'ph'
    k.par.value1.expr = "op('modlib').module.phase() if %sTimesource=='phase' else ((absTime.seconds/%s) %% 1.0)" % (P, L)
    k.par.name2 = 't'
    k.par.value2.expr = "(op('modlib').module.phase()*%s) if %sTimesource=='phase' else absTime.seconds" % (L, P)
    o = c.op(out)
    src = looksrc or o.inputs[0]
    lk = c.create(td.glslTOP, 'look')
    lk.par.pixeldat = c.create(td.textDAT, 'look_glsl')
    lk.par.pixeldat.eval().text = LOOKGLSL
    lk.inputConnectors[0].connect(src)
    lk.par.outputresolution = 'useinput'
    lk.par.format = 'rgba16float'
    lk.seq.vec.numBlocks = 1
    lk.par.vec0name = 'uL'
    lk.par.vec0valuex.expr = "1 if parent().par.Look=='mono' else 0"
    lk.par.vec0valuey.expr = "parent().par.Accent"
    lk.par.vec0valuez.val = accmode
    lk.par.vec0valuew.expr = "parent().par.Monogain"
    o.inputConnectors[0].connect(lk)
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    if not c.par.Loopreset.eval(): return\n"
              "    ph = op('clock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if ph < prev - 0.5:\n"
              "        c.par.%s.pulse()\n"
              "    return\n" % rst)
    e.par.framestart = True; e.par.active = True
PHX = "op('clock')['ph']"      # wrapped loop phase 0..1
TX = "op('clock')['t']"        # loop-aware seconds
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)
# RETRO END

NAME = 'GEN_boids'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

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
def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t
def P(n): return f"parent().par.{n}"
SIDE = "max(2, int(math.ceil(math.sqrt(parent().par.Count))))"
def glsl(name, fname, inputs=(), vecs=(), res='side', fmt='rgba32float'):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = text(name + '_glsl', rd(fname))
    g.par.format = fmt
    g.par.outputresolution = 'custom'
    if res == 'side':
        g.par.resolutionw.expr = SIDE; g.par.resolutionh.expr = SIDE
    else:
        g.par.resolutionw.expr = P('Resolutionw'); g.par.resolutionh.expr = P('Resolutionh')
    g.par.inputfiltertype = 'nearest'
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = e
    return g
def V(name, par): return (name, [P(par)])

# ---------------- custom pars ----------------
p = c.appendCustomPage('Controls')
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')
q = p.appendInt('Count', label='Count')[0]; q.default = q.val = 4096; q.min = 16; q.max = 65536; q.clampMin = q.clampMax = True; q.normMax = 16384
addf(p, 'Speed', 'Speed', 1.0, 0, 5, 0, 2)
q = p.appendInt('Seed', label='Seed')[0]; q.default = q.val = 1; q.min = 0
q = p.appendWH('Resolution', label='Resolution'); q[0].default = q[0].val = 1280; q[1].default = q[1].val = 720
q[0].min = q[1].min = 16; q[0].clampMin = q[1].clampMin = True

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
addf(p, 'Obstacleorbit', 'Obstacle Orbit (loop)', 0.0, 0, None, 0, 5)
addf(p, 'Obstacleradius', 'Obstacle Radius', 1.3, 0.05, None, 0.2, 4)

p = c.appendCustomPage('Render')
addf(p, 'Boidsize', 'Boid Size', 0.5, 0.01, None, 0.2, 4)
for n, d in (('Color1', (0.1, 0.45, 1.0)), ('Color2', (1.0, 0.55, 0.15))):
    q = p.appendRGB(n, label=n)
    for par, v in zip(q, d): par.default = v; par.val = v
addf(p, 'Camdist', 'Camera Distance', 17.0, 1.0, None, 4, 40)
addf(p, 'Camspin', 'Camera Spin (deg/s)', 10.0, None, None, -60, 60)

# ---------------- simulation ----------------
zero = c.create(td.constantTOP, 'size_ref')
zero.par.format = 'rgba32float'; zero.par.outputresolution = 'custom'
zero.par.resolutionw.expr = SIDE; zero.par.resolutionh.expr = SIDE

SIDEV = ('uSide', [SIDE])
init_pos = glsl('init_pos', 'init_pos.glsl', inputs=[zero], vecs=[V('uBound', 'Boundsize'), V('uSeed', 'Seed'), SIDEV])
init_vel = glsl('init_vel', 'init_vel.glsl', inputs=[zero], vecs=[V('uSeed', 'Seed'), ('uSpeed', [P('Maxspeed') + ' * 0.6']), SIDEV])
def fbk(name, src):
    f = c.create(td.feedbackTOP, name); f.par.format = 'rgba32float'
    f.par.outputresolution = 'custom'; f.par.resolutionw.expr = SIDE; f.par.resolutionh.expr = SIDE
    f.inputConnectors[0].connect(src); return f
fb_pos = fbk('fb_pos', init_pos); fb_vel = fbk('fb_vel', init_vel)

DT = ('uDt', [f"{P('Speed')} * {P('Play')} / 60.0"])
OBPOS = {'x': P('Obstacleposx') + " + " + P('Obstacleorbit') + "*math.cos(2*math.pi*" + PHX + ")",
         'y': P('Obstacleposy'),
         'z': P('Obstacleposz') + " + " + P('Obstacleorbit') + "*math.sin(2*math.pi*" + PHX + ")"}
OBS = [V('uObsOn', 'Obstacle'), V('uObsR', 'Obstacleradius'),
       ('uObsPos', [OBPOS['x'], OBPOS['y'], OBPOS['z']])]
WRAP = ('uWrap', ["1 if parent().par.Boundmode == 'wrap' else 0"])
vel_new = glsl('vel_update', 'vel.glsl', inputs=[fb_pos, fb_vel], vecs=[
    V('uCount', 'Count'), DT, V('uSepW', 'Separation'), V('uAliW', 'Alignment'), ('uCohW', [P('Cohesion') + "*(1+3*op('modlib').module.m('band1'))"]),
    V('uSepR', 'Sepradius'), V('uAliR', 'Aliradius'), V('uCohR', 'Cohradius'),
    V('uMaxSpeed', 'Maxspeed'), V('uMinSpeed', 'Minspeed'), V('uMaxForce', 'Maxforce'),
    V('uBound', 'Boundsize'), WRAP, ('uWander', [P('Wander') + "*(1+4*op('modlib').module.m('beat'))"]), ('uTime', [PHX + " * max(1, round(0.7*op('clock')['len']))"]), ('uWK', ["max(1, round(0.7*op('clock')['len']))"])] + OBS)
vel = c.create(td.nullTOP, 'vel'); vel.par.format = 'rgba32float'; vel.inputConnectors[0].connect(vel_new)
pos_new = glsl('pos_update', 'pos.glsl', inputs=[fb_pos, vel], vecs=[
    DT, V('uBound', 'Boundsize'), WRAP, V('uCount', 'Count')] + OBS)
pos = c.create(td.nullTOP, 'pos'); pos.par.format = 'rgba32float'; pos.inputConnectors[0].connect(pos_new)
fb_pos.par.top = pos; fb_vel.par.top = vel

colr = glsl('color', 'color.glsl', inputs=[vel], vecs=[
    ('uColA', [P('Color1r'), P('Color1g'), P('Color1b')]), ('uColB', [P('Color2r'), P('Color2g'), P('Color2b')]),
    V('uMaxSpeed', 'Maxspeed')])
colr.par.outputresolution = 'custom'

# ---------------- TOP -> POP instance data ----------------
tp = c.create(td.toptoPOP, 'instance_data')
tp.par.rgba = 'custom'
tp.seq.input.numBlocks = 3
tp.par.input0top = pos; tp.par.input0chanscope = 'r g b'; tp.par.input0attrscope = 'P'
tp.par.input1top = vel; tp.par.input1chanscope = 'r g b'; tp.par.input1attrscope = 'N'
tp.par.input2top = colr; tp.par.input2chanscope = 'r g b a'; tp.par.input2attrscope = 'Color'
tp.par.maxpointsenable = True
tp.par.maxpoints.expr = P('Count')
out_pop = c.create(td.nullPOP, 'out1'); out_pop.inputConnectors[0].connect(tp)   # primary output: boid points (P, N=heading, Color)

# ---------------- rendering ----------------
geo = c.create(td.geometryCOMP, 'boid_geo')
for o in list(geo.children): o.destroy()
tube = geo.create(td.tubePOP, 'cone_tube')
tube.par.orient = 'y'; tube.par.height = 1.0; tube.par.cols = 10; tube.par.rows = 2
tube.par.radx = 0.5; tube.par.rady = 0.5; tube.par.endcaps = True
taper_dat = geo.create(td.textDAT, 'taper_glsl')
taper_dat.text = """void main() {
	const uint id = TDIndex();
	if (id >= TDNumElements())
		return;
	vec3 p = TDIn_P();
	float k = clamp(0.5 - p.y, 0.0, 1.0);   // radius tapers to 0 at the +Y tip
	P[id] = vec3(p.x * k * 0.2, p.y * 0.6, p.z * k * 0.2) * uSize;
}
"""
taper = geo.create(td.glslPOP, 'cone_taper')
taper.inputConnectors[0].connect(tube)
taper.par.computedat = taper_dat
taper.par.outputattrs = 'P'
taper.seq.vec.numBlocks = 1
taper.par.vec0name = 'uSize'
taper.par.vec0valuex.expr = 'parent(2).par.Boidsize'
nrm = geo.create(td.normalPOP, 'cone_normals')
nrm.inputConnectors[0].connect(taper)
tmpl = geo.create(td.selectPOP, 'template')
tmpl.par.pop = tp
cp = geo.create(td.copyPOP, 'copy_to_boids')
cp.inputConnectors[0].connect(nrm); cp.inputConnectors[1].connect(tmpl)
cp.par.dotemplatetranslate = True
cp.par.dotemplaterotateto = True
cp.par.vecattr = 'N'
cp.par.instanceforward = 'posy'
cp.par.doattr = True
cp.par.templateattr0names = 'Color'
cp.display = True; cp.render = True
mat = c.create(td.phongMAT, 'boid_mat')
mat.par.diffr = 1; mat.par.diffg = 1; mat.par.diffb = 1
mat.par.ambr = 0.6; mat.par.ambg = 0.6; mat.par.ambb = 0.6
geo.par.material = mat

og = c.create(td.geometryCOMP, 'obstacle_geo')
for o in list(og.children): o.destroy()
sph = og.create(td.sphereSOP, 'sphere'); sph.display = True; sph.render = True
og.par.tx.expr = OBPOS['x']; og.par.ty.expr = OBPOS['y']; og.par.tz.expr = OBPOS['z']
for a in 'xyz': getattr(og.par, 's' + a).expr = P('Obstacleradius') + ' * 0.97'
og.par.render.expr = P('Obstacle')
omat = c.create(td.phongMAT, 'obstacle_mat')
omat.par.diffr = omat.par.diffg = omat.par.diffb = 0.22
omat.par.ambr = omat.par.ambg = omat.par.ambb = 0.25
og.par.material = omat

cam = c.create(td.cameraCOMP, 'cam')
cam.par.tx.expr = P('Camdist') + " * math.sin(math.radians(" + TX + " * parent().par.Camspin))"
cam.par.tz.expr = P('Camdist') + " * math.cos(math.radians(" + TX + " * parent().par.Camspin))"
cam.par.ry.expr = "" + TX + " * parent().par.Camspin"
cam.par.ty.expr = P('Camdist') + " * 0.25"
cam.par.rx.expr = "-math.degrees(math.atan2(0.25, 1.0))"
cam.par.far = 500
light = c.create(td.lightCOMP, 'light')
light.par.tx = 8; light.par.ty = 14; light.par.tz = 10
light.par.dimmer = 1.5

r = c.create(td.renderTOP, 'render')
r.par.camera = cam; r.par.geometry = '*geo'; r.par.lights = light
r.par.outputresolution = 'custom'
r.par.resolutionw.expr = P('Resolutionw'); r.par.resolutionh.expr = P('Resolutionh')
r.par.bgcolorr = 0.01; r.par.bgcolorg = 0.012; r.par.bgcolorb = 0.025; r.par.bgcolora = 1
r.par.antialias = '4x' if 'antialias' in [x.name for x in r.pars()] else r.par.antialias
# internal preview render (node viewer), not an output
o1 = c.create(td.nullTOP, 'preview'); o1.inputConnectors[0].connect(r)
# second output: the instanced cone mesh, ready to render
cones = c.create(td.selectPOP, 'cones_select'); cones.par.pop = cp
o2 = c.create(td.nullPOP, 'out2'); o2.inputConnectors[0].connect(cones)

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

c.op('out1').comment = 'boid points (POP)'
c.op('out2').comment = 'boid cones (POP)'
retro(c, accmode=0, gain=1.5, out='preview')
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = o1
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
