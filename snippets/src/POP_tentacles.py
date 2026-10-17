exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('POP_tentacles')

def metal(ex, name, rgb, metallic, rough):
    m = ex.create(pbrMAT, name)
    m.par.basecolorr, m.par.basecolorg, m.par.basecolorb = rgb
    m.par.metallic = metallic; m.par.roughness = rough
    return m

ex = example(s, 1, 'Tentacles from a torus', 'A Torus POP feeds in1: one writhing tentacle grows from every point, away from the origin.\nout1 is the tube mesh (POP); a Geometry COMP + Render TOP draws it here.\nTry: Length, Wiggle (writhing amount), Thickness and Taper (shape of each arm), Speed.')
src = ex.create(torusPOP, 'torus'); src.par.rows = 10; src.par.cols = 30
src.par.radx = 3.0; src.par.rady = 0.8
t = instance(ex, 'POP_tentacles')
t.inputConnectors[0].connect(src)
t.par.Length = 1.6; t.par.Thickness = 0.09; t.par.Segments = 32; t.par.Sides = 8
m = metal(ex, 'metal', (0.85, 0.85, 0.9), 0.2, 0.35)
r = render_pop(ex, t.op('out1'), cam_dist=16, cam_height=6, material=m)
out(ex, 1, r)

ex = example(s, 2, 'Fewer, longer, matte arms', 'A coarse geodesic Sphere POP gives a few points, so each tentacle is long and thick.\nSeed changes the personality of every arm; Grow retracts them into the sphere (try 0 to 1).\nNoisefreq sets how many bends each arm has, Pulse adds travelling swelling.')
src = ex.create(spherePOP, 'sphere'); src.par.type = 'geodesic'; src.par.freq = 2; src.par.radx = src.par.rady = src.par.radz = 1.2
t = instance(ex, 'POP_tentacles')
t.inputConnectors[0].connect(src)
t.par.Length = 4.0; t.par.Thickness = 0.16; t.par.Wiggle = 0.6; t.par.Noisefreq = 0.8; t.par.Seed = 7; t.par.Pulse = 0.3; t.par.Autogrow = True
m = metal(ex, 'rubber', (1.0, 0.3, 0.2), 0.0, 0.6)
r = render_pop(ex, t.op('out1'), cam_dist=14, cam_height=4, material=m)
out(ex, 2, r)

ex = example(s, 3, 'Driven by the modulation CHOP', 'LFOs named band1..band4 and beat feed the optional last input (modulation CHOP).\nband1 adds writhing, band2 the travelling wave, band3 the pulse, band4 the length, beat swells the thickness.\nReplace the LFOs with an Audio Spectrum / Beat CHOP for live reactivity.')
src = ex.create(spherePOP, 'sphere'); src.par.type = 'geodesic'; src.par.freq = 3
lfo = ex.create(lfoCHOP, 'bands'); lfo.par.wavetype = 'sin'; lfo.par.frequency = 0.4; lfo.par.amp = 0.5; lfo.par.offset = 0.5
lfo.par.channelname = 'band1'
c2 = ex.create(constantCHOP, 'mods')
for i, n in enumerate(('band2', 'band3', 'band4', 'beat')):
    getattr(c2.par, 'name%d' % i).val = n
    getattr(c2.par, 'value%d' % i).expr = '0.5+0.5*math.sin(absTime.seconds*%s)' % (1.3 + 0.9 * i)
mg = ex.create(mergeCHOP, 'merge'); mg.inputConnectors[0].connect(lfo); mg.inputConnectors[0].connect(c2)
t = instance(ex, 'POP_tentacles')
t.inputConnectors[0].connect(src)
t.inputConnectors[1].connect(mg)
t.par.Length = 2.0; t.par.Thickness = 0.06
m = metal(ex, 'metal', (0.85, 0.85, 0.9), 0.2, 0.35)
r = render_pop(ex, t.op('out1'), cam_dist=12, cam_height=4, material=m)
out(ex, 3, r)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
