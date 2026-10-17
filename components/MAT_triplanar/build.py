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
    sw.par.index.expr = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
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

PH = "(absTime.seconds/8.0)"   # internal preview animation phase (no loop parameters)
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

# ---- modulation In CHOP ----
def MOD(ch):
    """expression term: modulation channel (0 when the mod In CHOP is unconnected) * Modamount"""
    return "parent().op('mod')['%s'].eval()*parent().par.Modamount" % ch
def add_modsetup(c, inname):
    """Material.Modamount par, optional modulation In CHOP -> merge over zero defaults -> Null 'mod'."""
    mp = [p for p in c.customPages if p.name == 'Material'][0]
    q = mp.appendFloat('Modamount', label='Modulation Amount')[0]
    q.default = 1; q.val = 1; q.min = 0; q.max = 4; q.normMin = 0; q.normMax = 4
    i = c.create(td.inCHOP, inname)
    k = c.create(td.constantCHOP, 'mod_default')
    names = ['band1', 'band2', 'band3', 'band4', 'beat']
    k.seq.const.numBlocks = len(names)
    for n, nm in enumerate(names):
        getattr(k.par, 'const%dname' % n).val = nm
        getattr(k.par, 'const%dvalue' % n).val = 0
    m = c.create(td.mergeCHOP, 'mod_merge'); m.par.duplicate = 'last'
    m.inputConnectors[0].connect(k); m.inputConnectors[1].connect(i)
    z = c.create(td.nullCHOP, 'mod'); z.inputConnectors[0].connect(m)

COMP = 'MAT_triplanar'; c = new_comp(COMP)
add_pars(c, [
 ('Pattern','menu',[('noise','Noise'),('voronoi','Voronoi'),('stripes','Stripes'),('grid','Grid'),('checker','Checker'),('texture','Texture (in1)')],0),
 ('Space','menu',[('object','Object space'),('world','World space')],0),
 ('Scale','float',2.0,0.1,30), ('Sharpness','float',6.0,1,32),
 ('Color1','rgb',(0.02,0.02,0.025)), ('Color2','rgb',(0.88,0.85,0.78)),
 ('Roughness','float',0.45,0.04,1,True), ('Metallic','float',0.0,0,1,True),
 ('Contrast','float',1.4,0.1,8), ('Bump','float',0.35,0,1,True),
 ('Linewidth','float',0.12,0.01,0.9), ('Octaves','int',4,1,8), ('Texscale','float',0.5,0.05,4),
 ('Animate','float',0.6,0,3), ('Scroll','int',0,-8,8),
], 'Material')
inp = c.create(td.inTOP, 'in1')
fb = c.create(td.noiseTOP, 'defsrc'); fb.par.outputresolution = 'custom'; fb.par.resolutionw = 512; fb.par.resolutionh = 512
tsw = c.create(td.switchTOP, 'tex'); tsw.inputConnectors[0].connect(fb); tsw.inputConnectors[1].connect(inp)
tsw.par.index.expr = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
add_modsetup(c, 'in2')
mat = make_mat(c, rd(COMP,'vert.glsl'), rd(COMP,'pix.glsl'), None, 'mat')
samplers(mat, [('uTex', tsw.name, {'extendu':'repeat','extendv':'repeat','filter':'mipmap'})])
Pp = lambda n: 'parent().par.' + n
PHT = "(" + PH + ")"
vecs(mat, [
 ('uA', [Pp('Scale'), Pp('Sharpness'), 'parent().par.Pattern.menuIndex', 'parent().par.Space.menuIndex']),
 ('uB', [Pp('Roughness'), Pp('Metallic'), Pp('Contrast')+'+'+MOD('band1')+'*1.5', Pp('Bump')]),
 ('uC', [Pp('Animate'), Pp('Scroll'), PHT, Pp('Linewidth')]),
 ('uD', [Pp('Octaves'), Pp('Texscale'), 0, 0]),
 ('uCol1', [Pp('Color1r'), Pp('Color1g'), Pp('Color1b'), 0]),
 ('uCol2', [Pp('Color2r'), Pp('Color2g'), Pp('Color2b'), 0]),
])
preview(c, mat)
c.op('out1').comment = 'preview render'
finish(c, COMP)
report(c)
