exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_pixel_stretch')
ex = example(s, 1, 'Slit-scan smear on a photo', 'Pixels crossing the luminance Threshold get dragged downward as fibrous streaks.\nTry: Direction, Threshold (which parts smear), Length (how far), Revert (how much of the clean image stays).')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_pixel_stretch'); g.inputConnectors[0].connect(src)
g.par.Threshold = 0.45; g.par.Length = 0.9; g.par.Revert = 0.3
out(ex, 1, g)
ex = example(s, 2, 'Sideways glitch on a movie', 'Count.mov smeared to the right with a wide Bandwidth for chunky stripes and strong Noise.\nInvert smears the dark parts instead; Animate wobbles the threshold over time.')
src = ex.create(moviefileinTOP, 'count'); src.par.file.expr = sample_expr('Map/Count.mov')
g = instance(ex, 'TOP_pixel_stretch'); g.inputConnectors[0].connect(src)
g.par.Direction = 'right'; g.par.Bandwidth = 12; g.par.Noise = 0.8; g.par.Length = 0.7; g.par.Threshold = 0.3
out(ex, 2, g)
ex = example(s, 3, 'Smear length kicked by band1', 'An LFO named band1 feeds the modulation input (in2).\nModamount scales how much band1 stretches Length: the smear lunges out on each pulse.\nSwap the LFO for a Beat or Audio Spectrum CHOP to hit on kicks.')
src = ex.create(moviefileinTOP, 'jelly'); src.par.file.expr = sample_expr('Map/Banana.tif')
l = ex.create(lfoCHOP, 'band1', row=1); l.par.channelname = 'band1'; l.par.frequency = 0.5; l.par.amp = 0.5; l.par.offset = 0.5
g = instance(ex, 'TOP_pixel_stretch'); g.inputConnectors[0].connect(src); g.inputConnectors[1].connect(l)
g.par.Modamount = 2.0; g.par.Length = 0.3; g.par.Threshold = 0.45; g.par.Revert = 0.3
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
