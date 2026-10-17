import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read()); exec(open(_G + 'gbuf.py').read())

COMP = 'TOP_env_reflect'
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('chrome', 'Chrome (reflect over colour)'), ('glass', 'Glass (refract colour + reflect)')], 0),
    ('Reflectivity', 'float', 0.9, 0, 1, True),
    ('Fresnel', 'float', 0.3, 0, 1, True),
    ('Roughness', 'float', 0.12, 0, 1, True),
    ('Ior', 'float', 1.5, 1.0, 3.0),
    ('Refraction', 'float', 0.3, 0, 2),
    ('Maskmode', 'menu', [('roughness', 'Mask scales roughness'), ('reflectivity', 'Mask scales reflectivity'), ('off', 'Ignore mask')], 1),
    ('Normalenc', 'menu', [('signed', 'Signed (-1..1)'), ('packed', 'Packed (0..1)')], 0),
    ('Fov', 'float', 40, 0, 170),
    *COMMON,
])
add_pars(c, [
    ('Envrotate', 'float', 0, -360, 360),
    ('Envtilt', 'float', 0, -90, 90),
    ('Envgain', 'float', 1.0, 0, 8),
    ('Tint', 'rgb', (1.0, 1.0, 1.0)),
], page='Look')
P = 'parent().par.'
F = ' + 0*absTime.frame'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3'); i4 = c.create(td.inTOP, 'in4')
d = demo_comp(c, outs=('color', 'normal', 'mask'))
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = '(1 if %s else 0)%s' % (HAS1, F)
setres(src); src.par.format = 'rgba16float'
fn = c.create(td.constantTOP, 'defnormal')    # no normals wired: zero normals = "no geometry", colour passes through
setres(fn); fn.par.format = 'rgba16float'; fn.par.colorr = fn.par.colorg = fn.par.colorb = 0; fn.par.alpha = 1
nsrc = c.create(td.switchTOP, 'normalsrc')
nsrc.inputConnectors[0].connect(d.outputConnectors[1]); nsrc.inputConnectors[1].connect(fn); nsrc.inputConnectors[2].connect(i2)
nsrc.par.index.expr = "(2 if len(parent().inputConnectors[1].connections) else (1 if %s else 0))%s" % (HAS1, F)
setres(nsrc); nsrc.par.format = 'rgba16float'
de = glsl(c, 'defenv', rd(COMP, 'env.glsl'), fmt='rgba16float')
de.par.outputresolution = 'custom'; de.par.resolutionw = 1024; de.par.resolutionh = 512
esrc = c.create(td.switchTOP, 'envsrc')
esrc.inputConnectors[0].connect(de); esrc.inputConnectors[1].connect(i3)
esrc.par.index.expr = "(1 if len(parent().inputConnectors[2].connections) else 0)" + F
esrc.par.outputresolution = 'useinput'; esrc.par.format = 'rgba16float'
wh = c.create(td.constantTOP, 'defmask'); setres(wh); wh.par.format = 'rgba16float'
wh.par.colorr = wh.par.colorg = wh.par.colorb = 1; wh.par.alpha = 1
msrc = c.create(td.switchTOP, 'masksrc')
msrc.inputConnectors[0].connect(d.outputConnectors[2]); msrc.inputConnectors[1].connect(wh); msrc.inputConnectors[2].connect(i4)
msrc.par.index.expr = "(2 if len(parent().inputConnectors[3].connections) else (1 if %s else 0))%s" % (HAS1, F)
setres(msrc); msrc.par.format = 'rgba16float'
rf = glsl(c, 'reflect', rd(COMP, 'reflect.glsl'), inputs=[src, nsrc, esrc, msrc], res=True, vecs=[
    ('uA', [P + 'Fov', P + 'Roughness', P + 'Reflectivity', P + 'Fresnel']),
    ('uB', [P + 'Ior', P + 'Refraction', P + 'Mode.menuIndex', P + 'Maskmode.menuIndex']),
    ('uC', ['math.radians(%sEnvrotate)' % P, 'math.radians(%sEnvtilt)' % P, P + 'Normalenc.menuIndex', P + 'Envgain']),
    ('uD', [P + 'Tintr', P + 'Tintg', P + 'Tintb', 0]),
])
rf.par.inputfiltertype = 'mipmap'; rf.par.inputextenduv = 'hold'
finish_v2(c, COMP, rf, src)
report(c)
