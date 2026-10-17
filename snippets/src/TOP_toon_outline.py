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


s = begin('TOP_toon_outline')

ex = example(s, 1, 'Ink outlines and posterize',
    'Image -> TOP_toon_outline -> example1. Colours are posterized into Levels flat bands and edges are drawn as ink lines.\nThreshold sets how strong an edge must be, Edgewidth the line thickness, Colorweight how much colour changes (vs. brightness) count as edges.\nout2 is the raw edge map.')
m = media(ex, 'Map/Banana.tif', col=0)
t = instance(ex, 'TOP_toon_outline', col=1)
connect(m, t); out(ex, 1, t, col=2)

ex = example(s, 2, 'Neon edges on a dimmed picture',
    'Style = neon draws glowing coloured lines. Dim darkens the underlying image so the lines pop.\nEdgecolor sets the line colour; Glowsize and Glowamount control the halo.\nLevels = 2 gives a graphic poster base.')
m = media(ex, 'Map/Nature/Movie.2.mp4', col=0)
t = instance(ex, 'TOP_toon_outline', col=1)
t.par.Style = 'neon'; t.par.Edgecolorr = 0.1; t.par.Edgecolorg = 0.9; t.par.Edgecolorb = 1.0
t.par.Dim = 0.15; t.par.Glowamount = 2.5; t.par.Levels = 3
connect(m, t); out(ex, 2, t, col=2)

ex = example(s, 3, 'Comic book: toon outline into TOP_halftone',
    'Chains two library components: TOP_toon_outline for ink lines and flat colour, then TOP_halftone (CMYK dots) over the top.\nAn LFO named band1 thickens the lines through the toon modulation input.\nTweak halftone Cellsize for finer or coarser print dots.')
m = media(ex, 'Map/Banana.tif', col=0)
t = instance(ex, 'TOP_toon_outline', col=1)
t.par.Levels = 5
h = instance(ex, 'TOP_halftone', col=2)
h.par.Cellsize = 7; h.par.Mix = 0.7
l = modsrc(ex, 'lfo', 'band1', 0.3, col=4)
connect(m, t); connect(l, t, in_index=1); connect(t, h); out(ex, 3, h, col=3)

keep_settings(s)
finish(s)
