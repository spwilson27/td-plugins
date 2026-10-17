# ---- matB shared helpers (prepended into each build.py by _matB/mk.sh; self-contained) ----
import os, td, math
ROOT = os.path.expanduser('~/software/td-plugins')

def readf(name, fn):
    return open(os.path.join(ROOT, 'components', name, fn)).read()

def fresh(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    o = b.op(name)
    if o: o.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, nm, text):
    d = c.create(td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    """spec: {page: [(kind, name, label, default, opts)]} kind: f,i,t,m,p,rgb,wh,xy,s"""
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            ps = {'f': pg.appendFloat, 'i': pg.appendInt, 't': pg.appendToggle, 'p': pg.appendPulse,
                  's': pg.appendStr, 'm': pg.appendMenu, 'rgb': pg.appendRGB, 'wh': pg.appendWH,
                  'xy': pg.appendXY}[kind](nm, label=lab)
            if kind == 'm':
                ps[0].menuNames = [m[0] for m in o['menu']]; ps[0].menuLabels = [m[1] for m in o['menu']]
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                p.default = v; p.val = v
                if 'min' in o: p.min = o['min']; p.normMin = o['min']; p.clampMin = o.get('clamp', False)
                if 'max' in o: p.max = o['max']; p.normMax = o['max']; p.clampMax = o.get('clamp', False)
    return c

PH = ("((parent().par.Phase if parent().par.Timesource=='phase' else absTime.seconds*parent().par.Speed/"
      "(parent().par.Loopbeats*60.0/parent().par.Bpm if parent().par.Loopbeats>0 else parent().par.Loopseconds)) % 1.0)")
PHU = PH.replace(" % 1.0)", ")")  # unwrapped (for rotation)

LOOP_PAGE = [
  ('m','Timesource','Time Source','abstime',{'menu':[('abstime','Abs Time'),('phase','Phase (external)')]}),
  ('f','Phase','Phase',0.0,{'min':0,'max':1}),
  ('f','Loopseconds','Loop Seconds',12.0,{'min':0.5,'max':120}),
  ('f','Loopbeats','Loop Beats (0=use seconds)',0.0,{'min':0,'max':64}),
  ('f','Bpm','BPM',120.0,{'min':20,'max':300}),
  ('f','Speed','Speed',1.0,{'min':0,'max':4}),
]
PREVIEW_PAGE = [
  ('wh','Resolution','Resolution',[1280,720],{'min':16,'max':8192}),
  ('f','Exposure','Exposure',1.0,{'min':0,'max':4}),
  ('f','Bloom','Bloom',0.25,{'min':0,'max':2}),
  ('i','Spinturns','Spin Turns / Loop',1,{'min':0,'max':8}),
  ('f','Tilt','Knot Tilt',20.0,{'min':-90,'max':90}),
  ('f','Camdist','Camera Distance',7.0,{'min':3,'max':20}),
  ('f','Backdrop','Backdrop Brightness',1.0,{'min':0,'max':4}),
]
ENV_PAR = [
  ('f','Envrot','Env Rotation',0.0,{'min':-180,'max':180}),
  ('f','Envint','Env Intensity',1.0,{'min':0,'max':4}),
]

def vecs(m, items):
    """items: list of (uniformName, [4 vals or expr strings])"""
    m.seq.vec.numBlocks = len(items)
    for i, (nm, vs) in enumerate(items):
        getattr(m.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', list(vs) + [0] * (4 - len(vs))):
            p = getattr(m.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v

def make_mat(c, pix, vert, uniforms):
    """GLSL MAT named 'mat' with shared env uniform + material uniforms."""
    m = c.create(td.glslMAT, 'mat')
    m.par.vdat.eval().text = vert; m.par.pdat.eval().text = pix
    env = ('uEnv', ['math.radians(parent().par.Envrot)', 'parent().par.Envint', PH, 0])
    vecs(m, [env] + list(uniforms))
    return m

def build_scene(c, mat, shells=None):
    """preview: sphere + torus knot, camera, render, tonemap/bloom -> out1.  shells: expr string for instancing count or None"""
    # knot SOP
    knot = c.create(td.scriptSOP, 'knot'); knot.par.callbacks.eval().text = KNOT_CB
    sph = c.create(td.sphereSOP, 'sphere'); sph.par.type = 'poly'; sph.par.freq = 24; sph.par.normals = True
    geos = []
    for nm, sop, tx in (('geo_sphere', sph, -1.45), ('geo_knot', knot, 1.5)):
        g = c.create(td.geometryCOMP, nm)
        for ch in list(g.children): ch.destroy()
        s2 = g.create(td.inSOP if False else td.selectSOP, 'sel'); s2.par.sop = '../' + sop.name
        s2.render = True; s2.display = True
        g.par.material = mat
        g.par.tx = tx
        if shells:
            g.par.instancing = True
            g.par.instancecountmode = 'manual' if 'manual' in g.par.instancecountmode.menuNames else g.par.instancecountmode.eval()
            g.par.numinstances.expr = shells
        geos.append(g)
    gs, gk = geos
    gs.par.ry.expr = "360*parent().par.Spinturns*" + PHU
    gs.par.rx = 0
    gk.par.ry.expr = "-360*parent().par.Spinturns*" + PHU
    gk.par.rx.expr = "parent().par.Tilt"
    cam = c.create(td.cameraCOMP, 'cam')
    cam.par.tz.expr = "parent().par.Camdist"; cam.par.ty = 0.15; cam.par.fov = 50
    cam.par.near = 0.5; cam.par.far = 60
    lt = c.create(td.lightCOMP, 'light'); lt.par.ty = 3; lt.par.tz = 4
    r = c.create(td.renderTOP, 'render')
    r.par.camera = 'cam'; r.par.geometry = 'geo_sphere geo_knot'; r.par.lights = 'light'
    r.par.outputresolution = 'custom'
    r.par.resolutionw.expr = 'parent().par.Resolutionw'; r.par.resolutionh.expr = 'parent().par.Resolutionh'
    r.par.bgcolora = 0; r.par.bgcolorr = 0; r.par.bgcolorg = 0; r.par.bgcolorb = 0
    r.par.antialias = 'aa4' if 'aa4' in r.par.antialias.menuNames else r.par.antialias.eval()
    r.par.format = 'rgba16float'
    th = c.create(td.glslTOP, 'bright'); th.inputConnectors[0].connect(r)
    th.par.pixeldat = mkdat(c, 'bright_code', BRIGHT); th.par.format = 'rgba16float'
    th.par.outputresolution = 'custom'; th.par.resolutionw.expr = 'parent().par.Resolutionw/2'; th.par.resolutionh.expr = 'parent().par.Resolutionh/2'
    b1 = c.create(td.blurTOP, 'bloom1'); b1.inputConnectors[0].connect(th); b1.par.size = 8; b1.par.extend = 'hold'
    b2 = c.create(td.blurTOP, 'bloom2'); b2.inputConnectors[0].connect(th); b2.par.size = 40; b2.par.extend = 'hold'
    for b in (b1, b2):
        b.par.format = 'rgba16float'
    t = c.create(td.glslTOP, 'tonemap')
    t.par.pixeldat = mkdat(c, 'tonemap_code', TONEMAP)
    for i, s in enumerate((r, b1, b2)): t.inputConnectors[i].connect(s)
    t.par.outputresolution = 'custom'
    t.par.resolutionw.expr = 'parent().par.Resolutionw'; t.par.resolutionh.expr = 'parent().par.Resolutionh'
    t.par.format = 'rgba16float'
    t.seq.vec.numBlocks = 1
    t.par.vec0name = 'uPrev'
    for ax, e in zip('xyzw', ['parent().par.Exposure', 'parent().par.Bloom', 'parent().par.Backdrop', 0]):
        p = getattr(t.par, 'vec0value' + ax)
        if isinstance(e, str): p.expr = e
    o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(t)
    return o

def report(c):
    errs = []
    for o in [c] + c.findChildren():
        for s in (o.errors(), o.warnings(), o.scriptErrors()):
            if s: errs.append((o.path, s[:400]))
    print('ERRS', errs)

def finish(c, name):
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True); c.save(p); print('saved', p)

KNOT_CB = '''
import math
def cl(t):
    r = 0.6 + 0.28*math.cos(3*t)
    return (r*math.cos(2*t), 0.28*math.sin(3*t), r*math.sin(2*t))
def onCook(scriptOp):
    scriptOp.clear()
    nu, nv = 256, 24
    scriptOp.pointAttribs.create('N')
    pts = []
    for i in range(nu):
        t = 2*math.pi*i/nu; e = 1e-3
        p0 = cl(t); p1 = cl(t+e)
        T = [p1[k]-p0[k] for k in range(3)]; l = math.sqrt(sum(x*x for x in T)); T = [x/l for x in T]
        up = (0, 1, 0)
        B = [T[1]*up[2]-T[2]*up[1], T[2]*up[0]-T[0]*up[2], T[0]*up[1]-T[1]*up[0]]
        lb = math.sqrt(sum(x*x for x in B)); B = [x/lb for x in B]
        Nn = [B[1]*T[2]-B[2]*T[1], B[2]*T[0]-B[0]*T[2], B[0]*T[1]-B[1]*T[0]]
        row = []
        for j in range(nv):
            a = 2*math.pi*j/nv
            n = [math.cos(a)*Nn[k]+math.sin(a)*B[k] for k in range(3)]
            q = scriptOp.appendPoint()
            q.x = p0[0]+0.15*n[0]; q.y = p0[1]+0.15*n[1]; q.z = p0[2]+0.15*n[2]
            q.N = tuple(n)
            row.append(q)
        pts.append(row)
    for i in range(nu):
        for j in range(nv):
            a = pts[i][j]; b = pts[(i+1) % nu][j]; c = pts[(i+1) % nu][(j+1) % nv]; d = pts[i][(j+1) % nv]
            poly = scriptOp.appendPoly(4, closed=True, addPoints=False)
            for k, pp in enumerate((a, d, c, b)): poly[k].point = pp
'''

BRIGHT = '''
out vec4 fragColor;
void main(){ vec3 c = texture(sTD2DInputs[0], vUV.st).rgb; fragColor = TDOutputSwizzle(vec4(max(c-vec3(1.0),vec3(0.0)),1.0)); }
'''
TONEMAP = '''
uniform vec4 uPrev; // exposure, bloom, backdrop
out vec4 fragColor;
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
void main(){
  vec2 uv = vUV.st;
  vec4 r = texture(sTD2DInputs[0], uv);
  vec3 b1 = texture(sTD2DInputs[1], uv).rgb, b2 = texture(sTD2DInputs[2], uv).rgb;
  vec2 q = uv - vec2(0.5, 0.45);
  float vig = 1.0 - dot(q*vec2(1.0,1.2), q*vec2(1.0,1.2))*1.6;
  vec3 bg = mix(vec3(0.008,0.008,0.010), vec3(0.045,0.047,0.055), clamp(vig,0.,1.)) * uPrev.z;
  // soft floor glow under objects
  bg += vec3(0.02,0.021,0.024)*uPrev.z*exp(-pow((uv.y-0.2)/0.12,2.0))*0.5;
  vec3 obj = r.rgb;                     // render is premultiplied by coverage
  vec3 col = bg*(1.0-r.a) + obj;
  col += (b1*0.6 + b2*0.9)*uPrev.y;
  col = aces(col*uPrev.x);
  col = pow(col, vec3(1.0/2.2));
  fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
# ---- end matB helpers ----
# ---- v2: Clock CHOP, modulation In CHOP ----
_OLD_PH = PH
def _wrap(s):
    ck = "parent().par.Clock.eval()"
    return "(%s['phase'].eval() if (parent().par.Timesource=='phase' and %s) else %s)" % (ck, ck, s)
PH = _wrap(_OLD_PH)
if 'PHU' in globals(): PHU = _wrap(_OLD_PH.replace(" % 1.0)", ")"))
def MOD(ch):
    """expression term: modulation channel (0 when the mod In CHOP is unconnected) * Modamount"""
    return "parent().op('mod')['%s'].eval()*parent().par.Modamount" % ch
def add_modsetup(c, inname):
    """Loop.Clock par, Material.Modamount par, optional modulation In CHOP -> merge over zero defaults -> Null 'mod'."""
    lp = [p for p in c.customPages if p.name == 'Loop'][0]
    lp.appendCHOP('Clock', label='Clock CHOP (phase)')
    mp = [p for p in c.customPages if p.name == 'Material'][0]
    q = mp.appendFloat('Modamount', label='Modulation Amount')[0]
    q.default = 1; q.val = 1; q.min = 0; q.max = 4; q.normMin = 0; q.normMax = 4
    i = c.create(td.inCHOP, inname)
    k = c.create(td.constantCHOP, 'mod_default')
    names = ['band1', 'band2', 'band3', 'band4', 'beat', 'phase']
    k.seq.const.numBlocks = len(names)
    for n, nm in enumerate(names):
        getattr(k.par, 'const%dname' % n).val = nm
        getattr(k.par, 'const%dvalue' % n).val = 0
    m = c.create(td.mergeCHOP, 'mod_merge'); m.par.duplicate = 'last'
    m.inputConnectors[0].connect(k); m.inputConnectors[1].connect(i)
    z = c.create(td.nullCHOP, 'mod'); z.inputConnectors[0].connect(m)

NAME = 'MAT_molten'
c = fresh(NAME)
pars(c, {
 'Material': [
  ('f','Heat','Heat (emission gain)',2.6,{'min':0,'max':20}),
  ('f','Cooling','Cooling',0.15,{'min':0,'max':1,'clamp':True}),
  ('f','Crackwidth','Crack Width',0.22,{'min':0,'max':1}),
  ('f','Crackscale','Crack Scale',2.2,{'min':0.3,'max':12}),
  ('f','Flow','Flow Warp',0.7,{'min':0,'max':2}),
  ('f','Streaks','Flow Streaks',0.6,{'min':0,'max':1}),
  ('f','Pulse','Pulse',0.4,{'min':0,'max':1}),
  ('f','Crustbump','Crust Relief',0.6,{'min':0,'max':2}),
  ('rgb','Crustcolor','Crust Color',[0.035,0.032,0.03],{'min':0,'max':1}),
  ('rgb','Glowtint','Glow Tint',[1,1,1],{'min':0,'max':2}),
 ] + ENV_PAR,
 'Preview': PREVIEW_PAGE,
 'Loop': LOOP_PAGE,
})
add_modsetup(c, 'in1')
pix = readf('_matB', 'common.glsl') + '\n' + readf(NAME, 'pixel.glsl')
vert = readf('_matB', 'vertex.glsl')
P = 'parent().par.'
m = make_mat(c, pix, vert, [
  ('uM0', [P+'Crackwidth', P+'Cooling', P+'Heat*(1+'+MOD('band1')+'*1.5+'+MOD('beat')+')', P+'Crackscale']),
  ('uM1', [P+'Flow', P+'Pulse', P+'Crustbump', P+'Streaks']),
  ('uCrust', [P+'Crustcolorr', P+'Crustcolorg', P+'Crustcolorb', 1]),
  ('uGlow', [P+'Glowtintr', P+'Glowtintg', P+'Glowtintb', 1]),
])
build_scene(c, m)
c.par.Bloom = 0.4; c.par.Bloom.default = 0.4
c.par.Envint = 0.8; c.par.Envint.default = 0.8
c.op('out1').comment = 'preview render'
finish(c, NAME)
report(c)
