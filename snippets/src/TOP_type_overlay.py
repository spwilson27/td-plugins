exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
s = begin('TOP_type_overlay')
# reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.

ex = example(s, 1, 'Title card over a movie', 'A movie into in1 gets the Rendah-style title, corner telemetry, crop marks and border.\nTry: Title (lines starting with * are bold), Layout, Margin, Opacity.\nUnconnected, the overlay sits on black at 1280x720.')
src = ex.create(moviefileinTOP, 'count'); src.par.file.expr = sample_expr('Map/Count.mov')
t = instance(ex, 'TOP_type_overlay')
t.inputConnectors[0].connect(src)
out(ex, 1, t)

ex = example(s, 2, 'Poster layout recipe', 'Poster layout with a huge title, white-only look (Accent off), thicker frame and extra data columns.\nUse Mix to fade the whole overlay in and out for a live title drop.\nTitlesize and Telelines scale the text blocks.')
src = ex.create(moviefileinTOP, 'photo'); src.par.file.expr = sample_expr('Map/Mettler.1.jpg')
t = instance(ex, 'TOP_type_overlay')
t.inputConnectors[0].connect(src)
t.par.Layout = 'poster'; t.par.Title = '*NIGHT\n*SHIFT\nlive set\nclub 04 / 2026'
t.par.Accent = 0; t.par.Borderwidth = 3; t.par.Telelines = 12; t.par.Titlesize = 0.07; t.par.Margin = 0.06
out(ex, 2, t)

ex = example(s, 3, 'Title pumped by band1', 'An LFO named band1 goes into the modulation input (the last input) and pumps the title size.\nModamount sets how much; Layout = data adds the extra telemetry columns.\nSwap the LFO for a Beat or Audio Spectrum CHOP to hit the title on the kick.')
src = ex.create(moviefileinTOP, 'fish', col=0, row=1); src.par.file.expr = sample_expr('Map/Starfish.tif')
b1 = ex.create(lfoCHOP, 'band1', col=2, row=1); b1.par.channelname = 'band1'; b1.par.frequency = 1.0; b1.par.amp = 0.5; b1.par.offset = 0.5
t = instance(ex, 'TOP_type_overlay', col=4)
t.inputConnectors[0].connect(src); t.inputConnectors[1].connect(b1)
t.par.Layout = 'data'; t.par.Modamount = 1.0
out(ex, 3, t)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
