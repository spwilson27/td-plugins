P = "parent().par."
c = new_comp(COMP)
add_pars(c, [
  ('Shape','menu',[('0','Box'),('1','Sphere'),('2','Cone')],0),
  ('Countx','int',40,2,256),
  ('County','int',24,2,256),
  ('Spacing','float',0.5,0.05,3),
  ('Basesize','float',0.42,0.02,3),
  ('Heightbase','float',0.1,0,4),
  ('Heightamt','float',3.0,0,20),
  ('Scaleamt','float',0.0,0,1),
  ('Rotamt','float',0.0,-4,4),
  ('Invert','toggle',0),
  ('Colormix','float',1.0,0,1),
  ('Noisespeed','float',0.15,0,2),
  ('Bgcolor','rgb',(0.03,0.03,0.05)),
  ('Modamount','float',0.5,0,2),
  *COMMON,
])
add_pars(c, [
  ('Orbitspeed','float',0.1,-2,2),
  ('Orbitangle','float',0.5,-6.28,6.28),
  ('Distance','float',32,3,120),
  ('Elevation','float',20,-20,80),
  ('Fov','float',45,15,100),
], page='Camera')
add_pars(c, [
  ('Lightangle','float',0.8,-6.28,6.28),
  ('Lightheight','float',20,2,100),
  ('Lightintensity','float',1.1,0,4),
  ('Ambient','float',0.35,0,1),
  ('Shadows','toggle',1),
], page='Light')
add_pars(c, [
  ('Look','menu',[('original','Original'),('mono','Mono')],0),
  ('Accent','float',0.0,0,1),
], page='Look')
loop_pars(c, beats=0, seconds=8)
LOOKI = P + "Look.menuIndex"
ISPH = "(1 if %sTimesource=='phase' else 0)" % P
def ORBIT(sp='Orbitspeed', off='Orbitangle'):
    S = P+sp; O = P+off
    return "(%s + 6.283185307*%s*(0 if abs(%s)<1e-4 else (1 if %s>0 else -1)*max(1,round(abs(%s)*%s/6.283185))) if %sTimesource=='phase' else absTime.seconds*%s+%s)" % (O, EXTPH, S, S, S, LENEXPR, P, S, O)
res_chop(c)
i1 = c.create(td.inTOP, 'in1')
def setu(g, items):
    for i, (nm, vs) in enumerate(items):
        getattr(g.par, 'vec%dname' % i).val = nm
        for ax, v in zip('xyzw', vs):
            p = getattr(g.par, 'vec%dvalue%s' % (i, ax))
            if isinstance(v, str): p.expr = v
            else: p.val = v
add_mod(c, 'in2')
nz = c.create(td.noiseTOP, 'default_noise')
nz.par.outputresolution='custom'; nz.par.resolutionw=512; nz.par.resolutionh=512
nz.par.mono = False; nz.par.period = 1.6; nz.par.amp = 0.55; nz.par.offset = 0.5; nz.par.harmon = 2
nz.par.tz.expr = "absTime.seconds*"+P+"Noisespeed*3"
# phase-periodic variant: 4D noise sampled on a circle in (tz, t4d)
nz4 = c.create(td.noiseTOP, 'default_noise_loop')
nz4.par.outputresolution='custom'; nz4.par.resolutionw=512; nz4.par.resolutionh=512
nz4.par.type='perlin4d'
nz4.par.mono = False; nz4.par.period = 1.6; nz4.par.amp = 0.55; nz4.par.offset = 0.5; nz4.par.harmon = 2
RAD = "max(0.2,%sNoisespeed*3*%s/6.283185)" % (P, LENEXPR)
nz4.par.tz.expr = RAD+"*math.cos(6.283185307*%s)" % PEXPR
nz4.par.t4d.expr = RAD+"*math.sin(6.283185307*%s)" % PEXPR
nsw = c.create(td.switchTOP, 'noise_mode'); nsw.inputConnectors[0].connect(nz); nsw.inputConnectors[1].connect(nz4)
nsw.par.index.expr = ISPH
sw = c.create(td.switchTOP, 'src_switch')
sw.inputConnectors[0].connect(nsw); sw.inputConnectors[1].connect(i1)
sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
rs = c.create(td.resolutionTOP, 'to_grid')
rs.par.outputresolution='custom'; rs.par.resolutionw.expr=P+"Countx"; rs.par.resolutionh.expr=P+"County"
rs.par.filtertype = 'linear' if 'linear' in rs.par.filtertype.menuNames else rs.par.filtertype.val
rs.inputConnectors[0].connect(sw)

