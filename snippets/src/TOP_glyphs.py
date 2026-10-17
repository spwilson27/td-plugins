exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_glyph_tunnel')

ex = example(s, 1, 'Glyph tunnel', 'GEN_glyph_tunnel with defaults: rings of glyphs streaming toward you down a tunnel.\nTry: Cols (glyphs per ring), Density (how many are lit), Fog (depth falloff), Refresh to reshuffle glyphs.\nAccentamt adds a few red glyphs.')
g = instance(ex, 'GEN_glyph_tunnel')
out(ex, 1, g)

ex = example(s, 2, 'Digital rain', 'Mode = Rain turns it into falling columns with fading trails.\nA custom Charset (any characters, edit the string) changes the alphabet, Trail sets tail length.\nTint recolours the glyphs; Brightness may need a nudge for dark tints.')
g = instance(ex, 'GEN_glyph_tunnel')
g.par.Mode = 'rain'; g.par.Charset = '01'; g.par.Cols = 48; g.par.Trail = 0.85
g.par.Tintr = 0.35; g.par.Tintg = 1.0; g.par.Tintb = 0.55
out(ex, 2, g)

ex = example(s, 3, 'Wall driven by a Clock CHOP', 'Mode = Wall with a ramp LFO named phase on Clock (Timesource = phase).\nThe wall scrolls exactly Rows-Per-Loop rows per LFO cycle, so the loop is seamless and the scroll speed follows the LFO frequency.\nSlow the LFO for a calm scroll, speed it up for a rush.')
lfo = ex.create(lfoCHOP, 'clock'); lfo.par.wavetype = 'ramp'; lfo.par.frequency = 0.25; lfo.par.channelname = 'phase'; lfo.par.amp = 1; lfo.par.offset = 0
g = instance(ex, 'GEN_glyph_tunnel')
g.par.Clock = lfo; g.par.Timesource = 'phase'; g.op('clock_exec').module.sync(g); g.par.Mode = 'wall'
out(ex, 3, g)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
