exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_plexus_points')

# 1. defaults -----------------------------------------------------------------------------
ex = example(s, 1, 'Default scan-strata cloud',
  'POP_plexus_points with nothing connected: a built-in head-ish blob is sampled as points, snapped into\n'
  'horizontal scan strata, joined by thin plexus lines, with a few long straight lines and a cross grid.\n'
  'Try: Linkdistance (more lines), Banding + Bands (strata), Sweep (scan plane), Longlines.')
p = instance(ex, 'POP_plexus_points')
out(ex, 1, p)

# 2. your own POP -------------------------------------------------------------------------
ex = example(s, 2, 'Plexus on your own POP geometry',
  'A Torus POP into in1 (any POP source: Sphere, Box, Samples Geo...). Source switches to it automatically.\n'
  'Its points become the cloud, so mesh resolution sets the density. Lower Linkdistance and Maxlinks\n'
  'to keep the web sparse; raise Pointsize and Brightness for a bolder scan look; Banding 0 removes the strata.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 64; tor.par.rows = 24
p = instance(ex, 'POP_plexus_points')
p.inputConnectors[0].connect(tor)
p.par.Linkdistance = 0.14; p.par.Banding = 0.6; p.par.Pointsize = 2.6; p.par.Longlines = 4
out(ex, 2, p)

# 3. image + clock ------------------------------------------------------------------------
ex = example(s, 3, 'Photo scan, looped by a Clock',
  'A photo into in2 with Source = Image: points are sampled where it is bright, so the banana is scanned.\n'
  'A ramp LFO named phase drives Clock (Timesource = phase): one cycle = one loop of sweep, camera and glitch steps.\n'
  'Banding < 1 loosens the strata so the shape reads. Threshold sets how bright a pixel must be to get points; Imgdepth gives relief.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file.expr = sample_expr('Map/Banana.tif')
lfo = ex.create(td.lfoCHOP, 'phase'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.0625; lfo.par.channelname = 'phase'
lfo.par.amp = 0.5; lfo.par.bias = 0.5
p = instance(ex, 'POP_plexus_points')
p.inputConnectors[1].connect(img)
p.par.Source = 'image'; p.par.Clock = lfo; p.par.Timesource = 'phase'; p.par.Orbitrange = 0.0; p.par.Scale = 0.5; p.par.Imgsamples = 3.0; p.par.Linkdistance = 0.1; p.par.Banding = 0.3; p.par.Points = 3000; p.par.Pointsize = 1.8; p.par.Brightness = 0.8
out(ex, 3, p)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
