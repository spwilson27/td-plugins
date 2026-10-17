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


s = begin('TOP_feedback_trails')

ex = example(s, 1, 'Trails behind a moving movie',
    'Movie -> TOP_feedback_trails -> example1. Each frame is blended over a slightly zoomed, rotated copy of the last one.\nDecay (0.8-1) sets trail length: closer to 1 is longer. Scale > 1 makes trails fly outward.\nInject controls how strongly new frames are fed into the loop.')
m = media(ex, 'Map/Nature/Movie.5.mp4', col=0)
f = instance(ex, 'TOP_feedback_trails', col=1)
f.par.Decay = 0.95
connect(m, f); out(ex, 1, f, col=2)

ex = example(s, 2, 'Rainbow vortex',
    'Big Rotate, a little extra Scale, Huedrift cycling the trail colour and Noiseamount warping the feedback.\nBlend = max keeps the brightest of old and new (add can blow out to white). Reset clears the buffer.\nNoisescale sets the size of the displacement swirls, Noisespeed how fast they move.')
m = media(ex, 'Map/Nature/Movie.2.mp4', col=0)
f = instance(ex, 'TOP_feedback_trails', col=1)
f.par.Rotate = 3; f.par.Scale = 1.03; f.par.Huedrift = 10; f.par.Noiseamount = 1.5; f.par.Blend = 'max'; f.par.Decay = 0.94
connect(m, f); out(ex, 2, f, col=2)

ex = example(s, 3, 'Looping trails with an external Clock',
    'Timesource = phase and the Clock parameter points at a CHOP with a "phase" channel (a Beat CHOP ramp), so the animation repeats exactly every Loopbeats beats.\nLoopreset restarts the feedback at the loop start so a rendered loop is seamless.\nBand1 (not wired here) would scale Inject; Beat would kick Rotate.')
m = media(ex, 'Map/Nature/Movie.3.mp4', col=0)
f = instance(ex, 'TOP_feedback_trails', col=1)
f.par.Timesource = 'phase'; f.par.Loopbeats = 4; f.par.Loopreset = True; f.par.Rotate = 2; f.par.Decay = 0.95
b = modsrc(ex, 'beat', col=3)
f.par.Clock = b
connect(m, f); connect(b, f, in_index=1); out(ex, 3, f, col=2)

keep_settings(s)
finish(s)
