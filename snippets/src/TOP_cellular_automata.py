exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name, col=None):
    c = instance(ex, name, col=col)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def media(ex, rel, name='media', col=None):
    isimg = rel.lower().endswith(('.tif', '.jpg', '.png'))
    m = ex.create(td.moviefileinTOP, name, col=col)
    m.par.file.expr = sample_expr(rel)
    if not isimg: m.par.play = True
    return m

s = begin('TOP_cellular_automata')

ex = example(s, 1, 'Life grown from a photo',
  'Movie File In (Banana.tif) -> TOP_cellular_automata -> example1.\n'
  'Bright pixels (Threshold) seed Game of Life cells, and every cell keeps the colour of the picture beneath it.\n'
  'Input Backdrop shows the photo behind the cells. Press Reset to reseed; Cellsize sets the grid.\n'
  'Try Rule = brain or ltl, Invert to seed from the dark parts.')
m = media(ex, 'Map/Banana.tif', col=0)
c = inst(ex, 'TOP_cellular_automata', col=1)
c.par.Resolutionmode = 'custom'; c.par.Resolutionw = 960; c.par.Resolutionh = 540
c.par.Threshold = 0.3; c.par.Density = 0.5; c.par.Cellsize = 5; c.par.Backdrop = 0.3
connect(m, c); out(ex, 1, c, col=2)

ex = example(s, 2, 'Injecting cells from a movie',
  'Movie File In (Count.mov) -> TOP_cellular_automata with Rule = brain.\n'
  'Inject Amount keeps spawning cells wherever the live picture is bright, so moving shapes leave\n'
  "sparking Brian's Brain trails. Coloring = age uses the Dead/Alive/Old colours instead of the movie.\n"
  'Raise Ghost for longer afterimages. out2 carries the raw state (r = state, g = age).')
m = media(ex, 'Map/Count.mov', col=0)
c = inst(ex, 'TOP_cellular_automata', col=1)
c.par.Resolutionmode = 'custom'; c.par.Resolutionw = 960; c.par.Resolutionh = 540
c.par.Rule = 'brain'; c.par.Threshold = 0.5; c.par.Inject = 0.012; c.par.Density = 0.2; c.par.Cellsize = 5
c.par.Backdrop = 0.15; c.par.Ghost = 0.4
connect(m, c); out(ex, 2, c, col=2)

ex = example(s, 3, 'LFO-driven injection',
  'LFO CHOP -> Rename (chan1 -> band1) -> modulation input (the last input).\n'
  'band1 scales Inject Amount (x1..x3) and a beat channel would add bursts, so the colonies pulse.\n'
  'Rule = ltl grows smooth organic blobs. Radius (Sim page) sets the blob size.')
m = media(ex, 'Map/Banana.tif', col=0)
l = ex.create(td.lfoCHOP, 'lfo', col=0, row=1); l.par.amp = 0.5; l.par.offset = 0.5; l.par.frequency = 0.3
r = ex.create(td.renameCHOP, 'as_band1', col=1, row=1); r.inputConnectors[0].connect(l)
r.par.renamefrom = 'chan1'; r.par.renameto = 'band1'
c = inst(ex, 'TOP_cellular_automata', col=1)
c.par.Resolutionmode = 'custom'; c.par.Resolutionw = 960; c.par.Resolutionh = 540
c.par.Rule = 'ltl'; c.par.Threshold = 0.3; c.par.Inject = 0.01; c.par.Density = 0.5; c.par.Cellsize = 3; c.par.Backdrop = 0.2
connect(m, c); connect(r, c, in_index=1); out(ex, 3, c, col=2)
finish(s)
