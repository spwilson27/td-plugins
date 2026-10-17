def onPulse(par):
    if par.name == 'Reset':
        for n in ('fb_state', 'fb_accum'):
            op(n).par.resetpulse.pulse()
