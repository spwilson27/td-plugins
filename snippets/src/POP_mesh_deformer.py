exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_mesh_deformer')

# 1. defaults -----------------------------------------------------------------------------
ex = example(s, 1, 'Default chrome blob',
  'POP_mesh_deformer with nothing connected: its built-in sphere is twisted, bent and rippled and\n'
  'rendered as dark-studio chrome. A built-in LFO fakes the audio bands.\n'
  'Try: Twist and Bend for the big shape, Ripple + Ripplefreq for surface waves, Roughness for matte vs mirror.')
d = instance(ex, 'POP_mesh_deformer')
out(ex, 1, d)

# 2. your own POP + environment ----------------------------------------------------------
ex = example(s, 2, 'Deform your own POP, with an env map',
  'A Torus POP into in1 (any POP geometry works: Box, Sphere, a Line-to-mesh chain...).\n'
  'A 360 photo into in2 becomes the reflection environment for the metal.\n'
  'Raise Detail so a coarse mesh still deforms smoothly; Noiseshell adds lumpy displacement.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 160; tor.par.rows = 64
env = ex.create(td.moviefileinTOP, 'env'); env.par.file.expr = sample_expr('Map/PalaceOfFineArts-360Designs.io.jpg')
d = instance(ex, 'POP_mesh_deformer')
d.inputConnectors[0].connect(tor)
d.inputConnectors[1].connect(env)
d.par.Twist = 1.4; d.par.Noiseshell = 0.5; d.par.Ripple = 0.5; d.par.Envintensity = 1.5
out(ex, 2, d)

# 3. modulation ---------------------------------------------------------------------------
ex = example(s, 3, 'Beat-driven deformation (mod CHOP)',
  'Four LFO CHOPs named band1..band4 are merged into the modulation input (in3, the last input).\n'
  'band1 -> Inflate + Bend, band2 -> Twist, band3 -> Ripple, band4 -> Noise shell; Modgain scales them.\n'
  'Replace the LFOs with an Audio Spectrum / Analyze CHOP (0-1) to make it react to music.')
lfos = []
for i, f in enumerate((0.5, 0.25, 0.75, 0.4)):
    l = ex.create(td.lfoCHOP, 'band%d' % (i + 1), col=i, row=1)
    l.par.channelname = 'band%d' % (i + 1); l.par.frequency = f; l.par.amp = 0.5; l.par.bias = 0.5
    l.par.wavetype = 'sin'; l.par.phase = i * 0.25
    lfos.append(l)
mg = ex.create(td.mergeCHOP, 'merge', col=4, row=1)
for l in lfos: mg.inputConnectors[0].connect(l)
d = instance(ex, 'POP_mesh_deformer', col=5, row=0)
d.inputConnectors[2].connect(mg)
d.par.Modgain = 2.0; d.par.Source = 'torus'
out(ex, 3, d)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
