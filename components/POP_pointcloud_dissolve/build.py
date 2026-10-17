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

def mcomb(c, name, src, consts, steps, angle='rad', delete=''):
    """Math Combine POP built from plain data.  consts: [(name, 'float'|'float3', [number or expression string, ...])]
    steps: [(operation, A, B, C, result attribute)]: each step reads attributes/constants and writes one attribute."""
    mc = c.create(td.mathcombinePOP, name)
    if src is not None: mc.inputConnectors[0].connect(src)
    mc.par.angleunit = angle
    mc.seq.vec.numBlocks = len(consts)
    for k, (nm, ty, vals) in enumerate(consts):
        getattr(mc.par, 'vec%dname' % k).val = nm; getattr(mc.par, 'vec%dtype' % k).val = ty
        for q, v in enumerate(vals):
            p_ = getattr(mc.par, 'vec%dvalue%d' % (k, q))
            if isinstance(v, str): p_.expr = v
            else: p_.val = v
    mc.seq.comb.numBlocks = len(steps)
    for k, (op_, a_, b_, c_, res) in enumerate(steps):
        getattr(mc.par, 'comb%doper' % k).val = op_
        getattr(mc.par, 'comb%dscopea' % k).val = a_; getattr(mc.par, 'comb%dscopeb' % k).val = b_
        getattr(mc.par, 'comb%dscopec' % k).val = c_; getattr(mc.par, 'comb%dresult' % k).val = res
    if delete: mc.par.delattrs = delete
    return mc

COMP = 'POP_pointcloud_dissolve'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Source','menu',[('shape','Input POP (in1; demo shape if unconnected)'),('image','Image (in2 depth/luma)')],0),
 ('Density','int',60,20,220),
 ('Dissolve','float',0.0,0,1,True),
 ('Auto','toggle',True),
 ('Autocycles','int',1,1,4),
 ('Automax','float',0.7,0.1,1.2),
 ('Wavemode','menu',[('plane','Moving Plane'),('sphere','Orbiting Sphere'),('radial','Radial (from axis)')],0),
 ('Axisx','float',0.0,-1,1),('Axisy','float',1.0,-1,1),('Axisz','float',0.25,-1,1),
 ('Edgewidth','float',0.35,0.05,1),
 ('Scatter','float',1.3,0,4),
 ('Jitter','float',0.25,0,1),
 ('Drift','float',0.35,-2,2),
 ('Noisefreq','float',2.2,0.2,5),
 ('Noisecycles','int',1,0,4),
 ('Depth','float',0.9,0,3),
 ('Invertluma','toggle',False),
])
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Demoshape','menu',[('blob','Head-ish blob'),('sphere','Sphere'),('torus','Torus')],0),
 ('Pointsize','float',2.0,0.5,8),
 ('Brightness','float',0.6,0,3),
 ('Edgeglow','float',1.5,0,4),
 ('Glow','float',0.35,0,2),
 ('Camdist','float',6.2,1.5,15),
 ('Camheight','float',0.35,-3,4),
 ('Orbitturns','int',1,0,4),
 ('Fov','float',45,10,90),
], page='Preview')
P = 'parent().par.'
PH = "(absTime.seconds/12.0)"      # internal preview animation (no loop parameters)
ang = "2*math.pi*"+PH

# inputs
inpop = c.create(td.inPOP, 'in1'); inpop.par.connectorder = 1
in1 = c.create(td.inTOP, 'in2'); in1.par.connectorder = 2
CON = '(len(parent().inputConnectors[0].connections)+0*absTime.frame)>0'

