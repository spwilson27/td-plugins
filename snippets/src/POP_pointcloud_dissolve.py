exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_pointcloud_dissolve')


def rig(ex, d, cam_dist=6.0, cam_height=0.35, row=1):
    """POP_pointcloud_dissolve is a filter: out1 = the eroded point cloud (with Color + pointscale).
    Render it with additive point sprites."""
    mat = ex.create(td.pointspriteMAT, 'sprite_mat', row=row + 2); mat.par.pointsize = 1
    mat.par.blending = True; mat.par.srcblend = 'sa'; mat.par.destblend = 'one'; mat.par.depthwriting = False
    pts = ex.create(td.convertPOP, 'points', row=row); pts.par.convert = 'topointprims'
    pts.inputConnectors[0].connect(d.outputConnectors[0])
    r = render_pop(ex, pts, cam_dist=cam_dist, cam_height=cam_height, material=mat, row=row)
    r.par.lights = ''; r.par.format = 'rgba16float'
    return r

# 1. your own mesh ------------------------------------------------------------------------
ex = example(s, 1, 'Dissolve your own POP mesh',
  'A Torus POP into in1 (mesh -> points); any POP geometry works. The component is a filter: out1 is the point\n'
  'cloud, rendered here with additive point sprites. Auto is off, so Dissolve (0-1) is a manual fader.\n'
  'Wavemode = Radial erodes from the axis outward; Axisx/y/z aim the wave. Scatter + Edgeglow shape the dust.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'; tor.par.normal = True
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 200; tor.par.rows = 80
d = instance(ex, 'POP_pointcloud_dissolve')
d.inputConnectors[0].connect(tor)
d.par.Auto = False; d.par.Dissolve = 0.45; d.par.Wavemode = 'radial'
d.par.Scatter = 1.8; d.par.Edgeglow = 2.5
out(ex, 1, rig(ex, d))

# 2. recipe: animated plane erosion -------------------------------------------------------
ex = example(s, 2, 'Recipe: auto erosion of a sphere',
  'A Sphere POP with Auto on: a moving plane erodes the points and re-forms them by itself (Autocycles, Automax).\n'
  'Jitter ragged-edges the front; Drift pushes the dust; Pointsize + Brightness set the look.\n'
  'Wavemode = Orbiting Sphere eats the cloud from a sphere circling it.')
sph = ex.create(td.spherePOP, 'sphere'); sph.par.type = 'geodesic'; sph.par.surftype = 'triangles'
sph.par.freq = 60; sph.par.normal = True
d = instance(ex, 'POP_pointcloud_dissolve')
d.inputConnectors[0].connect(sph)
d.par.Auto = True; d.par.Automax = 0.9; d.par.Wavemode = 'plane'; d.par.Jitter = 0.5; d.par.Pointsize = 2.5
out(ex, 2, rig(ex, d))

# 3. image depth --------------------------------------------------------------------------
ex = example(s, 3, 'Photo as depth',
  'A photo into in2 (the depth/luma TOP) with Source = Image: brightness becomes depth for a point relief.\n'
  'Invertluma flips depth; Depth sets relief height; Density sets how many points sample the picture.\n'
  'Dissolve (or Auto) erodes the relief just like a mesh.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file.expr = sample_expr('Map/Banana.tif')
d = instance(ex, 'POP_pointcloud_dissolve')
d.inputConnectors[1].connect(img)
d.par.Source = 'image'; d.par.Density = 120; d.par.Auto = False; d.par.Dissolve = 0.2
d.par.Depth = 1.3
out(ex, 3, rig(ex, d, cam_dist=5.0))

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
