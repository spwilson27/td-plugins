# ---- v3 helpers (self-contained; copy into each build.py) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
COMP = 'POP_terrain'

def rd(comp, fn): return open(os.path.join(ROOT, 'components', comp, fn)).read()
def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)
def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

# resolution of the effect: follows in1 when connected and Resolutionmode == input, else custom
RW = "(parent().op('in1').width if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionw)"
RH = "(parent().op('in1').height if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionh)"
CONN = "len(parent().inputConnectors[0].connections)"
def setres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RW; o.par.resolutionh.expr = RH
def CH(n): return "parent().op('mod')['%s'].eval()" % n

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=True):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    return g

def add_pars(c, specs, page='Controls'):
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse': pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]; p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            for q, v in zip(pg.appendWH(n), s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'rgb':
            for q, v in zip(pg.appendRGB(n), s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def std_top_pars(c):
    """Mix / Bypass / Resolutionmode / Resolution on the Controls page (call after the component pars)."""
    pg = [p for p in c.customPages if p.name == 'Controls'][0]
    p = pg.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    pg.appendToggle('Bypass')
    p = pg.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    for q, v in zip(pg.appendWH('Resolution'), (1280, 720)):
        q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
    c.par.Resolutionw.enableExpr = "parent().par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "parent().par.Resolutionmode=='custom'"

def mod_chop(c, name):
    """optional modulation In CHOP (band1..4, beat) merged over zeros so every channel always exists"""
    im = c.create(td.inCHOP, name)
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im); mg.inputConnectors[1].connect(mz)
    mg.par.duplicate = 'first'; mg.par.align = 'start'
    return mg

def demo_switch(c, demo_out, name='src', in1='in1'):
    """Switch TOP: index 0 = demo (gated), 1 = in1. Index is 1 when in1 is connected."""
    sw = c.create(td.switchTOP, name)
    sw.inputConnectors[0].connect(demo_out); sw.inputConnectors[1].connect(c.op(in1))
    sw.par.index.expr = "(1 if %s else 0) + 0*absTime.frame" % CONN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

def mix_bypass(c, dry, wet, out_name='out1'):
    x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(dry); x.inputConnectors[1].connect(wet)
    x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'; x.par.outputresolution = 'useinput'
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(x); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "1 if (parent().par.Bypass and %s) else 0" % CONN
    o = c.create(td.outTOP, out_name); o.inputConnectors[0].connect(bp)
    return o

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
# ---- end helpers ----

