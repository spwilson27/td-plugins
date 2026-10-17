exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
exec(open(os.path.join(LIB, 'components/_gbuf/gbuf.py')).read())
s = begin('TOP_ssao')
R = ('1280', '720')

ex = example(s, 1, 'Ambient occlusion on a Render TOP G-buffer',
             'A Render TOP draws Sphere / Torus / Box POPs with a GLSL MAT writing colour, linear depth and view-space\nnormals to three colour buffers. TOP_ssao darkens contact areas: under the shapes, in the torus hole.\nTry: Radius (size of the shadowing), Intensity, Samples, Blur (smoothness).')
gb = make_gbuffer(s, res=R, prefix='ex1_')
sky = add_sky(s, gb['color'], R, prefix='ex1_')
f = instance(ex, 'TOP_ssao')
f.inputConnectors[0].connect(sky); f.inputConnectors[1].connect(gb['depth']); f.inputConnectors[2].connect(gb['normal'])
out(ex, 1, f)

ex = example(s, 2, 'The AO mask on its own',
             'out2 of TOP_ssao is the final AO multiplier (white = open, dark = occluded).\nUse it to drive other effects, e.g. multiply it into reflections or fog.\nHere a large Radius and strong Intensity make the mask easy to read.')
gb = make_gbuffer(s, res=R, prefix='ex2_')
f = instance(ex, 'TOP_ssao')
f.inputConnectors[0].connect(gb['color']); f.inputConnectors[1].connect(gb['depth']); f.inputConnectors[2].connect(gb['normal'])
f.par.Radius = 1.8; f.par.Intensity = 1.5; f.par.Samples = 32; f.par.Blur = 6
n = ex.create(td.nullTOP, 'mask'); n.name = 'example2'
n.inputConnectors[0].connect(f.outputConnectors[1]); n.viewer = True
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
