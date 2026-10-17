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
    'beat' -> channels `beat` (pulse) and `phase` (0-1 ramp) from a Beat CHOP."""
    if kind == 'lfo':
        l = ex.create(td.lfoCHOP, name or 'lfo', col=col, row=1)
        l.par.frequency = freq; l.par.amp = 0.5; l.par.offset = 0.5
        r = ex.create(td.renameCHOP, 'as_' + chan, col=col + 1, row=1)
        r.inputConnectors[0].connect(l); r.par.renamefrom = 'chan1'; r.par.renameto = chan
        return r
    b = ex.create(td.beatCHOP, name or 'beat', col=col, row=1)
    b.par.pulse = True; b.par.ramp = True
    r = ex.create(td.renameCHOP, 'as_beat_phase', col=col + 1, row=1)
    r.inputConnectors[0].connect(b); r.par.renamefrom = 'pulse ramp'; r.par.renameto = 'beat phase'
    return r


def keep_settings(s):
    """Keep the parameter values set above when the snippet is reloaded (otherwise the external tox
    would reset the instance's custom parameters to the library defaults)."""
    for c in s.findChildren(type=td.baseCOMP, depth=1):
        if c.par.externaltox.eval():
            c.par.reloadcustom = False


s = begin('TOP_glitch')

ex = example(s, 1, 'Glitch a movie',
    'Movie -> TOP_glitch -> example1.\nDefaults give RGB split, block shifts, scanline tears, pixel sorting and smear.\nRaise Amount (0-2) for chaos, lower Rate for slower hits, change Seed to get a different glitch sequence.')
m = media(ex, 'Map/Nature/Movie.1.mp4', col=0)
g = instance(ex, 'TOP_glitch', col=1)
g.par.Amount = 1.4; g.par.Rate = 2
connect(m, g); out(ex, 1, g, col=2)

ex = example(s, 2, 'Pixel-sort and smear only',
    'Turn off the RGB/block/tear layers and push Pixelsort and Smear for a datamosh-like drag.\nSortthreshold sets which brightness range gets sorted; Sortaxis picks the direction.\nSmearblock sets the macro-block size of the held/smeared blocks.')
m = media(ex, 'Map/Jellybeans.1.jpg', col=0)
g = instance(ex, 'TOP_glitch', col=1)
g.par.Rgbsplit = 0.1; g.par.Blockdisplace = 0; g.par.Scanlinetear = 0.1
g.par.Pixelsort = 1; g.par.Smear = 0.9; g.par.Sortaxis = 'vertical'; g.par.Sortthreshold = 0.3
g.par.Smearblock = 24; g.par.Amount = 1.5; g.par.Rate = 1.5
connect(m, g); out(ex, 2, g, col=2)

ex = example(s, 3, 'Glitch driven by a modulation CHOP',
    'The last (CHOP) input takes band1-band4 / beat / phase channels. Here an LFO called band1 and a Beat CHOP pulse (beat) both push Amount up.\nTry replacing the LFO with an Audio Spectrum CHOP split into band1-band4 for audio-reactive glitch.\nKeep the base Amount low so the glitch only blooms on the hits.')
m = media(ex, 'Map/Nature/Movie.3.mp4', col=0)
g = instance(ex, 'TOP_glitch', col=1)
g.par.Amount = 0.35
l = modsrc(ex, 'lfo', 'band1', 0.5, col=3)
b = modsrc(ex, 'beat', col=5)
mg = ex.create(td.mergeCHOP, 'mod', col=7, row=1); mg.inputConnectors[0].connect(l); mg.inputConnectors[0].connect(b)
connect(m, g); connect(mg, g, in_index=1); out(ex, 3, g, col=2)

keep_settings(s)
finish(s)
