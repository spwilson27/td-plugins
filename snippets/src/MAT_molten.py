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
N = 'MAT_molten'
s = begin(N)

ex = example(s, 1, 'Molten crust on a sphere',
  'Emissive lava cracks in a dark cooling crust, all in object space (no UVs, no textures).\n'
  'Drag your Geometry COMP (or a Render TOP) onto the material\'s Apply To field.\n'
  'Heat is the emission gain (HDR, the example tonemaps it). Cooling thickens the crust and hides the glow.\n'
  'Try: Cooling 0.6 (nearly cold), Heat 6 (white hot), Crackscale for bigger/smaller plates.')
p = inst(ex, N, col=0, row=0)
g = scene(ex, [dict(comp=p, shape='sphere')], cam_z=4.8, expo=0.9)
out(ex, 1, g)

ex = example(s, 2, 'Recipes: cooling stages',
  'Same geometry, three Cooling values: 0.0 = fresh lava, 0.35 = cooling, 0.5 = mostly crust (heat boosted to 7 with a blue tint).\n'
  'Flow warps the crack network, Streaks adds drawn-out glow, Crustbump the rock relief.\n'
  'Glowtint recolours the heat (here a blue-white plasma on the right).')
a = inst(ex, N, 'hot', col=0, row=0, Cooling=0.0, Heat=3.5)
b = inst(ex, N, 'mid', col=1, row=0, Cooling=0.35)
c = inst(ex, N, 'cold', col=2, row=0, Cooling=0.5, Heat=7.0)
c.par.Glowtintr = 0.4; c.par.Glowtintg = 0.7; c.par.Glowtintb = 1.5
g = scene(ex, [dict(comp=a, shape='sphere', x=-2.3, scale=0.9), dict(comp=b, shape='sphere', x=0, scale=0.9), dict(comp=c, shape='sphere', x=2.3, scale=0.9)], cam_z=8.8, col0=3, expo=0.9)
out(ex, 2, g)

ex = example(s, 3, 'Beat-pumped heat + external Clock',
  'Beat CHOP (channels renamed phase + beat) and an LFO (band1) -> modulation input. Heat is multiplied by 1 + band1*1.5 + beat.\n'
  'The Beat CHOP phase also drives the Clock parameter (Loop page) with Timesource=phase, so the crack flow loops exactly every 4 beats.\n'
  'Change the Beat CHOP Period to re-time the loop; raise Modamount for more punch.')
bt = beat_mod(ex, 'beat', 4, col=0, row=2)
lf = lfo_band(ex, 'lfo', 0.25, col=2, row=2)
mg = merge_mod(ex, lf, bt, col=4, row=2)
p = inst(ex, N, col=0, row=0, Timesource='phase', Heat=1.6, Cooling=0.25, Modamount=1.0)
p.par.Clock = bt.parent().path + '/' + bt.name if False else mg.name
connect(mg, p)
g = scene(ex, [dict(comp=p, shape='torus', scale=1.0)], cam_z=6.4, expo=0.9, via_render=True)
out(ex, 3, g)
tidy(s); finish(s)
