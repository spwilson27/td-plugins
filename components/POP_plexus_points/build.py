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

import math
def MC(parent_, name, src, consts, steps, keep=(), drop=()):
    """consts: [(name, type, [values or expressions])]; steps: [(operation, A, B, C, result)]; each step is one Math block."""
    m = parent_.create(td.mathcombinePOP, name)
    m.inputConnectors[0].connect(src)
    m.par.angleunit = 'rad'     # sin/cos in radians
    consts = consts or [('unused', 'float', [0.0])]
    m.seq.vec.numBlocks = len(consts)
    for i, (nm, ty, vals) in enumerate(consts):
        m.par['vec%dname' % i] = nm; m.par['vec%dtype' % i] = ty
        for j, v in enumerate(vals):
            q = m.par['vec%dvalue%d' % (i, j)]
            if isinstance(v, str): q.expr = v
            else: q.val = v
    m.seq.comb.numBlocks = len(steps)
    for i, (o_, a_, b_, c_, r_) in enumerate(steps):
        m.par['comb%doper' % i] = o_
        m.par['comb%dscopea' % i] = a_; m.par['comb%dscopeb' % i] = b_; m.par['comb%dscopec' % i] = c_
        m.par['comb%dresult' % i] = r_
    # tidy: delete this block's scratch attributes (everything it created except P, N and what is listed in keep) plus 'drop'
    temps = [r_ for (_o, _a, _b, _c, r_) in steps if '(' not in r_ and r_ not in ('P', 'N') and r_ not in keep]
    m.par.delattrs = ' '.join(dict.fromkeys(temps + list(drop)))
    return m
def RND(parent_, name, src, attr, comps, kind='uniform', seed=1, offset=0.0, amp=1.0):
    """Random POP: a per-point random attribute (set, not added)"""
    r = parent_.create(td.randomPOP, name); r.inputConnectors[0].connect(src)
    r.par.type = kind; r.par.seed = seed
    r.par.outputattrscope = attr; r.par.overrideautoattr = True; r.par.attrnumcomps = str(comps)
    r.par.combineop = 'set'
    if kind == 'uniform': r.par.amp0 = amp; r.par.offset0 = offset
    return r


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
# head-ish blob = the sphere, squashed, bumped by noise along its normals, with a bump on the face and a jaw hint
bl1 = MC(demo, 'blob_squash', sp, [('squash', 'float3', [0.82, 1.28, 1.0])], [('mult', 'P', 'squash', '', 'P')])
bl2 = demo.create(td.noisePOP, 'blob_bumps'); bl2.inputConnectors[0].connect(bl1)
bl2.par.type = 'simplex3d'; bl2.par.period = 1 / 2.2; bl2.par.harmon = 0; bl2.par.amp0 = 0.13
bl2.par.combineop = 'translatealongnormal'; bl2.par.combineentity = 'noise'
bl3 = MC(demo, 'blob_face', bl2,
  [('nose', 'float3', [0.0, 0.05, 0.9]), ('zhat', 'float3', [0.0, 0.0, 1.0]), ('k14', 'float', [-14.0]), ('k034', 'float', [0.34]),
   ('e0', 'float', [-0.2]), ('e1', 'float', [-1.0]), ('one', 'float', [1.0]), ('jaw', 'float', [-0.12])],
  [('asubb', 'P', 'nose', '', 'Q'), ('dot', 'Q', 'Q', '', 'Q2'), ('mult', 'Q2', 'k14', '', 'E'), ('exp', 'E', '', '', 'Ex'),
   ('mult', 'Ex', 'k034', '', 'Bump'), ('amultbaddc', 'zhat', 'Bump', 'P', 'P'),          # bump towards the viewer
   ('smoothstep', 'e0', 'e1', 'P(1)', 'Jy'), ('abs', 'P(0)', '', '', 'Ax'), ('asubb', 'one', 'Ax', '', 'Side'),
   ('mult', 'Jy', 'Side', '', 'J0'), ('amultbaddc', 'J0', 'jaw', 'P(1)', 'P(1)'),         # jaw hint
   ('normalize', 'P', '', '', 'N')])

