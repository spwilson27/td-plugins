exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name):
    # keep the parameter values set in this snippet when the external tox reloads
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def beat_mod(ex, bpm=120):
    """Beat CHOP -> Rename to the library's modulation channels: beat (pulse), band1 (smooth 0..1 wave)."""
    bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False; bt.par.bpm = bpm
    rn = ex.create(td.renameCHOP, 'modnames', col=1, row=1); rn.inputConnectors[0].connect(bt)
    rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
    return rn

def phase_clock(ex, hz=0.125):
    """Ramp LFO renamed to `phase`: a stand-in for a timeline / master clock (0..1 per loop)."""
    l = ex.create(td.lfoCHOP, 'clock_lfo', col=0, row=2); l.par.wavetype = 'ramp'; l.par.frequency = hz
    l.par.amp = 1; l.par.offset = 0
    rn = ex.create(td.renameCHOP, 'clock_phase', col=1, row=2); rn.inputConnectors[0].connect(l)
    rn.par.renamefrom = 'chan1'; rn.par.renameto = 'phase'
    return rn

def text_mask(ex, txt='TD', size=0.5):
    t = ex.create(td.textTOP, 'mask'); t.par.text = txt
    t.par.outputresolution = 'custom'; t.par.resolutionw = 1280; t.par.resolutionh = 720
    t.par.fontsizex = 380; t.par.fontsizey = 380
    t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0; t.par.bgalpha = 1
    t.par.fontcolorr = t.par.fontcolorg = t.par.fontcolorb = 1
    return t
s = begin('POP_boids')

ex = example(s, 1, 'Flock a torus',
  'The points of the input POP (here a Torus POP) become the flock: count = input points (capped by Max Boids),\n'
  'start positions = the input P. out2 = the ready-made cone mesh, rendered with Geometry COMP + Camera + Light.\n'
  'Try: Separation / Alignment / Cohesion, Boundmode wrap vs bounce, Reset to re-seed.')
tor = ex.create(td.torusPOP, 'torus', row=1)
tor.par.surftype = 'triangles'; tor.par.radx = 3.2; tor.par.rady = 1.1; tor.par.cols = 90; tor.par.rows = 30
b = inst(ex, 'POP_boids')
b.inputConnectors[0].connect(tor)
b.par.Boidsize = 0.7; b.par.Obstacle = False; b.par.Speed = 0.7
mat = ex.create(td.phongMAT, 'mat', row=2); mat.par.diffr = mat.par.diffg = mat.par.diffb = 0.9
r = render_pop(ex, b.op('out2'), material=mat, cam_dist=18, cam_height=5)
out(ex, 1, r)

ex = example(s, 2, 'Instance your own geometry',
  'out1 = boid points: P = position, N = heading, Color. A Copy POP puts any geometry on them,\n'
  'aimed along N (Rotate To Vector). Here: small boxes on a tight murmuration (high Cohesion / Alignment)\n'
  'seeded from a Sphere POP. Swap the Box POP for any POP or a loaded model.')
sp = ex.create(td.spherePOP, 'sphere', row=1); sp.par.type = 'geodesic'; sp.par.surftype = 'triangles'
sp.par.radx = sp.par.rady = sp.par.radz = 3.0; sp.par.freq = 14
b = inst(ex, 'POP_boids')
b.inputConnectors[0].connect(sp)
b.par.Cohesion = 2.2; b.par.Alignment = 2.0; b.par.Separation = 1.0; b.par.Obstacle = False
bx = ex.create(td.boxPOP, 'shape', row=1); bx.par.sizex = 0.08; bx.par.sizey = 0.3; bx.par.sizez = 0.08
tp = ex.create(td.selectPOP, 'points', row=1); tp.par.pop = b.op('out1')
cp = ex.create(td.copyPOP, 'copy', row=1); cp.inputConnectors[0].connect(bx); cp.inputConnectors[1].connect(tp)
cp.par.dotemplatetranslate = True; cp.par.dotemplaterotateto = True; cp.par.vecattr = 'N'; cp.par.instanceforward = 'posy'
mat = ex.create(td.phongMAT, 'mat', row=2); mat.par.diffr = 0.95; mat.par.diffg = 0.92; mat.par.diffb = 0.85
r = render_pop(ex, cp, material=mat, row=0, cam_dist=18, cam_height=5)
out(ex, 2, r)

ex = example(s, 3, 'Startled by the beat',
  'No geometry connected: the built-in demo points flock. A Beat CHOP (renamed beat / band1) feeds the last input:\n'
  'band1 swells Cohesion so the flock tightens and loosens with the pulse, and every beat spikes Wander.\n'
  'Swap the Beat CHOP for an Audio Spectrum CHOP renamed to band1..band4 to follow music.')
b = inst(ex, 'POP_boids')
b.par.Boundmode = 'bounce'; b.par.Boidsize = 0.6; b.par.Obstacle = False
rn = beat_mod(ex, 100)
b.inputConnectors[1].connect(rn)
mat = ex.create(td.phongMAT, 'mat', row=3); mat.par.diffr = 1.0; mat.par.diffg = 0.45; mat.par.diffb = 0.15
r = render_pop(ex, b.op('out2'), material=mat, cam_dist=18, cam_height=5)
out(ex, 3, r)

finish(s)
