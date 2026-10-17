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


s = begin('TOP_halftone')

ex = example(s, 1, 'CMYK halftone',
    'Image -> TOP_halftone -> example1. Mode = halftone with the CMYK screen: four rotated dot grids like a printed comic.\nCellsize sets the dot pitch, Angle rotates the screen, Softness blurs the dot edges.\nHalftonetype = mono gives a single black-dot screen.')
m = media(ex, 'Map/Banana.tif', col=0)
h = instance(ex, 'TOP_halftone', col=1)
h.par.Cellsize = 10
connect(m, h); out(ex, 1, h, col=2)

ex = example(s, 2, 'Two-level Bayer dither',
    'Mode = dither. Levels = 2 is pure black and white; raise it for more tones. Dithertype picks the pattern (Bayer matrices, blue noise, error-diffusion look).\nKeepcolor keeps hue instead of mono. Ink and Paper set the two colours.\nGood for 1-bit looks; Invert swaps them.')
m = media(ex, 'Map/Jellybeans.1.jpg', col=0)
h = instance(ex, 'TOP_halftone', col=1)
h.par.Mode = 'dither'; h.par.Dithertype = 'bayer4'; h.par.Levels = 2; h.par.Cellsize = 3
connect(m, h); out(ex, 2, h, col=2)

ex = example(s, 3, 'ASCII movie, size on an LFO',
    'Mode = ascii turns each cell into a character from the Ramp string (dark to bright). An LFO named band1 swells Cellsize through the modulation input.\nKeepcolor tints the glyphs with the source colour; edit Ramp to change the character set.\nFeed audio bands in instead of the LFO to pump the grid size.')
m = media(ex, 'Map/Nature/Movie.1.mp4', col=0)
h = instance(ex, 'TOP_halftone', col=1)
h.par.Mode = 'ascii'; h.par.Cellsize = 10; h.par.Keepcolor = True
l = modsrc(ex, 'lfo', 'band1', 0.3, col=3)
connect(m, h); connect(l, h, in_index=1); out(ex, 3, h, col=2)

keep_settings(s)
finish(s)
