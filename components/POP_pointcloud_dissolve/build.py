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
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ---- loop helpers (batch 2) ----
def loop_page(c, seconds=8.0, beats=16):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]
    p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute Time', 'Phase (external)']
    p.default = 'abstime'; p.val = 'abstime'
    pg.appendCHOP('Clock')
    p = pg.appendFloat('Phase')[0]; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.default = 0; p.val = 0
    p = pg.appendFloat('Loopseconds')[0]; p.min = 0.5; p.max = 120; p.normMin = 1; p.normMax = 60; p.default = seconds; p.val = seconds
    p = pg.appendInt('Loopbeats')[0]; p.min = 1; p.max = 256; p.normMin = 1; p.normMax = 64; p.default = beats; p.val = beats
    p = pg.appendFloat('Bpm')[0]; p.min = 20; p.max = 300; p.normMin = 60; p.normMax = 200; p.default = 120; p.val = 120
    p = pg.appendToggle('Usebeats')[0]; p.default = False; p.val = False
    return pg

def make_clock(c):
    """constant CHOP 'clock': len (loop seconds), ph (0-1 phase), t (seconds, = ph*len in phase mode)"""
    k = c.create(td.constantCHOP, 'clock')
    P = 'parent().par.'
    PHS = "(float(parent().par.Clock.eval()['phase']) if parent().par.Clock.eval() else parent().par.Phase)"
    L = "((%sLoopbeats*60.0/%sBpm) if %sUsebeats else %sLoopseconds)" % (P, P, P, P)
    exprs = [('len', L),
             ('ph', "((absTime.seconds/%s)%%1.0) if %sTimesource=='abstime' else %s" % (L, P, PHS)),
             ('t', "absTime.seconds if %sTimesource=='abstime' else %s*%s" % (P, PHS, L))]
    k.par.name0 = 'len'; k.par.value0.expr = exprs[0][1]
    k.par.name1 = 'ph'; k.par.value1.expr = exprs[1][1]
    k.par.name2 = 't'; k.par.value2.expr = exprs[2][1]
    return k
CLK_PH = "op('clock')['ph']"
CLK_T = "op('clock')['t']"

COMP = 'POP_pointcloud_dissolve'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Source','menu',[('sphere','Sphere'),('torus','Torus'),('blob','Head-ish Blob'),('image','Image (in2 depth/luma)'),('input','Input POP (in1)')],4),
 ('Density','int',60,20,220),
 ('Dissolve','float',0.0,0,1,True),
 ('Auto','toggle',True),
 ('Autocycles','int',1,1,4),
 ('Automax','float',0.7,0.1,1.2),
 ('Wavemode','menu',[('plane','Moving Plane'),('sphere','Orbiting Sphere'),('radial','Radial (from axis)')],0),
 ('Axisx','float',0.0,-1,1),('Axisy','float',1.0,-1,1),('Axisz','float',0.25,-1,1),
 ('Edgewidth','float',0.35,0.05,1),
 ('Scatter','float',1.3,0,4),
 ('Jitter','float',0.25,0,1),
 ('Drift','float',0.35,-2,2),
 ('Noisefreq','float',2.2,0.2,5),
 ('Noisecycles','int',1,0,4),
 ('Depth','float',0.9,0,3),
 ('Invertluma','toggle',False),
])
add_pars(c, [
 ('Pointsize','float',2.0,0.5,8),
 ('Brightness','float',0.6,0,3),
 ('Edgeglow','float',1.5,0,4),
 ('Glow','float',0.35,0,2),
 ('Camdist','float',6.2,1.5,15),
 ('Camheight','float',0.35,-3,4),
 ('Orbitturns','int',1,0,4),
 ('Fov','float',45,10,90),
], page='Render')
loop_page(c, 12.0, 24)
clk = make_clock(c)
P = 'parent().par.'
PH = CLK_PH
ang = "2*math.pi*"+PH

# in1 TOP + default source
inpop = c.create(td.inPOP, 'in1'); inpop.par.connectorder = 1
in1 = c.create(td.inTOP, 'in2'); in1.par.connectorder = 2
CON = 'len(parent().inputConnectors[0].connections)>0'
dn = c.create(td.noiseTOP, 'default_img')
dn.par.outputresolution = 'custom'; dn.par.resolutionw = 512; dn.par.resolutionh = 512
dn.par.period = 0.5; dn.par.harmon = 3; dn.par.amp = 0.5; dn.par.offset = 0.5
dn.par.tz.expr = "0.6*math.cos(%s)" % ang
dn.par.ty.expr = "0.6*math.sin(%s)" % ang
isw = c.create(td.switchTOP, 'img_switch'); isw.inputConnectors[0].connect(dn); isw.inputConnectors[1].connect(in1)
isw.par.index.expr = "1 if len(parent().inputConnectors[1].connections)>0 else 0"

