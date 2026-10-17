exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_video_synth')

ex = example(s, 1, 'Oscillators bend a photo', 'Banana photo -> TOP_video_synth (Bone Waves preset). Three cross-modulating oscillators displace the picture,\nrotate its hue (Colorize) and are blended on top (Pattern).\nTry: Displace, Modulate, Pattern, Colorize, and the Preset menu.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
v = instance(ex, 'TOP_video_synth'); v.inputConnectors[0].connect(src)
v.par.Displace = 1.2; v.par.Pattern = 0.3; v.par.Colorize = 0.5
out(ex, 1, v)

ex = example(s, 2, 'Kaleidoscope and echo', 'Preset Red Kaleid folds the picture into 8 mirrored segments and adds a zoom/rotate echo trail.\nKaleid, Feedback, Echozoom and Echorot shape the tunnel of echoes; Mixmode = Difference/Multiply changes how the oscillators combine with the input.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
v = instance(ex, 'TOP_video_synth'); v.inputConnectors[0].connect(src)
v.par.Preset = 'red_kaleid'; v.op('preset_exec').module.apply(v, 'red_kaleid')
out(ex, 2, v)

ex = example(s, 3, 'Luma key with modulation', 'Mixmode = Luma key: oscillator patterns appear where the picture is dark (Keylevel is the threshold).\nAn LFO named band1 on the modulation input pumps Displace; Beat-style channels band2/band3/beat modulate frequency, echo and hue.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
lfo = ex.create(lfoCHOP, 'lfo'); lfo.par.channelname = 'band1'; lfo.par.frequency = 0.4; lfo.par.amp = 1; lfo.par.offset = 1
v = instance(ex, 'TOP_video_synth'); v.inputConnectors[0].connect(src); v.inputConnectors[1].connect(lfo)
v.par.Preset = 'luma_key'; v.op('preset_exec').module.apply(v, 'luma_key'); v.par.Palette = 'rainbow'; v.par.Keylevel = 0.3
out(ex, 3, v)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
