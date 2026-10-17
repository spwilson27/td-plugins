exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# NOTE: reloadcustom is turned off at the end so the parameter values set below survive reloading the snippet.
s = begin('GEN_text_fluid')

ex = example(s, 1, 'Text dissolving in fluid', 'GEN_text_fluid with defaults: the word is injected into a fluid sim, smeared and swirled by two\ninternal emitters, then re-injected so it reforms.\nTry: Text, Smear and Vorticity (how violently it is stirred), Cycles (re-injections per loop).')
f = instance(ex, 'GEN_text_fluid')
f.par.Injectfrac = 0.3
out(ex, 1, f)

ex = example(s, 2, 'Slow melt, tinted', 'A longer word with stronger stirring (Smear 1.2, 3 Emitters) and one short injection per loop melts further.\nTint colours the monochrome result; Dissipation fades the dye faster or slower.\nPress Reset to clear the fluid and inject the text again immediately.')
f = instance(ex, 'GEN_text_fluid')
f.par.Text = 'MELTDOWN'; f.par.Smear = 1.2; f.par.Emitters = 3; f.par.Injectfrac = 0.12; f.par.Cycles = 1
f.par.Tintr = 1.0; f.par.Tintg = 0.35; f.par.Tintb = 0.25
out(ex, 2, f)

ex = example(s, 3, 'Re-inject on a beat', 'A Beat CHOP bar ramp renamed phase drives Clock (Timesource = phase).\nWith Cycles = 1 the text is re-injected exactly once per bar, on the downbeat.\nRaise Cycles to re-inject on every beat; the fluid itself stays a free-running simulation.')
bt = ex.create(beatCHOP, 'beat'); bt.par.bpm = 120; bt.par.ramp = False; bt.par.rampbar = True
rn = ex.create(renameCHOP, 'phase'); rn.inputConnectors[0].connect(bt); rn.par.renamefrom = 'rampbar'; rn.par.renameto = 'phase'
f = instance(ex, 'GEN_text_fluid')
f.par.Clock = rn; f.par.Timesource = 'phase'; f.op('clock_exec').module.sync(f); f.par.Cycles = 1; f.par.Injectfrac = 0.3; f.par.Text = 'DOWNBEAT'
out(ex, 3, f)
for c in s.findChildren(type=COMP, depth=1):
    if c.par.externaltox.eval(): c.par.reloadcustom = False
finish(s)
