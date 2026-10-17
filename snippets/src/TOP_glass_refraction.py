exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_glass_refraction')
ex = example(s, 1, 'Glass blob over a photo', 'A morphing glass shape floats over Banana.tif and refracts it, with colour fringes at the edges.\nTry: Ior (bend strength), Dispersion (rainbow fringes), Shape, Size, Highlights.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_glass_refraction'); g.inputConnectors[0].connect(src)
g.par.Absorption = 0.1; g.par.Ior = 1.25; g.par.Frost = 0.15
out(ex, 1, g)
ex = example(s, 2, 'Frosted torus over a movie', 'Count.mov seen through a frosted glass torus.\nFrost blurs what is behind the glass, Absorption tints thick parts, Spin sets turns per loop.')
src = ex.create(moviefileinTOP, 'count'); src.par.file.expr = sample_expr('Map/Count.mov')
g = instance(ex, 'TOP_glass_refraction'); g.inputConnectors[0].connect(src)
g.par.Shape = 'torus'; g.par.Frost = 0.4; g.par.Dispersion = 0.25; g.par.Size = 1.3
out(ex, 2, g)
ex = example(s, 3, 'Glass bends on band1', 'An LFO named band1 feeds the modulation input (in2).\nModamount scales how much band1 raises the Ior, so the glass bends harder on each pulse.\nUse a Beat or Audio Spectrum CHOP to react to music.')
src = ex.create(moviefileinTOP, 'jelly'); src.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
l = ex.create(lfoCHOP, 'band1', row=1); l.par.channelname = 'band1'; l.par.frequency = 0.5; l.par.amp = 0.5; l.par.offset = 0.5
g = instance(ex, 'TOP_glass_refraction'); g.inputConnectors[0].connect(src); g.inputConnectors[1].connect(l)
g.par.Modamount = 2.0; g.par.Ior = 1.2; g.par.Shape = 'cube'
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
