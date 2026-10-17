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
s = begin('GEN_verlet_cloth')

ex = example(s, 1, 'Pinned cloth in the wind',
  'A 64x64 Verlet cloth pinned along the top, blown by wind with turbulence, draped over a sphere.\n'
  'Try: Wind / Turbulence for flutter, Stiffness and Iterations for how stretchy it is,\n'
  'Pinmode = corners, Collider on/off. out2 = particle positions texture.')
v = inst(ex, 'GEN_verlet_cloth')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
out(ex, 1, v)

ex = example(s, 2, 'Corner-pinned banner, mono',
  'Pinmode = corners, collider off and a strong sideways wind turn it into a rippling banner.\n'
  'Lower Stiffness / Iterations for a loose, stretchy fabric. Mono look with a thin red Accent.\n'
  'Camangle and Camdist move the view.')
v = inst(ex, 'GEN_verlet_cloth')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
v.par.Pinmode = 'corners'; v.par.Collider = False; v.par.Wind = 9; v.par.Winddirx = 1; v.par.Winddirz = -0.3
v.par.Camangle = 25; v.par.Look = 'mono'
out(ex, 2, v)

ex = example(s, 3, 'Gusts on the beat',
  'The Beat CHOP (modulation input) multiplies Wind by up to 4x with band1: the cloth billows in time.\n'
  'Replace with Audio Spectrum band channels to make music gust the fabric.\n'
  'Gravity and Damping set how fast it settles between gusts.')
v = inst(ex, 'GEN_verlet_cloth')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
v.par.Wind = 2; v.par.Turbulence = 0.3; v.par.Pinmode = 'corners'; v.par.Collider = False; v.par.Winddirx = 0.6; v.par.Winddirz = -0.8; v.par.Color1r = 0.1; v.par.Color1g = 0.5; v.par.Color1b = 0.9
rn = beat_mod(ex, 80)
v.inputConnectors[0].connect(rn)
out(ex, 3, v)
finish(s)