# ---- demo COMP: preview-only sources (demo shapes, demo depth image); not selected when inputs are connected
demo = c.create(td.baseCOMP, 'demo')
PP = 'parent(2).par.'
dn = demo.create(td.noiseTOP, 'default_img')
dn.par.outputresolution = 'custom'; dn.par.resolutionw = 512; dn.par.resolutionh = 512
dn.par.period = 0.5; dn.par.harmon = 3; dn.par.amp = 0.5; dn.par.offset = 0.5
dn.par.tz.expr = "0.6*math.cos(2*math.pi*absTime.seconds/12.0)"
dn.par.ty.expr = "0.6*math.sin(2*math.pi*absTime.seconds/12.0)"
dimg = demo.create(td.outTOP, 'out2'); dimg.inputConnectors[0].connect(dn)
sp = demo.create(td.spherePOP, 'src_sphere'); sp.par.type = 'geodesic'; sp.par.surftype = 'triangles'
sp.par.radx = 1; sp.par.rady = 1; sp.par.radz = 1; sp.par.freq.expr = PP+'Density'
tr = demo.create(td.torusPOP, 'src_torus'); tr.par.surftype = 'triangles'
tr.par.radx = 0.9; tr.par.rady = 0.38
tr.par.cols.expr = PP+'Density*3'; tr.par.rows.expr = PP+'Density*1.2'
# head-ish blob: a stretched sphere with lumpy noise along the normals and a nose bump
bl0 = demo.create(td.spherePOP, 'blob_sphere'); bl0.par.type = 'geodesic'; bl0.par.surftype = 'triangles'
bl0.par.radx = 1; bl0.par.rady = 1; bl0.par.radz = 1; bl0.par.freq.expr = PP+'Density'
bl1 = demo.create(td.transformPOP, 'blob_stretch'); bl1.inputConnectors[0].connect(bl0)
bl1.par.sx = 0.85; bl1.par.sy = 1.25
bl1n = demo.create(td.normalPOP, 'blob_normals'); bl1n.inputConnectors[0].connect(bl1)
bl2 = demo.create(td.noisePOP, 'blob_lumps'); bl2.inputConnectors[0].connect(bl1n)
bl2.par.type = 'simplex3d'; bl2.par.harmon = 1; bl2.par.period = 2/2.2; bl2.par.amp0 = 0.1; bl2.par.combineop = 'translatealongnormal'
bl3 = mcomb(demo, 'blob_nose', bl2, [('nosepos', 'float3', [0, 0.05, 0.9]), ('nosefall', 'float', [-14]), ('noseheight', 'float', [0.35])],
            [('asubb', 'P', 'nosepos', '', 'tonose'), ('dot', 'tonose', 'tonose', '', 'd2'),
             ('mult', 'd2', 'nosefall', '', 'arg'), ('exp', 'arg', '', '', 'bump'),
             ('aaddbmultc', 'P.z', 'bump', 'noseheight', 'P.z')], delete='tonose d2 arg bump')
dsw = demo.create(td.switchPOP, 'shape')
dsw.inputConnectors[0].connect(sp); dsw.inputConnectors[1].connect(tr); dsw.inputConnectors[2].connect(bl3)
dsw.par.index.expr = "{'sphere':0,'torus':1,'blob':2}[%sDemoshape.eval()]" % PP
dshape = demo.create(td.outPOP, 'out1'); dshape.inputConnectors[0].connect(dsw)

# depth image for Source = Image: black unless in2 is connected, else the demo image
none = c.create(td.constantTOP, 'img_none'); none.par.outputresolution = 'custom'; none.par.resolutionw = 16; none.par.resolutionh = 16
isw = c.create(td.switchTOP, 'img_switch'); isw.inputConnectors[0].connect(none); isw.inputConnectors[1].connect(in1); isw.inputConnectors[2].connect(demo.outputConnectors[1])
isw.par.index.expr = "0 if parent().par.Source!='image' else (1 if (len(parent().inputConnectors[1].connections)+0*absTime.frame)>0 else 2)"

# ---- sources: demo shape / in1 / image heightfield (grid sampled from the in2 luma), one Switch, then normals and a default lum
gr = c.create(td.gridPOP, 'src_grid'); gr.par.sizex = 2; gr.par.sizey = 2
gr.par.cols.expr = P+'Density*2.5'; gr.par.rows.expr = P+'Density*2.5'
imgl = c.create(td.lookuptexturePOP, 'image_lookup'); imgl.inputConnectors[0].connect(gr)
imgl.par.top = isw; imgl.par.lookupindexattr0 = 'Tex.x'; imgl.par.lookupindexattr1 = 'Tex.y'; imgl.par.outputattrscope = 'imgcol'
# luma -> height: P = (x*1.2, y*1.2, (luma-0.5)*Depth); the luma itself is kept in the attribute lum
imgh = mcomb(c, 'image_heightfield', imgl,
    [('lumaweights', 'float3', [0.299, 0.587, 0.114]), ('invert', 'float', ["1 if %sInvertluma else 0" % P]),
     ('one', 'float', [1]), ('scalexy', 'float', [1.2]), ('depth', 'float', [P+'Depth']), ('half', 'float', [0.5])],
    [('dot', 'imgcol.rgb', 'lumaweights', '', 'luma0'), ('asubb', 'one', 'luma0', '', 'luma1'),
     ('mix', 'luma0', 'luma1', 'invert', 'lum'),
     ('mult', 'P.xy', 'scalexy', '', 'newxy'),
     ('asubb', 'lum', 'half', '', 'lumc'), ('mult', 'lumc', 'depth', '', 'newz'),
     ('copya', 'newxy', '', '', 'P.xy'), ('copya', 'newz', '', '', 'P.z')], delete='luma0 luma1 newxy lumc newz imgcol')
