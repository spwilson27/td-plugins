# G-buffer demo scene shared by TOP_depth_fog / TOP_ssao / TOP_env_reflect / TOP_normal_shade (and their snippets).
# exec() inside TD, then:  g = make_gbuffer(parent_comp, res=('1280','720'), time='absTime.seconds', prefix='')
# Renders Sphere/Torus/Box POPs with a GLSL MAT that writes three colour buffers (one Render TOP):
#   buffer 0  lit colour               (RGB, A=1 on geometry, 0 on sky)
#   buffer 1  LINEAR eye-space depth   (R = distance along the view axis in world units, GBA = same, A=1 on geometry, 0 on sky)
#   buffer 2  VIEW-space normals       (RGB in -1..1, +Z toward the camera, A=1 on geometry)
#   (normal buffer alpha doubles as an objects-only mask: 1 on shapes, 0 on the floor / sky)
# Returns dict(color=, depth=, normal=, render=, cam=) of TOPs (Render Select TOPs for buffers 0..2).
import td, math

GB_VERT = '''
out vec3 vNrmView;
out float vViewZ;
out vec3 vWorld;
void main(){
    vec4 w = TDDeform(TDPos());
    vec3 nw = normalize(TDDeformNorm(TDNormal()));
    mat4 cam = uTDMats[TDCameraIndex()].cam;
    vNrmView = mat3(cam) * nw;
    vViewZ = -(cam * w).z;
    vWorld = w.xyz;
    gl_Position = TDWorldToProj(w);
}
'''

GB_PIX = '''
uniform vec4 uCol;     // rgb albedo, a = pattern strength
in vec3 vNrmView;
in float vViewZ;
in vec3 vWorld;
layout(location = 0) out vec4 oColor;
layout(location = 1) out vec4 oDepth;
layout(location = 2) out vec4 oNormal;
void main(){
    TDCheckDiscard();
    vec3 n = normalize(vNrmView);
    if (!gl_FrontFacing) n = -n;
    vec3 alb = uCol.rgb;
    vec2 g = floor(vWorld.xz * 1.0);
    float chk = mod(g.x + g.y, 2.0);
    alb *= mix(1.0, 0.45 + 0.55 * chk, uCol.a);
    vec3 L = normalize(vec3(-0.5, 0.8, 0.6));
    float nl = max(dot(n, L), 0.0);
    vec3 H = normalize(L + vec3(0.0, 0.0, 1.0));
    float spec = pow(max(dot(n, H), 0.0), 40.0) * 0.35;
    float rim = pow(1.0 - clamp(n.z, 0.0, 1.0), 3.0) * 0.25;
    vec3 c = alb * (0.16 + 0.9 * nl) + spec + rim * vec3(0.5, 0.6, 0.8);
    oColor = TDOutputSwizzle(vec4(c, 1.0));
    oDepth = vec4(vec3(vViewZ), 1.0);
    oNormal = vec4(n, uCol.a > 0.5 ? 0.0 : 1.0);   // A = 'objects' mask (1 on the shapes, 0 on the floor): used as a reflection mask by the demos
}
'''

