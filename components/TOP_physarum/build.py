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

NAME = 'GEN_physarum'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')
AW = 512  # agent texture is AW x AW

def rd(f): return open(D + f).read()
root = op('/build') or op('/').create(td.baseCOMP, 'build')
old = root.op(NAME)
if old: old.destroy()
c = root.create(td.baseCOMP, NAME)

def mk(t, name, **kw):
    o = c.create(t, name)
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): o.par[k].expr = v[1:]
        else: o.par[k] = v
    return o
def dat(name, text): 
    d = c.create(td.textDAT, name); d.text = text; return d
def vec(o, i, name, *exprs):
    o.par['vec%dname' % i] = name
    for k, e in zip('xyzw', exprs): o.par['vec%dvalue%s' % (i, k)].expr = e

# ---- custom parameters
P = c.appendCustomPage('Controls')
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False):
    pg = (page.appendInt if isint else page.appendFloat)(name, label=label)
    p = pg[0]; p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo; p.normMax = hi; p.clampMin = clo; p.clampMax = chi
    return p
num(P, 'Agents', 'Agents', 120000, 1000, AW*AW, isint=True)
num(P, 'Sensorangle', 'Sensor Angle', 35, 5, 120)
num(P, 'Sensordist', 'Sensor Dist', 18, 1, 60, chi=False)
num(P, 'Turnspeed', 'Turn Speed', 25, 1, 180)
num(P, 'Stepsize', 'Step Size', 1.0, 0.1, 6, chi=False)
num(P, 'Deposit', 'Deposit', 0.5, 0.01, 5, chi=False)
num(P, 'Decay', 'Decay', 0.94, 0.8, 1.0)
num(P, 'Diffuse', 'Diffuse', 0.3, 0, 1)
num(P, 'Gain', 'Gain', 1.0, 0.1, 20, chi=False)
for n, col in (('Color1', (0.0, 0.0, 0.05)), ('Color2', (0.9, 0.2, 0.5)), ('Color3', (1.0, 0.95, 0.6))):
    pg = P.appendRGB(n); 
    for p, v in zip(pg, col): p.default = v; p.val = v
