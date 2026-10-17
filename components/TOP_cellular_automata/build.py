import os, td
NAME = 'TOP_cellular_automata'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')

MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat) of the optional modulation In CHOP, else default
def m(n, d=0.0):
    i = [o for o in parent().children if o.OPType == 'inCHOP']
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
'''

def rd(f): return open(D + f).read()
root = op('/build') or op('/').create(td.baseCOMP, 'build')
old = root.op(NAME)
if old: old.destroy()
c = root.create(td.baseCOMP, NAME)

def mk(t, name, **kw):
    o = c.create(t, name)
    for k, v in kw.items(): o.par[k] = v
    return o
def dat(name, text):
    d = c.create(td.textDAT, name); d.text = text; return d
def vec(o, i, name, *exprs):
    o.par['vec%dname' % i] = name
    for k, e in zip('xyzw', exprs): o.par['vec%dvalue%s' % (i, k)].expr = e
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False):
    p = (page.appendInt if isint else page.appendFloat)(name, label=label)[0]
    p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
def menu(page, name, label, names, labels, default=0):
    p = page.appendMenu(name, label=label)[0]; p.menuNames = names; p.menuLabels = labels; p.val = names[default]; p.default = names[default]
def rgb(page, name, label, col):
    for p, v in zip(page.appendRGB(name, label=label), col): p.default = v; p.val = v

# ---- parameters
P = c.appendCustomPage('Controls')
num(P, 'Mix', 'Mix', 1.0, 0, 1)
P.appendToggle('Bypass', label='Bypass')
menu(P, 'Resolutionmode', 'Resolution Mode', ['input', 'custom'], ['Follow input', 'Custom'])
pg = P.appendWH('Resolution', label='Resolution')
for p, v in zip(pg, (1280, 720)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096
c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"
menu(P, 'Rule', 'Rule', ['life', 'brain', 'wireworld', 'ltl', 'custom'],
     ['Game of Life', "Brian's Brain", 'Wireworld', 'Larger than Life', 'Custom B/S'])
rs = P.appendStr('Rulestring', label='B/S Rule'); rs[0].default = 'B3/S23'; rs[0].val = 'B3/S23'
P.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
num(P, 'Rate', 'Rate (steps/s)', 30, 1, 60)
num(P, 'Stepsperframe', 'Steps / Frame', 1, 1, 16, chi=False, isint=True)
P.appendPulse('Reset', label='Reset (reseed from input)')

I = c.appendCustomPage('Input')
num(I, 'Threshold', 'Threshold', 0.4, 0, 1)
I.appendToggle('Invert', label='Invert (dark seeds)')
num(I, 'Density', 'Seed Density', 0.4, 0, 1)
num(I, 'Inject', 'Inject Amount', 0.02, 0, 1)
num(I, 'Seed', 'Seed', 1, 0, 1000, isint=True)

R = c.appendCustomPage('Render')
num(R, 'Cellsize', 'Cell Size (px)', 6, 1, 32, isint=True)
menu(R, 'Coloring', 'Coloring', ['input', 'age', 'flat'], ['Input colours', 'By Age', 'Flat'])
num(R, 'Backdrop', 'Input Backdrop', 0.25, 0, 1)
num(R, 'Vivid', 'Vivid', 0.6, 0, 1)
num(R, 'Cellgap', 'Cell Gap', 0.0, 0, 0.8)
num(R, 'Agerange', 'Age Range', 40, 1, 500, chi=False)
num(R, 'Ghost', 'Ghost Trail', 0.6, 0, 1)
num(R, 'Ghostdecay', 'Ghost Decay', 0.9, 0.5, 0.99)
rgb(R, 'Colordead', 'Dead (age/flat)', (0.02, 0.02, 0.06))
rgb(R, 'Coloralive', 'Alive (young)', (0.3, 1.0, 0.9))
rgb(R, 'Colorold', 'Old / Tail', (0.9, 0.2, 0.7))
rgb(R, 'Coloraux', 'Dying / Conductor', (1.0, 0.65, 0.1))

S = c.appendCustomPage('Sim')
num(S, 'Radius', 'LtL Radius', 5, 1, 15, isint=True)
num(S, 'Ltlbirthlo', 'LtL Birth Min', 0.28, 0, 1); num(S, 'Ltlbirthhi', 'LtL Birth Max', 0.38, 0, 1)
num(S, 'Ltlsurvlo', 'LtL Survive Min', 0.28, 0, 1); num(S, 'Ltlsurvhi', 'LtL Survive Max', 0.48, 0, 1)

rules = dat('rules', rd('rules.py'))
dat('modlib', MODLIB)
RB = "op('rules').module.bs(parent().par.Rule.menuIndex, parent().par.Rulestring.eval())"
M = lambda n: "op('modlib').module.m('%s')" % n

# ---- source: in1, or the gated demo
inn = mk(td.inTOP, 'in1')
demo = c.create(td.baseCOMP, 'demo')
# ---- native demo helpers: Constant / Ramp / Noise / Circle / Rectangle / Composite TOPs (no GLSL) ----
def nd_set(o, **kw):
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): o.par[k].expr = v[1:]
        else: o.par[k] = v
    return o
def nd_res(o, W, H):
    o.par.outputresolution = 'custom'; o.par.format = 'rgba16float'
    for k, v in (('resolutionw', W), ('resolutionh', H)):
        if isinstance(v, str): o.par[k].expr = v
        else: o.par[k] = v
    return o
def nd_s(v, W, H):
    """Lengths below are in units of the picture HEIGHT (centre = 0); Circle/Rectangle 'fractionaspect' units are relative to the WIDTH, so scale by H/W."""
    if not isinstance(W, str) and not isinstance(H, str): return v * H / W if not isinstance(v, str) else '=(%s)*%s' % (v[1:], H / W)
    return '=(%s)*(%s)/(%s)' % (v[1:] if isinstance(v, str) else repr(v), H, W)
def nd_const(d, name, W, H, col):
    o = d.create(td.constantTOP, name); nd_res(o, W, H)
    return nd_set(o, colorr=col[0], colorg=col[1], colorb=col[2], alpha=1)
def nd_ramp(d, name, W, H, stops, kind='vertical'):
    """stops: [(pos, (r,g,b)), ...]"""
    t = d.create(td.tableDAT, name + '_stops'); t.clear()
    t.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for p, c in stops: t.appendRow([p, c[0], c[1], c[2], 1])
    o = d.create(td.rampTOP, name); nd_res(o, W, H); o.par.type = kind; o.par.dat = t
    return o
def nd_circle(d, name, W, H, cx, cy, r, col, soft=0.003, ring=0, alpha=1.0, **kw):
    """cx, cy, r in 'fraction (aspect)' units (screen height = 1, centre = 0); ring > 0 draws an outline instead of a disc."""
    o = d.create(td.circleTOP, name); nd_res(o, W, H)
    nd_set(o, centerunit='fractionaspect', radiusunit='fractionaspect', softnessunit='fractionaspect', borderwidthunit='fractionaspect',
           centerx=nd_s(cx, W, H), centery=nd_s(cy, W, H), radiusx=nd_s(r, W, H), radiusy=nd_s(r, W, H), softness=nd_s(soft, W, H), bgalpha=0, **kw)
    if ring:
        nd_set(o, fillalpha=0, borderwidth=nd_s(ring, W, H), borderr=col[0], borderg=col[1], borderb=col[2], borderalpha=alpha)
    else:
        nd_set(o, fillcolorr=col[0], fillcolorg=col[1], fillcolorb=col[2], fillalpha=alpha, borderalpha=0)
    return o
def nd_rect(d, name, W, H, cx, cy, sx, sy, col, rot=0, soft=0.002, alpha=1.0, **kw):
    o = d.create(td.rectangleTOP, name); nd_res(o, W, H)
    return nd_set(o, centerunit='fractionaspect', sizeunit='fractionaspect', softnessunit='fractionaspect', centerx=nd_s(cx, W, H), centery=nd_s(cy, W, H), sizex=nd_s(sx, W, H), sizey=nd_s(sy, W, H), rotate=rot,
                  softness=nd_s(soft, W, H), bgalpha=0, fillcolorr=col[0], fillcolorg=col[1], fillcolorb=col[2], fillalpha=alpha, borderalpha=0, **kw)
def nd_over(d, name, W, H, layers, operand='over'):
    o = d.create(td.compositeTOP, name); nd_res(o, W, H); o.par.operand = operand
    for l in reversed(layers): l.outputConnectors[0].connect(o)   # Composite: first input is on top, so connect the topmost layer first
    return o

def _nd_demo(demo):
    import math
    W, H, T = "parent(2).par.Resolutionw", "parent(2).par.Resolutionh", "absTime.seconds"
    lay = [nd_const(demo, 'bg', W, H, (0.02, 0.02, 0.05))]
    for i in range(4):   # four drifting discs, each with an orbit ring
        hue = [0.25 + 0.75 * (0.5 + 0.5 * math.cos(6.2831 * (i / 4.0 + k))) for k in (0.0, 0.33, 0.67)]
        cx = "=0.42*math.sin(%s*(0.4+0.13*%d)+%d*1.7)" % (T, i, i)
        cy = "=0.25*math.cos(%s*(0.33+0.1*%d)+%d*2.3)" % (T, i, i)
        lay.append(nd_circle(demo, 'disc%d' % i, W, H, cx, cy, 0.16, hue, soft=0.01))
        lay.append(nd_circle(demo, 'ring%d' % i, W, H, cx, cy, 0.24, [h * 0.9 for h in hue], ring=0.012, soft=0.004, alpha=0.9))
    return nd_over(demo, 'comp', W, H, lay)
dg = _nd_demo(demo)
dout = demo.create(td.outTOP, 'out1'); dout.inputConnectors[0].connect(dg)
src = mk(td.switchTOP, 'src', format='rgba16float')
src.inputConnectors[0].connect(demo.outputConnectors[0]); src.inputConnectors[1].connect(inn)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

RW = "(op('src').width if parent().par.Resolutionmode=='input' else parent().par.Resolutionw)"
RH = "(op('src').height if parent().par.Resolutionmode=='input' else parent().par.Resolutionh)"
gw = "max(1, int(%s // parent().par.Cellsize))" % RW
gh = "max(1, int(%s // parent().par.Cellsize))" % RH

# ---- simulation
zero = mk(td.constantTOP, 'zero', outputresolution='custom', format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
fb = mk(td.feedbackTOP, 'fb', outputresolution='custom', format='rgba32float')
st = mk(td.glslTOP, 'state', outputresolution='custom', format='rgba32float', inputfiltertype='nearest')
for o in (zero, fb, st):
    o.par.resolutionw.expr = gw; o.par.resolutionh.expr = gh
st.par.pixeldat = dat('state_pix', rd('state.glsl'))
fb.inputConnectors[0].connect(zero)
st.inputConnectors[0].connect(fb); st.inputConnectors[1].connect(src)
fb.par.top = st.name
fb.par.reset.expr = "parent().par.Reset"
st.par.npasses.expr = "parent().par.Stepsperframe"
vec(st, 0, 'uA', "parent().par.Rule.menuIndex", "parent().par.Reset", "parent().par.Density",
    "1 if (parent().par.Play and absTime.frame % max(1, round(60 / parent().par.Rate)) == 0) else 0")
vec(st, 1, 'uB', RB + "[0]", RB + "[1]", "parent().par.Radius", "parent().par.Threshold")
vec(st, 2, 'uC', "parent().par.Ltlbirthlo", "parent().par.Ltlbirthhi", "parent().par.Ltlsurvlo", "parent().par.Ltlsurvhi")
vec(st, 3, 'uD', "parent().par.Ghostdecay", "parent().par.Seed", "parent().par.Invert", "absTime.frame")
vec(st, 4, 'uE', "min(1.0, parent().par.Inject*(1+2*%s) + 0.3*%s)" % (M('band1'), M('beat')))

# ---- colour / composite
col = mk(td.glslTOP, 'color', outputresolution='custom', format='rgba16float', inputfiltertype='nearest')
col.par.resolutionw.expr = RW; col.par.resolutionh.expr = RH
col.par.pixeldat = dat('color_pix', rd('color.glsl'))
col.inputConnectors[0].connect(st); col.inputConnectors[1].connect(src)
for i, n in enumerate(('dead', 'alive', 'old', 'aux')):
    vec(col, i, 'uCol%d' % i, *["parent().par.Color%s%s" % (n, ch) for ch in 'rgb'])
vec(col, 4, 'uM', "parent().par.Rule.menuIndex", "parent().par.Coloring.menuIndex", "parent().par.Agerange", "parent().par.Ghost")
vec(col, 5, 'uN', "parent().par.Backdrop", "parent().par.Cellgap", "parent().par.Mix", "parent().par.Vivid")

bp = mk(td.switchTOP, 'bypass', format='rgba16float')
bp.inputConnectors[0].connect(col); bp.inputConnectors[1].connect(src)
bp.par.index.expr = "1 if parent().par.Bypass else 0"
o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(bp); o1.comment = 'cells over input'
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(st); o2.comment = 'raw cell state'
mi = mk(td.inCHOP, 'in2')
c.save(OUT); print('saved')
