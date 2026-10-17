exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_fractal_zoom')

ex = example(s, 1, 'Mandelbulb orbit', 'GEN_fractal_zoom with defaults: a raymarched Mandelbulb orbiting and breathing in and out.\nTry: Power (2-16) reshapes the bulb, Glow and Ao change the mood, Palette picks the colouring.\nMorph + Morphmotion animate the shape over the loop.')
f = instance(ex, 'GEN_fractal_zoom')
out(ex, 1, f)

ex = example(s, 2, 'Infinite Menger zoom', 'Fractal = KIFS Menger: the camera dives toward a corner of the sponge forever.\nZoomloops sets how many 3x zoom levels one loop covers (more = faster dive).\nPalette Chrome with a low Glow looks like polished metal; raise Iterations for finer detail.')
f = instance(ex, 'GEN_fractal_zoom')
f.par.Fractal = 'menger'; f.par.Palette = 1; f.par.Zoomloops = 2; f.par.Glow = 0.3; f.par.Resolutionw = 960; f.par.Resolutionh = 540
out(ex, 2, f)

ex = example(s, 3, 'Tempo-locked with a Clock CHOP', 'A Beat CHOP ramp renamed phase feeds the Clock parameter; Timesource = phase.\nOne bar of the beat clock = one full orbit/zoom loop, locked to the BPM (change bpm on the Beat CHOP).\nAny CHOP with a 0-1 channel called phase works: LFO ramp, timeline, MIDI clock.')
bt = ex.create(beatCHOP, 'beat'); bt.par.bpm = 120; bt.par.ramp = False; bt.par.rampbar = True
rn = ex.create(renameCHOP, 'phase'); rn.inputConnectors[0].connect(bt); rn.par.renamefrom = 'rampbar'; rn.par.renameto = 'phase'
f = instance(ex, 'GEN_fractal_zoom')
f.par.Clock = rn; f.par.Timesource = 'phase'; f.op('clock_exec').module.sync(f); f.par.Palette = 2; f.par.Resolutionw = 960; f.par.Resolutionh = 540
out(ex, 3, f)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
