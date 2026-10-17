# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_repeat'
c = new_comp(NAME)
pars(c, {'Controls': [('m', 'Mode', 'Mode', 'finite', {'menu': [('grid', 'Grid (infinite)'), ('finite', 'Grid (finite)'), ('polar', 'Polar')]}),
                      ('xyz', 'Spacing', 'Spacing (0 = no repeat)', [1.6, 1.6, 1.6], {'min': 0, 'max': 20, 'norm': (0, 5)}),
                      ('xyz', 'Count', 'Cells each side (finite)', [1, 1, 1], {'min': 0, 'max': 50, 'norm': (0, 10)}),
                      ('i', 'Polarcount', 'Polar Count', 6, {'min': 1, 'max': 64, 'clamp': True}),
                      ('m', 'Polaraxis', 'Polar Axis', 'y', {'menu': [('x', 'X'), ('y', 'Y'), ('z', 'Z')]}),
                      ('f', 'Colorvary', 'Color Variation', 0.0, {'min': 0, 'max': 1, 'clamp': True})]})
node(c, 'repeat', rd(NAME, 'node.glsl'), """vals = [(p.Spacingx, p.Spacingy, p.Spacingz, p.Mode.menuIndex), (round(p.Countx.eval()), round(p.County.eval()), round(p.Countz.eval()), p.Colorvary),
        (p.Polarcount, p.Polaraxis.menuIndex, 0, 0)]""", nin=1, defaults='A')
preview(c)
finish(c, NAME); report(c)
