# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_sphere'
c = new_comp(NAME)
pars(c, {'Controls': [('f', 'Radius', 'Radius', 0.7, {'min': 0.01, 'max': 3, 'norm': (0.01, 2)})]})
pars(c, color_par((0.85, 0.85, 0.85)))
node(c, 'sphere', rd(NAME, 'node.glsl'), "vals = [(p.Radius, 0, 0, 0), (p.Colorr, p.Colorg, p.Colorb, 0)]")
preview(c)
finish(c, NAME); report(c)
