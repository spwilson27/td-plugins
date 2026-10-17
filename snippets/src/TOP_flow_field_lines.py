exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('GEN_flow_field_lines')
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.

ex = example(s, 1, 'Default flow field', 'GEN_flow_field_lines with defaults: 40k particles ride a curl-noise field and leave\nfading strokes in a long-exposure buffer.\nTry: Fieldscale (bigger = tighter swirls), Fade (closer to 1 = longer trails), Reset pulse.')
g = instance(ex, 'GEN_flow_field_lines')
out(ex, 1, g)

ex = example(s, 2, 'Flow driven by an image', 'A photo into in1: its luminance sets the flow angle, so strokes bend around the shapes.\nRaise Inputamt for stronger image steering, switch Colormode to Palette by direction.\nTurbulence adds noise back in so the lines do not collapse into the edges.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'GEN_flow_field_lines')
g.inputConnectors[0].connect(src)
g.par.Inputamt = 2.0; g.par.Colormode = 1; g.par.Turbulence = 0.25; g.par.Fade = 0.99
out(ex, 2, g)

ex = example(s, 3, 'Looping with a Clock CHOP', 'A ramp LFO named phase drives the Clock parameter (Timesource = phase).\nThe field then moves as a pure function of the ramp: one ramp cycle = one loop of field motion.\nTurn on Loopreset to clear the strokes at each wrap for a repeatable loop; change the LFO frequency to retime it.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.125; lfo.par.channelname = 'phase'
lfo.par.amp = 1; lfo.par.offset = 0
g = instance(ex, 'GEN_flow_field_lines')
g.par.Clock = lfo; g.par.Timesource = 'phase'; g.op('clock_exec').module.sync(g); g.par.Loopreset = True; g.par.Colormode = 2
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
