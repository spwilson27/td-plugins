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

NAME = 'GEN_reaction_diffusion'
HERE = os.path.expanduser('~/software/td-plugins/components/' + NAME)
def rd(f): return open(os.path.join(HERE, f)).read()

root = op('/')
bld = root.op('build') or root.create(td.baseCOMP, 'build')
old = bld.op(NAME)
if old: old.destroy()
c = bld.create(td.baseCOMP, NAME)

# ---------- helpers ----------
def text(name, s):
    t = c.create(td.textDAT, name); t.text = s; return t
def glsl(name, dat, fmt='rgba32float', inputs=(), vecs=(), passes=None):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = dat
    g.par.format = fmt
    g.par.outputresolution = 'custom'
    g.par.resolutionw.expr = "parent().par.Resolutionw"
    g.par.resolutionh.expr = "parent().par.Resolutionh"
    for i, s in enumerate(inputs): g.inputConnectors[i].connect(s)
    g.seq.vec.numBlocks = len(vecs)
    for i, (n, exprs) in enumerate(vecs):
        getattr(g.par, f'vec{i}name').val = n
        for j, e in enumerate(exprs):
            getattr(g.par, f'vec{i}value' + 'xyzw'[j]).expr = e
    if passes: g.par.npasses.expr = passes
    return g

# ---------- custom pars ----------
p = c.appendCustomPage('Controls')
m = p.appendMenu('Preset', label='Preset')[0]
names = ['custom', 'coral', 'mitosis', 'labyrinth', 'spots', 'worms']
m.menuNames = names; m.menuLabels = [n.capitalize() for n in names]; m.default = 'coral'; m.val = 'coral'
f = p.appendFloat('Feed', label='Feed')[0]; f.min = 0; f.max = 0.1; f.normMin = 0.01; f.normMax = 0.09; f.default = 0.0545; f.val = 0.0545
k = p.appendFloat('Kill', label='Kill')[0]; k.min = 0; k.max = 0.1; k.normMin = 0.04; k.normMax = 0.08; k.default = 0.062; k.val = 0.062
for n, lab, d in (('Diffa', 'Diffusion A', 1.0), ('Diffb', 'Diffusion B', 0.5)):
    q = p.appendFloat(n, label=lab)[0]; q.min = 0; q.max = 2; q.normMax = 1.2; q.default = d; q.val = d
q = p.appendInt('Steps', label='Steps')[0]; q.min = 1; q.max = 100; q.normMax = 40; q.default = 12; q.val = 12
q = p.appendToggle('Play', label='Play')[0]; q.default = 1; q.val = 1
p.appendPulse('Reset', label='Reset')
q = p.appendWH('Resolution', label='Resolution'); q[0].default = 1280; q[1].default = 720; q[0].val = 1280; q[1].val = 720
q[0].min = q[1].min = 16; q[0].clampMin = q[1].clampMin = True

p2 = c.appendCustomPage('Render')
defs = {'Color1': (0.02, 0.02, 0.10), 'Color2': (0.05, 0.35, 0.55), 'Color3': (0.95, 0.55, 0.15), 'Color4': (1.0, 0.97, 0.85)}
for n, d in defs.items():
    q = p2.appendRGB(n, label=n)
    for par, v in zip(q, d): par.default = v; par.val = v
q = p2.appendFloat('Contrast', label='Contrast')[0]; q.default = 1.7; q.val = 1.7; q.min = 0; q.normMax = 6
q = p2.appendFloat('Bump', label='Bump')[0]; q.default = 6; q.val = 6; q.min = 0; q.normMax = 20

p3 = c.appendCustomPage('Sim')
q = p3.appendFloat('Loopmod', label='Loop Modulation')[0]; q.default = q.val = 0.0; q.min = 0; q.max = 0.5; q.normMax = 0.2
q = p3.appendFloat('Dt', label='Time Step')[0]; q.default = 1.0; q.val = 1.0; q.min = 0.01; q.max = 1.5
q = p3.appendInt('Seed', label='Seed')[0]; q.default = 1; q.val = 1; q.min = 0; q.normMax = 100

# ---------- network ----------
inn = c.create(td.inTOP, 'in1')
d_init = text('init_glsl', rd('init.glsl'))
d_sim = text('sim_glsl', rd('sim.glsl'))
d_col = text('color_glsl', rd('color.glsl'))

init = glsl('init', d_init, inputs=[inn], vecs=[
    ('uHasIn', ["1 if len(parent().inputConnectors[0].connections) else 0"]),
    ('uRes', ["parent().par.Resolutionw", "parent().par.Resolutionh"]),
    ('uSeed', ["parent().par.Seed"]),
])
fb = c.create(td.feedbackTOP, 'feedback')
fb.par.format = 'rgba32float'
fb.inputConnectors[0].connect(init)
sim = glsl('sim', d_sim, inputs=[fb], vecs=[
    ('uFeed', ["parent().par.Feed * (1 + parent().par.Loopmod * math.sin(2*math.pi*" + PHX + ") + 0.15*op('modlib').module.m('band1'))"]),
    ('uKill', ["parent().par.Kill * (1 + parent().par.Loopmod * math.cos(2*math.pi*" + PHX + "))"]),
    ('uDa', ["parent().par.Diffa"]), ('uDb', ["parent().par.Diffb"]),
    ('uDt', ["parent().par.Dt"]), ('uPlay', ["parent().par.Play"]),
], passes="max(1, int(parent().par.Steps))")
state = c.create(td.nullTOP, 'state'); state.par.format = 'rgba32float'
state.inputConnectors[0].connect(sim)
fb.par.top = state

def col(n): return [f"parent().par.{n}r", f"parent().par.{n}g", f"parent().par.{n}b"]
color = glsl('color', d_col, fmt='rgba8fixed', inputs=[state], vecs=[
    ('uC0', col('Color1')), ('uC1', col('Color2')), ('uC2', col('Color3')), ('uC3', col('Color4')),
    ('uContrast', ["parent().par.Contrast"]), ('uBump', ["parent().par.Bump"]),
])
o1 = c.create(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(color)
o2 = c.create(td.nullTOP, 'out2'); o2.par.format = 'rgba32float'; o2.inputConnectors[0].connect(state)
o1.viewer = True

# ---------- callbacks ----------
cb = text('callbacks', '''
PRESETS = {'coral': (0.0545, 0.062), 'mitosis': (0.0367, 0.0649), 'labyrinth': (0.029, 0.057),
           'spots': (0.03, 0.0625), 'worms': (0.078, 0.061)}
def onValueChange(par, prev):
    if par.name == 'Preset' and par.eval() in PRESETS:
        fe, ki = PRESETS[par.eval()]
        par.owner.par.Feed = fe
        par.owner.par.Kill = ki
def onPulse(par):
    if par.name == 'Reset':
        par.owner.op('feedback').par.resetpulse.pulse()
''')
pe = c.create(td.parameterexecuteDAT, 'parexec')
pe.par.op = '..'
pe.par.pars = 'Preset Reset'
pe.par.valuechange = True
pe.par.onpulse = True
pe.par.custom = True
pe.par.builtin = False
pe.par.active = True
pe.par.pars = 'Preset Reset'
pe.text = cb.text


c.op('out1').comment = 'render'
c.op('out2').comment = 'state'
retro(c, accmode=1)
for i, o in enumerate(c.children):
    o.nodeX = 200 * (i % 6); o.nodeY = -150 * (i // 6)
c.par.opviewer = o1
c.save(os.path.expanduser('~/software/td-plugins/tox/_raw/%s.tox' % NAME))
print('saved')
