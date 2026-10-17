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
    sw.par.index.expr = "(1 if parent().inputConnectors[0].connections else 0) + 0*absTime.frame"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish(c, name):
    c.layout()
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

COMP = 'POP_tentacles'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Length','float',2.2,0.3,8),
 ('Grow','float',1.0,0,1),
 ('Autogrow','toggle',False),
 ('Speed','float',0.5,0,4),
 ('Seed','float',0.0,0,100),
 ('Segments','int',64,8,200),
 ('Sides','int',12,4,32),
 ('Thickness','float',0.075,0.005,0.4),
 ('Taper','float',0.8,0.1,3),
 ('Tipmin','float',0.04,0,0.5),
 ('Wiggle','float',0.35,0,1.5),
 ('Noisefreq','float',1.3,0.2,5),
 ('Wave','float',0.07,0,0.5),
 ('Wavefreq','float',2.0,0.5,8),
 ('Pulse','float',0.18,0,0.8),
 ('Pulsefreq','float',6.0,1,20),
])
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Metallic','float',1.0,0,1),
 ('Roughness','float',0.22,0.02,1),
 ('Basecolor','rgb',(0.82,0.82,0.85)),
 ('Envintensity','float',1.0,0,4),
 ('Redaccent','float',0.7,0,1),
 ('Camdist','float',9.5,2,30),
 ('Camheight','float',1.2,-8,10),
 ('Bgcolor','rgb',(0.006,0.006,0.008)),
], page='Look')
P = 'parent().par.'

# ---- inputs: in1 POP (points), in2 modulation CHOP ----
inp = c.create(td.inPOP, 'in1')
inm = c.create(td.inCHOP, 'in2'); inm.par.connectorder = 1
# demo (preview only): points on a sphere, gated off whenever in1 is connected
demo = c.create(td.baseCOMP, 'demo')
dsp = demo.create(td.spherePOP, 'points'); dsp.par.type = 'geodesic'; dsp.par.freq = 3
dout = demo.create(td.outPOP, 'out1'); dout.inputConnectors[0].connect(dsp)
sw = c.create(td.switchPOP, 'src')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(inp)
sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

# ---- modulation: band1..4, beat (default 0 when absent) ----
base = c.create(td.constantCHOP, 'modbase')
for i, n in enumerate(('band1','band2','band3','band4','beat')):
    getattr(base.par, 'name%d'%i).val = n; getattr(base.par, 'value%d'%i).val = 0
mod = c.create(td.mergeCHOP, 'mod'); mod.par.duplicate = 'first'
mod.inputConnectors[0].connect(inm); mod.inputConnectors[0].connect(inm)
mod.inputConnectors[1].connect(base)
def M(n): return "op('mod')['%s']" % n

# ---- geometry ----
tube = c.create(td.tubePOP, 'tube'); tube.par.orient = 'y'; tube.par.height = 1.0
tube.par.radx = 0.5; tube.par.rady = 0.5; tube.par.endcaps = False
tube.par.cols.expr = P+'Sides'; tube.par.rows.expr = P+'Segments'
# every input point is the root of one tentacle: its position travels along as the attribute Root
rg = mcomb(c, 'rootattr', sw, [('zero', 'float', [0])], [('copya', 'P', '', '', 'Root')])
# the spine of every tentacle: a straight line of Segments points (y = -0.5..0.5), one copy per root
spl = c.create(td.linePOP, 'spine_line'); spl.cook(force=True)
spl.par.pt0posx = 0; spl.par.pt0posy = -0.5; spl.par.pt0posz = 0; spl.par.pt1posx = 0; spl.par.pt1posy = 0.5; spl.par.pt1posz = 0
spl.par.divs.expr = P+'Segments-1'
cp = c.create(td.copyPOP, 'spine_copies')
cp.inputConnectors[0].connect(spl); cp.inputConnectors[1].connect(rg)
cp.par.dotemplatetranslate = False
cp.par.doattr = True; cp.par.templateattr0names = 'Root'
# the tube mesh: one copy of the straight tube per root; templateid numbers the tentacles (attribute tid)
cp2 = c.create(td.copyPOP, 'tube_copies')
cp2.inputConnectors[0].connect(tube); cp2.inputConnectors[1].connect(rg)
cp2.par.dotemplatetranslate = False
cp2.par.templateid = 'point'; cp2.par.templateidname = 'tid'

