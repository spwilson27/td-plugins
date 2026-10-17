exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_glyphs')

ex = example(s, 1, 'ASCII a photo', 'Banana photo -> TOP_glyphs (Grid layout). Each cell takes its glyph from the cell luminance\n(Charset runs dark to bright) and its colour from the photo.\nTry: Cols (cell size), Contrast, Invert, Background (dim original behind the glyphs), a different Charset.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_glyphs'); g.inputConnectors[0].connect(src)
g.par.Cols = 90; g.par.Background = 0.1
out(ex, 1, g)

ex = example(s, 2, 'Digital rain over footage', 'Layout = Rain: columns of glyphs fall with fading tails and only light up the picture where the tail passes.\nTail sets the length, Trailfloor how much of the picture stays visible between tails.\nA binary Charset reads like classic digital rain.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_glyphs'); g.inputConnectors[0].connect(src)
g.par.Layout = 'rain'; g.par.Charset = ' 01'; g.par.Cols = 90; g.par.Tail = 14; g.par.Trailfloor = 0.3; g.par.Speed = 1.5
out(ex, 2, g)

ex = example(s, 3, 'Mono tunnel driven by a modulation CHOP', 'Layout = Tunnel wraps the glyph grid around a vanishing point (polar remap); Look = Mono with a red Accent.\nAn LFO named band1 on the modulation input pumps Contrast, a Beat-style pulse on beat flashes glyphs.\nTwist spirals the tunnel; out2 is the glyph index field.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
lfo = ex.create(lfoCHOP, 'lfo'); lfo.par.channelname = 'band1'; lfo.par.frequency = 0.5; lfo.par.amp = 0.5; lfo.par.offset = 0.5
g = instance(ex, 'TOP_glyphs'); g.inputConnectors[0].connect(src)
g.inputConnectors[1].connect(lfo)
g.par.Layout = 'tunnel'; g.par.Cols = 48; g.par.Look = 'mono'; g.par.Accent = 0.4; g.par.Twist = 0.3; g.par.Background = 0.0; g.par.Brightness = 1.0; g.par.Cols = 64
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
