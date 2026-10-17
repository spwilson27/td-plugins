# ---- v2: Clock CHOP parameter (Loop page) ----
import td as _td
CLOCK_CB = '''def sync(c):
    clk = c.par.Clock.eval()
    if clk:
        c.par.Phase.expr = "me.par.Clock.eval()['phase'].eval() if me.par.Clock.eval() and me.par.Clock.eval()['phase'] is not None else 0"
    elif c.par.Phase.mode == ParMode.EXPRESSION:
        c.par.Phase.expr = ''
        c.par.Phase.mode = ParMode.CONSTANT
        c.par.Phase.val = 0.0

def onValueChange(par, prev):
    sync(par.owner)
    return
'''
def add_clock(c):
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendCHOP('Clock', label='Clock (CHOP, phase channel)')[0]
    cb = c.create(_td.parameterexecuteDAT, 'clock_exec')
    cb.text = CLOCK_CB
    cb.par.op = '..'; cb.par.pars = 'Clock'; cb.par.valuechange = True; cb.par.onpulse = False
    cb.par.custom = True; cb.par.builtin = False
# ---- end v2 clock ----
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
    L = "((%sLoopbeats*60.0/%sBpm) if %sUsebeats else %sLoopseconds)" % (P, P, P, P)
    exprs = [('len', L),
             ('ph', "((absTime.seconds/%s)%%1.0) if %sTimesource=='abstime' else %sPhase" % (L, P, P)),
             ('t', "absTime.seconds if %sTimesource=='abstime' else %sPhase*%s" % (P, P, L))]
    k.par.name0 = 'len'; k.par.value0.expr = exprs[0][1]
    k.par.name1 = 'ph'; k.par.value1.expr = exprs[1][1]
    k.par.name2 = 't'; k.par.value2.expr = exprs[2][1]
    return k
CLK_PH = "op('clock')['ph']"
CLK_T = "op('clock')['t']"

COMP = 'GEN_terrain_flyover'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Mode','menu',[('wire','Wireframe'),('solid','Solid'),('both','Both')],2),
 ('Source','menu',[('noise','Noise'),('image','Image (in1 TOP)')],0),
 ('Style','menu',[('rolling','Rolling'),('ridged','Ridged'),('terraced','Terraced')],1),
 ('Amplitude','float',3.2,0,12),
 ('Frequency','float',0.16,0.03,1.0),
 ('Zperiod','int',8,2,32),
 ('Loops','int',2,0,8),
 ('Valley','float',0.85,0,1),
 ('Valleywidth','float',0.55,0.05,1.5),
 ('Gridx','int',90,20,400),
 ('Gridz','int',130,20,500),
 ('Width','float',60,10,200),
 ('Length','float',90,20,300),
])
add_pars(c, [
 ('Camheight','float',2.6,0.3,15),
 ('Pitch','float',6,-10,40),
 ('Fov','float',70,20,120),
 ('Sway','float',0.8,0,4),
 ('Fogstart','float',0.03,0,1),
 ('Fogend','float',0.75,0.1,1.5),
 ('Linebright','float',0.95,0,3),
 ('Redaccent','float',1.0,0,3),
 ('Glow','float',1.0,0,3),
 ('Sun','float',0.0,0,1),
 ('Horizonglow','float',0.9,0,2),
 ('Wirecolor','rgb',(0.9,0.88,0.82)),
 ('Solidcolor','rgb',(0.006,0.006,0.008)),
 ('Glowcolor','rgb',(0.9,0.06,0.04)),
], page='Render')
loop_page(c, 16.0, 32)
clk = make_clock(c)
P = 'parent().par.'
PH = CLK_PH
ang = "2*math.pi*"+PH

in1 = c.create(td.inTOP, 'in1'); in1.par.connectorder = 1
dn = c.create(td.noiseTOP, 'default_img')
dn.par.outputresolution = 'custom'; dn.par.resolutionw = 512; dn.par.resolutionh = 512
dn.par.period = 0.3; dn.par.harmon = 4; dn.par.amp = 0.5; dn.par.offset = 0.5
isw = c.create(td.switchTOP, 'img_switch'); isw.inputConnectors[0].connect(dn); isw.inputConnectors[1].connect(in1)
isw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"

def mkgrid(nm, surf):
    gp = c.create(td.gridPOP, nm); gp.par.surftype = surf
    gp.par.sizex.expr = P+'Width'; gp.par.sizey.expr = P+'Length'
    gp.par.cols.expr = P+'Gridx'; gp.par.rows.expr = P+'Gridz'
    return gp
