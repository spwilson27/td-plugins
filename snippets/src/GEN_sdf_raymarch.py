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
s = begin('GEN_sdf_raymarch')

ex = example(s, 1, 'Smooth union',
  'A raymarched sphere smoothly blended into a torus, with soft shadows, ambient occlusion and fog.\n'
  'Try: Smooth K (blend radius), Shape A / Shape B, Combine = subtract or intersect,\n'
  'Orbitspeed / Distance for the camera, Light azimuth / elevation for the shadow direction.')
r = inst(ex, 'GEN_sdf_raymarch')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
out(ex, 1, r)

ex = example(s, 2, 'Gyroid forest',
  'Shape A = gyroid with Domain Repeat tiles an infinite lattice you can fly through.\n'
  'Thickness fades the walls, Repeatsize spaces the cells, Palette / Hue recolour it.\n'
  'Raise Steps if you see banding at distance; lower it to save GPU.')
r = inst(ex, 'GEN_sdf_raymarch')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
r.par.Shape1 = '4'; r.par.Shape2 = '1'; r.par.Repeat = True; r.par.Repeatsize = 3.5
r.par.Palette = '2'; r.par.Distance = 6; r.par.Fog = 1.2; r.par.Orbitspeed = 0.15
out(ex, 2, r)

ex = example(s, 3, 'Pulsing blob on a clock',
  'The camera orbit follows the Clock CHOP (ramp LFO renamed "phase", Timesource = phase) so one\n'
  'orbit = one loop. The Beat CHOP (modulation input) widens Smooth K with band1 and pops the\n'
  'Scale on each beat. Mono palette for a pure black / white look.')
r = inst(ex, 'GEN_sdf_raymarch')
r.par.Resolutionw = 960; r.par.Resolutionh = 540
r.par.Shape1 = '1'; r.par.Shape2 = '0'; r.par.Palette = '4'; r.par.Timesource = 'phase'
rn = beat_mod(ex); ck = phase_clock(ex)
r.inputConnectors[0].connect(rn); r.par.Clock = ck
out(ex, 3, r)
finish(s)
