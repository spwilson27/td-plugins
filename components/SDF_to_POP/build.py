# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_to_POP'
c = new_comp(NAME)
pars(c, {'Controls': [('i', 'Resolution', 'Resolution (voxels per side)', 64, {'min': 8, 'max': 256, 'clamp': True}),
                      ('xyz', 'Boundscenter', 'Bounds Center', [0, 0, 0], {'min': -100, 'max': 100, 'norm': (-5, 5)}),
                      ('xyz', 'Boundssize', 'Bounds Size', [3, 3, 3], {'min': 0.01, 'max': 200, 'norm': (0.1, 10)}),
                      ('f', 'Inflate', 'Inflate (iso offset)', 0.0, {'min': -2, 'max': 2, 'norm': (-0.5, 0.5)}),
                      ('m', 'Normals', 'Normals', 'gradient', {'menu': [('none', 'None'), ('gradient', 'Smooth (gradient)'), ('surface', 'Flat (surface)')]})]})
lib_dat(c)
i1 = c.create(td.inDAT, 'in1')
sh, vc = scene_feed(c, 'bk_', i1, rd(NAME, 'node.glsl'), tb=True)
P = 'parent().par.'
g = c.create(td.glslTOP, 'bake'); g.par.mode = 'compute'; g.par.computedat = sh
bind_tex(g, c, 'bk_')
g.par.type = 'texture3d'; g.par.outputresolution = 'custom'
g.par.resolutionw.expr = P + 'Resolution'; g.par.resolutionh.expr = P + 'Resolution'
g.par.depth = 'custom'; g.par.customdepth.expr = P + 'Resolution'
g.par.format = 'rgba32float'
set_array(g, vc, tb=True)
vecs(g, [('uBc', [P + 'Boundscenterx', P + 'Boundscentery', P + 'Boundscenterz', P + 'Resolution']),
         ('uBs', [P + 'Boundssizex', P + 'Boundssizey', P + 'Boundssizez', 0])])
pp = c.create(td.polygonizePOP, 'poly')
pp.par.top = g; pp.par.channel = 'red'; pp.par.inside = 'lteq'; pp.par.extend = 'hold'
pp.par.threshold.expr = P + 'Inflate'
pp.par.nmlmethod.expr = P + 'Normals'
pp.par.rerangep = True
for k, ax in enumerate('xyz'):
    pp.par['tolow%d' % k].expr = "%sBoundscenter%s - %sBoundssize%s/2" % (P, ax, P, ax)
    pp.par['tohigh%d' % k].expr = "%sBoundscenter%s + %sBoundssize%s/2" % (P, ax, P, ax)
o = c.create(td.nullPOP, 'out1'); o.inputConnectors[0].connect(pp)
# preview: render the mesh
geo = c.create(td.geometryCOMP, 'geo')
for ch in list(geo.children): ch.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = '../poly'; sel.display = True; sel.render = True
geo.par.ry.expr = 'absTime.seconds * 25'
cam = c.create(td.cameraCOMP, 'cam')
cam.par.tz.expr = "max(%sBoundssizex, %sBoundssizey, %sBoundssizez) * 1.6" % (P, P, P)
cam.par.ty.expr = "max(%sBoundssizex, %sBoundssizey, %sBoundssizez) * 0.6" % (P, P, P)
cam.par.rx.expr = "-math.degrees(math.atan2(me.par.ty, me.par.tz))"
lt = c.create(td.lightCOMP, 'light'); lt.par.tx = 4; lt.par.ty = 8; lt.par.tz = 6
r = c.create(td.renderTOP, 'preview')
r.par.camera = cam; r.par.geometry = geo; r.par.lights = lt
r.par.outputresolution = 'custom'; r.par.resolutionw = 400; r.par.resolutionh = 300
r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.04; r.par.bgcolora = 1
finish(c, NAME); report(c)
