exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_infinite_tunnel')

ex = example(s, 1, 'Endless corridor', 'GEN_infinite_tunnel with defaults: a raymarched sci-fi corridor you fly down forever.\nSegments are plain, ribbed, lit, or bulkheads, picked by a hash of the segment index.\nTry: Speed for flight speed, Sway/Roll for camera motion, Seed for a new layout.')
t = instance(ex, 'GEN_infinite_tunnel')
out(ex, 1, t)

ex = example(s, 2, 'Ember palette, tighter cut', 'A narrow, tall tube with the Ember palette, more lights and more non-plain segments.\nVariation sets how many segments are non-plain; Lights scales emitter strength.\nLower Fog to see further; raise Exposure if the palette looks dim.')
t = instance(ex, 'GEN_infinite_tunnel')
t.par.Palette = 'ember'; t.par.Width = 1.1; t.par.Height = 1.8; t.par.Variation = 0.9; t.par.Lights = 1.8; t.par.Fog = 0.6; t.par.Seed = 17
out(ex, 2, t)

ex = example(s, 3, 'Beat-locked flight', 'A Beat CHOP bar ramp renamed phase drives Clock; Timesource = phase.\nOne bar = one loop of Segments-per-Loop corridor segments, so a bulkhead hits on the downbeat.\nRaise Segments for faster flight at the same BPM.')
bt = ex.create(beatCHOP, 'beat'); bt.par.bpm = 120; bt.par.ramp = False; bt.par.rampbar = True
rn = ex.create(renameCHOP, 'phase'); rn.inputConnectors[0].connect(bt); rn.par.renamefrom = 'rampbar'; rn.par.renameto = 'phase'
t = instance(ex, 'GEN_infinite_tunnel')
t.par.Clock = rn; t.par.Timesource = 'phase'; t.op('clock_exec').module.sync(t); t.par.Segments = 8
out(ex, 3, t)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
