c = new_comp(COMP)
add_pars(c, [
    ('Direction', 'menu', [('down', 'Down'), ('up', 'Up'), ('left', 'Left'), ('right', 'Right')], 0),
    ('Threshold', 'float', 0.4, 0, 1),
    ('Animate', 'float', 0.5, 0, 1),
    ('Invert', 'toggle', 0),
    ('Length', 'float', 0.6, 0.02, 2),
    ('Noise', 'float', 0.5, 0, 1),
    ('Streak', 'float', 0.6, 0, 1),
    ('Grain', 'float', 0.4, 0, 1),
    ('Bandwidth', 'float', 3, 1, 64),
    ('Revert', 'float', 0.15, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
loop_pars(c, beats=8)
p = lambda n: 'parent().par.' + n
sw = v2_input(c, COMP)
add_mod(c, 'in2')
DI = 'parent().par.Direction.menuIndex'
mp = glsl(c, 'colmap', rd(COMP, 'map.glsl'), inputs=[sw], fmt='rgba32float', vecs=[
    ('uA', [PEXPR, DI, p('Threshold'), p('Animate')]), ('uB', [p('Noise'), p('Invert'), 0, 0])])
mp.par.outputresolution = 'custom'; mp.par.resolutionw = 2048; mp.par.resolutionh = 1
mp.par.inputextenduv = 'hold'
st = glsl(c, 'stretch', rd(COMP, 'stretch.glsl'), inputs=[sw, mp], res=True, vecs=[
    ('uA', [PEXPR, DI, "%s*(1+%s*%s)" % (p('Length'), p('Modamount'), MOD('band1')), p('Bandwidth')]),
    ('uB', [p('Grain'), 1, p('Revert'), p('Streak')]),
    ('uC', [24, 0, 0, 0])])
st.par.inputextenduv = 'hold'
finish_v2(c, COMP, st, sw)
report(c)