P = 'parent().par.'
c = new_comp(COMP)
add_pars(c, [
    ('Heightsource', 'menu', [('noise', 'Noise'), ('input', 'Input (in2 TOP)')], 0),
    ('Style', 'menu', [('smooth', 'Smooth'), ('ridged', 'Ridged'), ('terraced', 'Terraced')], 0),
    ('Height', 'float', 0.22, 0, 3),
    ('Scale', 'float', 3.0, 0.5, 20),
    ('Terraces', 'int', 6, 2, 24),
    ('Speed', 'float', 0.15, -2, 2),
    ('Seed', 'int', 1, 0, 999),
])
add_pars(c, [
    ('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
    ('Accent', 'float', 0.0, 0, 1),
], page='Look')

i1 = c.create(td.inPOP, 'in1'); i1.par.connectorder = 1
i2 = c.create(td.inTOP, 'in2'); i2.par.connectorder = 2
mod_chop(c, 'in3')

# ---- demo (preview only): a grid POP, gated off whenever in1 is connected
demo = c.create(td.baseCOMP, 'demo')
dg = demo.create(td.gridPOP, 'grid')
dg.par.surftype = 'quads'; dg.par.sizex = 2; dg.par.sizey = 2; dg.par.cols = 80; dg.par.rows = 80
do = demo.create(td.outPOP, 'out1'); do.inputConnectors[0].connect(dg)
sw = c.create(td.switchPOP, 'src')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = "(1 if %s else 0) + 0*absTime.frame" % CONN

# ---- texcoords (planar from bounding box) + normals
tm = c.create(td.texturemapPOP, 'texcoords'); tm.inputConnectors[0].connect(sw)
tm.par.texmethod = 'xyznorm'; tm.par.axis = 'z'
nin = c.create(td.normalPOP, 'normals_in'); nin.inputConnectors[0].connect(tm)

# ---- heightmap: internal noise or in2
nz = c.create(td.noiseTOP, 'hnoise')
nz.par.type = 'simplex2d'
nz.par.outputresolution = 'custom'; nz.par.resolutionw = 512; nz.par.resolutionh = 512
nz.par.period.expr = '8.0/' + P + 'Scale'; nz.par.harmon = 3; nz.par.rough = 0.45
nz.par.amp = 0.5; nz.par.offset = 0.5; nz.par.mono = True
nz.par.seed.expr = P + 'Seed'; nz.par.format = 'rgba16float'
hm = c.create(td.switchTOP, 'hmap')
hm.inputConnectors[0].connect(nz); hm.inputConnectors[1].connect(i2)
hm.par.index.expr = "0*absTime.frame + 1 if (%sHeightsource=='input' and len(parent().inputConnectors[1].connections)) else 0" % P
hm.par.outputresolution = 'useinput' if 'useinput' in hm.par.outputresolution.menuNames else hm.par.outputresolution.val

# ---- displace
code = mkdat(c, 'displace_code', rd(COMP, 'terrain.glsl'))
g = c.create(td.glslPOP, 'displace'); g.inputConnectors[0].connect(nin)
g.par.computedat = code; g.par.outputattrs = 'P'; g.par.attr0name = 'color'
g.par.sampler0name = 'uTex'; g.par.sampler0top = hm
g.par.sampler0extendv = 'mirror'
SRC_NOISE = "(0 if (%sHeightsource=='input' and len(parent().inputConnectors[1].connections)) else 1)" % P
g.seq.vec.numBlocks = 2
vecs = [('uA', [P + 'Height*(1+0.6*' + CH('band1') + '+0.3*' + CH('beat') + ')',
                'absTime.seconds*' + P + 'Speed*(1+0.5*' + CH('band2') + ')*0.2',
                "{'smooth':0,'ridged':1,'terraced':2}[%sStyle.eval()]" % P, P + 'Terraces']),
        ('uB', [P + 'Look.menuIndex', P + 'Accent', SRC_NOISE, 0])]
for i, (nm, vals) in enumerate(vecs):
    getattr(g.par, 'vec%dname' % i).val = nm
    getattr(g.par, 'vec%dtype' % i).val = 'vec4'
    for j, v in enumerate(vals):
        p = getattr(g.par, 'vec%dvalue%s' % (i, 'xyzw'[j]))
        if isinstance(v, str): p.expr = v
        else: p.val = v
nout = c.create(td.normalPOP, 'normals_out'); nout.inputConnectors[0].connect(g)
o1 = c.create(td.outPOP, 'out1'); o1.inputConnectors[0].connect(nout)

# ---- preview: dark ground + wire render
geo_w = c.create(td.geometryCOMP, 'geo_wire'); geo_s = c.create(td.geometryCOMP, 'geo_ground')
for geo in (geo_w, geo_s):
    for o in list(geo.children): o.destroy()
    sel = geo.create(td.selectPOP, 'select'); sel.par.pop = o1
    sel.display = True; sel.render = True
    geo.par.rx = -90
mw = c.create(td.constantMAT, 'wire_mat'); mw.par.applypointcolor = True; mw.par.wireframe = True; mw.par.wirewidth = 1.5
mw.par.blending = True; mw.par.srcblend = 'one'; mw.par.destblend = 'one'; mw.par.depthwriting = False
ms = c.create(td.constantMAT, 'ground_mat'); ms.par.colorr = ms.par.colorg = ms.par.colorb = 0.004
geo_w.par.material = mw; geo_s.par.material = ms
geo_s.par.drawpriority = 1; geo_w.par.drawpriority = -1
cam = c.create(td.cameraCOMP, 'cam')
cam.par.tx = 0; cam.par.ty = 2.3; cam.par.tz = 2.6; cam.par.rx = -41; cam.par.fov = 45
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = 'geo_ground geo_wire'; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw = 800; rt.par.resolutionh = 450
rt.par.bgcolorr = rt.par.bgcolorg = rt.par.bgcolorb = 0.012; rt.par.bgcolora = 1
rt.par.format = 'rgba16float'; rt.par.antialias = 'aa4'
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(rt); bl.par.size = 8
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1 = 1.0
cm = c.create(td.compositeTOP, 'preview'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(rt); cm.inputConnectors[1].connect(lv)
finish(c, COMP)
report(c)