th = "absTime.seconds*%sSpeed" % P
grow = "((0.5-0.5*math.cos(%s))**0.7 if %sAutogrow else %sGrow)" % (th, P, P)
Lg = "(%sLength*(1+0.3*%s))*%s" % (P, M('band4'), grow)          # grown length of a tentacle
off = "0.8*(math.cos(%s), math.sin(%s), 0.5*math.cos(2*%s))" % (th, th, th)

# 1. per-point set-up: u = 0..1 along the tentacle (plus u a little before and after it, to find the direction of the spine),
#    growth direction, a ring frame (p1, p2) and a coordinate for the seed noise
m1 = mcomb(c, 'tentacle_setup', cp,
  [('zero', 'float', [0]), ('one', 'float', [1]), ('half', 'float', [0.5]), ('eps', 'float', [1e-5]), ('step', 'float', [0.01]),
   ('xaxis', 'float3', [1, 0, 0]), ('yaxis', 'float3', [0, 1, 0]), ('k09', 'float', [0.9]),
   ('seedscale', 'float', [7.7]), ('seedshift', 'float', ["3.1+%sSeed*1.37" % P])],
  [('add', 'P.y', 'half', '', 'u0'), ('clamp', 'u0', 'zero', 'one', 'u'),
   ('asubb', 'u', 'step', '', 'ua0'), ('clamp', 'ua0', 'zero', 'one', 'ua'),
   ('add', 'u', 'step', '', 'ub0'), ('clamp', 'ub0', 'zero', 'one', 'ub'),
   ('add', 'Root', 'eps', '', 'rootE'), ('normalize', 'rootE', '', '', 'dir'),
   ('abs', 'dir.y', '', '', 'dy'), ('lt', 'dy', 'k09', '', 'useY'),          # reference axis for the frame: Y unless the tentacle points along Y
   ('mix', 'xaxis', 'yaxis', 'useY', 'ref'),
   ('cross', 'dir', 'ref', '', 'p1raw'), ('normalize', 'p1raw', '', '', 'p1'), ('cross', 'dir', 'p1', '', 'p2'),
   ('amultbaddc', 'Root', 'seedscale', 'seedshift', 'sq')], delete='u0 ua0 ub0 rootE dy useY ref p1raw')
# 2. seed: one random-ish number (0..1) per tentacle, from noise looked up at the root position
ns = c.create(td.noisePOP, 'seed_noise'); ns.inputConnectors[0].connect(m1)
ns.par.type = 'simplex3d'; ns.par.harmon = 1; ns.par.period = 1; ns.par.amp0 = 0.5; ns.par.offset0 = 0.5
ns.par.noiselookupattr = 'sq'; ns.par.combineop = 'none'
ns.par.noise = True; ns.par.noiseoutputattrscope = 'seed'; ns.par.noisesize = '1'
# 3. where to sample the writhing noise: along the tentacle (at ua and ub) and travelling through noise space over time
m2 = mcomb(c, 'writhe_coords', ns,
  [('k23', 'float', [2.3]), ('yaxis', 'float3', [0, 1, 0]), ('noisefreq', 'float', [P+'Noisefreq']),
   ('travel', 'float3', [off + "[0]", off + "[1]", off + "[2]"]), ('three', 'float', [3])],
  [('mult', 'dir', 'k23', '', 'qa0'), ('mult', 'seed', 'three', '', 'seed3'), ('add', 'qa0', 'travel', '', 'qa1'), ('add', 'qa1', 'seed3', '', 'qbase'),
   ('mult', 'ua', 'noisefreq', '', 'ufa'), ('mult', 'yaxis', 'ufa', '', 'qya'), ('add', 'qbase', 'qya', '', 'qa'),
   ('mult', 'ub', 'noisefreq', '', 'ufb'), ('mult', 'yaxis', 'ufb', '', 'qyb'), ('add', 'qbase', 'qyb', '', 'qb')],
  delete='qa0 seed3 qa1 qbase ufa qya ufb qyb')
