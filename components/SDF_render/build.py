# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_render'
c = new_comp(NAME)
pars(c, {'Controls': [('wh', 'Resolution', 'Resolution', [1280, 720], {'min': 16, 'max': 8192, 'norm': (16, 4096)}),
                      ('comp', 'Camera', 'Camera (COMP, empty = built-in)', ''),
                      ('f', 'Orbitspeed', 'Default Camera Orbit (deg/s)', 15.0, {'min': -90, 'max': 90, 'norm': (-45, 45)}),
                      ('f', 'Maxdist', 'Max Distance', 30.0, {'min': 1, 'max': 500, 'norm': (5, 100)}),
                      ('i', 'Maxsteps', 'Max Steps', 128, {'min': 8, 'max': 512, 'clamp': True}),
                      ('f', 'Epsilon', 'Epsilon', 0.001, {'min': 0.00005, 'max': 0.05, 'norm': (0.0002, 0.01)}),
                      ('f', 'Stepscale', 'Step Scale (<1 safer)', 0.9, {'min': 0.2, 'max': 1.0, 'clamp': True})],
          'Light': [('f', 'Lightazimuth', 'Key Azimuth (deg)', 40.0, {'min': -180, 'max': 180}),
                    ('f', 'Lightelevation', 'Key Elevation (deg)', 50.0, {'min': -10, 'max': 90}),
                    ('f', 'Shadows', 'Shadow Hardness (0 = off)', 10.0, {'min': 0, 'max': 64, 'norm': (0, 32)}),
                    ('f', 'Ao', 'Ambient Occlusion', 0.8, {'min': 0, 'max': 1, 'clamp': True}),
                    ('f', 'Reflectivity', 'Reflectivity', 0.0, {'min': 0, 'max': 1, 'clamp': True})]})
pars(c, {'Look': [('m', 'Background', 'Background', 'env', {'menu': [('env', 'Environment'), ('solid', 'Solid color')]}),
                  ('rgb', 'Bgcolor', 'Background Color', [0.02, 0.02, 0.025], {'min': 0, 'max': 1}),
                  ('f', 'Fog', 'Fog Density (0 = off)', 0.0, {'min': 0, 'max': 1, 'norm': (0, 0.3)}),
                  ('rgb', 'Fogcolor', 'Fog Color', [0.3, 0.33, 0.4], {'min': 0, 'max': 1}),
                  ('f', 'Gamma', 'Output Gamma (1 = linear)', 2.2, {'min': 1, 'max': 3}),
                  ('t', 'Alphabg', 'Transparent Background', False)]})
lib_dat(c)
i1 = c.create(td.inDAT, 'in1')
i2 = c.create(td.inTOP, 'in2')
envdef = c.create(td.glslTOP, 'envdef'); envdef.par.pixeldat = mkdat(c, 'envdef_code', rd(NAME, 'env.glsl'))
envdef.par.outputresolution = 'custom'; envdef.par.resolutionw = 512; envdef.par.resolutionh = 256; envdef.par.format = 'rgba16float'
env = c.create(td.switchTOP, 'env')
env.inputConnectors[0].connect(envdef); env.inputConnectors[0 + 1].connect(i2)
env.par.index.expr = "(1 if len(parent().inputConnectors[1].connections) else 0) + 0*absTime.frame"
sh, vc = scene_feed(c, '', i1, rd(NAME, 'node.glsl').replace('//@@LIB@@', rd(NAME, 'lib.glsl')), base=(1, 0))
cam = c.create(td.constantCHOP, 'cam')
names = ['px', 'py', 'pz', 'tanf', 'rx', 'ry', 'rz', 'fmode', 'ux', 'uy', 'uz', 'u0', 'fx', 'fy', 'fz', 'f0']
cam.par.name0 = names[0]
for i, nm in enumerate(names):
    cam.par['name%d' % i] = nm
    cam.par['value%d' % i].expr = "op('sdflib').module.camv(parent().par.Camera.eval(), absTime.seconds, parent().par.Orbitspeed.eval())[%d]" % i
P = 'parent().par.'
g = c.create(td.glslTOP, 'render'); g.par.pixeldat = sh
bind_tex(g, c, '')
g.inputConnectors[0].connect(env)
g.par.outputresolution = 'custom'; g.par.resolutionw.expr = P + 'Resolutionw'; g.par.resolutionh.expr = P + 'Resolutionh'
g.par.format = 'rgba16float'; g.par.numcolorbufs = 4
set_array(g, vc)
C = lambda n: "op('cam')['%s']" % n
lz = "math.radians(%sLightelevation.eval())" % P
laz = "math.radians(%sLightazimuth.eval())" % P
vecs(g, [('uCamPos', [C('px'), C('py'), C('pz'), C('tanf')]),
         ('uCamR', [C('rx'), C('ry'), C('rz'), C('fmode')]),
         ('uCamU', [C('ux'), C('uy'), C('uz'), 0]),
         ('uCamF', [C('fx'), C('fy'), C('fz'), 0]),
         ('uA', [P + 'Maxdist', P + 'Maxsteps', P + 'Epsilon', P + 'Stepscale']),
         ('uB', [P + 'Shadows', P + 'Ao', P + 'Fog', P + 'Reflectivity']),
         ('uC', ["math.cos(%s)*math.sin(%s)" % (lz, laz), "math.sin(%s)" % lz, "math.cos(%s)*math.cos(%s)" % (lz, laz), P + 'Gamma']),
         ('uD', [P + 'Fogcolorr', P + 'Fogcolorg', P + 'Fogcolorb', "0 if %sAlphabg else 1" % P]),
         ('uE', [P + 'Bgcolorr', P + 'Bgcolorg', P + 'Bgcolorb', "0 if %sBackground=='env' else 1" % P])])
o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(g)
for k in (1, 2, 3):
    r = c.create(td.renderselectTOP, 'out%d' % (k + 1)); r.par.top = g; r.par.bufferindex = k
finish(c, NAME); report(c)
