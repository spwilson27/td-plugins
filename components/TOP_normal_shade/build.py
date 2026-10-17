import os
_G = os.path.expanduser('~/software/td-plugins/components/_gbuf/')
exec(open(_G + 'hdr.py').read()); exec(open(_G + 'gbuf.py').read())

COMP = 'TOP_normal_shade'
# --- native-node helper (pasted into the body of native build.py files) ---
def nat(c, typ, name, *ins, fmt='rgba16float', **kw):
    """Create a native op, wire inputs, set pars. A str value starting with '=' is an expression."""
    o = c.create(getattr(td, typ), name)
    for i, s in enumerate(ins):
        if s is not None: o.inputConnectors[i].connect(s)
    if fmt and hasattr(o.par, 'format'): o.par.format = fmt
    for k, v in kw.items():
        p = o.par[k]
        if isinstance(v, str) and v.startswith('='): p.expr = v[1:]
        elif isinstance(v, str): p.val = v
        else: p.val = v
    return o
c = new_comp(COMP)
add_pars(c, [
    ('Mode', 'menu', [('matcap', 'Matcap lookup'), ('lights', 'Key / fill / rim lights')], 0),
    ('Normalenc', 'menu', [('signed', 'Signed (-1..1)'), ('packed', 'Packed (0..1)')], 0),
    ('Colormix', 'float', 1.0, 0, 1, True),
    ('Brightness', 'float', 1.0, 0, 4),
    ('Background', 'menu', [('transparent', 'Transparent black'), ('color', 'in3 colour')], 0),
    ('Matcaprotate', 'float', 0, -180, 180),
    ('Matcapflip', 'toggle', 0),
    *COMMON,
])
add_pars(c, [
    ('Keyazimuth', 'float', -35, -180, 180),
    ('Keyelevation', 'float', 40, -89, 89),
    ('Keyintensity', 'float', 0.7, 0, 8),
    ('Keycolor', 'rgb', (1.0, 0.92, 0.82)),
    ('Fillintensity', 'float', 0.22, 0, 4),
    ('Fillcolor', 'rgb', (0.45, 0.6, 1.0)),
    ('Rimintensity', 'float', 0.6, 0, 8),
    ('Rimcolor', 'rgb', (0.8, 0.9, 1.0)),
    ('Rimpower', 'float', 3.0, 0.5, 12),
    ('Ambient', 'float', 0.03, 0, 1),
    ('Specamount', 'float', 0.3, 0, 4),
    ('Specpower', 'float', 40, 2, 400),
    ('Wrap', 'float', 0.2, 0, 1),
], page='Lights')
P = 'parent().par.'
F = ' + 0*absTime.frame'
HAS1 = "len(parent().inputConnectors[0].connections)"
res_chop(c)
RW, RH = "=op('res')['w']", "=op('res')['h']"
def sres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RW[1:]; o.par.resolutionh.expr = RH[1:]; return o
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')

# ---------------- demo (preview only): a bumpy height field -> Normal Map TOP -> signed normals ----------------
d = c.create(td.baseCOMP, 'demo')
d.comment = 'preview-only source (used while in1 is unconnected; does not cook otherwise)'
def dres(o, w=None, h=None):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w or "op('../res')['w']"; o.par.resolutionh.expr = h or "op('../res')['h']"; return o

dome = dres(nat(d, 'circleTOP', 'dome', radiusx=0.26, radiusy=0.26, softness=0.26, softnesstype='halfcosine',
                centerx="=-0.12+0.1*math.sin(absTime.seconds*0.7)", centery="=0.02+0.06*math.cos(absTime.seconds*0.5)"))
dome2 = dres(nat(d, 'circleTOP', 'dome2', radiusx=0.15, radiusy=0.15, softness=0.15, softnesstype='halfcosine',
                 centerx="=0.28+0.08*math.cos(absTime.seconds*0.6)", centery="=-0.1+0.1*math.sin(absTime.seconds*0.8)"))
box = dres(nat(d, 'rectangleTOP', 'box', sizex=0.22, sizey=0.16, cornerradius=0.05, softness=0.06, rotate="=absTime.seconds*20",
               centerx=0.15, centery="=0.2+0.05*math.sin(absTime.seconds)"))
hmax = nat(d, 'compositeTOP', 'height', dome, dome2, box, operand='maximum')
hround = nat(d, 'levelTOP', 'round_profile', hmax, gamma1=1.8)          # dome-like profile
nmap = nat(d, 'normalmapTOP', 'normal_map', hround, source='red', zscale="=8.6/op('../res')['h']")
hmask = nat(d, 'thresholdTOP', 'shape_mask', hmax, threshold=0.002, comparator='less')
dsig = nat(d, 'channelmixTOP', 'to_signed', nmap, red1=2, green1=0, green2=2, blue1=0, blue2=0, blue3=2,
           constant1=-1, constant2=-1, constant3=-1)
