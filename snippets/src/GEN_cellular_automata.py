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
s = begin('GEN_cellular_automata')

ex = example(s, 1, 'Game of Life',
  'Classic Conway Life (B3/S23) from a random seed; Coloring = age shades long-lived cells,\n'
  'Ghost leaves fading trails of dead ones. Try: Rule = brain / wireworld / ltl,\n'
  'Cellsize for chunkier pixels, Rate for speed, Reset to reseed (Density sets the fill).')
c = inst(ex, 'GEN_cellular_automata')
c.par.Resolutionw = 960; c.par.Resolutionh = 540
out(ex, 1, c)

ex = example(s, 2, 'Life from a shape',
  'A white Text TOP into in1 seeds the automaton on Reset: bright pixels start alive. Life\n'
  'the letters erupt into gliders and debris. Press Reset after changing the input (it re-seeds).\n'
  'Try Cellsize 2 for finer detail, Rule = brain for sparks, Ghost for longer trails.')
t = text_mask(ex)
c = inst(ex, 'GEN_cellular_automata')
c.par.Resolutionw = 960; c.par.Resolutionh = 540
c.par.Rule = 'life'; c.par.Cellsize = 3
c.inputConnectors[0].connect(t)
out(ex, 2, c)

ex = example(s, 3, 'Beat-injected cells',
  'Larger-than-Life rule (Rule = ltl) makes smooth, organic blobs. The Beat CHOP (modulation input)\n'
  'injects a burst of live cells every beat at an orbiting point, so each beat spawns a new colony.\n'
  'Injectradius sets the burst size; Loopinject gives a constant trickle instead.')
c = inst(ex, 'GEN_cellular_automata')
c.par.Resolutionw = 960; c.par.Resolutionh = 540
c.par.Rule = 'ltl'; c.par.Density = 0.3; c.par.Injectradius = 0.1; c.par.Cellsize = 3
rn = beat_mod(ex, 90)
c.inputConnectors[1].connect(rn)
out(ex, 3, c)
finish(s)
