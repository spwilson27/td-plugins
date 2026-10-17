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

# ---- native-build helpers (natB) ----
import math
def mk(par, typ, name, ins=(), **kw):
    """create op, set params. value str starting with '=' -> expression; tuple/list for menus not needed."""
    o = par.create(typ, name)
    for k, v in kw.items():
        p = getattr(o.par, k)
        if isinstance(v, str) and v.startswith('='):
            p.expr = v[1:]
        else:
            p.val = v
    for i, s in enumerate(ins):
        if s is not None:
            o.inputConnectors[i].connect(s.outputConnectors[0] if getattr(s, 'isCOMP', False) else s)
    return o
def resx(o, par_expr_w="op('res')['w']", par_expr_h="op('res')['h']"):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = par_expr_w; o.par.resolutionh.expr = par_expr_h
    return o
def keys_dat(par, name, rows):
    d = par.create(td.tableDAT, name)
    d.clear(); d.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for r in rows: d.appendRow([('%.5g' % x) for x in r])
    return d
def ramp_from(par, name, rows, w=1024, h=1, typ='horizontal', **kw):
    d = keys_dat(par, name + '_keys', rows)
    r = par.create(td.rampTOP, name)
    r.par.dat = d; r.par.type = typ
    r.par.extendleft = 'hold'; r.par.extendright = 'hold'
    r.par.outputresolution = 'custom'; r.par.resolutionw = w; r.par.resolutionh = h
    r.par.format = 'rgba16float'
    for k, v in kw.items():
        p = getattr(r.par, k)
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        else: p.val = v
    return r
def smooth(a, b, x):
    t = min(1, max(0, (x - a) / (b - a))); return t * t * (3 - 2 * t)