sw = c.create(td.switchPOP, 'src_switch')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(inpop); sw.inputConnectors[2].connect(imgh)
sw.par.index.expr = "2 if %sSource=='image' else (1 if %s else 0)" % (P, CON)
n0 = c.create(td.normalPOP, 'normals_in'); n0.inputConnectors[0].connect(sw)
# lum = 1 for the mesh sources (the image source already has its own lum, which this node leaves alone)
lum1 = c.create(td.attributePOP, 'lum_default'); lum1.inputConnectors[0].connect(n0)
lum1.par.attr0name = 'custom'; lum1.par.attr0customname = 'lum'; lum1.par.attr0numcomps = '1'; lum1.par.attr0value0 = 1
lum1.par.overrideifexists = False; lum1.par.notificationifexists = 'ignore'

# ---- the dissolve, built from native POPs
th = ang
noff = "(math.cos(%s*%sNoisecycles), math.sin(%s*%sNoisecycles), 0.4*math.cos(%s*%sNoisecycles*2))" % ((th, P)*3)
# jitter: noise that shifts the erosion front point by point (vn - 0.5 in the old shader)
jn = c.create(td.noisePOP, 'jitter_noise'); jn.inputConnectors[0].connect(lum1)
jn.par.type = 'simplex3d'; jn.par.harmon = 1; jn.par.period = 2/2.5; jn.par.amp0 = 0.36
jn.par.noisesize = '1'; jn.par.combineop = 'none'; jn.par.noise = True; jn.par.noiseoutputattrscope = 'jn'
for k, ax_ in enumerate('xyz'):
    getattr(jn.par, 't'+ax_).expr = "0.4*" + noff + "[%d]" % k
# scatter: curl noise (a divergence-free swirl) written to the attribute 'cv'
cn = c.create(td.noisePOP, 'curl_noise'); cn.inputConnectors[0].connect(jn)
cn.par.type = 'simplex3d'; cn.par.harmon = 1; cn.par.period.expr = "2.0/%sNoisefreq" % P
cn.par.amp0 = 0.153; cn.par.combineop = 'none'; cn.par.curl3d = True; cn.par.curl3doutputattrscope = 'cv'
for k, ax_ in enumerate('xyz'):
    getattr(cn.par, 't'+ax_).expr = "0.6*" + noff + "[%d]" % k