dnorm = nat(d, 'compositeTOP', 'normals_masked', dsig, hmask, operand='multiply')
do = d.create(td.outTOP, 'o_normal'); do.inputConnectors[0].connect(dnorm)
src = nat(c, 'switchTOP', 'src', d.outputConnectors[0], i1)
src.par.index.expr = '(1 if %s else 0)%s' % (HAS1, F)
sres(src)

# ---------------- inputs: matcap / colour ----------------
# default matcap, built from gradients: clay body + cool fresnel rim + soft specular
def mres512(o): o.par.outputresolution = 'custom'; o.par.resolutionw = 512; o.par.resolutionh = 512; return o
mc = c.create(td.baseCOMP, 'defmatcap'); mc.comment = 'default matcap (preview/fallback), made of Circle TOPs'
def mcn(typ, name, *ins, **kw): return mres512(nat(mc, typ, name, *ins, **kw))
mc_bg = mcn('constantTOP', 'base', colorr=0.06, colorg=0.055, colorb=0.05, alpha=1)
mc_body = mcn('circleTOP', 'body', radiusx=0.8, radiusy=0.8, radiusunit='fraction', softness=0.8, softnessunit='fraction', softnesstype='halfcosine',
              fillcolorr=0.72, fillcolorg=0.68, fillcolorb=0.62, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, centerx=-0.2, centery=0.24)
mc_body2 = mcn('levelTOP', 'wrap_curve', mc_body, gamma1=0.65)
mc_rim0 = mcn('circleTOP', 'rim', radiusx=0.5, radiusy=0.5, radiusunit='fraction', softness=0.5, softnessunit='fraction', softnesstype='halfcosine',
             fillcolorr=0, fillcolorg=0, fillcolorb=0, fillalpha=1, bgcolorr=1, bgcolorg=1, bgcolorb=1, bgalpha=1, centerx=0, centery=0)
mc_rim1 = mcn('levelTOP', 'rim_falloff', mc_rim0, gamma1=0.2)
mc_rim = mcn('channelmixTOP', 'rim_color', mc_rim1, red1=0.19, red2=0, red3=0, green1=0.275, green2=0, green3=0, blue1=0.44, blue2=0, blue3=0)
mc_spec = mcn('circleTOP', 'spec', radiusx=0.06, radiusy=0.06, radiusunit='fraction', softness=0.05, softnessunit='fraction', softnesstype='halfcosine',
              fillcolorr=0.8, fillcolorg=0.8, fillcolorb=0.8, fillalpha=1, bgcolorr=0, bgcolorg=0, bgcolorb=0, bgalpha=1, centerx=-0.2, centery=0.24)
mc_sum = mcn('compositeTOP', 'sum', mc_bg, mc_body2, mc_rim, mc_spec, operand='add')
mc_out = mc.create(td.outTOP, 'out1'); mc_out.inputConnectors[0].connect(mc_sum)
msrc = nat(c, 'switchTOP', 'matcapsrc', mc.outputConnectors[0], i2, outputresolution='useinput')
msrc.par.index.expr = "(1 if len(parent().inputConnectors[1].connections) else 0)" + F
wh = sres(nat(c, 'constantTOP', 'defcolor', colorr=1, colorg=1, colorb=1, alpha=1))
csrc = nat(c, 'switchTOP', 'colorsrc', wh, i3)
csrc.par.index.expr = "(1 if len(parent().inputConnectors[2].connections) else 0)" + F
sres(csrc)

# ---------------- shading core: one small GLSL pass (matcap lookup + key/fill/rim lights) ----------------
R = 'math.radians'
sh = glsl(c, 'shade', rd(COMP, 'shade.glsl'), inputs=[src, msrc, csrc], res=True, vecs=[
    ('uA', [P + 'Mode.menuIndex', P + 'Normalenc.menuIndex', R + '(%sMatcaprotate)' % P, '1 if %sMatcapflip else 0' % P]),
    ('uB', [R + '(%sKeyazimuth)' % P, R + '(%sKeyelevation)' % P, P + 'Keyintensity', P + 'Ambient']),
    ('uC', [P + 'Keycolorr', P + 'Keycolorg', P + 'Keycolorb', P + 'Fillintensity']),
    ('uD', [P + 'Fillcolorr', P + 'Fillcolorg', P + 'Fillcolorb', P + 'Rimintensity']),
    ('uE', [P + 'Rimcolorr', P + 'Rimcolorg', P + 'Rimcolorb', P + 'Rimpower']),
    ('uF', [P + 'Specamount', P + 'Specpower', P + 'Wrap', P + 'Colormix']),
    ('uG', [P + 'Brightness', P + 'Background.menuIndex', 0, 0]),
])
finish_v2(c, COMP, sh, src)
report(c)
