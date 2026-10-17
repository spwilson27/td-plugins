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

def setres(o, w=None, h=None):
    pre = "op('../res')" if o.parent().name == 'demo' else "op('res')"
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w or pre + "['w']"; o.par.resolutionh.expr = h or pre + "['h']"

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
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish_old(c, name):
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ======================= v2 additions (td-plugins CONVENTIONS v2) =======================
P_ = 'parent().par.'
# Standard Controls entries every TOP_ effect has. Append `*COMMON` to your Controls spec list
# (do NOT add your own Resolution / Mix / Bypass).
COMMON = [
    ('Mix', 'float', 1.0, 0, 1, True),
    ('Bypass', 'toggle', 0),
    ('Resolutionmode', 'menu', [('input', 'Follow Input'), ('custom', 'Custom')], 0),
    ('Resolution', 'wh', (1280, 720)),
]

# --- animation: absTime only (makes the preview example move; there is no Loop page) ---
PEXPR = "((absTime.seconds/8.0) % 1.0)"     # 0..1 over 8 s
LENEXPR = "8"
FREXPR = "240"
def uP(extra=0):
    return ('uP', [PEXPR, 8, 240, extra])

# --- resolution: Resolutionmode 'input' follows in1 (or Resolutionw/h when unconnected), 'custom' uses Resolutionw/h ---
def res_chop(c):
    k = c.create(td.constantCHOP, 'res')
    conn = "parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections and op('in1').width>0"
    k.par.name0 = 'w'; k.par.value0.expr = "(op('in1').width if (%s) else parent().par.Resolutionw)" % conn
    k.par.name1 = 'h'; k.par.value1.expr = "(op('in1').height if (%s) else parent().par.Resolutionh)" % conn
    return k

def new_demo(c):
    """Base COMP 'demo': holds every preview-only source. Not selected (so not cooking) when in1 is connected."""
    return c.create(td.baseCOMP, 'demo')

def demo_out(d, top, name='demo_out'):
    o = d.create(td.outTOP, name); o.inputConnectors[0].connect(top); return o

HASIN = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"

def v2_input(c, comp=None, srcfile='src.glsl', extra_vecs=()):
    """in1 (In TOP) + demo COMP (animated default source) -> Switch 'src' sized by 'res'."""
    res_chop(c)
    i = c.create(td.inTOP, 'in1')
    d = new_demo(c)
    code = (rd(comp, srcfile) if comp else open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read())
    g = glsl(d, 'defsrc', code, vecs=[uP()] + list(extra_vecs), res=True)
    demo_out(d, g)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = HASIN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

# --- optional modulation In CHOP (must be the LAST input). channels band1-4, beat ---
def add_mod(c, name):
    """name e.g. 'in3'. Creates In CHOP + Null 'modin'. Use MOD('band1') in expressions."""
    i = c.create(td.inCHOP, name); n = c.create(td.nullCHOP, 'modin'); n.inputConnectors[0].connect(i)
    return n
def MOD(ch, default=0):
    return "(op('modin')['%s'].eval() if (op('modin') and op('modin').numChans and op('modin')['%s'] is not None) else %s)" % (ch, ch, default)

# --- tail: Mix (dry/wet vs src), Bypass, out1 ---
def finish_v2(c, name, result, src, label='result', extra_outs=()):
    """result = effect TOP, src = dry input switch. Adds Mix cross, Bypass switch, out1 (+ extra_outs=[(top,'label'),..] as out2..)."""
    mx = c.create(td.crossTOP, 'mixer')
    mx.inputConnectors[0].connect(src); mx.inputConnectors[1].connect(result)
    mx.par.cross.expr = 'parent().par.Mix'
    setres(mx); mx.par.format = 'rgba16float'
    bp = c.create(td.switchTOP, 'bypass')
    bp.inputConnectors[0].connect(mx); bp.inputConnectors[1].connect(src)
    bp.par.index.expr = 'parent().par.Bypass'
    setres(bp); bp.par.format = 'rgba16float'
    o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(bp); o.comment = label
    for k, (t, lab) in enumerate(extra_outs):
        n = c.create(td.nullTOP, 'out%d' % (k + 2)); n.inputConnectors[0].connect(t); n.comment = lab
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c.save(p)
    print('saved', p)
# ======================= end v2 additions =======================

