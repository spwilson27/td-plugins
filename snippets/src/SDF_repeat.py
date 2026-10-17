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
s = begin('SDF_repeat')
ex = example(s, 1, 'Infinite tunnel', 'A square frame (box minus box) repeated along Z forms an endless corridor; the camera flies down it.\nFog fades the distance, Color Variation tints each segment. Mode = grid with Spacing X/Y = 0 repeats only along Z.')
o = N(ex, 'SDF_box', Sizex=3.0, Sizey=3.0, Sizez=0.5, Roundness=0.0, Colorr=0.55, Colorg=0.6, Colorb=0.7)
i = N(ex, 'SDF_box', Sizex=2.5, Sizey=2.5, Sizez=2.0, Roundness=0.0)
c = N(ex, 'SDF_combine', Operation='subtract', Smooth=0.0); W(o, c, 0); W(i, c, 1)
rp = N(ex, 'SDF_repeat', Mode='grid', Spacingx=0, Spacingy=0, Spacingz=1.6, Colorvary=0.6); W(c, rp)
cam = ex.create(cameraCOMP, 'cam'); cam.par.tz.expr = '-absTime.seconds*2.0'; cam.par.ry = 180; cam.par.fov = 75
r = R(ex, rp, 1, Fog=0.12, Stepscale=0.8, Maxdist=40, Shadows=0.0, Fogcolorr=0.02, Fogcolorg=0.02, Fogcolorb=0.04)
r.par.Camera = cam
ex = example(s, 2, 'Mirror lattice', 'A rotating torus repeated on an infinite 3D grid, reflective with fog: a mirror-room feel.\nThe camera sits between cells. Increase Spacing for more room, Color Variation for per-cell tint.')
t = N(ex, 'SDF_torus', Majorradius=0.45, Minorradius=0.12, Colorr=0.85, Colorg=0.85, Colorb=0.9)
tr = N(ex, 'SDF_transform', Rotatex='=absTime.seconds*40', Rotatey='=absTime.seconds*25'); W(t, tr)
rp = N(ex, 'SDF_repeat', Mode='grid', Spacingx=2.0, Spacingy=2.0, Spacingz=2.0, Colorvary=0.4); W(tr, rp)
cam = ex.create(cameraCOMP, 'cam'); cam.par.tx = 1.0; cam.par.ty = 1.0; cam.par.tz.expr = '1.0-absTime.seconds*0.6'; cam.par.ry = 180; cam.par.fov = 70
r = R(ex, rp, 2, Reflectivity=0.7, Fog=0.08, Shadows=0.0, Stepscale=0.8, Maxdist=40)
r.par.Camera = cam
ex = example(s, 3, 'Polar and finite repeat', 'Mode = polar repeats around an axis: eight boxes in a ring. SDF_repeat (finite) in a second node stacks the ring three high.\nTry: Polar Count, Polar Axis, Cells each side.')
b = N(ex, 'SDF_box', Sizex=0.3, Sizey=0.9, Sizez=0.3, Roundness=0.05)
tb = N(ex, 'SDF_transform', Translatex=1.2); W(b, tb)
pr = N(ex, 'SDF_repeat', Mode='polar', Polarcount=8); W(tb, pr)
tr = N(ex, 'SDF_transform', Rotatey='=absTime.seconds*20'); W(pr, tr)
fr = N(ex, 'SDF_repeat', Mode='finite', Spacingx=0, Spacingy=2.0, Spacingz=0, Countx=0, County=1, Countz=0, Colorvary=0.5); W(tr, fr)
R(ex, fr, 3)
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
