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
s = begin('GEN_strange_attractors')

ex = example(s, 1, 'Lorenz butterfly',
  '80k particles flow along the Lorenz system, drawn with additive trails and an orbiting camera.\n'
  'Try: Trails (0.94 -> 0.98) for long streaks, Intensity / Exposure for brightness,\n'
  'Speed, Scale, Attractor menu (aizawa, thomas, halvorsen, dadras). out2 = particle state.')
a = inst(ex, 'GEN_strange_attractors')
a.par.Resolutionw = 960; a.par.Resolutionh = 540
out(ex, 1, a)

ex = example(s, 2, 'Morph two attractors',
  'Attractor = thomas, Attractorb = aizawa, Morph = 0.5 blends the two vector fields: the cloud\n'
  'settles into a hybrid shape. Animate Morph 0..1 (LFO / slider) to tween between systems.\n'
  'Mono look = white-hot filaments on black.')
a = inst(ex, 'GEN_strange_attractors')
a.par.Resolutionw = 960; a.par.Resolutionh = 540
a.par.Attractor = 'thomas'; a.par.Attractorb = 'aizawa'; a.par.Morph = 0.5; a.par.Look = 'mono'
a.par.Trails = 0.96
out(ex, 2, a)

ex = example(s, 3, 'Wobbling coefficients on a clock',
  'Coefmod wiggles the attractor coefficients in step with the Clock CHOP (ramp LFO renamed\n'
  '"phase", Timesource = phase) so the shape breathes and loops. The Beat CHOP (modulation input)\n'
  'adds extra band1 wobble and speeds the flow with band2.')
a = inst(ex, 'GEN_strange_attractors')
a.par.Resolutionw = 960; a.par.Resolutionh = 540
a.par.Attractor = 'halvorsen'; a.par.Coefmod = 0.25; a.par.Timesource = 'phase'
rn = beat_mod(ex); ck = phase_clock(ex)
a.inputConnectors[0].connect(rn); a.par.Clock = ck
out(ex, 3, a)
finish(s)
