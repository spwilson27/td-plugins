# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_combine'
c = new_comp(NAME)
pars(c, {'Controls': [('m', 'Operation', 'Operation', 'union', {'menu': [('union', 'Union'), ('subtract', 'Subtract B from A'), ('intersect', 'Intersect'), ('morph', 'Morph A to B')]}),
                      ('f', 'Smooth', 'Smooth K', 0.25, {'min': 0, 'max': 3, 'norm': (0, 1)}),
                      ('f', 'Morph', 'Morph', 0.5, {'min': 0, 'max': 1, 'clamp': True})]})
node(c, 'combine', rd(NAME, 'node.glsl'), "vals = [(p.Smooth, p.Operation.menuIndex, p.Morph, 0)]", nin=2)
preview(c)
finish(c, NAME); report(c)