def make_gbuffer(c, res=('1280', '720'), time='absTime.seconds', prefix='', camdist=13.0, aa='aa1'):
    P = prefix
    def mkdat(name, s):
        d = c.create(td.textDAT, P + name); d.text = s; return d
    vd, pd = mkdat('gb_vert', GB_VERT), mkdat('gb_pix', GB_PIX)
    mats = {}
    for nm, col in (('floor', (0.62, 0.6, 0.56, 1.0)), ('sphere', (0.85, 0.25, 0.2, 0.0)),
                    ('torus', (0.2, 0.55, 0.85, 0.0)), ('box', (0.9, 0.8, 0.3, 0.0))):
        m = c.create(td.glslMAT, P + 'gb_mat_' + nm)
        m.par.glslversion = 'glsl430'
        m.par.vdat = vd; m.par.pdat = pd
        m.seq.vec.numBlocks = 1
        m.par.vec0name = 'uCol'
        for ax, v in zip('xyzw', col): m.par['vec0value' + ax] = v
        mats[nm] = m
    geos = []
    def geo(nm, mk, setup, mat, tx, ty, tz, rx=0, ry=0, rz=0):
        g = c.create(td.geometryCOMP, P + 'gb_' + nm)
        for ch in list(g.children): ch.destroy()
        s = g.create(mk, 'shape'); setup(s)
        s.par.texture = s.par.texture.menuNames[1]
        s.display = True; s.render = True
        g.par.material = mat
        for k, e in (('tx', tx), ('ty', ty), ('tz', tz), ('rx', rx), ('ry', ry), ('rz', rz)):
            if isinstance(e, str): g.par[k].expr = e
            else: g.par[k] = e
        geos.append(g)
        return g
    T = time
    def sph(s): s.par.type = 'sharedpoles'; s.par.rows = 40; s.par.cols = 64; s.par.normal = 'pointNormals'; s.par.radx = s.par.rady = s.par.radz = 1.2
    def tor(s): s.par.rows = 36; s.par.cols = 72; s.par.normal = 'pointNormals'; s.par.radx = 1.25; s.par.rady = 0.5
    def bx(s): s.par.sizex = s.par.sizey = s.par.sizez = 1.7; s.par.uniquepoints = True; s.par.normal = 'pointNormals'
    def fl(s): s.par.sizex = 80; s.par.sizey = 0.2; s.par.sizez = 80; s.par.uniquepoints = True; s.par.normal = 'pointNormals'
    geo('floor', td.boxPOP, fl, mats['floor'], 0, -1.3, 0)
    geo('sphere', td.spherePOP, sph, mats['sphere'], -2.4, 'math.sin(%s*0.9)*0.25' % T, -0.5)
    geo('torus', td.torusPOP, tor, mats['torus'], 0.3, 'math.cos(%s*0.7)*0.2-0.1' % T, 1.4, rx='62+%s*18' % T, ry='%s*25' % T)
    geo('box', td.boxPOP, bx, mats['box'], 2.7, -0.3, -1.6, ry='%s*30+20' % T, rx='%s*12' % T)
    cam = c.create(td.cameraCOMP, P + 'gb_cam')
    cam.par.tz = camdist; cam.par.ty = 3.2; cam.par.rx = -math.degrees(math.atan2(3.2, camdist)) * 0.8
    cam.par.fov = 40; cam.par.near = 0.5; cam.par.far = 100
    lt = c.create(td.lightCOMP, P + 'gb_light')
    r = c.create(td.renderTOP, P + 'gb_render')
    r.par.camera = cam; r.par.geometry = ' '.join(g.name for g in geos); r.par.lights = lt
    r.par.numcolorbufs = 3
    r.par.outputresolution = 'custom'
    r.par.resolutionw.expr = res[0]; r.par.resolutionh.expr = res[1]
    r.par.format = 'rgba32float'; r.par.antialias = aa
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = r.par.bgcolora = 0
    outs = {}
    for i, nm in enumerate(('color', 'depth', 'normal')):
        s = c.create(td.renderselectTOP, P + 'gb_' + nm)
        s.par.top = r; s.par.bufferindex = i
        s.par.outputresolution = 'useinput'
        outs[nm] = s
    outs.update(render=r, cam=cam)
    return outs


SKY_GLSL = '''
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec4 c = texture(sTD2DInputs[0], uv);
    float h = smoothstep(0.50, 0.86, uv.y);
    vec3 sky = mix(vec3(0.50, 0.46, 0.46), vec3(0.08, 0.14, 0.30), h);
    fragColor = TDOutputSwizzle(vec4(mix(sky, c.rgb, c.a), 1.0));
}
'''

def add_sky(c, col, res=('1280', '720'), prefix=''):
    """Composite the G-buffer colour (alpha = coverage) over a dusk sky gradient. Returns the new GLSL TOP."""
    sk = c.create(td.glslTOP, prefix + 'gb_sky')
    dat = c.create(td.textDAT, prefix + 'gb_sky_code'); dat.text = SKY_GLSL
    sk.par.pixeldat = dat
    sk.inputConnectors[0].connect(col); sk.par.format = 'rgba16float'
    sk.par.outputresolution = 'custom'
    sk.par.resolutionw.expr = res[0]; sk.par.resolutionh.expr = res[1]
    return sk

MASK_GLSL = '''
out vec4 fragColor;
void main(){ fragColor = TDOutputSwizzle(vec4(vec3(texture(sTD2DInputs[0], vUV.st).a), 1.0)); }
'''

def add_mask(c, normal, res=('1280', '720'), prefix=''):
    """Objects-only mask (R) taken from the G-buffer normals alpha."""
    m = c.create(td.glslTOP, prefix + 'gb_mask')
    dat = c.create(td.textDAT, prefix + 'gb_mask_code'); dat.text = MASK_GLSL
    m.par.pixeldat = dat; m.inputConnectors[0].connect(normal); m.par.format = 'rgba16float'
    m.par.outputresolution = 'custom'
    m.par.resolutionw.expr = res[0]; m.par.resolutionh.expr = res[1]
    return m

def demo_comp(c, outs=('color', 'depth', 'normal'), sky=True):
    """Base COMP 'demo' holding the G-buffer scene (preview only). Returns the COMP; its Out TOPs
    (o_color / o_depth / o_normal, in that connector order) carry the requested buffers. Resolution follows ../res."""
    d = c.create(td.baseCOMP, 'demo')
    R = ("op('../res')['w']", "op('../res')['h']")
    g = make_gbuffer(d, res=R)
    col = add_sky(d, g['color'], R) if sky else g['color']
    srcs = dict(color=col, depth=g['depth'], normal=g['normal'])
    if 'mask' in outs: srcs['mask'] = add_mask(d, g['normal'], R)
    for i, nm in enumerate(outs):
        o = d.create(td.outTOP, 'o_' + nm); o.inputConnectors[0].connect(srcs[nm])
        if hasattr(o.par, 'connectorder'): o.par.connectorder = i
    return d