dsw = demo.create(td.switchPOP, 'shape'); dsw.inputConnectors[0].connect(bl3); dsw.inputConnectors[1].connect(sp); dsw.inputConnectors[2].connect(tr)
dsw.par.index.expr = "{'blob':0,'sphere':1,'torus':2}[%sDemoshape.eval()]" % PP
dshape = demo.create(td.outPOP, 'out1'); dshape.inputConnectors[0].connect(dsw)

# image source for Source = Image: black unless in2 connected, else the demo image
none = c.create(td.constantTOP, 'img_none'); none.par.outputresolution = 'custom'; none.par.resolutionw = 16; none.par.resolutionh = 16
isw = c.create(td.switchTOP, 'img_switch'); isw.inputConnectors[0].connect(none); isw.inputConnectors[1].connect(intop); isw.inputConnectors[2].connect(demo.outputConnectors[1])
isw.par.index.expr = "0 if parent().par.Source!='image' else (1 if (len(parent().inputConnectors[1].connections)+0*absTime.frame) else 2)"

# sources
gr = c.create(td.gridPOP, 'src_grid'); gr.par.surftype = 'triangles'; gr.par.sizex = 2; gr.par.sizey = 2
gr.par.cols.expr = "int(math.sqrt(%sPoints*5))" % P; gr.par.rows.expr = "int(math.sqrt(%sPoints*5))" % P
camx = "math.sin(%s*%sOrbitturns)*%sOrbitrange" % (ang, P, P)
camz = "math.cos(%s*%sOrbitturns)*%sOrbitrange" % (ang, P, P)
# ---- Math Combine POP helper: one POP, a list of named constants and a list of steps ----
# ---- scalars that change once per frame are plain expressions (no per-point work) ----
TH = ang                                          # scan angle (radians), 1 turn per 16 s
STEPI = "int((((%s)/(2*math.pi))%%1.0)*%sBandsteps)" % (TH, P)    # which glitch step we are in
CAMU = "(%s)/math.sqrt((%s)**2+0.12**2+(%s)**2)" 
camxu = CAMU % (camx, camx, camz); camzu = CAMU % (camz, camx, camz); camyu = "0.12/math.sqrt((%s)**2+0.12**2+(%s)**2)" % (camx, camz)

# random-looking table: x = band / line number, y = glitch step (one random pair per cell) -> "strata offsets"
rtex = c.create(td.noiseTOP, 'random_table'); rtex.par.type = 'random'; rtex.par.mono = False
rtex.par.outputresolution = 'custom'; rtex.par.resolutionw = 128; rtex.par.resolutionh = 64; rtex.par.format = 'rgba32float'
rtex.par.amp = 0.5; rtex.par.offset = 0.5; rtex.par.seed = 7

# in1 -> normals from the points (as a point cloud has no surface): N = normalize(P)
in_n = MC(c, 'input_normals', inpop, [], [('normalize', 'P', '', '', 'N')])
pts = c.create(td.switchPOP, 'points_src')
pts.inputConnectors[0].connect(demo.outputConnectors[0]); pts.inputConnectors[1].connect(in_n)
pts.par.index.expr = "(1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0)"
# points: scaled by Scale (and a default luma so every path carries 'Lum')

pts_s = MC(c, 'scale', pts, [('scale', 'float', [P + 'Scale']), ('lum0', 'float', [0.7])],
           [('mult', 'P', 'scale', '', 'P'), ('copya', 'lum0', '', '', 'Lum')], keep=('Lum',))

# image: a grid whose points are lifted by the picture's brightness; N = +Z; Lum is the brightness
gtm = c.create(td.texturemapPOP, 'image_uv'); gtm.inputConnectors[0].connect(gr)
gtm.par.texmethod = 'xyznorm'; gtm.par.axis = 'z'
imgl = c.create(td.reorderTOP, 'image_luma'); imgl.inputConnectors[0].connect(isw)
for sl in ('red', 'green', 'blue', 'alpha'):
    imgl.par['output' + sl] = 'input1'; imgl.par['output' + sl + 'chan'] = 'luminance'
