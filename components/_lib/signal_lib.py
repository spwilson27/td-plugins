# ---- signal_lib: loop params + periodic default source (appended after lib.py) ----
LENEXPR = "max(0.25,(parent().par.Loopseconds if parent().par.Loopseconds>0 else parent().par.Loopbeats*60.0/max(1.0,parent().par.Bpm)))"
PEXPR = "((parent().par.Phase if parent().par.Timesource=='phase' else absTime.seconds/%s) %% 1.0)" % LENEXPR
FREXPR = "max(2,2*round(%s*15))" % LENEXPR
def uP(extra=0):
    return ('uP', [PEXPR, LENEXPR, FREXPR, extra])

def loop_pars(c, beats=8):
    add_pars(c, [
        ('Timesource', 'menu', [('abstime', 'Abs Time'), ('phase', 'Phase')], 0),
        ('Phase', 'float', 0, 0, 1),
        ('Loopbeats', 'float', beats, 1, 64),
        ('Bpm', 'float', 120, 30, 300),
        ('Loopseconds', 'float', 0, 0, 60),
    ], page='Loop')

def sig_input(c):
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read(), vecs=[uP()], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw); sw.par.format = 'rgba16float'
    return sw
# ---- end signal_lib ----
