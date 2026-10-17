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
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True); c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ---- loop helper (matl) ----
def add_loop(c):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]; p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute time', 'Phase (loop)']
    p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1
    p = pg.appendFloat('Loopseconds')[0]; p.default = 8; p.val = 8; p.min = 0.1; p.max = 120; p.normMin = 0.1; p.normMax = 60; p.clampMin = True
    p = pg.appendInt('Loopbeats')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 128; p.normMin = 0; p.normMax = 32; p.clampMin = True
    p = pg.appendFloat('Bpm')[0]; p.default = 120; p.val = 120; p.min = 20; p.max = 300; p.normMin = 20; p.normMax = 300
PH = ("(parent().par.Phase if parent().par.Timesource=='phase' else absTime.seconds/"
      "(parent().par.Loopseconds if parent().par.Loopbeats==0 else parent().par.Loopbeats*60.0/parent().par.Bpm))")
def P(n): return 'parent().par.' + n

# ---- matC helpers ----
def mkop(c, t, name, **kw):
    o = c.create(t, name)
    for k, v in kw.items():
        setattr(o.par, k, v)
    return o

def vecs(m, items):
    """items: list of (name, [4 vals or exprs]) -> sets GLSL MAT vector uniforms"""
    m.seq.vec.numBlocks = len(items)
    for i, (n, vals) in enumerate(items):
        m.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = m.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v

def samplers(m, items):
    m.seq.sampler.numBlocks = len(items)
    for i, (n, top, extra) in enumerate(items):
        m.par['sampler%dname' % i] = n
        m.par['sampler%dtop' % i] = top
        for k, v in (extra or {}).items():
            m.par['sampler%d%s' % (i, k)] = v

def make_mat(c, vert, pix, geo_src=None, name='mat'):
    m = c.create(td.glslMAT, name)
    m.par.glslversion = 'glsl430'
    m.par.vdat = mkdat(c, name + '_vert', vert)
    m.par.pdat = mkdat(c, name + '_pix', pix)
    if geo_src:
        m.par.gdat = mkdat(c, name + '_geom', geo_src)
    return m

def preview(c, mat, cam_z=5.6):
    """Preview page + sphere + torus + camera + render -> out1. mat = MAT op."""
    pg = c.appendCustomPage('Preview')
    ps = pg.appendWH('Resolution'); 
    for q, v in zip(ps, (1280, 720)):
        q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
    p = pg.appendInt('Turns')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 8; p.normMin = 0; p.normMax = 4; p.clampMin = True
    p = pg.appendRGB('Background'); 
    for q, v in zip(p, (0.012, 0.012, 0.014)):
        q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
    p = pg.appendFloat('Camdistance')[0]; p.default = cam_z; p.val = cam_z; p.min = 2; p.max = 20; p.normMin = 2; p.normMax = 12
    p = pg.appendToggle('Showtorus')[0]; p.default = 1; p.val = 1
    p = pg.appendToggle('Showsphere')[0]; p.default = 1; p.val = 1
    geos = []
    for nm, mk, tx in (('sphere_geo', td.sphereSOP, -1.45), ('torus_geo', td.torusSOP, 1.55)):
        g = c.create(td.geometryCOMP, nm)
        for ch in list(g.children): ch.destroy()
        s = g.create(mk, 'shape')
        if mk is td.sphereSOP:
            s.par.rows = 48; s.par.cols = 64; s.par.radx = 1.05; s.par.rady = 1.05; s.par.radz = 1.05
        else:
            s.par.rows = 40; s.par.cols = 96; s.par.radx = 0.95; s.par.rady = 0.38
        n = g.create(td.outSOP, 'out1'); n.inputConnectors[0].connect(s); n.render = True; n.display = True
        g.par.tx = tx
        g.par.material = mat.name if mat.parent() == c else mat.path
        geos.append(g)
    sg, tg = geos
    sg.par.ry.expr = '360*parent().par.Turns*' + PH
    tg.par.rx.val = 62
    tg.par.ry.expr = '360*parent().par.Turns*' + PH
    sg.par.display.expr = 'parent().par.Showsphere'; sg.par.render.expr = 'parent().par.Showsphere'
    tg.par.display.expr = 'parent().par.Showtorus'; tg.par.render.expr = 'parent().par.Showtorus'
    cam = c.create(td.cameraCOMP, 'cam'); cam.par.tz.expr = 'parent().par.Camdistance'; cam.par.fov = 58
    r = c.create(td.renderTOP, 'render')
    r.par.camera = cam.name; r.par.geometry = 'sphere_geo torus_geo'; r.par.lights = ''
    r.par.outputresolution = 'custom'; setres(r)
    r.par.format = 'rgba16float'; r.par.antialias = 'aa4'
    for k, a in zip('rgb', 'rgb'):
        r.par['bgcolor' + k].expr = 'parent().par.Background' + a
    r.par.bgcolora = 1
    o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(r)
    return o

