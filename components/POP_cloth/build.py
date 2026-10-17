# POP_cloth: simulate the input mesh (any topology with polygons) as cloth on the GPU.
#   in1 (POP) -> Neighbor POP (edge connectivity) -> state attrs -> Feedback POP loop
#   [Verlet GLSL POP -> N x Jacobi edge-constraint passes] -> Normal POP -> out1 (POP)
# A demo Grid POP (inside the gated `demo` COMP) is used when in1 is not connected.
# An internal `preview` TOP renders the result for the node viewer.
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
NAME = 'POP_cloth'
D = os.path.join(ROOT, 'components', NAME)
OUT = os.path.join(ROOT, 'tox', '_raw', NAME + '.tox')
P = 'parent().par.'

def rd(f): return open(os.path.join(D, f)).read()
root = op('/build') or op('/').create(td.baseCOMP, 'build')
old = root.op(NAME)
if old: old.destroy()
c = root.create(td.baseCOMP, NAME)

MODLIB = '''# modulation helper: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else default
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''
def MOD(n): return "op('modlib').module.m('%s')" % n

def mk(t, name, **kw):
    o = c.create(t, name)
    for k, v in kw.items(): o.par[k] = v
    return o
def dat(name, text):
    d = c.create(td.textDAT, name); d.text = text; return d
def vec(o, i, name, *vals, typ='vec4'):
    o.par['vec%dname' % i] = name
    if typ: o.par['vec%dtype' % i] = typ
    for k, v in zip('xyzw', vals):
        p = o.par['vec%dvalue%s' % (i, k)]
        if isinstance(v, str): p.expr = v
        else: p.val = v
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False):
    p = (page.appendInt if isint else page.appendFloat)(name, label=label)[0]
    p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
def menu(page, name, label, names, labels, default=0):
    p = page.appendMenu(name, label=label)[0]
    p.menuNames = names; p.menuLabels = labels; p.val = names[default]; p.default = names[default]
def trip(page, name, label, vals, lo=-10, hi=10, rgb=False):
    pg = (page.appendRGB if rgb else page.appendXYZ)(name, label=label)
    for p, v in zip(pg, vals):
        p.default = v; p.val = v
        if not rgb: p.min = lo; p.max = hi; p.normMin = lo; p.normMax = hi

# ---------------------------------------------------------------- parameters
Pg = c.appendCustomPage('Controls')
menu(Pg, 'Pinmode', 'Pin Points', ['top', 'attribute', 'group', 'none'],
     ['Top Row (highest Y)', 'Pin Attribute (>0.5)', 'Point Group', 'None'])
p = Pg.appendStr('Pingroup', label='Pin Group')[0]; p.default = 'pinned'; p.val = 'pinned'
num(Pg, 'Pinthickness', 'Top Row Thickness', 0.005, 0.0, 0.5)
num(Pg, 'Gravity', 'Gravity', 9.8, -30, 30, False, False)
num(Pg, 'Wind', 'Wind', 4.0, 0, 30, True, False)
trip(Pg, 'Winddir', 'Wind Dir', (0, 0, -1))
num(Pg, 'Turbulence', 'Turbulence', 0.8, 0, 3, True, False)
num(Pg, 'Damping', 'Damping', 0.01, 0, 0.2)
num(Pg, 'Stiffness', 'Stiffness', 1.0, 0.05, 1.0)
num(Pg, 'Iterations', 'Iterations', 32, 1, 128, chi=False, isint=True)
Pg.appendToggle('Collider', label='Sphere Collider'); c.par.Collider = True; c.par.Collider.default = True
trip(Pg, 'Spherepos', 'Sphere Pos', (0, -0.55, -0.35))
num(Pg, 'Sphereradius', 'Sphere Radius', 0.6, 0.05, 2, chi=False)
num(Pg, 'Speed', 'Speed', 1.0, 0.1, 2.0, chi=False)
num(Pg, 'Modgain', 'Modulation Gain', 1.0, 0, 3)
Pg.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
Pg.appendPulse('Reset', label='Reset')
S = c.appendCustomPage('Sim')
num(S, 'Maxneighbors', 'Max Neighbours', 8, 4, 16, isint=True)
num(S, 'Demogrid', 'Demo Grid (NxN)', 64, 8, 256, isint=True)
num(S, 'Demosize', 'Demo Cloth Size', 2.0, 0.2, 6, chi=False)
R = c.appendCustomPage('Look')
trip(R, 'Color1', 'Color A', (0.85, 0.2, 0.25), rgb=True)
trip(R, 'Color2', 'Color B', (0.95, 0.9, 0.8), rgb=True)
num(R, 'Checker', 'Checker Cells', 16, 1, 128, isint=True)
trip(R, 'Spherecolor', 'Sphere Color', (0.25, 0.45, 0.8), rgb=True)
num(R, 'Camangle', 'Cam Orbit (deg)', 28, -180, 180, False, False)
num(R, 'Camdist', 'Cam Distance', 7.5, 1, 30, chi=False)
num(R, 'Camheight', 'Cam Height', 1.2, -5, 5, False, False)
trip(R, 'Background', 'Background', (0.05, 0.06, 0.09), rgb=True)

# ---------------------------------------------------------------- inputs, demo, modulation
inp = mk(td.inPOP, 'in1')
inm = mk(td.inCHOP, 'in2')
dat('modlib', MODLIB)

demo = mk(td.baseCOMP, 'demo')
dg = demo.create(td.gridPOP, 'grid')
dg.par.surftype = 'triangles'
dg.par.cols.expr = 'parent(2).par.Demogrid'; dg.par.rows.expr = 'parent(2).par.Demogrid'
dg.par.sizex.expr = 'parent(2).par.Demosize'; dg.par.sizey.expr = 'parent(2).par.Demosize'
dg.par.ty.expr = '0.9 - parent(2).par.Demosize / 2'
dg.par.texture = 'point'
do = demo.create(td.outPOP, 'out1'); do.inputConnectors[0].connect(dg)

src = mk(td.switchPOP, 'src')
src.inputConnectors[0].connect(demo.outputConnectors[0])
src.inputConnectors[1].connect(inp)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
src.par.lengthmismatchnotif = 'ignore'

# ---------------------------------------------------------------- mesh connectivity + pins
nb = mk(td.neighborPOP, 'neighbors'); nb.inputConnectors[0].connect(src)
nb.par.nebrtype = 'connected'; nb.par.maxneighbors.expr = P + 'Maxneighbors'
nb.par.nebrs = True; nb.par.numnebrs = True

def attr1(o, name, val):
    o.par.attr0name = 'custom'; o.par.attr0customname = name
    o.par.attr0type = 'float'; o.par.attr0numcomps = '1'; o.par.attr0value0 = val
pinA = mk(td.attributePOP, 'pin_attr'); pinA.inputConnectors[0].connect(nb)
pinA.par.attr = 1; attr1(pinA, 'Pin', 0.0)
pinA.par.overrideifexists = False; pinA.par.notificationifexists = 'ignore'
pinG = mk(td.attributePOP, 'pin_group'); pinG.inputConnectors[0].connect(pinA)
pinG.par.attr = 1; attr1(pinG, 'Pin', 1.0)
pinG.par.overrideifexists = True; pinG.par.notificationifexists = 'ignore'
pinG.par.group.expr = P + 'Pingroup'
pinG.par.bypass.expr = "0 if parent().par.Pinmode == 'group' else 1"

an = mk(td.analyzePOP, 'bounds'); an.inputConnectors[0].connect(src)
an.par.inputattrs = 'P'; an.par.avg = False; an.par.min = True; an.par.max = True

init = mk(td.glslPOP, 'init'); init.inputConnectors[0].connect(pinG); init.inputConnectors[1].connect(an)
init.par.computedat = dat('init_code', rd('init.glsl'))
init.par.outputattrs = 'Pin'
init.seq.attr.numBlocks = 2
for i, n in enumerate(('RestP', 'PrevP')):
    init.par['attr%dname' % i] = 'custom'; init.par['attr%dcustomname' % i] = n
    init.par['attr%dtype' % i] = 'float'; init.par['attr%dnumcomps' % i] = '3'
init.seq.vec.numBlocks = 1
vec(init, 0, 'uI', "parent().par.Pinmode.menuIndex if parent().par.Pinmode.menuIndex < 2 else (1 if parent().par.Pinmode == 'group' else 2)", P + 'Pinthickness', 0, 0)

# ---------------------------------------------------------------- simulation loop
fb = mk(td.feedbackPOP, 'fb'); fb.inputConnectors[0].connect(init)

SX = [P + "Spherepos%s" % a for a in 'xyz'] + [P + "Sphereradius if %sCollider else 0" % P]
integ = mk(td.glslPOP, 'integrate'); integ.inputConnectors[0].connect(fb); integ.inputConnectors[1].connect(init)
integ.par.computedat = dat('integrate_code', rd('integrate.glsl'))
integ.par.outputattrs = 'P PrevP'
integ.par.simplexnoise = 'performance'
integ.seq.vec.numBlocks = 5
WIND = "%sWind*(1+%sModgain*(3*%s+2*%s))" % (P, P, MOD('band1'), MOD('beat'))
vec(integ, 0, 'uG', 0, "-%sGravity*(1-0.8*min(1,%sModgain*%s))" % (P, P, MOD('band3')), 0, P + 'Damping')
vec(integ, 1, 'uW', WIND, "%sTurbulence+%sModgain*1.5*%s" % (P, P, MOD('band2')), "absTime.seconds", 1.3)
vec(integ, 2, 'uD', P + 'Winddirx', P + 'Winddiry', P + 'Winddirz', "1 if %sPlay else 0" % P)
vec(integ, 3, 'uS', *SX)
vec(integ, 4, 'uF', "(%sSpeed / 60.0) ** 2" % P, 0, 0, 0)

cons = mk(td.glslPOP, 'constraints'); cons.inputConnectors[0].connect(integ)
cons.par.computedat = dat('constraint_code', rd('constraint.glsl'))
cons.par.outputattrs = 'P'
cons.par.npasses.expr = P + 'Iterations'
cons.par.prevpassoutput = True
cons.seq.vec.numBlocks = 2
vec(cons, 0, 'uC', P + 'Stiffness', P + 'Maxneighbors', 0, 0)
vec(cons, 1, 'uS', *SX)

sim = mk(td.nullPOP, 'sim'); sim.inputConnectors[0].connect(cons)
fb.par.targetpop = sim

# ---------------------------------------------------------------- output
nrm = mk(td.normalPOP, 'normals'); nrm.inputConnectors[0].connect(sim)
nrm.par.nml = 'alwayscompute'
clean = mk(td.attributePOP, 'cleanup'); clean.inputConnectors[0].connect(nrm)
clean.par.deletepoint = 'RestP PrevP Pin Nebr NumNebrs'
o1 = mk(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(clean)
o1.comment = 'cloth mesh'

# ---------------------------------------------------------------- reset
pe = c.create(td.parameterexecuteDAT, 'reset_exec')
pe.par.op = c; pe.par.pars = 'Reset'; pe.par.valuechange = False; pe.par.onpulse = True
pe.text = ("def onPulse(par):\n"
           "    f = parent().op('fb')\n"
           "    f.par.initializepulse.pulse()\n"
           "    f.par.startpulse.pulse()\n"
           "    return\n")

# ---------------------------------------------------------------- preview render (internal, not an output)
geo = mk(td.geometryCOMP, 'cloth_geo')
for ch in list(geo.children): ch.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = o1
sel.display = True; sel.render = True
chk = mk(td.glslTOP, 'checker', outputresolution='custom', format='rgba8fixed')
chk.par.resolutionw = 512; chk.par.resolutionh = 512
chk.par.pixeldat = dat('checker_code', rd('checker.glsl'))
chk.seq.vec.numBlocks = 3
vec(chk, 0, 'uA', *[P + 'Color1' + a for a in 'rgb'], 1, typ=None)
vec(chk, 1, 'uB', *[P + 'Color2' + a for a in 'rgb'], 1, typ=None)
vec(chk, 2, 'uC', P + 'Checker', 0, 0, 0, typ=None)
cm = mk(td.phongMAT, 'cloth_mat')
cm.par.colormap = chk
geo.par.material = cm

sgeo = mk(td.geometryCOMP, 'sphere_geo')
for ch in list(sgeo.children): ch.destroy()
sp = sgeo.create(td.spherePOP, 'sphere'); sp.par.surftype = 'triangles'; sp.par.normal = True
sp.par.radx = sp.par.rady = sp.par.radz = 1
sp.par.cols = 48; sp.par.rows = 24
sp.display = True; sp.render = True
sgeo.par.tx.expr = P + 'Spherepos' + 'x'; sgeo.par.ty.expr = P + 'Spherepos' + 'y'; sgeo.par.tz.expr = P + 'Spherepos' + 'z'
for a in 'xyz':
    sgeo.par['s' + a].expr = "(%sSphereradius if %sCollider else 0.0001)" % (P, P)
smat = mk(td.phongMAT, 'sphere_mat')
for a in 'rgb':
    smat.par['diff' + a].expr = P + 'Spherecolor' + a
sgeo.par.material = smat

cam = mk(td.cameraCOMP, 'cam', fov=40)
cam.par.tx.expr = P + "Camdist * math.sin(math.radians(%sCamangle))" % P
cam.par.tz.expr = P + "Camdist * math.cos(math.radians(%sCamangle))" % P
cam.par.ty.expr = P + "Camheight"
tgt = mk(td.nullCOMP, 'target', ty=-0.2)
cam.par.lookat = tgt
lt = mk(td.lightCOMP, 'light', tx=3, ty=5, tz=6)
lt.par.lookat = tgt
rend = mk(td.renderTOP, 'preview', outputresolution='custom', format='rgba16float')
rend.par.resolutionw = 640; rend.par.resolutionh = 360
rend.par.camera = cam; rend.par.geometry = geo.name + ' ' + sgeo.name; rend.par.lights = lt
rend.par.bgcolorr.expr = P + "Backgroundr"; rend.par.bgcolorg.expr = P + "Backgroundg"; rend.par.bgcolorb.expr = P + "Backgroundb"
rend.par.bgcolora = 1
rend.par.antialias = 'aa4'
c.save(OUT); print('saved')

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300].replace('\n',' | '))
