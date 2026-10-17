exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_kinetic_type')

ex = example(s, 1, 'Scatter on beat', 'GEN_kinetic_type with defaults: the word scatters apart on every beat and snaps back.\nAuto Beat fires Beats Per Loop times each loop; the Trigger pulse fires one by hand.\nTry: Amount (kick size), Beat Decay (how fast it settles), Text.')
k = instance(ex, 'GEN_kinetic_type')
out(ex, 1, k)

ex = example(s, 2, 'Extruded depth stack', 'Mode = Extrude stacks Layers copies of the text in depth, so it reads as a solid slab.\nDepth sets the slab thickness, Sway swings the camera so the stack reveals itself.\nChange Text to your own word, Fontname to another installed font.')
k = instance(ex, 'GEN_kinetic_type')
k.par.Mode = 'extrude'; k.par.Text = 'DEPTH'; k.par.Layers = 20; k.par.Depth = 8; k.par.Sway = 0.6
out(ex, 2, k)

ex = example(s, 3, 'Beats locked to a Clock CHOP', 'A ramp LFO named phase drives Clock (Timesource = phase), so Beats Per Loop kicks happen per LFO cycle.\nBeats Per Loop = 2 gives two kicks per cycle; a small Amount keeps each kick a gentle jolt.\nRaise Amount for explosions and lower Beat Decay for slower recovery.\nUse a Beat CHOP ramp for true tempo sync instead of the LFO.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.5; lfo.par.channelname = 'phase'; lfo.par.amp = 1; lfo.par.offset = 0
k = instance(ex, 'GEN_kinetic_type')
k.par.Clock = lfo; k.par.Timesource = 'phase'; k.op('clock_exec').module.sync(k); k.par.Text = 'FOUR ON THE FLOOR'; k.par.Beatsperloop = 2; k.par.Amount = 0.25; k.par.Decay = 4
out(ex, 3, k)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