# 4. the writhing itself: 3D vector noise looked up at qa and qb
nwa = c.create(td.noisePOP, 'writhe_noise_a'); nwa.inputConnectors[0].connect(m2)
nwb = c.create(td.noisePOP, 'writhe_noise_b'); nwb.inputConnectors[0].connect(nwa)
for nw_, q_, o_ in ((nwa, 'qa', 'writhea'), (nwb, 'qb', 'writheb')):
    nw_.par.type = 'simplex3d'; nw_.par.harmon = 1; nw_.par.period = 2; nw_.par.amp0 = 0.36
    nw_.par.noiselookupattr = q_; nw_.par.combineop = 'none'
    nw_.par.noise = True; nw_.par.noiseoutputattrscope = o_; nw_.par.noisesize = '3'
# 5. build the tentacle: spine = root + direction*length*u + writhing + sideways sway, evaluated just before (a) and just after (b)
#    each point; the tube ring sits at their midpoint, in the plane perpendicular to the difference (the spine direction)
consts = [('zero', 'float', [0]), ('one', 'float', [1]), ('c04', 'float', [0.4]), ('c06', 'float', [0.6]), ('tau', 'float', [2*3.14159265]),
          ('length', 'float', [Lg]),
          ('wigglek', 'float', ["2*%sWiggle*(1+%s)*(%s)" % (P, M('band1'), Lg)]),
          ('half', 'float', [0.5]), ('wavek', 'float', ["%sWave*(1+2*%s)*(%s)" % (P, M('band2'), Lg)]),
          ('wavefreq', 'float', [P+'Wavefreq']), ('wavetime', 'float', [th]), ('seedphase', 'float', [6.28]), ('c13', 'float', [1.3]), ('c2', 'float', [2]),
          ('thick', 'float', ["%sThickness*(1+0.5*%s)" % (P, M('beat'))]), ('taper', 'float', [P+'Taper']),
          ('tipmin', 'float', ["%sTipmin*%sThickness*(1+0.5*%s)" % (P, P, M('beat'))]),
          ('pulseamt', 'float', ["%sPulse+0.3*%s" % (P, M('band3'))]), ('pulsefreq', 'float', ["math.pi*%sPulsefreq" % P]), ('seedpulse', 'float', [6.0]),
          ('c03', 'float', [0.3]), ('c001', 'float', [0.01]), ('c2r', 'float', [2]), ('growamt', 'float', [grow]), ('eps', 'float', [1e-6])]
def spine(x):
    """steps that put the spine point for u = u<x> (x = 'a' or 'b') into the attribute spine<x>"""
    u, w = 'u' + x, 'writhe' + x
    S = lambda n: n + x
    return [
      # smooth start of the writhing (none at the root), growing towards the tip
      ('smoothstep', 'zero', 'half', u, S('ramp')), ('amultbaddc', u, 'c06', 'c04', S('grow')), ('mult', S('ramp'), S('grow'), '', S('envl')),
      ('mult', w, 'wigglek', '', S('w1')), ('mult', S('w1'), S('envl'), '', S('writheoff')),
      # travelling sideways sway in the two ring-plane directions
      ('mult', 'wavefreq', u, '', S('wf1')), ('mult', S('wf1'), 'tau', '', S('wph0')), ('asubb', S('wph0'), 'wavetime', '', S('wph1')),
      ('amultbaddc', 'seed', 'seedphase', S('wph1'), S('wph')),
      ('sin', S('wph'), '', '', S('sn')), ('amultbaddc', u, 'c2', 'c13', S('ph2a')), ('add', S('wph'), S('ph2a'), '', S('ph2')), ('cos', S('ph2'), '', '', S('cs')),
      ('mult', 'p1', S('sn'), '', S('sw1')), ('mult', 'p2', S('cs'), '', S('sw2')), ('add', S('sw1'), S('sw2'), '', S('sway0')),
      ('mult', u, u, '', S('uu')), ('mult', S('sway0'), 'wavek', '', S('sway1')), ('mult', S('sway1'), S('uu'), '', S('sway')),
      # spine point
      ('mult', 'dir', 'length', '', S('along0')), ('mult', S('along0'), u, '', S('along')),
      ('add', 'Root', S('along'), '', S('sp0')), ('add', S('sp0'), S('writheoff'), '', S('sp1')), ('add', S('sp1'), S('sway'), '', 'spine' + x)]
