exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name):
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def beat_mod(ex, bpm=120):
    """Beat CHOP -> Rename to the library's modulation channels: beat (pulse), band1 (smooth 0..1 wave)."""
    bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False; bt.par.bpm = bpm
    rn = ex.create(td.renameCHOP, 'modnames', col=1, row=1); rn.inputConnectors[0].connect(bt)
    rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
    return rn

s = begin('TOP_physarum')

ex = example(s, 1, 'Slime follows a photo',
  'The input image is the food map: agents crawl toward bright areas, so veins grow thickest on the bananas.\n'
  'Try: Attraction (strength; negative repels), Fieldblur (how far the pull reaches), Invert (follow the dark),\n'
  'Inputlevel (how much of the photo shows through), Reset (restart the growth).')
src = ex.create(td.moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
p = inst(ex, 'TOP_physarum')
p.inputConnectors[0].connect(src)
p.par.Resolutionmode = 'custom'; p.par.Resolutionw = 960; p.par.Resolutionh = 540; p.par.Stepsize = 2; p.par.Decay = 0.9; p.par.Deposit = 0.12; p.par.Agents = 120000
p.par.Attraction = 14; p.par.Fieldblur = 5
out(ex, 1, p)

ex = example(s, 2, 'Follow the dark, tinted trails',
  'Invert makes the agents seek dark areas; Colormode = tint paints the trails one colour, and Compose = add\n'
  'lets them glow over a dimmed copy of the image. A long Sensordist gives coarse cells, a short one fine veins.')
src = ex.create(td.moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
p = inst(ex, 'TOP_physarum')
p.inputConnectors[0].connect(src)
p.par.Resolutionmode = 'custom'; p.par.Resolutionw = 960; p.par.Resolutionh = 540; p.par.Stepsize = 2; p.par.Decay = 0.9; p.par.Deposit = 0.12; p.par.Agents = 120000
p.par.Invert = True; p.par.Attraction = 14; p.par.Fieldblur = 4
p.par.Colormode = 'tint'; p.par.Tintr = 0.3; p.par.Tintg = 1.0; p.par.Tintb = 0.7
p.par.Compose = 'add'; p.par.Inputlevel = 0.25; p.par.Sensordist = 10
out(ex, 2, p)

ex = example(s, 3, 'Raw trail map, modulated',
  'out2 is the raw trail map (a single float channel) for use as a mask or displacement source.\n'
  'The Beat CHOP drives the modulation input: band1 boosts Deposit, so the veins swell with the beat.\n'
  'Colormode = image tints the trails with the colours of the photo underneath.')
src = ex.create(td.moviefileinTOP, 'count'); src.par.file.expr = sample_expr('Map/Count.mov')
p = inst(ex, 'TOP_physarum')
p.inputConnectors[0].connect(src)
p.par.Resolutionmode = 'custom'; p.par.Resolutionw = 960; p.par.Resolutionh = 540; p.par.Stepsize = 2; p.par.Decay = 0.9; p.par.Deposit = 0.12; p.par.Agents = 120000
p.par.Attraction = 8; p.par.Colormode = 'image'; p.par.Compose = 'over'; p.par.Inputlevel = 0.2; p.par.Gain = 1.5; p.par.Deposit = 0.12
rn = beat_mod(ex)
p.inputConnectors[1].connect(rn)
lv = ex.create(td.levelTOP, 'expose'); lv.par.brightness1 = 2.5; connect(p, lv, out_index=1)
out(ex, 3, lv)
finish(s)