COMP = 'TOP_instance_grid'
P = "parent().par."
c = new_comp(COMP)
add_pars(c, [
  ('Shape','menu',[('0','Box'),('1','Sphere'),('2','Cone')],0),
  ('Countx','int',40,2,256),
  ('County','int',24,2,256),
  ('Spacing','float',0.5,0.05,3),
  ('Basesize','float',0.42,0.02,3),
  ('Heightbase','float',0.1,0,4),
  ('Heightamt','float',3.0,0,20),
  ('Scaleamt','float',0.0,0,1),
  ('Rotamt','float',0.0,-4,4),
  ('Invert','toggle',0),
  ('Colormix','float',1.0,0,1),
  ('Noisespeed','float',0.15,0,2),
  ('Bgcolor','rgb',(0.03,0.03,0.05)),
  ('Modamount','float',0.5,0,2),
  *COMMON,
])
add_pars(c, [
  ('Orbitspeed','float',0.1,-2,2),
  ('Orbitangle','float',0.5,-6.28,6.28),
  ('Distance','float',32,3,120),
  ('Elevation','float',20,-20,80),
  ('Fov','float',45,15,100),
], page='Camera')
add_pars(c, [
  ('Lightangle','float',0.8,-6.28,6.28),
  ('Lightheight','float',20,2,100),
  ('Lightintensity','float',1.1,0,4),
  ('Ambient','float',0.35,0,1),
  ('Shadows','toggle',1),
], page='Light')
add_pars(c, [
  ('Look','menu',[('original','Original'),('mono','Mono')],0),
  ('Accent','float',0.0,0,1),
], page='Look')
LOOKI = P + "Look.menuIndex"
def ORBIT(sp='Orbitspeed', off='Orbitangle'):
    return "(absTime.seconds*%s%s+%s%s)" % (P, sp, P, off)
