# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_torus'
c = new_comp(NAME)
pars(c, {'Controls': [('f', 'Majorradius', 'Major Radius', 0.6, {'min': 0.01, 'max': 4, 'norm': (0.01, 2)}),
                      ('f', 'Minorradius', 'Minor Radius', 0.22, {'min': 0.005, 'max': 2, 'norm': (0.005, 1)}),
                      ('m', 'Axis', 'Axis', 'y', {'menu': [('x', 'X'), ('y', 'Y'), ('z', 'Z')]})]})
pars(c, color_par((0.3, 0.6, 0.9)))
node(c, 'torus', rd(NAME, 'node.glsl'), "vals = [(p.Majorradius, p.Minorradius, p.Axis.menuIndex, 0), (p.Colorr, p.Colorg, p.Colorb, 0)]")
preview(c)
finish(c, NAME); report(c)
