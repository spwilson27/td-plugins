exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_pointcloud_dissolve')

# 1. defaults -----------------------------------------------------------------------------
ex = example(s, 1, 'Default dissolving head',
  'POP_pointcloud_dissolve with nothing connected: a built-in lumpy head becomes a white point cloud,\n'
  'and a moving plane erodes it into scattering dust, then re-forms it (Auto).\n'
  'Try: Wavemode (plane / orbiting sphere / radial), Scatter, Edgeglow, Pointsize.')
d = instance(ex, 'POP_pointcloud_dissolve')
d.par.Dissolve = 0.35; d.par.Auto = False
out(ex, 1, d)

# 2. your own mesh ------------------------------------------------------------------------
ex = example(s, 2, 'Dissolve your own POP mesh',
  'A Torus POP into in1 (mesh -> points); any POP geometry works. Source follows in1 when it is connected.\n'
  'Auto is off here, so Dissolve (0-1) is a manual fader: bring it down to re-form, up to scatter.\n'
  'Wavemode = Radial erodes from the axis outward; Axisx/y/z aim the wave. Density only sets the built-in shapes.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'; tor.par.normal = True
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 200; tor.par.rows = 80
d = instance(ex, 'POP_pointcloud_dissolve')
d.inputConnectors[0].connect(tor)
d.par.Auto = False; d.par.Dissolve = 0.45; d.par.Wavemode = 'radial'
d.par.Scatter = 1.8; d.par.Edgeglow = 2.5
out(ex, 2, d)

# 3. image depth + clock ------------------------------------------------------------------
ex = example(s, 3, 'Photo as depth, looped by a Clock',
  'A photo into in2 (the depth/luma TOP) with Source = Image: brightness becomes depth for a point relief.\n'
  'A ramp LFO named phase drives Clock (Timesource = phase): one ramp cycle = one dissolve and re-form.\n'
  'Invertluma flips depth; Depth sets relief height. Change the LFO frequency to retime the loop.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file.expr = sample_expr('Map/Banana.tif')
lfo = ex.create(td.lfoCHOP, 'phase'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.1; lfo.par.channelname = 'phase'
lfo.par.amp = 0.5; lfo.par.bias = 0.5
d = instance(ex, 'POP_pointcloud_dissolve')
d.inputConnectors[1].connect(img)
d.par.Source = 'image'; d.par.Density = 120; d.par.Clock = lfo; d.par.Timesource = 'phase'
d.par.Depth = 1.3; d.par.Camdist = 5.0; d.par.Orbitturns = 0
out(ex, 3, d)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
