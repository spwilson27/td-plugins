# Shared snippet helpers. Each snippets/src/<NAME>.py starts with:
#   exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
# then:
#   s = begin('TOP_glitch')
#   ex = example(s, 1, 'Glitch a movie', 'Movie File In -> TOP_glitch -> example1.\nRaise Amount for more ...')
#   src = ex.create(moviefileinTOP, 'banana'); src.par.file = sample('Map/Banana.tif')
#   g = instance(ex, 'TOP_glitch'); g.inputConnectors[0].connect(src)   # wire, set params
#   out(ex, 1, g)                                                       # Null TOP 'example1' + viewer
#   finish(s)
#
# Layout: examples are stacked left-to-right, each inside its own Annotate box (title + explanation),
# exactly like Derivative's OP Snippets. Components are referenced via externaltox so snippets always
# use the current library version.
import os, td, math

LIB = os.path.expanduser('~/software/td-plugins')
LIBEXPR = "__import__('os').environ.get('TD_PLUGINS_HOME') or __import__('os').path.expanduser('~/software/td-plugins')"
EX_W, EX_H, GAP = 1100, 700, 200


def sample(rel):
    """Path to a file in TouchDesigner's Samples folder, as an expression-safe absolute path."""
    return os.path.join(app.samplesFolder, rel)


def sample_expr(rel):
    """Expression that resolves a Samples file on any machine (use for par.file.expr)."""
    return "app.samplesFolder + '/%s'" % rel


def begin(name):
    h = op('/snipbuild') or op('/').create(td.baseCOMP, 'snipbuild')
    old = h.op(name + '_snippet')
    if old: old.destroy()
    s = h.create(td.baseCOMP, name + '_snippet')
    s.comment = 'Operator snippets for %s (td-plugins). Each Annotate box is one self-contained example.' % name
    s.store('examples', 0)
    return s


def example(s, n, title, body):
    """Create example n: a baseCOMP-free area marked by an Annotate COMP. Returns the snippet COMP
    (examples share one network, so ops are placed with place())."""
    a = s.create(td.annotateCOMP, 'annotate%d' % n)
    a.par.Titletext = '%d. %s' % (n, title)
    a.par.Bodytext = body
    a.par.Bodyfontsize = 9
    a.nodeX = (n - 1) * (EX_W + GAP) - 60
    a.nodeY = -EX_H + 220   # Annotate nodeY is the bottom edge; rows of ops sit at y=0,-160,-320...
    a.nodeWidth = EX_W
    a.nodeHeight = EX_H
    s.store('examples', max(n, s.fetch('examples', 0)))
    s.store('ex%d_next' % n, 0)
    return Example(s, n)


class Example:
    """Thin wrapper so ops created through it are auto-placed inside the example's Annotate box."""
    def __init__(self, s, n):
        self.s, self.n, self.col = s, n, 0

    def create(self, optype, name, col=None, row=0):
        o = self.s.create(optype, 'ex%d_%s' % (self.n, name))
        c = self.col if col is None else col
        o.nodeX = (self.n - 1) * (EX_W + GAP) + c * 220
        o.nodeY = -row * 160 - 0
        if col is None:
            self.col += 1
        return o


def instance(ex, name, col=None, row=0):
    """Instance of a library component, referenced via externaltox (always current)."""
    fam = name.split('_')[0]
    c = ex.create(td.baseCOMP, name, col=col, row=row)
    c.par.externaltox.expr = LIBEXPR + " + '/tox/%s/%s.tox'" % (fam, name)
    c.par.enableexternaltox = True
    # keep parameter values set in the snippet when the external tox reloads
    for pn in ('reloadcustom', 'reloadbuiltin'):
        if hasattr(c.par, pn): setattr(c.par, pn, False)
    c.par.reinitnet.pulse()
    c.viewer = True
    return c


