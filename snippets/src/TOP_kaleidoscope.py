exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())


def media(ex, rel, name='media', col=None):
    """Movie / image from the TouchDesigner Samples folder (path resolved at load time)."""
    isimg = rel.lower().endswith(('.tif', '.jpg', '.png'))
    m = ex.create(td.moviefileinTOP, name, col=col)
    m.par.file.expr = sample_expr(rel)
    if not isimg:
        m.par.play = True
    return m


def modsrc(ex, kind, chan='band1', freq=0.35, name=None, col=None):
    """A modulation CHOP for the component's last input: 'lfo' -> one 0-1 channel called `chan`;
    'beat' -> channel `beat` (pulse) from a Beat CHOP."""
    if kind == 'lfo':
        l = ex.create(td.lfoCHOP, name or 'lfo', col=col, row=1)
        l.par.frequency = freq; l.par.amp = 0.5; l.par.offset = 0.5
        r = ex.create(td.renameCHOP, 'as_' + chan, col=col + 1, row=1)
        r.inputConnectors[0].connect(l); r.par.renamefrom = 'chan1'; r.par.renameto = chan
        return r
    b = ex.create(td.beatCHOP, name or 'beat', col=col, row=1)
    b.par.pulse = True; b.par.ramp = False
    r = ex.create(td.renameCHOP, 'as_beat', col=col + 1, row=1)
    r.inputConnectors[0].connect(b); r.par.renamefrom = 'pulse'; r.par.renameto = 'beat'
    return r


def keep_settings(s):
    """Keep the parameter values set above when the snippet is reloaded (otherwise the external tox
    would reset the instance's custom parameters to the library defaults)."""
    for c in s.findChildren(type=td.baseCOMP, depth=1):
        if c.par.externaltox.eval():
            c.par.reloadcustom = False


s = begin('TOP_kaleidoscope')

ex = example(s, 1, 'N-fold kaleidoscope',
    'Image -> TOP_kaleidoscope -> example1. Mode = N-fold radial mirrors a wedge of the source around the centre.\nSegments sets the number of mirrors, Rotation and Zoom spin and scale the pattern, Srczoom picks how much of the source is sampled.\nCenter moves the pivot.')
m = media(ex, 'Map/Banana.tif', col=0)
k = instance(ex, 'TOP_kaleidoscope', col=1)
k.par.Segments = 10
connect(m, k); out(ex, 1, k, col=2)

ex = example(s, 2, 'Hex mirror tiles',
    'Mode = hex mirror tiles: the source is reflected across a hexagonal grid.\nTiles sets the grid density. Try the square and triangle tile modes for other wallpaper symmetries.\nAnimate with Speed to drift the sampling point.')
m = media(ex, 'Map/Jellybeans.1.jpg', col=0)
k = instance(ex, 'TOP_kaleidoscope', col=1)
k.par.Mode = '3'; k.par.Tiles = 3
connect(m, k); out(ex, 2, k, col=2)

ex = example(s, 3, 'Hyperbolic, kicked by a beat',
    'Mode = hyperbolic (Poincare disk).\nThe beat pulse (Beat CHOP, channel "beat") nudges Zoom through the modulation input; band1 would add rotation.\nHyperq changes the tiling of the disk.')
m = media(ex, 'Map/Nature/Movie.5.mp4', col=0)
k = instance(ex, 'TOP_kaleidoscope', col=1)
k.par.Mode = '4'; k.par.Segments = 6; k.par.Hyperq = 5
b = modsrc(ex, 'beat', col=3)
connect(m, k); connect(b, k, in_index=1); out(ex, 3, k, col=2)

keep_settings(s)
finish(s)
