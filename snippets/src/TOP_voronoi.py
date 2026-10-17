exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name, col=None):
    c = instance(ex, name, col=col)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def media(ex, rel, col=0):
    m = ex.create(td.moviefileinTOP, 'media', col=col)
    m.par.file.expr = sample_expr(rel)
    if not rel.lower().endswith(('.tif', '.jpg', '.png')): m.par.play = True
    return m

s = begin('TOP_voronoi')

ex = example(s, 1, 'Stained glass photo',
  'Map/Banana.tif -> TOP_voronoi (Style = stained) -> example1. Every cell takes the colour sampled from the picture at its site.\n'
  'Try Seeds for chunkier or finer glass, Borderwidth for the lead lines, and Style = cracked for a shattered window.')
m = media(ex, 'Map/Banana.tif')
v = inst(ex, 'TOP_voronoi')
v.par.Style = 'stained'; v.par.Seeds = 110; v.par.Borderwidth = 2.5; v.par.Speed = 0
connect(m, v); out(ex, 1, v)

ex = example(s, 2, 'Density follows edges',
  'Style = edges with Density Follows = Edges: seeds crowd around the contours of the picture so the cell borders trace it.\n'
  'Density Amount 0 gives an even scatter. Edge Tint blends the glow between the input colours and Edge Colour.')
m = media(ex, 'Map/Banana.tif')
v = inst(ex, 'TOP_voronoi')
v.par.Style = 'edges'; v.par.Seeds = 128; v.par.Densitymode = 'edges'; v.par.Densityamount = 1; v.par.Speed = 0; v.par.Glow = 1.5
connect(m, v); out(ex, 2, v)

ex = example(s, 3, 'Cell id / edge map and beat modulation',
  'out2 of TOP_voronoi is the cell id colour with edge distance in alpha (shown here). Use it to drive other effects.\n'
  'A Beat CHOP renamed to band1/beat is wired to the modulation input: it pulses the edge glow.')
m = media(ex, 'Map/Banana.tif')
v = inst(ex, 'TOP_voronoi')
v.par.Style = 'cells'; v.par.Seeds = 60; v.par.Speed = 0.3
connect(m, v)
bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False
rn = ex.create(td.renameCHOP, 'modnames', col=1, row=1); rn.inputConnectors[0].connect(bt)
rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
v.inputConnectors[1].connect(rn)
o = ex.create(td.nullTOP, 'x'); o.name = 'example3'; o.inputConnectors[0].connect(v.outputConnectors[1]); o.viewer = True
finish(s)
