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


s = begin('TOP_filmic_look')

ex = example(s, 1, 'Filmic grade on footage',
    'Movie -> TOP_filmic_look -> example1: bloom, glare streaks, chromatic aberration, ACES tonemap, grain and vignette.\nExposure (stops) pushes more of the image into bloom; Tonemap picks the shoulder.\nEverything is subtle by default; compare with Bypass on.')
m = media(ex, 'Map/Banana.tif', col=0)
f = instance(ex, 'TOP_filmic_look', col=1)
f.par.Bloomamount = 1.2; f.par.Chromatic = 1.5; f.par.Vignette = 0.6; f.par.Exposure = 0.5
connect(m, f); out(ex, 1, f, col=2)

ex = example(s, 2, 'Hot bloom and anamorphic glare',
    'Lower Bloomthreshold so more of the picture blooms, raise Glareamount and Glarelength for streaks, and add Chromatic and Grain.\nGlaretint colours the streaks (blue is the classic anamorphic look).\nBloomsize widens the halo.')
m = media(ex, 'Map/Banana.tif', col=0)
f = instance(ex, 'TOP_filmic_look', col=1)
f.par.Exposure = 1.0; f.par.Bloomthreshold = 0.45; f.par.Bloomamount = 1.6; f.par.Glareamount = 1.8; f.par.Glarelength = 0.6
f.par.Chromatic = 2.0; f.par.Grain = 0.15; f.par.Vignette = 0.7; f.par.Tonemap = 'filmic'
connect(m, f); out(ex, 2, f, col=2)

ex = example(s, 3, 'Breathing bloom from an LFO',
    'An LFO renamed band1 drives Bloomamount through the modulation input; a Beat pulse named beat adds an exposure kick.\nSwap the LFO for an Audio Spectrum band for music-reactive bloom.\nKeep Bloomthreshold low enough that there is something to bloom.')
m = media(ex, 'Map/Nature/Movie.4.mp4', col=0)
f = instance(ex, 'TOP_filmic_look', col=1)
f.par.Bloomthreshold = 0.3
l = modsrc(ex, 'lfo', 'band1', 0.25, col=3)
b = modsrc(ex, 'beat', col=5)
mg = ex.create(td.mergeCHOP, 'mod', col=7, row=1); mg.inputConnectors[0].connect(l); mg.inputConnectors[0].connect(b)
connect(m, f); connect(mg, f, in_index=1); out(ex, 3, f, col=2)

keep_settings(s)
finish(s)
