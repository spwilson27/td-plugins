exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

# ---- local MAT snippet helpers (self-contained; each MAT_ snippet file carries this block) ----
GRADE = """
uniform vec4 uG; // exposure, bg, vignette
out vec4 fragColor;
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.,1.); }
void main(){
  vec2 uv = vUV.st; vec4 r = texture(sTD2DInputs[0], uv);
  vec2 q = uv - vec2(0.5, 0.45);
  vec3 bg = mix(vec3(0.010,0.010,0.012), vec3(0.060,0.062,0.072), clamp(1.0-dot(q,q)*2.2,0.,1.)) * uG.y;
  vec3 col = bg*(1.0-r.a) + r.rgb;
  col = pow(aces(col*uG.x), vec3(1.0/2.2));
  fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
"""

def inst(ex, comp, tag=None, col=None, row=0, small=True, **pars):
    c = instance(ex, comp, col=col, row=row)
    # keep the values set below when the external tox is (re)loaded with the snippet
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    if tag:
        c.name = 'ex%d_%s_%s' % (ex.n, comp, tag)
    for k, v in pars.items():
        if isinstance(v, str) and k not in ('Mode', 'Style', 'Matcap', 'Pattern', 'Wiremode', 'Timesource', 'Decaymode', 'Space', 'Blend'):
            getattr(c.par, k).val = v
        else:
            getattr(c.par, k).val = v
    if small:      # the component's own turntable preview is not what we look at here: keep it cheap
        c.par.Resolutionw = 160; c.par.Resolutionh = 90; c.viewer = False
    return c

def scene(ex, items, cam_z=4.2, cam_y=0.0, expo=1.0, shape_scale=1.0, res=(1280, 720), bg=1.0, col0=1, row0=1, spin=18, via_render=False):
    """items: list of dict(comp=<instance COMP>, shape='torus'|'sphere'|'teapot', x=0, y=0, scale=1, instances=None)
    Geometry COMP (own SOPs) + material via apply_material (Apply To) + Camera + Light + Render TOP + tonemap.
    Returns the graded TOP (feed it into out())."""
    geos = []
    for i, it in enumerate(items):
        g = ex.create(td.geometryCOMP, 'geo%d' % (i + 1), col=col0 + i, row=row0)
        for ch in list(g.children): ch.destroy()
        sh = it.get('shape', 'torus')
        if sh == 'torus':
            s = g.create(td.torusSOP, 'shape'); s.par.rows = 48; s.par.cols = 96; s.par.radx = 0.9; s.par.rady = 0.38
            g.par.rx = 62
        elif sh == 'sphere':
            s = g.create(td.sphereSOP, 'shape'); s.par.type = 'poly'; s.par.freq = 24; s.par.normals = True
            s.par.radx = s.par.rady = s.par.radz = 1.0
        else:
            f = g.create(td.fileinSOP, 'file'); f.par.file.expr = "app.samplesFolder + '/Geo/UtahTeapot.obj'"
            n = g.create(td.facetSOP, 'shape'); n.inputConnectors[0].connect(f)
            n.par.postnml = True; n.par.unique = False
            g.par.rx = 0
            s = n
        o = g.create(td.outSOP, 'out1'); o.inputConnectors[0].connect(s); o.render = True; o.display = True
        sc = it.get('scale', 1.0)
        g.par.scale = sc
        g.par.tx = it.get('x', 0); g.par.ty = it.get('y', 0) - (0.46 * sc if sh == 'teapot' else 0)
        if sh != 'torus' or True:
            g.par.ry.expr = "absTime.seconds*%s" % spin
        if it.get('instances'):
            g.par.instancing = True
            g.par.instancecountmode = 'manual'
            g.par.numinstances.expr = it['instances']
        geos.append(g)
    cam = ex.create(td.cameraCOMP, 'cam', col=col0 + len(items), row=row0)
    cam.par.tz = cam_z; cam.par.ty = cam_y; cam.par.fov = 45; cam.par.near = 0.3; cam.par.far = 60
    lt = ex.create(td.lightCOMP, 'light', col=col0 + len(items) + 1, row=row0)
    lt.par.ty = 3; lt.par.tz = 4
    r = ex.create(td.renderTOP, 'render', col=col0, row=row0 + 1)
    r.par.camera = cam.name; r.par.geometry = ' '.join(g.name for g in geos); r.par.lights = lt.name
    r.par.outputresolution = 'custom'; r.par.resolutionw = res[0]; r.par.resolutionh = res[1]
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0; r.par.bgcolora = 0
    r.par.format = 'rgba16float'; r.par.antialias = 'aa4'
    if via_render:   # one material for the whole scene: Render TOP Override Material
        assert len({id(it['comp']) for it in items}) == 1
        apply_material(items[0]['comp'], r)
    else:
        for c in {id(it['comp']): it['comp'] for it in items}.values():
            apply_material(c, *[g for g, it in zip(geos, items) if it['comp'] is c])
    d = ex.create(td.textDAT, 'grade_code', col=col0 + 1, row=row0 + 1); d.text = GRADE
    gr = ex.create(td.glslTOP, 'tonemap', col=col0 + 2, row=row0 + 1)
    gr.inputConnectors[0].connect(r); gr.par.pixeldat = d
    gr.par.outputresolution = 'custom'; gr.par.resolutionw = res[0]; gr.par.resolutionh = res[1]; gr.par.format = 'rgba16float'
    gr.seq.vec.numBlocks = 1; gr.par.vec0name = 'uG'; gr.par.vec0valuex = expo; gr.par.vec0valuey = bg
    return gr

