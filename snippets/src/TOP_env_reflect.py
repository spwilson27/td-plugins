exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
exec(open(os.path.join(LIB, 'components/_gbuf/gbuf.py')).read())
s = begin('TOP_env_reflect')
R = ('1280', '720')

ex = example(s, 1, 'Chrome shapes from a Render TOP G-buffer',
             'A Render TOP draws Sphere / Torus / Box POPs with a GLSL MAT writing colour, depth and view-space normals\nto three colour buffers. TOP_env_reflect uses colour + normals and its built-in studio environment.\nin4 is a mask (objects only, so the floor stays matte; Maskmode = reflectivity).\nTry: Reflectivity, Fresnel, Roughness (blurred reflection), Envrotate.')
gb = make_gbuffer(s, res=R, prefix='ex1_')
sky = add_sky(s, gb['color'], R, prefix='ex1_')
f = instance(ex, 'TOP_env_reflect')
mk = add_mask(s, gb['normal'], R, prefix='ex1_')
f.inputConnectors[0].connect(sky); f.inputConnectors[1].connect(gb['normal']); f.inputConnectors[3].connect(mk)
out(ex, 1, f)

ex = example(s, 2, 'Glass with a custom environment map',
             'Mode = glass refracts the colour behind the shape and adds Fresnel reflections.\nin3 takes any equirectangular image: here Banana.tif is used as the environment.\nTry: Ior, Refraction, Tint (absorption colour), Envtilt.')
gb = make_gbuffer(s, res=R, prefix='ex2_')
sky = add_sky(s, gb['color'], R, prefix='ex2_')
env = ex.create(td.moviefileinTOP, 'env', row=1); env.par.file.expr = sample_expr('Map/Banana.tif')
f = instance(ex, 'TOP_env_reflect')
f.inputConnectors[0].connect(sky); mk = add_mask(s, gb['normal'], R, prefix='ex2_')
f.inputConnectors[1].connect(gb['normal']); f.inputConnectors[2].connect(env); f.inputConnectors[3].connect(mk)
f.par.Mode = 'glass'; f.par.Fresnel = 0.8; f.par.Reflectivity = 0.5; f.par.Ior = 1.45; f.par.Refraction = 0.8
f.par.Roughness = 0.05; f.par.Tintr, f.par.Tintg, f.par.Tintb = 0.8, 0.95, 1.0
out(ex, 2, f)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
