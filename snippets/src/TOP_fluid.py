exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('GEN_fluid_2d')

def inst(ex, name):
    # keep the values set below when the external tox reloads (custom pars would otherwise reset to defaults)
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

# 1. defaults -----------------------------------------------------------------------------
ex = example(s, 1, 'Animated emitters',
  'GEN_fluid_2d with nothing connected: three Lissajous emitters stir hue-cycling dye.\n'
  'Try: Vorticity up (0.3 -> 1.5) for curlier eddies; Dyedissipation up for shorter trails.\n'
  'out1 = dye (tone-mapped), out2 = velocity field. Lower Iterations (8-12) if the GPU is busy.')
f = inst(ex, 'GEN_fluid_2d')
f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Vorticity = 0.8; f.par.Exposure = 3; f.par.Density = 0.08
out(ex, 1, f)

# 2. image as dye -------------------------------------------------------------------------
ex = example(s, 2, 'Smear a photo',
  'A photo into in1: its colour is injected as dye and its edges push the flow.\n'
  'Emitters = 0 so only the picture drives it. Raise Inputvelocity for more swirl along edges,\n'
  'Inputdensity for stronger colour; Reset clears the fluid so the picture re-forms.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file = sample('Map/Banana.tif')
f = inst(ex, 'GEN_fluid_2d')
f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Emitters = 0; f.par.Inputdensity = 1.5; f.par.Inputvelocity = 1.5; f.par.Exposure = 1.0
f.par.Dyedissipation = 0.04; f.par.Exposure = 2.5
f.inputConnectors[0].connect(img)
out(ex, 2, f)

# 3. modulation ---------------------------------------------------------------------------
ex = example(s, 3, 'Beat-driven splashes',
  'A Beat CHOP renamed to the modulation channels (beat, band1) goes into the last input (in2).\n'
  'beat kicks the emitter Force x4 on every pulse; band1 boosts the dye amount.\n'
  'Replace the Beat CHOP with an Audio Spectrum -> Rename (band1..band4, beat) to react to music.')
bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False
bt.par.bpm = 120
rn = ex.create(td.renameCHOP, 'names'); rn.inputConnectors[0].connect(bt)
rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
f = inst(ex, 'GEN_fluid_2d')
f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Force = 3; f.par.Density = 0.08; f.par.Exposure = 3
f.inputConnectors[1].connect(rn)
out(ex, 3, f)
finish(s)
