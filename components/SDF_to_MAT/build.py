# ---- SDF_ shared build helpers (pasted at the top of every SDF_ build.py by gen.sh; self-contained) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, nm, text, kind=None):
    d = c.create(kind or td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    """spec: {page: [(kind, name, label, default, opts)]}; kind f,i,t,m,p,rgb,wh,xy,xyz,s,comp.
    opts: min, max, clamp, menu=[(id,label)], norm=(a,b)"""
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            ap = dict(f=pg.appendFloat, i=pg.appendInt, t=pg.appendToggle, p=pg.appendPulse, s=pg.appendStr, m=pg.appendMenu,
                      rgb=pg.appendRGB, wh=pg.appendWH, xy=pg.appendXY, xyz=pg.appendXYZ, comp=pg.appendCOMP)[kind]
            ps = ap(nm, label=lab)
            if kind == 'm':
                ps[0].menuNames = [m[0] for m in o['menu']]; ps[0].menuLabels = [m[1] for m in o['menu']]
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                if kind == 'comp': continue
                p.default = v; p.val = v
                if 'min' in o:
                    p.min = o['min']; p.normMin = o.get('norm', (o['min'], o.get('max')))[0]; p.clampMin = o.get('clamp', False)
                if 'max' in o:
                    p.max = o['max']; p.normMax = o.get('norm', (o.get('min'), o['max']))[1]; p.clampMax = o.get('clamp', False)
    return c

def color_par(default=(0.8, 0.8, 0.8), page='Look'):
    return {page: [('rgb', 'Color', 'Color', list(default), {'min': 0, 'max': 1})]}

def vecs(g, items):
    """items: list of (name, [4 values or expression strings]) -> vec uniforms of a GLSL TOP/MAT"""
    g.seq.vec.numBlocks = len(items)
    for i, (nm, vs) in enumerate(items):
        g.par['vec%dname' % i] = nm
        for ax, v in zip('xyzw', vs):
            p = g.par['vec%d value%s' % (i, ax)] if False else g.par['vec%dvalue%s' % (i, ax)]
            if isinstance(v, str): p.expr = v
            else: p.val = v

def set_array(g, chop, tb=False):
    g.seq.array.numBlocks = 1
    g.par.array0name = 'uSdf'; g.par.array0type = 'vec4'; g.par.array0chop = chop
    if tb: g.par.array0arraytype = 'texturebuffer'

def lib_dat(c):
    return mkdat(c, 'sdflib', rd(c.name, 'sdflib.py'))

def scene_feed(c, pfx, src, template, tb=False):
    """Consumer plumbing for an SDF wire: Script DAT <pfx>shader (template with the assembled scene; only
    rewritten when the structure changes) and the uniform-array CHOP <pfx>vals (values, per frame).
    `src` is any DAT carrying the payload (In DAT or the node's own `sdf`)."""
    t = mkdat(c, pfx + 'template', template)
    cb = mkdat(c, pfx + 'shader_cb', "def onCook(dat):\n    op('sdflib').module.write_shader(dat, op('%s').text, op('%stemplate').text, %r)\n" % (src.name, pfx, tb))
    sh = c.create(td.scriptDAT, pfx + 'shader'); sh.par.callbacks = cb
    sh.inputConnectors[0].connect(src)
    vcb = mkdat(c, pfx + 'vals_cb', "def onCook(dat):\n    op('sdflib').module.write_vals(dat, op('%s').text)\n" % src.name)
    vt = c.create(td.scriptDAT, pfx + 'vals_tbl'); vt.par.callbacks = vcb
    vt.inputConnectors[0].connect(src)
    vc = c.create(td.dattoCHOP, pfx + 'vals'); vc.par.dat = vt
    vc.par.firstrow = 'values'; vc.par.firstcolumn = 'values'; vc.par.output = 'chanpercol'
    return sh, vc

def node(c, kind, code, vals_py, nin=0, defaults='AB'):
    """The SDF node itself: In DATs, Script DAT `sdf` (writes the payload), Out DAT out1."""
    lib_dat(c)
    ins = []
    for i in range(nin):
        d = c.create(td.inDAT, 'in%d' % (i + 1)); ins.append(d)
    mkdat(c, 'code', code)
    body = ("def onCook(dat):\n    import math\n    p = parent().par\n"
            + ''.join('    ' + ln + '\n' for ln in vals_py.strip('\n').split('\n'))
            + "    op('sdflib').module.write_node(dat, parent(), %r, [%s], op('code').text, vals, %r)\n"
            % (kind, ', '.join("op('in%d')" % (i + 1) for i in range(nin)), defaults))
    cb = mkdat(c, 'sdf_cb', body)
    sd = c.create(td.scriptDAT, 'sdf'); sd.par.callbacks = cb
    for i, d in enumerate(ins): sd.inputConnectors[i].connect(d)
    o = c.create(td.outDAT, 'out1'); o.inputConnectors[0].connect(sd)
    return sd

def preview(c, src='sdf', w=400, h=300):
    """Internal `preview` TOP: small orbiting raymarch of the node's own SDF (shown in the node viewer)."""
    tmpl = rd(c.name, 'preview.glsl').replace('//@@LIB@@', rd(c.name, 'lib.glsl'))
    sh, vc = scene_feed(c, 'pv_', c.op(src), tmpl)
    g = c.create(td.glslTOP, 'preview'); g.par.pixeldat = sh
    g.par.outputresolution = 'custom'; g.par.resolutionw = w; g.par.resolutionh = h
    g.par.format = 'rgba8fixed'
    set_array(g, vc)
    vecs(g, [('uPv', ['absTime.seconds', 0, 0, 0])])
    return g

def finish(c, name):
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True); c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
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
sh, vc = scene_feed(c, 'm_', i1, rd(NAME, 'node.glsl').replace('//@@LIB@@', rd(NAME, 'lib.glsl')))
mat = c.create(td.glslMAT, 'mat')
mat.par.glslversion = 'glsl430'
mat.par.vdat = mkdat(c, 'mat_vert', rd(NAME, 'vert.glsl'))
mat.par.pdat = sh
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