res_chop(c)
i1 = c.create(td.inTOP, 'in1')
def setu(g, items):
    for i, (nm, vs) in enumerate(items):
        getattr(g.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', vs):
            p = getattr(g.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v
add_mod(c, 'in2')
dm = new_demo(c)
nz = dm.create(td.noiseTOP, 'default_noise')
nz.par.outputresolution='custom'; nz.par.resolutionw=512; nz.par.resolutionh=512
nz.par.mono = False; nz.par.period = 1.6; nz.par.amp = 0.55; nz.par.offset = 0.5; nz.par.harmon = 2
nz.par.tz.expr = "absTime.seconds*parent(2).par.Noisespeed*3"
demo_out(dm, nz)
sw = c.create(td.switchTOP, 'src_switch')
sw.inputConnectors[0].connect(dm.outputConnectors[0]); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = HASIN
rs = c.create(td.resolutionTOP, 'to_grid')
rs.par.outputresolution='custom'; rs.par.resolutionw.expr=P+"Countx"; rs.par.resolutionh.expr=P+"County"
rs.par.filtertype = 'linear' if 'linear' in rs.par.filtertype.menuNames else rs.par.filtertype.val
rs.inputConnectors[0].connect(sw)

# ---- per-instance data, built from native TOPs. Every pixel of the Countx x County image is one instance ----
def tiny(o, fmt='rgba32float'):
    """size an op like the grid (one pixel per instance) and use float pixels"""
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = P + "Countx"; o.par.resolutionh.expr = P + "County"
    o.par.format = fmt
    o.par.inputfiltertype = 'nearest'
    return o
def mk(typ, name, *ins, **pars):
    o = tiny(c.create(typ, name))
    for i, s_ in enumerate(ins): o.inputConnectors[i].connect(s_)
    for k, v in pars.items():
        if isinstance(v, str) and k.endswith('_expr'): o.par[k[:-5]].expr = v
        else: o.par[k] = v
    return o
def reorder(name, r, g, b, a=None):
    """Reorder TOP: build RGB from (input TOP, channel) pairs; a defaults to 1"""
    ins = []
    for src_, ch in (r, g, b):
        if src_ not in ins: ins.append(src_)
    o = tiny(c.create(td.reorderTOP, name))
    for i, s_ in enumerate(ins): o.inputConnectors[i].connect(s_)
    for slot, (src_, ch) in zip(('red', 'green', 'blue'), (r, g, b)):
        o.par['output' + slot] = 'input%d' % (ins.index(src_) + 1)
        o.par['output' + slot + 'chan'] = ch
    o.par.outputalpha = 'input1'; o.par.outputalphachan = 'one'
    return o

# luminance of the picture (0..1, optionally inverted)
luma = tiny(c.create(td.reorderTOP, 'luma_raw')); luma.inputConnectors[0].connect(rs)
for sl in ('red', 'green', 'blue'):
    luma.par['output' + sl] = 'input1'; luma.par['output' + sl + 'chan'] = 'luminance'
luma.par.outputalpha = 'input1'; luma.par.outputalphachan = 'luminance'   # alpha = luma too, so the Math TOP below can map it as well
lum = mk(td.levelTOP, 'luma', luma, clampinput=1, invert_expr=P + "Invert")
# One Math TOP turns the luminance (0..1) into four numbers per instance, each with its own From -> To range (per channel):
#   R = width   : Basesize, grown by luma when Scaleamt > 0
#   G = height  : Heightbase + Heightamt * luma   (band1 swells it)
#   B = rotation: Rotamt * luma * 360 degrees about Y
#   A = half the height (instances sit on the ground: translate Y = height / 2)
HAMT = P + "Heightamt*(1+" + P + "Modamount*" + MOD('band1') + ")"
sets = {'r': ("%sBasesize*(1-0.85*%sScaleamt)" % (P, P), "%sBasesize*(1+0.25*%sScaleamt)" % (P, P)),
        'g': (P + "Heightbase", P + "Heightbase+" + HAMT),
        'b': ("0", P + "Rotamt*360"),
        'a': ("0.5*" + P + "Heightbase", "0.5*(" + P + "Heightbase+" + HAMT + ")")}
fx = mk(td.mathTOP, 'from_luma', lum)
for ch, (lo, hi) in sets.items():
    # the Level TOP's Invert flips RGB but not alpha, so the alpha channel (half height) flips here
    fx.par['fromrange' + ch + '1'].expr = P + 'Invert' if ch == 'a' else '0'
    fx.par['fromrange' + ch + '2'].expr = '1-' + P + 'Invert' if ch == 'a' else '1'
    fx.par['torange' + ch + '1'].expr = lo; fx.par['torange' + ch + '2'].expr = hi
# towers are never thinner than 0.02 (Maximum against a constant, per channel)
minc = mk(td.constantTOP, 'min_height', colorr=-1e6, colorg=0.02, colorb=-1e6, alpha=0.01)
wrh = mk(td.compositeTOP, 'width_height_rot', fx, minc, operand='maximum')
# grid position: two ramps (left-right = X, bottom-top = Z) scaled to Spacing
rx = mk(td.rampTOP, 'ramp_x'); rx.par.type = 'horizontal'
rz = mk(td.rampTOP, 'ramp_z'); rz.par.type = 'vertical'
SPAN = "0.5*" + P + "Countx*" + P + "Spacing"; SPANZ = "0.5*" + P + "County*" + P + "Spacing"
posx = mk(td.mathTOP, 'pos_x', rx, fromrange1=0, fromrange2=1, torange1_expr="-" + SPAN, torange2_expr=SPAN)
posz = mk(td.mathTOP, 'pos_z', rz, fromrange1=0, fromrange2=1, torange1_expr="-" + SPANZ, torange2_expr=SPANZ)
zero = mk(td.constantTOP, 'zero', colorr=0, colorg=0, colorb=0, alpha=1)
# instancing: translate = inst_t (x, height/2, z); rotate and scale read channels of width_height_rot directly
# (rotate Y = blue, scale X/Z = red, scale Y = green); colour = whichever Look branch is selected
it = reorder('inst_t', (posx, 'red'), (wrh, 'alpha'), (posz, 'red'))
# colour: Look = original -> picture colour mixed with white by Colormix
white = mk(td.constantTOP, 'white', colorr=1, colorg=1, colorb=1, alpha=1)
col_orig = mk(td.crossTOP, 'colour_original', white, rs, cross_expr=P + "Colormix")
# Look = mono -> bone-white grey ramp from luma, with red on the brightest instances (smoothstep .78-.92 times Accent)
mono_g = mk(td.mathTOP, 'mono_grey', lum, gain=0.88, postoff=0.12)
bone = mk(td.constantTOP, 'bone', colorr=0.95, colorg=0.93, colorb=0.88, alpha=1)
mono_c = mk(td.compositeTOP, 'mono_bone', mono_g, bone, operand='multiply')
acc0 = mk(td.levelTOP, 'accent_t', lum, inlow=0.78, inhigh=0.92, clampinput=0, clamp=1)
acc1 = mk(td.mathTOP, 'accent_t2', acc0, postop='square')                       # t*t
acc2 = mk(td.mathTOP, 'accent_3m2t', acc0, gain=-2.0, postoff=3.0)              # 3-2t
acc3 = mk(td.compositeTOP, 'accent_smooth', acc1, acc2, operand='multiply')    # smoothstep = t*t*(3-2t)
acc4 = mk(td.mathTOP, 'accent_amount', acc3, gain_expr=P + "Accent")
acc5 = reorder('accent_alpha', (acc4, 'red'), (acc4, 'red'), (acc4, 'red'))
acc5.par.outputalpha = 'input1'; acc5.par.outputalphachan = 'red'
redc = mk(td.constantTOP, 'accent_red', colorr=0.95, colorg=0.04, colorb=0.04, alpha=1)
red_l = mk(td.compositeTOP, 'accent_layer', redc, acc5, operand='multiply')
mono_f = mk(td.compositeTOP, 'colour_mono', red_l, mono_c, operand='over')
dat = {'inst_t': it}

# geometry
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
bx = geo.create(td.boxSOP,'box1'); sp = geo.create(td.sphereSOP,'sphere1'); cn = geo.create(td.tubeSOP,'cone1')
cn.par.type='poly'; cn.par.rad1=0.5; cn.par.rad2=0; cn.par.height=1; cn.par.cols=24; cn.par.rows=1; cn.par.cap=True; cn.par.orient='y' if 'y' in cn.par.orient.menuNames else cn.par.orient.val
sp.par.type='poly'; sp.par.radx=0.5; sp.par.rady=0.5; sp.par.radz=0.5; sp.par.rows=16; sp.par.cols=24
sw3 = geo.create(td.switchSOP,'shape_switch')
for k,o in enumerate((bx,sp,cn)): sw3.inputConnectors[0 if k==0 else 0].connect(o) if False else None
# switchSOP inputs are a growing list
sw3.inputConnectors[0].connect(bx)
sw3.inputConnectors[1].connect(sp)
sw3.inputConnectors[2].connect(cn)
sw3.par.input.expr = "parent(2).par.Shape.menuIndex"
sw3.display = True; sw3.render = True
SZ = [('box1',bx),('sphere1',sp),('cone1',cn)]
mat = c.create(td.phongMAT,'mat')
mat.par.diffr=1; mat.par.diffg=1; mat.par.diffb=1
mat.par.ambr=1; mat.par.ambg=1; mat.par.ambb=1
mat.par.specr=0.3; mat.par.specg=0.3; mat.par.specb=0.3
geo.par.material = mat
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = dat['inst_t']
geo.par.instancetop = dat['inst_t']
geo.par.instancetx='r'; geo.par.instancety='g'; geo.par.instancetz='b'
geo.par.instancerop = wrh
geo.par.instancerx=''; geo.par.instancery='b'; geo.par.instancerz=''
geo.par.instancesop = wrh
geo.par.instancesx='r'; geo.par.instancesy='g'; geo.par.instancesz='r'
geo.par.instancecolorop.expr = "parent().op('colour_mono') if parent().par.Look=='mono' else parent().op('colour_original')"
geo.par.instancer='r'; geo.par.instanceg='g'; geo.par.instanceb='b'

tgt = c.create(td.nullCOMP,'target')
cam = c.create(td.cameraCOMP,'cam')
cam.par.tx.expr = "math.sin(%s)*%sDistance" % (ORBIT(),P)
cam.par.tz.expr = "math.cos(%s)*%sDistance" % (ORBIT(),P)
cam.par.ty.expr = P+"Elevation"
cam.par.fov.expr = P+"Fov"
cam.par.lookat = tgt
lt = c.create(td.lightCOMP,'light')
lt.par.tx.expr = "math.sin(%sLightangle)*%sLightheight*0.7" % (P,P)
lt.par.tz.expr = "math.cos(%sLightangle)*%sLightheight*0.7" % (P,P)
lt.par.ty.expr = P+"Lightheight"
lt.par.lookat = tgt
lt.par.dimmer.expr = P+"Lightintensity"
lt.par.shadowtype.expr = "'hard2d' if "+P+"Shadows else 'off'"
al = c.create(td.ambientlightCOMP,'ambient_light')
al.par.dimmer.expr=P+"Ambient"
rt = c.create(td.renderTOP,'render')
rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = 'light ambient_light'
setres(rt)
rt.par.bgcolorr.expr="0 if %s else %sBgcolorr"%(LOOKI,P); rt.par.bgcolorg.expr="0 if %s else %sBgcolorg"%(LOOKI,P); rt.par.bgcolorb.expr="0 if %s else %sBgcolorb"%(LOOKI,P); rt.par.bgcolora=1
rt.par.antialias = 'aa4'
# dry = default/in1 image scaled to render resolution
src = c.create(td.switchTOP, 'src'); src.inputConnectors[0].connect(sw)
setres(src); src.par.format = 'rgba16float'
finish_v2(c, COMP, rt, src)
report(c)
