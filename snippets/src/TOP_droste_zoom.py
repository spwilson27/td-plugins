exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_droste_zoom')

ex = example(s, 1, 'Droste zoom on a photo',
  'Banana.tif -> TOP_droste_zoom -> example1: the picture repeats inside itself and zooms forever.\n'
  'Innerscale sets how small each nested copy is (smaller = more copies on screen).\n'
  'Zoomperiods sets zoom direction and how many copies pass per loop; Loopseconds sets loop length.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(src)
out(ex, 1, g)

ex = example(s, 2, 'Spiral Droste with spin',
  'Rotation twists each nested copy (a spiral); Spin turns the whole picture, in whole turns per loop so it still loops.\n'
  'Try Zoomperiods = -1 to zoom out, and Seam to soften the ring joins. Mix drops back to the dry image.')
mv = ex.create(moviefileinTOP, 'jelly'); mv.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(mv)
g.par.Innerscale = 0.4; g.par.Rotation = 0.25; g.par.Spin = 1; g.par.Seam = 0.8; g.par.Zoomperiods = 2
out(ex, 2, g)

ex = example(s, 3, 'Clock-driven zoom + beat pump',
  'A ramp LFO named phase drives the Clock parameter (Timesource = phase): one ramp cycle = one loop.\n'
  'A Beat-style LFO named band1 goes into the modulation input (last input): each pulse pushes Innerscale (Modamount).\n'
  'Replace the LFOs with a Beat CHOP / audio analysis to lock the tunnel to your music.')
src = ex.create(moviefileinTOP, 'banana', row=1); src.par.file.expr = sample_expr('Map/Banana.tif')
lfo = ex.create(lfoCHOP, 'clock', row=2); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.125; lfo.par.channelname = 'phase'
lfo.par.amp = 1; lfo.par.offset = 0
b1 = ex.create(lfoCHOP, 'band1', row=3); b1.par.wavetype = 'sin'; b1.par.frequency = 1.0; b1.par.channelname = 'band1'
b1.par.amp = 0.5; b1.par.offset = 0.5
g = instance(ex, 'TOP_droste_zoom')
g.inputConnectors[0].connect(src)
g.inputConnectors[1].connect(b1)
g.par.Clock = lfo; g.par.Timesource = 'phase'; g.par.Modamount = 1.0
out(ex, 3, g)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