imgl.par.format = 'rgba16float'
gl_ = c.create(td.lookuptexturePOP, 'image_brightness'); gl_.inputConnectors[0].connect(gtm)
gl_.par.top = imgl; gl_.par.lookupindexattr0 = 'Tex(0)'; gl_.par.lookupindexattr1 = 'Tex(1)'
gl_.par.outputattrscope = 'Lum'; gl_.par.overrideautoattr = True; gl_.par.attrnumcomps = 1; gl_.par.channelmask = 1
gl_.par.inputextend0 = 'hold'; gl_.par.inputextend1 = 'hold'
img_s = MC(c, 'image_shape', gl_,
  [('flat', 'float3', [1.25, 1.25, 0.0]), ('zhat', 'float3', [0.0, 0.0, 1.0]), ('half', 'float', [0.5]), ('depth', 'float', [P + 'Imgdepth'])],
  [('mult', 'P', 'flat', '', 'P'),               # x,y stretched 1.25, z cleared
   ('asubb', 'Lum', 'half', '', 'LumC'),         # brightness - 0.5
   ('mult', 'LumC', 'depth', '', 'Zoff'),        # ... * Imgdepth
   ('amultbaddc', 'zhat', 'Zoff', 'P', 'P'),     # z = (brightness - 0.5) * depth
   ('copya', 'zhat', '', '', 'N')], keep=('Lum',))   # normals point at the viewer
img_s.par.delattrs += ' Tex'

shp = c.create(td.switchPOP, 'shape_switch')
shp.inputConnectors[0].connect(pts_s); shp.inputConnectors[1].connect(img_s)
shp.par.index.expr = "1 if parent().par.Source=='image' else 0"

# strata: snap y into horizontal slices; some slices slide sideways (random per slice and per glitch step)
st1 = MC(c, 'strata_slices', shp,
  [('bands', 'float', ["max(%sBands,1)" % P]), ('half', 'float', [0.5]), ('stepi', 'float', [STEPI])],
  [('mult', 'P(1)', 'bands', '', 'Yb'),          # y * bands
   ('floor', 'Yb', '', '', 'Band'),              # slice number
   ('add', 'Band', 'half', '', 'Bm'),            # slice centre (in slices)
   ('adivb', 'Bm', 'bands', '', 'Ysnap'),        # ... back to world y
   ('copya', 'stepi', '', '', 'StepI')], keep=('Ysnap', 'StepI', 'Band'))         # glitch step (same for all points)

st2 = c.create(td.lookuptexturePOP, 'strata_random'); st2.inputConnectors[0].connect(st1)
st2.par.top = rtex; st2.par.lookupindexattr0 = 'Band'; st2.par.lookupindexattr1 = 'StepI'
st2.par.indexunit0 = 'pixelindex'; st2.par.indexunit1 = 'pixelindex'
st2.par.inputextend0 = 'repeat'; st2.par.inputextend1 = 'repeat'; st2.par.interpolate = False
st2.par.outputattrscope = 'BandRnd'; st2.par.overrideautoattr = True; st2.par.attrnumcomps = 2; st2.par.channelmask = 3
st3 = MC(c, 'strata_shift', st2,
  [('thr', 'float', [0.7]), ('half', 'float', [0.5]), ('two_shift', 'float', [2 * 1.0]), ('shift', 'float', [P + 'Bandshift']),
   ('banding', 'float', [P + 'Banding'])],
  [('gt', 'BandRnd(1)', 'thr', '', 'Slide'),             # only some slices slide
   ('asubb', 'BandRnd(0)', 'half', '', 'Dir'),           # random direction/size -0.5..0.5
   ('mult', 'Dir', 'Slide', '', 'Dir2'),
   ('mult', 'Dir2', 'shift', '', 'Dir3'),
   ('mult', 'Dir3', 'two_shift', '', 'Dx'),              # * 2 * Bandshift
   ('mult', 'Dx', 'banding', '', 'DxB'),
   ('add', 'P(0)', 'DxB', '', 'P(0)'),                   # x slides
   ('mix', 'P(1)', 'Ysnap', 'banding', 'P(1)')])         # y snaps to the slice centre by Banding

