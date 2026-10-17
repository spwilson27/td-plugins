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
s = begin('GEN_physarum')

ex = example(s, 1, 'Slime network',
  'Physarum agents deposit a trail, sense it ahead-left/right and steer toward it: veins form on their own.\n'
  'Try: Sensorangle (wide = thick webs, narrow = long tendrils), Decay (trail memory),\n'
  'Diffuse (blur), Deposit. out2 = the raw trail map.')
p = inst(ex, 'GEN_physarum')
p.par.Resolutionw = 960; p.par.Resolutionh = 540
out(ex, 1, p)

ex = example(s, 2, 'Ring collapse, mono',
  'Initpattern = ring starts the agents on a circle that collapses into a lattice. Short Sensordist and\n'
  'a wide Sensorangle give a fine honeycomb. Mono look = bone-white veins on black.\n'
  'Press Reset to replay the growth.')
p = inst(ex, 'GEN_physarum')
p.par.Resolutionw = 960; p.par.Resolutionh = 540
p.par.Initpattern = 'ring'; p.par.Sensorangle = 55; p.par.Sensordist = 10; p.par.Decay = 0.9
p.par.Look = 'mono'; p.par.Monogain = 1.0
out(ex, 2, p)

ex = example(s, 3, 'Pulsing trails on a clock',
  'Loopmod wobbles sensor angle and distance in step with the Clock CHOP (ramp LFO renamed "phase",\n'
  'Timesource = phase), so the network breathes in a loop. band1 from the Beat CHOP (modulation input)\n'
  'boosts Deposit on every swell, so the veins flash brighter.')
p = inst(ex, 'GEN_physarum')
p.par.Resolutionw = 960; p.par.Resolutionh = 540
p.par.Loopmod = 0.25; p.par.Timesource = 'phase'; p.par.Sensorangle = 45
rn = beat_mod(ex); ck = phase_clock(ex)
p.inputConnectors[0].connect(rn); p.par.Clock = ck
out(ex, 3, p)
finish(s)
