# ---- SDF_ shared build helpers: components/_sdf/helpers.py (read at build time; the built tox is self-contained) ----
import os
exec(open(os.path.expanduser('~/software/td-plugins/components/_sdf/helpers.py')).read())
# ---- end shared helpers ----
NAME = 'SDF_from_POP'
c = new_comp(NAME)
P = 'parent().par.'

pars(c, {'Controls': [('m', 'Mode', 'Mode', 'points', {'menu': [('points', 'Points (live metaballs)'), ('mesh', 'Mesh (baked distance volume)')]})]})
pars(c, {'Points': [('f', 'Radius', 'Radius', 0.1, {'min': 0.001, 'max': 20, 'norm': (0.01, 1)}),
                    ('f', 'Blend', 'Blend (smooth K)', 0.12, {'min': 0, 'max': 5, 'norm': (0, 0.5)}),
                    ('t', 'Usepscale', 'Use PointScale Attribute', True),
                    ('t', 'Usecolor', 'Use Color Attribute', True),
                    ('i', 'Maxpoints', 'Max Points', 50000, {'min': 1, 'max': 4000000, 'norm': (100, 200000), 'clamp': True}),
                    ('i', 'Gridres', 'Grid Resolution', 32, {'min': 4, 'max': 96, 'norm': (8, 64), 'clamp': True}),
                    ('i', 'Cellcap', 'Cell Capacity', 48, {'min': 4, 'max': 128, 'norm': (8, 64), 'clamp': True})],
         'Mesh': [('i', 'Resolution', 'Resolution (voxels per side)', 96, {'min': 32, 'max': 256, 'clamp': True}),
                  ('m', 'Boundsmode', 'Bounds', 'auto', {'menu': [('auto', 'Auto (bounding box + padding)'), ('manual', 'Manual')]}),
                  ('f', 'Padding', 'Padding (fraction of size)', 0.1, {'min': 0, 'max': 2, 'norm': (0, 0.5)}),
                  ('xyz', 'Boundscenter', 'Bounds Center', [0, 0, 0], {'min': -100, 'max': 100, 'norm': (-5, 5)}),
                  ('xyz', 'Boundssize', 'Bounds Size', [3, 3, 3], {'min': 0.01, 'max': 200, 'norm': (0.1, 10)}),
                  ('i', 'Band', 'Narrow Band (voxels)', 4, {'min': 2, 'max': 16, 'clamp': True}),
                  ('m', 'Update', 'Update', 'once', {'menu': [('once', 'Once (on input / parameter change)'), ('everyframe', 'Every frame')]})]})
c.customPages[-1].appendPulse('Bake', label='Bake Now')
pars(c, color_par((0.85, 0.85, 0.85)))
pars(c, {'Look': [('f', 'Previewscale', 'Preview Framing Scale', 1.0, {'min': 0.05, 'max': 100, 'norm': (0.2, 10)})]})

# ---------------- inputs, demo, source ----------------
inp = c.create(td.inPOP, 'in1')
inm = c.create(td.inCHOP, 'in2')
mkdat(c, 'modlib', '''# modulation helpers: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else the default
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i or not i[0].inputs: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
''')
MOD = lambda n, d=0.0: "op('modlib').module.m('%s', %s)" % (n, d)

demo = c.create(td.baseCOMP, 'demo')
dsp = demo.create(td.spherePOP, 'blob'); dsp.par.type = 'geodesic'; dsp.par.freq = 8; dsp.par.surftype = 'triangles'
dsp.par.radx = dsp.par.rady = dsp.par.radz = 0.62
dnz = demo.create(td.noisePOP, 'lumps'); dnz.inputConnectors[0].connect(dsp)
dnz.par.type = 'simplex3d'; dnz.par.harmon = 2; dnz.par.period = 1.6; dnz.par.amp0 = 0.32; dnz.par.combineop = 'translatealongnormal'
dnz.par.tx.expr = 'absTime.seconds * 0.35'; dnz.par.ty.expr = 'absTime.seconds * 0.22'
dto = demo.create(td.torusPOP, 'torus'); dto.par.radx = 0.75; dto.par.rady = 0.3; dto.par.cols = 40; dto.par.rows = 20
dto.par.orient = 'x' if 'x' in dto.par.orient.menuNames else dto.par.orient.eval()
dsw = demo.create(td.switchPOP, 'shape'); dsw.inputConnectors[0].connect(dnz); dsw.inputConnectors[1].connect(dto)
dsw.par.index.expr = "0 if parent(2).par.Mode == 'points' else 1"
dout = demo.create(td.outPOP, 'out1'); dout.inputConnectors[0].connect(dsw)

