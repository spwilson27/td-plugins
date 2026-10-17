import os, td
# RETRO BEGIN (v2: Loop page + Clock CHOP + optional modulation In CHOP + Look menu)
MODLIB = '''# modulation helpers: m(name) reads a channel (band1-4, beat, phase) of the optional In CHOP, else default
def _ins():
    return [o for o in parent().children if o.OPType == 'inCHOP']
def m(n, d=0.0):
    i = _ins()
    if not i: return d
    ch = i[0][n]
    return ch.eval() if ch is not None else d
def clk():
    # phase 0..1 from the Clock CHOP's 'phase' channel (None if no Clock set / channel missing)
    c = parent().par.Clock.eval()
    if c is None: return None
    ch = c['phase']
    return ch.eval() if ch is not None else None
def phase():
    c = clk()
    return (c if c is not None else parent().par.Phase.eval()) % 1.0
'''
LOOKGLSL = open(os.path.expanduser('~/software/td-plugins/components/_retro/look.glsl')).read()
def retro(c, accmode=0, gain=1.0, out='out1', rst='Reset', looksrc=None):
    import math
    ctl = [p for p in c.customPages if p.name == 'Controls'][0]
    m = ctl.appendMenu('Look', label='Look')[0]
    m.menuNames = ['original', 'mono']; m.menuLabels = ['Original', 'Mono (Rendah)']
    m.default = 'original'; m.val = 'original'
    t = ctl.appendToggle('Accent', label='Red Accent (Mono)')[0]; t.default = 0; t.val = 0
    g = ctl.appendFloat('Monogain', label='Mono Gain')[0]; g.default = g.val = gain; g.min = 0.05; g.max = 8; g.normMin = 0.2; g.normMax = 4
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]
    p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute Time', 'Phase (external)']; p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.default = 0; p.val = 0
    pg.appendCHOP('Clock', label='Clock CHOP (phase)')
    p = pg.appendFloat('Loopseconds')[0]; p.min = 0.5; p.max = 120; p.normMin = 1; p.normMax = 60; p.clampMin = True; p.default = 8.0; p.val = 8.0
    p = pg.appendInt('Loopbeats')[0]; p.min = 0; p.max = 256; p.normMin = 0; p.normMax = 64; p.clampMin = True; p.default = 0; p.val = 0
    p = pg.appendFloat('Bpm')[0]; p.min = 20; p.max = 300; p.normMin = 60; p.normMax = 200; p.default = 120; p.val = 120
    p = pg.appendToggle('Loopreset')[0]; p.default = 0; p.val = 0
    # modulation In CHOP: last input
    nin = len([o for o in c.children if o.OPType in ('inTOP', 'inPOP', 'inSOP', 'inCHOP', 'inDAT')])
    mi = c.create(td.inCHOP, 'in%d' % (nin + 1))
    ml = c.create(td.textDAT, 'modlib'); ml.text = MODLIB
    P = 'parent().par.'
    L = "(%sLoopbeats*60.0/%sBpm if %sLoopbeats>0 else %sLoopseconds)" % (P, P, P, P)
    k = c.create(td.constantCHOP, 'clock')
    k.par.name0 = 'len'; k.par.value0.expr = L
    k.par.name1 = 'ph'
    k.par.value1.expr = "op('modlib').module.phase() if %sTimesource=='phase' else ((absTime.seconds/%s) %% 1.0)" % (P, L)
    k.par.name2 = 't'
    k.par.value2.expr = "(op('modlib').module.phase()*%s) if %sTimesource=='phase' else absTime.seconds" % (L, P)
    o = c.op(out)
    src = looksrc or o.inputs[0]
    lk = c.create(td.glslTOP, 'look')
    lk.par.pixeldat = c.create(td.textDAT, 'look_glsl')
    lk.par.pixeldat.eval().text = LOOKGLSL
    lk.inputConnectors[0].connect(src)
    lk.par.outputresolution = 'useinput'
    lk.par.format = 'rgba16float'
    lk.seq.vec.numBlocks = 1
    lk.par.vec0name = 'uL'
    lk.par.vec0valuex.expr = "1 if parent().par.Look=='mono' else 0"
    lk.par.vec0valuey.expr = "parent().par.Accent"
    lk.par.vec0valuez.val = accmode
    lk.par.vec0valuew.expr = "parent().par.Monogain"
    o.inputConnectors[0].connect(lk)
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    if not c.par.Loopreset.eval(): return\n"
              "    ph = op('clock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if ph < prev - 0.5:\n"
              "        c.par.%s.pulse()\n"
              "    return\n" % rst)
    e.par.framestart = True; e.par.active = True
PHX = "op('clock')['ph']"      # wrapped loop phase 0..1
TX = "op('clock')['t']"        # loop-aware seconds
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)
# RETRO END

NAME = 'GEN_cellular_automata'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')

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
    pg = (page.appendInt if isint else page.appendFloat)(name, label=label)
    p = pg[0]; p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
def menu(page, name, label, names, labels, default=0):
    p = page.appendMenu(name, label=label)[0]; p.menuNames = names; p.menuLabels = labels; p.val = names[default]; p.default = names[default]
def rgb(page, name, label, col):
    pg = page.appendRGB(name, label=label)
    for p, v in zip(pg, col): p.default = v; p.val = v

# ---- custom parameters
P = c.appendCustomPage('Controls')
menu(P, 'Rule', 'Rule', ['life', 'brain', 'wireworld', 'ltl', 'custom'],
     ['Game of Life', "Brian's Brain", 'Wireworld', 'Larger than Life', 'Custom B/S'])
