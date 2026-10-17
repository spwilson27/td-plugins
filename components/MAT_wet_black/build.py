# ---- shared helpers (pasted at top of each build.py by components/_lib/mk.sh) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

def setres(o, w='parent().par.Resolutionw', h='parent().par.Resolutionh'):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w; o.par.resolutionh.expr = h

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=False, filt=None):
    """vecs: list of (uniformName, [4 values/exprs]) ; exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:   # inputs beyond the 3 wire connectors go through the TOPs parameter (index 3..)
        g.par.tops = ' '.join(s.name for s in inputs[3:])
    if vecs:
        g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    if filt: g.par.filtertype = filt
    return g

def add_pars(c, specs, page='Controls'):
    """spec tuples: (name, kind, ...)
      ('Amount','float',default,min,max)   ('Count','int',def,min,max)  ('On','toggle',def)
      ('Reset','pulse')  ('Mode','menu',[(id,label),..],default_index)  ('Res','wh',(w,h))
      ('Col','rgb',(r,g,b))  ('Txt','str',default)  ('Xy','xy',(x,y))"""
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse':
            pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]
            p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            ps = pg.appendWH(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'xy':
            ps = pg.appendXY(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.normMin = -1; q.normMax = 1
        elif k == 'rgb':
            ps = pg.appendRGB(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def input_stage(c, comp, bg=1.0):
    """in1 + animated default source -> switch 'src' (resolution = Resolution par). Returns src TOP."""
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', rd(comp, 'src.glsl'), vecs=[('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish(c, name):
    report(c)
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)
    c.destroy()   # so validation cannot accidentally lean on /build paths

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# =============== matA shared: preview rig ===============
import math
SPEED = 'parent().par.Speed'
LOOPLEN = "(parent().par.Loopseconds if parent().par.Loopbeats==0 else parent().par.Loopbeats*60.0/parent().par.Bpm)"
# wrapped loop phase in [0,1): everything periodic in this
PHW = ("(((float(parent().par.Clock.eval()['phase']) if parent().par.Clock.eval() else parent().par.Phase) if parent().par.Timesource=='phase' else absTime.seconds*parent().par.Speed/%s) %% 1.0)" % LOOPLEN)

KNOT_CB = '''
import math
def onSetupParameters(scriptOp): return
def onPulse(par): return
def onCook(scriptOp):
    scriptOp.clear()
    U, V = 220, 28
    p, q = 2, 3
    R, r = 1.0, 0.34
    def C(u):
        cu = math.cos(q*u); su = math.sin(q*u)
        rad = R + 0.45*cu
        return (rad*math.cos(p*u), 0.45*su*1.0 + 0.0, rad*math.sin(p*u))
    def sub(a,b): return (a[0]-b[0],a[1]-b[1],a[2]-b[2])
    def cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    def nrm(a):
        l = math.sqrt(a[0]**2+a[1]**2+a[2]**2) or 1.0
        return (a[0]/l,a[1]/l,a[2]/l)
    pts = []
    for i in range(U):
        u = 2*math.pi*i/U
        e = 1e-3
        c0 = C(u); c1 = C(u+e); c2 = C(u-e)
        T = nrm(sub(c1,c2))
        # second derivative-ish normal
        acc = (c1[0]+c2[0]-2*c0[0], c1[1]+c2[1]-2*c0[1], c1[2]+c2[2]-2*c0[2])
        N = nrm(acc)
        B = nrm(cross(T,N))
        N = nrm(cross(B,T))
        for j in range(V):
            v = 2*math.pi*j/V
            cv, sv = math.cos(v), math.sin(v)
            P = (c0[0]+r*(cv*N[0]+sv*B[0]), c0[1]+r*(cv*N[1]+sv*B[1]), c0[2]+r*(cv*N[2]+sv*B[2]))
            pt = scriptOp.appendPoint()
            pt.P = P
            pts.append(pt)
    for i in range(U):
        for j in range(V):
            a = pts[i*V+j]; b = pts[((i+1)%U)*V+j]; c = pts[((i+1)%U)*V+(j+1)%V]; d = pts[i*V+(j+1)%V]
            poly = scriptOp.appendPoly(4, closed=True, addPoints=False)
            poly[0].point = a; poly[1].point = b; poly[2].point = c; poly[3].point = d
    return
'''

def preview_rig(c, comp, mat, geo='both', sphere_rows=64, sphere_pos=(-1.55, 0, 0), knot_pos=(1.4, 0, 0), sphere_rad=1.0, cam=(0, 0.35, 10.0), fov=36):
    """Builds Preview page + geos + camera + render + post -> out1. mat = the MAT op."""
    pg = c.appendCustomPage('Preview')
    p = pg.appendWH('Resolution'); 
    for q, v in zip(p, (1280, 720)):
        q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 64; q.normMax = 4096
    m = pg.appendMenu('Geometry')[0]
    m.menuNames = ['both', 'sphere', 'knot']; m.menuLabels = ['Sphere + Knot', 'Sphere', 'Torus knot']
    m.default = geo; m.val = geo
    q = pg.appendInt('Spin')[0]; q.default = 1; q.val = 1; q.min = 0; q.max = 8; q.normMin = 0; q.normMax = 4; q.clampMin = True
    q.label = 'Spin (turns per loop)'
    q = pg.appendFloat('Camdist')[0]; q.default = cam[2]; q.val = cam[2]; q.min = 2; q.max = 30; q.normMin = 3; q.normMax = 15
    q = pg.appendFloat('Backdrop')[0]; q.default = 1.0; q.val = 1.0; q.min = 0; q.max = 4; q.normMin = 0; q.normMax = 2
    q = pg.appendFloat('Exposure')[0]; q.default = 1.0; q.val = 1.0; q.min = 0.1; q.max = 8; q.normMin = 0.25; q.normMax = 4
    q = pg.appendFloat('Vignette')[0]; q.default = 0.6; q.val = 0.6; q.min = 0; q.max = 2; q.normMin = 0; q.normMax = 1.5

    # geometry
    sph = c.create(td.sphereSOP, 'sphere_sop')
    sph.par.type = 'mesh'; sph.par.surftype = 'quads'; sph.par.rows = sphere_rows; sph.par.cols = sphere_rows * 2
    sph.par.radx = sph.par.rady = sph.par.radz = sphere_rad
    sn = c.create(td.nullSOP, 'sphere_out'); sn.inputConnectors[0].connect(sph)
    sc = c.create(td.scriptSOP, 'knot_sop'); cb = mkdat(c, 'knot_cb', KNOT_CB); sc.par.callbacks = cb
    nm = c.create(td.facetSOP, 'knot_normals'); nm.par.postnml = True; nm.inputConnectors[0].connect(sc)
    tx = c.create(td.textureSOP, 'knot_uv'); tx.inputConnectors[0].connect(nm)
    kn = c.create(td.nullSOP, 'knot_out'); kn.inputConnectors[0].connect(tx)

    g1 = c.create(td.geometryCOMP, 'geo_sphere'); g2 = c.create(td.geometryCOMP, 'geo_knot')
    for g, src, pos, sc_ in ((g1, sn, sphere_pos, 1.0), (g2, kn, knot_pos, 0.78)):
        for ch in list(g.children): ch.destroy()
        # SOP reference via a Select SOP inside the geo
        sel = g.create(td.selectSOP, 'sel'); sel.par.sop = sel.relativePath(src)
        o = g.create(td.nullSOP, 'out'); o.inputConnectors[0].connect(sel); o.render = True; o.display = True
        g.par.tx, g.par.ty, g.par.tz = pos
        g.par.sx = g.par.sy = g.par.sz = sc_
        g.par.material = g.relativePath(mat)
    g1.par.ry.expr = "360.0*parent().par.Spin*%s" % PHW
    g2.par.ry.expr = "-360.0*parent().par.Spin*%s" % PHW
    g2.par.rx = 20; g2.par.rz = 0
    g1.par.render.expr = "parent().par.Geometry in ('both','sphere')"
    g2.par.render.expr = "parent().par.Geometry in ('both','knot')"
    # center single objects
    g1.par.tx.expr = "%s if parent().par.Geometry=='both' else 0" % sphere_pos[0]
    g2.par.tx.expr = "%s if parent().par.Geometry=='both' else 0" % knot_pos[0]

    cm = c.create(td.cameraCOMP, 'cam')
    cm.par.tx = cam[0]; cm.par.ty = cam[1]; cm.par.tz.expr = 'parent().par.Camdist'
    cm.par.rx = -2.0
    cm.par.fov = fov

    r = c.create(td.renderTOP, 'render')
    r.par.camera = r.relativePath(cm); r.par.geometry = ' '.join([r.relativePath(g1), r.relativePath(g2)]); r.par.lights = ''
    r.par.antialias = 'aa4'; r.par.dither = False
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0; r.par.bgcolora = 0
    setres(r); r.par.format = 'rgba16float'

    post = glsl(c, 'post', open(os.path.join(ROOT, 'components', '_matA', 'post.glsl')).read(), inputs=[r],
                vecs=[('uPost', ['parent().par.Backdrop', 'parent().par.Exposure', 'parent().par.Vignette', 'absTime.seconds']),
                      ('uRes', ['parent().par.Resolutionw', 'parent().par.Resolutionh', 0, 0])], fmt='rgba16float', res=True)
    out = c.create(td.outTOP, 'out1'); out.comment = 'preview'; out.inputConnectors[0].connect(post)
    return out

def mat_uniforms(m, vecs, samplers=()):
    m.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        m.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            pp = m.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): pp.expr = v
            else: pp.val = v
    if samplers:
        m.seq.sampler.numBlocks = len(samplers)
        for i, (n, top) in enumerate(samplers):
            m.par['sampler%dname' % i] = n
            m.par['sampler%dtop' % i] = top

def make_mat(c, name, vtxt, ptxt):
    m = c.create(td.glslMAT, name)
    vd = mkdat(c, name + '_vertex', vtxt); pd = mkdat(c, name + '_pixel', ptxt)
    m.par.vdat = vd; m.par.pdat = pd
    return m

def env_inputs(c):
    """in1 (TOP envmap, optional) and in2 (CHOP modulation, optional) + shared Env pars. returns (envtop, modchop)"""
    i1 = c.create(td.inTOP, 'in1'); i1.par.connectorder = 1
    i2 = c.create(td.inCHOP, 'in2'); i2.par.connectorder = 2
    return i1, i2

def mod_chop(c, i2):
    k = c.create(td.constantCHOP, 'mod_default'); k.par.name0 = 'mod'; k.par.value0 = 0
    sw = c.create(td.switchCHOP, 'mod_sel'); sw.inputConnectors[0].connect(k); sw.inputConnectors[1].connect(i2)
    sw.par.index.expr = "1 if any(o.isCHOP for o in parent().inputs) else 0"
    return sw

def env_pars(pg_name_page):
    """spec list for the shared Environment controls (append to add_pars specs)"""
    return [('Envmix', 'float', 0.0, 0, 1), ('Envrot', 'float', 0.0, 0, 1), ('Envgain', 'float', 1.0, 0, 8),
            ('Accent', 'float', 0.35, 0, 2)]

def time_pars(c):
    add_loop(c)

# ---- loop helper (matl) ----
def add_loop(c):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]; p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute time', 'Phase (loop)']
    p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1
    pg.appendCHOP('Clock')
    p = pg.appendFloat('Loopseconds')[0]; p.default = 8; p.val = 8; p.min = 0.1; p.max = 120; p.normMin = 0.1; p.normMax = 60; p.clampMin = True
    p = pg.appendInt('Loopbeats')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 128; p.normMin = 0; p.normMax = 32; p.clampMin = True
    p = pg.appendFloat('Bpm')[0]; p.default = 120; p.val = 120; p.min = 20; p.max = 300; p.normMin = 20; p.normMax = 300
PH = ("((float(parent().par.Clock.eval()['phase']) if parent().par.Clock.eval() else parent().par.Phase) if parent().par.Timesource=='phase' else absTime.seconds/"
      "(parent().par.Loopseconds if parent().par.Loopbeats==0 else parent().par.Loopbeats*60.0/parent().par.Bpm))")
def P(n): return 'parent().par.' + n

COMP = 'MAT_wet_black'; c = new_comp(COMP)
ENV = rd('_matA', 'env.glsl')
vtx = rd('_matA', 'vtx.glsl')
pix = rd('MAT_wet_black', 'pixel.glsl')
add_pars(c, [
    ('Wetness', 'float', 0.9, 0, 1),
    ('Bump', 'float', 1.0, 0, 4),
    ('Scale', 'float', 1.6, 0.1, 10),
    ('Flow', 'float', 1.0, 0, 4),
    ('Dripscale', 'float', 1.0, 0.2, 5),
    ('Dripamt', 'float', 0.9, 0, 3),
    ('Roughness', 'float', 0.03, 0, 1),
    ('Reflect', 'float', 3.0, 0, 10),
    ('Basecolor', 'rgb', (0.012, 0.012, 0.014)),
    ('Speed', 'float', 1.0, 0, 8),
    ('Envmix', 'float', 0.0, 0, 1), ('Envrot', 'float', 0.0, 0, 1), ('Envgain', 'float', 1.0, 0, 8),
    ('Accent', 'float', 0.5, 0, 2),
], page='Material')
add_loop(c)
i1, i2 = env_inputs(c)
m = make_mat(c, 'mat', vtx, ENV + pix)
mat_uniforms(m, [
    ('uP0', [PHW, P('Envmix'), P('Envrot'), P('Envgain')]),
    ('uP1', [P('Accent'), 0, 0, 0]),
    ('uW0', [P('Wetness'), P('Bump'), P('Scale'), P('Flow')]),
    ('uW1', [P('Dripscale'), P('Dripamt'), P('Roughness'), P('Reflect')]),
    ('uW2', [P('Basecolorr'), P('Basecolorg'), P('Basecolorb'), 0]),
], samplers=[('sEnv', 'in1')])
preview_rig(c, COMP, m)
finish(c, COMP)
