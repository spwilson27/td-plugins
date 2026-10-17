exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_mirror_room')

ex = example(s, 1, 'Mirror room', 'GEN_mirror_room with defaults: a torus spinning inside a six-sided mirrored box.\nEvery wall reflects every other, giving infinite recursive reflections.\nTry: Bounces (more = deeper reflections), Mirror (reflectivity), Shape.')
m = instance(ex, 'GEN_mirror_room')
out(ex, 1, m)

ex = example(s, 2, 'Knot with kaleidoscope folds', 'Shape = knot and Kaleido = 2 fold the space into a kaleidoscope before reflecting.\nIce palette and a slightly less reflective Mirror keep the detail readable.\nSpin sets whole turns per loop, so it still loops seamlessly.')
m = instance(ex, 'GEN_mirror_room')
m.par.Shape = 'knot'; m.par.Kaleido = 2; m.par.Palette = 'ice'; m.par.Mirror = 0.7; m.par.Spin = 2
out(ex, 2, m)

ex = example(s, 3, 'Driven by an LFO ramp', 'A ramp LFO named phase drives Clock; Timesource = phase.\nOne ramp cycle (8 s here) is exactly one spin loop; change the LFO frequency to retime the spin live.\nUse a Beat CHOP ramp instead to lock the spin to a tempo.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.125; lfo.par.channelname = 'phase'; lfo.par.amp = 1; lfo.par.offset = 0
m = instance(ex, 'GEN_mirror_room')
m.par.Clock = lfo; m.par.Timesource = 'phase'; m.op('clock_exec').module.sync(m); m.par.Shape = 'sphere'; m.par.Bounces = 8
out(ex, 3, m)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
