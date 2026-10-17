import os, td

NAME = 'TOP_fluid'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else default
def _ins():
    return [o for o in parent().children if o.OPType == 'inCHOP']
def m(n, d=0.0):
    i = _ins()
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)

bld = op('/').op('build') or op('/').create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t
SIMW = "(parent().par.Resolutionw if parent().par.Resolutionmode=='custom' else op('src').width)"
SIMH = "(parent().par.Resolutionh if parent().par.Resolutionmode=='custom' else op('src').height)"
def setres(o):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = SIMW; o.par.resolutionh.expr = SIMH
def glsl(name, fname, inputs=(), vecs=(), passes=None, fmt='rgba32float'):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = text(name + '_glsl', rd(fname))
    g.par.format = fmt
    setres(g)
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = e
    if passes: g.par.npasses.expr = passes
    return g
def V(name, par): return (name, [par if par.startswith(('parent', 'op(')) else f"parent().par.{par}"])

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
addf(p, 'Mix', 'Mix', 1.0, 0, 1, 0, 1)
q = p.appendToggle('Bypass', label='Bypass')[0]; q.default = 0; q.val = 0
q = p.appendMenu('Resolutionmode', label='Resolution Mode')[0]
q.menuNames = ['input', 'custom']; q.menuLabels = ['Input', 'Custom']; q.default = 'input'; q.val = 'input'
q = p.appendWH('Resolution', label='Resolution'); q[0].default = q[0].val = 1280; q[1].default = q[1].val = 720
q[0].min = q[1].min = 16; q[0].clampMin = q[1].clampMin = True
q = p.appendMenu('Dyesource', label='Dye Source')[0]
q.menuNames = ['inject', 'seed']; q.menuLabels = ['Inject continuously', 'Seed on Reset only']; q.default = 'inject'; q.val = 'inject'
addf(p, 'Injectrate', 'Inject Rate', 0.02, 0, 1, 0, 0.3)
addf(p, 'Speed', 'Speed', 1.0, 0, 4, 0, 2)
q = p.appendInt('Iterations', label='Pressure Iterations')[0]; q.default = q.val = 20; q.min = 1; q.max = 200; q.normMax = 60
addf(p, 'Vorticity', 'Vorticity', 0.5, 0, 5, 0, 1.5)
addf(p, 'Veldissipation', 'Velocity Dissipation', 0.003, 0, 0.5, 0, 0.05)
addf(p, 'Dyedissipation', 'Dye Dissipation', 0.0, 0, 0.5, 0, 0.1)

p = c.appendCustomPage('Forces')
addf(p, 'Forcein', 'In2 Force', 1.0, 0, 50, 0, 10)
addf(p, 'Edgeforce', 'Edge Force', 0.3, 0, 20, 0, 4)
q = p.appendInt('Emitters', label='Stir Emitters')[0]; q.default = q.val = 2; q.min = 0; q.max = 6
addf(p, 'Splatsize', 'Splat Size', 0.06, 0.002, 0.5, 0.01, 0.2)
addf(p, 'Force', 'Stir Force', 0.8, 0, 50, 0, 6)
addf(p, 'Emitterspeed', 'Stir Speed', 0.12, 0, 2, 0, 0.6)

# ---------------- network ----------------
inn = c.create(td.inTOP, 'in1')
in2 = c.create(td.inTOP, 'in2')
inm = c.create(td.inCHOP, 'in3')
ml = c.create(td.textDAT, 'modlib'); ml.text = MODLIB

# demo (preview only): colourful noise + text. Gated by the switch below.
demo = c.create(td.baseCOMP, 'demo')
dn = demo.create(td.noiseTOP, 'noise'); dn.par.outputresolution = 'custom'; dn.par.resolutionw = 1280; dn.par.resolutionh = 720
dn.par.mono = False; dn.par.period = 0.35; dn.par.harmon = 1
dn.par.tz.expr = 'absTime.seconds * 0.05'
dt_ = demo.create(td.textTOP, 'text'); dt_.par.text = 'FLUID'
dt_.par.outputresolution = 'custom'; dt_.par.resolutionw = 1280; dt_.par.resolutionh = 720
dt_.par.fontsizex = 260; dt_.par.fontcolorr = dt_.par.fontcolorg = dt_.par.fontcolorb = 1
dt_.par.bgcolorr = dt_.par.bgcolorg = dt_.par.bgcolorb = 0; dt_.par.bgalpha = 0
dco = demo.create(td.compositeTOP, 'over'); dco.par.operand = 'over'
dco.inputConnectors[0].connect(dt_); dco.inputConnectors[1].connect(dn)
dout = demo.create(td.outTOP, 'dout'); dout.inputConnectors[0].connect(dco)

