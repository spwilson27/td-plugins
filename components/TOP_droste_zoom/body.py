c = new_comp(COMP)
add_pars(c, [
    ('Speed', 'float', 1.0, 0, 8),
    ('Innerscale', 'float', 0.33, 0.05, 0.9),
    ('Zoomperiods', 'int', 1, -8, 8),
    ('Rotation', 'float', 0.0, -2, 2),
    ('Spin', 'int', 0, -4, 4),
    ('Fill', 'float', 1.0, 0.4, 1.6),
    ('Center', 'xy', (0, 0)),
    ('Seam', 'float', 0.5, 0, 1),
    ('Original', 'float', 0.0, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
loop_pars(c, beats=0, seconds=8)
# unwrapped loop phase: 1.0 == one loop (Speed scales abs time); phase mode reads Phase / Clock
PH = "(%s if parent().par.Timesource=='phase' else absTime.seconds*parent().par.Speed/%s)" % (EXTPH, LENEXPR)
res_chop(c)
i1 = c.create(td.inTOP, 'in1')
d = glsl(c, 'defsrc', rd(COMP, 'src.glsl'), vecs=[('uT', [PH, 0, 0, 0])], res=True)
src = c.create(td.switchTOP, 'src')
src.inputConnectors[0].connect(d); src.inputConnectors[1].connect(i1)
src.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
setres(src); src.par.format = 'rgba16float'
add_mod(c, 'in2')
p = lambda n: 'parent().par.' + n
g = glsl(c, 'droste', rd(COMP, 'droste.glsl'), inputs=[src], res=True, vecs=[
    ('uA', [PH, p('Zoomperiods'), p('Rotation'), p('Spin')]),
    ('uB', ["min(0.9,%s+%s*%s*0.3)" % (p('Innerscale'), p('Modamount'), MOD('band1')), p('Fill'), p('Centerx'), p('Centery')]),
    ('uC', [p('Original'), p('Seam'), 0, 0]),
])
g.par.inputextenduv = 'mirror'
finish_v2(c, COMP, g, src)
report(c)
