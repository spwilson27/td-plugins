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


def movers(ex, col, bg=None):
    """Fast-moving test pattern so the time displacement is obvious: spinning checker, or a swinging
    ball over `bg`."""
    cc = ex.create(td.circleTOP, 'ball', col=col, row=1)
    cc.par.outputresolution = 'custom'; cc.par.resolutionw = 1280; cc.par.resolutionh = 720
    cc.par.radiusx = 0.1; cc.par.radiusy = 0.1; cc.par.fillcolorr = 1; cc.par.fillcolorg = 0.2; cc.par.fillcolorb = 0.1
    tr = ex.create(td.transformTOP, 'swing', col=col + 1, row=1)
    tr.inputConnectors[0].connect(cc); tr.par.tx.expr = '0.35*math.sin(absTime.seconds*2.5)'; tr.par.ty.expr = '0.2*math.sin(absTime.seconds*1.7)'
    ov = ex.create(td.overTOP, 'over', col=col + 2, row=1)
    ov.inputConnectors[0].connect(tr); ov.inputConnectors[1].connect(bg)
    return ov


s = begin('TOP_slit_scan')

ex = example(s, 1, 'Slit-scan a moving subject',
    'A swinging ball -> TOP_slit_scan -> example1 (use any movie in practice). Each pixel is read from a different past frame, chosen by a horizontal gradient, so motion smears into time-bent shapes.\nFrames is how far back the slit reaches (about 2 s at 60 fps here: Frames 126 with Buffersize 128 on the Render page).\nGive it a few seconds to fill the buffer.')
bgr = ex.create(td.rampTOP, 'backdrop', col=0, row=2); bgr.par.type = 'horizontal'; bgr.par.outputresolution = 'custom'; bgr.par.resolutionw = 1280; bgr.par.resolutionh = 720
m = movers(ex, 0, bg=bgr)
sl = instance(ex, 'TOP_slit_scan', col=3)
sl.par.Buffersize = 128; sl.par.Frames = 126
connect(m, sl); out(ex, 1, sl, col=4)

ex = example(s, 2, 'Radial time tunnel',
    'Mode = radial: the age of the pixel depends on its distance from the centre, producing a rippling time tunnel.\nSpeed scrolls the map; Direction flips which side is past. Smooth interpolates between frames.\nShorter Frames gives a tighter effect.')
mm = ex.create(td.moviefileinTOP, 'media', col=0, row=2); mm.par.file.expr = sample_expr('Map/Nature/Movie.2.mp4'); mm.par.play = True
m = movers(ex, 0, bg=mm)
sl = instance(ex, 'TOP_slit_scan', col=3)
sl.par.Buffersize = 128; sl.par.Mode = 'radial'; sl.par.Frames = 126; sl.par.Speed = 0.3
connect(m, sl); out(ex, 2, sl, col=4)

ex = example(s, 3, 'Custom time map (in2) with LFO depth',
    'Mode = in2 uses any image on the second input as the time map (a Ramp TOP here, rotated by a Transform; brighter = older).\nAn LFO called band1 on the CHOP input scales Frames so the smear breathes.\nTry a Noise or Movie as the map for organic distortions.')
mm = ex.create(td.moviefileinTOP, 'media', col=0, row=2); mm.par.file.expr = sample_expr('Map/Nature/Movie.2.mp4'); mm.par.play = True
m = movers(ex, 0, bg=mm)
rp = ex.create(td.rampTOP, 'map', col=3, row=2)
rp.par.type = 'radial'
sl = instance(ex, 'TOP_slit_scan', col=3)
sl.par.Buffersize = 128; sl.par.Mode = 'in2'; sl.par.Frames = 126
l = modsrc(ex, 'lfo', 'band1', 0.3, col=3)
connect(m, sl); sl.inputConnectors[1].connect(rp); connect(l, sl, in_index=2); out(ex, 3, sl, col=4)

keep_settings(s)
finish(s)
