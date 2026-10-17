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

NAME = 'GEN_verlet_cloth'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')

def rd(f): return open(D + f).read()
root = op('/build') or op('/').create(td.baseCOMP, 'build')
old = root.op(NAME)
if old: old.destroy()
c = root.create(td.baseCOMP, NAME)

def mk(t, name, **kw):
    o = c.create(t, name)
    for k, v in kw.items(): o.par[k] = v
    return o
def dat(name, text):
    d = c.create(td.textDAT, name); d.text = text; return d
def vec(o, i, name, *exprs):
    o.par['vec%dname' % i] = name
    for k, e in zip('xyzw', exprs): o.par['vec%dvalue%s' % (i, k)].expr = e
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False):
    pg = (page.appendInt if isint else page.appendFloat)(name, label=label)
    p = pg[0]; p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
def menu(page, name, label, names, labels, default=0):
    p = page.appendMenu(name, label=label)[0]; p.menuNames = names; p.menuLabels = labels; p.val = names[default]; p.default = names[default]
def trip(page, name, label, vals, lo=-10, hi=10, rgb=False):
    pg = (page.appendRGB if rgb else page.appendXYZ)(name, label=label)
    for p, v in zip(pg, vals):
        p.default = v; p.val = v
        if not rgb: p.min = lo; p.max = hi; p.normMin = lo; p.normMax = hi