# sources
sp = c.create(td.spherePOP, 'src_sphere'); sp.par.type = 'geodesic'; sp.par.surftype = 'triangles'
sp.par.radx = 1; sp.par.rady = 1; sp.par.radz = 1; sp.par.normal = True; sp.par.freq.expr = P+'Density'
tr = c.create(td.torusPOP, 'src_torus'); tr.par.surftype = 'triangles'; tr.par.normal = True
tr.par.radx = 0.9; tr.par.rady = 0.38
tr.par.cols.expr = P+'Density*3'; tr.par.rows.expr = P+'Density*1.2'
gr = c.create(td.gridPOP, 'src_grid'); gr.par.sizex = 2; gr.par.sizey = 2; gr.par.normal = True
gr.par.cols.expr = P+'Density*2.5'; gr.par.rows.expr = P+'Density*2.5'
sw = c.create(td.switchPOP, 'src_switch')
sw.inputConnectors[0].connect(sp); sw.inputConnectors[1].connect(tr); sw.inputConnectors[2].connect(gr); sw.inputConnectors[3].connect(inpop)
sw.par.index.expr = "((3 if %s else 0) if %sSource=='input' else {'sphere':0,'blob':0,'torus':1,'image':2}[%sSource.eval()])" % (CON, P, P)

dd = mkdat(c, 'dissolve_code', rd(name, 'dissolve.glsl'))
n0 = c.create(td.normalPOP, 'normals_in'); n0.inputConnectors[0].connect(sw)
g = c.create(td.glslPOP, 'dissolve'); g.inputConnectors[0].connect(n0)
g.par.computedat = dd; g.par.outputattrs = 'P'
g.par.attr0name = 'color'
g.seq.attr.numBlocks = 2
g.par.attr1name = 'pointscale'
g.par.sampler0name = 'uTex'; g.par.sampler0top = isw
g.seq.vec.numBlocks = 6
eff = "(%sAutomax*(0.5-0.5*math.cos(%s*%sAutocycles))**1.6 if %sAuto else %sDissolve)" % (P, ang, P, P, P)
vecs = [('uA',[eff, "{'plane':0,'sphere':1,'radial':2}[%sWavemode.eval()]" % P, P+'Scatter', P+'Jitter']),
        ('uB',[ang, P+'Noisefreq', P+'Edgewidth', P+'Drift']),
        ('uC',["(0 if %sSource=='input' and %s else 2 if %sSource=='input' else {'sphere':0,'torus':1,'blob':2,'image':3}[%sSource.eval()])" % (P, CON, P, P), P+'Depth', P+'Brightness', P+'Noisecycles']),
        ('uD',[P+'Axisx', P+'Axisy', P+'Axisz', "1 if %sInvertluma else 0" % P]),
        ('uE',[1,1,1, P+'Edgeglow']),
        ('uF',[P+'Pointsize',0,0,0])]
for i,(nm,vals) in enumerate(vecs):
    getattr(g.par,'vec%dname'%i).val = nm
    getattr(g.par,'vec%dtype'%i).val = 'vec4'
    for j,v in enumerate(vals):
        p = getattr(g.par,'vec%dvalue%s'%(i,'xyzw'[j]))
        if isinstance(v,str): p.expr = v
        else: p.val = v
o2 = c.create(td.nullPOP, 'out2'); o2.comment = 'points'; o2.inputConnectors[0].connect(g)

geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
pts = c.create(td.convertPOP, 'points_only'); pts.par.convert = 'topointprims'; pts.inputConnectors[0].connect(g)
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = pts
sel.display = True; sel.render = True
mat = c.create(td.pointspriteMAT, 'sprite_mat')
mat.par.pointsize = 1
mat.par.blending = True; mat.par.srcblend = 'sa'; mat.par.destblend = 'one'
mat.par.depthwriting = False
geo.par.material = mat
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
cam.par.tx.expr = "math.sin(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.tz.expr = "math.cos(%s*%sOrbitturns)*%sCamdist" % (ang, P, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov.expr = P+'Fov'; cam.par.lookat = tgt
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr = 0; rt.par.bgcolorg = 0; rt.par.bgcolorb = 0; rt.par.bgcolora = 1; rt.par.format = 'rgba16float'
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(rt); bl.par.size = 12
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1.expr = P+'Glow*2.0'
cm = c.create(td.compositeTOP, 'comp'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(rt); cm.inputConnectors[1].connect(lv)
o = c.create(td.nullTOP, 'out1'); o.comment = 'render'; o.inputConnectors[0].connect(cm)
finish(c, name)
report(c)
