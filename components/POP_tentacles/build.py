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
    sw.par.index.expr = "(1 if parent().inputConnectors[0].connections else 0) + 0*absTime.frame"
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


COMP = 'POP_tentacles'
name = COMP
c = new_comp(name)
add_pars(c, [
 ('Length','float',2.2,0.3,8),
 ('Grow','float',1.0,0,1),
 ('Autogrow','toggle',False),
 ('Speed','float',0.5,0,4),
 ('Seed','float',0.0,0,100),
 ('Segments','int',64,8,200),
 ('Sides','int',12,4,32),
 ('Thickness','float',0.075,0.005,0.4),
 ('Taper','float',0.8,0.1,3),
 ('Tipmin','float',0.04,0,0.5),
 ('Wiggle','float',0.35,0,1.5),
 ('Noisefreq','float',1.3,0.2,5),
 ('Wave','float',0.07,0,0.5),
 ('Wavefreq','float',2.0,0.5,8),
 ('Pulse','float',0.18,0,0.8),
 ('Pulsefreq','float',6.0,1,20),
])
add_pars(c, [
 ('Resolution','wh',(1280,720)),
 ('Metallic','float',1.0,0,1),
 ('Roughness','float',0.22,0.02,1),
 ('Basecolor','rgb',(0.82,0.82,0.85)),
 ('Envintensity','float',1.0,0,4),
 ('Redaccent','float',0.7,0,1),
 ('Camdist','float',9.5,2,30),
 ('Camheight','float',1.2,-8,10),
 ('Bgcolor','rgb',(0.006,0.006,0.008)),
], page='Look')
P = 'parent().par.'

# ---- inputs: in1 POP (points), in2 modulation CHOP ----
inp = c.create(td.inPOP, 'in1')
inm = c.create(td.inCHOP, 'in2'); inm.par.connectorder = 1
# demo (preview only): points on a sphere, gated off whenever in1 is connected
demo = c.create(td.baseCOMP, 'demo')
dsp = demo.create(td.spherePOP, 'points'); dsp.par.type = 'geodesic'; dsp.par.freq = 3
dout = demo.create(td.outPOP, 'out1'); dout.inputConnectors[0].connect(dsp)
sw = c.create(td.switchPOP, 'src')
sw.inputConnectors[0].connect(demo.outputConnectors[0]); sw.inputConnectors[1].connect(inp)
sw.par.index.expr = "(1 if len(parent().inputConnectors[0].connections) else 0) + 0*absTime.frame"

# ---- modulation: band1..4, beat (default 0 when absent) ----
base = c.create(td.constantCHOP, 'modbase')
for i, n in enumerate(('band1','band2','band3','band4','beat')):
    getattr(base.par, 'name%d'%i).val = n; getattr(base.par, 'value%d'%i).val = 0
mod = c.create(td.mergeCHOP, 'mod'); mod.par.duplicate = 'first'
mod.inputConnectors[0].connect(inm); mod.inputConnectors[0].connect(inm)
mod.inputConnectors[1].connect(base)
def M(n): return "op('mod')['%s']" % n

# ---- geometry ----
tube = c.create(td.tubePOP, 'tube'); tube.par.orient = 'y'; tube.par.height = 1.0
tube.par.radx = 0.5; tube.par.rady = 0.5; tube.par.endcaps = False
tube.par.cols.expr = P+'Sides'; tube.par.rows.expr = P+'Segments'
rcol = mkdat(c, 'root_code', "void main(){ const uint id=TDIndex(); if(id>=TDNumElements()) return; Root[id]=TDIn_P(); }")
rg = c.create(td.glslPOP, 'rootattr'); rg.inputConnectors[0].connect(sw); rg.par.computedat = rcol
rg.par.outputattrs = 'Root'
rg.par.attr0name = 'custom'; rg.par.attr0customname = 'Root'; rg.par.attr0type = 'float'; rg.par.attr0numcomps = 3
cp = c.create(td.copyPOP, 'copy')
cp.inputConnectors[0].connect(tube); cp.inputConnectors[1].connect(rg)
cp.par.dotemplatetranslate = False
cp.par.doattr = True; cp.par.templateattr0names = 'Root'
dd = mkdat(c, 'tentacle_code', rd(name, 'tentacle.glsl'))
g = c.create(td.glslPOP, 'tentacle'); g.inputConnectors[0].connect(cp)
g.par.computedat = dd; g.par.outputattrs = 'P'
g.seq.vec.numBlocks = 4
th = "absTime.seconds*%sSpeed" % P
grow = "((0.5-0.5*math.cos(%s))**0.7 if %sAutogrow else %sGrow)" % (th, P, P)
vecs = [('uA',[P+'Length*(1+0.3*'+M('band4')+')', P+'Wiggle*(1+'+M('band1')+')', P+'Thickness*(1+0.5*'+M('beat')+')', P+'Taper']),
        ('uB',[th, P+'Noisefreq', P+'Pulse+0.3*'+M('band3'), P+'Pulsefreq']),
        ('uC',[grow, P+'Tipmin', P+'Wavefreq', P+'Wave*(1+2*'+M('band2')+')']),
        ('uD',[P+'Seed', 1, 1, 0])]
