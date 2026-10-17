# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_deform'
c = new_comp(NAME)
pars(c, {'Controls': [('m', 'Mode', 'Mode', 'twist', {'menu': [('twist', 'Twist'), ('bend', 'Bend'), ('noise', 'Noise Displace'), ('round', 'Round (inflate)'), ('onion', 'Onion (shell)')]}),
                      ('f', 'Amount', 'Amount', 1.5, {'min': -10, 'max': 10, 'norm': (-3, 3)}),
                      ('m', 'Axis', 'Axis (twist / bend)', 'y', {'menu': [('x', 'X'), ('y', 'Y'), ('z', 'Z')]}),
                      ('f', 'Frequency', 'Noise Frequency', 3.0, {'min': 0.1, 'max': 30, 'norm': (0.5, 10)}),
                      ('xyz', 'Noiseoffset', 'Noise Offset', [0, 0, 0], {'min': -1000, 'max': 1000, 'norm': (-10, 10)})]})
node(c, 'deform', rd(NAME, 'node.glsl'), """vals = [(p.Mode.menuIndex, p.Amount, p.Frequency, p.Axis.menuIndex), (p.Noiseoffsetx, p.Noiseoffsety, p.Noiseoffsetz, 0)]""", nin=1, defaults='B')
preview(c)
finish(c, NAME); report(c)
