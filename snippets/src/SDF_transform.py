exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# SDF snippet helpers: N = instance with parameters ('=expr' sets an expression), W = wire SDF out -> in, R = render -> exampleN
def N(ex, name, **kw):
    i = instance(ex, name)
    for k, v in kw.items():
        if isinstance(v, str) and v.startswith('='): i.par[k].expr = v[1:]
        else: i.par[k] = v
    return i
def W(a, b, idx=0): connect(a, b, 0, idx)
def R(ex, scene, n, res=(960, 540), **kw):
    r = N(ex, 'SDF_render', Resolutionw=res[0], Resolutionh=res[1], **kw)
    W(scene, r); out(ex, n, r); return r
def ORBIT(ex, dist=5.0, height=1.6, speed=0.4, fov=60, target_y=0.0):
    cam = ex.create(cameraCOMP, 'cam')
    cam.par.tx.expr = '%g*math.sin(absTime.seconds*%g)' % (dist, speed)
    cam.par.tz.expr = '%g*math.cos(absTime.seconds*%g)' % (dist, speed)
    cam.par.ty = height
    cam.par.ry.expr = 'math.degrees(absTime.seconds*%g)' % speed
    cam.par.rx = -math.degrees(math.atan2(height - target_y, dist))
    cam.par.fov = fov
    return cam

STUDIO = """out vec4 fragColor;
float bx(vec2 q, vec2 c, vec2 h, float s){ vec2 d = abs(q - c) - h; return 1.0 - smoothstep(-s, s, max(d.x, d.y)); }
void main(){
    vec2 q = vec2(vUV.x - 0.5, vUV.y - 0.5);
    vec3 c = mix(vec3(0.01, 0.012, 0.02), vec3(0.16, 0.18, 0.24), smoothstep(-0.3, 0.5, q.y));
    float s = 0.006;
    c += vec3(1.0) * bx(q, vec2(0.0, 0.30), vec2(0.32, 0.035), s) * 2.0;
    c += vec3(1.0, 0.96, 0.9) * bx(q, vec2(0.25, 0.0), vec2(0.03, 0.30), s) * 2.2;
    c += vec3(0.8, 0.9, 1.0) * bx(q, vec2(-0.27, 0.05), vec2(0.04, 0.22), s) * 1.8;
    c += vec3(1.0, 0.2, 0.1) * bx(q, vec2(0.45, 0.1), vec2(0.02, 0.16), s) * 1.8;
    c += vec3(0.9) * bx(q, vec2(0.0, -0.32), vec2(0.4, 0.012), s) * 1.2;
    fragColor = TDOutputSwizzle(vec4(c, 1.0));
}"""
def studio(ex):
    d = ex.create(textDAT, 'studio_code'); d.text = STUDIO
    g = ex.create(glslTOP, 'studio'); g.par.pixeldat = d
    g.par.outputresolution = 'custom'; g.par.resolutionw = 1024; g.par.resolutionh = 512; g.par.format = 'rgba16float'
    return g
s = begin('SDF_transform')
ex = example(s, 1, 'Move, rotate, scale', 'SDF_transform places an SDF in space. The box tumbles and bobs; Scale is uniform so distances stay exact.\nTry: Translate, Rotate (degrees), Scale.')
b = N(ex, 'SDF_box', Roundness=0.12)
t = N(ex, 'SDF_transform', Rotatex='=absTime.seconds*35', Rotatey='=absTime.seconds*50', Translatey='=0.4*math.sin(absTime.seconds*2)', Scale='=1+0.3*math.sin(absTime.seconds)'); W(b, t)
R(ex, t, 1)
ex = example(s, 2, 'Orbiting moons', 'Several transforms of one SDF_sphere, joined with SDF_combine: a planet and two moons.\nEach SDF_transform has its own Translate/Rotate.')
p = N(ex, 'SDF_sphere', Radius=0.7, Colorr=0.3, Colorg=0.5, Colorb=0.9)
m = N(ex, 'SDF_sphere', Radius=0.25, Colorr=0.9, Colorg=0.85, Colorb=0.8)
t1 = N(ex, 'SDF_transform', Rotatey='=absTime.seconds*60', Translatex=1.5); W(m, t1)
t1b = N(ex, 'SDF_transform', Rotatey='=absTime.seconds*60'); W(t1, t1b)
t2 = N(ex, 'SDF_transform', Translatex=1.1); W(m, t2)
t2b = N(ex, 'SDF_transform', Rotatez=60, Rotatey='=-absTime.seconds*110'); W(t2, t2b)
c1 = N(ex, 'SDF_combine', Smooth=0.0); W(p, c1, 0); W(t1b, c1, 1)
c2 = N(ex, 'SDF_combine', Smooth=0.0); W(c1, c2, 0); W(t2b, c2, 1)
R(ex, c2, 2)
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
