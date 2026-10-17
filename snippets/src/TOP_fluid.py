exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_fluid')

def inst(ex, name):
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

# 1. real image ----------------------------------------------------------------------
ex = example(s, 1, 'Smear a photo',
  'A photo into in1 is advected as dye by the fluid; the internal stir emitters and the image edges push the flow.\n'
  'Try: Vorticity up for curlier eddies, Injectrate down so the smear lasts longer, Reset to restart.\n'
  'Dyesource = seed loads the picture only on Reset and then lets it smear away.\n'
  'out1 = smeared image, out2 = velocity, out3 = dye field.')
img = ex.create(td.moviefileinTOP, 'banana'); img.par.file.expr = sample_expr('Map/Banana.tif')
f = inst(ex, 'TOP_fluid')
f.par.Resolutionmode = 'custom'; f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Emitters = 3; f.par.Force = 8; f.par.Injectrate = 0.004; f.par.Vorticity = 1.0; f.par.Edgeforce = 2
f.inputConnectors[0].connect(img)
out(ex, 1, f)

# 2. fluid text -----------------------------------------------------------------------
ex = example(s, 2, 'Fluid text',
  'Text is just a Text TOP into in1: it slides left and right (Transform TOP) and is injected as dye,\n'
  'while a moving noise TOP (offset -0.5, so it is signed) into in2 is the force field that stirs it.\n'
  'Try: In2 Force up, Emitters = 0 to be driven only by the noise, Injectrate lower for longer smears.')
tx = ex.create(td.textTOP, 'text'); tx.par.text = 'FLUID'
tx.par.outputresolution = 'custom'; tx.par.resolutionw = 960; tx.par.resolutionh = 540
tx.par.fontsizex = 230
tx.par.fontcolorr = 1; tx.par.fontcolorg = 0.55; tx.par.fontcolorb = 0.15
tx.par.bgcolorr = 0.02; tx.par.bgcolorg = 0.03; tx.par.bgcolorb = 0.1; tx.par.bgalpha = 1
tr = ex.create(td.transformTOP, 'slide'); tr.inputConnectors[0].connect(tx)
tr.par.tx.expr = '0.25*math.sin(absTime.seconds*0.8)'
nz = ex.create(td.noiseTOP, 'flow', col=0, row=1); nz.par.outputresolution = 'custom'
nz.par.resolutionw = 480; nz.par.resolutionh = 270
nz.par.mono = False; nz.par.period = 0.5
nz.par.tx.expr = 'absTime.seconds*0.15'; nz.par.tz.expr = 'absTime.seconds*0.2'
nz.par.offset = -0.5; nz.par.format = 'rgba16float'
mt = nz
f = inst(ex, 'TOP_fluid')
f.par.Resolutionmode = 'custom'; f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Emitters = 0; f.par.Forcein = 0.4; f.par.Veldissipation = 0.03; f.par.Injectrate = 0.08; f.par.Edgeforce = 1
f.inputConnectors[0].connect(tr); f.inputConnectors[1].connect(mt)
out(ex, 2, f)

# 3. modulation ------------------------------------------------------------------------
ex = example(s, 3, 'Beat-driven stir',
  'A Beat CHOP renamed to the modulation channels (beat, band1) goes into the last input (in3).\n'
  'beat kicks the stir force x4 on each pulse; band1 raises vorticity.\n'
  'Replace the Beat CHOP with Audio Spectrum -> Rename (band1..band4, beat) to react to music.')
mv = ex.create(td.moviefileinTOP, 'count'); mv.par.file.expr = sample_expr('Map/Count.mov')
bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False
bt.par.bpm = 120
rn = ex.create(td.renameCHOP, 'names'); rn.inputConnectors[0].connect(bt)
rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
f = inst(ex, 'TOP_fluid')
f.par.Resolutionmode = 'custom'; f.par.Resolutionw = 960; f.par.Resolutionh = 540
f.par.Force = 5; f.par.Emitters = 3; f.par.Injectrate = 0.004
f.inputConnectors[0].connect(mv); f.inputConnectors[2].connect(rn)
out(ex, 3, f)
finish(s)
