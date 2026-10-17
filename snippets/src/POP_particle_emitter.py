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
s = begin('GEN_gpu_particles')

ex = example(s, 1, 'Curl-noise fountain',
  'GEN_gpu_particles defaults: 200k points are emitted from a disc, lifted by curl noise and pulled\n'
  'by an attractor. Try: Curlstrength up for more turbulence, Gravity down for floaty smoke,\n'
  'Pointsize / Brightness for density. out1 = render, out2 = particle texture, out3 = particle POP.')
g = inst(ex, 'GEN_gpu_particles')
g.par.Resolutionw = 960; g.par.Resolutionh = 540
out(ex, 1, g)

ex = example(s, 2, 'Twin attractor swirl',
  'Gravity off, a second attractor switched on, and both orbit (Attrorbit) so particles are\n'
  'slung between two wells. Mono look = bone-white points on black; Accent adds a red tint.\n'
  'Try: Attr1strength / Attr2strength for lopsided pulls, Damping for how tightly they orbit.')
g = inst(ex, 'GEN_gpu_particles')
g.par.Resolutionw = 960; g.par.Resolutionh = 540
g.par.Gravity = 0; g.par.Emitvelocity = 0.6; g.par.Attr2strength = 2.0; g.par.Attrorbit = 1.5
g.par.Curlstrength = 0.3; g.par.Damping = 0.5; g.par.Look = 'mono'; g.par.Monogain = 1.5
out(ex, 2, g)

ex = example(s, 3, 'Beat bursts + phase clock',
  'The Beat CHOP (renamed beat/band1) is wired to the last input: each beat multiplies the emit rate x4,\n'
  'band1 swells the curl strength. Loop > Timesource = phase with a ramp LFO renamed "phase" in the\n'
  'Clock parameter makes the camera spin and noise drift loop exactly with that clock.')
g = inst(ex, 'GEN_gpu_particles')
g.par.Resolutionw = 960; g.par.Resolutionh = 540
g.par.Emitrate = 20000; g.par.Curlstrength = 0.8; g.par.Timesource = 'phase'
rn = beat_mod(ex); ck = phase_clock(ex)
g.inputConnectors[0].connect(rn); g.par.Clock = ck
out(ex, 3, g)
finish(s)
