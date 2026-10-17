import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read()); exec(open(_G + 'gbuf.py').read())

COMP = 'TOP_ssao'
c = new_comp(COMP)
add_pars(c, [
    ('Depthmode', 'menu', [('linear', 'Linear eye-space z'), ('nonlinear', 'Render TOP depth (0-1)')], 0),
    ('Near', 'float', 0.5, 0.001, 100),
    ('Far', 'float', 100, 1, 10000),
    ('Depthscale', 'float', 1.0, 0.0001, 1000),
    ('Normalenc', 'menu', [('signed', 'Signed (-1..1)'), ('packed', 'Packed (0..1)')], 0),
    ('Fov', 'float', 40, 1, 170),
    ('Radius', 'float', 1.0, 0.01, 20),
    ('Samples', 'int', 20, 4, 64),
    ('Intensity', 'float', 1.4, 0, 3),
    ('Bias', 'float', 0.04, 0, 1),
    ('Power', 'float', 1.5, 0.2, 4),
    ('Blur', 'int', 4, 0, 16),
    *COMMON,
])
P = 'parent().par.'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')
d = demo_comp(c, outs=('color', 'depth', 'normal'))
def sw3(name, demo_idx, fb, inp, k, fmt):
    s = c.create(td.switchTOP, name)
    s.inputConnectors[0].connect(d.outputConnectors[demo_idx]); s.inputConnectors[1].connect(fb); s.inputConnectors[2].connect(inp)
    s.par.index.expr = "(2 if len(parent().inputConnectors[%d].connections) else (1 if %s else 0)) + 0*absTime.frame" % (k, HAS1)
    setres(s); s.par.format = fmt
    return s
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d.outputConnectors[0]); src.inputConnectors[1].connect(i1)
src.par.index.expr = '(1 if %s else 0) + 0*absTime.frame' % HAS1
setres(src); src.par.format = 'rgba16float'
fd = c.create(td.constantTOP, 'defdepth'); setres(fd); fd.par.format = 'rgba16float'
fd.par.colorr.expr = "(%sFar*0.25 if %sDepthmode=='linear' else 0.995)" % (P, P)
fd.par.colorg.expr = fd.par.colorb.expr = fd.par.colorr.expr; fd.par.alpha = 1
fn = c.create(td.constantTOP, 'defnormal'); setres(fn); fn.par.format = 'rgba16float'
fn.par.colorr = 0; fn.par.colorg = 0; fn.par.alpha = 1
fn.par.colorb.expr = "(1.0 if %sNormalenc=='signed' else 1.0)" % P
dsrc = sw3('depthsrc', 1, fd, i2, 1, 'rgba32float')
nsrc = sw3('normalsrc', 2, fn, i3, 2, 'rgba16float')
DEP = [P + 'Depthmode.menuIndex', P + 'Near', P + 'Far', P + 'Depthscale']
ao = glsl(c, 'ao', rd(COMP, 'ao.glsl'), inputs=[dsrc, nsrc], res=True, fmt='rgba16float', vecs=[
    ('uA', DEP), ('uB', [P + 'Fov', P + 'Radius', P + 'Samples', P + 'Bias']),
    ('uC', [P + 'Normalenc.menuIndex', 0, 0, 0])])
bh = glsl(c, 'blur_h', rd(COMP, 'blur.glsl'), inputs=[ao, dsrc], res=True, fmt='rgba16float',
          vecs=[('uA', DEP), ('uB', [1, 0, P + 'Blur', 0])])
bv = glsl(c, 'blur_v', rd(COMP, 'blur.glsl'), inputs=[bh, dsrc], res=True, fmt='rgba16float',
          vecs=[('uA', DEP), ('uB', [0, 1, P + 'Blur', 0])])
mk = glsl(c, 'mask', rd(COMP, 'mask.glsl'), inputs=[bv], res=True, fmt='rgba16float',
          vecs=[('uA', [P + 'Intensity', P + 'Power', 0, 0])])
ap = glsl(c, 'apply', rd(COMP, 'apply.glsl'), inputs=[src, mk], res=True)
finish_v2(c, COMP, ap, src, extra_outs=[(mk, 'AO mask')])
report(c)