src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(demo.outputConnectors[0])
src.inputConnectors[0].connect(demo.outputConnectors[0])
src.inputConnectors[1].connect(inn)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

zero = c.create(td.constantTOP, 'zero')
zero.par.format = 'rgba32float'
for a in ('colorr', 'colorg', 'colorb'): setattr(zero.par, a, 0)
zero.par.alpha = 1
setres(zero)
seed = c.create(td.nullTOP, 'dye_seed'); seed.par.format = 'rgba32float'
setres(seed); seed.inputConnectors[0].connect(src)

def fbk(name, init):
    f = c.create(td.feedbackTOP, name); f.par.format = 'rgba32float'
    f.inputConnectors[0].connect(init); return f
fbV, fbP, fbD = fbk('fb_vel', zero), fbk('fb_pressure', zero), fbk('fb_dye', seed)

DT = ('uDt', ["parent().par.Speed * parent().par.Play"])
ASP = ('uAspect', [f"{SIMW} / {SIMH}"])
RS = ('uResScale', [f"{SIMH} / 720.0"])

force = glsl('force', 'force.glsl', inputs=[src, in2], vecs=[
    V('uEdge', 'Edgeforce'), V('uForceIn', 'Forcein'),
    ('uHas2', ["1 if len(parent().inputConnectors[1].connections) else 0"]), RS])
curl = glsl('curl', 'curl.glsl', inputs=[fbV])
vadv = glsl('vel_adv', 'vel_adv.glsl', inputs=[fbV, curl, force], vecs=[
    DT, V('uVelDiss', 'Veldissipation'), ('uVort', ["parent().par.Vorticity*(1+2*" + MOD('band1') + ")"]),
    ('uT', ["absTime.seconds * parent().par.Emitterspeed"]), ASP,
    V('uEmitters', 'Emitters'), V('uSplatSize', 'Splatsize'),
    ('uForce', ["parent().par.Force*(1+3*" + MOD('beat') + ")"]), RS])
div = glsl('divergence', 'div.glsl', inputs=[vadv])
jac = glsl('jacobi', 'jacobi.glsl', inputs=[fbP, div], passes="max(1, int(parent().par.Iterations))")
pnull = c.create(td.nullTOP, 'pressure'); pnull.par.format = 'rgba32float'; pnull.inputConnectors[0].connect(jac)
fbP.par.top = pnull
proj = glsl('project', 'project.glsl', inputs=[vadv, pnull])
vel = c.create(td.nullTOP, 'velocity'); vel.par.format = 'rgba32float'; vel.inputConnectors[0].connect(proj)
fbV.par.top = vel
dadv = glsl('dye_adv', 'dye_adv.glsl', inputs=[fbD, vel, src], vecs=[
    DT, V('uDyeDiss', 'Dyedissipation'),
    ('uInject', ["parent().par.Injectrate if parent().par.Dyesource=='inject' else 0"])])
dye = c.create(td.nullTOP, 'dye'); dye.par.format = 'rgba32float'; dye.inputConnectors[0].connect(dadv)
fbD.par.top = dye
mixg = glsl('mixout', 'mix.glsl', fmt='rgba16float', inputs=[dye, src], vecs=[V('uMix', 'Mix')])
byp = c.create(td.switchTOP, 'bypass')
byp.inputConnectors[0].connect(mixg); byp.inputConnectors[0].connect(mixg)
byp.inputConnectors[1].connect(src)
byp.par.index.expr = "parent().par.Bypass"
o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(byp); o1.comment = 'smeared image'
o2 = c.create(td.nullTOP, 'out2'); o2.comment = 'velocity'; o2.par.format = 'rgba32float'; o2.inputConnectors[0].connect(vel)
o3 = c.create(td.nullTOP, 'out3'); o3.comment = 'dye field'; o3.par.format = 'rgba32float'; o3.inputConnectors[0].connect(dye)

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
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 7); o.nodeY = -150 * (i // 7)
c.par.opviewer = o1
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
