exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
exec(open(os.path.join(LIB, 'components/_gbuf/gbuf.py')).read())
s = begin('TOP_depth_fog')
R = ('1280', '720')

ex = example(s, 1, 'Fog over a Render TOP G-buffer',
             'A Render TOP draws Sphere / Torus / Box POPs with a GLSL MAT that writes three colour buffers:\ncolour, linear eye-space depth (R) and view-space normals. Colour + depth go into TOP_depth_fog.\nTry: Density, Fogmode, Heightdensity (ground fog), Glow / Glowwidth (horizon glow), Fogcolor.')
gb = make_gbuffer(s, res=R, prefix='ex1_')
sky = add_sky(s, gb['color'], R, prefix='ex1_')
f = instance(ex, 'TOP_depth_fog')
f.inputConnectors[0].connect(sky); f.inputConnectors[1].connect(gb['depth'])
out(ex, 1, f)

ex = example(s, 2, 'Linear fog from the raw Render TOP depth',
             'The depth here is the Render TOP depth buffer itself (Depth TOP, non-linear 0-1).\nDepthmode = nonlinear + Near/Far matching the Camera COMP linearises it.\nLinear fog (Start/End) with height fog off gives a clean distance haze.')
gb = make_gbuffer(s, res=R, prefix='ex2_')
sky = add_sky(s, gb['color'], R, prefix='ex2_')
dp = ex.create(td.depthTOP, 'depth', row=1)
dp.par.op = gb['render']; dp.par.depthspace = 'input'; dp.par.pixelformat = 'r32float'
dp.par.outputresolution = 'useinput'
f = instance(ex, 'TOP_depth_fog')
f.inputConnectors[0].connect(sky); f.inputConnectors[1].connect(dp)
f.par.Depthmode = 'nonlinear'; f.par.Near = 0.5; f.par.Far = 100
f.par.Fogmode = 'linear'; f.par.Start = 3; f.par.End = 30; f.par.Heightfog = 0
f.par.Fogcolorr, f.par.Fogcolorg, f.par.Fogcolorb = 0.12, 0.2, 0.32
f.par.Glow = 0.0; f.par.Skyblend = 0.6
out(ex, 2, f)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
