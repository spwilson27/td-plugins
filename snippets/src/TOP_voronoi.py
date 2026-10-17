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
s = begin('GEN_voronoi')

ex = example(s, 1, 'Edge-glow cells',
  'Animated Voronoi cells with glowing borders over built-in noise colour.\n'
  'Try: Mode (flat, edge glow, cracked glass, stained glass), Seeds for cell count,\n'
  'Jitter 0 = regular grid, Delaunay overlay, Palette / Hue to recolour.')
v = inst(ex, 'GEN_voronoi')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
out(ex, 1, v)

ex = example(s, 2, 'Stained-glass photo',
  'A photo into in1 and Mode = stained glass: each cell takes the colour of the picture beneath it.\n'
  'Fewer Seeds = chunkier glass; Borderwidth sets the lead lines. Try Mode = cracked glass for a\n'
  'shattered-window look.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file = sample('Map/Banana.tif')
v = inst(ex, 'GEN_voronoi')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
v.par.Mode = '3'; v.par.Seeds = 90; v.par.Borderwidth = 2.5
v.inputConnectors[0].connect(img)
out(ex, 2, v)

ex = example(s, 3, 'Beat-synced cells',
  'Cell drift follows the Clock CHOP (ramp LFO renamed "phase", Timesource = phase) so the motion\n'
  'loops cleanly. The Beat CHOP (modulation input, in2) adds band1 to Motion and a flash of Glow on\n'
  'every beat. Palette = mono for black and white.')
v = inst(ex, 'GEN_voronoi')
v.par.Resolutionw = 960; v.par.Resolutionh = 540
v.par.Palette = '4'; v.par.Timesource = 'phase'
rn = beat_mod(ex); ck = phase_clock(ex)
v.inputConnectors[1].connect(rn); v.par.Clock = ck
out(ex, 3, v)
finish(s)
