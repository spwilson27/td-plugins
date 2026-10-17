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


s = begin('TOP_vhs_crt')

ex = example(s, 1, 'VHS + CRT on a movie',
    'Movie -> TOP_vhs_crt -> example1. Mode "both" runs the tape stage then the CRT stage.\nAmount scales the whole effect; Mix blends back to the clean picture.\nTry Mode = vhs for tape only or crt for the tube only.')
m = media(ex, 'Map/Banana.tif', col=0)
v = instance(ex, 'TOP_vhs_crt', col=1)
connect(m, v); out(ex, 1, v, col=2)

ex = example(s, 2, 'Curved CRT close-up',
    'CRT only: heavy Curvature, strong Scanlines and aperture-mask (Maskstrength), plus Glow.\nScanlinecount is the number of tube lines; lower it for chunky retro-console looks.\nFlicker adds the mains-frequency brightness wobble.')
m = media(ex, 'Map/Jellybeans.1.jpg', col=0)
v = instance(ex, 'TOP_vhs_crt', col=1)
v.par.Mode = 'crt'; v.par.Curvature = 1.2; v.par.Scanlines = 1.0; v.par.Maskstrength = 0.8
v.par.Scanlinecount = 240; v.par.Glow = 1.0; v.par.Vignette = 1.0
connect(m, v); out(ex, 2, v, col=2)

ex = example(s, 3, 'Damaged tape on the beat',
    'VHS only with wide Chromashift and tracking noise. An LFO named band1 pushes Tracking and a Beat pulse named beat kicks Jitter.\nDrive the CHOP input from your audio analysis to make the tape "break" on drops.\nRaise Headswitch for the noisy bar at the bottom of the frame.')
m = media(ex, 'Map/Nature/Movie.4.mp4', col=0)
v = instance(ex, 'TOP_vhs_crt', col=1)
v.par.Mode = 'vhs'; v.par.Chromashift = 8; v.par.Noise = 0.9; v.par.Headswitch = 1.5; v.par.Wobble = 1.0
l = modsrc(ex, 'lfo', 'band1', 0.4, col=3)
b = modsrc(ex, 'beat', col=5)
mg = ex.create(td.mergeCHOP, 'mod', col=7, row=1); mg.inputConnectors[0].connect(l); mg.inputConnectors[0].connect(b)
connect(m, v); connect(mg, v, in_index=1); out(ex, 3, v, col=2)

keep_settings(s)
finish(s)
