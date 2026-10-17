exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
NAME = 'MAT_iridescent'
s = begin(NAME)
ENVPHOTO = 'Map/PalaceOfFineArts-360Designs.io.jpg'

def rig(ex, inst, shape='torus', dist=None, via_render=False):
    """Geometry COMP (your own geometry) + Camera + Light + Render TOP; the material comes from
    <instance>/mat. Returns the Render TOP.
    The material is applied with apply_material (what dragging onto Apply To does): to the Geometry COMP, or with
    via_render=True to the Render TOP (Override Material)."""
    dist = dist or {'torus': 6.5, 'teapot': 4.3, 'sphere': 7.0}[shape]
    geo = ex.create(td.geometryCOMP, 'geo', col=1, row=1)
    for o in list(geo.children): o.destroy()
    if shape == 'torus':
        so = geo.create(td.torusSOP, 'shape'); so.par.rows = 96; so.par.cols = 192; so.par.radx = 1.1; so.par.rady = 0.45
        geo.par.rx = 25
    elif shape == 'sphere':
        so = geo.create(td.sphereSOP, 'shape'); so.par.rows = 96; so.par.cols = 192; so.par.radx = 1.3; so.par.rady = 1.3; so.par.radz = 1.3
    else:
        so = geo.create(td.fileinSOP, 'shape'); so.par.file.expr = sample_expr('Geo/UtahTeapot.obj')
        geo.par.sx = geo.par.sy = geo.par.sz = 1.15; geo.par.ry = -35; geo.par.ty = -0.45
    so.display = True; so.render = True
    cam = ex.create(td.cameraCOMP, 'cam', col=2, row=1); cam.par.tz = dist; cam.par.ty = 0.2
    lt = ex.create(td.lightCOMP, 'light', col=3, row=1); lt.par.tx = 3; lt.par.ty = 4; lt.par.tz = 4
    r = ex.create(td.renderTOP, 'render', col=4, row=1)
    r.par.camera = cam.name; r.par.geometry = geo.name; r.par.lights = lt.name
    r.par.outputresolution = 'custom'; r.par.resolutionw = 1280; r.par.resolutionh = 720
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.015; r.par.bgcolora = 1
    r.par.antialias = 'aa4'; r.par.format = 'rgba16float'
    apply_material(inst, r if via_render else geo)
    return r

def envphoto(ex):
    e = ex.create(td.moviefileinTOP, 'envphoto', col=0, row=2); e.par.file.expr = sample_expr(ENVPHOTO)
    return e

def ramp_phase(ex, freq=0.125):
    l = ex.create(td.lfoCHOP, 'phase', col=0, row=3); l.par.wavetype = 'ramp'; l.par.frequency = freq
    l.par.channelname = 'phase'; l.par.amp = 1; l.par.offset = 0
    return l

def lfo_par(ex, inst, par, lo, hi, freq=0.2, name='lfo'):
    """LFO CHOP (sine between lo and hi) driving one parameter of the instance by expression."""
    l = ex.create(td.lfoCHOP, name, col=0, row=3); l.par.wavetype = 'sin'; l.par.frequency = freq
    l.par.amp = (hi - lo) / 2.0; l.par.offset = (hi + lo) / 2.0; l.par.channelname = 'v'
    getattr(inst.par, par).expr = "parent().op('%s')['v'].eval()" % l.name
    return l

ex = example(s, 1, 'Thin-film on your own torus',
  'MAT_iridescent is a material. Drag your Geometry COMP (or a Render TOP) onto the material\'s Apply To field.\n'
  'Any geometry with normals works; this is a plain Torus SOP, a Camera, a Light and a Render TOP.\n'
  'Try: Filmthickness (the colour band: 200 blue-green, 500 magenta-gold), Iridescence 0 -> 1, Fresnelpower for rim colour.')
m = instance(ex, NAME, col=0)
out(ex, 1, rig(ex, m, 'torus'))

ex = example(s, 2, 'Soap-bubble teapot (parameter recipe)',
  'Samples/Geo/UtahTeapot.obj in a File In SOP. Recipe: Filmthickness 620, Filmvariation 450 and\n'
  'Oilscale 2.5 give swirling oil-slick bands; Basecolor near black keeps the colour saturated.\n'
  'Raise Oilmotion to make the film drift faster; Anisotropy + Brushangle stretch the sheen into brushed streaks.')
m = instance(ex, NAME, col=0)
m.par.Filmthickness = 620; m.par.Filmvariation = 450; m.par.Oilscale = 2.5; m.par.Oilmotion = 1.5
out(ex, 2, rig(ex, m, 'teapot'))

ex = example(s, 3, 'Environment photo + breathing film (LFO)',
  'A 360 photo into in1 replaces the studio reflection (iridescent shows it through the film).\n'
  'A slow LFO drives Filmthickness by expression, so the rainbow bands crawl across the surface.\n'
  'Swap the LFO for an Audio Spectrum CHOP channel (scaled to 200-700) to make the colour pulse with music.')
env = envphoto(ex)
m = instance(ex, NAME, col=0)
m.inputConnectors[0].connect(env)
lfo_par(ex, m, 'Filmthickness', 250, 650, 0.15)
out(ex, 3, rig(ex, m, 'torus', via_render=True))

for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
