exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def inst(ex, name):
    # keep the parameter values set in this snippet when the external tox reloads
    c = instance(ex, name)
    c.par.reloadcustom = False; c.par.reloadbuiltin = False
    return c

def beat_mod(ex, bpm=120):
    """Beat CHOP -> Rename to the library's modulation channels: beat (pulse), band1 (smooth 0..1 wave)."""
    bt = ex.create(td.beatCHOP, 'beat', col=0, row=1); bt.par.pulse = True; bt.par.sine = True; bt.par.ramp = False; bt.par.bpm = bpm
    rn = ex.create(td.renameCHOP, 'modnames', col=1, row=1); rn.inputConnectors[0].connect(bt)
    rn.par.renamefrom = 'pulse sine'; rn.par.renameto = 'beat band1'
    return rn

def preset(l, name, **kw):
    """Select an L-system preset right now (the Parameter Execute DAT only fires a frame after a change), then override;
    the segment Script DAT re-cooks by itself."""
    m = l.op('lsys_expand').module
    l.par.Preset = name
    m.apply_preset(l, name)
    for k, v in kw.items(): setattr(l.par, k, v)

def line_mat(ex, width=1.0):
    """Line MAT: draws POP lines with the LineWidth / Color attributes the component writes."""
    m = ex.create(td.lineMAT, 'linemat', row=2)
    m.par.widthnear = width; m.par.widthfar = width
    for k in ('linenear', 'linefar'):
        for ch in 'rgb': getattr(m.par, k + 'color' + ch).val = 1
    return m

def lines_out(ex, n, l, dist=14.0, height=3.0, width=1.0):
    r = render_pop(ex, l.op('out1'), cam_dist=dist, cam_height=height, material=line_mat(ex, width), res=(960, 540))
    out(ex, n, r)
    return r

s = begin('GEN_lsystem')

ex = example(s, 1, 'A forest on a sphere',
  'A Sphere POP is the planting input: one tree grows from every (thinned) point, tilted along the\n'
  'surface normal (Align To Normal). out1 is plain line geometry, rendered here with a Line MAT.\n'
  'Try: Max Trees, Tree Size, Variation (random spin and size), Preset (tree, bush) and Seed.')
sp = ex.create(td.spherePOP, 'sphere'); sp.par.radx = sp.par.rady = sp.par.radz = 3.0
l = inst(ex, 'GEN_lsystem')
preset(l, 'tree', Iterations=6); l.par.Align = True; l.par.Maxtrees = 50; l.par.Treesize = 1.4
l.par.Animate = False; l.par.Growth = 1; l.par.Linewidth = 1.5; l.par.Taper = 0.75
l.inputConnectors[0].connect(sp)
lines_out(ex, 1, l, dist=12.0, height=8.0)

ex = example(s, 2, 'Orchard rows from a Grid POP',
  'Grid POP points are the planting positions; Max Trees caps the count and Seed re-rolls spin and\n'
  'size. Mono look = bone-white trees on black (Accent adds red tips). Growth is set by hand here.\n'
  'Try: Animate on to watch every tree grow, Angle and Branch Length Scale on the Lsystem page.')
gd = ex.create(td.gridPOP, 'grid'); gd.par.surftype = 'points'; gd.par.cols = 5; gd.par.rows = 4
gd.par.sizex = 9; gd.par.sizey = 6; gd.par.rx = -90
l = inst(ex, 'GEN_lsystem')
preset(l, 'plant', Iterations=4); l.par.Maxtrees = 40; l.par.Treesize = 1.8; l.par.Look = 'mono'; l.par.Accent = 1
l.par.Animate = False; l.par.Growth = 1; l.par.Linewidth = 1.6; l.par.Seed = 4
l.inputConnectors[0].connect(gd)
lines_out(ex, 2, l, dist=11.0, height=5.0)

ex = example(s, 3, 'Beat-driven bush',
  'No input connected: the built-in demo plants a single tree at the origin. A Beat CHOP drives the\n'
  'modulation input: band1 thickens the lines and each beat flashes the growing tips.\n'
  'Try: Preset = bush or dragon, Iterations (one more doubles the branches), Animate Growth.')
l = inst(ex, 'GEN_lsystem')
preset(l, 'bush', Iterations=4); l.par.Treesize = 2.0; l.par.Linewidth = 2.0; l.par.Look = 'mono'; l.par.Animate = False; l.par.Growth = 1
rn = beat_mod(ex)
l.inputConnectors[1].connect(rn)
r = lines_out(ex, 3, l, dist=5.0, height=1.0, width=1.0)
cam = r.par.camera.eval(); cam.par.ty = 0.9; cam.par.rx = 0   # frame the tree: root low, crown centred
finish(s)
