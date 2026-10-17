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

NAME = 'GEN_gpu_particles'
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
    return q

# ---------------- custom pars ----------------
p = c.appendCustomPage('Controls')
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')
q = p.appendInt('Count', label='Max Particles')[0]; q.default = q.val = 200000; q.min = 100; q.clampMin = True; q.normMax = 1000000
addf(p, 'Lifetime', 'Lifetime', 5.0, 0.05, None, 0.1, 20)
addf(p, 'Emitrate', 'Emit Rate', 40000, 0, None, 0, 200000)
addxyz(p, 'Emitterpos', 'Emitter Position', (0, -1.5, 0))
addf(p, 'Emitradius', 'Emitter Radius', 0.4, 0.0, None, 0, 2)
addf(p, 'Emitvelocity', 'Emit Velocity', 1.5, None, None, -5, 5)
addf(p, 'Speed', 'Speed', 1.0, 0, 5, 0, 2)
q = p.appendWH('Resolution', label='Resolution'); q[0].default = q[0].val = 1280; q[1].default = q[1].val = 720
q[0].min = q[1].min = 16; q[0].clampMin = q[1].clampMin = True

p = c.appendCustomPage('Forces')
addf(p, 'Curlstrength', 'Curl Strength', 0.5, None, None, 0, 3)
addf(p, 'Curlscale', 'Curl Scale', 0.6, 0.01, None, 0.05, 3)
addf(p, 'Curlspeed', 'Curl Speed', 0.15, None, None, 0, 1)
addf(p, 'Gravity', 'Gravity', 0.3, None, None, -5, 5)
addf(p, 'Damping', 'Damping', 0.25, 0, 1, 0, 0.5)
addf(p, 'Attrradius', 'Attractor Radius', 3.0, 0.05, None, 0.5, 8)
addf(p, 'Attrorbit', 'Attractor Orbit (loop)', 0.0, 0, None, 0, 4)
addxyz(p, 'Attr1pos', 'Attractor 1 Position', (1.5, 1.0, 0))
addf(p, 'Attr1strength', 'Attractor 1 Strength', 2.0, None, None, -10, 10)
addxyz(p, 'Attr2pos', 'Attractor 2 Position', (-1.5, 1.0, 0))
addf(p, 'Attr2strength', 'Attractor 2 Strength', 0.0, None, None, -10, 10)

p = c.appendCustomPage('Render')
addf(p, 'Pointsize', 'Point Size', 2.5, 0.1, None, 0.5, 12)
for n, d in (('Color', (1.0, 0.45, 0.12)), ('Colorend', (0.1, 0.35, 1.0))):
    q = p.appendRGB(n, label=n)
    for par, v in zip(q, d): par.default = v; par.val = v
addf(p, 'Brightness', 'Brightness', 0.6, 0, 1, 0, 1)
addf(p, 'Camdist', 'Camera Distance', 8.0, 0.5, None, 2, 20)
addf(p, 'Camspin', 'Camera Spin (deg/s)', 8.0, None, None, -60, 60)

# ---------------- POP network ----------------
pg = c.create(td.pointgeneratorPOP, 'emitter')
pg.par.shape = 'sphere'; pg.par.distribution = 'volume'; pg.par.numpoints = 4096
for a in 'xyz':
    getattr(pg.par, 'radius' + a).expr = "parent().par.Emitradius"
    getattr(pg.par, 't' + a).expr = f"parent().par.Emitterpos{a}"

null_loop = c.create(td.nullPOP, 'null_loop')
pp = c.create(td.particlePOP, 'particles')
pp.inputConnectors[0].connect(pg)
pp.par.targetpop = null_loop
pp.par.maxparticles.expr = "parent().par.Count"
pp.par.birthrate.expr = "parent().par.Emitrate*(1+3*op('modlib').module.m('beat'))"
pp.par.life.expr = "parent().par.Lifetime"
pp.par.lifevariance = 0.25
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
fr1.par.radialstrength.expr = "-parent().par.Attr1strength"   # sign: positive Attr strength attracts (verified in test)
OR1 = {'x': "parent().par.Attrorbit*math.cos(2*math.pi*" + PHX + ")", 'y': "parent().par.Attrorbit*math.sin(2*math.pi*" + PHX + ")", 'z': "0"}
OR2 = {'x': "-(" + OR1['x'] + ")", 'y': "-(" + OR1['y'] + ")", 'z': "0"}
for a in 'xyz': getattr(fr1.par, 'pos' + a).expr = f"parent().par.Attr1pos{a} + " + OR1[a]
fr2 = c.create(td.forceradialPOP, 'force_attr2')
fr2.inputConnectors[0].connect(fr1)
fr2.par.radial = True
fr2.par.falloffradius.expr = "parent().par.Attrradius"
fr2.par.radialstrength.expr = "-parent().par.Attr2strength"
for a in 'xyz': getattr(fr2.par, 'pos' + a).expr = f"parent().par.Attr2pos{a} + " + OR2[a]

nz = c.create(td.noisePOP, 'curl_noise')
nz.inputConnectors[0].connect(fr2)
nz.par.noise = False
nz.par.curl3d = True
nz.par.curl3doutputattrscope = 'PartForce'
nz.par.combineop = 'add'
nz.par.combineentity = 'curl3d'
nz.par.combineattrscope = 'PartForce'
nz.par.amp0.expr = "parent().par.Curlstrength*(1+2*op('modlib').module.m('band1'))"
nz.par.period.expr = "1.0 / max(parent().par.Curlscale, 1e-3)"
nz.par.harmon = 0
# loop-periodic curl evolution: walk a circle in the noise translate instead of running t4d forever
nz.par.t4d = 0
nz.par.tx.expr = "parent().par.Curlspeed*op('clock')['len']/6.2832*math.cos(2*math.pi*" + PHX + ")"
nz.par.ty.expr = "parent().par.Curlspeed*op('clock')['len']/6.2832*math.sin(2*math.pi*" + PHX + ")"

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

# ---------------- rendering ----------------
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
cam.par.tx.expr = "parent().par.Camdist * math.sin(math.radians(" + TX + " * parent().par.Camspin))"
cam.par.tz.expr = "parent().par.Camdist * math.cos(math.radians(" + TX + " * parent().par.Camspin))"
cam.par.ry.expr = "" + TX + " * parent().par.Camspin"
cam.par.ty = 0

r = c.create(td.renderTOP, 'render')
r.par.camera = cam; r.par.geometry = geo; r.par.lights = ''
r.par.outputresolution = 'custom'
r.par.resolutionw.expr = "parent().par.Resolutionw"; r.par.resolutionh.expr = "parent().par.Resolutionh"
r.par.bgcolorr = 0; r.par.bgcolorg = 0; r.par.bgcolorb = 0; r.par.bgcolora = 1
r.par.format = 'rgba16float'

o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(r)
pt = c.create(td.poptoTOP, 'popto')
pt.par.pop = null_loop
pt.par.format = 'rgba32float'
o2 = c.create(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(pt)
op_out = c.create(td.nullPOP, 'out_pop'); op_out.inputConnectors[0].connect(null_loop)

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

c.op('out1').comment = 'render'
c.op('out2').comment = 'particles'
c.op('out_pop').comment = 'particles'
retro(c, accmode=0, gain=1.0)
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = o1
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