code = mkdat(c, 'terrain_code', rd(name, 'terrain.glsl'))
# scroll in world units: noise -> Zperiod/Frequency * Loops per cycle; image -> 2*texlen*Loops
PZ = "(%sZperiod/%sFrequency)" % (P, P)
scroll = "(%s*%sLoops*%s*(2 if %sSource=='image' else 1))" % (PH, P, PZ, P)
def mkshade(nm, gp, mode):
    g = c.create(td.glslPOP, nm); g.inputConnectors[0].connect(gp)
    g.par.computedat = code; g.par.outputattrs = 'P'; g.par.attr0name = 'color'
    g.par.sampler0name = 'uTex'; g.par.sampler0top = isw
    g.seq.vec.numBlocks = 6
    vecs = [('uA',[P+'Amplitude', P+'Frequency', P+'Zperiod', scroll]),
            ('uB',[P+'Valley', P+'Valleywidth', "1 if %sSource=='image' else 0" % P, "{'rolling':0,'ridged':1,'terraced':2}[%sStyle.eval()]" % P]),
            ('uC',[mode, P+'Fogstart', P+'Fogend', P+'Linebright']),
            ('uD',[P+'Wirecolorr', P+'Wirecolorg', P+'Wirecolorb', P+'Redaccent']),
            ('uE',[P+'Solidcolorr', P+'Solidcolorg', P+'Solidcolorb', PZ]),
            ('uF',[P+'Width', P+'Length', 0, 0])]
    for i,(n2,vals) in enumerate(vecs):
        getattr(g.par,'vec%dname'%i).val = n2
        getattr(g.par,'vec%dtype'%i).val = 'vec4'
        for j,v in enumerate(vals):
            p = getattr(g.par,'vec%dvalue%s'%(i,'xyzw'[j]))
            if isinstance(v,str): p.expr = v
            else: p.val = v
    return g
gw = mkshade('terrain_wire', mkgrid('grid_wire','linestrips'), 0)
gs = mkshade('terrain_solid', mkgrid('grid_solid','triangles'), 1)
o2 = c.create(td.nullPOP, 'out2'); o2.inputConnectors[0].connect(gs)

def mkgeo(nm, src, wire):
    geo = c.create(td.geometryCOMP, nm)
    for o in list(geo.children): o.destroy()
    sel = geo.create(td.selectPOP, 'select'); sel.par.pop = src
    sel.display = True; sel.render = True
    m = c.create(td.constantMAT, nm+'_mat'); m.par.applypointcolor = True
    m.par.wireframe = False
    if wire:
        m.par.blending = True; m.par.srcblend = 'one'; m.par.destblend = 'one'; m.par.depthwriting = False
        m.par.depthtest = True
    else:
        m.par.polygonoffset = True; m.par.polygonoffsetfactor = 2; m.par.polygonoffsetunits = 2
    geo.par.material = m
    return geo
geo_w = mkgeo('geo_wire', gw, True)
geo_s = mkgeo('geo_solid', gs, False)
# draw solid first, wire on top (polygon offset alone is ignored on macOS/Metal; Render TOP order isn't draw order)
geo_s.par.drawpriority = 1
geo_w.par.drawpriority = -1
geo_w.par.render.expr = "%sMode in ('wire','both')" % P
geo_s.par.render.expr = "%sMode in ('solid','both')" % P

cam = c.create(td.cameraCOMP, 'cam')
cam.par.tx.expr = "math.sin(%s*2)*%sSway" % (ang, P)
cam.par.ty.expr = P+'Camheight'
cam.par.tz = 0
cam.par.rx.expr = "-%sPitch" % P
cam.par.ry.expr = "-math.sin(%s*2)*%sSway*1.2" % (ang, P)
cam.par.rz.expr = "math.sin(%s*2+0.6)*%sSway*0.8" % (ang, P)
cam.par.fov.expr = P+'Fov'
cam.par.far = 400
rt = c.create(td.renderTOP, 'render'); rt.par.camera = cam; rt.par.geometry = 'geo_solid geo_wire'; rt.par.lights = ''
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr = 0; rt.par.bgcolorg = 0; rt.par.bgcolorb = 0; rt.par.bgcolora = 0; rt.par.format = 'rgba16float'
rt.par.antialias = 'aa4'
# background (horizon glow + optional sun)
hy = "0.5 + math.tan(math.radians(%sPitch))/(2*math.tan(math.radians(%sFov)/2)*%sResolutionh/%sResolutionw)" % (P,P,P,P)
bg = glsl(c, 'bg', rd(name, 'bg.glsl'), vecs=[('uA',[hy, P+'Sun', P+'Horizonglow', 0]), ('uB',[P+'Glowcolorr',P+'Glowcolorg',P+'Glowcolorb',0])], fmt='rgba16float', res=True)
ov = c.create(td.overTOP, 'over'); ov.inputConnectors[0].connect(rt); ov.inputConnectors[1].connect(bg)
bl = c.create(td.blurTOP, 'glow_blur'); bl.inputConnectors[0].connect(rt); bl.par.size = 10
lv = c.create(td.levelTOP, 'glow_gain'); lv.inputConnectors[0].connect(bl); lv.par.brightness1.expr = P+'Glow*2.5'
cm = c.create(td.compositeTOP, 'comp'); cm.par.operand = 'add'
cm.inputConnectors[0].connect(ov); cm.inputConnectors[1].connect(lv)
o = c.create(td.nullTOP, 'out1'); o.inputConnectors[0].connect(cm); o.comment = 'render'; o2.comment = 'terrain'
add_clock(c)
finish(c, name)
report(c)