def out(ex, n, src, col=None):
    """Final Null TOP named exampleN (what validate_snippet captures), viewer on."""
    o = ex.create(td.nullTOP, 'x', col=col)
    o.name = 'example%d' % n
    connect(src, o)
    o.viewer = True
    return o


def connect(src, dst, out_index=0, in_index=0):
    """Wire src -> dst. src may be a component instance (uses its Nth output connector)."""
    if src.isCOMP and src.family == 'COMP':
        oc = src.outputConnectors
        assert len(oc) > out_index, 'component %s has no output %d (was the externaltox loaded?)' % (src.path, out_index + 1)
        dst.inputConnectors[in_index].connect(oc[out_index])
    else:
        dst.inputConnectors[in_index].connect(src)


def finish(s):
    # lay out each example inside its Annotate box with no overlaps (td-organize), boxes resized to fit
    # group by name, not by where nodes happen to sit: move each example's ops inside its Annotate box first
    for n in range(1, s.fetch('examples', 0) + 1):
        box = s.op('annotate%d' % n)
        if box is None:
            continue
        members = [o for o in s.children if (o.name.startswith('ex%d_' % n) or o.name == 'example%d' % n) and o is not box]
        for i, o in enumerate(members):
            o.nodeX = box.nodeX + 40 + (i % 6) * 160
            o.nodeY = box.nodeY + 40 + (i // 6) * 120
    ns = {}
    exec(open(__import__('os').path.join(__import__('os').path.expanduser(__import__('os').environ.get('TD_PLUGINS_HOME', '~/software/td-plugins')), 'td_organize', 'td_runtime.py')).read(), ns)
    ns['organize'](s, recursive=True, annotate_groups=True)
    name = s.name[:-len('_snippet')]
    path = os.path.join(LIB, 'snippets', name + '.tox')
    s.save(path)
    print('saved', path, 'examples:', s.fetch('examples', 0))


def apply_material(inst, *targets):
    """Show the MAT_ 'Apply To' workflow: list Geometry COMPs / Render TOPs in the material component's
    Applyto field (exactly what dragging them onto the field does). The component's own callback assigns
    <inst>/mat to them; we also run it now because callbacks don't fire in the frame the snippet is built."""
    inst.par.Applyto = ' '.join(t.name for t in targets)
    cb = inst.op('applyto_callbacks')
    if cb is not None:
        cb.module.apply(inst)
    else:  # externaltox not loaded yet: assign directly (same result)
        for t in targets:
            if t.OPType == 'renderTOP':
                t.par.overridemat = inst.op('mat')
            else:
                t.par.material = inst.op('mat')


def render_pop(ex, pop, cam_dist=14.0, cam_height=3.0, material=None, res=(960, 540), col=None, row=0):
    """Minimal render rig for a POP output: Geometry COMP (Select POP of `pop`) + Camera + Light + Render TOP.
    Returns the Render TOP. `pop` is an op (e.g. inst.op('out2')) — referenced, not copied."""
    g = ex.create(td.geometryCOMP, 'geo', col=col, row=row)
    for o in list(g.children): o.destroy()
    sel = g.create(td.selectPOP, 'select'); sel.par.pop = pop
    sel.display = True; sel.render = True
    if material is not None:
        g.par.material = material
    cam = ex.create(td.cameraCOMP, 'cam', row=row + 1)
    cam.par.tz = cam_dist; cam.par.ty = cam_height
    cam.par.rx = -math.degrees(math.atan2(cam_height, cam_dist))
    lt = ex.create(td.lightCOMP, 'light', row=row + 1)
    lt.par.tx = 8; lt.par.ty = 14; lt.par.tz = 10
    r = ex.create(td.renderTOP, 'render', row=row)
    r.par.camera = cam; r.par.geometry = g; r.par.lights = lt
    r.par.outputresolution = 'custom'; r.par.resolutionw, r.par.resolutionh = res
    r.par.bgcolorr = r.par.bgcolorg = r.par.bgcolorb = 0.01; r.par.bgcolora = 1
    return r