tmp_ = 'ramp grow envl w1 writheoff wf1 wph0 wph1 wph sn ph2a ph2 cs sw1 sw2 sway0 uu sway1 sway along0 along sp0 sp1'
steps = spine('a') + spine('b') + [
  # ring centre = midpoint of the two spine points, spine direction = their difference
  ('add', 'spinea', 'spineb', '', 'sumab'), ('mult', 'sumab', 'half', '', 'centre'),
  ('asubb', 'spineb', 'spinea', '', 'diff'), ('add', 'diff', 'eps', '', 'diffE'), ('normalize', 'diffE', '', '', 'tang'),
  # ring frame: p1 made perpendicular to the spine direction (nn), and its cross product with it (bb)
  ('dot', 'p1', 'tang', '', 'p1T'), ('mult', 'tang', 'p1T', '', 'Tp'), ('asubb', 'p1', 'Tp', '', 'nraw'), ('normalize', 'nraw', '', '', 'nn'), ('cross', 'tang', 'nn', '', 'bb'),
  # radius: taper, tip minimum, pulses travelling along, nothing while retracted
  ('asubb', 'one', 'u', '', 'iu'), ('apowerb', 'iu', 'taper', '', 'tp'), ('mult', 'tp', 'thick', '', 'r0'), ('amultbaddc', 'iu', 'tipmin', 'r0', 'r1'),
  ('mult', 'pulsefreq', 'u', '', 'pf1'), ('asubb', 'pf1', 'wavetime', '', 'pf2'), ('amultbaddc', 'seed', 'seedpulse', 'pf2', 'pph'),
  ('sin', 'pph', '', '', 'psn'), ('smoothstep', 'zero', 'c03', 'u', 'pramp'), ('mult', 'psn', 'pramp', '', 'p3'),
  ('amultbaddc', 'p3', 'pulseamt', 'one', 'pk'), ('mult', 'r1', 'pk', '', 'r2'),
  ('smoothstep', 'zero', 'c001', 'growamt', 'alive'), ('mult', 'r2', 'alive', '', 'ringr')]
delete = ' '.join([t + x for x in 'ab' for t in tmp_.split()] +
    'spinea spineb sumab diff diffE tang p1T Tp nraw iu tp r0 r1 pf1 pf2 pph psn pramp p3 pk r2 alive '
    'writhea writheb seed qa qb sq ua ub dir p1 p2 Root'.split())
spine_table = mcomb(c, 'spine_table', nwb, consts, steps, delete=delete)   # per spine point: centre, nn, bb, ringr (and u)

# ---- the tube vertices fetch their ring from the spine table
# ring number of every tube vertex -> which spine point of which tentacle it belongs to: index = tid * Segments + ring
tix = mcomb(c, 'tube_index', cp2,
  [('half', 'float', [0.5]), ('segm1', 'float', [P+'Segments-1']), ('segs', 'float', [P+'Segments'])],
  [('add', 'P.y', 'half', '', 'v'), ('mult', 'v', 'segm1', '', 'ringf'), ('round', 'ringf', '', '', 'ring'),
   ('amultbaddc', 'tid', 'segs', 'ring', 'spineidx')], delete='v ringf ring')
