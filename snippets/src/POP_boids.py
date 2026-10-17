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
s = begin('GEN_boids')

ex = example(s, 1, 'Render the flock',
  'GEN_boids only outputs geometry (POP). out2 = the ready-made cone mesh, one cone per boid;\n'
  'here it is rendered with a Geometry COMP (Select POP) + Camera + Light + Render TOP.\n'
  'Try: Separation / Alignment / Cohesion, Boundmode wrap vs bounce. The node viewer shows a built-in preview.')
b = inst(ex, 'GEN_boids')
b.par.Boidsize = 0.8
mat = ex.create(td.phongMAT, 'mat', row=2); mat.par.diffr = mat.par.diffg = mat.par.diffb = 0.9
r = render_pop(ex, b.op('out2'), material=mat)
out(ex, 1, r)

ex = example(s, 2, 'Instance your own geometry',
  'out1 = boid points: P = position, N = heading, Color. Copy POP puts any geometry on them,\n'
  'aimed along N (Rotate To Vector). Here: small boxes, tight murmuration (high Cohesion / Alignment).\n'
  'Swap the Box POP for any POP or a loaded model.')
b = inst(ex, 'GEN_boids')
b.par.Cohesion = 2.2; b.par.Alignment = 2.0; b.par.Separation = 1.0; b.par.Obstacle = False
bx = ex.create(td.boxPOP, 'shape', row=1); bx.par.sizex = 0.08; bx.par.sizey = 0.3; bx.par.sizez = 0.08
tp = ex.create(td.selectPOP, 'points', row=1); tp.par.pop = b.op('out1')
cp = ex.create(td.copyPOP, 'copy', row=1); cp.inputConnectors[0].connect(bx); cp.inputConnectors[1].connect(tp)
cp.par.dotemplatetranslate = True; cp.par.dotemplaterotateto = True; cp.par.vecattr = 'N'; cp.par.instanceforward = 'posy'
mat = ex.create(td.phongMAT, 'mat', row=2); mat.par.diffr = 0.95; mat.par.diffg = 0.92; mat.par.diffb = 0.85
r = render_pop(ex, cp, material=mat, row=0)
out(ex, 2, r)

ex = example(s, 3, 'Startled by the beat',
  'Beat CHOP (renamed beat / band1) into the modulation input: band1 swells Cohesion so the flock\n'
  'tightens and loosens with the pulse, and every beat spikes Wander so it scatters.\n'
  'Swap the Beat CHOP for an Audio Spectrum CHOP renamed to band1..band4 to follow music.')
b = inst(ex, 'GEN_boids')
b.par.Boundmode = 'bounce'; b.par.Count = 8192; b.par.Boidsize = 0.6; b.par.Obstacle = False
rn = beat_mod(ex, 100)
b.inputConnectors[0].connect(rn)
mat = ex.create(td.phongMAT, 'mat', row=3); mat.par.diffr = 1.0; mat.par.diffg = 0.45; mat.par.diffb = 0.15
r = render_pop(ex, b.op('out2'), material=mat)
out(ex, 3, r)

finish(s)
