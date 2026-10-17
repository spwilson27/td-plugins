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
s = begin('SDF_to_MAT')
def rig(ex, mat_inst, extra=None):
    geo = ex.create(geometryCOMP, 'geo')
    for ch in list(geo.children): ch.destroy()
    b = geo.create(boxSOP, 'box'); b.par.sizex = b.par.sizey = b.par.sizez = 3.0; b.render = b.display = True
    cam = ex.create(cameraCOMP, 'cam', row=1); cam.par.tz = 7; cam.par.ty = 2.5; cam.par.rx = -19.6
    lt = ex.create(lightCOMP, 'light', row=1); lt.par.tx = 6; lt.par.ty = 10; lt.par.tz = 8
    r = ex.create(renderTOP, 'render')
    r.par.camera = cam; r.par.geometry = geo; r.par.lights = lt
    r.par.outputresolution = 'custom'; r.par.resolutionw = 960; r.par.resolutionh = 540
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.03; r.par.bgcolora = 1
    return geo, cam, lt, r
ex = example(s, 1, 'SDF inside a proxy box', 'SDF_to_MAT is a material: Apply To a Geometry COMP whose geometry covers the Bounds (here a Box SOP of size 3).\nThe fragment shader raymarches the SDF in the geometry\'s object space, so moving or rotating the Geometry COMP moves the SDF.')
f = N(ex, 'SDF_fractal', Iterations=6, Power=8.0)
m = N(ex, 'SDF_to_MAT', Epsilon=0.001); W(f, m)
geo, cam, lt, r = rig(ex, m)
geo.par.ry.expr = 'absTime.seconds * 25'
apply_material(m, geo)
out(ex, 1, r)
ex = example(s, 2, 'Depth composites with polygons', 'The material writes depth, so ordinary polygons intersect the raymarched SDF correctly: a plain Sphere SOP pokes through a gyroid.\nBoth live in the same Render TOP.')
g = N(ex, 'SDF_gyroid', Boundradius=1.4, Thickness=0.4)
m = N(ex, 'SDF_to_MAT'); W(g, m)
geo, cam, lt, r = rig(ex, m)
geo.par.ry.expr = 'absTime.seconds * 20'
sph = ex.create(geometryCOMP, 'ball')
for ch in list(sph.children): ch.destroy()
sp = sph.create(sphereSOP, 'sp'); sp.par.radx = sp.par.rady = sp.par.radz = 0.7; sp.render = sp.display = True
sph.par.tx.expr = '1.3*math.sin(absTime.seconds)'
r.par.geometry = geo.name + ' ' + sph.name
apply_material(m, geo)
out(ex, 2, r)
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
