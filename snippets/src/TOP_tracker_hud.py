exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_tracker_hud')
# reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.

ex = example(s, 1, 'Tracking HUD on a photo', 'A photo into in1: the HUD locks boxes, ids and connecting lines onto its brightest features.\nTry: Points (how many targets), Threshold (how bright a feature must be),\nand Mix to fade the HUD against the clean photo.')
src = ex.create(moviefileinTOP, 'banana'); src.par.file.expr = sample_expr('Map/Banana.tif')
h = instance(ex, 'TOP_tracker_hud')
h.inputConnectors[0].connect(src)
out(ex, 1, h)

ex = example(s, 2, 'Data-heavy recipe', 'White labels showing id and coordinates, a tight grid, more lines, bigger boxes, dimmed picture.\nGood for a cold surveillance look: raise Dim to see more of the image, Scanlines for CRT grain,\nRefresh re-picks the targets several times per loop.')
src = ex.create(moviefileinTOP, 'beans'); src.par.file.expr = sample_expr('Map/Jellybeans.1.jpg')
h = instance(ex, 'TOP_tracker_hud')
h.inputConnectors[0].connect(src)
h.par.Points = 40; h.par.Labelmode = 'both'; h.par.Labelcolor = 'white'; h.par.Gridsize = 48
h.par.Linecount = 24; h.par.Boxsize = 22; h.par.Dim = 0.55; h.par.Scanlines = 0.8; h.par.Threshold = 0.45
out(ex, 2, h)

ex = example(s, 3, 'Beat-reactive targets (mod CHOP)', 'band1 (Jitter) and band2 (Boxsize) come from two LFOs merged into the modulation input (in2).\nThe targets shake and the boxes pulse; Modamount sets how hard.\nSwap the LFOs for an Audio Spectrum / Analyze CHOP (0-1) to react to music.')
src = ex.create(moviefileinTOP, 'oil', col=0, row=1); src.par.file.expr = sample_expr('Map/OilDrums.jpg')
l1 = ex.create(lfoCHOP, 'band1', col=1, row=1); l1.par.channelname = 'band1'; l1.par.frequency = 0.5; l1.par.amp = 0.5; l1.par.offset = 0.5
l2 = ex.create(lfoCHOP, 'band2', col=2, row=1); l2.par.channelname = 'band2'; l2.par.frequency = 1.0; l2.par.amp = 0.5; l2.par.offset = 0.5
mg = ex.create(mergeCHOP, 'merge', col=3, row=1)
mg.inputConnectors[0].connect(l1); mg.inputConnectors[0].connect(l2)
h = instance(ex, 'TOP_tracker_hud', col=4)
h.inputConnectors[0].connect(src); h.inputConnectors[1].connect(mg)
h.par.Modamount = 1.5
out(ex, 3, h)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
