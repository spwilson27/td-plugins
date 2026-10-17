# ---- SDF_ shared build helpers: components/_sdf/helpers.py, exec'd by every SDF_ build.py (the built tox is self-contained) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

SHARED = ('sdflib.py', 'lib.glsl', 'preview.glsl')   # one copy for every SDF_ component, in components/_sdf/

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', '_sdf' if fn in SHARED else comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, nm, text, kind=None):
    d = c.create(kind or td.textDAT, nm); d.text = text; return d

def pars(c, spec):
    """spec: {page: [(kind, name, label, default, opts)]}; kind f,i,t,m,p,rgb,wh,xy,xyz,s,comp.
    opts: min, max, clamp, menu=[(id,label)], norm=(a,b)"""
    for page, items in spec.items():
        pg = c.appendCustomPage(page)
        for it in items:
            kind, nm, lab, dflt = it[:4]; o = it[4] if len(it) > 4 else {}
            ap = dict(f=pg.appendFloat, i=pg.appendInt, t=pg.appendToggle, p=pg.appendPulse, s=pg.appendStr, m=pg.appendMenu,
                      rgb=pg.appendRGB, wh=pg.appendWH, xy=pg.appendXY, xyz=pg.appendXYZ, comp=pg.appendCOMP)[kind]
            ps = ap(nm, label=lab)
            if kind == 'm':
                ps[0].menuNames = [m[0] for m in o['menu']]; ps[0].menuLabels = [m[1] for m in o['menu']]
            vals = dflt if isinstance(dflt, (list, tuple)) else [dflt]
            for p, v in zip(ps, vals):
                if kind == 'comp': continue
                p.default = v; p.val = v
                if 'min' in o:
                    p.min = o['min']; p.normMin = o.get('norm', (o['min'], o.get('max')))[0]; p.clampMin = o.get('clamp', False)
                if 'max' in o:
                    p.max = o['max']; p.normMax = o.get('norm', (o.get('min'), o['max']))[1]; p.clampMax = o.get('clamp', False)
    return c

def color_par(default=(0.8, 0.8, 0.8), page='Look'):
    return {page: [('rgb', 'Color', 'Color', list(default), {'min': 0, 'max': 1})]}

def vecs(g, items):
    """items: list of (name, [4 values or expression strings]) -> vec uniforms of a GLSL TOP/MAT"""
    g.seq.vec.numBlocks = len(items)
    for i, (nm, vs) in enumerate(items):
        g.par['vec%dname' % i] = nm
        for ax, v in zip('xyzw', vs):
            p = g.par['vec%d value%s' % (i, ax)] if False else g.par['vec%dvalue%s' % (i, ax)]
            if isinstance(v, str): p.expr = v
            else: p.val = v

def set_array(g, chop, tb=False):
    g.seq.array.numBlocks = 1
    g.par.array0name = 'uSdf'; g.par.array0type = 'vec4'; g.par.array0chop = chop
    if tb: g.par.array0arraytype = 'texturebuffer'

def lib_dat(c):
    return mkdat(c, 'sdflib', rd(c.name, 'sdflib.py'))

def scene_feed(c, pfx, src, template, tb=False, kind='top', base=(0, 0)):
    """Consumer plumbing for an SDF wire: Script DAT <pfx>shader (template with the assembled scene; only
    rewritten when the structure changes) and the uniform-array CHOP <pfx>vals (values, per frame).
    `src` is any DAT carrying the payload (In DAT or the node's own `sdf`). Also the table <pfx>tex of the
    wire's @tex records: call bind_tex(glsl_op, c, pfx, kind) after creating the consumer GLSL TOP/MAT (kind 'top'|'mat';
    base = wired 2D/3D inputs of a TOP, which come before the extra textures)."""
    t = mkdat(c, pfx + 'template', template)
    cb = mkdat(c, pfx + 'shader_cb', "def onCook(dat):\n    op('sdflib').module.write_shader(dat, op('%s').text, op('%stemplate').text, %r, %r, %r)\n" % (src.name, pfx, tb, kind, tuple(base)))
    sh = c.create(td.scriptDAT, pfx + 'shader'); sh.par.callbacks = cb
    sh.inputConnectors[0].connect(src)
    xcb = mkdat(c, pfx + 'tex_cb', "def onCook(dat):\n    op('sdflib').module.write_tex(dat, op('%s').text)\n" % src.name)
    xt = c.create(td.scriptDAT, pfx + 'tex'); xt.par.callbacks = xcb
    xt.inputConnectors[0].connect(src)
    vcb = mkdat(c, pfx + 'vals_cb', "def onCook(dat):\n    op('sdflib').module.write_vals(dat, op('%s').text)\n" % src.name)
    vt = c.create(td.scriptDAT, pfx + 'vals_tbl'); vt.par.callbacks = vcb
    vt.inputConnectors[0].connect(src)
    vc = c.create(td.dattoCHOP, pfx + 'vals'); vc.par.dat = vt
    vc.par.firstrow = 'values'; vc.par.firstcolumn = 'values'; vc.par.output = 'chanpercol'
    return sh, vc

