# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_fractal'
c = new_comp(NAME)
pars(c, {'Controls': [('m', 'Fractal', 'Fractal', 'mandelbulb', {'menu': [('mandelbulb', 'Mandelbulb'), ('menger', 'Menger Sponge'), ('kifs', 'Kaleidoscopic IFS')]}),
                      ('i', 'Iterations', 'Iterations', 6, {'min': 1, 'max': 16, 'clamp': True}),
                      ('f', 'Power', 'Power / Scale', 8.0, {'min': 1.5, 'max': 16, 'norm': (2, 12)}),
                      ('f', 'Size', 'Size', 1.0, {'min': 0.05, 'max': 8, 'norm': (0.1, 4)})],
          'Fold': [('xyz', 'Foldoffset', 'Fold Offset (KIFS)', [1.0, 1.0, 1.0], {'min': -3, 'max': 3}),
                   ('f', 'Foldrotate', 'Fold Rotate (KIFS, deg)', 0.0, {'min': -180, 'max': 180})]})
pars(c, {'Look': [('rgb', 'Color', 'Color', [0.85, 0.8, 0.7], {'min': 0, 'max': 1}),
                  ('rgb', 'Color2', 'Orbit Trap Color', [0.85, 0.25, 0.15], {'min': 0, 'max': 1})]})
node(c, 'fractal', rd(NAME, 'node.glsl'), """ty = p.Fractal.menuIndex
sc = p.Power.eval()
if ty == 1: sc = 3.0
elif ty == 2: sc = max(1.2, min(sc, 4.0)) if sc < 5 else 2.0
vals = [(ty, p.Iterations.eval(), sc, p.Size.eval()), (p.Colorr, p.Colorg, p.Colorb, 0), (p.Color2r, p.Color2g, p.Color2b, 0),
        (p.Foldoffsetx, p.Foldoffsety, p.Foldoffsetz, math.radians(p.Foldrotate.eval()))]""")
preview(c)
finish(c, NAME); report(c)