pg = P.appendMenu('Initpattern', label='Init Pattern')
pg[0].menuNames = ['random', 'disc', 'ring']; pg[0].menuLabels = ['Random', 'Disc (inward)', 'Ring (outward)']
P.appendToggle('Play', label='Play')[0].default = True; c.par.Play = True
P.appendPulse('Reset', label='Reset')
S = c.appendCustomPage('Sim')
num(S, 'Loopmod', 'Loop Modulation', 0.0, 0.0, 0.8)
pg = S.appendWH('Resolution', label='Resolution')
for p, v in zip(pg, (1280, 720)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096

# ---- agents
fbA = mk(td.feedbackTOP, 'fb_agents')
agents = mk(td.glslTOP, 'agents', outputresolution='custom', resolutionw=AW, resolutionh=AW, format='rgba32float', inputfiltertype='nearest')
agents.par.pixeldat = dat('agents_pix', rd('agents.glsl'))
fbT = mk(td.feedbackTOP, 'fb_trail', outputresolution='custom', format='rgba32float')
fbT.par.resolutionw.expr = "parent().par.Resolutionw"; fbT.par.resolutionh.expr = "parent().par.Resolutionh"
agents.inputConnectors[0].connect(fbA); agents.inputConnectors[1].connect(fbT)
fbA.par.top = agents.name
fbA.par.outputresolution = 'custom'; fbA.par.resolutionw = AW; fbA.par.resolutionh = AW; fbA.par.format = 'rgba32float'
fbA.par.reset.expr = "parent().par.Reset"; fbT.par.reset.expr = "parent().par.Reset"
vec(agents, 0, 'uP', "parent().par.Sensorangle*0.0174533*(1+parent().par.Loopmod*math.sin(2*math.pi*" + PHX + "))", "parent().par.Sensordist*(1+0.5*parent().par.Loopmod*math.cos(2*math.pi*" + PHX + "))", "parent().par.Turnspeed*0.0174533*(1+op('modlib').module.m('band2'))", "parent().par.Stepsize")
vec(agents, 1, 'uQ', "parent().par.Reset", "1 if parent().par.Play else 0", "absTime.frame", "parent().par.Initpattern.menuIndex")
zA = mk(td.constantTOP, 'zero_agents', outputresolution='custom', resolutionw=AW, resolutionh=AW, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
zT = mk(td.constantTOP, 'zero_trail', outputresolution='custom', format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
zT.par.resolutionw.expr = "parent().par.Resolutionw"; zT.par.resolutionh.expr = "parent().par.Resolutionh"
fbA.inputConnectors[0].connect(zA); fbT.inputConnectors[0].connect(zT)
agents.par.inputextenduv = 'repeat'
agents.par.inputfiltertype = 'linear'  # trail sampling is bilinear; agent texel fetches use texelFetch

# ---- deposit render (instanced points, additive)
geo = mk(td.geometryCOMP, 'deposit_geo')
for ch in list(geo.children): ch.destroy()
pt = geo.create(td.gridSOP, 'quad'); pt.par.rows = 2; pt.par.cols = 2; pt.par.sizex = 1; pt.par.sizey = 1
out = geo.create(td.outSOP, 'out1'); out.inputConnectors[0].connect(pt)
out.render = True; out.display = True
geo.par.instancing = True; geo.par.instancecountmode = 'manual'; geo.par.numinstances = AW*AW
mat = mk(td.glslMAT, 'deposit_mat', blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False, cullface='neither', glslversion='glsl430')
mat.par.vdat = dat('dep_vert', rd('dep_vert.glsl')); mat.par.pdat = dat('dep_pix', rd('dep_pix.glsl'))
mat.par.sampler0name = 'uAgents'; mat.par.sampler0top = agents.name
mat.par.sampler0filter = 'nearest' if 'nearest' in mat.par.sampler0filter.menuNames else mat.par.sampler0filter.val
vec(mat, 0, 'uCount', "parent().par.Agents")
vec(mat, 1, 'uDeposit', "parent().par.Deposit*(1+2*op('modlib').module.m('band1'))")
vec(mat, 2, 'uAgentsW', str(AW))
vec(mat, 3, 'uPx', "2.0/parent().par.Resolutionw", "2.0/parent().par.Resolutionh")
geo.par.material = mat.name
cam = mk(td.cameraCOMP, 'cam', tz=5)
rend = mk(td.renderTOP, 'deposit_render', outputresolution='custom', format='rgba32float', antialias='aa1' if False else 0)
rend.par.resolutionw.expr = "parent().par.Resolutionw"; rend.par.resolutionh.expr = "parent().par.Resolutionh"
rend.par.camera = cam.name; rend.par.geometry = geo.name; rend.par.lights = ''
rend.par.bgcolora = 0

# ---- trail
trail = mk(td.glslTOP, 'trail', outputresolution='custom', format='rgba32float')
trail.par.resolutionw.expr = "parent().par.Resolutionw"; trail.par.resolutionh.expr = "parent().par.Resolutionh"
trail.par.pixeldat = dat('trail_pix', rd('trail.glsl'))
trail.inputConnectors[0].connect(fbT); trail.inputConnectors[1].connect(rend)
trail.par.inputextenduv = 'repeat'; trail.par.inputfiltertype = 'linear'
fbT.par.top = trail.name
vec(trail, 0, 'uT', "parent().par.Diffuse", "parent().par.Decay", "1 if parent().par.Play else 0")

# ---- output
col = mk(td.glslTOP, 'color', outputresolution='custom', format='rgba16float')
col.par.resolutionw.expr = "parent().par.Resolutionw"; col.par.resolutionh.expr = "parent().par.Resolutionh"
col.par.pixeldat = dat('color_pix', rd('color.glsl'))
col.inputConnectors[0].connect(trail)
vec(col, 0, 'uC1', "parent().par.Color1r", "parent().par.Color1g", "parent().par.Color1b")
vec(col, 1, 'uC2', "parent().par.Color2r", "parent().par.Color2g", "parent().par.Color2b")
vec(col, 2, 'uC3', "parent().par.Color3r", "parent().par.Color3g", "parent().par.Color3b")
vec(col, 3, 'uGain', "parent().par.Gain")
o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(col)
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(trail)
o1.viewer = True
c.par.opviewer = o1.path if 'opviewer' in c.par else None
c.op('out1').comment = 'render'
c.op('out2').comment = 'trail'
retro(c, accmode=1, gain=0.7)
c.save(OUT); print('saved')
