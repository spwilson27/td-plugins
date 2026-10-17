exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_plexus_points')


def render_plexus(ex, p, cam_dist=7.0, cam_height=0.5, row=1):
    """POP_plexus_points is a filter: out1 = point cloud, out2 = plexus lines, out3 = long lines.
    Render them with additive point sprites / blended lines (Geometry COMP + Select POP each)."""
    dot = ex.create(td.pointspriteMAT, 'dot_mat', row=row + 2); dot.par.pointsize = 1
    dot.par.blending = True; dot.par.srcblend = 'one'; dot.par.destblend = 'one'; dot.par.depthwriting = False
    lm = ex.create(td.constantMAT, 'link_mat', row=row + 2); lm.par.colorr = lm.par.colorg = lm.par.colorb = 1
    lm.par.alpha = 0.38; lm.par.blending = True; lm.par.srcblend = 'sa'; lm.par.destblend = 'one'; lm.par.depthwriting = False
    gm = ex.create(td.constantMAT, 'long_mat', row=row + 2); gm.par.applypointcolor = True
    gm.par.blending = True; gm.par.srcblend = 'one'; gm.par.destblend = 'one'; gm.par.depthwriting = False
    pts = ex.create(td.convertPOP, 'points', row=row); pts.par.convert = 'topointprims'
    pts.inputConnectors[0].connect(p.outputConnectors[0])
    r = render_pop(ex, pts, cam_dist=cam_dist, cam_height=cam_height, row=row)
    geo_pts = [o for o in ex.s.children if o.name.startswith('ex%d_geo' % ex.n)][-1]
    geo_pts.par.material = dot
    names = [geo_pts.name]
    for k, (mat, o) in enumerate(((lm, 1), (gm, 2))):
        g = ex.create(td.geometryCOMP, 'geo_l%d' % (k + 1), row=row)
        for ch in list(g.children): ch.destroy()
        sel = g.create(td.selectPOP, 'select')
        g.par.material = mat
        names.append(g.name)
        sel.display = True; sel.render = True
        sel.par.pop = p.op('out%d' % (o + 1))
    r.par.geometry = ' '.join(names); r.par.lights = ''
    return r

# 1. your own POP -------------------------------------------------------------------------
ex = example(s, 1, 'Plexus on your own POP geometry',
  'A Torus POP into in1 (any POP source: Sphere, Box, Samples Geo...). The component is a filter:\n'
  'out1 = the scan-strata point cloud, out2 = plexus lines, out3 = long lines. Here all three are rendered.\n'
  'Lower Linkdistance and Maxlinks for a sparse web; Banding + Bands set the strata; Sweep moves the scan plane.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 64; tor.par.rows = 24
p = instance(ex, 'POP_plexus_points')
p.inputConnectors[0].connect(tor)
p.par.Linkdistance = 0.14; p.par.Banding = 0.6; p.par.Pointsize = 2.6; p.par.Longlines = 4
out(ex, 1, render_plexus(ex, p))

# 2. photo scan ---------------------------------------------------------------------------
ex = example(s, 2, 'Photo scan from a TOP',
  'A photo into in2 with Source = Image: points are sampled where it is bright, so the banana is scanned.\n'
  'Banding < 1 loosens the strata so the shape reads. Threshold sets how bright a pixel must be to get points;\n'
  'Imgdepth gives relief; Imgsamples sets the density.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file.expr = sample_expr('Map/Banana.tif')
p = instance(ex, 'POP_plexus_points')
p.inputConnectors[1].connect(img)
p.par.Source = 'image'; p.par.Scale = 0.5; p.par.Imgsamples = 3.0; p.par.Linkdistance = 0.1; p.par.Banding = 0.3
p.par.Points = 3000; p.par.Pointsize = 1.8; p.par.Brightness = 0.8
out(ex, 2, render_plexus(ex, p, cam_dist=5.0, cam_height=0.0))

# 3. recipe: bold web ---------------------------------------------------------------------
ex = example(s, 3, 'Recipe: bold constellation',
  'A Sphere POP into in1 with fewer, bigger points and longer links makes a constellation web.\n'
  'Banding 0 removes the strata; Maxlinks 5 and Linkdistance 0.35 join neighbours; Longlines adds random chords.\n'
  'Jitter shivers the points; Brightness scales point intensity.')
sph = ex.create(td.spherePOP, 'sphere'); sph.par.type = 'geodesic'; sph.par.surftype = 'triangles'; sph.par.freq = 12
p = instance(ex, 'POP_plexus_points')
p.inputConnectors[0].connect(sph)
p.par.Banding = 0.0; p.par.Linkdistance = 0.35; p.par.Maxlinks = 5; p.par.Pointsize = 4.0; p.par.Longlines = 16; p.par.Jitter = 0.03
out(ex, 3, render_plexus(ex, p))

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
