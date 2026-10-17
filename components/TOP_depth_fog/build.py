import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read()); exec(open(_G + 'gbuf.py').read())

COMP = 'TOP_depth_fog'
c = new_comp(COMP)
add_pars(c, [
    ('Depthmode', 'menu', [('linear', 'Linear eye-space z'), ('nonlinear', 'Render TOP depth (0-1)')], 0),
    ('Near', 'float', 0.5, 0.001, 100),
    ('Far', 'float', 100, 1, 10000),
    ('Depthscale', 'float', 1.0, 0.0001, 1000),
    ('Fogmode', 'menu', [('exp', 'Exponential'), ('exp2', 'Exponential squared'), ('linear', 'Linear')], 1),
    ('Density', 'float', 0.03, 0, 1),
    ('Start', 'float', 8, 0, 500),
    ('End', 'float', 60, 0.1, 1000),
    ('Fogamount', 'float', 1.0, 0, 1, True),
    ('Fov', 'float', 40, 1, 170),
    *COMMON,
])
add_pars(c, [
    ('Fogcolor', 'rgb', (0.42, 0.47, 0.56)),
    ('Heightfog', 'toggle', 1),
    ('Heightbase', 'float', -1.3, -100, 100),
    ('Heightfalloff', 'float', 0.25, 0.001, 5),
    ('Heightdensity', 'float', 0.06, 0, 2),
    ('Camheight', 'float', 3.2, -100, 100),
    ('Campitch', 'float', 14.0, -89, 89),
], page='Fog')
add_pars(c, [
    ('Glow', 'float', 0.55, 0, 5),
    ('Glowwidth', 'float', 0.09, 0.01, 1),
    ('Glowcolor', 'rgb', (1.0, 0.62, 0.35)),
    ('Skyblend', 'float', 1.0, 0, 1, True),
], page='Look')
P = 'parent().par.'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2')
d = demo_comp(c, outs=('color', 'depth'))
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = '(1 if %s else 0) + 0*absTime.frame' % HAS1
setres(src); src.par.format = 'rgba16float'
fb = c.create(td.constantTOP, 'defdepth')   # in1 connected but no depth: a flat mid-distance depth
setres(fb); fb.par.format = 'rgba16float'
fb.par.colorr.expr = "(%sFar*0.25 if %sDepthmode=='linear' else 0.995)" % (P, P)
fb.par.colorg.expr = fb.par.colorb.expr = fb.par.colorr.expr
fb.par.alpha = 1
dsrc = c.create(td.switchTOP, 'depthsrc')
dsrc.inputConnectors[0].connect(d.outputConnectors[1]); dsrc.inputConnectors[1].connect(fb); dsrc.inputConnectors[2].connect(i2)
dsrc.par.index.expr = "(2 if len(parent().inputConnectors[1].connections) else (1 if %s else 0)) + 0*absTime.frame" % HAS1
setres(dsrc); dsrc.par.format = 'rgba32float'
fog = glsl(c, 'fog', rd(COMP, 'fog.glsl'), inputs=[src, dsrc], res=True, vecs=[
    ('uA', [P + 'Depthmode.menuIndex', P + 'Near', P + 'Far', P + 'Depthscale']),
    ('uB', [P + 'Fogmode.menuIndex', P + 'Density', P + 'Start', P + 'End']),
    ('uC', [P + 'Fogcolorr', P + 'Fogcolorg', P + 'Fogcolorb', P + 'Fogamount']),
    ('uD', [P + 'Fov', P + 'Camheight', P + 'Campitch', P + 'Skyblend']),
    ('uE', ['1 if %sHeightfog else 0' % P, P + 'Heightbase', P + 'Heightfalloff', P + 'Heightdensity']),
    ('uF', [P + 'Glow', P + 'Glowwidth', 0, 0]),
    ('uG', [P + 'Glowcolorr', P + 'Glowcolorg', P + 'Glowcolorb', 0]),
])
finish_v2(c, COMP, fog, src)
report(c)
