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

# ---- frame graphics (border, crop marks, centre cross, edge ticks): Rectangle TOPs ----
# The frame is symmetric left/right and top/bottom, so only its BOTTOM-LEFT QUARTER is drawn (on a canvas a quarter of
# the size, 8 bit); a Tile TOP with 'reflect' then mirrors it into the full frame. Only the accent crop mark (top-left)
# breaks the symmetry; it is drawn on its own small canvas and placed with a Transform TOP.
# 'geo' holds the measurements in pixels so every rectangle just reads a number.
geo = c.create(td.constantCHOP, 'geo')
for i, (nm, ex) in enumerate([
    ('W', "op('res')['w']"), ('H', "op('res')['h']"),
    ('inset', "parent().par.Margin*op('res')['h']*0.5"),                      # frame inset from the edge
    ('bw', "parent().par.Borderwidth"),                                        # border line width
    ('t', "max(2, parent().par.Borderwidth*2.5)"),                             # crop-mark line width
    ('L', "0.035*op('res')['h']"),                                             # crop-mark arm length
    ('hx', "op('res')['w']*0.5 - parent().par.Margin*op('res')['h']*0.5"),     # half width of the frame
    ('hy', "op('res')['h']*0.5 - parent().par.Margin*op('res')['h']*0.5"),     # half height of the frame
    ('sp', "(op('res')['w'] - parent().par.Margin*op('res')['h'])/40.0"),      # tick spacing
]):
    geo.par['name%d' % i] = nm; geo.par['value%d' % i].expr = ex
G = lambda k: "op('geo')['%s']" % k
hx, hy, T, Ln = G('hx'), G('hy'), G('t'), G('L')
QX, QY = '(%s/4)' % G('W'), '(%s/4)' % G('H')      # the quarter canvas is centred at (-W/4, -H/4) of the frame

def rect(name, cx, cy, w, h, color='Textcolor', gate=None, src=None, border=False, opa=True, quarter='BL'):
    """Rectangle TOP on a quarter-size 8-bit canvas. cx, cy, w, h in pixels in FRAME coordinates (from the frame
    centre, y up); drawn over src. quarter = 'BL' or 'TL' (which quarter of the frame the canvas shows)."""
    r = c.create(td.rectangleTOP, name)
    r.par.outputresolution = 'custom'
    r.par.resolutionw.expr = "op('res')['w']/2"; r.par.resolutionh.expr = "op('res')['h']/2"
    r.par.format = 'rgba8fixed'
    r.par.sizeunit = 'pixels'; r.par.centerunit = 'pixels'
    sgn = '-' if quarter == 'BL' else '+'
    r.par.sizex.expr = w; r.par.sizey.expr = h
    r.par.centerx.expr = '(%s) + %s' % (cx, QX); r.par.centery.expr = '(%s) %s %s' % (cy, '+' if quarter == 'BL' else '-', QY)
    for k in 'rgb':
        r.par['fillcolor' + k].expr = 'parent().par.%s%s' % (color, k)
        r.par['border' + k].expr = 'parent().par.%s%s' % (color, k)
        r.par['bgcolor' + k] = 0
    r.par.bgalpha = 0
    a = ('parent().par.Opacity' if opa else '1') + (' * ' + gate if gate else '')
    r.par.fillalpha.expr = '0' if border else a
    r.par.borderalpha.expr = a if border else '0'
    if border:
        r.par.borderwidthunit = 'pixels'; r.par.borderwidth.expr = G('bw'); r.par.borderoffset = 0.5
    r.par.premultrgbbyalpha = 1
    if src is not None:
        r.inputConnectors[0].connect(src)
    return r

def q_comp(name, operand, *ins):
    k = c.create(td.compositeTOP, name); k.par.operand = operand
    k.par.outputresolution = 'custom'
    k.par.resolutionw.expr = "op('res')['w']/2"; k.par.resolutionh.expr = "op('res')['h']/2"
    k.par.format = 'rgba8fixed'
    for i in ins: i.outputConnectors[0].connect(k)
    return k

