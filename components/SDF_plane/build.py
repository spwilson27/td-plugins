# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_plane'
c = new_comp(NAME)
pars(c, {'Controls': [('xyz', 'Normal', 'Normal', [0, 1, 0], {'min': -1, 'max': 1}),
                      ('f', 'Offset', 'Offset', -0.8, {'min': -10, 'max': 10, 'norm': (-3, 3)})]})
pars(c, {'Look': [('rgb', 'Color', 'Color', [0.55, 0.55, 0.58], {'min': 0, 'max': 1}),
                  ('t', 'Checker', 'Checker', True),
                  ('f', 'Checksize', 'Checker Size', 0.5, {'min': 0.02, 'max': 5, 'norm': (0.05, 2)}),
                  ('rgb', 'Color2', 'Checker Color', [0.12, 0.12, 0.14], {'min': 0, 'max': 1})]})
node(c, 'plane', rd(NAME, 'node.glsl'), """import math
n = [p.Normalx.eval(), p.Normaly.eval(), p.Normalz.eval()]
l = math.sqrt(sum(x * x for x in n)) or 1.0
n = [x / l for x in n]
vals = [(n[0], n[1], n[2], p.Offset.eval() ), (p.Colorr, p.Colorg, p.Colorb, 0),
        (p.Checksize.eval() if p.Checker.eval() else 0.0, 0, 0, 0), (p.Color2r, p.Color2g, p.Color2b, 0)]""")
preview(c)
finish(c, NAME); report(c)
