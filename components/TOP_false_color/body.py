c = new_comp(COMP)
add_pars(c, [
    ('Map', 'menu', [('thermal', 'Thermal'), ('xray', 'X-Ray'), ('night', 'Night Vision'), ('custom', 'Custom Gradient')], 0),
    ('Driver', 'menu', [('luma', 'Luminance'), ('in2', 'In2 (depth)')], 0),
    ('Gain', 'float', 1.3, 0, 4),
    ('Bias', 'float', 0.0, -1, 1),
    ('Invert', 'toggle', 0),
    ('Edges', 'float', 0.4, 0, 1),
    ('Edgecolor', 'rgb', (0.93, 0.91, 0.85)),
    ('Noise', 'float', 0.3, 0, 1),
    ('Isotherms', 'float', 0.0, 0, 1),
    ('Mixoriginal', 'float', 0.0, 0, 1),
    ('Modamount', 'float', 0.5, 0, 2),
    ('Crosshair', 'toggle', 1),
    ('Legend', 'toggle', 1),
    ('Target', 'xy', (0.5, 0.5)),
    ('Hudcolor', 'rgb', (0.93, 0.91, 0.85)),
    ('Colora', 'rgb', (0.0, 0.0, 0.0)),
    ('Colorb', 'rgb', (0.9, 0.05, 0.05)),
    ('Colorc', 'rgb', (0.93, 0.91, 0.85)),
    *COMMON,
])
loop_pars(c, beats=8)
src = v2_input(c, None)
in2 = c.create(td.inTOP, 'in2')
add_mod(c, 'in3')
drv = c.create(td.switchTOP, 'driver')
drv.inputConnectors[0].connect(src); drv.inputConnectors[1].connect(in2)
drv.par.index.expr = "1 if (parent().par.Driver=='in2' and len(parent().inputConnectors)>1 and parent().inputConnectors[1].connections) else 0"
setres(drv); drv.par.format = 'rgba16float'
p = lambda n: 'parent().par.' + n
g = glsl(c, 'falsecolor', rd(COMP, 'fc.glsl'), inputs=[src, drv], res=True, vecs=[
    uP(),
    ('uA', [p('Map') + '.menuIndex', "%s+%s*%s" % (p('Gain'), p('Modamount'), MOD('band1')), p('Bias'), p('Invert')]),
    ('uB', [p('Edges'), p('Noise'), p('Isotherms'), p('Mixoriginal')]),
    ('uC', [p('Crosshair'), p('Legend'), p('Targetx'), p('Targety')]),
    ('uD', [p('Hudcolorr'), p('Hudcolorg'), p('Hudcolorb'), 1]),
    ('uE', [p('Edgecolorr'), p('Edgecolorg'), p('Edgecolorb'), 1]),
    ('uF', [p('Coloraa') if False else p('Colorar'), p('Colorag'), p('Colorab'), 1]),
    ('uG', [p('Colorbr'), p('Colorbg'), p('Colorbb'), 1]),
    ('uH', [p('Colorcr'), p('Colorcg'), p('Colorcb'), 1]),
])
finish_v2(c, COMP, g, src)
report(c)
