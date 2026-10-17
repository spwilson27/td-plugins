# ---- v3 helpers (self-contained) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
COMP = 'GEN_kinetic_type'

def rd(comp, fn): return open(os.path.join(ROOT, 'components', comp, fn)).read()
def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)
def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d
def CH(n): return "parent().op('mod')['%s'].eval()" % n

def add_pars(c, specs, page='Controls'):
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse': pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]; p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'rgb':
            for q, v in zip(pg.appendRGB(n), s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def mod_chop(c, name):
    im = c.create(td.inCHOP, name)
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im); mg.inputConnectors[1].connect(mz)
    mg.par.duplicate = 'first'; mg.par.align = 'start'
    return mg

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
# ---- end helpers ----

c = new_comp(COMP)
P = 'parent().par.'
add_pars(c, [
    ('Text', 'str', 'KINETIC TYPE'),
    ('Mode', 'menu', [('scatter', 'Scatter on beat'), ('slit', 'Slit stretch'), ('noise', 'Noise warp'), ('extrude', 'Extrude / depth stack')], 0),
    ('Speed', 'float', 1.0, 0, 8),
    ('Trigger', 'pulse'),
    ('Autobeat', 'toggle', 1),
    ('Beatspercycle', 'int', 4, 1, 32),
    ('Amount', 'float', 1.0, 0, 3),
    ('Decay', 'float', 3.0, 0.2, 12),
    ('Stretch', 'float', 5.0, 0, 20),
    ('Layers', 'int', 12, 1, 32),
    ('Depth', 'float', 6.0, 0, 20),
    ('Fontname', 'str', 'Courier New'),
    ('Size', 'float', 1.0, 0.2, 4),
    ('Spacing', 'float', 1.0, 0.7, 2),
    ('Seed', 'int', 3, 0, 999),
])
add_pars(c, [
    ('Tint', 'rgb', (0.92, 0.92, 0.88)),
    ('Accent', 'rgb', (1.0, 0.08, 0.05)),
    ('Accentamt', 'float', 0.1, 0, 1),
], page='Look')

mod_chop(c, 'in1')
PH = "(absTime.seconds*%sSpeed/8.0)" % P     # motion phase: 1.0 == one 8 s cycle at Speed 1 (motion only)
NEXP = "max(len(%sText.eval()),1)" % P
EFFL = "(%sLayers if %sMode=='extrude' else 1)" % (P, P)

pe = c.create(td.parameterexecuteDAT, 'trig_exec')
pe.par.op = c; pe.par.pars = 'Trigger'; pe.par.onpulse = True
pe.text = "def onPulse(par):\n\tparent().store('t0', absTime.seconds)\n\treturn\n"
c.store('t0', -1000.0)
TRIG = "math.exp(-(absTime.seconds-parent().fetch('t0',-1000.0))*%sDecay)" % P

# ---- out1: one point per glyph (x layers in extrude mode), attributes written by a GLSL POP ----
pg = c.create(td.pointgeneratorPOP, 'glyph_points')
pg.par.shape = 'line'
pg.par.numpoints.expr = "int(%s*%s)" % (NEXP, EFFL)
code = mkdat(c, 'inst_code', rd(COMP, 'inst.glsl'))
gl = c.create(td.glslPOP, 'kinetic'); gl.inputConnectors[0].connect(pg)
gl.par.computedat = code
gl.par.outputattrs = 'P rotation scale glyph layer Color uvrect'
attrs = [('rotation', 3), ('scale', 3), ('glyph', 1), ('layer', 1), ('Color', 4), ('uvrect', 4)]
gl.seq.attr.numBlocks = len(attrs)
for i, (n, k) in enumerate(attrs):
    if n == 'Color': gl.par['attr%dname' % i] = 'color'
    else:
        gl.par['attr%dname' % i] = 'custom'; gl.par['attr%dcustomname' % i] = n
    gl.par['attr%dnumcomps' % i] = str(k) if gl.par['attr%dnumcomps' % i].isMenu else k