code = rd(COMP,'inst.glsl')
d = mkdat(c, 'inst_code', code)
dat = {}
for i, nm in enumerate(['inst_t','inst_r','inst_s','inst_c']):
    g = c.create(td.glslTOP, nm)
    g.par.pixeldat = d
    g.par.outputresolution='custom'; g.par.resolutionw.expr=P+"Countx"; g.par.resolutionh.expr=P+"County"
    g.par.format = 'rgba32float'
    g.par.inputfiltertype = 'nearest' if 'nearest' in g.par.inputfiltertype.menuNames else g.par.inputfiltertype.val
    g.inputConnectors[0].connect(rs)
    setu(g, [('uA',[P+"Countx",P+"County",P+"Spacing",i]),
            ('uB',[P+"Heightamt"+"*(1+"+P+"Modamount*"+MOD('band1')+")",P+"Scaleamt",P+"Rotamt",P+"Basesize"]),
            ('uC',[P+"Invert",P+"Colormix",P+"Heightbase",0]),
            ('uD',[LOOKI,P+"Accent",0,0])])
    dat[nm]=g

# geometry
geo = c.create(td.geometryCOMP, 'geo')
for o in list(geo.children): o.destroy()
bx = geo.create(td.boxSOP,'box1'); sp = geo.create(td.sphereSOP,'sphere1'); cn = geo.create(td.tubeSOP,'cone1')
cn.par.type='poly'; cn.par.rad1=0.5; cn.par.rad2=0; cn.par.height=1; cn.par.cols=24; cn.par.rows=1; cn.par.cap=True; cn.par.orient='y' if 'y' in cn.par.orient.menuNames else cn.par.orient.val
sp.par.type='poly'; sp.par.radx=0.5; sp.par.rady=0.5; sp.par.radz=0.5; sp.par.rows=16; sp.par.cols=24
sw3 = geo.create(td.switchSOP,'shape_switch')
for k,o in enumerate((bx,sp,cn)): sw3.inputConnectors[0 if k==0 else 0].connect(o) if False else None
# switchSOP inputs are a growing list
sw3.inputConnectors[0].connect(bx)
sw3.inputConnectors[1].connect(sp)
sw3.inputConnectors[2].connect(cn)
sw3.par.input.expr = "parent(2).par.Shape.menuIndex"
sw3.display = True; sw3.render = True
SZ = [('box1',bx),('sphere1',sp),('cone1',cn)]
mat = c.create(td.phongMAT,'mat')
mat.par.diffr=1; mat.par.diffg=1; mat.par.diffb=1
mat.par.ambr=1; mat.par.ambg=1; mat.par.ambb=1
mat.par.specr=0.3; mat.par.specg=0.3; mat.par.specb=0.3
geo.par.material = mat
geo.par.instancing = True
geo.par.instancecountmode = 'oplength'
geo.par.instanceop = dat['inst_t']
geo.par.instancetop = dat['inst_t']
geo.par.instancetx='r'; geo.par.instancety='g'; geo.par.instancetz='b'
geo.par.instancerop = dat['inst_r']
geo.par.instancerx='r'; geo.par.instancery='g'; geo.par.instancerz='b'
geo.par.instancesop = dat['inst_s']
geo.par.instancesx='r'; geo.par.instancesy='g'; geo.par.instancesz='b'
geo.par.instancecolorop = dat['inst_c']
geo.par.instancer='r'; geo.par.instanceg='g'; geo.par.instanceb='b'

tgt = c.create(td.nullCOMP,'target')
cam = c.create(td.cameraCOMP,'cam')
cam.par.tx.expr = "math.sin(%s)*%sDistance" % (ORBIT(),P)
cam.par.tz.expr = "math.cos(%s)*%sDistance" % (ORBIT(),P)
cam.par.ty.expr = P+"Elevation"
cam.par.fov.expr = P+"Fov"
cam.par.lookat = tgt
lt = c.create(td.lightCOMP,'light')
lt.par.tx.expr = "math.sin(%sLightangle)*%sLightheight*0.7" % (P,P)
lt.par.tz.expr = "math.cos(%sLightangle)*%sLightheight*0.7" % (P,P)
lt.par.ty.expr = P+"Lightheight"
lt.par.lookat = tgt
lt.par.dimmer.expr = P+"Lightintensity"
lt.par.shadowtype.expr = "'hard2d' if "+P+"Shadows else 'off'"
al = c.create(td.ambientlightCOMP,'ambient_light')
al.par.dimmer.expr=P+"Ambient"
rt = c.create(td.renderTOP,'render')
rt.par.camera = cam; rt.par.geometry = geo; rt.par.lights = 'light ambient_light'
setres(rt)
rt.par.bgcolorr.expr="0 if %s else %sBgcolorr"%(LOOKI,P); rt.par.bgcolorg.expr="0 if %s else %sBgcolorg"%(LOOKI,P); rt.par.bgcolorb.expr="0 if %s else %sBgcolorb"%(LOOKI,P); rt.par.bgcolora=1
rt.par.antialias = 'aa4'
# dry = default/in1 image scaled to render resolution
src = c.create(td.switchTOP, 'src'); src.inputConnectors[0].connect(sw)
setres(src); src.par.format = 'rgba16float'
finish_v2(c, COMP, rt, src)
report(c)