def res(page, name, label, w, h):
    pg = page.appendWH(name, label=label)
    for p, v in zip(pg, (w, h)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096

# ---- parameters
P = c.appendCustomPage('Controls')
menu(P, 'Pinmode', 'Pinning', ['top', 'corners', 'none'], ['Top Row', 'Corners', 'None'])
num(P, 'Gravity', 'Gravity', 9.8, -30, 30, False, False)
num(P, 'Wind', 'Wind', 4.0, 0, 30, True, False)
trip(P, 'Winddir', 'Wind Dir', (0, 0, -1))
num(P, 'Turbulence', 'Turbulence', 0.8, 0, 3, True, False)
num(P, 'Damping', 'Damping', 0.01, 0, 0.2)
num(P, 'Stiffness', 'Stiffness', 1.0, 0.05, 1.0)
num(P, 'Iterations', 'Iterations', 32, 1, 64, chi=False, isint=True)
P.appendToggle('Collider', label='Sphere Collider'); c.par.Collider = True; c.par.Collider.default = True
trip(P, 'Spherepos', 'Sphere Pos', (0, -0.55, -0.35))
num(P, 'Sphereradius', 'Sphere Radius', 0.6, 0.05, 2, chi=False)
P.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
P.appendPulse('Reset', label='Reset')
S = c.appendCustomPage('Sim')
res(S, 'Resolution', 'Resolution', 1280, 720)
num(S, 'Gridsize', 'Grid Size (NxN)', 64, 8, 256, isint=True)
num(S, 'Clothsize', 'Cloth Size', 2.0, 0.2, 6, chi=False)
num(S, 'Speed', 'Speed', 1.0, 0.1, 2.0, chi=False)
R = c.appendCustomPage('Render')
trip(R, 'Color1', 'Color A', (0.85, 0.2, 0.25), rgb=True)
trip(R, 'Color2', 'Color B', (0.95, 0.9, 0.8), rgb=True)
num(R, 'Checker', 'Checker Cells', 16, 1, 128, isint=True)
trip(R, 'Spherecolor', 'Sphere Color', (0.25, 0.45, 0.8), rgb=True)
trip(R, 'Lightdir', 'Light Dir', (0.5, 0.8, 0.9), lo=-1, hi=1)
num(R, 'Camangle', 'Cam Orbit (deg)', 0, -180, 180, False, False)
num(R, 'Camdist', 'Cam Distance', 8.0, 1, 20, chi=False)
num(R, 'Camheight', 'Cam Height', 0.3, -5, 5, False, False)
trip(R, 'Background', 'Background', (0.05, 0.06, 0.09), rgb=True)

N = "parent().par.Gridsize"
def sq(o):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = N; o.par.resolutionh.expr = N
    o.par.format = 'rgba32float'
    o.par.inputfiltertype = 'nearest'

# ---- simulation
rest = mk(td.glslTOP, 'rest'); sq(rest)
rest.par.pixeldat = dat('rest_pix', rd('rest.glsl'))
vec(rest, 0, 'uR', N, "parent().par.Clothsize", "parent().par.Pinmode.menuIndex", "0.9")

zero = mk(td.constantTOP, 'zero', outputresolution='custom', format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
zero.par.resolutionw.expr = N; zero.par.resolutionh.expr = N
fbP = mk(td.feedbackTOP, 'fb_pos'); sq(fbP)
fbV = mk(td.feedbackTOP, 'fb_prev'); sq(fbV)
fbP.inputConnectors[0].connect(zero); fbV.inputConnectors[0].connect(zero)
fbP.par.reset.expr = "parent().par.Reset"; fbV.par.reset.expr = "parent().par.Reset"

integ = mk(td.glslTOP, 'integrate'); sq(integ)
integ.par.pixeldat = dat('integrate_pix', rd('integrate.glsl'))
integ.par.simplexnoise = 'performance'
integ.inputConnectors[0].connect(fbP); integ.inputConnectors[1].connect(fbV); integ.inputConnectors[2].connect(rest)
sx = ["parent().par.Spherepos%s" % a for a in 'xyz'] + ["parent().par.Sphereradius if parent().par.Collider else 0"]
vec(integ, 0, 'uG', "0", "-parent().par.Gravity", "0", "parent().par.Damping")
vec(integ, 1, 'uW', "parent().par.Wind*(1+3*op('modlib').module.m('band1'))", "parent().par.Turbulence", PHX, "parent().par.Reset")
vec(integ, 2, 'uD', "parent().par.Winddirx", "parent().par.Winddiry", "parent().par.Winddirz", "1 if parent().par.Play else 0")
vec(integ, 3, 'uS', *sx)
vec(integ, 4, 'uF', "(parent().par.Speed / 60.0) ** 2")

cons = mk(td.glslTOP, 'constraints'); sq(cons)
cons.par.pixeldat = dat('constraint_pix', rd('constraint.glsl'))
cons.inputConnectors[0].connect(integ); cons.inputConnectors[1].connect(rest)
cons.par.npasses.expr = "parent().par.Iterations"
vec(cons, 0, 'uC', N, "parent().par.Clothsize", "parent().par.Stiffness", "0")
vec(cons, 1, 'uS', *sx)
fbP.par.top = cons.name
fbV.par.top = fbP.name
pos = mk(td.nullTOP, 'pos_out'); sq(pos); pos.inputConnectors[0].connect(cons)

# ---- render
geo = mk(td.geometryCOMP, 'cloth_geo')
for ch in list(geo.children): ch.destroy()
gr = geo.create(td.gridSOP, 'grid'); gr.par.rows.expr = 'parent(2).par.Gridsize'; gr.par.cols.expr = 'parent(2).par.Gridsize'; gr.par.sizex = 1; gr.par.sizey = 1
gr.par.surftype = 'triangles' if 'triangles' in gr.par.surftype.menuNames else gr.par.surftype.val
gr.par.texture = 'rowcol'
gout = geo.create(td.outSOP, 'out1'); gout.inputConnectors[0].connect(gr); gout.render = True; gout.display = True

cam = mk(td.cameraCOMP, 'cam', fov=40)
cam.par.tx.expr = "parent().par.Camdist * math.sin(math.radians(parent().par.Camangle))"
cam.par.tz.expr = "parent().par.Camdist * math.cos(math.radians(parent().par.Camangle))"
cam.par.ty.expr = "parent().par.Camheight"
tgt = mk(td.nullCOMP, 'target', ty=-0.2)
cam.par.lookat = tgt.name

mat = mk(td.glslMAT, 'cloth_mat', cullface='neither', glslversion='glsl430')
mat.par.vdat = dat('cloth_vert', rd('cloth_vert.glsl')); mat.par.pdat = dat('cloth_pix', rd('cloth_pix.glsl'))
mat.par.sampler0name = 'uPos'; mat.par.sampler0top = pos.name
vec(mat, 0, 'uN', N)
vec(mat, 1, 'uC1', *["parent().par.Color1%s" % a for a in 'rgb'])
vec(mat, 2, 'uC2', *["parent().par.Color2%s" % a for a in 'rgb'])
vec(mat, 3, 'uCam', "op('cam').par.tx", "op('cam').par.ty", "op('cam').par.tz")
vec(mat, 4, 'uLight', *["parent().par.Lightdir%s" % a for a in 'xyz'])
vec(mat, 5, 'uCheck', "parent().par.Checker")
geo.par.material = mat.name

sgeo = mk(td.geometryCOMP, 'sphere_geo')
for ch in list(sgeo.children): ch.destroy()
sp = sgeo.create(td.sphereSOP, 'sphere')
so = sgeo.create(td.outSOP, 'out1'); so.inputConnectors[0].connect(sp); so.render = True; so.display = True
smat = mk(td.glslMAT, 'sphere_mat', glslversion='glsl430')
smat.par.vdat = dat('sph_vert', rd('sph_vert.glsl')); smat.par.pdat = dat('sph_pix', rd('sph_pix.glsl'))
vec(smat, 0, 'uS', *sx)
vec(smat, 1, 'uCam', "op('cam').par.tx", "op('cam').par.ty", "op('cam').par.tz")
vec(smat, 2, 'uLight', *["parent().par.Lightdir%s" % a for a in 'xyz'])
vec(smat, 3, 'uCol', *["parent().par.Spherecolor%s" % a for a in 'rgb'])
sgeo.par.material = smat.name

rend = mk(td.renderTOP, 'render', outputresolution='custom', format='rgba16float')
rend.par.resolutionw.expr = "parent().par.Resolutionw"; rend.par.resolutionh.expr = "parent().par.Resolutionh"
rend.par.camera = cam.name; rend.par.geometry = geo.name + ' ' + sgeo.name; rend.par.lights = ''
rend.par.bgcolorr.expr = "parent().par.Backgroundr"; rend.par.bgcolorg.expr = "parent().par.Backgroundg"; rend.par.bgcolorb.expr = "parent().par.Backgroundb"
rend.par.bgcolora = 1
rend.par.antialias = 'aa4'
o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(rend)
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(pos)   # raw particle positions (rgb=xyz)
c.op('out1').comment = 'render'
c.op('out2').comment = 'positions'
retro(c, accmode=0, gain=1.0)
c.save(OUT); print('saved')
