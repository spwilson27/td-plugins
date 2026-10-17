exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_flow_field_lines')
# reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.

ex = example(s, 1, 'Strokes flowing along a photo',
    'Banana.tif -> TOP_flow_field_lines -> example1. Particles are advected along a field built from the image\n(Fieldmode = contour: strokes follow edges) and take the colour of the pixel they pass over.\nTry: Inputamt (edge influence), Turbulence (noise vs. image), Fade (longer exposure), Reset pulse.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_flow_field_lines')
g.inputConnectors[0].connect(src)
out(ex, 1, g)

ex = example(s, 2, 'Hue angle field on a nature movie',
    'Fieldmode = hue: the colour of each pixel sets the stroke direction, so colour regions become separate swirls.\nCompose = on background shows the strokes alone; Colormode = direction gives a palette instead of image colour.\nout2 is the field itself (RG direction, B strength).')
src = ex.create(moviefileinTOP, 'movie'); src.par.file.expr = sample_expr('Map/Nature/Movie.2.mp4'); src.par.play = True
g = instance(ex, 'TOP_flow_field_lines')
g.inputConnectors[0].connect(src)
g.par.Fieldmode = 'hue'; g.par.Compose = 'bg'; g.par.Turbulence = 0.2; g.par.Fade = 0.97
out(ex, 2, g)

ex = example(s, 3, 'Audio-style modulation',
    'An LFO named band1 drives Speed and band1 pulses on the modulation input (last input).\nband2 adds turbulence, band3 intensity, band4 line width, beat kicks the field rotation.\nHere only band1 is wired: watch the strokes speed up and slow down.')
src = ex.create(moviefileinTOP, 'banana3'); src.par.file.expr = sample_expr('Map/Banana.tif')
m = modsrc(ex, 'lfo', chan='band1', freq=0.3, col=1) if 'modsrc' in globals() else None
if m is None:
    l = ex.create(lfoCHOP, 'lfo', row=1); l.par.frequency = 0.3; l.par.amp = 0.5; l.par.offset = 0.5
    m = ex.create(renameCHOP, 'as_band1', row=1); m.inputConnectors[0].connect(l); m.par.renamefrom = 'chan1'; m.par.renameto = 'band1'
g = instance(ex, 'TOP_flow_field_lines')
g.inputConnectors[0].connect(src); g.inputConnectors[1].connect(m)
g.par.Fieldmode = 'gradient'; g.par.Compose = 'add'; g.par.Colormode = 'image'
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
