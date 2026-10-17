# ---- retroB helpers for the 'effects' group (lib.py based). Prepend after _lib/lib.py ----
PP = "parent().par."
RL = "(%sLoopbeats*60.0/%sBpm if %sLoopbeats>0 else %sLoopseconds)" % (PP, PP, PP, PP)   # loop length (s)
ISPH = "(1 if %sTimesource=='phase' else 0)" % PP
PH01 = "((%sPhase) %% 1.0 if %sTimesource=='phase' else (absTime.seconds/%s) %% 1.0)" % (PP, PP, RL)
# source clock: seconds in abstime, 2*pi*phase in phase mode
TSRC = "(6.283185307*%sPhase if %sTimesource=='phase' else absTime.seconds)" % (PP, PP)
def look_pg(c):
    add_pars(c, [('Look', 'menu', [('original', 'Original'), ('mono', 'Mono')], 0),
                 ('Accent', 'float', 0.0, 0, 1)], page='Look')
LOOKI = PP + "Look.menuIndex"
def input_stage_rb(c, comp, bg=1.0):
    """like lib.input_stage but with phase-periodic + Mono-capable default source (_lib/rb_src.glsl)"""
    i = c.create(td.inTOP, 'in1')
    code = open(os.path.join(ROOT, 'components', '_lib', 'rb_src.glsl')).read()
    d = glsl(c, 'defsrc', code, vecs=[('uTime', [TSRC, 0, 0, 0]), ('uBg', [bg, 0, 0, 0]), ('uM', [ISPH, LOOKI, PP + 'Accent', 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw
def add_loopreset2(c, reset_par='Reset'):
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendToggle('Loopreset', label='Reset Feedback At Loop Start')[0]; p.default = False; p.val = False
    k = c.create(td.constantCHOP, 'loopclock'); k.par.name0 = 'ph'; k.par.value0.expr = PH01
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    ph = op('loopclock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if c.par.Loopreset.eval() and ph < prev - 0.5:\n"
              "        c.par.%s.pulse()\n"
              "    return\n" % reset_par)
    e.par.framestart = True; e.par.active = True
def CYC(speed):
    return "(0 if %s<=0 else max(1,round(%s)))" % (speed, speed)
def TEXPR(speed):
    """abstime: absTime*speed ; phase: 2pi*phase*integer cycles"""
    return "(6.283185307*%sPhase*%s if %sTimesource=='phase' else absTime.seconds*%s)" % (PP, CYC(speed), PP, speed)
def add_loop(c):
    pg = c.appendCustomPage('Loop')
    p = pg.appendMenu('Timesource')[0]; p.menuNames = ['abstime', 'phase']; p.menuLabels = ['Absolute time', 'Phase (loop)']
    p.default = 'abstime'; p.val = 'abstime'
    p = pg.appendFloat('Phase')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1
    p = pg.appendFloat('Loopseconds')[0]; p.default = 8; p.val = 8; p.min = 0.1; p.max = 120; p.normMin = 0.1; p.normMax = 60; p.clampMin = True
    p = pg.appendInt('Loopbeats')[0]; p.default = 0; p.val = 0; p.min = 0; p.max = 128; p.normMin = 0; p.normMax = 32; p.clampMin = True
    p = pg.appendFloat('Bpm')[0]; p.default = 120; p.val = 120; p.min = 20; p.max = 300; p.normMin = 20; p.normMax = 300