def lfo_band(ex, name='lfo', freq=0.4, col=None, row=2, chan='band1'):
    l = ex.create(td.lfoCHOP, name, col=col, row=row)
    l.par.wavetype = 'sin'; l.par.frequency = freq; l.par.amp = 0.5; l.par.offset = 0.5
    rn = ex.create(td.renameCHOP, name + '_rename', col=None if col is None else col + 1, row=row)
    rn.par.renamefrom = 'chan1'; rn.par.renameto = chan; rn.inputConnectors[0].connect(l)
    return rn

def beat_mod(ex, name='beat', period=4, col=None, row=2):
    b = ex.create(td.beatCHOP, name, col=col, row=row)
    b.par.ramp = True; b.par.pulse = True; b.par.period = period
    rn = ex.create(td.renameCHOP, name + '_rename', col=None if col is None else col + 1, row=row)
    rn.par.renamefrom = 'ramp pulse'; rn.par.renameto = 'phase beat'; rn.inputConnectors[0].connect(b)
    return rn

def merge_mod(ex, *srcs, col=None, row=2):
    m = ex.create(td.mergeCHOP, 'mods', col=col, row=row)
    for i, s in enumerate(srcs): m.inputConnectors[i].connect(s)
    return m

def tidy(s):
    """Pack each example's nodes into a 5-column grid inside its Annotate box (creation order, exampleN last)."""
    for n in range(1, s.fetch('examples', 0) + 1):
        ops_ = [o for o in s.children if o.name.startswith('ex%d_' % n) or o.name == 'example%d' % n]
        ops_.sort(key=lambda o: o.name == 'example%d' % n)
        for i, o in enumerate(ops_):
            o.nodeX = (n - 1) * (EX_W + GAP) + 20 + (i % 5) * 200
            box = s.op('annotate%d' % n)
            o.nodeY = box.nodeY + box.nodeHeight - 150 - (i // 5) * 170   # relative to the Annotate box
N = 'MAT_velvet'
s = begin(N)

ex = example(s, 1, 'Velvet sheen on a teapot',
  'Single-pass sheen: fuzzy grazing-angle highlight plus rim fuzz, no UVs.\n'
  'Drag your Geometry COMP (or a Render TOP) onto the material\'s Apply To field.\n'
  'Try: Basecolor / Sheencolor for fabric dye, Fuzz (low = tight satin, high = soft moleskin), Rimfuzz for the halo.')
p = inst(ex, N, col=0, row=0)
g = scene(ex, [dict(comp=p, shape='teapot')], cam_z=3.8)
out(ex, 1, g)

ex = example(s, 2, 'Shell fur (instanced shells)',
  'Mode=shells needs instancing: the Geometry COMP has Instancing on, Count = manual, Instances = the MAT_velvet Shells parameter\n'
  '(numinstances expression: op(\'ex2_MAT_velvet\').par.Shells). Each instance is one fur layer pushed out along the normal.\n'
  'Recipe: Shells 32, Furlength 0.09, Density 90, Strandwidth 0.6 = plush; Furlength 0.02 = peach fuzz. Rootdark gives depth.')
p = inst(ex, N, col=0, row=0, Mode='shells', Shells=32, Furlength=0.09, Density=90, Strandwidth=0.6)
p.par.Basecolorr = 0.05; p.par.Basecolorg = 0.12; p.par.Basecolorb = 0.35
p.par.Sheencolorr = 0.45; p.par.Sheencolorg = 0.7; p.par.Sheencolorb = 1.0
g = scene(ex, [dict(comp=p, shape='sphere', instances="op('ex2_MAT_velvet').par.Shells")], cam_z=5.2)
out(ex, 2, g)

ex = example(s, 3, 'Pulsing sheen',
  'An LFO renamed band1 and a Beat CHOP feed the optional modulation input.\n'
  'band1 raises Sheen strength, band2 (unused here, add a second LFO) would widen Rimfuzz. Modamount scales the effect.\n'
  'Swap the LFO for an Audio Spectrum CHOP with channels renamed band1..band4 for a velvet that breathes with the music.')
lf = lfo_band(ex, 'lfo', 0.4, col=0, row=2)
p = inst(ex, N, col=0, row=0, Sheen=0.4, Modamount=1.0)
connect(lf, p)
g = scene(ex, [dict(comp=p, shape='torus')], cam_z=6.4, via_render=True)
out(ex, 3, g)
tidy(s); finish(s)
