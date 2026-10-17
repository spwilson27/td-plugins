# ---- v3 shared helpers (pasted at top of each build.py) ----
import os, re, td
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
    """vecs: list of (uniformName, [4 values/exprs]); exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:
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

def look_pg(c):
    add_pars(c, [('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
                 ('Accent', 'float', 0.0, 0, 1)], page='Look')

LOOK_VECS = [('uM', [0, 'parent(2).par.Look.menuIndex', 'parent(2).par.Accent', 0])]

def demo_src(c, comp, fn='src.glsl', bg=1.0, vecs=None, fmt='rgba16float'):
    """in1 + gated `demo` COMP (preview-only source) -> Switch TOP 'src'.
    The switch picks the demo only while in1 is unconnected, so the demo does not cook otherwise."""
    i = c.create(td.inTOP, 'in1')
    d = c.create(td.baseCOMP, 'demo')
    d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
    if vecs is None:
        vecs = [('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])] + LOOK_VECS
    g = glsl(d, 'defsrc', rd(comp, fn), vecs=vecs, fmt=fmt)
    setres(g, 'parent(2).par.Resolutionw', 'parent(2).par.Resolutionh')
    o = d.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(g); o.par.label = 'demo source'
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"   # in1.width: re-evaluate when a TOP is plugged in
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

_RW = "[parent().op('in1').width, parent().par.Resolutionw][0 if (parent().par.Resolutionmode=='input' and len(parent().inputConnectors[0].connections)) else 1]"
_RH = "[parent().op('in1').height, parent().par.Resolutionh][0 if (parent().par.Resolutionmode=='input' and len(parent().inputConnectors[0].connections)) else 1]"
_CH = lambda n: "parent().op('mod')['%s'].eval()" % n

def _subexpr(c, pat, fn):
    rx = re.compile(pat)
    for o in [c] + c.findChildren():
        for p in o.pars():
            if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                p.expr = rx.sub(fn, p.expr)

def v3_finish(c, name, dry='src', mod=(), selfmix=False, outlabels=None):
    ctl = c.appendCustomPage('Controls')
    if not hasattr(c.par, 'Mix'):
        p = ctl.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    ctl.appendToggle('Bypass')
    p = ctl.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"
    nin = len([o for o in c.children if o.OPType in ('inTOP', 'inSOP', 'inPOP')])
    im = c.create(td.inCHOP, 'in%d' % (nin + 1))
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im)
    mg.inputConnectors[1].connect(mz); mg.par.duplicate = 'first'; mg.par.align = 'start'
    _subexpr(c, r"parent\(\)\.par\.Resolutionw\b", lambda m: _RW)
    _subexpr(c, r"parent\(\)\.par\.Resolutionh\b", lambda m: _RH)
    for pn, tmpl in mod:
        rx = re.compile(r"parent\(\)\.par\.%s\b" % pn)
        hit = 0
        for g in c.findChildren(type=td.glslTOP):
            for p in g.pars():
                if p.mode == ParMode.EXPRESSION and rx.search(p.expr):
                    p.expr = rx.sub(lambda m: tmpl.format(v=m.group(0), b1=_CH('band1'), b2=_CH('band2'), b3=_CH('band3'), b4=_CH('band4'), beat=_CH('beat')), p.expr); hit += 1
        assert hit, 'mod target not found: ' + pn
    o1 = c.op('out1')
    res = o1.inputConnectors[0].connections[0].owner
    d = c.op(dry)
    if not selfmix:
        x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(d); x.inputConnectors[1].connect(res)
        x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'
        x.par.outputresolution = 'useinput'
        res = x
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(res); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "(1 if (parent().par.Bypass and len(parent().inputConnectors[0].connections)) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
    o1.inputConnectors[0].connect(bp)
    o1.comment = 'result'
    for k, v in (outlabels or {}).items(): c.op(k).comment = v
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)
# ---- end helpers ----
COMP = 'TOP_glitch'
c = new_comp(COMP)
add_pars(c, [
    ('Amount', 'float', 1.0, 0, 2),
    ('Seed', 'float', 1.0, 0, 100),
    ('Rate', 'float', 3.0, 0, 30),
    ('Rgbsplit', 'float', 0.5, 0, 1),
    ('Blockdisplace', 'float', 0.5, 0, 1),
    ('Scanlinetear', 'float', 0.4, 0, 1),
    ('Pixelsort', 'float', 0.35, 0, 1),
    ('Smear', 'float', 0.35, 0, 1),
    ('Sortthreshold', 'float', 0.45, 0, 2),
    ('Sortaxis', 'menu', [('horizontal', 'Horizontal'), ('vertical', 'Vertical')], 0),
    ('Smearthreshold', 'float', 0.08, 0.001, 1),
    ('Smearblock', 'float', 16, 2, 64),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
look_pg(c)
# --- native-node helper (pasted into the body of native build.py files) ---
def nat(c, typ, name, *ins, fmt='rgba16float', **kw):
    """Create a native op, wire inputs, set pars. A str value starting with '=' is an expression."""
    o = c.create(getattr(td, typ), name)
    for i, s in enumerate(ins):
        if s is not None: o.inputConnectors[i].connect(s)
    if fmt and hasattr(o.par, 'format'): o.par.format = fmt
    for k, v in kw.items():
        p = o.par[k]
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        elif isinstance(v, str): p.val = v
        else: p.val = v
    return o

P = 'parent().par.'
# ---------------- demo (preview only): bar + five discs on a noisy grid, all native TOPs ----------------
i1 = c.create(td.inTOP, 'in1')
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
LOOKM = "parent(2).par.Look.menuIndex"; ACC = "parent(2).par.Accent"
def dres(o):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = 'parent(2).par.Resolutionw'; o.par.resolutionh.expr = 'parent(2).par.Resolutionh'; return o
def dn(typ, name, *ins, **kw): return dres(nat(d, typ, name, *ins, **kw))
bg0 = dn('noiseTOP', 'bg_noise', type='simplex3d', period=0.6, amp=0.03, offset=0.07, mono=False, tz="=absTime.seconds*0.03")
def stripes(name, kind):
    r = dn('rampTOP', name + '_ramp', type=kind, period=1 / 14.0, extendleft='repeat', extendright='sameasleft')
    return dn('thresholdTOP', name, r, threshold=0.5, comparator='less')
sx, sy = stripes('stripes_x', 'horizontal'), stripes('stripes_y', 'vertical')
chk0 = dn('compositeTOP', 'checker', sx, sy, operand='difference')
chk = dn('levelTOP', 'grid_level', chk0, brightness1=0.06)
tint = dn('compositeTOP', 'bg', bg0, chk, operand='add')
tint.par.format = 'rgba16float'
def hue(h):   # python expression string of an rgb tuple member in TD expression language
    return h
layers = [tint]
def colr(i, base_h, sat, val, ch):
    # hue to rgb channel in an expression; mono look gives bone-white greys
    off = {'r': 0.0, 'g': 2.0/3.0, 'b': 1.0/3.0}[ch]
    k = "max(0,min(1,abs(((%s+%f)%%1)*6-3)-1))" % (base_h, off)
    colv = "(%f*(1-%f+%f*%s))" % (val, sat, sat, k)
    grey = "(%f*0.9*%s)" % (val * (0.35 + 0.65 * ((base_h_val(i)*3) % 1)), {'r': '0.96', 'g': '0.94', 'b': '0.89'}[ch])
    return "=(%s if %s else %s)" % (grey, LOOKM + '==1', colv)
def base_h_val(i): return 0.12 * i
bar = dn('rectangleTOP', 'bar', sizex=0.47, sizey=0.06, sizeunit='fractionaspect' if False else 'fraction', centery=-0.18, rotate="=-absTime.seconds*0.7*57.2958",
         fillcolorr="=(3*(0.96*(1-%s)+%s) if %s==1 else 0.9)" % (ACC, ACC, LOOKM), fillcolorg="=(3*(0.94*(1-%s)+0.04*%s) if %s==1 else 2.7)" % (ACC, ACC, LOOKM),
         fillcolorb="=(3*(0.89*(1-%s)+0.04*%s) if %s==1 else 3.0)" % (ACC, ACC, LOOKM), fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=0)
layers.append(bar)
for i in range(5):
    t = "absTime.seconds"
    cx = "=math.sin(%s*(0.35+0.11*%d)+%d*1.7)*0.44" % (t, i, i)
    cy = "=math.cos(%s*(0.27+0.09*%d)+%d*2.3)*0.33" % (t, i, i)
    r = (0.11 + 0.025 * i) * 0.5625      # circle radii are fractions of the width (720/1280 of the height)
    hh = "(%f+%s*0.03)" % (0.12 * i, t)
    ring = dn('circleTOP', 'disc%d' % i, radiusx=r, radiusy=r, softness=0.004, centerx=cx, centery=cy, bgalpha=0,
              fillcolorr=colr(i, hh, 0.85, 0.6, 'r'), fillcolorg=colr(i, hh, 0.85, 0.6, 'g'), fillcolorb=colr(i, hh, 0.85, 0.6, 'b'), fillalpha=1,
              bgcolorr=0, bgcolorg=0, bgcolorb=0)
    core = dn('circleTOP', 'core%d' % i, radiusx=r * 0.45, radiusy=r * 0.45, softness=r * 0.45, centerx=cx, centery=cy,
              fillcolorr=3.0, fillcolorg=2.7, fillcolorb=2.1, fillalpha=1, bgalpha=0, bgcolorr=0, bgcolorg=0, bgcolorb=0)
    layers += [ring, core]
dem = dn('compositeTOP', 'objects', *reversed(layers[1:]), operand='over')      # first input is on top
demsum = dn('compositeTOP', 'scene', dem, tint, operand='over')
do = d.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(demsum); do.par.label = 'demo source'
src = nat(c, 'switchTOP', 'src', d.outputConnectors[0], i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame + 0*parent().op('in1').width"
setres(src)

fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(src)
fb.par.format = 'rgba16float'; setres(fb)
fb.par.reset.expr = 'parent().par.Reset'
g = glsl(c, 'glitch', rd(COMP, 'glitch.glsl'), inputs=[src, fb], res=True, vecs=[
    ('uG', ['parent().par.Amount', 'parent().par.Seed', 'absTime.seconds', 'parent().par.Rate']),
    ('uA', ['parent().par.Rgbsplit', 'parent().par.Blockdisplace', 'parent().par.Scanlinetear', 'parent().par.Pixelsort']),
    ('uB', ['parent().par.Smear', 'parent().par.Smearthreshold', 'parent().par.Sortthreshold', 'parent().par.Sortaxis.menuIndex']),
    ('uC', ['parent().par.Smearblock', 'parent().par.Active', 0, 0]),
])
g.par.inputextenduv = 'mirror'
nul = c.create(td.nullTOP, 'fb_out'); nul.inputConnectors[0].connect(g)
fb.par.top = nul
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(nul)
v3_finish(c, COMP, mod=[('Amount','({v}*(1+{b1}+{beat}))')])
report(c)