# thin border: an outline-only rectangle the size of the frame (only its bottom-left corner shows on this canvas)
chain = rect('border', '0', '0', '2*' + hx, '2*' + hy, gate='parent().par.Border', border=True)
# crop marks: two thin rectangles per corner (a horizontal and a vertical arm)
arm = '(%s + %s/2)' % (Ln, T)
chain = rect('mark_h', '-(%s + %s/4 - %s/2)' % (hx, T, Ln), '-' + hy, arm, T, gate='parent().par.Marks', src=chain)
chain = rect('mark_v', '-' + hx, '-(%s + %s/4 - %s/2)' % (hy, T, Ln), T, arm, gate='parent().par.Marks', src=chain)
# centre cross: two thin bars
# (2 px bars at half opacity: the mirrored copies add up to a soft 1 px line, like the original)
chain = rect('cross_h', '0', '0', '2*0.012*' + G('H'), '2', gate='0.5*parent().par.Crosshair', src=chain)
chain = rect('cross_v', '0', '0', '2', '2*0.012*' + G('H'), gate='0.5*parent().par.Crosshair', src=chain)
# edge ticks: one tick is drawn wide, then a Transform TOP squeezes it to the tick spacing and repeats it
# (Extend = repeat). Minor ticks at every spacing, taller major ticks at every 5th.
def tick_layer(tag, period, length_frac):
    lenx = '(%s*%s)' % (length_frac, G('H'))
    wpx = '(%s/2/(%s*%d))' % (G('W'), G('sp'), period)          # width that squeezes to 1 px
    # the tick sits on the frame's bottom edge, pointing inwards; x = middle of the source canvas
    tk = rect('tick_%s' % tag, '0', '-(%s - %s/2)' % (hy, lenx), wpx, lenx)
    tk.par.centerx.expr = '0'      # centred on the source canvas; the Transform below positions the tiles
    tr_ = c.create(td.transformTOP, 'tick_%s_repeat' % tag)
    tr_.inputConnectors[0].connect(tk)
    tr_.par.outputresolution = 'custom'
    tr_.par.resolutionw.expr = "op('res')['w']/2"; tr_.par.resolutionh.expr = "op('res')['h']/2"
    tr_.par.format = 'rgba8fixed'
    tr_.par.extend = 'repeat'
    tr_.par.tunit = 'pixels'
    tr_.par.sx.expr = '%d*%s/(%s/2)' % (period, G('sp'), G('W'))
    tr_.par.tx.expr = '-%s/4 + %s' % (G('W'), G('inset'))    # first tick on the left edge of the frame
    return tr_
tk_minor = tick_layer('minor', 1, 0.006)
tk_major = tick_layer('major', 5, 0.012)
tk = q_comp('ticks_all', 'maximum', tk_major, tk_minor)
# keep only the ticks inside the frame, and honour the Edgeticks switch
win = rect('ticks_window', '-(%s + 0.5)/2' % hx, '0', '%s + 0.5' % hx, '2*' + G('H'), gate='parent().par.Edgeticks', opa=False)
tkm = q_comp('ticks', 'inside', tk, win)
quarter = q_comp('quarter', 'over', chain, tkm)
# mirror the quarter into the full frame
til = c.create(td.tileTOP, 'frame_mirror')
til.inputConnectors[0].connect(quarter)
til.par.repeatx = 2; til.par.repeaty = 2; til.par.reflectx = 1; til.par.reflecty = 1
til.par.outputresolution = 'custom'; setres(til); til.par.format = 'rgba8fixed'
# the accent (top-left) crop mark: two rectangles on a quarter canvas, moved into the top-left corner
acc = rect('accent_h', '-(%s + %s/4 - %s/2)' % (hx, T, Ln), hy, arm, T, color='Accentcolor', gate='parent().par.Marks', quarter='TL')
acc = rect('accent_v', '-' + hx, '(%s + %s/4 - %s/2)' % (hy, T, Ln), T, arm, color='Accentcolor', gate='parent().par.Marks', src=acc, quarter='TL')
for k in 'rgb':   # accent off -> same bone colour as the other marks
    for n in ('accent_h', 'accent_v'):
        c.op(n).par['fillcolor' + k].expr = "parent().par.Accentcolor%s if parent().par.Accent else parent().par.Textcolor%s" % (k, k)
acc_pl = c.create(td.transformTOP, 'accent_place')
acc_pl.inputConnectors[0].connect(acc)
acc_pl.par.outputresolution = 'custom'; setres(acc_pl); acc_pl.par.format = 'rgba8fixed'
# the Transform stretches its input to the output size, so scale by 1/2 (back to native pixels) and move to the top-left quarter
acc_pl.par.sx = 0.5; acc_pl.par.sy = 0.5; acc_pl.par.tx = -0.25; acc_pl.par.ty = 0.25
mk_layers = (acc_pl, til)   # fed straight into the final Composite below

comp = c.create(td.compositeTOP, 'comp')
comp.par.operand = 'over'
comp.par.outputresolution = 'custom'; setres(comp); comp.par.format = 'rgba16float'
for s in (acc_pl, til, brt, blt, trt, rc, tl, tb, tb2, tb3, tr_, bsw):   # TD Composite: first input is on top
    s.outputConnectors[0].connect(comp)
finish_v2(c, COMP, comp, bsw)
report(c)
