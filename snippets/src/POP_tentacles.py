exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_tentacles')

ex = example(s, 1, 'Chrome tentacles', 'GEN_tentacles with defaults: 48 chrome tentacles writhe out of a sphere in a dark studio.\nTry: Count, Length, Wiggle (writhing amount), Thickness and Taper (shape of each arm).\nCamdist and Orbitturns control the camera orbit.')
t = instance(ex, 'GEN_tentacles')
out(ex, 1, t)

ex = example(s, 2, 'Matte tentacles in a real environment', 'A 360 photo on in1 lights the scene instead of the studio softboxes.\nMetallic = 0 and a coloured Basecolor turn the chrome into painted rubber; Roughness softens highlights.\nRaise Envintensity if the environment looks dim.')
src = ex.create(moviefileinTOP, 'env'); src.par.file.expr = sample_expr('Map/PalaceOfFineArts-360Designs.io.jpg')
t = instance(ex, 'GEN_tentacles')
t.inputConnectors[0].connect(src)
t.par.Metallic = 0.0; t.par.Roughness = 0.45; t.par.Basecolorr = 0.9; t.par.Basecolorg = 0.2; t.par.Basecolorb = 0.15; t.par.Count = 90; t.par.Length = 1.6
out(ex, 2, t)

ex = example(s, 3, 'Growing on a Clock CHOP', 'A ramp LFO named phase drives Clock (Timesource = phase), and Autogrow makes the tentacles grow out and retract once per cycle.\nWiggle, wave and pulse motion are integer multiples of the phase, so the loop is seamless.\nSet the LFO frequency to retime; Noisecycles and Wavecycles change how busy each loop is.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.125; lfo.par.channelname = 'phase'; lfo.par.amp = 1; lfo.par.offset = 0
t = instance(ex, 'GEN_tentacles')
t.par.Clock = lfo; t.par.Timesource = 'phase'; t.op('clock_exec').module.sync(t); t.par.Autogrow = True
out(ex, 3, t)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
