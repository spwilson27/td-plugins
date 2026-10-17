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

NAME = 'GEN_strange_attractors'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')
PW = 512   # particle texture PW x PW (262,144 particles)

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
def rgb(page, name, label, vals):
    pg = page.appendRGB(name, label=label)
    for p, v in zip(pg, vals): p.default = v; p.val = v

AN = ['lorenz', 'aizawa', 'thomas', 'halvorsen', 'dadras']
AL = ['Lorenz', 'Aizawa', 'Thomas', 'Halvorsen', 'Dadras']
P = c.appendCustomPage('Controls')
menu(P, 'Attractor', 'Attractor A', AN, AL, 0)
menu(P, 'Attractorb', 'Attractor B', AN, AL, 1)
num(P, 'Morph', 'Morph A>B', 0.0, 0, 1)
num(P, 'Speed', 'Speed', 1.0, 0.0, 4, True, False)
num(P, 'Scale', 'Scale', 1.0, 0.1, 10, True, False)
num(P, 'Coefmod', 'Coef Animate', 0.0, 0, 1)
num(P, 'Coefspeed', 'Coef Rate', 0.3, 0, 5)
P.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
P.appendPulse('Reset', label='Reset')
R = c.appendCustomPage('Render')
num(R, 'Count', 'Particles', 80000, 1000, PW * PW, isint=True)
num(R, 'Pointsize', 'Point Size (px)', 1.2, 0.5, 8, True, False)
num(R, 'Intensity', 'Intensity', 0.35, 0.005, 2, True, False)
num(R, 'Exposure', 'Exposure', 1.0, 0.1, 10, True, False)
num(R, 'Trails', 'Trails', 0.94, 0.0, 0.995)
rgb(R, 'Color1', 'Color Slow', (0.1, 0.35, 1.0))
rgb(R, 'Color2', 'Color Fast', (1.0, 0.45, 0.15))
num(R, 'Colorspeed', 'Color Speed Scale', 40, 0.1, 500, True, False)
rgb(R, 'Background', 'Background', (0.0, 0.0, 0.015))
num(R, 'Camangle', 'Cam Angle', 0, -180, 180, False, False)
num(R, 'Orbitspeed', 'Orbit Speed (deg/s)', 12, -90, 90, False, False)
num(R, 'Camdist', 'Cam Distance', 7.0, 1, 40, True, False)
num(R, 'Camheight', 'Cam Height', 1.0, -10, 10, False, False)
S = c.appendCustomPage('Sim')
pg = S.appendWH('Resolution', label='Resolution')
for p, v in zip(pg, (1280, 720)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096
num(S, 'Substeps', 'Substeps / Frame', 6, 1, 24, isint=True)
num(S, 'Seed', 'Seed', 1, 0, 1000, isint=True)

# ---- particle state
zero = mk(td.constantTOP, 'zero', outputresolution='custom', resolutionw=PW, resolutionh=PW, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
fbS = mk(td.feedbackTOP, 'fb_state', outputresolution='custom', resolutionw=PW, resolutionh=PW, format='rgba32float')
step = mk(td.glslTOP, 'step', outputresolution='custom', resolutionw=PW, resolutionh=PW, format='rgba32float', inputfiltertype='nearest')
step.par.pixeldat = dat('step_pix', rd('step.glsl'))
fbS.inputConnectors[0].connect(zero); step.inputConnectors[0].connect(fbS); fbS.par.top = step.name
fbS.par.reset.expr = "parent().par.Reset"
vec(step, 0, 'uA', "parent().par.Attractor.menuIndex", "parent().par.Attractorb.menuIndex", "parent().par.Morph", "parent().par.Reset")
vec(step, 1, 'uB', "parent().par.Speed * (1 if parent().par.Play else 0)*(1+op('modlib').module.m('band2'))", "2*math.pi*" + PHX + "*max(1, round(parent().par.Coefspeed*op('clock')['len']/6.2832))", "parent().par.Substeps", "parent().par.Seed")
vec(step, 2, 'uC', "parent().par.Coefmod + 0.5*op('modlib').module.m('band1')", "parent().par.Coefspeed")
pstate = mk(td.nullTOP, 'particles'); pstate.inputConnectors[0].connect(step)

# ---- render
geo = mk(td.geometryCOMP, 'pts_geo')
for ch in list(geo.children): ch.destroy()
q = geo.create(td.gridSOP, 'quad'); q.par.rows = 2; q.par.cols = 2; q.par.sizex = 1; q.par.sizey = 1
go = geo.create(td.outSOP, 'out1'); go.inputConnectors[0].connect(q); go.render = True; go.display = True
geo.par.instancing = True; geo.par.instancecountmode = 'manual'; geo.par.numinstances = PW * PW
mat = mk(td.glslMAT, 'pts_mat', blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False, cullface='neither', glslversion='glsl430')
mat.par.vdat = dat('pts_vert', rd('pvert.glsl')); mat.par.pdat = dat('pts_pix', rd('ppix.glsl'))
mat.par.sampler0name = 'uPos'; mat.par.sampler0top = pstate.name
mat.par.sampler0filter = 'nearest'
vec(mat, 0, 'uCount', "parent().par.Count")
vec(mat, 1, 'uW', str(PW))
vec(mat, 2, 'uView', "parent().par.Scale", "parent().par.Pointsize", "parent().par.Colorspeed", "parent().par.Intensity")
vec(mat, 3, 'uPx', "2.0/parent().par.Resolutionw", "2.0/parent().par.Resolutionh")
vec(mat, 4, 'uC1', *["parent().par.Color1%s" % a for a in 'rgb'])
vec(mat, 5, 'uC2', *["parent().par.Color2%s" % a for a in 'rgb'])
geo.par.material = mat.name
cam = mk(td.cameraCOMP, 'cam', fov=45)
ang = "math.radians(parent().par.Camangle + " + TX + " * parent().par.Orbitspeed)"
cam.par.tx.expr = "parent().par.Camdist * math.sin(%s)" % ang
cam.par.tz.expr = "parent().par.Camdist * math.cos(%s)" % ang
cam.par.ty.expr = "parent().par.Camheight"
tgt = mk(td.nullCOMP, 'target'); cam.par.lookat = tgt.name
rend = mk(td.renderTOP, 'render', outputresolution='custom', format='rgba16float')
rend.par.resolutionw.expr = "parent().par.Resolutionw"; rend.par.resolutionh.expr = "parent().par.Resolutionh"
rend.par.camera = cam.name; rend.par.geometry = geo.name; rend.par.lights = ''
rend.par.bgcolora = 0; rend.par.antialias = 'aa1'

# ---- trails + output
zt = mk(td.constantTOP, 'zero_trail', outputresolution='custom', format='rgba16float', colorr=0, colorg=0, colorb=0, alpha=0)
fbT = mk(td.feedbackTOP, 'fb_trail', outputresolution='custom', format='rgba16float')
trail = mk(td.glslTOP, 'trail', outputresolution='custom', format='rgba16float')
tone = mk(td.glslTOP, 'tone', outputresolution='custom', format='rgba16float')
for o in (zt, fbT, trail, tone):
    o.par.resolutionw.expr = "parent().par.Resolutionw"; o.par.resolutionh.expr = "parent().par.Resolutionh"
trail.par.pixeldat = dat('trail_pix', rd('trail.glsl')); tone.par.pixeldat = dat('tone_pix', rd('tone.glsl'))
fbT.inputConnectors[0].connect(zt); trail.inputConnectors[0].connect(fbT); trail.inputConnectors[1].connect(rend)
fbT.par.top = trail.name; fbT.par.reset.expr = "parent().par.Reset"
vec(trail, 0, 'uT', "parent().par.Trails", "1 if parent().par.Play else 0")
tone.inputConnectors[0].connect(trail)
vec(tone, 0, 'uE', "parent().par.Exposure")
vec(tone, 1, 'uBg', *["parent().par.Background%s" % a for a in 'rgb'])
o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(tone)
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(pstate)   # raw particle state (xyz normalised attractor space, a = 1+speed)
c.op('out1').comment = 'render'
c.op('out2').comment = 'particles'
retro(c, accmode=0, gain=1.0)
c.save(OUT); print('saved')
