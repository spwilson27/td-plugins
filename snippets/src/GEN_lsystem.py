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
s = begin('GEN_lsystem')

ex = example(s, 1, 'Growing plant',
  'The Fractal plant preset expands an L-system on load and grows it with a saw ramp.\n'
  'Try: Preset menu (tree, bush, koch, dragon), Angle (a few degrees changes the whole silhouette),\n'
  'Iterations (5 -> 6 doubles the branches), Linewidth and Taper for stem thickness.')
l = inst(ex, 'GEN_lsystem')
l.par.Resolutionw = 960; l.par.Resolutionh = 540
out(ex, 1, l)

ex = example(s, 2, 'Koch snowflake',
  'Preset = koch draws the classic snowflake curve; Animate off and Growth = 1 shows the finished\n'
  'curve. Colour a tip / root gradient with Root Color and Tip Color; Zoom frames it.\n'
  'Switch Preset to custom to type your own Axiom and Rule 1-3.')
l = inst(ex, 'GEN_lsystem')
l.par.Resolutionw = 960; l.par.Resolutionh = 540
l.par.Preset = 'koch'; l.par.Animate = False; l.par.Growth = 1; l.par.Linewidth = 0.004
l.par.Colorbr = 0.3; l.par.Colorbg = 0.8; l.par.Colorbb = 1.0
out(ex, 2, l)

ex = example(s, 3, 'Clocked tree, mono + beat',
  'Growth grows and retracts exactly once per Clock loop (ramp LFO renamed "phase", Timesource =\n'
  'phase). The Beat CHOP (modulation input) thickens the lines with band1 and nudges Zoom each beat.\n'
  'Mono look = bone-white tree on black.')
l = inst(ex, 'GEN_lsystem')
l.par.Resolutionw = 960; l.par.Resolutionh = 540
l.par.Preset = 'tree'; l.par.Timesource = 'phase'; l.par.Look = 'mono'
rn = beat_mod(ex); ck = phase_clock(ex)
l.inputConnectors[0].connect(rn); l.par.Clock = ck
out(ex, 3, l)
finish(s)
