exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_instance_grid')

ex = example(s, 1, 'A photo as a 3D field', 'A real image into in1: every pixel of the Count X x Count Y grid becomes a box.\nLuminance sets the height, pixel colour sets the colour, and the camera slowly orbits.\nTry: Heightamt for taller towers, Countx/County for finer detail, Invert to flip bright and dark.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_instance_grid'); g.inputConnectors[0].connect(src)
g.par.Countx = 48; g.par.County = 32; g.par.Heightamt = 4.0
out(ex, 1, g)

ex = example(s, 2, 'Mono spheres recipe', 'A parameter recipe for a stark VJ look: Shape = Sphere, Look = Mono with a red Accent,\nWidth from Luma so bright pixels swell, and Rotamt for a twist. Lower Elevation for a low-angle shot.\nMix blends the render with the source image if you want a ghost of the photo underneath.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
g = instance(ex, 'TOP_instance_grid'); g.inputConnectors[0].connect(src)
g.par.Shape = '1'; g.par.Look = 'mono'; g.par.Accent = 0.8; g.par.Scaleamt = 0.8; g.par.Heightamt = 2.0
g.par.Countx = 56; g.par.County = 36; g.par.Basesize = 0.5; g.par.Rotamt = 0.5; g.par.Elevation = 30
out(ex, 2, g)

ex = example(s, 3, 'Pumping heights and a cone grid', 'An LFO named band1 goes into the modulation input (in2) and pumps the tower height;\nModamount sets how hard. Orbitspeed turns the camera around the grid.\nSwap in a Beat or Audio CHOP for real audio.')
mv = ex.create(moviefileinTOP, 'count'); mv.par.file.expr = sample_expr('Map/Count.mov')
b1 = ex.create(lfoCHOP, 'band1', row=2); b1.par.channelname = 'band1'; b1.par.frequency = 1.0; b1.par.amp = 0.5; b1.par.offset = 0.5
g = instance(ex, 'TOP_instance_grid'); g.inputConnectors[0].connect(mv)
connect(b1, g, in_index=1)
g.par.Modamount = 1.0; g.par.Shape = '2'; g.par.Orbitspeed = 0.5
out(ex, 3, g)

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