def mat_geo_note():
    pass

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

COMP = 'MAT_matcap'; c = new_comp(COMP)
add_loop(c)
names = ['clay','chrome','pearl','toon','jade','gold','bone','blackglass','custom']
labels = ['Clay','Chrome','Pearl','Toon','Jade','Gold','Bone','Black glass','Custom (in1)']
add_pars(c, [
 ('Matcap','menu',list(zip(names, labels)),1),
 ('Tint','rgb',(1.0,1.0,1.0)), ('Tintamount','float',0.0,0,1,True),
 ('Brightness','float',1.0,0,4), ('Rotate','float',0.0,-180,180), ('Flipy','toggle',0),
 ('Spinmatcap','int',0,-8,8),
], 'Material')
inp = c.create(td.inTOP, 'in1')
code = rd(COMP, 'matcap.glsl')
gen = glsl(c, 'matcap_gen', code, vecs=[('uIdx', ["0 if parent().par.Matcap=='custom' else parent().par.Matcap.menuIndex", 0, 0, 0])], fmt='rgba16float')
gen.par.outputresolution = 'custom'; gen.par.resolutionw = 512; gen.par.resolutionh = 512
atlas = c.create(td.glslTOP, 'atlas')
atlas.par.pixeldat = gen.par.pixeldat.eval()
atlas.seq.vec.numBlocks = 1; atlas.par.vec0name = 'uIdx'; atlas.par.vec0valuex = -1
atlas.par.outputresolution = 'custom'; atlas.par.resolutionw = 1024; atlas.par.resolutionh = 512; atlas.par.format = 'rgba16float'
sw = c.create(td.switchTOP, 'matcap_sel')
sw.inputConnectors[0].connect(gen); sw.inputConnectors[1].connect(inp)
sw.par.index.expr = "1 if (parent().par.Matcap=='custom' and parent().inputConnectors[0].connections) else 0"
mcout = c.create(td.nullTOP, 'matcap_out'); mcout.inputConnectors[0].connect(sw)
mcout.par.filtertype = 'linear' if 'linear' in mcout.par.filtertype.menuNames else mcout.par.filtertype.eval()

add_modsetup(c, 'in2')
mat = make_mat(c, rd(COMP,'vert.glsl'), rd(COMP,'pix.glsl'), None, 'mat')
samplers(mat, [('uMatcap', mcout.name, {'extendu':'hold','extendv':'hold','filter':'linear'})])
Pp = lambda n: 'parent().par.' + n
vecs(mat, [
 ('uA', ["math.radians(parent().par.Rotate) + " + MOD("band2") + "*1.5 + 2*math.pi*parent().par.Spinmatcap*" + PH, Pp('Brightness')+'+'+MOD('band1')+'*0.8', Pp('Tintamount'), Pp('Flipy')]),
 ('uTint', [Pp('Tintr'), Pp('Tintg'), Pp('Tintb'), 0]),
])
o1 = preview(c, mat)
o2 = c.create(td.nullTOP, 'out2'); o2.inputConnectors[0].connect(mcout)
o3 = c.create(td.nullTOP, 'out3'); o3.inputConnectors[0].connect(atlas)
c.op('out1').comment = 'preview render'
c.op('out2').comment = 'matcap'; c.op('out3').comment = 'matcap atlas'
finish(c, COMP)
report(c)
