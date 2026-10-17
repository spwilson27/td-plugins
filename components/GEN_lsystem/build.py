# ---- shared helpers (pasted at top of each build.py; self-contained) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def fresh(name):
    b = op('/build') or op('/').create(td.containerCOMP, 'build')
    o = b.op(name)
    if o: o.destroy()
    c = b.create(td.baseCOMP, name)
    return c

def readf(name, fn):
    return open(os.path.join(ROOT, 'components', name, fn)).read()

def mkdat(c, nm, text):
    d = c.create(td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    """spec: {page: [(kind, name, label, default, opts)]} kind: f,i,t,m,p,rgb,wh,xy,s"""
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            if kind == 'f': ps = pg.appendFloat(nm, label=lab)
            elif kind == 'i': ps = pg.appendInt(nm, label=lab)
            elif kind == 't': ps = pg.appendToggle(nm, label=lab)
            elif kind == 'p': ps = pg.appendPulse(nm, label=lab)
            elif kind == 's': ps = pg.appendStr(nm, label=lab)
            elif kind == 'm': ps = pg.appendMenu(nm, label=lab)
            elif kind == 'rgb': ps = pg.appendRGB(nm, label=lab)
            elif kind == 'wh': ps = pg.appendWH(nm, label=lab)
            elif kind == 'xy': ps = pg.appendXY(nm, label=lab)
            p0 = ps[0]
            if kind == 'm':
                p0.menuNames = [m[0] for m in o['menu']]; p0.menuLabels = [m[1] for m in o['menu']]
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                p.default = v; p.val = v
                if 'min' in o: p.min = o['min']; p.normMin = o['min']; p.clampMin = o.get('clamp', False)
                if 'max' in o: p.max = o['max']; p.normMax = o['max']; p.clampMax = o.get('clamp', False)
    return c

def uni(g, items):
    """items: list of (name, [4 values or expr strings]); sets vecN on a GLSL TOP"""
    for i, (nm, vs) in enumerate(items):
        getattr(g.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', vs):
            p = getattr(g.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v

def glsl(c, nm, code, items, res=True, fmt=None, mode=None):
    d = mkdat(c, nm + '_code', code)
    g = c.create(td.glslTOP, nm)
    g.par.pixeldat = d
    if res:
        g.par.outputresolution = 'custom'
        g.par.resolutionw.expr = "parent().par.Resolutionw"
        g.par.resolutionh.expr = "parent().par.Resolutionh"
    if fmt: g.par.format = fmt
    uni(g, items)
    return g

def ios(c, src):
    o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(src); return o

def report(c):
    errs = []
    for o in [c] + c.findChildren():
        for s in (o.errors(), o.warnings(), o.scriptErrors()):
            if s: errs.append((o.path, s[:300]))
    print('ERRS', errs)
# ---- end helpers ----
# ---- GEN_lsystem (v3): POP lines out (out1), optional POP in1 = planting points, optional modulation CHOP last ----
name = 'GEN_lsystem'
c = fresh(name)
P = "parent().par."
HASIN = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
def MOD(ch, default=0):
    return "(op('modin')['%s'].eval() if (op('modin') and op('modin').numChans and op('modin')['%s'] is not None) else %s)" % (ch, ch, default)

pars(c, {
 'Controls': [
  ('wh','Resolution','Preview Resolution',[960,540]),
  ('m','Preset','Preset',0,{'menu':[('plant','Fractal plant'),('tree','Binary tree'),('bush','Bush'),('koch','Koch snowflake'),('dragon','Dragon curve'),('custom','Custom')]}),
  ('f','Growth','Growth',1.0,{'min':0,'max':1,'clamp':True}),
  ('t','Animate','Animate Growth',True),
  ('f','Growspeed','Grow Speed',0.15,{'min':0,'max':2}),
  ('f','Treesize','Tree Size',1.0,{'min':0.01,'max':20}),
  ('i','Maxtrees','Max Trees',32,{'min':1,'max':500}),
  ('f','Variation','Variation (rotation, size)',1.0,{'min':0,'max':1,'clamp':True}),
  ('t','Align','Align To Normal',False),
  ('i','Seed','Seed',1,{'min':0,'max':1000}),
  ('f','Linewidth','Line Width',3.0,{'min':0.5,'max':20}),
  ('f','Taper','Branch Taper',0.8,{'min':0.3,'max':1}),
  ('rgb','Colora','Root Color',[0.45,0.28,0.12]),
  ('rgb','Colorb','Tip Color',[0.4,1.0,0.35]),
 ],
 'Lsystem': [
  ('s','Axiom','Axiom','X'),
  ('s','Rule1','Rule 1','X=F+[[X]-X]-F[-FX]+X'),
  ('s','Rule2','Rule 2','F=FF'),
  ('s','Rule3','Rule 3',''),
  ('i','Iterations','Iterations',5,{'min':0,'max':14}),
  ('f','Angle','Angle',25,{'min':0,'max':180}),
  ('f','Lengthscale','Branch Length Scale',1.0,{'min':0.3,'max':1.2}),
  ('f','Heading','Start Heading',65,{'min':-180,'max':360}),
  ('m','Anchor','Anchor',0,{'menu':[('root','Root at planting point'),('center','Centered')]}),
  ('p','Regenerate','Regenerate',False),
 ],
 'Preview': [
  ('f','Camdist','Camera Distance',2.7,{'min':0.5,'max':100}),
  ('f','Camlift','Camera Target Height',0.45,{'min':-5,'max':20}),
  ('f','Fov','Field of View',40,{'min':10,'max':90}),
  ('rgb','Bgcolor','Background',[0.02,0.03,0.04]),
 ]})
pg = c.appendCustomPage('Look')
p = pg.appendMenu('Look', label='Look')[0]; p.menuNames=['original','mono']; p.menuLabels=['Original','Mono']; p.default='original'; p.val='original'
p = pg.appendFloat('Accent', label='Accent (red, Mono)')[0]; p.min=0; p.max=1; p.normMin=0; p.normMax=1; p.default=0; p.val=0
MONO = P + "Look.menuIndex"
c.par.Preset = 'plant'

# ---- inputs ----
i1 = c.create(td.inPOP, 'in1')
i2 = c.create(td.inCHOP, 'in2')
mi = c.create(td.nullCHOP, 'modin'); mi.inputConnectors[0].connect(i2)

# ---- template tree: table -> points (2 per segment) -> lines ----
ex = mkdat(c, 'lsys_expand', readf(name, 'expand.py'))
tab = c.create(td.scriptDAT, 'segs')
cb = mkdat(c, 'segs_callbacks', readf(name, 'segs_cb.py'))
tab.par.callbacks = cb
pe = c.create(td.parameterexecuteDAT, 'pexec'); pe.text = readf(name, 'pexec.py')
pe.par.op = c
pe.par.pars = 'Preset Regenerate'
pe.par.valuechange = True; pe.par.onpulse = True
tab.cook(force=True)
dp = c.create(td.dattoPOP, 'segpts'); dp.par.pointsdat = tab
dp.par.attr0columnstype = 'number'; dp.par.attr0columns = '0 1 2'; dp.par.attr0outputscope = 'P'; dp.par.attr0numcomps = '3'
dp.seq.attr.numBlocks = 3
dp.par.attr1columnstype = 'number'; dp.par.attr1columns = '3 4 5 6'; dp.par.attr1outputscope = 'Color'; dp.par.attr1numcomps = '4'
dp.par.attr2columnstype = 'number'; dp.par.attr2columns = '7 8 9'; dp.par.attr2outputscope = 'Tex'; dp.par.attr2numcomps = '3'
ln = c.create(td.primitivePOP, 'lines'); ln.inputConnectors[0].connect(dp)
ln.par.keep = True; ln.par.method = 'set'; ln.par.setprimtype = 'lines'

# ---- growth / colour / width ----
gcode = mkdat(c, 'grow_code', readf(name, 'grow.glsl'))
gr = c.create(td.glslPOP, 'grow'); gr.inputConnectors[0].connect(ln); gr.par.computedat = gcode
gr.par.outputattrs = 'P Color LineWidth'
gr.seq.attr.numBlocks = 1
gr.par.attr0name = 'linewidth'
gr.seq.vec.numBlocks = 4
GR = "min(1.0, ((absTime.seconds*%sGrowspeed + 0.45) %% 1.5) / 0.9) if %sAnimate else %sGrowth" % (P, P, P)
vecs = [('uA', [GR, P+"Linewidth", P+"Taper", MOD('beat')]),
        ('uB', ["0.32 if %s else %sColorar" % (MONO, P), "0.32 if %s else %sColorag" % (MONO, P), "0.31 if %s else %sColorab" % (MONO, P), MOD('band1')]),
        ('uC', ["0.94 if %s else %sColorbr" % (MONO, P), "0.92 if %s else %sColorbg" % (MONO, P), "0.86 if %s else %sColorbb" % (MONO, P), 0]),
        ('uD', [MONO, P+"Accent", 0, 0])]
for k, (n2, vals) in enumerate(vecs):
    getattr(gr.par, 'vec%dname' % k).val = n2
    getattr(gr.par, 'vec%dtype' % k).val = 'vec4'
    for j, v in enumerate(vals):
        q = getattr(gr.par, 'vec%dvalue%s' % (k, 'xyzw'[j]))
        if isinstance(v, str): q.expr = v
        else: q.val = v

# ---- planting points: demo (one tree at origin) or in1 ----
demo = c.create(td.baseCOMP, 'demo')
dpt = demo.create(td.gridPOP, 'origin')   # one point at the origin, normal +Y
dpt.par.surftype = 'points'; dpt.par.cols = 1; dpt.par.rows = 1; dpt.par.planex = False; dpt.par.planey = True; dpt.par.rx = -90
do = demo.create(td.outPOP, 'demo_out'); do.inputConnectors[0].connect(dpt)
sw = c.create(td.switchPOP, 'plantsrc')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = HASIN
pcode = mkdat(c, 'plant_code', readf(name, 'plant.glsl'))
po = c.create(td.primitivePOP, 'ptsonly'); po.inputConnectors[0].connect(sw)   # drop faces/lines, keep the points
po.par.keep = True; po.par.method = 'none'
pl = c.create(td.glslPOP, 'plant'); pl.inputConnectors[0].connect(po); pl.par.computedat = pcode
pl.par.outputattrs = 'TreeRot TreeScale TreeKeep'
pl.seq.attr.numBlocks = 3
pl.par.attr0name = 'custom'; pl.par.attr0customname = 'TreeRot'; pl.par.attr0numcomps = '3'
pl.par.attr1name = 'custom'; pl.par.attr1customname = 'TreeScale'; pl.par.attr1numcomps = '3'
pl.par.attr2name = 'custom'; pl.par.attr2customname = 'TreeKeep'; pl.par.attr2numcomps = '1'
pl.seq.vec.numBlocks = 1
pl.par.vec0name = 'uA'; pl.par.vec0type = 'vec4'
pl.par.vec0valuex.expr = P + "Seed"; pl.par.vec0valuey.expr = P + "Variation"; pl.par.vec0valuez.expr = P + "Treesize"; pl.par.vec0valuew.expr = P + "Maxtrees"
thin = c.create(td.deletePOP, 'thin'); thin.inputConnectors[0].connect(pl)
thin.par.entity = 'point'; thin.par.attr = 1
thin.par.attr0inattr = 'TreeKeep'; thin.par.attr0func = 'lt'; thin.par.attr0value = 0.5

# ---- copy tree onto points ----
cp = c.create(td.copyPOP, 'plantcopy')
cp.inputConnectors[0].connect(gr); cp.inputConnectors[1].connect(thin)
cp.par.dotemplaterotate = True; cp.par.rotateattr = 'TreeRot'
cp.par.dotemplatescale = True; cp.par.scaleattrib = 'TreeScale'
cp.par.dotemplaterotateto.expr = P + "Align"; cp.par.instanceforward = 'posy'; cp.par.vecattr = 'N'
res = c.create(td.nullPOP, 'lines_out'); res.inputConnectors[0].connect(cp)
o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(res); o1.comment = 'lines (POP)'

# ---- internal preview render (not an output) ----
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = res
sel.display = True; sel.render = True
mat = c.create(td.lineMAT, 'mat')
mat.par.widthnear = 1; mat.par.widthfar = 1
for k in ('linenear', 'linefar'):
    for ch in 'rgb': getattr(mat.par, k + 'color' + ch).val = 1
geo.par.material = mat
cam = c.create(td.cameraCOMP, 'cam')
cam.par.tz.expr = P + "Camdist"; cam.par.ty.expr = P + "Camlift"
cam.par.fov.expr = P + "Fov"
cam.par.tx = 0
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P + "Resolutionw"; rt.par.resolutionh.expr = P + "Resolutionh"
rt.par.bgcolorr.expr = "0 if %s else %sBgcolorr" % (MONO, P); rt.par.bgcolorg.expr = "0 if %s else %sBgcolorg" % (MONO, P); rt.par.bgcolorb.expr = "0 if %s else %sBgcolorb" % (MONO, P); rt.par.bgcolora = 1
rt.par.antialias = 'aa4'
pv = c.create(td.nullTOP, 'preview'); pv.inputConnectors[0].connect(rt)
pv.comment = 'preview render (node viewer; not an output)'
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % name))
report(c)
print('saved', c.op('segs').numRows // 2, 'segments')
