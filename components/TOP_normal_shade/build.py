import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read()); exec(open(_G + 'gbuf.py').read())

COMP = 'TOP_normal_shade'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('matcap', 'Matcap lookup'), ('lights', 'Key / fill / rim lights')], 0),
    ('Normalenc', 'menu', [('signed', 'Signed (-1..1)'), ('packed', 'Packed (0..1)')], 0),
    ('Colormix', 'float', 1.0, 0, 1, True),
    ('Brightness', 'float', 1.0, 0, 4),
    ('Background', 'menu', [('transparent', 'Transparent black'), ('color', 'in3 colour')], 0),
    ('Matcaprotate', 'float', 0, -180, 180),
    ('Matcapflip', 'toggle', 0),
    *COMMON,
])
add_pars(c, [
    ('Keyazimuth', 'float', -35, -180, 180),
    ('Keyelevation', 'float', 40, -89, 89),
    ('Keyintensity', 'float', 0.7, 0, 8),
    ('Keycolor', 'rgb', (1.0, 0.92, 0.82)),
    ('Fillintensity', 'float', 0.22, 0, 4),
    ('Fillcolor', 'rgb', (0.45, 0.6, 1.0)),
    ('Rimintensity', 'float', 0.6, 0, 8),
    ('Rimcolor', 'rgb', (0.8, 0.9, 1.0)),
    ('Rimpower', 'float', 3.0, 0.5, 12),
    ('Ambient', 'float', 0.03, 0, 1),
    ('Specamount', 'float', 0.3, 0, 4),
    ('Specpower', 'float', 40, 2, 400),
    ('Wrap', 'float', 0.2, 0, 1),
], page='Lights')
P = 'parent().par.'
F = ' + 0*absTime.frame'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')
d = demo_comp(c, outs=('normal',), sky=False)
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = '(1 if %s else 0)%s' % (HAS1, F)
setres(src); src.par.format = 'rgba16float'
dm = glsl(c, 'defmatcap', rd(COMP, 'matcap.glsl'), fmt='rgba16float')
dm.par.outputresolution = 'custom'; dm.par.resolutionw = 512; dm.par.resolutionh = 512
msrc = c.create(td.switchTOP, 'matcapsrc')
msrc.inputConnectors[0].connect(dm); msrc.inputConnectors[1].connect(i2)
msrc.par.index.expr = "(1 if len(parent().inputConnectors[1].connections) else 0)" + F
msrc.par.outputresolution = 'useinput'; msrc.par.format = 'rgba16float'
wh = c.create(td.constantTOP, 'defcolor'); setres(wh); wh.par.format = 'rgba16float'
wh.par.colorr = wh.par.colorg = wh.par.colorb = 1; wh.par.alpha = 1
csrc = c.create(td.switchTOP, 'colorsrc')
csrc.inputConnectors[0].connect(wh); csrc.inputConnectors[1].connect(i3)
csrc.par.index.expr = "(1 if len(parent().inputConnectors[2].connections) else 0)" + F
setres(csrc); csrc.par.format = 'rgba16float'
R = 'math.radians'
sh = glsl(c, 'shade', rd(COMP, 'shade.glsl'), inputs=[src, msrc, csrc], res=True, vecs=[
    ('uA', [P + 'Mode.menuIndex', P + 'Normalenc.menuIndex', R + '(%sMatcaprotate)' % P, '1 if %sMatcapflip else 0' % P]),
    ('uB', [R + '(%sKeyazimuth)' % P, R + '(%sKeyelevation)' % P, P + 'Keyintensity', P + 'Ambient']),
    ('uC', [P + 'Keycolorr', P + 'Keycolorg', P + 'Keycolorb', P + 'Fillintensity']),
    ('uD', [P + 'Fillcolorr', P + 'Fillcolorg', P + 'Fillcolorb', P + 'Rimintensity']),
    ('uE', [P + 'Rimcolorr', P + 'Rimcolorg', P + 'Rimcolorb', P + 'Rimpower']),
    ('uF', [P + 'Specamount', P + 'Specpower', P + 'Wrap', P + 'Colormix']),
    ('uG', [P + 'Brightness', P + 'Background.menuIndex', 0, 0]),
])
finish_v2(c, COMP, sh, src)
report(c)