AXN = "(%sAxisx**2+%sAxisy**2+%sAxisz**2+1e-10)**0.5" % (P, P, P)
ax3 = ["%sAxis%s/%s" % (P, q, AXN) for q in 'xyz']
eff = "(%sAutomax*(0.5-0.5*math.cos(%s*%sAutocycles))**1.6 if %sAuto else %sDissolve)" % (P, ang, P, P, P)
Wd = "max(%sEdgewidth,0.02)" % P
Sc = P + 'Scatter'
Lv = (0.5, 0.8, 0.6); Ln = sum(x*x for x in Lv) ** 0.5
consts = [('zero', 'float', [0]), ('one', 'float', [1]), ('half', 'float', [0.5]),
          ('axis', 'float3', ax3), ('modesphere', 'float', ["1 if %sWavemode=='sphere' else 0" % P]), ('moderadial', 'float', ["1 if %sWavemode=='radial' else 0" % P]),
          ('kplane', 'float', [0.5/1.5]), ('orbit', 'float3', ["0.7*math.cos(%s)" % th, 0.14, "0.7*math.sin(%s)" % th]),
          ('ksphere', 'float', [1/(1.5*1.6)]), ('kradial', 'float', [1/1.5]),
          ('jitter', 'float', [P+'Jitter']),
          ('front', 'float', ["%s*(1+%s+%sJitter)" % (eff, Wd, P)]), ('width', 'float', [Wd]),
          ('kcurl', 'float', ["%s*0.5" % Sc]), ('axdrift', 'float3', ["%s*%sDrift" % (a_, P) for a_ in ax3]),
          ('kout', 'float', ["0.15*" + Sc]), ('krand', 'float', ["0.9*" + Sc]), ('c03', 'float', [0.3]),
          ('lightdir', 'float3', [Lv[0]/Ln, Lv[1]/Ln, Lv[2]/Ln]),
          ('k07', 'float', [0.7]), ('k03', 'float', [0.3]), ('k02', 'float', [0.2]), ('k075', 'float', [0.75]), ('k025', 'float', [0.25]),
          ('isimage', 'float', ["1 if %sSource=='image' else 0" % P]),
          ('four', 'float', [4]), ('edgeglow', 'float', [P+'Edgeglow']), ('bright', 'float', [P+'Brightness']),
          ('fadefrom', 'float', [0.82]), ('psize', 'float', [P+'Pointsize']), ('k08', 'float', [0.8]), ('k06', 'float', [0.6]),
          ('minushalf', 'float', [-0.5]),
          ('hashmul', 'float', [12.9898]), ('hashbig', 'float', [43758.5453])] + \
         [('hashk%d' % k, 'float', [k*78.233]) for k in (1, 2, 3, 5)]
def rnd(k, res):
    """the old shader's per-point hash: fract(sin(pointIndex*12.9898 + k*78.233) * 43758.5453)"""
    return [('amultbaddc', '_PointI', 'hashmul', 'hashk%d' % k, 'hx'), ('sin', 'hx', '', '', 'hs'), ('mult', 'hs', 'hashbig', '', 'hb'), ('fract', 'hb', '', '', res)]
steps = [
  # erosion-front coordinate tw (0..1 across the shape): plane, orbiting sphere or radial; the Wavemode menu selects one by mixing
  ('dot', 'P', 'axis', '', 'along'), ('amultbaddc', 'along', 'kplane', 'half', 'twplane'),
  ('asubb', 'P', 'orbit', '', 'rel'), ('length', 'rel', '', '', 'dist'), ('mult', 'dist', 'ksphere', '', 'twsphere'),
  ('mult', 'axis', 'along', '', 'onaxis'), ('asubb', 'P', 'onaxis', '', 'perp'), ('length', 'perp', '', '', 'dist2'), ('mult', 'dist2', 'kradial', '', 'twradial'),
  ('mix', 'twplane', 'twsphere', 'modesphere', 'tw0'), ('mix', 'tw0', 'twradial', 'moderadial', 'tw'),
  # how far the erosion front has passed each point: e = smoothstep((front - (tw + jitter)) / width), 0 = intact, 1 = gone
  ('mult', 'jn', 'jitter', '', 'jit'), ('add', 'tw', 'jit', '', 'twj'), ('asubb', 'front', 'twj', '', 'ahead'),
  ('adivb', 'ahead', 'width', '', 'xarg'), ('smoothstep', 'zero', 'one', 'xarg', 'e'), ('mult', 'e', 'e', '', 'e2')] + \
  rnd(1, 'rx') + rnd(2, 'ry') + rnd(3, 'rz') + rnd(5, 'rw') + [
  ('copya', 'rx', '', '', 'rv.x'), ('copya', 'ry', '', '', 'rv.y'), ('copya', 'rz', '', '', 'rv.z'),
  # scatter: curl swirl + drift along the axis + outward push + random dust, all growing with e
  ('mult', 'cv', 'kcurl', '', 'sw0'), ('mult', 'sw0', 'e2', '', 'swirl'),
  ('mult', 'axdrift', 'e2', '', 'drift'),
  ('normalize', 'P', '', '', 'pdir'), ('mult', 'pdir', 'e', '', 'p1'), ('mult', 'p1', 'kout', '', 'outward'),
  ('asubb', 'rv', 'half', '', 'r0'), ('add', 'e', 'c03', '', 'e03'), ('mult', 'e', 'e03', '', 'ee'),
  ('mult', 'r0', 'ee', '', 'r1'), ('mult', 'r1', 'krand', '', 'dust'),
  ('add', 'swirl', 'drift', '', 's1'), ('add', 's1', 'outward', '', 's2'), ('add', 's2', 'dust', '', 'disp'),
  # shading: lit mesh grey (or the image luma), brighter on the erosion edge, alpha fades as the point is eroded
  ('dot', 'N', 'lightdir', '', 'ndl'), ('max', 'ndl', 'zero', '', 'lit'), ('abs', 'N.z', '', '', 'az'),
  ('asubb', 'one', 'az', '', 'iaz'), ('mult', 'iaz', 'iaz', '', 'rimk'),
  ('amultbaddc', 'lit', 'k07', 'k03', 'sh0'), ('aaddbmultc', 'sh0', 'rimk', 'k02', 'shapeshade'),
  ('amultbaddc', 'lum', 'k075', 'k025', 'imageshade'), ('mix', 'shapeshade', 'imageshade', 'isimage', 'shade'),
  ('asubb', 'one', 'e', '', 'ie'), ('mult', 'e', 'ie', '', 'e1'), ('mult', 'e1', 'four', '', 'edge'),
  ('amultbaddc', 'edge', 'edgeglow', 'one', 'glow'), ('mult', 'shade', 'glow', '', 'g1'), ('mult', 'g1', 'bright', '', 'col'),
  ('smoothstep', 'fadefrom', 'one', 'e', 'gone'), ('asubb', 'one', 'gone', '', 'alpha'),
  ('amultbaddc', 'rw', 'k08', 'k06', 'sz0'), ('amultbaddc', 'e', 'minushalf', 'one', 'sz1'), ('mult', 'sz0', 'sz1', '', 'sz2'),
  # write the results
  ('add', 'P', 'disp', '', 'P'), ('copya', 'col', '', '', 'Color.rgb'), ('copya', 'alpha', '', '', 'Color.a'),
  ('mult', 'sz2', 'psize', '', 'PointScale')]