# jitter: tiny per-point wobble, each point on its own phase
st3.par.delattrs += ' Ysnap StepI BandRnd Band'

rj3 = RND(c, 'jitter_dir', st3, 'Jr', 3, seed=11, offset=-0.5)
rjp = RND(c, 'jitter_phase', rj3, 'Jph', 1, seed=12)
jt = MC(c, 'jitter', rjp,
  [('th', 'float', [TH]), ('tau', 'float', [6.2831853]), ('half', 'float', [0.5]), ('jit', 'float', [P + 'Jitter'])],
  [('amultbaddc', 'Jph', 'tau', 'th', 'Ph'),           # phase = th + random * 2 pi
   ('sin', 'Ph', '', '', 'Sn'),
   ('amultbaddc', 'Sn', 'half', 'half', 'Env'),        # 0.5 + 0.5 sin
   ('mult', 'Env', 'jit', '', 'Amp'),
   ('amultbaddc', 'Jr', 'Amp', 'P', 'P')])             # P += random * Amp

jt.par.delattrs += ' Jr Jph'

# sweeping scan plane + shading (brightness, point size) + which points to keep
r6 = RND(c, 'shade_random', jt, 'Hshade', 1, seed=13)
r7 = RND(c, 'size_random', r6, 'Hsize', 1, seed=14)
r9 = RND(c, 'keep_random', r7, 'Hkeep', 1, seed=15)
SWY = "(-1.5 + 3.0*((((%s)/(2*math.pi))*%sSweepcycles)%%1.0))" % (TH, P)
shd = MC(c, 'sweep_and_shade', r9,
  [('sy', 'float', [SWY]), ('five', 'float', [5.0]), ('mone', 'float', [-1.0]), ('swamt', 'float', [P + 'Sweep']),
   ('cam', 'float3', [camxu, camyu, camzu]), ('half', 'float', [0.5]), ('lo12', 'float', [-1.2]), ('hi12', 'float', [1.2]),
   ('c035', 'float', [0.35]), ('one', 'float', [1.0]), ('k065', 'float', [0.65]), ('k04', 'float', [0.4]), ('k06', 'float', [0.6]),
   ('bright', 'float', [P + 'Brightness']), ('three', 'float', [3.0]), ('psize', 'float', [P + 'Pointsize']), ('k07', 'float', [0.7]),
   ('k12', 'float', [1.2]), ('thr', 'float', [P + 'Threshold']), ('samples', 'float', [P + 'Imgsamples']), ('two', 'float', [2.0]),
   ('isimage', 'float', ["1 if parent().par.Source=='image' else 0"]),
   ('black4', 'float4', [0, 0, 0, 1]), ('white4', 'float4', [1, 1, 1, 1])],
  [('asubb', 'P(1)', 'sy', '', 'Dy'),                     # distance to the sweep plane
   ('mult', 'Dy', 'five', '', 'D5'), ('square', 'D5', '', '', 'D5s'), ('mult', 'D5s', 'mone', '', 'Neg'), ('exp', 'Neg', '', '', 'Gauss'),
   ('mult', 'Gauss', 'swamt', '', 'Sweep'),               # bright band that sweeps up the cloud
   ('dot', 'N', 'cam', '', 'Fd'), ('amultbaddc', 'Fd', 'half', 'half', 'Facing'),          # facing the camera
   ('dot', 'P', 'cam', '', 'Dd'), ('smoothstep', 'lo12', 'hi12', 'Dd', 'Ds'), ('mix', 'c035', 'one', 'Ds', 'Depthc'),   # depth cue
   ('amultbaddc', 'Facing', 'k065', 'c035', 'S0'), ('mult', 'S0', 'Depthc', '', 'S1'),
   ('amultbaddc', 'Hshade', 'k04', 'k06', 'V6'), ('mult', 'S1', 'V6', '', 'S2'),         # random 0.6..1
   ('mult', 'S2', 'bright', '', 'S3'), ('amultbaddc', 'Sweep', 'three', 'one', 'Sw3'), ('mult', 'S3', 'Sw3', '', 'Bv'),
   ('mix', 'black4', 'white4', 'Bv', 'Color'),             # grey level Bv, alpha 1
   ('amultbaddc', 'Hsize', 'k06', 'k07', 'V7'), ('mult', 'V7', 'psize', '', 'V7p'),
   ('amultbaddc', 'Sweep', 'k12', 'one', 'Sw12'), ('mult', 'V7p', 'Sw12', '', 'PointScale'),
   ('smoothstep', 'thr', 'one', 'Lum', 'Kp0'), ('mult', 'Kp0', 'samples', '', 'Kp1'),     # image: keep probability
   ('mix', 'two', 'Kp1', 'isimage', 'Kp'),                 # other sources keep everything
   ('lt', 'Hkeep', 'Kp', '', 'Keep')], keep=('Color', 'PointScale', 'Keep'))
