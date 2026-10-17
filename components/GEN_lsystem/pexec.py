def onValueChange(par, prev):
    # selecting a preset overwrites the Lsystem page; the segment table (Script DAT) then re-cooks by itself
    c = parent()
    if par.name == 'Preset' and str(par.eval()) != 'custom':
        op('lsys_expand').module.apply_preset(c, str(par.eval()))

def onPulse(par):
    op('segs').cook(force=True)
