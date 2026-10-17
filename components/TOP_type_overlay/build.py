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

COMP = 'TOP_type_overlay'
c = new_comp(COMP)
add_pars(c, [
 ('Layout','menu',[('rendah','Rendah (title bottom-left)'),('center','Center'),('poster','Poster (title top-left)'),('minimal','Minimal'),('data','Data heavy')],0),
 ('Title','str','*PHANTOM\n*SIGNAL\nfield recordings\nvol. 07 / 2026'),
 ('Titlesize','float',0.085,0.01,0.3), ('Telemetry','toggle',1), ('Telesize','float',1.0,0.4,3), ('Telelines','int',6,1,16),
 ('Tickrate','float',8.0,0.5,60), ('Fps','int',24,1,120),
 ('Marks','toggle',1), ('Border','toggle',1), ('Edgeticks','toggle',1), ('Crosshair','toggle',1), ('Borderwidth','float',1.0,0.5,6),
 ('Margin','float',0.045,0.0,0.2), ('Textcolor','rgb',(0.93,0.91,0.86)), ('Accent','toggle',1), ('Accentcolor','rgb',(0.90,0.07,0.05)),
 ('Opacity','float',1.0,0,1,True), ('Modamount','float',0.5,0,2),
 *COMMON,
], 'Controls')
res_chop(c)
add_mod(c, 'in2')
# Make Title a multi-line-friendly string: leave as Str; '\n' (backslash-n) also accepted.
lib = mkdat(c, 'lib', rd(COMP, 'lib.py'))
inp = c.create(td.inTOP, 'in1')
dm = new_demo(c)
blk = dm.create(td.constantTOP, 'black'); setres(blk); blk.par.format = 'rgba16float'
for k in ('colorr','colorg','colorb'): blk.par[k] = 0
blk.par.alpha = 1
demo_out(dm, blk)
bsw = c.create(td.switchTOP, 'base')
bsw.inputConnectors[0].connect(dm.outputConnectors[0]); bsw.inputConnectors[1].connect(inp)
bsw.par.index.expr = HASIN
setres(bsw); bsw.par.format = 'rgba16float'

M = "op('lib').module."
def text(name, elem, fn, bold=False, accent=False, tele=True, dx=0.0, dy=0.0):
    t = c.create(td.textTOP, name)
    t.par.text.expr = M + fn + '()'
    t.par.outputresolution = 'custom'; setres(t)
    t.par.format = 'rgba16float'
    t.par.fontautosize = 'nofit'
    t.par.fontsizexunit = 'pixels'
    t.par.fontsizex.expr = M + "size('%s')" % elem
    t.par.font = 'Menlo'
    t.par.positionunit = 'fraction'
    t.par.positionx.expr = M + "pos('%s','x')" % elem + (" + %g*%ssize('%s')/op('res')['w']" % (dx, M, elem) if dx else '')
    t.par.positiony.expr = M + "pos('%s','y')" % elem + (" + %g*%ssize('%s')/op('res')['h']" % (dy, M, elem) if dy else '')
    t.par.alignx.expr = M + "align('%s','x')" % elem
    t.par.aligny.expr = M + "align('%s','y')" % elem
    t.par.alignxmode = 'metrics'
    cr = 'Accentcolor' if accent else 'Textcolor'
    for k in 'rgb': t.par['fontcolor' + k].expr = "parent().par.%s%s" % (cr, k)
    gate = (" * parent().par.Telemetry" if tele else "")
    t.par.fontalpha.expr = M + "vis('%s') * parent().par.Opacity" % elem + gate
    t.par.bgalpha = 0
    t.par.linespacing = 0 if False else t.par.linespacing.eval()
    return t
# TD cannot select Menlo Bold, so 'bold' is faux-bold: three copies nudged by ~2% of the font size
tb = text('title_bold', 'title', 'title_bold', tele=False, dx=0.022)
tb2 = text('title_bold2', 'title', 'title_bold', tele=False, dx=-0.022)
tb3 = text('title_bold3', 'title', 'title_bold', tele=False, dy=0.022)
tr_ = text('title_reg', 'title', 'title_reg', tele=False)
tl = text('tele_tl', 'tl', 'tl'); rc = text('tele_rec', 'rec', 'rec', accent=True)
trt = text('tele_tr', 'tr', 'tr'); blt = text('tele_bl', 'bl', 'bl'); brt = text('tele_br', 'br', 'br')
# accent toggle: rec turns bone when Accent off
for k in 'rgb':
    rc.par['fontcolor' + k].expr = "parent().par.Accentcolor%s if parent().par.Accent else parent().par.Textcolor%s" % (k, k)

mk = glsl(c, 'marks', rd(COMP, 'marks.glsl'), vecs=[
  ('uRes', ["op('res')['w']", "op('res')['h']", "parent().par.Margin*op('res')['h']", 'parent().par.Borderwidth']),
  ('uCol', ['parent().par.Textcolorr', 'parent().par.Textcolorg', 'parent().par.Textcolorb', 'parent().par.Opacity']),
  ('uAcc', ['parent().par.Accentcolorr', 'parent().par.Accentcolorg', 'parent().par.Accentcolorb', 'parent().par.Accent']),
  ('uF', ['parent().par.Marks', 'parent().par.Border', 'parent().par.Edgeticks', 'parent().par.Crosshair']),
], fmt='rgba16float', res=True)

comp = c.create(td.compositeTOP, 'comp')
comp.par.operand = 'over'
comp.par.outputresolution = 'custom'; setres(comp); comp.par.format = 'rgba16float'
for s in (mk, brt, blt, trt, rc, tl, tb, tb2, tb3, tr_, bsw):   # TD Composite: first input is on top
    s.outputConnectors[0].connect(comp)
finish_v2(c, COMP, comp, bsw)
report(c)
