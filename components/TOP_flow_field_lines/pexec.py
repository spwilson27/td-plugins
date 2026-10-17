def onPulse(par):
    if par.name == 'Reset':
        op('fb_accum').par.resetpulse.pulse()
        op('particles').par.initializepulse.pulse()