rs = P.appendStr('Rulestring', label='B/S Rule'); rs[0].default = 'B3/S23'; rs[0].val = 'B3/S23'
num(P, 'Radius', 'LtL Radius', 5, 1, 15, isint=True)
num(P, 'Density', 'Density', 0.3, 0, 1)
num(P, 'Stepsperframe', 'Steps / Frame', 1, 1, 16, chi=False, isint=True)
num(P, 'Rate', 'Rate (steps/s)', 30, 1, 60)
P.appendToggle('Play', label='Play'); c.par.Play = True; c.par.Play.default = True
P.appendPulse('Reset', label='Reset')
R = c.appendCustomPage('Render')
num(R, 'Cellsize', 'Cell Size (px)', 4, 1, 32, isint=True)
menu(R, 'Coloring', 'Coloring', ['flat', 'age'], ['Flat', 'By Age'], 1)
num(R, 'Agerange', 'Age Range', 40, 1, 500, chi=False)
num(R, 'Ghost', 'Ghost Trail', 0.6, 0, 1)
num(R, 'Ghostdecay', 'Ghost Decay', 0.9, 0.5, 0.99)
rgb(R, 'Colordead', 'Dead', (0.02, 0.02, 0.06))
rgb(R, 'Coloralive', 'Alive (young)', (0.3, 1.0, 0.9))
rgb(R, 'Colorold', 'Old / Tail', (0.9, 0.2, 0.7))
rgb(R, 'Coloraux', 'Dying / Conductor', (1.0, 0.65, 0.1))
S = c.appendCustomPage('Sim')
pg = S.appendWH('Resolution', label='Resolution')
for p, v in zip(pg, (1280, 720)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096
num(S, 'Seed', 'Seed', 1, 0, 1000, isint=True)
num(S, 'Loopinject', 'Loop Injector Density', 0.0, 0, 1)
num(S, 'Injectradius', 'Injector Radius', 0.08, 0.01, 0.5)
num(S, 'Ltlbirthlo', 'LtL Birth Min', 0.28, 0, 1); num(S, 'Ltlbirthhi', 'LtL Birth Max', 0.38, 0, 1)
num(S, 'Ltlsurvlo', 'LtL Survive Min', 0.28, 0, 1); num(S, 'Ltlsurvhi', 'LtL Survive Max', 0.48, 0, 1)

rules = dat('rules', rd('rules.py'))
RB = "op('rules').module.bs(parent().par.Rule.menuIndex, parent().par.Rulestring.eval())"

gw = "max(1, int(parent().par.Resolutionw // parent().par.Cellsize))"
gh = "max(1, int(parent().par.Resolutionh // parent().par.Cellsize))"
inn = mk(td.inTOP, 'in1')
zero = mk(td.constantTOP, 'zero', outputresolution='custom', format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
fb = mk(td.feedbackTOP, 'fb', outputresolution='custom', format='rgba32float')
st = mk(td.glslTOP, 'state', outputresolution='custom', format='rgba32float', inputfiltertype='nearest')
for o in (zero, fb, st):
    o.par.resolutionw.expr = gw; o.par.resolutionh.expr = gh
st.par.pixeldat = dat('state_pix', rd('state.glsl'))
fb.inputConnectors[0].connect(zero)
st.inputConnectors[0].connect(fb); st.inputConnectors[1].connect(inn)
fb.par.top = st.name
fb.par.reset.expr = "parent().par.Reset"
st.par.npasses.expr = "parent().par.Stepsperframe"
vec(st, 0, 'uA', "parent().par.Rule.menuIndex", "parent().par.Reset", "parent().par.Density",
    "1 if (parent().par.Play and absTime.frame % max(1, round(60 / parent().par.Rate)) == 0) else 0")
vec(st, 1, 'uB', RB + "[0]", RB + "[1]", "parent().par.Radius", "1 if len(parent().inputConnectors[0].connections) else 0")
vec(st, 2, 'uC', "parent().par.Ltlbirthlo", "parent().par.Ltlbirthhi", "parent().par.Ltlsurvlo", "parent().par.Ltlsurvhi")
vec(st, 3, 'uD', "parent().par.Ghostdecay", "parent().par.Seed")

col = mk(td.glslTOP, 'color', outputresolution='custom', format='rgba16float', inputfiltertype='nearest')
col.par.resolutionw.expr = "parent().par.Resolutionw"; col.par.resolutionh.expr = "parent().par.Resolutionh"
col.par.pixeldat = dat('color_pix', rd('color.glsl'))
col.inputConnectors[0].connect(st)
for i, n in enumerate(('dead', 'alive', 'old', 'aux')):
    vec(col, i, 'uCol%d' % i, *["parent().par.Color%s%s" % (n, ch) for ch in 'rgb'])
vec(col, 4, 'uM', "parent().par.Rule.menuIndex", "1 if parent().par.Coloring == 'age' else 0", "parent().par.Agerange", "parent().par.Ghost")
vec(st, 4, 'uE', "max(parent().par.Loopinject, 0.4*op('modlib').module.m('beat'))", "0.5+0.3*math.cos(2*math.pi*" + PHX + ")", "0.5+0.3*math.sin(2*math.pi*" + PHX + ")", "parent().par.Injectradius")
o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(col)
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(st)
c.op('out1').comment = 'render'
c.op('out2').comment = 'state'
retro(c, accmode=0, gain=1.2)
c.save(OUT); print('saved')
