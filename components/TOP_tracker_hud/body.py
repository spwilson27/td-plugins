P = lambda n: 'parent().par.' + n
c = new_comp(COMP)
add_pars(c, [
    ('Points', 'int', 28, 1, 64),
    ('Labelmode', 'menu', [('id', 'ID'), ('coords', 'Coords'), ('both', 'Both')], 0),
    ('Labelcolor', 'menu', [('red', 'Red'), ('white', 'White')], 0),
    ('Fontsize', 'int', 14, 7, 42),
    ('Boxsize', 'float', 16, 4, 64),
    ('Linecount', 'int', 10, 0, 64),
    ('Gridsize', 'float', 80, 16, 400),
    ('Threshold', 'float', 0.35, 0, 1),
    ('Refresh', 'int', 4, 0, 64),
    ('Jitter', 'float', 0.5, 0, 3),
    ('Dim', 'float', 0.8, 0, 1.5),
    ('Scanlines', 'float', 0.5, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
loop_pars(c, beats=0, seconds=8)
sw = v2_input(c, COMP)
add_mod(c, 'in2')
pa = glsl(c, 'points', rd(COMP, 'pts.glsl'), inputs=[sw], fmt='rgba32float', vecs=[
    ('uA', [PEXPR, P('Points'), P('Threshold'), P('Refresh')]), ('uB', ["%s+%s*%s*2" % (P('Jitter'), P('Modamount'), MOD('band1')), 0, 0, 0])])
pa.par.outputresolution = 'custom'; pa.par.resolutionw = 64; pa.par.resolutionh = 1
pa.par.inputextenduv = 'hold'
hu = glsl(c, 'hud', rd(COMP, 'hud.glsl'), inputs=[sw, pa], res=True, vecs=[
    ('uA', [PEXPR, P('Points'), 'parent().par.Labelmode.menuIndex', P('Fontsize')]),
    ('uB', [P('Linecount'), P('Gridsize'), 1.0, P('Scanlines')]),
    ('uC', ["%s*(1+%s*%s)" % (P('Boxsize'), P('Modamount'), MOD('band2')), 'parent().par.Labelcolor.menuIndex', 0.55, 1.0]),
    ('uD', [P('Dim'), 0, 0, 0])])
hu.par.inputextenduv = 'hold'
finish_v2(c, COMP, hu, sw)
report(c)
