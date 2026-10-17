# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_gyroid'
c = new_comp(NAME)
pars(c, {'Controls': [('m', 'Surface', 'Surface', 'gyroid', {'menu': [('gyroid', 'Gyroid'), ('schwarzp', 'Schwarz P'), ('diamond', 'Diamond')]}),
                      ('f', 'Frequency', 'Frequency', 4.0, {'min': 0.2, 'max': 30, 'norm': (0.5, 12)}),
                      ('f', 'Thickness', 'Thickness', 0.35, {'min': 0.01, 'max': 2, 'norm': (0.05, 1)}),
                      ('f', 'Boundradius', 'Bound Radius (0 = infinite)', 1.1, {'min': 0, 'max': 20, 'norm': (0, 4)})]})
pars(c, {'Look': [('rgb', 'Color', 'Color', [0.9, 0.55, 0.2], {'min': 0, 'max': 1}),
                  ('rgb', 'Color2', 'Color 2', [0.2, 0.35, 0.8], {'min': 0, 'max': 1})]})
node(c, 'gyroid', rd(NAME, 'node.glsl'), """vals = [(p.Frequency, p.Thickness, p.Surface.menuIndex, p.Boundradius), (p.Colorr, p.Colorg, p.Colorb, 0), (p.Color2r, p.Color2g, p.Color2b, 0)]""")
preview(c)
finish(c, NAME); report(c)
