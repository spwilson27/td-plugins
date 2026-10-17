# ---- retroB helpers (batch-1 -> batch-2 retrofit); needs _helpers.py + _loop.py above ----
PP = "parent().par."
ISPH = "(1 if %sTimesource=='phase' else 0)" % PP
PH01 = "((%sPhase) %% 1.0 if %sTimesource=='phase' else (absTime.seconds/%s) %% 1.0)" % (PP, PP, LOOPLEN)
def CYC(speed):
    """integer cycles per loop for a speed value (phase mode)"""
    return "(0 if %s<=0 else max(1,round(%s)))" % (speed, speed)
def TEXPR(speed='parent().par.Speed'):
    """seconds-like time: absTime*speed in abstime mode; 2pi*phase*cycles in phase mode (periodic)"""
    return "(6.283185307*%sPhase*%s if %sTimesource=='phase' else absTime.seconds*%s)" % (PP, CYC(speed), PP, speed)
def ORBIT(sp='Orbitspeed', off='Orbitangle'):
    """angle: abstime = absTime*speed+offset ; phase = offset + 2pi*phase*integer cycles (rate-matched)"""
    S=PP+sp; O=PP+off
    return "(%s + 6.283185307*%sPhase*(0 if abs(%s)<1e-4 else (1 if %s>0 else -1)*max(1,round(abs(%s)*%s/6.283185))) if %sTimesource=='phase' else absTime.seconds*%s+%s)" % (O,PP,S,S,S,LOOPLEN,PP,S,O)
def look_page(c, accent=True):
    items = [('m','Look','Look','original',{'menu':[('original','Original'),('mono','Mono')]})]
    if accent: items.append(('f','Accent','Accent (red, Mono)',0.0,{'min':0,'max':1}))
    pars(c, {'Look': items})
LOOKI = PP + "Look.menuIndex"
# ---- end retroB helpers ----

def add_loopreset(c, resets, default=False):
    """Loopreset toggle on Loop page + frame-start DAT pulsing reset pulses when loop phase wraps.
    resets: list of (opname, parname) pulse pars to fire."""
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendToggle('Loopreset', label='Reset Stateful Sim At Loop Start')[0]; p.default = default; p.val = default
    k = c.create(td.constantCHOP, 'loopclock'); k.par.name0 = 'ph'; k.par.value0.expr = PH01
    e = c.create(td.executeDAT, 'loopexec')
    e.text = ("RESETS = %r\n"
              "def onFrameStart(frame):\n"
              "    c = parent()\n"
              "    ph = op('loopclock')['ph'].eval()\n"
              "    prev = c.fetch('_lastph', ph)\n"
              "    c.store('_lastph', ph)\n"
              "    if c.par.Loopreset.eval() and ph < prev - 0.5:\n"
              "        for o, n in RESETS:\n"
              "            op(o).par[n].pulse()\n"
              "    return\n" % (list(resets),))
    e.par.framestart = True; e.par.active = True
