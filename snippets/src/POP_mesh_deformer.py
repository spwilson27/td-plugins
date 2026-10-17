exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_mesh_deformer')


def rig(ex, d, env=None, row=1, cam_dist=6.5):
    """POP_mesh_deformer is a filter: out1 is the deformed POP. Render it with a PBR chrome material,
    a key light and (optionally) an environment light from a 360 photo."""
    mat = ex.create(td.pbrMAT, 'chrome', row=row + 2)
    mat.par.basecolorr = mat.par.basecolorg = mat.par.basecolorb = 0.86
    mat.par.metallic = 1.0; mat.par.roughness = 0.25
    r = render_pop(ex, d.op('out1'), cam_dist=cam_dist, cam_height=1.0, material=mat, row=row)
    if env is not None:
        el = ex.create(td.environmentlightCOMP, 'envlight', row=row + 1); el.par.envlightmap = env
        lt = [o for o in ex.s.children if o.name.startswith('ex%d_light' % ex.n)][-1]
        r.par.lights = '%s %s' % (lt.name, el.name)
    r.par.format = 'rgba16float'; r.par.antialias = 'aa4'
    return r

# 1. your own POP -------------------------------------------------------------------------
ex = example(s, 1, 'Deform your own POP, with an env map',
  'A Torus POP into in1 (any POP geometry works: Box, Sphere, Samples Geo...). The component is a filter:\n'
  'out1 is the deformed mesh, rendered here with a PBR chrome material lit by a 360 photo.\n'
  'Twist and Bend set the big shape; Noiseshell adds lumpy displacement; Ripple + Ripplefreq adds surface waves.')
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 160; tor.par.rows = 64
env = ex.create(td.moviefileinTOP, 'env'); env.par.file.expr = sample_expr('Map/PalaceOfFineArts-360Designs.io.jpg')
d = instance(ex, 'POP_mesh_deformer')
d.inputConnectors[0].connect(tor)
d.par.Twist = 1.4; d.par.Noiseshell = 0.5; d.par.Ripple = 0.5
out(ex, 1, rig(ex, d, env))

# 2. recipe -------------------------------------------------------------------------------
ex = example(s, 2, 'Recipe: inflated ripple sphere',
  'A Sphere POP into in1 with Inflate and Ripple turned up and Twist off gives a pulsing rippled orb.\n'
  'Ripplecycles sets the wave count around the object; Noisefreq scales the lumps; Bend 0 keeps it symmetric.\n'
  'Mesh resolution matters: the deformation is per-point, so use a dense sphere.')
sph = ex.create(td.spherePOP, 'sphere'); sph.par.type = 'sharedpoles'; sph.par.surftype = 'triangles'
sph.par.cols = 240; sph.par.rows = 120; sph.par.normal = True
d = instance(ex, 'POP_mesh_deformer')
d.inputConnectors[0].connect(sph)
d.par.Twist = 0.0; d.par.Bend = 0.0; d.par.Inflate = 0.3; d.par.Ripple = 0.8; d.par.Ripplefreq = 12; d.par.Noiseshell = 0.4
out(ex, 2, rig(ex, d, env))

# 3. modulation ---------------------------------------------------------------------------
ex = example(s, 3, 'Beat-driven deformation (mod CHOP)',
  'Four LFO CHOPs named band1..band4 are merged into the modulation input (in2, the last input).\n'
  'band1 -> Inflate + Bend, band2 -> Twist, band3 -> Ripple, band4 -> Noise shell; Modgain scales them.\n'
  'Replace the LFOs with an Audio Spectrum / Analyze CHOP (0-1) to make it react to music.')
lfos = []
for i, f in enumerate((0.5, 0.25, 0.75, 0.4)):
    l = ex.create(td.lfoCHOP, 'band%d' % (i + 1), col=i, row=3)
    l.par.channelname = 'band%d' % (i + 1); l.par.frequency = f; l.par.amp = 0.5; l.par.bias = 0.5
    l.par.wavetype = 'sin'; l.par.phase = i * 0.25
    lfos.append(l)
mg = ex.create(td.mergeCHOP, 'merge', col=4, row=3)
for l in lfos: mg.inputConnectors[0].connect(l)
tor = ex.create(td.torusPOP, 'torus'); tor.par.surftype = 'triangles'
tor.par.radx = 0.9; tor.par.rady = 0.38; tor.par.cols = 160; tor.par.rows = 64
d = instance(ex, 'POP_mesh_deformer', col=5, row=0)
d.inputConnectors[0].connect(tor)
d.inputConnectors[1].connect(mg)
d.par.Modgain = 2.0
out(ex, 3, rig(ex, d, env))

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