lk = c.create(td.lookupattributePOP, 'ring_lookup')
lk.inputConnectors[0].connect(tix); lk.inputConnectors[1].connect(spine_table)
lk.par.lookupindexattr = 'spineidx'; lk.par.indexunit = 'pointindex'; lk.par.interpolate = False
lk.seq.lookup.numBlocks = 4
for k_, (src_, dst_) in enumerate((('centre', 'ringcentre'), ('nn', 'ringnn'), ('bb', 'ringbb'), ('ringr', 'ringradius'))):
    getattr(lk.par, 'lookup%dvalueattr' % k_).val = src_; getattr(lk.par, 'lookup%doutputattrscope' % k_).val = dst_
# vertex = ring centre + (nn * x + bb * z) * 2 * radius   (the template tube has radius 0.5)
g = mcomb(c, 'tentacle', lk,
  [('two', 'float', [2])],
  [('mult', 'ringnn', 'P.x', '', 'rx'), ('mult', 'ringbb', 'P.z', '', 'rz'), ('add', 'rx', 'rz', '', 'ring0'),
   ('mult', 'ring0', 'two', '', 'ring1'), ('mult', 'ring1', 'ringradius', '', 'ring2'),
   ('add', 'ringcentre', 'ring2', '', 'P')],
  delete='rx rz ring0 ring1 ring2 ringcentre ringnn ringbb ringradius spineidx tid')
nr = c.create(td.normalPOP, 'tubes'); nr.inputConnectors[0].connect(g)
o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(nr); o1.comment = 'tentacle tubes'

# ---- internal preview render (not an output) ----
env = glsl(c, 'envmap', open(os.path.join(ROOT,'components','_lib','env.glsl')).read(),
           vecs=[('uA',[P+'Envintensity', P+'Redaccent', 0, 0])], fmt='rgba16float')
env.par.outputresolution = 'custom'; env.par.resolutionw = 1024; env.par.resolutionh = 512
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = nr
sel.display = True; sel.render = True
mat = c.create(td.pbrMAT, 'mat')
mat.par.basecolorr.expr = P+'Basecolorr'; mat.par.basecolorg.expr = P+'Basecolorg'; mat.par.basecolorb.expr = P+'Basecolorb'
mat.par.applypointcolor = False
mat.par.metallic.expr = P+'Metallic'; mat.par.roughness.expr = P+'Roughness'
geo.par.material = mat
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
ang = "absTime.seconds*0.25"
cam.par.tx.expr = "math.sin(%s)*%sCamdist" % (ang, P)
cam.par.tz.expr = "math.cos(%s)*%sCamdist" % (ang, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov = 50; cam.par.lookat = tgt
el = c.create(td.environmentlightCOMP, 'envlight'); el.par.envlightmap = env
key = c.create(td.lightCOMP, 'key'); key.par.tx = -4; key.par.ty = 5; key.par.tz = 4; key.par.lookat = tgt
key.par.dimmer = 0.6; key.par.shadowtype = 'off'
rim = c.create(td.lightCOMP, 'rim'); rim.par.tx = 4.5; rim.par.ty = 2; rim.par.tz = -5; rim.par.lookat = tgt
rim.par.cr = 1; rim.par.cg = 0.15; rim.par.cb = 0.1; rim.par.dimmer.expr = P+'Redaccent*0.8'; rim.par.shadowtype = 'off'
rt = c.create(td.renderTOP, 'preview'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = 'envlight key rim'
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr.expr = P+'Bgcolorr'; rt.par.bgcolorg.expr = P+'Bgcolorg'; rt.par.bgcolorb.expr = P+'Bgcolorb'; rt.par.bgcolora = 1
rt.par.antialias = 'aa4'; rt.par.format = 'rgba16float'
finish(c, name)
report(c)
