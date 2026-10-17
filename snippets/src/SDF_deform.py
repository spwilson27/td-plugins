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
s = begin('SDF_deform')
ex = example(s, 1, 'Twisted box', 'SDF_deform (Twist) bends space around an axis, here Y. Amount is animated; Axis picks X/Y/Z.\nBend, Noise, Round and Onion are other modes.')
b = N(ex, 'SDF_box', Sizex=1.0, Sizey=2.2, Sizez=1.0, Roundness=0.05)
d = N(ex, 'SDF_deform', Mode='twist', Amount='=1.5*math.sin(absTime.seconds*0.8)'); W(b, d)
R(ex, d, 1, Stepscale=0.6)
ex = example(s, 2, 'Liquid chrome', 'Metaball spheres (smooth SDF_combine) with SDF_deform noise displacement, rendered mirror-like with Reflectivity.\nA studio-light environment (GLSL TOP) feeds SDF_render in2; the Noise Offset is animated.')
sp = [N(ex, 'SDF_sphere', Radius=0.6 - 0.07 * k) for k in range(3)]
tr = []
for k, s_ in enumerate(sp):
    t = N(ex, 'SDF_transform', Translatex='=0.8*math.sin(absTime.seconds*%g+%d)' % (0.8 + 0.3 * k, k), Translatey='=0.6*math.cos(absTime.seconds*%g+%d)' % (0.9 + 0.2 * k, 2 * k), Translatez='=0.7*math.sin(absTime.seconds*%g+%d)' % (0.7 + 0.25 * k, 3 * k))
    W(s_, t); tr.append(t)
c1 = N(ex, 'SDF_combine', Smooth=0.9); W(tr[0], c1, 0); W(tr[1], c1, 1)
c2 = N(ex, 'SDF_combine', Smooth=0.9); W(c1, c2, 0); W(tr[2], c2, 1)
d = N(ex, 'SDF_deform', Mode='noise', Amount=0.12, Frequency=3.0, Noiseoffsety='=absTime.seconds*0.5'); W(c2, d)
r = R(ex, d, 2, Reflectivity=0.95, Shadows=0.0, Ao=0.3, Stepscale=0.7)
connect(studio(ex), r, 0, 1)
ex = example(s, 3, 'Onion shell cutaway', 'Mode = onion turns a solid into a thin shell (Amount = thickness); combine (subtract) with a box to cut it open.\nRound inflates a shape instead.')
sp = N(ex, 'SDF_sphere', Radius=1.0, Colorr=0.9, Colorg=0.6, Colorb=0.3)
d = N(ex, 'SDF_deform', Mode='onion', Amount=0.06); W(sp, d)
bx = N(ex, 'SDF_box', Sizex=2.4, Sizey=1.0, Sizez=1.0)
tb = N(ex, 'SDF_transform', Translatex=0.8, Translatey=0.6, Rotatey='=absTime.seconds*30'); W(bx, tb)
c = N(ex, 'SDF_combine', Operation='subtract', Smooth=0.0); W(d, c, 0); W(tb, c, 1)
R(ex, c, 3)
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
