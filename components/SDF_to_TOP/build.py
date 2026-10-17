# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_to_TOP'
c = new_comp(NAME)
pars(c, {'Controls': [('i', 'Resolution', 'Resolution (voxels per side)', 64, {'min': 8, 'max': 512, 'clamp': True}),
                      ('xyz', 'Boundscenter', 'Bounds Center', [0, 0, 0], {'min': -100, 'max': 100, 'norm': (-5, 5)}),
                      ('xyz', 'Boundssize', 'Bounds Size', [3, 3, 3], {'min': 0.01, 'max': 200, 'norm': (0.1, 10)}),
                      ('m', 'Precision', 'Precision', 'f16', {'menu': [('f16', '16-bit float'), ('f32', '32-bit float')]})]})
lib_dat(c)
i1 = c.create(td.inDAT, 'in1')
sh, vc = scene_feed(c, 'bk_', i1, rd(NAME, 'node.glsl'), tb=True)
P = 'parent().par.'
g = c.create(td.glslTOP, 'bake'); g.par.mode = 'compute'; g.par.computedat = sh
bind_tex(g, c, 'bk_')
g.par.type = 'texture3d'; g.par.outputresolution = 'custom'
g.par.resolutionw.expr = P + 'Resolution'; g.par.resolutionh.expr = P + 'Resolution'
g.par.depth = 'custom'; g.par.customdepth.expr = P + 'Resolution'
g.par.format.expr = "'rgba16float' if %sPrecision=='f16' else 'rgba32float'" % P
set_array(g, vc, tb=True)
vecs(g, [('uBc', [P + 'Boundscenterx', P + 'Boundscentery', P + 'Boundscenterz', P + 'Resolution']),
         ('uBs', [P + 'Boundssizex', P + 'Boundssizey', P + 'Boundssizez', 0])])
o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(g)
pv = c.create(td.glslTOP, 'preview')
pv.par.pixeldat = mkdat(c, 'pv_code', rd(NAME, 'bakeprev.glsl').replace('//@@LIB@@', rd(NAME, 'lib.glsl')))
pv.inputConnectors[0].connect(o)
pv.par.outputresolution = 'custom'; pv.par.resolutionw = 400; pv.par.resolutionh = 300; pv.par.format = 'rgba8fixed'
vecs(pv, [('uBc', [P + 'Boundscenterx', P + 'Boundscentery', P + 'Boundscenterz', 0]),
          ('uBs', [P + 'Boundssizex', P + 'Boundssizey', P + 'Boundssizez', 0]),
          ('uPv', ['absTime.seconds', 0, 0, 0])])
finish(c, NAME); report(c)
