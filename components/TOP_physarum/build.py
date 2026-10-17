import os, td

NAME = 'TOP_physarum'
D = os.path.expanduser('~/software/td-plugins/components/' + NAME + '/')
OUT = os.path.expanduser('~/software/td-plugins/tox/_raw/' + NAME + '.tox')
AW = 512  # agent texture is AW x AW

MODLIB = '''# modulation helper: m(name) reads a channel (band1-4, beat) of the optional In CHOP, else the default
def m(n, d=0.0):
    i = op('in2')
    if i is None or not i.numChans: return d
    ch = i[n]
    return ch.eval() if ch is not None else d
'''
def MOD(n, d=0.0): return "op('modlib').module.m('%s', %s)" % (n, d)

# working resolution: in1's size when connected (Resolutionmode=input), else Resolutionw/h
W = "(parent().op('in1').width if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionw)"
H = "(parent().op('in1').height if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionh)"

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
def res(o, fmt=None):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = W; o.par.resolutionh.expr = H
    if fmt: o.par.format = fmt

# ---- custom parameters
def num(page, name, label, default, lo, hi, clo=True, chi=True, isint=False, nlo=None, nhi=None):
    pg = (page.appendInt if isint else page.appendFloat)(name, label=label)
    p = pg[0]; p.default = default; p.val = default; p.min = lo; p.max = hi
    p.normMin = lo if nlo is None else nlo; p.normMax = hi if nhi is None else nhi
    p.clampMin = clo; p.clampMax = chi
    return p
P = c.appendCustomPage('Controls')
num(P, 'Mix', 'Mix', 1.0, 0, 1)
P.appendToggle('Bypass', label='Bypass')
P.appendToggle('Play', label='Play')[0].default = True; c.par.Play = True
P.appendPulse('Reset', label='Reset')
num(P, 'Seed', 'Seed', 0, 0, 1000, isint=True)
pg = P.appendMenu('Initpattern', label='Init Pattern')
pg[0].menuNames = ['random', 'disc', 'ring']; pg[0].menuLabels = ['Random', 'Disc (inward)', 'Ring (outward)']
pg[0].default = 'random'; pg[0].val = 'random'
pg = P.appendMenu('Resolutionmode', label='Resolution Mode')
pg[0].menuNames = ['input', 'custom']; pg[0].menuLabels = ['Follow input', 'Custom']; pg[0].default = 'input'; pg[0].val = 'input'
pg = P.appendWH('Resolution', label='Resolution')
for p, v in zip(pg, (1280, 720)): p.default = v; p.val = v; p.min = 16; p.clampMin = True; p.max = 4096; p.normMax = 4096
c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"

A = c.appendCustomPage('Attractor')
num(A, 'Attraction', 'Attraction', 12.0, -50, 50, clo=False, chi=False, nlo=-20, nhi=20)
A.appendToggle('Invert', label='Invert (follow dark)')
num(A, 'Fieldpower', 'Contrast (Power)', 1.0, 0.2, 5, chi=False, nlo=0.3, nhi=3)
num(A, 'Fieldblur', 'Field Blur (px)', 6.0, 0, 100, chi=False, nlo=0, nhi=40)

S = c.appendCustomPage('Agents')
num(S, 'Agents', 'Agents', 150000, 1000, AW*AW, isint=True)
num(S, 'Sensorangle', 'Sensor Angle', 35, 5, 120)
num(S, 'Sensordist', 'Sensor Dist', 14, 1, 60, chi=False)
num(S, 'Turnspeed', 'Turn Speed', 25, 1, 180)
num(S, 'Stepsize', 'Step Size', 1.0, 0.1, 6, chi=False)
num(S, 'Deposit', 'Deposit', 0.5, 0.01, 5, chi=False)
num(S, 'Decay', 'Decay', 0.94, 0.8, 1.0)
num(S, 'Diffuse', 'Diffuse', 0.3, 0, 1)

L = c.appendCustomPage('Look')
pg = L.appendMenu('Colormode', label='Trail Colour')
pg[0].menuNames = ['ramp', 'tint', 'image']; pg[0].menuLabels = ['Ramp (3 colours)', 'Tint', 'From image']
pg[0].default = 'ramp'; pg[0].val = 'ramp'
pg = L.appendMenu('Compose', label='Composite')
pg[0].menuNames = ['over', 'add', 'screen']; pg[0].menuLabels = ['Over', 'Add', 'Screen']
pg[0].default = 'over'; pg[0].val = 'over'
num(L, 'Inputlevel', 'Input Brightness', 0.35, 0, 1.5, chi=False, nhi=1)
num(L, 'Gain', 'Trail Gain', 1.0, 0.1, 20, chi=False, nhi=5)
for n, col in (('Tint', (0.4, 1.0, 0.8)), ('Color1', (0.0, 0.0, 0.05)), ('Color2', (0.9, 0.2, 0.5)), ('Color3', (1.0, 0.95, 0.6))):
    pg = L.appendRGB(n)
    for p, v in zip(pg, col): p.default = v; p.val = v