COMP = 'TOP_dof_motionblur'
c = new_comp(COMP)
add_pars(c, [
    ('Speed', 'float', 1.0, 0, 8),
    ('Depthmode', 'menu', [('auto', 'Auto (in2, else radial)'), ('in2', 'in2 TOP'), ('luma', 'Luminance'), ('radial', 'Radial mask')], 0),
    ('Invertdepth', 'toggle', 0),
    ('Focus', 'float', 0.5, 0, 1),
    ('Range', 'float', 0.08, 0, 0.5),
    ('Falloff', 'float', 0.4, 0.02, 1),
    ('Maxblur', 'float', 28, 0, 100),
    ('Quality', 'int', 64, 8, 160),
    ('Boost', 'float', 2.0, 0, 20),
    ('Blades', 'int', 6, 0, 12),
    ('Bladerot', 'float', 0.2, 0, 6.28),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
add_pars(c, [
    ('Mbactive', 'toggle', 1),
    ('Shutter', 'float', 0.55, 0, 0.97),
    ('Velscale', 'float', 1.0, 0, 20),
    ('Velsamples', 'int', 24, 4, 63),
    ('Reset', 'pulse'),
], page='Motion')
add_pars(c, [('Showdepth', 'toggle', 0), ('Showcoc', 'toggle', 0)], page='Output')
P = 'parent().par.'
HAS1 = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
def has(n): return "(len(parent().inputConnectors[%d].connections)+0*absTime.frame)" % n
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')
add_mod(c, 'in4')
# ------------------------------------------------------------------ demo scene (native, gated): floor lines + dots at many depths
dm = new_demo(c)
DW = "op('../res')['w']"; DH = "op('../res')['h']"
PH = "((absTime.seconds*parent(2).par.Speed/8.0)%1.0)"
def h11(n):
    import math as m_; v = m_.sin(n * 127.1) * 43758.5453; return v - m_.floor(v)
def dres(o): return resx(o, DW, DH)
def scene(tag, depth):
    """tag 'c' = colour image, 'd' = depth image. Same geometry in both."""
    if depth:
        fl = ramp_from(dm, 'floor_d', [(0, 0, 0, 0, 1), (0.58, 1, 1, 1, 1), (1, 1, 1, 1, 1)], w=8, h=256, typ='vertical')
        fl.par.resolutionw.expr = DW; fl.par.resolutionh.expr = DH
        x = fl
    else:
        x = mk(dm, td.constantTOP, 'base_c', colorr=0.01, colorg=0.01, colorb=0.01, alpha=1, format='rgba16float'); dres(x)
        for k in range(10):     # horizontal floor lines: perspective spacing, scrolling with the loop phase
            zz = "((%d+%s*6.0)%%10+0.35)" % (k, PH)
            x = mk(dm, td.rectangleTOP, 'hline%d' % k, [x], sizeunit='pixels', centerunit='pixels', sizex='=' + DW, sizey=2.0, centerx=0,
                   centery='=(.08-.5/(%s*0.6))*%s' % (zz, DH), bgalpha=0, borderwidth=0, softness=0, operand='add',
                   fillcolorr='=.62*math.exp(-%s*0.6*0.12)' % zz, fillcolorg='=.62*math.exp(-%s*0.6*0.12)' % zz, fillcolorb='=.6*math.exp(-%s*0.6*0.12)' % zz, format='rgba16float'); dres(x)
        for m in range(-4, 5):   # converging floor lines through the vanishing point on the horizon
            if m == 0: continue
            th = math.atan(m * 0.25)
            x = mk(dm, td.rectangleTOP, 'vline%d' % (m + 4), [x], sizeunit='pixels', centerunit='pixels', sizex=2.0, sizey='=1.0*' + DH,
                   centerx='=%.4f*%s' % (.5 * math.sin(th), DH), centery='=(.08-%.4f)*%s' % (.5 * math.cos(th), DH), rotate=math.degrees(th),
                   bgalpha=0, borderwidth=0, softness=0, operand='add', fillcolorr=0.28, fillcolorg=0.28, fillcolorb=0.27, format='rgba16float'); dres(x)
    dots = []
    for i in range(30):
        fi = float(i)
        dots.append((h11(fi * 3.7 + 1.0), i))
    dots.sort(reverse=True)    # far first, near drawn last (nearest wins)
    for dz, i in dots:
        fi = float(i)
        bx = (h11(fi * 1.3 + 0.1) - .5) * 1.9; by = (h11(fi * 2.9 + 0.7) - .5) * 0.9
        k = 1.0 + math.floor(h11(fi + 9.0) * 3.0)
        rad = 0.006 + 0.02 * h11(fi * 5.1 + 2.0); rad = max(rad, 0.008)
        cx = "(%.4f+0.06*math.sin(6.2831853*(%s*%d)+%.2f))*%s" % (bx, PH, k, fi, DH)
        cy = "(%.4f+0.06*math.cos(6.2831853*(%s*%d)+%.2f))*%s" % (by, PH, k, fi * 1.7, DH)
        hot = h11(fi * 8.3) > 0.88
        br = 0.7 + 0.9 * h11(fi * 4.4)
        if depth: col = (dz, dz, dz)
        else:     col = ((1.0, .1, .05) if hot else (.95, .94, .9)); col = tuple(v * br for v in col)
        x = mk(dm, td.circleTOP, '%sdot%d' % (tag, i), [x], radiusunit='pixels', centerunit='pixels', radiusx='=%.4f*%s' % (rad * 1.0, DH), radiusy='=%.4f*%s' % (rad * 1.0, DH),
               centerx='=' + cx, centery='=' + cy, fillcolorr=col[0], fillcolorg=col[1], fillcolorb=col[2], fillalpha=1, bgalpha=0, borderwidth=0,
               softness=0, format='rgba16float'); dres(x)
    if depth: x = mk(dm, td.reorderTOP, 'depth_opaque', [x], outputalphachan='one', format='rgba16float')
    return x
import math
dcol = scene('c', False); ddep = scene('d', True)
demo_out(dm, dcol, 'demo_color'); demo_out(dm, ddep, 'demo_depth')
def sw(nm, ins, expr):
    s = c.create(td.switchTOP, nm)
    for k, a in enumerate(ins): s.inputConnectors[k].connect(a)
    s.par.index.expr = expr
    setres(s); s.par.format = 'rgba16float'
    return s
src = sw('src', [dm.outputConnectors[0], i1], HAS1)
nod = c.create(td.constantTOP, 'nodepth'); setres(nod); nod.par.format = 'rgba16float'
nod.par.colorr = nod.par.colorg = nod.par.colorb = 0; nod.par.alpha = 1
dsrc = sw('depthsrc', [dm.outputConnectors[1], i2, nod], "1 if %s else (2 if %s else 0)" % (has(1), has(0)))

# ------------------------------------------------------------------ depth preparation (native): pick source, invert
d_in = mk(c, td.monochromeTOP, 'depth_in', [dsrc], rgb='red', alpha='one', format='rgba16float')
d_luma = mk(c, td.monochromeTOP, 'luma', [src], rgb='luminance', alpha='one', format='rgba16float')
radd = mk(c, td.circleTOP, 'radial_disc', radiusunit='pixels', radiusx="=op('res')['h']/1.15", radiusy="=op('res')['h']/1.15", softnessunit='pixels',
          softness="=op('res')['h']/1.15", softnesstype='linear', fillalpha=1, bgalpha=0, borderwidth=0, format='rgba16float'); resx(radd)
d_rad = mk(c, td.mathTOP, 'radial', [radd], gain=-1.0, postoff=1.0, format='rgba16float')
# auto: in2 if connected (or the demo is showing), otherwise radial
IDX = ("(lambda m: 0 if m==1 else (1 if m==2 else (2 if m==3 else (0 if (%s or not %s) else 2))))(%sDepthmode.menuIndex)" % (has(1), has(0), P))
dsel = mk(c, td.switchTOP, 'depth_source', [d_in, d_luma, d_rad], index='=' + IDX)
prep = mk(c, td.levelTOP, 'prep', [dsel], invert="=1 if %sInvertdepth else 0" % P, format='rgba16float')   # prepared depth map = out2 (Invertdepth flips it)

# ------------------------------------------------------------------ depth of field: |depth - focus| drives a Luma Blur TOP
FOC = "min(1,max(0,%sFocus+%sModamount*%s*0.5))" % (P, P, MOD('band1'))
FOCD = "(1-%s if %sInvertdepth else %s)" % (FOC, P, FOC)   # |1-d-f| = |d-(1-f)|: inverting the depth just mirrors the focus value
dist = mk(c, td.mathTOP, 'focus_distance', [dsel], preoff='=-(%s)' % FOCD, preop='square', postop='root', format='rgba16float')
RS = "op('res')['h']/720.0"
lb = mk(c, td.lumablurTOP, 'defocus', [src, dist], type="='box' if %sBlades>=3 else 'gaussian'" % P, widthchan='luminance', extend='hold',
        blackvalue='=%sRange' % P, whitevalue='=%sRange+%sFalloff' % (P, P), blackwidth=0, whitewidth='=%sMaxblur*%s' % (P, RS), format='rgba16float')
dof_on = mk(c, td.switchTOP, 'dof_switch', [src, lb], index="=1 if %sMaxblur>0 else 0" % P)

# ------------------------------------------------------------------ velocity motion blur (one small GLSL pass, see README)
vel_on = glsl(c, 'mblur', rd(COMP, 'mblur.glsl'), inputs=[dof_on, i3], res=True,
              vecs=[('uA', [P + 'Velscale*' + P + 'Mbactive', P + 'Velsamples', "1 if %s else 0" % has(2), 0])])
vel_on.par.inputextenduv = 'hold'

# ------------------------------------------------------------------ frame accumulation: Cross TOP against a Feedback TOP
blk = c.create(td.constantTOP, 'blank'); setres(blk)
blk.par.format = 'rgba16float'; blk.par.colorr = blk.par.colorg = blk.par.colorb = 0; blk.par.alpha = 1
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(blk)
fb.par.format = 'rgba16float'
fb.par.reset.expr = P + 'Reset'
acc = mk(c, td.crossTOP, 'accumulate', [vel_on, fb], cross='=%sShutter*(1 if %sMbactive else 0)' % (P, P), format='rgba16float'); setres(acc)
nul = c.create(td.nullTOP, 'accum_out'); nul.inputConnectors[0].connect(acc)
fb.par.top = nul

# ------------------------------------------------------------------ debug views: depth, focus map (green in focus, red blurred)
x01 = mk(c, td.mathTOP, 'coc_x', [dist], preoff='=-%sRange' % P, gain='=1.0/max(%sFalloff,0.001)' % P, format='rgba16float')
x01c = mk(c, td.levelTOP, 'coc_clamp', [x01], clamp=True, clamplow2=0.0, clamphigh2=1.0, format='rgba16float')
ss = ramp_from(c, 'smoothstep_curve', [(i / 16, ) + ((i / 16) ** 2 * (3 - 2 * i / 16),) * 3 + (1,) for i in range(17)])
coc = mk(c, td.lookupTOP, 'coc', [x01c, ss], channel='luminance', darkuv1='=0.5/1024', lightuv1='=1-0.5/1024', format='rgba16float')
gr = ramp_from(c, 'coc_colors', [(0, 0.035, 0.63, 0.14, 1), (1, 0.7, 0.07, 0.07, 1)])
cocv = mk(c, td.lookupTOP, 'coc_view', [coc, gr], channel='luminance', darkuv1='=0.5/1024', lightuv1='=1-0.5/1024', format='rgba16float')
vis = mk(c, td.switchTOP, 'view', [nul, prep, cocv], index="=2 if %sShowcoc else (1 if %sShowdepth else 0)" % (P, P))
finish_v2(c, COMP, vis, src, extra_outs=[(prep, 'depth')])
report(c)