def bind_tex(g, c, pfx, kind='top'):
    """Bind the wire's @tex records (table <pfx>tex) on the consumer GLSL TOP / MAT `g`: 2d/3d TOPs through `tops` (TOP)
    or sampler blocks (MAT), POP attributes through buffer blocks (GLSL: TDBuffer_<name>(i)). Unused slots point at
    placeholders (`nobuf` POP, `notex` TOP). All by expression, so a texture/buffer change never needs a write."""
    nb = c.create(td.pointgeneratorPOP, 'nobuf'); nb.par.numpoints = 1
    nt = c.create(td.constantTOP, 'notex'); nt.par.outputresolution = 'custom'; nt.par.resolutionw = 4; nt.par.resolutionh = 4
    if kind != 'mat':       # 3D placeholder for the unused 3D slots of `tops` (GLSL TOP consumers)
        n3 = c.create(td.glslTOP, 'notex3'); n3.par.type = 'texture3d'; n3.par.outputresolution = 'custom'
        n3.par.resolutionw = 4; n3.par.resolutionh = 4; n3.par.depth = 'custom'; n3.par.customdepth = 4; n3.par.format = 'rgba8fixed'
    T = "op('sdflib').module.tex_par(op('%stex'), %%r, %%d, %%r)" % pfx
    g.seq.buffer.numBlocks = 6
    for i in range(6):
        for par, f in (('pop', 'path'), ('attrclass', 'cls'), ('attr', 'attr'), ('name', 'name')):
            g.par['buffer%d%s' % (i, par)].expr = T % ('buffer', i, f)
    if kind == 'mat':
        g.seq.sampler.numBlocks = 3
        for i in range(3):
            for par, f in (('top', 'path'), ('name', 'name')):
                g.par['sampler%d%s' % (i, par)].expr = T % ('sampler', i, f)
            g.par['sampler%dfilter' % i] = 'linear'
            for ax in 'uvw': g.par['sampler%dextend%s' % (i, ax)] = 'hold'
    else:
        g.par.tops.expr = "op('sdflib').module.tex_par(op('%stex'), 'tops')" % pfx

def node(c, kind, code, vals_py, nin=0, defaults='AB', tex_py=None):
    """The SDF node itself: In DATs, Script DAT `sdf` (writes the payload), Out DAT out1.
    tex_py (optional): Python lines that set `tex` = list of dicts(name, type, path, attr, cls) for the wire's @tex records."""
    lib_dat(c)
    ins = []
    for i in range(nin):
        d = c.create(td.inDAT, 'in%d' % (i + 1)); ins.append(d)
    mkdat(c, 'code', code)
    body = ("def onCook(dat):\n    import math\n    p = parent().par\n"
            + ''.join('    ' + ln + '\n' for ln in vals_py.strip('\n').split('\n'))
            + ('' if not tex_py else ''.join('    ' + ln + '\n' for ln in tex_py.strip('\n').split('\n')))
            + "    op('sdflib').module.write_node(dat, parent(), %r, [%s], op('code').text, vals, %r, %s)\n"
            % (kind, ', '.join("op('in%d')" % (i + 1) for i in range(nin)), defaults, 'tex' if tex_py else 'None'))
    cb = mkdat(c, 'sdf_cb', body)
    sd = c.create(td.scriptDAT, 'sdf'); sd.par.callbacks = cb
    for i, d in enumerate(ins): sd.inputConnectors[i].connect(d)
    o = c.create(td.outDAT, 'out1'); o.inputConnectors[0].connect(sd)
    return sd

def preview(c, src='sdf', w=400, h=300, scale=0):
    """Internal `preview` TOP: small orbiting raymarch of the node's own SDF (shown in the node viewer)."""
    tmpl = rd(c.name, 'preview.glsl').replace('//@@LIB@@', rd(c.name, 'lib.glsl'))
    sh, vc = scene_feed(c, 'pv_', c.op(src), tmpl)
    g = c.create(td.glslTOP, 'preview'); g.par.pixeldat = sh
    bind_tex(g, c, 'pv_')
    g.par.outputresolution = 'custom'; g.par.resolutionw = w; g.par.resolutionh = h
    g.par.format = 'rgba8fixed'
    set_array(g, vc)
    vecs(g, [('uPv', ['absTime.seconds', scale, 0, 0])])
    return g

def finish(c, name):
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True); c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
