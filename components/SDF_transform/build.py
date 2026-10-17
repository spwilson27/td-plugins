# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_transform'
c = new_comp(NAME)
pars(c, {'Controls': [('xyz', 'Translate', 'Translate', [0, 0, 0], {'min': -10, 'max': 10, 'norm': (-3, 3)}),
                      ('xyz', 'Rotate', 'Rotate (deg)', [0, 0, 0], {'min': -360, 'max': 360, 'norm': (-180, 180)}),
                      ('f', 'Scale', 'Scale', 1.0, {'min': 0.01, 'max': 20, 'norm': (0.1, 4)})]})
node(c, 'transform', rd(NAME, 'node.glsl'), """rx, ry, rz = [math.radians(v) for v in (p.Rotatex.eval(), p.Rotatey.eval(), p.Rotatez.eval())]
cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
# R = Rz * Ry * Rx; the shader needs R^-1 = R^T (rows of the inverse = columns of R)
R = [[cz*cy, cz*sy*sx - sz*cx, cz*sy*cx + sz*sx], [sz*cy, sz*sy*sx + cz*cx, sz*sy*cx - cz*sx], [-sy, cy*sx, cy*cx]]
vals = [(p.Translatex, p.Translatey, p.Translatez, p.Scale)] + [(R[0][i], R[1][i], R[2][i], 0) for i in range(3)]""", nin=1, defaults='B')
preview(c)
finish(c, NAME); report(c)