src = c.create(td.switchPOP, 'source')
src.inputConnectors[0].connect(demo.outputConnectors[0]); src.inputConnectors[1].connect(inp)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

def setvec(o, i, name, *vals):
    o.par['vec%dname' % i] = name
    o.par['vec%dtype' % i] = 'vec4'
    for k, v in zip('xyzw', vals):
        p = o.par['vec%dvalue%s' % (i, k)]
        if isinstance(v, str): p.expr = v
        else: p.val = v

def attr(o, i, name, typ, n, arr=None):
    o.par['attr%dname' % i] = 'custom'; o.par['attr%dcustomname' % i] = name
    o.par['attr%dtype' % i] = typ; o.par['attr%dnumcomps' % i] = str(n)
    if arr is not None:
        o.par['attr%disarray' % i] = True
        if isinstance(arr, str): o.par['attr%darraysize' % i].expr = arr
        else: o.par['attr%darraysize' % i] = arr

# ---------------- points: pack -> grid ----------------
base_pack = rd(NAME, 'pack.glsl')
for v in range(4):
    mkdat(c, 'pack_code%d' % v, ('#define HAS_PSCALE\n' if v & 1 else '') + ('#define HAS_COLOR\n' if v & 2 else '') + base_pack)
pk = c.create(td.glslPOP, 'pack'); pk.inputConnectors[0].connect(src)
pk.par.computedat.expr = ("op('pack_code%d' % ((1 if 'PointScale' in [a.name for a in op('source').pointAttributes] else 0)"
                          " + (2 if 'Color' in [a.name for a in op('source').pointAttributes] else 0)))")
pk.par.outputattrs = ''
pk.seq.attr.numBlocks = 1
attr(pk, 0, 'pts', 'float', 1, 8)
pk.seq.vec.numBlocks = 2
setvec(pk, 0, 'uA', P + 'Radius * (1 + 0.6 * ' + MOD('beat') + ')', "1 if %sUsepscale else 0" % P, P + 'Maxpoints', "1 if %sUsecolor else 0" % P)
setvec(pk, 1, 'uC', P + 'Colorr', P + 'Colorg', P + 'Colorb', 0)

cells = c.create(td.pointgeneratorPOP, 'cells')
cells.par.numpoints.expr = P + 'Gridres ** 3'
gr = c.create(td.glslPOP, 'grid'); gr.inputConnectors[0].connect(cells); gr.inputConnectors[1].connect(pk)
gr.par.computedat = mkdat(c, 'grid_code', rd(NAME, 'grid.glsl'))
gr.par.numthreadsmode = 'otherinputelements'; gr.par.threadsinput = 1
gr.par.npasses = 3; gr.par.outputaccess = 'readwrite'; gr.par.outputattrs = ''
gr.seq.attr.numBlocks = 3
attr(gr, 0, 'cell', 'uint', 1, P + 'Cellcap + 1')
attr(gr, 1, 'bnd', 'float', 1, 7)
attr(gr, 2, 'red', 'uint', 1, 8)
gr.seq.vec.numBlocks = 1
setvec(gr, 0, 'uA', P + 'Gridres', P + 'Cellcap', P + 'Blend * (1 + 2 * ' + MOD('band1') + ')', 0)

