exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_pixel_sort')

# 1. still image
ex = example(s, 1, 'Sort a photo', 'Movie File In (Trillium.jpg) -> TOP_pixel_sort -> example1.\nPixels brighter than Thresholdlow and darker than Thresholdhigh get sorted along Direction.\nRaise Passes for longer smears (it is sorted a few steps per frame, so let it run a second or two).\nPress Reset to start the sort again from the clean picture.')
m = ex.create(moviefileinTOP, 'photo'); m.par.file.expr = sample_expr('Map/Trillium.jpg')
g = instance(ex, 'TOP_pixel_sort'); g.inputConnectors[0].connect(m)
g.par.Passes = 16; g.par.Bytebeat = 0; g.par.Shuffle = 0; g.par.Loopfade = 0; g.par.Refresh = 0
out(ex, 1, g)

# 2. recipe: vertical hue sort on a movie
ex = example(s, 2, 'Vertical hue drips on a movie', 'Movie File In (Count.mov) -> TOP_pixel_sort.\nRecipe for drips: Direction = Down, Key = Hue, Thresholdlow 0.05.\nRefresh (0.02-0.1) keeps pulling the live movie back in, so moving video stays readable.\nBytebeat and Shuffle add the bit-crush bands and colour swaps on top.')
m = ex.create(moviefileinTOP, 'movie'); m.par.file.expr = sample_expr('Map/Count.mov')
g = instance(ex, 'TOP_pixel_sort'); g.inputConnectors[0].connect(m)
g.par.Direction = 'down'; g.par.Key = 'hue'; g.par.Thresholdlow = 0.05; g.par.Refresh = 0.05
g.par.Passes = 12; g.par.Loopfade = 0; g.par.Bytebeat = 0.35; g.par.Shuffle = 0.4
out(ex, 2, g)

# 3. modulation
ex = example(s, 3, 'Pulse the corruption with an LFO', 'LFO CHOP -> Rename (chan1 -> band1) -> TOP_pixel_sort modulation input.\nThe mod input channel band1 adds to Bytebeat, scaled by Modamount.\nSwap the LFO for a Beat or Audio Spectrum CHOP renamed band1 to hit the corruption on the kick.')
m = ex.create(moviefileinTOP, 'photo'); m.par.file.expr = sample_expr('Map/Banana.tif')
l = ex.create(lfoCHOP, 'lfo'); l.par.amp = 0.5; l.par.offset = 0.5; l.par.frequency = 0.5
r = ex.create(renameCHOP, 'rename'); r.inputConnectors[0].connect(l)
r.par.renamefrom = 'chan1'; r.par.renameto = 'band1'
g = instance(ex, 'TOP_pixel_sort'); g.inputConnectors[0].connect(m); g.inputConnectors[1].connect(r)
g.par.Passes = 10; g.par.Bytebeat = 0.0; g.par.Modamount = 1.0; g.par.Shuffle = 0.0; g.par.Loopfade = 0
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
