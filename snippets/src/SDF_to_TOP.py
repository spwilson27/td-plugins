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
SLICE = """uniform vec4 uT;
out vec4 fragColor;
void main(){
    vec3 uvw = vec3(vUV.st, 0.5 + 0.35 * sin(uT.x * 0.7));
    vec4 s = texture(sTD3DInputs[0], uvw);
    float d = s.r;
    float iso = 0.5 + 0.5 * cos(d * 40.0);
    vec3 col = (d < 0.0 ? vec3(0.9, 0.5, 0.3) : vec3(0.3, 0.5, 0.9)) * (0.25 + 0.75 * iso * exp(-abs(d) * 1.5));
    if (abs(d) < 0.01) col = vec3(1.0);
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}"""
s = begin('SDF_to_TOP')
ex = example(s, 1, 'Slice through the baked volume', 'SDF_to_TOP bakes the SDF into a 3D texture (R = distance, GBA = color) over the Bounds at the given Resolution.\nA GLSL TOP samples a moving slice and draws distance isolines: white = the surface, orange = inside.')
g = N(ex, 'SDF_gyroid', Boundradius=1.2)
b = N(ex, 'SDF_to_TOP', Resolution=96, Boundssizex=3.0, Boundssizey=3.0, Boundssizez=3.0); W(g, b)
dt = ex.create(textDAT, 'slice_code'); dt.text = SLICE
gl = ex.create(glslTOP, 'slice'); gl.par.pixeldat = dt
gl.par.outputresolution = 'custom'; gl.par.resolutionw = 768; gl.par.resolutionh = 768
gl.seq.vec.numBlocks = 1; gl.par.vec0name = 'uT'; gl.par.vec0valuex.expr = 'absTime.seconds'
connect(b, gl)
out(ex, 1, gl)
ex = example(s, 2, 'Resolution is a trade-off', 'The same SDF baked at Resolution 24: the node preview raymarches the baked volume (trilinear), so you see exactly what the 3D texture holds.\nUse a larger Bounds with higher Resolution for bigger scenes; the 3D TOP feeds any GLSL TOP that samples sTD3DInputs.')
t = N(ex, 'SDF_torus', Majorradius=0.8, Minorradius=0.3)
b = N(ex, 'SDF_to_TOP', Resolution=24); W(t, b)
sel = ex.create(selectTOP, 'baked_view'); sel.par.top = b.op('preview')
out(ex, 2, sel)
for c_ in s.findChildren(type=COMP, depth=1):
    if c_.par.externaltox.eval(): c_.par.reloadcustom = False
finish(s)
