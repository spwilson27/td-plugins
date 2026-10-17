# ---- shared helpers (pasted at top of each build.py by components/_lib/mk.sh) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

def setres(o, w='parent().par.Resolutionw', h='parent().par.Resolutionh'):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w; o.par.resolutionh.expr = h

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=False, filt=None):
    """vecs: list of (uniformName, [4 values/exprs]) ; exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:   # inputs beyond the 3 wire connectors go through the TOPs parameter (index 3..)
        g.par.tops = ' '.join(s.name for s in inputs[3:])
    if vecs:
        g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    if filt: g.par.filtertype = filt
    return g

def add_pars(c, specs, page='Controls'):
    """spec tuples: (name, kind, ...)
      ('Amount','float',default,min,max)   ('Count','int',def,min,max)  ('On','toggle',def)
      ('Reset','pulse')  ('Mode','menu',[(id,label),..],default_index)  ('Res','wh',(w,h))
      ('Col','rgb',(r,g,b))  ('Txt','str',default)  ('Xy','xy',(x,y))"""
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse':
            pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]
            p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            ps = pg.appendWH(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'xy':
            ps = pg.appendXY(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.normMin = -1; q.normMax = 1
        elif k == 'rgb':
            ps = pg.appendRGB(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def input_stage(c, comp, bg=1.0):
    """in1 + animated default source -> switch 'src' (resolution = Resolution par). Returns src TOP."""
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', rd(comp, 'src.glsl'), vecs=[('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

COMP = 'POP_plexus_points'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Source','menu',[('shape','Input POP (in1; demo shape if unconnected)'),('image','Image luma (in2 TOP)')],0),
 ('Points','int',2500,100,12000),
 ('Linkdistance','float',0.16,0.02,0.8),
 ('Maxlinks','int',3,1,8),
 ('Longlines','int',10,0,60),
 ('Longspread','float',3.2,1,8),
 ('Pointsize','float',2.6,0.5,10),
 ('Lineopacity','float',0.38,0,1),
 ('Longopacity','float',1.7,0,2),
 ('Brightness','float',1.0,0,3),
 ('Banding','float',0.85,0,1),
 ('Bands','int',10,2,80),
 ('Bandshift','float',0.08,0,0.3),
 ('Bandsteps','int',8,1,32),
 ('Sweep','float',0.6,0,2),
 ('Sweepcycles','int',2,1,6),
 ('Jitter','float',0.012,0,0.1),
 ('Scale','float',1.0,0.2,3),
 ('Threshold','float',0.12,0,1),
 ('Imgsamples','float',2.5,0.1,3),
 ('Imgdepth','float',0.8,0,3),
])
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Demoshape','menu',[('blob','Head-ish blob'),('sphere','Sphere'),('torus','Torus')],0),
 ('Camdist','float',7.6,2,20),
 ('Camheight','float',0.5,-4,6),
 ('Orbitturns','int',1,0,4),
 ('Orbitrange','float',1.0,0,1),
 ('Fov','float',42,10,90),
 ('Grid','float',0.28,0,2),
 ('Gridsize','float',0.09,0.02,0.4),
 ('Glow','float',0.35,0,2),
], page='Preview')
P = 'parent().par.'
PH = "(absTime.seconds/16.0)"      # internal preview animation (no loop parameters)
ang = "2*math.pi*"+PH

# inputs
inpop = c.create(td.inPOP, 'in1'); inpop.par.connectorder = 1
intop = c.create(td.inTOP, 'in2'); intop.par.connectorder = 2

# ---- demo COMP: preview-only sources (demo shape, demo image); not selected when inputs are connected
demo = c.create(td.baseCOMP, 'demo')
PP = 'parent(2).par.'
dn = demo.create(td.noiseTOP, 'default_img')
dn.par.outputresolution = 'custom'; dn.par.resolutionw = 512; dn.par.resolutionh = 512
dn.par.period = 0.35; dn.par.harmon = 3; dn.par.amp = 0.55; dn.par.offset = 0.4
dn.par.tz.expr = "0.5*math.cos(2*math.pi*absTime.seconds/16.0)"; dn.par.ty.expr = "0.5*math.sin(2*math.pi*absTime.seconds/16.0)"
rp = demo.create(td.rampTOP, 'default_vig'); rp.par.type = 'radial'
rp.par.outputresolution = 'custom'; rp.par.resolutionw = 512; rp.par.resolutionh = 512
dcmp = demo.create(td.compositeTOP, 'default_comp'); dcmp.par.operand = 'multiply'
dcmp.inputConnectors[0].connect(dn); dcmp.inputConnectors[1].connect(rp)
dimg = demo.create(td.outTOP, 'out2'); dimg.inputConnectors[0].connect(dcmp)
sp = demo.create(td.spherePOP, 'src_sphere'); sp.par.type = 'geodesic'; sp.par.surftype = 'triangles'
sp.par.radx = 1; sp.par.rady = 1; sp.par.radz = 1
sp.par.freq.expr = "max(2, int(math.sqrt(%sPoints/10.0)))" % PP
tr = demo.create(td.torusPOP, 'src_torus'); tr.par.surftype = 'triangles'; tr.par.radx = 0.9; tr.par.rady = 0.38
tr.par.cols.expr = "int(math.sqrt(%sPoints*2.4))" % PP; tr.par.rows.expr = "int(math.sqrt(%sPoints/2.4))" % PP
dsw = demo.create(td.switchPOP, 'shape'); dsw.inputConnectors[0].connect(sp); dsw.inputConnectors[1].connect(tr)
dsw.par.index.expr = "1 if %sDemoshape=='torus' else 0" % PP
dshape = demo.create(td.outPOP, 'out1'); dshape.inputConnectors[0].connect(dsw)

# image source for Source = Image: black unless in2 connected, else the demo image
none = c.create(td.constantTOP, 'img_none'); none.par.outputresolution = 'custom'; none.par.resolutionw = 16; none.par.resolutionh = 16
isw = c.create(td.switchTOP, 'img_switch'); isw.inputConnectors[0].connect(none); isw.inputConnectors[1].connect(intop); isw.inputConnectors[2].connect(demo.outputConnectors[1])
isw.par.index.expr = "0 if parent().par.Source!='image' else (1 if (len(parent().inputConnectors[1].connections)+0*absTime.frame) else 2)"

# sources
gr = c.create(td.gridPOP, 'src_grid'); gr.par.surftype = 'triangles'; gr.par.sizex = 2; gr.par.sizey = 2
gr.par.cols.expr = "int(math.sqrt(%sPoints*5))" % P; gr.par.rows.expr = "int(math.sqrt(%sPoints*5))" % P
sw = c.create(td.switchPOP, 'src_switch')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(inpop); sw.inputConnectors[2].connect(gr)
sw.par.index.expr = "2 if parent().par.Source=='image' else (1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0)"

# cloud shader
camx = "math.sin(%s*%sOrbitturns)*%sOrbitrange" % (ang, P, P)
camz = "math.cos(%s*%sOrbitturns)*%sOrbitrange" % (ang, P, P)
code = mkdat(c, 'cloud_code', rd(name, 'cloud.glsl'))
g = c.create(td.glslPOP, 'cloud'); g.inputConnectors[0].connect(sw)
g.par.computedat = code; g.par.outputattrs = 'P'
g.par.attr0name = 'color'
g.seq.attr.numBlocks = 3
g.par.attr1name = 'pointscale'
g.par.attr2name = 'custom'; g.par.attr2customname = 'Keep'
g.par.sampler0name = 'uTex'; g.par.sampler0top = isw
g.seq.vec.numBlocks = 5
vecs = [('uA',[P+'Bands', P+'Banding', P+'Bandshift', P+'Bandsteps']),
        ('uB',[ang, P+'Scale', "3 if parent().par.Source=='image' else (4 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else {'blob':0,'sphere':1,'torus':2}[parent().par.Demoshape.eval()])", P+'Imgdepth']),
        ('uC',[P+'Threshold', P+'Imgsamples', P+'Pointsize', P+'Jitter']),
        ('uD',[camx, "0.12", camz, P+'Brightness']),
        ('uE',[P+'Sweep', P+'Sweepcycles', 0, 0])]
for i,(n2,vals) in enumerate(vecs):
    getattr(g.par,'vec%dname'%i).val = n2
    getattr(g.par,'vec%dtype'%i).val = 'vec4'
    for j,v in enumerate(vals):
        p = getattr(g.par,'vec%dvalue%s'%(i,'xyzw'[j]))
        if isinstance(v,str): p.expr = v
        else: p.val = v
dl = c.create(td.deletePOP, 'drop'); dl.inputConnectors[0].connect(g)
dl.par.entity = 'point'; dl.par.attr0inattr = 'Keep'; dl.par.attr0func = 'lt'; dl.par.attr0value = 0.5; dl.par.invert = 'delete'
cloud = c.create(td.nullPOP, 'out1'); cloud.comment = 'point cloud'; cloud.inputConnectors[0].connect(dl)
dots = c.create(td.convertPOP, 'dots'); dots.par.convert = 'topointprims'; dots.inputConnectors[0].connect(cloud)
px = c.create(td.proximityPOP, 'plexus'); px.inputConnectors[0].connect(cloud)
px.par.maxdist.expr = P+'Linkdistance'; px.par.maxlinesperpoint.expr = P+'Maxlinks'; px.par.output = 'lines'
px.par.maxtempneighbors = 16
out2 = c.create(td.nullPOP, 'out2'); out2.comment = 'plexus lines'; out2.inputConnectors[0].connect(px)

# long lines: copy a 2-point line onto random seed points
seeds = c.create(td.pointgeneratorPOP, 'seeds'); seeds.par.shape = 'sphere'; seeds.par.distribution = 'volume'
seeds.par.numpoints.expr = "max(1,%sLonglines)" % P
for a in 'xyz': getattr(seeds.par, 'radius'+a).val = 1.0
sg = mkdat(c, 'seed_code', "void main(){ const uint id=TDIndex(); if(id>=TDNumElements()) return; Color[id]=vec4(TDIn_P()+vec3(float(id)*0.37,0.0,0.0),1.0); }")
sgp = c.create(td.glslPOP, 'seedattr'); sgp.inputConnectors[0].connect(seeds); sgp.par.computedat = sg
sgp.par.outputattrs = ''; sgp.par.attr0name = 'color'
ln = c.create(td.gridPOP, 'line_tmpl'); ln.par.surftype = 'lines'; ln.par.cols = 2; ln.par.rows = 1; ln.par.sizex = 1; ln.par.sizey = 0
cp = c.create(td.copyPOP, 'copy_lines'); cp.inputConnectors[0].connect(ln); cp.inputConnectors[1].connect(sgp)
cp.par.dotemplatetranslate = False; cp.par.doattr = True; cp.par.templateattr0names = 'Color'
lcode = mkdat(c, 'long_code', rd(name, 'long.glsl'))
lg = c.create(td.glslPOP, 'longlines'); lg.inputConnectors[0].connect(cp)
lg.par.computedat = lcode; lg.par.outputattrs = 'P'; lg.par.attr0name = 'color'
out3 = c.create(td.nullPOP, 'out3'); out3.comment = 'long lines'; out3.inputConnectors[0].connect(lg)
lg.seq.vec.numBlocks = 2
for i,(n2,vals) in enumerate([('uA',[ang, P+'Longspread', 1, P+'Bandsteps']), ('uB',[P+'Longopacity', P+'Sweepcycles', 0, 0])]):
    getattr(lg.par,'vec%dname'%i).val = n2; getattr(lg.par,'vec%dtype'%i).val = 'vec4'
    for j,v in enumerate(vals):
        p = getattr(lg.par,'vec%dvalue%s'%(i,'xyzw'[j]))
        if isinstance(v,str): p.expr = v
        else: p.val = v

# geometry
def mkgeo(nm, src, mat):
    geo = c.create(td.geometryCOMP, nm)
    for o in list(geo.children): o.destroy()
    sel = geo.create(td.selectPOP, 'select'); sel.par.pop = src
    sel.display = True; sel.render = True
    geo.par.material = mat
    return geo
smat = c.create(td.pointspriteMAT, 'dot_mat'); smat.par.pointsize = 1
smat.par.blending = True; smat.par.srcblend = 'one'; smat.par.destblend = 'one'; smat.par.depthwriting = False
lmat = c.create(td.constantMAT, 'link_mat'); lmat.par.colorr = lmat.par.colorg = lmat.par.colorb = 1
lmat.par.alpha.expr = P+'Lineopacity'
lmat.par.blending = True; lmat.par.srcblend = 'sa'; lmat.par.destblend = 'one'; lmat.par.depthwriting = False
gmat = c.create(td.constantMAT, 'long_mat'); gmat.par.applypointcolor = True
gmat.par.blending = True; gmat.par.srcblend = 'one'; gmat.par.destblend = 'one'; gmat.par.depthwriting = False
geo_d = mkgeo('geo_dots', dots, smat)
geo_l = mkgeo('geo_links', px, lmat)
geo_g = mkgeo('geo_long', lg, gmat)
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
cam.par.tx.expr = camx+"*"+P+"Camdist"; cam.par.tz.expr = "(%s + 1 - %sOrbitrange)*%sCamdist" % (camz, P, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov.expr = P+'Fov'; cam.par.lookat = tgt
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = 'geo_dots geo_links geo_long'; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr = 0; rt.par.bgcolorg = 0; rt.par.bgcolorb = 0; rt.par.bgcolora = 1; rt.par.format = 'rgba16float'
rt.par.antialias = 'aa4'
gridt = glsl(c, 'grid', rd(name, 'grid.glsl'), vecs=[('uA',[P+'Grid', P+'Gridsize', 0, 0])], fmt='rgba16float', res=True)
cm0 = c.create(td.compositeTOP, 'comp_grid'); cm0.par.operand = 'add'
cm0.inputConnectors[0].connect(rt); cm0.inputConnectors[1].connect(gridt)
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(cm0); bl.par.size = 8
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1.expr = P+'Glow*2.0'
cm = c.create(td.compositeTOP, 'comp'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(cm0); cm.inputConnectors[1].connect(lv)
o = c.create(td.nullTOP, 'preview'); o.comment = 'preview render'; o.inputConnectors[0].connect(cm)
finish(c, name)
report(c)