# ---- inputs
i1 = mk(td.inTOP, 'in1')
i2 = mk(td.inCHOP, 'in2')
dat('modlib', MODLIB)

# ---- demo source (gated: only selected when in1 is not connected)
demo = c.create(td.baseCOMP, 'demo')
def dm(t, name, **kw):
    o = demo.create(t, name)
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): o.par[k].expr = v[1:]
        else: o.par[k] = v
    return o
dn = dm(td.noiseTOP, 'noise', outputresolution='custom', resolutionw=640, resolutionh=360, period=1.3, harmon=1, mono=True, format='rgba16float')
dn.par.seed = 3
dl = dm(td.levelTOP, 'blobs', brightness1=1.0, contrast=4.0, blacklevel=0.0, format='rgba16float')
dl.inputConnectors[0].connect(dn)
dc = dm(td.circleTOP, 'dot', outputresolution='custom', resolutionw=640, resolutionh=360, radiusx=0.16, radiusy=0.16, softness=0.05, format='rgba16float',
        bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, fillcolorr=1, fillcolorg=1, fillcolorb=1)
dc.par.centerx = 0.7; dc.par.centery = 0.45
dp = dm(td.compositeTOP, 'comp', operand='add', format='rgba16float')
dp.inputConnectors[0].connect(dl); dp.inputConnectors[1].connect(dc)
dout = demo.create(td.outTOP, 'out1'); dout.inputConnectors[0].connect(dp)

