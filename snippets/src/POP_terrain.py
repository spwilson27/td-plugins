exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_terrain_flyover')

ex = example(s, 1, 'Wire and solid terrain', 'GEN_terrain_flyover with defaults: a ridged, retro-futurist grid terrain with a central valley road.\nMode picks wireframe, solid or both; Amplitude and Frequency shape the mountains.\nSun and Horizonglow dress the horizon; Fogend sets how far you can see.')
t = instance(ex, 'GEN_terrain_flyover')
out(ex, 1, t)

ex = example(s, 2, 'Image as heightmap', 'A photo on in1 becomes the height field (Source = Image): bright pixels are peaks.\nThe image is mirrored along the flight direction so it never shows a seam.\nRaise Amplitude to exaggerate it; Valley carves the road through the middle.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
t = instance(ex, 'GEN_terrain_flyover')
t.inputConnectors[0].connect(src)
t.par.Source = 'image'; t.par.Amplitude = 10; t.par.Mode = 'both'
out(ex, 2, t)

ex = example(s, 3, 'Terraced, tempo-locked flight', 'A Beat CHOP bar ramp renamed phase drives Clock (Timesource = phase).\nOne bar travels Loops lattice periods of terrain, so the landscape returns to its start on the downbeat.\nStyle = Terraced makes stepped plateaus; Sun adds a striped sun on the horizon.')
bt = ex.create(beatCHOP, 'beat'); bt.par.bpm = 120; bt.par.ramp = False; bt.par.rampbar = True
rn = ex.create(renameCHOP, 'phase'); rn.inputConnectors[0].connect(bt); rn.par.renamefrom = 'rampbar'; rn.par.renameto = 'phase'
t = instance(ex, 'GEN_terrain_flyover')
t.par.Clock = rn; t.par.Timesource = 'phase'; t.op('clock_exec').module.sync(t); t.par.Style = 'terraced'; t.par.Sun = 0.8; t.par.Mode = 'wire'
out(ex, 3, t)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