# ---------------- mesh: triangles -> voxel columns -> 3D texture (+ bounds texture) ----------------
mkdat(c, 'ctl', '''# Update = once: the triangle POP `unique` is LOCKED, so the input mesh and everything upstream stop cooking (the voxelizer and
# the baked texture only re-run when a bake parameter changes). It is unlocked for a few frames after load, Bake Now,
# a Mode / Update change and an input rewire (capture), then locked again (settle). State is per component,
# module-level, never saved.
_S = {}
def touch(c):
    if c.path not in _S:                    # first cook of the node in mesh mode (e.g. after load): freeze once baked
        _S[c.path] = 1
        run("op(%r).module.settle(op(%r))" % (c.op('ctl').path, c.path), delayFrames=5)
def lock(c, v):
    o = c.op('unique')
    if v: o.cook(force=True)
    o.lock = bool(v)
def capture(c):
    _S[c.path] = 1
    lock(c, False)
    run("op(%r).module.settle(op(%r))" % (c.op('ctl').path, c.path), delayFrames=5)
def settle(c):
    if c.par.Mode.eval() == 'mesh' and c.par.Update.eval() == 'once': lock(c, True)
''')
qt = c.create(td.convertPOP, 'quads_to_tris'); qt.inputConnectors[0].connect(src); qt.par.convert = 'quadstotriangles'
tri = c.create(td.switchPOP, 'triangles')      # the converter only runs (and only warns about missing quads) when there are quads
tri.inputConnectors[0].connect(src); tri.inputConnectors[1].connect(qt)
tri.par.index.expr = "0 if op('source').numVerts() == 3 * op('source').numPrims() else 1"
uniq = c.create(td.facetPOP, 'unique'); uniq.inputConnectors[0].connect(tri); uniq.par.operation = 'unique'
cols = c.create(td.pointgeneratorPOP, 'columns')
cols.par.numpoints.expr = P + 'Resolution ** 2'
vx = c.create(td.glslPOP, 'vox'); vx.inputConnectors[0].connect(cols); vx.inputConnectors[1].connect(uniq)
vx.par.computedat = mkdat(c, 'vox_code', rd(NAME, 'vox.glsl'))
vx.par.numthreadsmode = 'otherinputelements'; vx.par.threadsinput = 1
vx.par.npasses = 3; vx.par.outputaccess = 'readwrite'; vx.par.outputattrs = ''
vx.seq.attr.numBlocks = 4
attr(vx, 0, 'dist', 'uint', 1, P + 'Resolution')
attr(vx, 1, 'par', 'uint', 1, 8)
attr(vx, 2, 'bnd', 'float', 1, 6)
attr(vx, 3, 'red', 'uint', 1, 8)
vx.seq.vec.numBlocks = 3
isman = "1 if %sBoundsmode == 'manual' else 0" % P
setvec(vx, 0, 'uA', P + 'Resolution', P + 'Band', isman, P + 'Padding')
setvec(vx, 1, 'uB', *[P + 'Boundscenter%s - %sBoundssize%s/2' % (a, P, a) for a in 'xyz'] + [0])
setvec(vx, 2, 'uC', *[P + 'Boundscenter%s + %sBoundssize%s/2' % (a, P, a) for a in 'xyz'] + [0])

bk = c.create(td.glslTOP, 'bake')
bk.par.mode = 'compute'; bk.par.computedat = mkdat(c, 'bake_code', rd(NAME, 'bake.glsl'))
bk.par.type = 'texture3d'; bk.par.outputresolution = 'custom'
bk.par.resolutionw.expr = P + 'Resolution'; bk.par.resolutionh.expr = P + 'Resolution'
bk.par.depth = 'custom'; bk.par.customdepth.expr = P + 'Resolution'
bk.par.format = 'rgba16float'
bk.seq.buffer.numBlocks = 3
for i, (nm, at) in enumerate((('vdist', 'dist'), ('vpar', 'par'), ('vbnd', 'bnd'))):
    bk.par['buffer%dpop' % i] = vx; bk.par['buffer%dattrclass' % i] = 'point'; bk.par['buffer%dattr' % i] = at; bk.par['buffer%dname' % i] = nm
