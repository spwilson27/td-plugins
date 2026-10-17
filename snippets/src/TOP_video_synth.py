exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_video_synth')

ex = example(s, 1, 'Oscillator patch', 'GEN_video_synth with defaults (Bone Waves preset): three oscillators cross-modulate each other,\nthen an analytic echo trail and a palette are applied.\nTry: Mode (presets), Modulate (how hard each oscillator bends the next), Kaleid, Feedback.')
v = instance(ex, 'GEN_video_synth')
out(ex, 1, v)

ex = example(s, 2, 'Patching a photo in', 'A photo on in1 displaces the oscillator coordinates (Inputdisplace) and blends into the result (Inputmix).\nPreset Chrome Moire gives fine interference lines that bend around the banana; set Kaleid to mirror it.\nRaise Inputdisplace for stronger melting around the image edges.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
v = instance(ex, 'GEN_video_synth')
v.inputConnectors[0].connect(src)
v.par.Mode = 'chrome_moire'; v.op('preset_exec').module.onValueChange(v.par.Mode, 'bone_waves')
v.par.Inputmix = 0.6; v.par.Inputdisplace = 0.9; v.par.Modulate = 0.05
out(ex, 2, v)

ex = example(s, 3, 'Tempo-locked tunnel', 'A Beat CHOP bar ramp renamed phase drives Clock (Timesource = phase).\nOscillator Sync values are integer cycles per loop, so the pattern repeats exactly once per bar.\nChange bpm on the Beat CHOP or try another Mode preset; Feedback gives the trails.')
bt = ex.create(beatCHOP, 'beat'); bt.par.bpm = 120; bt.par.ramp = False; bt.par.rampbar = True
rn = ex.create(renameCHOP, 'phase'); rn.inputConnectors[0].connect(bt); rn.par.renamefrom = 'rampbar'; rn.par.renameto = 'phase'
v = instance(ex, 'GEN_video_synth')
v.par.Mode = 'tunnel'; v.op('preset_exec').module.onValueChange(v.par.Mode, 'bone_waves')
v.par.Clock = rn; v.par.Timesource = 'phase'; v.op('clock_exec').module.sync(v)
out(ex, 3, v)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
