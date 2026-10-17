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
s = begin('POP_particle_emitter')

def sprite(ex, size=3.0, alpha=0.7):
    m = ex.create(td.pointspriteMAT, 'sprite', row=2)
    m.par.pointsize = size; m.par.blending = True
    m.par.srcblend = 'sa'; m.par.destblend = 'one'; m.par.depthwriting = False; m.par.alpha = alpha
    return m

def pop_out(ex, n, e, mat, dist=9.0):
    r = render_pop(ex, e.op('out1'), cam_dist=dist, cam_height=1.0, material=mat)
    out(ex, n, r)
    return r

ex = example(s, 1, 'Particles from a sphere',
  'A Sphere POP feeds the emitter input: particles are born on its points, lifted by curl noise\n'
  'and pulled towards an attractor. out1 is a particle POP rendered here by Geometry + Render TOP.\n'
  'Try: Curlstrength for turbulence, Gravity for weight, Lifetime / Emitrate for density.')
sp = ex.create(td.spherePOP, 'sphere'); sp.par.radx = sp.par.rady = sp.par.radz = 1.2
e = inst(ex, 'POP_particle_emitter'); e.par.Count = 120000; e.par.Emitrate = 30000
e.inputConnectors[0].connect(sp.outputConnectors[0] if sp.isCOMP else sp)
pop_out(ex, 1, e, sprite(ex))

ex = example(s, 2, 'Grid emitter, twin attractors',
  'A Grid POP is the emitter; gravity is off and two attractors (Attr1/Attr2 strength) sling the\n'
  'particles between them. Try: Attr2strength negative to repel, Damping for tighter orbits,\n'
  'Emitvelocity for the initial push.')
gr = ex.create(td.gridPOP, 'grid')
e = inst(ex, 'POP_particle_emitter'); e.par.Count = 120000; e.par.Emitrate = 30000
e.inputConnectors[0].connect(gr)
e.par.Gravity = 0; e.par.Emitvelocity = 0.4; e.par.Attr2strength = 2.0
e.par.Curlstrength = 0.3; e.par.Damping = 0.5
e.par.Colorr, e.par.Colorg, e.par.Colorb = 0.9, 0.9, 0.85
e.par.Colorendr, e.par.Colorendg, e.par.Colorendb = 0.85, 0.15, 0.1
pop_out(ex, 2, e, sprite(ex, 2.5, 0.8))

ex = example(s, 3, 'Beat bursts from a torus',
  'A Torus POP emitter; a Beat CHOP (renamed beat/band1) is wired to the last input: each beat\n'
  'multiplies the emit rate, band1 swells the curl strength.\n'
  'Try: change the Beat CHOP bpm, or drive the channels from an Audio Spectrum.')
bx = ex.create(td.torusPOP, 'torus'); bx.par.radx = 1.3; bx.par.rady = 0.4
e = inst(ex, 'POP_particle_emitter'); e.par.Count = 120000; e.par.Emitrate = 15000
e.par.Curlstrength = 0.8; e.par.Gravity = -0.2
e.inputConnectors[0].connect(bx)
rn = beat_mod(ex)
e.inputConnectors[1].connect(rn)
pop_out(ex, 3, e, sprite(ex))
finish(s)