vecs(bk, [('uA', [P + 'Resolution', P + 'Band', 0, 0]), ('uCol', [P + 'Colorr', P + 'Colorg', P + 'Colorb', 0])])
volume = c.create(td.nullTOP, 'volume'); volume.inputConnectors[0].connect(bk)
bd = c.create(td.glslTOP, 'mbnd')              # bounds of the volume: texel 0 = min xyz, texel 1 = max xyz (locked together with it)
bd.par.pixeldat = mkdat(c, 'mbnd_code', rd(NAME, 'mbnd.glsl'))
bd.par.outputresolution = 'custom'; bd.par.resolutionw = 2; bd.par.resolutionh = 1; bd.par.format = 'rgba32float'
bd.par.inputfiltertype = 'nearest'
bd.seq.buffer.numBlocks = 1
bd.par.buffer0pop = vx; bd.par.buffer0attrclass = 'point'; bd.par.buffer0attr = 'bnd'; bd.par.buffer0name = 'vbnd'

# Bake pulse / parameter changes re-capture the held mesh
mkdat(c, 'bake_cb', '''def onPulse(par):
    op('ctl').module.capture(par.owner)
    return
def onValueChange(par, prev):
    op('ctl').module.capture(par.owner)
    return
''', td.parameterexecuteDAT)
pe = c.op('bake_cb')
pe.par.op = '..'; pe.par.pars = 'Bake Update Mode'; pe.par.onpulse = True; pe.par.valuechange = True; pe.par.custom = True; pe.par.builtin = False
mkdat(c, 'pathwatch', '''# the wire carries absolute operator paths: re-write it when this component is renamed or moved;
# a new input wiring re-captures the held mesh (Update = once)
def onNameChange(changeOp):
    op('sdf').cook(force=True)
    return
def onPathChange(changeOp):
    op('sdf').cook(force=True)
    return
def onWireChange(changeOp):
    op('ctl').module.capture(parent())
    return
''', td.opexecuteDAT)
aw = c.op('pathwatch')
aw.par.op = '..'
for pn in ('precook', 'postcook', 'flagchange', 'uichange', 'numchildrenchange', 'childrename', 'currentchildchange', 'extensionchange'):
    if hasattr(aw.par, pn): setattr(aw.par, pn, False)
aw.par.namechange = True; aw.par.pathchange = True; aw.par.wirechange = True

# ---------------- the SDF node ----------------
node(c, 'from_pop', rd(NAME, 'node_points.glsl'),
     """if p.Mode == 'points':
    vals = [(p.Gridres, p.Cellcap, p.Blend.eval() * (1 + 2 * (op('modlib').module.m('band1'))), 0)]
else:
    vals = [(p.Resolution, p.Band, 0, 0)]""",
     tex_py="""if p.Mode == 'points':
    tex = [dict(name='T_@ID@_p', type='buffer', path=parent().op('pack').path, attr='pts', cls='point'),
           dict(name='T_@ID@_g', type='buffer', path=parent().op('grid').path, attr='cell', cls='point'),
           dict(name='T_@ID@_b', type='buffer', path=parent().op('grid').path, attr='bnd', cls='point')]
else:
    op('ctl').module.touch(parent())
    tex = [dict(name='T_@ID@_b', type='2d', path=parent().op('mbnd').path, attr='P', cls='point'),
           dict(name='T_@ID@_v', type='3d', path=parent().op('volume').path, attr='P', cls='point')]""")
cb = c.op('sdf_cb')
cb.text = cb.text.replace("op('code').text", "op('code_mesh' if p.Mode == 'mesh' else 'code').text")
mkdat(c, 'code_mesh', rd(NAME, 'node_mesh.glsl'))
preview(c, scale=P + 'Previewscale')
finish(c, NAME); report(c)