src = mk(td.switchTOP, 'src')
src.inputConnectors[0].connect(demo.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"
res(src, 'rgba16float')

# ---- attractor field from input luminance
fld = mk(td.glslTOP, 'field')
fld.par.pixeldat = dat('field_pix', rd('field.glsl'))
fld.inputConnectors[0].connect(src)
res(fld, 'rgba16float')
vec(fld, 0, 'uF', "1 if parent().par.Invert else 0", "parent().par.Fieldpower")
blur = mk(td.blurTOP, 'fieldblur', size='=parent().par.Fieldblur', format='rgba16float')
blur.inputConnectors[0].connect(fld)
blur.par.outputresolution = 'useinput'

# ---- agents
fbA = mk(td.feedbackTOP, 'fb_agents')
agents = mk(td.glslTOP, 'agents', outputresolution='custom', resolutionw=AW, resolutionh=AW, format='rgba32float', inputfiltertype='nearest')
agents.par.pixeldat = dat('agents_pix', rd('agents.glsl'))
fbT = mk(td.feedbackTOP, 'fb_trail', outputresolution='custom', format='rgba32float')
fbT.par.resolutionw.expr = W; fbT.par.resolutionh.expr = H
agents.inputConnectors[0].connect(fbA); agents.inputConnectors[1].connect(fbT); agents.inputConnectors[2].connect(blur)
fbA.par.top = agents.name
fbA.par.outputresolution = 'custom'; fbA.par.resolutionw = AW; fbA.par.resolutionh = AW; fbA.par.format = 'rgba32float'
fbA.par.reset.expr = "parent().par.Reset"; fbT.par.reset.expr = "parent().par.Reset"
vec(agents, 0, 'uP', "parent().par.Sensorangle*0.0174533", "parent().par.Sensordist", "parent().par.Turnspeed*0.0174533*(1+%s)" % MOD('band2'), "parent().par.Stepsize")
vec(agents, 1, 'uQ', "parent().par.Reset", "1 if parent().par.Play else 0", "absTime.frame", "parent().par.Initpattern.menuIndex")
vec(agents, 2, 'uA', "parent().par.Attraction*(1+1.5*%s)" % MOD('band3'), "parent().par.Seed")
zA = mk(td.constantTOP, 'zero_agents', outputresolution='custom', resolutionw=AW, resolutionh=AW, format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
zT = mk(td.constantTOP, 'zero_trail', outputresolution='custom', format='rgba32float', colorr=0, colorg=0, colorb=0, alpha=0)
zT.par.resolutionw.expr = W; zT.par.resolutionh.expr = H
fbA.inputConnectors[0].connect(zA); fbT.inputConnectors[0].connect(zT)
agents.par.inputextenduv = 'repeat'
agents.par.inputfiltertype = 'linear'

# ---- deposit render (instanced quads, additive)
geo = mk(td.geometryCOMP, 'deposit_geo')
for ch in list(geo.children): ch.destroy()
pt = geo.create(td.gridSOP, 'quad'); pt.par.rows = 2; pt.par.cols = 2; pt.par.sizex = 1; pt.par.sizey = 1
o = geo.create(td.outSOP, 'out1'); o.inputConnectors[0].connect(pt)
o.render = True; o.display = True
geo.par.instancing = True; geo.par.instancecountmode = 'manual'; geo.par.numinstances = AW*AW
mat = mk(td.glslMAT, 'deposit_mat', blending=True, srcblend='one', destblend='one', depthtest=False, depthwriting=False, cullface='neither', glslversion='glsl430')
mat.par.vdat = dat('dep_vert', rd('dep_vert.glsl')); mat.par.pdat = dat('dep_pix', rd('dep_pix.glsl'))
mat.par.sampler0name = 'uAgents'; mat.par.sampler0top = agents.name
mat.par.sampler0filter = 'nearest' if 'nearest' in mat.par.sampler0filter.menuNames else mat.par.sampler0filter.val
vec(mat, 0, 'uCount', "parent().par.Agents")
vec(mat, 1, 'uDeposit', "parent().par.Deposit*(1+2*%s)" % MOD('band1'))
vec(mat, 2, 'uAgentsW', str(AW))
vec(mat, 3, 'uPx', "2.0/" + W, "2.0/" + H)
geo.par.material = mat.name
cam = mk(td.cameraCOMP, 'cam', tz=5)
rend = mk(td.renderTOP, 'deposit_render', outputresolution='custom', format='rgba32float', antialias=0)
rend.par.resolutionw.expr = W; rend.par.resolutionh.expr = H
rend.par.camera = cam.name; rend.par.geometry = geo.name; rend.par.lights = ''
rend.par.bgcolora = 0

# ---- trail map
trail = mk(td.glslTOP, 'trail', outputresolution='custom', format='rgba32float')
trail.par.resolutionw.expr = W; trail.par.resolutionh.expr = H
trail.par.pixeldat = dat('trail_pix', rd('trail.glsl'))
trail.inputConnectors[0].connect(fbT); trail.inputConnectors[1].connect(rend)
trail.par.inputextenduv = 'repeat'; trail.par.inputfiltertype = 'linear'
fbT.par.top = trail.name
vec(trail, 0, 'uT', "parent().par.Diffuse", "parent().par.Decay", "1 if parent().par.Play else 0")

# ---- composite over the input
col = mk(td.glslTOP, 'color')
res(col, 'rgba16float')
col.par.pixeldat = dat('color_pix', rd('color.glsl'))
col.inputConnectors[0].connect(trail); col.inputConnectors[1].connect(src)
vec(col, 0, 'uC1', "parent().par.Color1r", "parent().par.Color1g", "parent().par.Color1b")
vec(col, 1, 'uC2', "parent().par.Color2r", "parent().par.Color2g", "parent().par.Color2b")
vec(col, 2, 'uC3', "parent().par.Color3r", "parent().par.Color3g", "parent().par.Color3b")
vec(col, 3, 'uTint', "parent().par.Tintr", "parent().par.Tintg", "parent().par.Tintb")
col.seq.vec.numBlocks = 5
vec(col, 4, 'uM', "parent().par.Colormode.menuIndex", "parent().par.Compose.menuIndex", "parent().par.Inputlevel", "parent().par.Gain*(1+0.6*%s)" % MOD('beat'))

mixfx = mk(td.crossTOP, 'mixfx', format='rgba16float', outputresolution='useinput')
mixfx.par.cross.expr = 'parent().par.Mix'
mixfx.inputConnectors[0].connect(src); mixfx.inputConnectors[1].connect(col)
bp = mk(td.switchTOP, 'bypass')
bp.inputConnectors[0].connect(mixfx); bp.inputConnectors[1].connect(src)
bp.par.index.expr = "1 if parent().par.Bypass else 0"

o1 = mk(td.nullTOP, 'out1'); o1.inputConnectors[0].connect(bp)
o2 = mk(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(trail)
o1.viewer = True
c.par.opviewer = o1.path
o1.comment = 'trails + image'
o2.comment = 'raw trail map'
c.save(OUT); print('saved')
