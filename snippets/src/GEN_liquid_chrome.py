exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_liquid_chrome')

ex = example(s, 1, 'Liquid chrome blob', 'GEN_liquid_chrome with defaults: a morphing metaball mirrored against a procedural studio.\nTry: Blobs (1-8), Displacement (surface ripple), Roughness (blurs the reflection),\nCamdistance and Camheight to frame it.')
l = instance(ex, 'GEN_liquid_chrome')
out(ex, 1, l)

ex = example(s, 2, 'Real environment + iridescence', 'A 360 photo on in1 replaces the procedural studio as the reflection environment.\nIridescence adds thin-film rainbow tints; Envrotation spins the environment (in turns).\nAny equirectangular image works: HDRIs give the most believable chrome.')
src = ex.create(moviefileinTOP, 'env'); src.par.file.expr = sample_expr('Map/PalaceOfFineArts-360Designs.io.jpg')
l = instance(ex, 'GEN_liquid_chrome')
l.inputConnectors[0].connect(src)
l.par.Iridescence = 0.6; l.par.Roughness = 0.02; l.par.Blobs = 3
out(ex, 2, l)

ex = example(s, 3, 'Clock-driven morph', 'A ramp LFO named phase drives Clock (Timesource = phase): one LFO cycle = one full morph loop.\nMorphspeed multiplies how many morph cycles fit in one loop; Blobs adds more shapes.\nSlow the LFO for a lava-lamp feel, speed it up for a throb.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.1; lfo.par.channelname = 'phase'; lfo.par.amp = 1; lfo.par.offset = 0
l = instance(ex, 'GEN_liquid_chrome')
l.par.Clock = lfo; l.par.Timesource = 'phase'; l.op('clock_exec').module.sync(l); l.par.Blobs = 6; l.par.Morphspeed = 2; l.par.Displacement = 0.9
out(ex, 3, l)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
