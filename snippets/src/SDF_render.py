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
s = begin('SDF_render')
ex = example(s, 1, 'Smooth union scene', 'Chain of SDF nodes into SDF_render: sphere + torus (smooth union), a floor via a second combine.\nSoft shadows (Shadow Hardness) and AO are on; fog is off by default. Try Key Azimuth/Elevation.')
a = N(ex, 'SDF_sphere', Radius=0.8, Colorr=0.9, Colorg=0.35, Colorb=0.3)
t = N(ex, 'SDF_torus', Majorradius=1.0, Minorradius=0.25, Colorr=0.3, Colorg=0.6, Colorb=0.95)
tt = N(ex, 'SDF_transform', Translatex='=0.9*math.sin(absTime.seconds)', Rotatex=90); W(t, tt)
c = N(ex, 'SDF_combine', Smooth=0.45); W(a, c, 0); W(tt, c, 1)
f = N(ex, 'SDF_plane', Offset=-1.0)
c2 = N(ex, 'SDF_combine', Smooth=0.0); W(c, c2, 0); W(f, c2, 1)
R(ex, c2, 1, Shadows=14.0)
ex = example(s, 2, 'Camera COMP', 'The Camera parameter takes a Camera COMP, so the SDF lines up with Render TOP scenes (same position, rotation and FOV). Empty = built-in orbiting camera.\nThis Camera COMP orbits the gyroid; edit its FOV or move it by hand.')
g = N(ex, 'SDF_gyroid', Boundradius=1.3, Thickness=0.4)
cam = ORBIT(ex, dist=4.0, height=1.2, speed=0.5, fov=65)
r = R(ex, g, 2)
r.par.Camera = cam
ex = example(s, 3, 'Mirror blob and the normals output', 'Reflectivity mirrors the environment; a studio-light GLSL TOP feeds in2 (use an HDRI equirect instead for realism).\nout2 depth, out3 view normals and out4 world position are separate outputs: the Select TOP next to the result shows the normals.')
sp = N(ex, 'SDF_sphere', Radius=0.9)
d = N(ex, 'SDF_deform', Mode='noise', Amount=0.1, Frequency=2.5, Noiseoffsetx='=absTime.seconds*0.4'); W(sp, d)
f = N(ex, 'SDF_plane', Offset=-1.0, Colorr=0.35, Colorg=0.35, Colorb=0.4)
c = N(ex, 'SDF_combine', Smooth=0.0); W(d, c, 0); W(f, c, 1)
r = N(ex, 'SDF_render', Resolutionw=960, Resolutionh=540, Reflectivity=0.9, Shadows=0.0, Stepscale=0.7); W(c, r)
connect(studio(ex), r, 0, 1)
out(ex, 3, r)
nrm = ex.create(selectTOP, 'normals'); nrm.par.top = r.op('out3')
nrm.viewer = True
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
