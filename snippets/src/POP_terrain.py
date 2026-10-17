exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('POP_terrain')

def rig(ex, pop):
    r = render_pop(ex, pop, cam_dist=2.6, cam_height=2.3, res=(960, 540))
    g = ex.s.op('ex%d_geo' % ex.n)
    g.par.rx = -90
    m = ex.create(constantMAT, 'wire'); m.par.applypointcolor = True; m.par.wireframe = True; m.par.wirewidth = 1.5
    g.par.material = m
    r.par.lights = ''
    return r

ex = example(s, 1, 'Terrain from a grid POP', 'A Grid POP -> POP_terrain (Heightsource = noise). Points move along the grid normal by a scrolling noise heightmap.\nStyle = ridged gives sharp crests; Height sets relief, Scale the feature frequency, Speed the scroll.\nThe render is a wireframe Geometry COMP with the Color attribute from the component.')
gr = ex.create(gridPOP, 'grid'); gr.par.surftype = 'quads'; gr.par.sizex = 2; gr.par.sizey = 2; gr.par.cols = 80; gr.par.rows = 80
t = instance(ex, 'POP_terrain'); t.inputConnectors[0].connect(gr)
t.par.Style = 'ridged'; t.par.Height = 0.22; t.par.Speed = 0
r = rig(ex, t.op('out1'))
out(ex, 1, r)

ex = example(s, 2, 'Heightmap from a photo', 'Heightsource = input uses the TOP wired to the second input (here the Banana photo) as the heightmap.\nThe grid UVs sample it, so the picture shows up as relief; Terraced style turns it into stepped plateaus.\nTry Terraces and Height.')
gr = ex.create(gridPOP, 'grid'); gr.par.surftype = 'quads'; gr.par.sizex = 2; gr.par.sizey = 2; gr.par.cols = 80; gr.par.rows = 80
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
t = instance(ex, 'POP_terrain'); t.inputConnectors[0].connect(gr); t.inputConnectors[1].connect(src)
t.par.Heightsource = 'input'; t.par.Style = 'terraced'; t.par.Terraces = 8; t.par.Height = 0.22; t.par.Speed = 0
r = rig(ex, t.op('out1'))
out(ex, 2, r)

ex = example(s, 3, 'Modulated mono terrain', 'An LFO named band1 on the modulation input (third input) breathes the Height.\nLook = Mono with a red Accent on the peaks. Smooth style with a low Scale gives rolling hills.')
gr = ex.create(gridPOP, 'grid'); gr.par.surftype = 'quads'; gr.par.sizex = 2; gr.par.sizey = 2; gr.par.cols = 80; gr.par.rows = 80
lfo = ex.create(lfoCHOP, 'lfo'); lfo.par.channelname = 'band1'; lfo.par.frequency = 0.4; lfo.par.amp = 0.5; lfo.par.offset = 0.5
t = instance(ex, 'POP_terrain'); t.inputConnectors[0].connect(gr); t.inputConnectors[2].connect(lfo)
t.par.Style = 'smooth'; t.par.Scale = 2; t.par.Look = 'mono'; t.par.Accent = 0.8; t.par.Height = 0.22; t.par.Speed = 0.3
r = rig(ex, t.op('out1'))
out(ex, 3, r)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
