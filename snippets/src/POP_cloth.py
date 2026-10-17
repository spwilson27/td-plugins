exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name, **kw):
    c = instance(ex, name, **kw)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def side_view(r, ang=35, dist=9.5, height=0.0):
    """Orbit the render_pop camera round to the side so billowing along z is visible."""
    cam = r.par.camera.eval()
    import math
    cam.par.tx = dist * math.sin(math.radians(ang)); cam.par.tz = dist * math.cos(math.radians(ang))
    cam.par.ty = height; cam.par.ry = ang; cam.par.rx = 0
    return r

def grid(ex, name, n=48, size=2.0, top=0.9, col=None):
    """Triangulated Grid POP in the XY plane, hanging from y = top."""
    g = ex.create(td.gridPOP, name, col=col)
    g.par.surftype = 'triangles'; g.par.cols = n; g.par.rows = n
    g.par.sizex = size; g.par.sizey = size; g.par.ty = top - size / 2
    return g

def fabric(ex):
    """Phong MAT textured with a Samples photo (the Grid POP's Tex attribute provides the UVs)."""
    tex = ex.create(td.moviefileinTOP, 'fabric_tex', row=2)
    tex.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
    m = ex.create(td.phongMAT, 'fabric', row=2)
    m.par.diffusemap = tex
    m.par.diffr = m.par.diffg = m.par.diffb = 0.8
    m.par.ambr = m.par.ambg = m.par.ambb = 0.3
    m.par.specr = m.par.specg = m.par.specb = 0.1
    return m

s = begin('POP_cloth')

ex = example(s, 1, 'A Grid POP becomes cloth',
  'Any POP mesh into in1 is simulated as cloth: a 48x48 Grid POP hangs from its top row (Pinmode = Top Row).\n'
  'Wind + Turbulence blow it, Gravity pulls, the sphere collider (Sphere Pos / Radius) is invisible here.\n'
  'Try: Stiffness and Iterations (stretchiness), Wind, Gravity, Winddir. out1 is a POP: render it as shown.')
g = grid(ex, 'grid')
c1 = inst(ex, 'POP_cloth')
c1.inputConnectors[0].connect(g)
c1.par.Collider = False; c1.par.Speed = 1.5; c1.par.Iterations = 48; c1.par.Wind = 9; c1.par.Turbulence = 1.2; c1.par.Winddirx = 0.3; c1.par.Winddirz = 1
r = render_pop(ex, c1.op('out1'), cam_dist=7.5, cam_height=1.0, material=fabric(ex), row=1)
side_view(r)
out(ex, 1, r)

ex = example(s, 2, 'Pin a group: a flying banner',
  'A Group POP marks the left edge as `pinned`; Pinmode = Point Group pins exactly those points.\n'
  '(Pinmode = Pin Attribute uses any point attribute named Pin > 0.5.) A sideways wind makes it ripple.\n'
  'Lower Stiffness / Iterations for loose fabric, or raise Max Neighbours for dense meshes.')
g = grid(ex, 'grid', n=40, size=2.4, top=1.2)
gp = ex.create(td.groupPOP, 'group'); gp.inputConnectors[0].connect(g)
gp.par.grname = 'pinned'
gp.par.bound = 1; gp.par.bound0enabled = True; gp.par.bound0type = 'usebbox'
gp.par.bound0translatex = -1.2; gp.par.bound0scalex = 0.1; gp.par.bound0scaley = 3; gp.par.bound0scalez = 2
c2 = inst(ex, 'POP_cloth')
c2.inputConnectors[0].connect(gp)
c2.par.Pinmode = 'group'; c2.par.Collider = False; c2.par.Gravity = 4
c2.par.Speed = 1.5; c2.par.Wind = 9; c2.par.Winddirx = 1; c2.par.Winddirz = -0.5; c2.par.Turbulence = 1.0
r = render_pop(ex, c2.op('out1'), cam_dist=8, cam_height=1.0, material=fabric(ex), row=1)
side_view(r, -25, 9.5)
out(ex, 2, r)

ex = example(s, 3, 'Gusts on the beat',
  'A Beat CHOP renamed to `beat` + `band1` (the modulation input, always the last input) gusts the wind.\n'
  'band1 and beat scale Wind, band2 adds turbulence, band3 lifts against gravity; Modgain scales it all.\n'
  'Replace the Beat CHOP with an Audio Spectrum band CHOP (0-1) to make music blow the fabric.')
g = grid(ex, 'grid', n=48)
bt = ex.create(td.beatCHOP, 'beat', row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False; bt.par.bpm = 80
rn = ex.create(td.renameCHOP, 'modnames', row=1); rn.inputConnectors[0].connect(bt)
rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
c3 = inst(ex, 'POP_cloth')
c3.inputConnectors[0].connect(g)
c3.inputConnectors[1].connect(rn)
c3.par.Speed = 1.5; c3.par.Iterations = 48; c3.par.Wind = 4; c3.par.Turbulence = 0.3; c3.par.Collider = False; c3.par.Winddirx = 0.3; c3.par.Winddirz = 1
r = render_pop(ex, c3.op('out1'), cam_dist=7.5, cam_height=1.0, material=fabric(ex), row=3)
side_view(r)
out(ex, 3, r)
finish(s)