gl.seq.vec.numBlocks = 7
vecs = [
 ('uA', [NEXP, EFFL, "%sMode.menuIndex" % P, PH]),
 ('uB', [P+"Size", P+"Spacing", P+"Amount", P+"Stretch"]),
 ('uC', [P+"Beatspercycle", "1 if %sAutobeat else 0" % P, TRIG, P+"Depth"]),
 ('uD', [P+"Accentamt", P+"Decay", P+"Seed", CH('beat')]),
 ('uE', [P+"Tintr", P+"Tintg", P+"Tintb", CH('band1')]),
 ('uF', [P+"Accentr", P+"Accentg", P+"Accentb", CH('band2')]),
 ('uG', [CH('band3'), CH('band4'), 0, 0]),
]
for k, (n2, vals) in enumerate(vecs):
    gl.par['vec%dname' % k] = n2
    gl.par['vec%dtype' % k] = 'vec4'
    for j, v in enumerate(vals):
        p = gl.par['vec%dvalue%s' % (k, 'xyzw'[j])]
        if isinstance(v, str): p.expr = v
        else: p.val = v
o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(gl); o1.comment = 'glyph instances (POP)'

# ---- out2: text mesh ----
tp = c.create(td.textPOP, 'textmesh')
tp.par.text.expr = P + 'Text'
tp.par.font.expr = P + 'Fontname'
o2 = c.create(td.nullPOP, 'out2'); o2.inputConnectors[0].connect(tp); o2.comment = 'text mesh (POP)'

# ---- preview (internal, not an output): atlas quads instanced on the glyph points ----
at = c.create(td.textTOP, 'atlas')
at.par.text.expr = P + 'Text'
at.par.font.expr = P + 'Fontname'
at.par.fontautosize = 'nofit'
at.par.fontsizexunit = 'pixels'; at.par.fontsizeyunit = 'pixels'
at.par.fontsizex = 100
at.par.outputresolution = 'custom'
at.par.resolutionw.expr = "min(%s*60, 16000)" % NEXP; at.par.resolutionh = 120
at.par.fontcolorr = at.par.fontcolorg = at.par.fontcolorb = 1
at.par.bgcolorr = at.par.bgcolorg = at.par.bgcolorb = 0; at.par.bgalpha = 0
at.par.alignx = 'center'; at.par.aligny = 'center'
at.par.format = 'rgba8fixed'

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
rc = geo.create(td.rectangleSOP, 'rect1'); rc.par.sizex = 0.5; rc.par.sizey = 1.0
rc.display = True; rc.render = True
mat = c.create(td.constantMAT, 'mat')
mat.par.colormap = at
mat.par.blending = 'on'; mat.par.srcblend = 'one'; mat.par.destblend = 'one'
mat.par.depthwriting = False
geo.par.material = mat
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = o1
geo.par.instancetx = 'P(0)'; geo.par.instancety = 'P(1)'; geo.par.instancetz = 'P(2)'
geo.par.instancerop = o1
geo.par.instancerx = 'rotation(0)'; geo.par.instancery = 'rotation(1)'; geo.par.instancerz = 'rotation(2)'
geo.par.instancesop = o1
geo.par.instancesx = 'scale(0)'; geo.par.instancesy = 'scale(1)'; geo.par.instancesz = 'scale(2)'
geo.par.instancecolorop = o1
geo.par.instancecolormode = 'multiply'
geo.par.instancer = 'Color(0)'; geo.par.instanceg = 'Color(1)'; geo.par.instanceb = 'Color(2)'; geo.par.instancea = 'Color(3)'
geo.par.instancetexmode = 'transform'
geo.par.instancetexcoordop = o1
geo.par.instanceu = 'uvrect(0)'; geo.par.instancev = 'uvrect(1)'
geo.par.instancescaleu = 'uvrect(2)'; geo.par.instancescalev = 'uvrect(3)'

tgt = c.create(td.nullCOMP, 'target')
cam = c.create(td.cameraCOMP, 'cam')
W = "(%s*0.5*%sSize*%sSpacing)" % (NEXP, P, P)
cam.par.tz.expr = "max(%s/(2*math.tan(math.radians(40/2)))*1.15, 3)" % W
cam.par.tx.expr = "math.sin(0.5*absTime.seconds)*%s*0.05" % W
cam.par.ty.expr = "math.cos(0.5*absTime.seconds)*0.3"
cam.par.fov = 40
cam.par.lookat = tgt
rt = c.create(td.renderTOP, 'render')
rt.par.camera = cam; rt.par.geometry = geo
rt.par.outputresolution = 'custom'; rt.par.resolutionw = 960; rt.par.resolutionh = 540
rt.par.bgcolorr = rt.par.bgcolorg = rt.par.bgcolorb = 0; rt.par.bgcolora = 1
pv = c.create(td.nullTOP, 'preview'); pv.inputConnectors[0].connect(rt)
finish(c, COMP)
report(c)
