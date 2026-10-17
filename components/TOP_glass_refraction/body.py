c = new_comp(COMP)
add_pars(c, [
    ('Shape', 'menu', [('morph', 'Morph blob/cube'), ('torus', 'Torus'), ('cube', 'Rounded cube')], 0),
    ('Ior', 'float', 1.45, 1.0, 2.4),
    ('Dispersion', 'float', 0.12, 0, 0.5),
    ('Frost', 'float', 0.0, 0, 1),
    ('Size', 'float', 1.0, 0.3, 2),
    ('Morphspeed', 'int', 1, 0, 6),
    ('Spin', 'int', 1, 0, 4),
    ('Highlights', 'float', 1.0, 0, 3),
    ('Absorption', 'float', 0.6, 0, 3),
    ('Camdistance', 'float', 4.0, 2, 10),
    ('Bgscale', 'float', 1.0, 0.3, 3),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
loop_pars(c, beats=8)
p = lambda n: 'parent().par.' + n
sw = v2_input(c, COMP)
add_mod(c, 'in2')
g = glsl(c, 'glass', rd(COMP, 'glass.glsl'), inputs=[sw], res=True, vecs=[
    ('uA', [PEXPR, "%s+%s*%s*0.5" % (p('Ior'), p('Modamount'), MOD('band1')), p('Dispersion'), p('Frost')]),
    ('uB', [p('Size'), 'parent().par.Shape.menuIndex', p('Morphspeed'), p('Spin')]),
    ('uC', [p('Highlights'), p('Camdistance'), p('Bgscale'), p('Absorption')]),
])
g.par.inputextenduv = 'mirror'
finish_v2(c, COMP, g, sw)
report(c)
