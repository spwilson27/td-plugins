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


s = begin('TOP_optical_flow')

ex = example(s, 1, 'See the motion',
    'Movie -> TOP_optical_flow -> example1 with Mode = viz: motion direction is colour (hue) and speed is brightness.\nGain scales the strength; Smoothing and Regularization trade noise against detail.\nStatic areas stay black. out2 is the raw flow vector field.')
m = media(ex, 'Map/Nature/Movie.5.mp4', col=0)
o = instance(ex, 'TOP_optical_flow', col=1)
o.par.Mode = 'viz'; o.par.Gain = 3
connect(m, o); out(ex, 1, o, col=2)

ex = example(s, 2, 'Motion smear',
    'Mode = smear: the image is dragged along the detected motion into a feedback buffer, leaving painterly streaks where things move.\nPersistence (0-0.995) is how long the smear lingers; Gain how hard motion pushes it.\nReset clears the buffer.')
m = media(ex, 'Map/Nature/Movie.2.mp4', col=0)
o = instance(ex, 'TOP_optical_flow', col=1)
o.par.Mode = 'smear'; o.par.Gain = 10; o.par.Persistence = 0.96
connect(m, o); out(ex, 2, o, col=2)

ex = example(s, 3, 'Flow warp, gain on an LFO',
    'Mode = warp bends the picture by its own motion. An LFO named band1 swings Gain from calm to heavy warping through the CHOP input.\nFlowscale (Render page) trades flow quality for speed.\nUse audio bands on band1 for beat-driven warps.')
m = media(ex, 'Map/Nature/Movie.3.mp4', col=0)
o = instance(ex, 'TOP_optical_flow', col=1)
o.par.Mode = 'warp'; o.par.Gain = 8
l = modsrc(ex, 'lfo', 'band1', 0.3, col=3)
connect(m, o); connect(l, o, in_index=1); out(ex, 3, o, col=2)

keep_settings(s)
finish(s)