shd.par.delattrs += ' Hshade Hsize Hkeep Lum'

dl = c.create(td.deletePOP, 'drop'); dl.inputConnectors[0].connect(shd)
dl.par.entity = 'point'; dl.par.attr0inattr = 'Keep'; dl.par.attr0func = 'lt'; dl.par.attr0value = 0.5; dl.par.invert = 'delete'
cloud = c.create(td.nullPOP, 'out1'); cloud.comment = 'point cloud'; cloud.inputConnectors[0].connect(dl)
dots = c.create(td.convertPOP, 'dots'); dots.par.convert = 'topointprims'; dots.inputConnectors[0].connect(cloud)
px = c.create(td.proximityPOP, 'plexus'); px.inputConnectors[0].connect(cloud)
px.par.maxdist.expr = P+'Linkdistance'; px.par.maxlinesperpoint.expr = P+'Maxlinks'; px.par.output = 'lines'
px.par.maxtempneighbors = 16
out2 = c.create(td.nullPOP, 'out2'); out2.comment = 'plexus lines'; out2.inputConnectors[0].connect(px)

# long lines: seed points -> random directions -> two rotating end points -> copied onto a 2-point line
seeds = c.create(td.pointgeneratorPOP, 'seeds'); seeds.par.shape = 'sphere'; seeds.par.distribution = 'volume'
seeds.par.numpoints.expr = "max(1,%sLonglines)" % P
for a in 'xyz': getattr(seeds.par, 'radius'+a).val = 1.0
d0 = RND(c, 'dir_start', seeds, 'D0', 3, kind='direction', seed=21)
d1 = RND(c, 'dir_end', d0, 'D1', 3, kind='direction', seed=22)
l1 = RND(c, 'line_h1', d1, 'Lh1', 1, seed=23); l2 = RND(c, 'line_h2', l1, 'Lh2', 1, seed=24)
l3 = RND(c, 'line_h3', l2, 'Lh3', 1, seed=25); l4 = RND(c, 'line_id', l3, 'Lr', 1, seed=26)
ls = MC(c, 'line_setup', l4,
  [('spread', 'float', [P + 'Longspread']), ('th', 'float', [TH]), ('half', 'float', [0.5]), ('one', 'float', [1.0]), ('two', 'float', [2.0]),
   ('mone', 'float', [-1.0]), ('deg', 'float', [180.0 / 3.14159265])],
  [('gt', 'Lh1', 'half', '', 'Pos'), ('mix', 'mone', 'one', 'Pos', 'Sgn'),                 # +1 or -1
   ('mult', 'Lh2', 'two', '', 'H2'), ('floor', 'H2', '', '', 'F2'), ('add', 'F2', 'one', '', 'Mag'),   # 1 or 2 turns
   ('mult', 'Sgn', 'Mag', '', 'K1'),
   ('mult', 'K1', 'th', '', 'AngR'), ('mult', 'AngR', 'deg', '', 'AngD'),                   # angle in degrees
   ('mult', 'AngD', 'mone', '', 'AngDneg'), ('mult', 'AngD', 'half', '', 'AngDh'),
   ('mult', 'D0', 'spread', '', 'A'), ('mult', 'D1', 'spread', '', 'B')],
  keep=('A', 'B', 'AngD', 'AngDneg', 'AngDh'))
