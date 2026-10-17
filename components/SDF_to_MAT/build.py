# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_to_MAT'
APPLY_CB = '''# Apply To: assign this component's material to the Geometry COMPs / Render TOPs dropped on the Applyto field.
def apply(comp):
    mat = comp.op('mat')
    prev = comp.fetch('applied_to', [])
    cur = []
    for t in comp.par.Applyto.evalOPs():
        if t is None or t == comp:
            continue
        if t.OPType == 'renderTOP':
            t.par.overridemat = mat
        elif t.isCOMP and hasattr(t.par, 'material'):
            t.par.material = mat
        else:
            debug('Apply To: %s is not a Geometry COMP or Render TOP' % t.path); continue
        cur.append(t.path)
    for p in prev:
        t = op(p)
        if p in cur or t is None:
            continue
        for pn in ('material', 'overridemat'):
            if hasattr(t.par, pn) and t.par[pn].eval() == mat:
                t.par[pn] = ''
    comp.store('applied_to', cur)

def onValueChange(par, prev):
    apply(par.owner)
    return
'''
c = new_comp(NAME)
pg = c.appendCustomPage('Controls')
ap = pg.appendOP('Applyto', label='Apply To')[0]
ap.help = 'Drag Geometry COMPs and/or Render TOPs here. Geometry: sets its Material; Render TOP: sets its Override Material. The Geometry should be a box covering the Bounds below.'
pars(c, {'Bounds': [('xyz', 'Boundscenter', 'Bounds Center', [0, 0, 0], {'min': -100, 'max': 100, 'norm': (-5, 5)}),
                    ('xyz', 'Boundssize', 'Bounds Size (proxy box)', [3, 3, 3], {'min': 0.01, 'max': 200, 'norm': (0.1, 10)})],
         'Quality': [('i', 'Maxsteps', 'Max Steps', 96, {'min': 8, 'max': 512, 'clamp': True}),
                     ('f', 'Epsilon', 'Epsilon', 0.0015, {'min': 0.00005, 'max': 0.05, 'norm': (0.0002, 0.01)}),
                     ('f', 'Stepscale', 'Step Scale (<1 safer)', 0.9, {'min': 0.2, 'max': 1.0, 'clamp': True})],
         'Light': [('f', 'Lightazimuth', 'Key Azimuth (deg)', 40.0, {'min': -180, 'max': 180}),
                   ('f', 'Lightelevation', 'Key Elevation (deg)', 50.0, {'min': -10, 'max': 90}),
                   ('f', 'Shadows', 'Shadow Hardness (0 = off)', 8.0, {'min': 0, 'max': 64, 'norm': (0, 32)}),
                   ('f', 'Ao', 'Ambient Occlusion', 0.8, {'min': 0, 'max': 1, 'clamp': True}),
                   ('f', 'Gamma', 'Output Gamma (1 = linear)', 2.2, {'min': 1, 'max': 3})]})
lib_dat(c)
i1 = c.create(td.inDAT, 'in1')
sh, vc = scene_feed(c, 'm_', i1, rd(NAME, 'node.glsl').replace('//@@LIB@@', rd(NAME, 'lib.glsl')), kind='mat')
mat = c.create(td.glslMAT, 'mat')
mat.par.glslversion = 'glsl430'
mat.par.vdat = mkdat(c, 'mat_vert', rd(NAME, 'vert.glsl'))
mat.par.pdat = sh
bind_tex(mat, c, 'm_', 'mat')
if hasattr(mat.par, 'cullface'): mat.par.cullface = 'off' if 'off' in mat.par.cullface.menuNames else mat.par.cullface.eval()
set_array(mat, vc)
P = 'parent().par.'
vecs(mat, [('uBc', [P + 'Boundscenterx', P + 'Boundscentery', P + 'Boundscenterz', 0]),
           ('uBs', [P + 'Boundssizex', P + 'Boundssizey', P + 'Boundssizez', 0]),
           ('uA', [P + 'Maxsteps', P + 'Epsilon', P + 'Stepscale', P + 'Gamma']),
           ('uB', [P + 'Shadows', P + 'Ao', "math.radians(%sLightazimuth.eval())" % P, "math.radians(%sLightelevation.eval())" % P])])
om = c.create(td.outMAT, 'out1'); om.inputConnectors[0].connect(mat)
ac = c.create(td.parameterexecuteDAT, 'applyto_callbacks'); ac.text = APPLY_CB
ac.par.op = '..'; ac.par.pars = 'Applyto'; ac.par.valuechange = True; ac.par.onpulse = False; ac.par.custom = True; ac.par.builtin = False
aw = c.create(td.opexecuteDAT, 'applyto_watch')
aw.text = "def onNameChange(changeOp):\n    op('applyto_callbacks').module.apply(changeOp)\n    return\n\ndef onPathChange(changeOp):\n    op('applyto_callbacks').module.apply(changeOp)\n    return\n"
aw.par.op = '..'
for pn in ('precook', 'postcook', 'flagchange', 'wirechange', 'uichange', 'numchildrenchange', 'childrename', 'currentchildchange', 'extensionchange'):
    if hasattr(aw.par, pn): setattr(aw.par, pn, False)
aw.par.namechange = True; aw.par.pathchange = True
# preview: proxy box + camera + render
geo = c.create(td.geometryCOMP, 'geo')
for ch in list(geo.children): ch.destroy()
b = geo.create(td.boxSOP, 'box'); b.display = True; b.render = True
for ax in 'xyz': b.par['size' + ax].expr = 'parent(2).par.Boundssize' + ax
geo.par.material = mat
geo.par.ry.expr = 'absTime.seconds * 20'
cam = c.create(td.cameraCOMP, 'cam'); cam.par.tz = 5.5; cam.par.ty = 2.2; cam.par.rx = -21
r = c.create(td.renderTOP, 'preview')
r.par.camera = cam; r.par.geometry = geo; r.par.lights = ''
r.par.outputresolution = 'custom'; r.par.resolutionw = 400; r.par.resolutionh = 300
r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.05; r.par.bgcolora = 1
finish(c, NAME); report(c)