tmp = ('along twplane rel dist twsphere onaxis perp dist2 twradial tw0 tw jit twj ahead xarg e e2 hx hs hb rx ry rz rw rv sw0 swirl drift pdir p1 outward '
       'r0 e03 ee r1 dust s1 s2 disp ndl lit az iaz rimk sh0 shapeshade imageshade shade ie e1 edge glow g1 col gone alpha sz0 sz1 sz2 jn cv lum')
g = mcomb(c, 'dissolve', jn if False else cn, consts, steps, delete=tmp)
# the attributes the node creates itself: Color (rgba, written at the end) and rv (random xyz)
g.seq.attr.numBlocks = 2
g.par.attr0name = 'color'; g.par.attr0type = 'color'; g.par.attr0numcomps = '4'
for k in range(4): getattr(g.par, 'attr0defaultval%d' % k).val = 1
g.par.attr1name = 'custom'; g.par.attr1customname = 'rv'; g.par.attr1type = 'float'; g.par.attr1numcomps = '3'
o1 = c.create(td.nullPOP, 'out1'); o1.comment = 'points'; o1.inputConnectors[0].connect(g)

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
pts = c.create(td.convertPOP, 'points_only'); pts.par.convert = 'topointprims'; pts.inputConnectors[0].connect(g)
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = pts
sel.display = True; sel.render = True
mat = c.create(td.pointspriteMAT, 'sprite_mat')
mat.par.pointsize = 1
mat.par.blending = True; mat.par.srcblend = 'sa'; mat.par.destblend = 'one'
mat.par.depthwriting = False
geo.par.material = mat
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
cam.par.tx.expr = "math.sin(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.tz.expr = "math.cos(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov.expr = P+'Fov'; cam.par.lookat = tgt
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr = 0; rt.par.bgcolorg = 0; rt.par.bgcolorb = 0; rt.par.bgcolora = 1; rt.par.format = 'rgba16float'
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(rt); bl.par.size = 12
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1.expr = P+'Glow*2.0'
cm = c.create(td.compositeTOP, 'comp'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(rt); cm.inputConnectors[1].connect(lv)
o = c.create(td.nullTOP, 'preview'); o.comment = 'preview render'; o.inputConnectors[0].connect(cm)
finish(c, name)
report(c)
