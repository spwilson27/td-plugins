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

NAME = 'GEN_fluid_2d'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

bld = op('/').op('build') or op('/').create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t
def glsl(name, fname, inputs=(), vecs=(), passes=None, fmt='rgba32float'):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = text(name + '_glsl', rd(fname))
    g.par.format = fmt
    g.par.outputresolution = 'custom'
    g.par.resolutionw.expr = "parent().par.Resolutionw"
    g.par.resolutionh.expr = "parent().par.Resolutionh"
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = e
    if passes: g.par.npasses.expr = passes
    return g
def V(name, par): return (name, [par if par.startswith('parent') or par[0].isdigit() or par.startswith('absTime') else f"parent().par.{par}"])

def addf(page, name, label, d, lo=None, hi=None, nlo=None, nhi=None):
    q = page.appendFloat(name, label=label)[0]
    q.default = d; q.val = d
    if lo is not None: q.min = lo; q.clampMin = True
    if hi is not None: q.max = hi; q.clampMax = True
    if nlo is not None: q.normMin = nlo
    if nhi is not None: q.normMax = nhi
    return q

# ---------------- custom pars ----------------
p = c.appendCustomPage('Controls')
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')
q = p.appendWH('Resolution', label='Resolution'); q[0].default = q[0].val = 1280; q[1].default = q[1].val = 720
q[0].min = q[1].min = 16; q[0].clampMin = q[1].clampMin = True
addf(p, 'Speed', 'Speed', 1.0, 0, 4, 0, 2)
q = p.appendInt('Iterations', label='Pressure Iterations')[0]; q.default = q.val = 20; q.min = 1; q.max = 200; q.normMax = 60
addf(p, 'Vorticity', 'Vorticity', 0.3, 0, 5, 0, 1.5)
addf(p, 'Veldissipation', 'Velocity Dissipation', 0.003, 0, 0.5, 0, 0.05)
addf(p, 'Dyedissipation', 'Dye Dissipation', 0.015, 0, 0.5, 0, 0.1)

p = c.appendCustomPage('Emitter')
q = p.appendInt('Emitters', label='Emitters')[0]; q.default = q.val = 3; q.min = 0; q.max = 6
addf(p, 'Splatsize', 'Splat Size', 0.05, 0.002, 0.5, 0.01, 0.2)
addf(p, 'Force', 'Force', 0.8, 0, 50, 0, 6)
addf(p, 'Density', 'Dye Amount', 0.04, 0, 5, 0, 1)
addf(p, 'Emitterspeed', 'Emitter Speed', 1.0, 0, 10, 0, 4)
addf(p, 'Huespeed', 'Hue Speed', 0.05, 0, 2, 0, 0.5)

p = c.appendCustomPage('Input')
addf(p, 'Inputdensity', 'Input Density', 0.5, 0, 20, 0, 4)
addf(p, 'Inputvelocity', 'Input Velocity', 1.0, 0, 20, 0, 4)

p = c.appendCustomPage('Render')
addf(p, 'Exposure', 'Exposure', 1.5, 0, 20, 0, 6)
addf(p, 'Saturation', 'Saturation', 1.2, 0, 3, 0, 2)
q = p.appendRGB('Background', label='Background')
for par, v in zip(q, (0.0, 0.0, 0.02)): par.default = v; par.val = v

# ---------------- network ----------------
inn = c.create(td.inTOP, 'in1')
zero = c.create(td.constantTOP, 'zero')
zero.par.format = 'rgba32float'
for a in ('colorr', 'colorg', 'colorb'): setattr(zero.par, a, 0)
zero.par.alpha = 1
zero.par.outputresolution = 'custom'
zero.par.resolutionw.expr = "parent().par.Resolutionw"; zero.par.resolutionh.expr = "parent().par.Resolutionh"

def fbk(name):
    f = c.create(td.feedbackTOP, name); f.par.format = 'rgba32float'
    f.inputConnectors[0].connect(zero); return f
fbV, fbP, fbD = fbk('fb_vel'), fbk('fb_pressure'), fbk('fb_dye')

DT = ('uDt', ["parent().par.Speed * parent().par.Play"])
ASP = ('uAspect', ["parent().par.Resolutionw / parent().par.Resolutionh"])
TIME = ('uPh', [PHX])
EMC = ('uEmitCyc', ["math.floor(parent().par.Emitterspeed+0.5)"])
HAS = ('uHasIn', ["1 if len(parent().inputConnectors[0].connections) else 0"])
RS = ('uResScale', ["parent().par.Resolutionh / 720.0"])

curl = glsl('curl', 'curl.glsl', inputs=[fbV])
vadv = glsl('vel_adv', 'vel_adv.glsl', inputs=[fbV, curl, inn], vecs=[
    DT, V('uVelDiss', 'Veldissipation'), V('uVort', 'Vorticity'), TIME, ASP, HAS, V('uInVel', 'Inputvelocity'),
    V('uEmitters', 'Emitters'), V('uSplatSize', 'Splatsize'), ('uForce', ["parent().par.Force*(1+3*"+MOD('beat')+")"]), EMC, RS])
div = glsl('divergence', 'div.glsl', inputs=[vadv])
jac = glsl('jacobi', 'jacobi.glsl', inputs=[fbP, div], passes="max(1, int(parent().par.Iterations))")
pnull = c.create(td.nullTOP, 'pressure'); pnull.par.format = 'rgba32float'; pnull.inputConnectors[0].connect(jac)
fbP.par.top = pnull
proj = glsl('project', 'project.glsl', inputs=[vadv, pnull])
vel = c.create(td.nullTOP, 'velocity'); vel.par.format = 'rgba32float'; vel.inputConnectors[0].connect(proj)
fbV.par.top = vel
dadv = glsl('dye_adv', 'dye_adv.glsl', inputs=[fbD, vel, inn], vecs=[
    DT, V('uDyeDiss', 'Dyedissipation'), TIME, ASP, HAS, V('uInDens', 'Inputdensity'),
    V('uEmitters', 'Emitters'), V('uSplatSize', 'Splatsize'), ('uDensity', ["parent().par.Density*(1+2*"+MOD('band1')+")"]),
    EMC, ('uHueCyc', ["(max(1, math.floor(parent().par.Huespeed*op('clock')['len']+0.5)) if parent().par.Huespeed>0 else 0)"])])
dye = c.create(td.nullTOP, 'dye'); dye.par.format = 'rgba32float'; dye.inputConnectors[0].connect(dadv)
fbD.par.top = dye
col = glsl('color', 'color.glsl', fmt='rgba8fixed', inputs=[dye], vecs=[
    V('uExposure', 'Exposure'), V('uSat', 'Saturation'),
    ('uBg', ["parent().par.Backgroundr", "parent().par.Backgroundg", "parent().par.Backgroundb"])])
o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(col)
o1.comment = 'dye'
o2 = c.create(td.nullTOP, 'out2'); o2.comment = 'velocity'; o2.par.format = 'rgba32float'; o2.inputConnectors[0].connect(vel)

# ---------------- callbacks ----------------
pe = c.create(td.parameterexecuteDAT, 'parexec')
pe.par.op = '..'; pe.par.pars = 'Reset'; pe.par.valuechange = False; pe.par.onpulse = True
pe.par.custom = True; pe.par.builtin = False; pe.par.active = True
pe.text = '''
def onPulse(par):
    if par.name == 'Reset':
        for n in ('fb_vel', 'fb_pressure', 'fb_dye'):
            par.owner.op(n).par.resetpulse.pulse()
'''

retro(c, accmode=0, gain=3.0)
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = o1
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