for i,(n2,vals) in enumerate(vecs):
    getattr(g.par,'vec%dname'%i).val = n2
    getattr(g.par,'vec%dtype'%i).val = 'vec4'
    for j,v in enumerate(vals):
        p = getattr(g.par,'vec%dvalue%s'%(i,'xyzw'[j]))
        if isinstance(v,str): p.expr = v
        else: p.val = v
nr = c.create(td.normalPOP, 'tubes'); nr.inputConnectors[0].connect(g)
o1 = c.create(td.nullPOP, 'out1'); o1.inputConnectors[0].connect(nr); o1.comment = 'tentacle tubes'

# ---- internal preview render (not an output) ----
env = glsl(c, 'envmap', open(os.path.join(ROOT,'components','_lib','env.glsl')).read(),
           vecs=[('uA',[P+'Envintensity', P+'Redaccent', 0, 0])], fmt='rgba16float')
env.par.outputresolution = 'custom'; env.par.resolutionw = 1024; env.par.resolutionh = 512
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
sel = geo.create(td.selectPOP, 'select'); sel.par.pop = nr
sel.display = True; sel.render = True
mat = c.create(td.pbrMAT, 'mat')
mat.par.basecolorr.expr = P+'Basecolorr'; mat.par.basecolorg.expr = P+'Basecolorg'; mat.par.basecolorb.expr = P+'Basecolorb'
mat.par.applypointcolor = False
mat.par.metallic.expr = P+'Metallic'; mat.par.roughness.expr = P+'Roughness'
geo.par.material = mat
cam = c.create(td.cameraCOMP, 'cam'); tgt = c.create(td.nullCOMP, 'target')
ang = "absTime.seconds*0.25"
cam.par.tx.expr = "math.sin(%s)*%sCamdist" % (ang, P)
cam.par.tz.expr = "math.cos(%s)*%sCamdist" % (ang, P)
cam.par.ty.expr = P+'Camheight'; cam.par.fov = 50; cam.par.lookat = tgt
el = c.create(td.environmentlightCOMP, 'envlight'); el.par.envlightmap = env
key = c.create(td.lightCOMP, 'key'); key.par.tx = -4; key.par.ty = 5; key.par.tz = 4; key.par.lookat = tgt
key.par.dimmer = 0.6; key.par.shadowtype = 'off'
rim = c.create(td.lightCOMP, 'rim'); rim.par.tx = 4.5; rim.par.ty = 2; rim.par.tz = -5; rim.par.lookat = tgt
rim.par.cr = 1; rim.par.cg = 0.15; rim.par.cb = 0.1; rim.par.dimmer.expr = P+'Redaccent*0.8'; rim.par.shadowtype = 'off'
rt = c.create(td.renderTOP, 'preview'); rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = 'envlight key rim'
rt.par.outputresolution = 'custom'; rt.par.resolutionw.expr = P+'Resolutionw'; rt.par.resolutionh.expr = P+'Resolutionh'
rt.par.bgcolorr.expr = P+'Bgcolorr'; rt.par.bgcolorg.expr = P+'Bgcolorg'; rt.par.bgcolorb.expr = P+'Bgcolorb'; rt.par.bgcolora = 1
rt.par.antialias = 'aa4'; rt.par.format = 'rgba16float'
finish(c, name)
report(c)
