c = new_comp(COMP)
MAXP = 16
add_pars(c, [
    ('Direction', 'menu', [('right', 'Right'), ('left', 'Left'), ('up', 'Up'), ('down', 'Down')], 0),
    ('Key', 'menu', [('luma', 'Luminance'), ('hue', 'Hue'), ('sat', 'Saturation'), ('red', 'Red')], 0),
    ('Thresholdlow', 'float', 0.15, 0, 1),
    ('Thresholdhigh', 'float', 0.9, 0, 1),
    ('Passes', 'int', 8, 0, MAXP),
    ('Sortamount', 'float', 1.0, 0, 1),
    ('Refresh', 'float', 0.02, 0, 1),
    ('Bytebeat', 'float', 0.25, 0, 1),
    ('Bandsize', 'float', 1.0, 0.2, 4),
    ('Bandholdframes', 'int', 3, 1, 30),
    ('Shuffle', 'float', 0.3, 0, 1),
    ('Seed', 'float', 1, 0, 100),
    ('Loopfade', 'toggle', 1),
    ('Active', 'toggle', 1),
    ('Reset', 'pulse'),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
loop_pars(c, beats=8)
src = v2_input(c, COMP)
add_mod(c, 'in2')
p = lambda n: 'parent().par.' + n
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(src)
fb.par.format = 'rgba16float'; setres(fb); fb.par.reset.expr = p('Reset')
sortcode = rd(COMP, 'sort.glsl')
prev = fb
hard = "1 if (%s and %s<1.5/%s) else 0" % (p('Loopfade'), PEXPR, FREXPR)
for i in range(MAXP):
    g = glsl(c, 'sort%d' % i, sortcode, inputs=[prev, src], res=True, fmt='rgba16float', vecs=[
        uP(),
        ('uS', [p('Direction') + '.menuIndex', p('Thresholdlow'), p('Thresholdhigh'), p('Key') + '.menuIndex']),
        ('uT', ['1 if (%s and %d < %s) else 0' % (p('Active'), i, p('Passes')), i, 'absFrame' if False else 'absTime.frame', p('Refresh')]),
        ('uU', [hard, 1 if i == 0 else 0, 0, 0]),
    ])
    prev = g
nul = c.create(td.nullTOP, 'state'); nul.inputConnectors[0].connect(prev)
fb.par.top = nul
cor = glsl(c, 'corrupt', rd(COMP, 'corrupt.glsl'), inputs=[nul, src], res=True, vecs=[
    uP(),
    ('uA', [p('Sortamount'), 'min(1,%s+%s*%s)' % (p('Bytebeat'), p('Modamount'), MOD('band1')), p('Shuffle'), p('Loopfade')]),
    ('uB', [0.5, p('Bandsize'), p('Seed'), p('Bandholdframes')]),
])
finish_v2(c, COMP, cor, src)
report(c)
