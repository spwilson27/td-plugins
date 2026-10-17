exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_kinetic_type')

def glyph_render(ex, k, cam_z=9.0, row=0, res=(960, 540)):
    """Render out1 (one point per glyph) by instancing a slab on every point with P / rotation / scale / Color."""
    g = ex.create(geometryCOMP, 'geo', row=row)
    for o in list(g.children): o.destroy()
    b = g.create(rectangleSOP, 'quad'); b.par.sizex = 0.5; b.par.sizey = 1.0
    b.display = True; b.render = True
    mat = ex.create(constantMAT, 'mat', row=row + 1)
    mat.par.colormap = k.op('atlas')   # the component's glyph atlas; per-point uvrect picks the glyph
    mat.par.blending = 'on'; mat.par.srcblend = 'one'; mat.par.destblend = 'one'; mat.par.depthwriting = False
    g.par.material = mat
    o1 = k.op('out1')
    g.par.instancing = True; g.par.instancecountmode = 'oplength'
    g.par.instanceop = o1
    g.par.instancetx = 'P(0)'; g.par.instancety = 'P(1)'; g.par.instancetz = 'P(2)'
    g.par.instancerop = o1
    g.par.instancerx = 'rotation(0)'; g.par.instancery = 'rotation(1)'; g.par.instancerz = 'rotation(2)'
    g.par.instancesop = o1
    g.par.instancesx = 'scale(0)'; g.par.instancesy = 'scale(1)'; g.par.instancesz = 'scale(2)'
    g.par.instancetexmode = 'transform'; g.par.instancetexcoordop = o1
    g.par.instanceu = 'uvrect(0)'; g.par.instancev = 'uvrect(1)'
    g.par.instancescaleu = 'uvrect(2)'; g.par.instancescalev = 'uvrect(3)'
    g.par.instancecolorop = o1; g.par.instancecolormode = 'multiply'
    g.par.instancer = 'Color(0)'; g.par.instanceg = 'Color(1)'; g.par.instanceb = 'Color(2)'; g.par.instancea = 'Color(3)'
    cam = ex.create(cameraCOMP, 'cam', row=row + 1); cam.par.tz = cam_z
    r = ex.create(renderTOP, 'render', row=row)
    r.par.camera = cam; r.par.geometry = g
    r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = res
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.01; r.par.bgcolora = 1
    return r

ex = example(s, 1, 'Scatter on beat', 'out1 holds one POP point per glyph (P, rotation, scale, glyph, Color, uvrect). A Geometry COMP\ninstances an atlas quad on every point, so each glyph of the word is a letter that scatters on every beat and snaps back.\nTry: Amount (kick size), Decay, Text, Seed, the Trigger pulse.')
k = instance(ex, 'GEN_kinetic_type')
k.par.Amount = 0.35
out(ex, 1, glyph_render(ex, k))

ex = example(s, 2, 'Extruded depth stack', 'Mode = Extrude stacks Layers copies of every glyph in depth (layer attribute) and sways them.\nDepth sets the slab thickness; the point count is glyphs x layers.\nChange Text to your own word.')
k = instance(ex, 'GEN_kinetic_type')
k.par.Mode = 'extrude'; k.par.Text = 'DEPTH'; k.par.Layers = 14; k.par.Depth = 5
r = glyph_render(ex, k, cam_z=7.0)
out(ex, 2, r)

ex = example(s, 3, 'Modulated noise warp', 'Mode = Noise warp rides sine fields over the glyph points; an LFO named band1 on the modulation input\npumps the Amount of motion. (out2 is a plain text mesh POP of the string if you need real glyph outlines.)\nWire a Beat CHOP into beat for scatter kicks in Scatter mode.')
lfo = ex.create(lfoCHOP, 'lfo'); lfo.par.channelname = 'band1'; lfo.par.frequency = 0.4; lfo.par.amp = 0.5; lfo.par.offset = 0.5
k = instance(ex, 'GEN_kinetic_type')
k.inputConnectors[0].connect(lfo)
k.par.Mode = 'noise'; k.par.Text = 'WARP'; k.par.Amount = 0.5
out(ex, 3, glyph_render(ex, k, cam_z=8.0))
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