ls.par.delattrs += ' D0 D1 Lh1 Lh2'

ta = c.create(td.transformPOP, 'rotate_start'); ta.inputConnectors[0].connect(ls)
ta.par.mode = 'transformattrscopepos'; ta.par.inputattrscope = 'A'; ta.par.outputattrscope = 'A'
ta.seq.map.numBlocks = 1; ta.par.map0element = 'AngD'; ta.par.map0parm = 'ry'; ta.par.map0combineop = 'set'
tb = c.create(td.transformPOP, 'rotate_end'); tb.inputConnectors[0].connect(ta)
tb.par.mode = 'transformattrscopepos'; tb.par.inputattrscope = 'B'; tb.par.outputattrscope = 'B'
tb.par.rord = 'yxz'
tb.seq.map.numBlocks = 2
tb.par.map0element = 'AngDneg'; tb.par.map0parm = 'ry'; tb.par.map0combineop = 'set'
tb.par.map1element = 'AngDh'; tb.par.map1parm = 'rx'; tb.par.map1combineop = 'set'
lp = MC(c, 'line_pulse', tb,
  [('thc', 'float', ["(%s)*%sSweepcycles" % (TH, P)]), ('tau', 'float', [6.2831853]), ('half', 'float', [0.5]),
   ('stepv', 'float', ["(%s + 0.5)/64.0" % STEPI]), ('thr', 'float', [0.35]), ('opac', 'float', [P + 'Longopacity'])],
  [('amultbaddc', 'Lh3', 'tau', 'thc', 'Pp'), ('sin', 'Pp', '', '', 'Ps'), ('amultbaddc', 'Ps', 'half', 'half', 'Pb'),
   ('square', 'Pb', '', '', 'Pq'), ('square', 'Pq', '', '', 'Pulse'),                   # (0.5+0.5 sin)^4: bursts
   ('copya', 'stepv', '', '', 'StepV')], keep=('Pulse', 'StepV'))
lp.par.delattrs += ' AngD AngDneg AngDh'

lv = c.create(td.lookuptexturePOP, 'line_visible'); lv.inputConnectors[0].connect(lp)
lv.par.top = rtex; lv.par.lookupindexattr0 = 'Lr'; lv.par.lookupindexattr1 = 'StepV'
lv.par.inputextend0 = 'repeat'; lv.par.inputextend1 = 'repeat'; lv.par.interpolate = False
lv.par.outputattrscope = 'LineRnd'; lv.par.overrideautoattr = True; lv.par.attrnumcomps = 1; lv.par.channelmask = 1
lb = MC(c, 'line_brightness', lv,
  [('thr', 'float', [0.35]), ('opac', 'float', [P + 'Longopacity'])],
  [('gt', 'LineRnd', 'thr', '', 'Vis'), ('mult', 'Pulse', 'Vis', '', 'Pv'), ('mult', 'Pv', 'opac', '', 'Br')], keep=('Br',))
lb.par.delattrs += ' LineRnd Pulse StepV Lr Lh3'

