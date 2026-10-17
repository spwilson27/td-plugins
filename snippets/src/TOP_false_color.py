exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_false_color')
ex = example(s, 1, 'Thermal camera on a photo', 'Banana.tif into in1 becomes a thermal (ironbow) image with sensor grain, edges and a reticle.\nTry: Map (X-Ray / Night Vision), Gain to push more of the image into hot colours, Isotherms for contour lines.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_false_color'); g.inputConnectors[0].connect(src)
g.par.Isotherms = 0.6; g.par.Gain = 1.6
out(ex, 1, g)
ex = example(s, 2, 'Night vision on a movie', 'Count.mov with the Night Vision map, a lot of noise and no HUD legend.\nUse Invert to flip hot/cold, Mixoriginal to bleed the real image back, Mix to fade the whole effect.')
src = ex.create(moviefileinTOP, 'count'); src.par.file.expr = sample_expr('Map/Count.mov')
g = instance(ex, 'TOP_false_color'); g.inputConnectors[0].connect(src)
g.par.Map = 'night'; g.par.Noise = 0.8; g.par.Legend = 0; g.par.Mixoriginal = 0.2
out(ex, 2, g)
ex = example(s, 3, 'Gain pumped by a beat LFO', 'An LFO named band1 goes into the modulation input (in3, the last one).\nModamount scales how far band1 pushes Gain, so the image flares hot on every pulse.\nReplace the LFO with an Audio Spectrum CHOP (0-1) to react to music.')
src = ex.create(moviefileinTOP, 'jelly'); src.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
l = ex.create(lfoCHOP, 'band1', row=1); l.par.channelname = 'band1'; l.par.frequency = 0.5; l.par.amp = 0.5; l.par.offset = 0.5
g = instance(ex, 'TOP_false_color'); g.inputConnectors[0].connect(src); g.inputConnectors[2].connect(l)
g.par.Modamount = 1.0; g.par.Gain = 0.5
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
