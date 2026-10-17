exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_dof_motionblur')

# 1. DOF on a photo with a radial depth map
ex = example(s, 1, 'Depth of field on a photo', 'Movie File In (Jellybeans) -> in1, Ramp TOP (radial) -> in2 as a depth map (0 near, 1 far).\nFocus picks the sharp depth, Range its thickness, Maxblur the bokeh size.\nBlades switches between a soft round blur and a hard-edged (box) blur.\nTurn on Showdepth / Showcoc to see what the effect thinks is in focus.')
m = ex.create(moviefileinTOP, 'photo'); m.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
d = ex.create(rampTOP, 'depth'); d.par.type = 'radial'
d.par.outputresolution = 'custom'; d.par.resolutionw = 1280; d.par.resolutionh = 720
g = instance(ex, 'TOP_dof_motionblur'); g.inputConnectors[0].connect(m); g.inputConnectors[1].connect(d)
g.par.Focus = 0.0; g.par.Range = 0.08; g.par.Maxblur = 40; g.par.Mbactive = 0
out(ex, 1, g)

# 2. rack focus via modulation
ex = example(s, 2, 'Rack focus with an LFO', 'LFO CHOP -> Rename (chan1 -> band1) -> modulation input (the last input, in4).\nband1 pushes Focus by Modamount * 0.5, so the sharp plane sweeps through the scene.\nWithout any input the built-in scene (floor lines and dots at many depths) shows the effect.\nUse a Beat CHOP renamed band1 for a focus pull on every beat.')
l = ex.create(lfoCHOP, 'lfo'); l.par.amp = 0.5; l.par.offset = 0.5; l.par.frequency = 0.25
r = ex.create(renameCHOP, 'rename'); r.inputConnectors[0].connect(l)
r.par.renamefrom = 'chan1'; r.par.renameto = 'band1'
g = instance(ex, 'TOP_dof_motionblur'); g.inputConnectors[3].connect(r)
g.par.Focus = 0.3; g.par.Modamount = 1.2; g.par.Maxblur = 45; g.par.Mbactive = 0
out(ex, 2, g)

# 3. motion blur from a velocity map
ex = example(s, 3, 'Velocity motion blur on a movie', 'Movie File In (Count.mov) -> in1, Constant TOP (R = 0.02) -> in3 as a velocity map.\nin3 R,G are a velocity in uv units: here a constant sideways smear.\nVelscale scales it, Velsamples sets smoothness, Shutter adds frame-accumulation trails.\nFeed a Optical Flow / Slope TOP into in3 for a real per-pixel velocity.')
m = ex.create(moviefileinTOP, 'movie'); m.par.file.expr = sample_expr('Map/Count.mov')
v = ex.create(constantTOP, 'velocity'); v.par.colorr = 0.03; v.par.colorg = 0.0; v.par.colorb = 0; v.par.alpha = 1
v.par.outputresolution = 'custom'; v.par.resolutionw = 1280; v.par.resolutionh = 720
g = instance(ex, 'TOP_dof_motionblur'); g.inputConnectors[0].connect(m); g.inputConnectors[2].connect(v)
g.par.Maxblur = 0; g.par.Velscale = 2; g.par.Shutter = 0.5
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
