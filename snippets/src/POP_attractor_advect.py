exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name):
    # keep the parameter values set in this snippet when the external tox reloads
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def beat_mod(ex, bpm=120):
    """Beat CHOP -> Rename to the library's modulation channels: beat (pulse), band1 (smooth 0..1 wave)."""
    bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False; bt.par.bpm = bpm
    rn = ex.create(td.renameCHOP, 'modnames', col=1, row=1); rn.inputConnectors[0].connect(bt)
    rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
    return rn

def text_mask(ex, txt='TD', size=0.5):
    t = ex.create(td.textTOP, 'mask'); t.par.text = txt
    t.par.outputresolution = 'custom'; t.par.resolutionw = 1280; t.par.resolutionh = 720
    t.par.fontsizex = 380; t.par.fontsizey = 380
    t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0; t.par.bgalpha = 1
    t.par.fontcolorr = t.par.fontcolorg = t.par.fontcolorb = 1
    return t
s = begin('POP_attractor_advect')

def points_mat(ex, size=3.0):
    m = ex.create(td.pointspriteMAT, 'sprite')
    m.par.pointsize = size; m.par.blending = True; m.par.srcblend = 'sa'; m.par.destblend = 'one'; m.par.depthwriting = False
    return m

def line_mat(ex):
    m = ex.create(td.constantMAT, 'linemat'); m.par.applypointcolor = True
    m.par.blending = True; m.par.srcblend = 'sa'; m.par.destblend = 'one'; m.par.depthwriting = False; m.par.alpha = 0.7
    return m

def scatter(ex, shape='sphere', n=8000, size=0.9):
    """Real POP geometry: a Sphere/Torus/Box POP scattered into points with a Sprinkle POP."""
    if shape == 'torus':
        g = ex.create(td.torusPOP, 'torus'); g.par.radx = size; g.par.rady = size * 0.35
    elif shape == 'box':
        g = ex.create(td.boxPOP, 'box'); g.par.sizex = g.par.sizey = g.par.sizez = size * 1.6
    else:
        g = ex.create(td.spherePOP, 'sphere'); g.par.type = 'geodesic'; g.par.freq = 6
        g.par.radx = g.par.rady = g.par.radz = size
    sp = ex.create(td.sprinklePOP, 'scatter'); sp.par.method = 'total'; sp.par.numpoints = n
    sp.inputConnectors[0].connect(g)
    return sp

ex = example(s, 1, 'Sphere flows into the Lorenz butterfly',
  'A Sphere POP, scattered into 8000 points, goes into in1. The points are advected along the Lorenz field\n'
  'and stream onto the attractor; out1 is rendered with render_pop.\n'
  'Try: Reset (recapture the sphere), Speed, Field Size, Attractor menu (aizawa, thomas, halvorsen, dadras).')
src = scatter(ex, 'sphere', 8000, 0.9)
a = inst(ex, 'POP_attractor_advect')
connect(src, a)
r = render_pop(ex, a.op('out1'), cam_dist=3.4, cam_height=0.7, material=points_mat(ex, 3.0))
out(ex, 1, r)

ex = example(s, 2, 'Trails: a torus winds into Thomas',
  'Trails = on turns out1 into polylines (Trail POP history, 0.8 s long) so you see the flow lines of the\n'
  'Thomas attractor. Morph blends part of the points toward Aizawa.\n'
  'Try: Trail Length, Morph, Substeps, Color Speed Scale.')
src = scatter(ex, 'torus', 3000, 0.9)
a = inst(ex, 'POP_attractor_advect')
connect(src, a)
a.par.Attractor = 'thomas'; a.par.Attractorb = 'aizawa'; a.par.Morph = 0.25
a.par.Fieldscale = 0.5; a.par.Trails = True; a.par.Traillength = 0.8
r = render_pop(ex, a.op('out1'), cam_dist=3.4, cam_height=0.7, material=line_mat(ex))
out(ex, 2, r)

ex = example(s, 3, 'Beat-driven Halvorsen',
  'A Box POP scatter advected by Halvorsen. The Beat CHOP (modulation input, last connector) kicks the\n'
  'speed on every beat (beat), swells the flow (band2) and wobbles the coefficients (band1).\n'
  'Try: Coef Animate, Rebirth (re-seed points from the box each frame), Color Mix.')
src = scatter(ex, 'box', 8000, 0.9)
a = inst(ex, 'POP_attractor_advect')
connect(src, a)
a.par.Attractor = 'halvorsen'; a.par.Fieldscale = 0.5; a.par.Coefmod = 0.3; a.par.Rebirth = 0.004
rn = beat_mod(ex)
a.inputConnectors[1].connect(rn)
r = render_pop(ex, a.op('out1'), cam_dist=3.4, cam_height=0.7, material=points_mat(ex, 3.0))
out(ex, 3, r)
finish(s)
