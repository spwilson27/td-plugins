exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())


def media(ex, rel, name='media', col=None):
    """Movie / image from the TouchDesigner Samples folder (path resolved at load time)."""
    m = ex.create(td.moviefileinTOP, name, col=col)
    m.par.file.expr = sample_expr(rel)
    if not rel.lower().endswith(('.tif', '.jpg', '.png')):
        m.par.play = True
    return m


def rd(ex, col=1, row=0, w=960, h=540):
    r = instance(ex, 'TOP_reaction_diffusion', col=col, row=row)
    r.par.reloadcustom = False; r.par.reloadbuiltin = False
    r.par.Resolutionmode = 'custom'; r.par.Resolutionw = w; r.par.Resolutionh = h
    r.par.Steps = 60; r.par.Sprinkle = 1.0
    return r


s = begin('TOP_reaction_diffusion')

ex = example(s, 1, 'Pattern grown on a photo',
    'Banana.tif -> TOP_reaction_diffusion -> example1. The image seeds chemical B when the sim resets and its luminance\n'
    'shifts Feed and Kill, so the pattern changes character with the picture (maze in dark areas, nothing in bright ones).\n'
    'Try Colormode (tint / multiply / emboss / warp), Feedmod / Killmod (how strongly the image steers it) and Reset.')
m = media(ex, 'Map/Banana.tif', col=0)
r = rd(ex)
r.par.Preset = 'labyrinth'; r.par.Feedmod = 0.6; r.par.Killmod = 0.3
r.par.Colormode = 'tint'; r.par.Strength = 2.0
connect(m, r); out(ex, 1, r, col=2)

ex = example(s, 2, 'out2 as a mask',
    'out2 is the raw chemical field (R = A, G = B). Here a GLSL TOP uses B as a mask to reveal a second picture\n'
    '(Butterfly1.tif) only inside the pattern, over the Banana. The field stays in sync with out1, so any\n'
    'Over / Multiply / Matte network can use it the same way. Set Colormode to field to see the raw mask.')
m = media(ex, 'Map/Banana.tif', col=0)
b = media(ex, 'Map/Butterfly1.tif', name='butterfly', col=0, )
r = rd(ex)
r.par.Preset = 'labyrinth'; r.par.Feedmod = 0.6; r.par.Killmod = 0.3
r.par.Colormode = 'field'
connect(m, r)
code = ex.create(td.textDAT, 'mask_code', col=1, row=2)
code.text = ('out vec4 fragColor;\n'
             'void main(){\n'
             '  vec2 uv = vUV.st;\n'
             '  float mask = smoothstep(0.08, 0.3, texture(sTD2DInputs[1], uv).g);\n'
             '  vec3 a = texture(sTD2DInputs[0], uv).rgb;\n'
             '  vec3 b = texture(sTD2DInputs[2], uv).rgb;\n'
             '  fragColor = TDOutputSwizzle(vec4(mix(a, b, mask), 1.0));\n'
             '}\n')
g = ex.create(td.glslTOP, 'reveal', col=3)
g.par.pixeldat = code
g.par.outputresolution = 'custom'; g.par.resolutionw = 960; g.par.resolutionh = 540
connect(m, g, 0, 0); connect(r, g, 1, 1); connect(b, g, 0, 2)
# out2 of the instance feeds input 1 (the field), butterfly is input 2
g.inputConnectors[1].connect(r.outputConnectors[1])
out(ex, 2, g, col=4)

ex = example(s, 3, 'Movie injection and displacement',
    'Continuous injection: with Inject > 0 bright parts of the moving image keep seeding B, so the pattern trails the\n'
    'movie. out2 (A in red, B in green) drives a Displace TOP on a butterfly picture (midpoints 1 and 0), a lens that follows\n'
    'the cells. An LFO named band1 on the last input pushes Feed (+0.01 at full) so the pattern breathes.')
m = media(ex, 'Map/Count.mov', col=0)
r = rd(ex)
r.par.Inject = 0.35; r.par.Colormode = 'tint'; r.par.Strength = 0.8; r.par.Preset = 'mitosis'; r.par.Feedmod = 1.0; r.par.Killmod = 0.5
connect(m, r)
l = ex.create(td.lfoCHOP, 'lfo', col=0, row=1); l.par.frequency = 0.2; l.par.amp = 0.5; l.par.offset = 0.5
rn = ex.create(td.renameCHOP, 'as_band1', col=1, row=1); rn.inputConnectors[0].connect(l); rn.par.renamefrom = 'chan1'; rn.par.renameto = 'band1'
r.inputConnectors[1].connect(rn)
d = ex.create(td.displaceTOP, 'displace', col=3)
d.par.horzsource = 'red'; d.par.vertsource = 'green'; d.par.midpointx = 1.0; d.par.midpointy = 0.0
d.par.displaceweightx = 0.1; d.par.displaceweighty = 0.1; d.par.extend = 'hold'
pic = media(ex, 'Map/Butterfly1.tif', name='butterfly', col=0)
connect(pic, d, 0, 0); d.inputConnectors[1].connect(r.outputConnectors[1])
out(ex, 3, d, col=4)
finish(s)
