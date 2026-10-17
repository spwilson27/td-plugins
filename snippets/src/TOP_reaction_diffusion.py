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
s = begin('GEN_reaction_diffusion')

ex = example(s, 1, 'Coral growth',
  'Gray-Scott reaction-diffusion with the coral preset: random seeds grow into branching fingers.\n'
  'Try the Preset menu (mitosis, labyrinth, spots, worms; it sets Feed and Kill) or nudge them\n'
  'by 0.002 at a time - the interesting patterns live in a very thin band.')
r = inst(ex, 'GEN_reaction_diffusion')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
out(ex, 1, r)

ex = example(s, 2, 'Seed from a shape',
  'A white-on-black Text TOP into in1: bright pixels seed chemical B when the sim resets, so the\n'
  'pattern grows out of the letters. Press Reset to re-seed. Labyrinth makes a maze that fills the\n'
  'space; Mono look gives the black / bone-white poster feel.')
t = text_mask(ex)
r = inst(ex, 'GEN_reaction_diffusion')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
r.par.Preset = 'labyrinth'; r.par.Feed = 0.029; r.par.Kill = 0.057; r.par.Look = 'mono'
r.inputConnectors[0].connect(t)
out(ex, 2, r)

ex = example(s, 3, 'Breathing feed on a clock',
  'Loopmod makes Feed and Kill wobble by +/-15% around their preset values, locked to the Clock\n'
  'CHOP (ramp LFO renamed "phase", Timesource = phase), while band1 from the Beat CHOP (last input)\n'
  'adds a pulse of extra feed. Mitosis cells split and merge rhythmically.')
r = inst(ex, 'GEN_reaction_diffusion')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
r.par.Preset = 'mitosis'; r.par.Feed = 0.0367; r.par.Kill = 0.0649; r.par.Steps = 30; r.par.Loopmod = 0.15; r.par.Timesource = 'phase'
rn = beat_mod(ex); ck = phase_clock(ex)
r.inputConnectors[1].connect(rn); r.par.Clock = ck
out(ex, 3, r)
finish(s)
