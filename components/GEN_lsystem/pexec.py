WATCH = ('Axiom', 'Rule1', 'Rule2', 'Rule3', 'Iterations', 'Angle', 'Lengthscale', 'Heading', 'Preset', 'Regenerate')
def _go(par):
    c = parent()
    if c.fetch('lsys_busy', False): return
    m = op('lsys_expand').module
    if par.name == 'Preset' and str(par.eval()) != 'custom':
        m.apply_preset(c, str(par.eval()))
    m.expand(c)

def onValueChange(par, prev):
    _go(par)

def onPulse(par):
    _go(par)