ln = c.create(td.gridPOP, 'line_tmpl'); ln.par.surftype = 'lines'; ln.par.cols = 2; ln.par.rows = 1; ln.par.sizex = 1; ln.par.sizey = 0
cp = c.create(td.copyPOP, 'copy_lines'); cp.inputConnectors[0].connect(ln); cp.inputConnectors[1].connect(lb)
cp.par.dotemplatetranslate = False; cp.par.doattr = True; cp.par.templateattr0names = 'A B Br'
lg = MC(c, 'longlines', cp,
  [('half', 'float', [0.5]), ('black4', 'float4', [0, 0, 0, 1]), ('white4', 'float4', [1, 1, 1, 1])],
  [('add', 'P(0)', 'half', '', 'E'),                      # 0 at one end of the template line, 1 at the other
   ('mix', 'A', 'B', 'E', 'P'),                           # slide between the two rotating end points
   ('mix', 'black4', 'white4', 'Br', 'Color')], keep=('Color',))
lg.par.delattrs += ' A B Br'

out3 = c.create(td.nullPOP, 'out3'); out3.comment = 'long lines'; out3.inputConnectors[0].connect(lg)

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
# cross-mark lattice (preview only): one tile (a cross and faint lines through its centre) is drawn large, then a Transform TOP
# squeezes it to the cell size (Gridsize * height) and repeats it over the frame.
CELL = "(%sGridsize*%sResolutionh)" % (P, P)
def prect(name, w, h, val, src=None):
    r = c.create(td.rectangleTOP, name); setres(r)
    r.par.format = 'rgba16float'; r.par.sizeunit = 'pixels'; r.par.centerunit = 'pixels'
    r.par.sizex.expr = w; r.par.sizey.expr = h; r.par.centerx = 0; r.par.centery = 0
    for k in 'rgb':
        r.par['fillcolor' + k].expr = val; r.par['bgcolor' + k] = 0
    r.par.fillalpha = 1; r.par.bgalpha = 1; r.par.antialias = 'on'
    if src is not None: r.inputConnectors[0].connect(src)
    return r
W_, H_ = "%sResolutionw" % P, "%sResolutionh" % P
TH_ = "2.0"
# faint lines through the tile centre (full tile wide / high, 0.7 px thick in the final image)
ln_h = prect('tile_line_h', W_, "0.7*%s/%s" % (H_, CELL), "0.6*0.12*%sGrid" % P)
ln_v = prect('tile_line_v', "0.7*%s/%s" % (W_, CELL), H_, "0.6*0.12*%sGrid" % P)
# the cross itself: arms 0.18 cell long, 1.4 px thick
cr_h = prect('tile_cross_h', "0.18*%s" % W_, "%s*%s/%s" % (TH_, H_, CELL), "0.6*%sGrid" % P)
cr_v = prect('tile_cross_v', "%s*%s/%s" % (TH_, W_, CELL), "0.18*%s" % H_, "0.6*%sGrid" % P)
tile = c.create(td.compositeTOP, 'tile'); tile.par.operand = 'add'
setres(tile); tile.par.format = 'rgba16float'
for t_ in (ln_h, ln_v, cr_h, cr_v): t_.outputConnectors[0].connect(tile)
gridt = c.create(td.transformTOP, 'grid'); gridt.inputConnectors[0].connect(tile)
setres(gridt); gridt.par.format = 'rgba16float'; gridt.par.extend = 'repeat'; gridt.par.tunit = 'pixels'
gridt.par.sx.expr = "%s/%s" % (CELL, W_); gridt.par.sy.expr = "%s/%s" % (CELL, H_)
gridt.par.tx.expr = "-%s/2" % W_; gridt.par.ty.expr = "-%s/2" % H_
cm0 = c.create(td.compositeTOP, 'comp_grid'); cm0.par.operand = 'add'
cm0.inputConnectors[0].connect(rt); cm0.inputConnectors[1].connect(gridt)
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(cm0); bl.par.size = 8
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1.expr = P+'Glow*2.0'
cm = c.create(td.compositeTOP, 'comp'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(cm0); cm.inputConnectors[1].connect(lv)
o = c.create(td.nullTOP, 'preview'); o.comment = 'preview render'; o.inputConnectors[0].connect(cm)
finish(c, name)
report(c)
