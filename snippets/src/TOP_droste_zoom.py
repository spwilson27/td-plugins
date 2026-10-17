exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_droste_zoom')

ex = example(s, 1, 'Droste zoom on a photo',
  'Banana.tif -> TOP_droste_zoom -> example1: the picture repeats inside itself and zooms forever.\n'
  'Innerscale sets how small each nested copy is (smaller = more copies on screen).\n'
  'Zoomperiods sets zoom direction and how many copies pass per cycle; Speed sets how fast it zooms.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(src)
out(ex, 1, g)

ex = example(s, 2, 'Spiral Droste with spin',
  'Rotation twists each nested copy (a spiral); Spin turns the whole picture in whole turns.\n'
  'Try Zoomperiods = -1 to zoom out, and Seam to soften the ring joins. Mix drops back to the dry image.')
mv = ex.create(moviefileinTOP, 'jelly'); mv.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(mv)
g.par.Innerscale = 0.4; g.par.Rotation = 0.25; g.par.Spin = 1; g.par.Seam = 0.8; g.par.Zoomperiods = 2
out(ex, 2, g)

ex = example(s, 3, 'Beat pump on the inner scale',
  'A sine LFO named band1 goes into the modulation input (the last input): each pulse pushes Innerscale (Modamount).\n'
  'Raise Speed to zoom faster, or drop Original in to blend the un-warped picture back.\n'
  'Replace the LFO with a Beat CHOP / audio analysis to lock the tunnel to your music.')
src = ex.create(moviefileinTOP, 'banana', row=1); src.par.file.expr = sample_expr('Map/Banana.tif')
b1 = ex.create(lfoCHOP, 'band1', row=3); b1.par.wavetype = 'sin'; b1.par.frequency = 1.0; b1.par.channelname = 'band1'
b1.par.amp = 0.5; b1.par.offset = 0.5
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(src)
g.inputConnectors[1].connect(b1)
g.par.Modamount = 1.0
out(ex, 3, g)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
