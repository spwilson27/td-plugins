# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_box'
c = new_comp(NAME)
pars(c, {'Controls': [('xyz', 'Size', 'Size', [1.2, 1.2, 1.2], {'min': 0.01, 'max': 6, 'norm': (0.01, 3)}),
                      ('f', 'Roundness', 'Roundness', 0.1, {'min': 0, 'max': 2, 'norm': (0, 0.5)})]})
pars(c, color_par((0.9, 0.35, 0.25)))
node(c, 'box', rd(NAME, 'node.glsl'), """hx, hy, hz = p.Sizex.eval() / 2, p.Sizey.eval() / 2, p.Sizez.eval() / 2
vals = [(hx, hy, hz, max(0.0, min(p.Roundness.eval(), hx, hy, hz))), (p.Colorr, p.Colorg, p.Colorb, 0)]""")
preview(c)
finish(c, NAME); report(c)
