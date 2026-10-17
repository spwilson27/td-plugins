# ---- shared helpers (pasted at top of each build.py by components/_lib/mk.sh) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')

def rd(comp, fn):
    return open(os.path.join(ROOT, 'components', comp, fn)).read()

def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)

def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

def setres(o, w=None, h=None):
    pre = "op('../res')" if o.parent().name == 'demo' else "op('res')"
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w or pre + "['w']"; o.par.resolutionh.expr = h or pre + "['h']"

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=False, filt=None):
    """vecs: list of (uniformName, [4 values/exprs]) ; exprs are strings evaluated in TD."""
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]):
        g.inputConnectors[i].connect(s)
    if len(inputs) > 3:   # inputs beyond the 3 wire connectors go through the TOPs parameter (index 3..)
        g.par.tops = ' '.join(s.name for s in inputs[3:])
    if vecs:
        g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    if filt: g.par.filtertype = filt
    return g

def add_pars(c, specs, page='Controls'):
    """spec tuples: (name, kind, ...)
      ('Amount','float',default,min,max)   ('Count','int',def,min,max)  ('On','toggle',def)
      ('Reset','pulse')  ('Mode','menu',[(id,label),..],default_index)  ('Res','wh',(w,h))
      ('Col','rgb',(r,g,b))  ('Txt','str',default)  ('Xy','xy',(x,y))"""
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]
            p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse':
            pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]
            p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            ps = pg.appendWH(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'xy':
            ps = pg.appendXY(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.normMin = -1; q.normMax = 1
        elif k == 'rgb':
            ps = pg.appendRGB(n)
            for q, v in zip(ps, s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def input_stage(c, comp, bg=1.0):
    """in1 + animated default source -> switch 'src' (resolution = Resolution par). Returns src TOP."""
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', rd(comp, 'src.glsl'), vecs=[('uTime', ['absTime.seconds', 0, 0, 0]), ('uBg', [bg, 0, 0, 0])], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw)
    sw.par.format = 'rgba16float'
    return sw

def finish_old(c, name):
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ======================= v2 additions (td-plugins CONVENTIONS v2) =======================
P_ = 'parent().par.'
# Standard Controls entries every TOP_ effect has. Append `*COMMON` to your Controls spec list
# (do NOT add your own Resolution / Mix / Bypass).
COMMON = [
    ('Mix', 'float', 1.0, 0, 1, True),
    ('Bypass', 'toggle', 0),
    ('Resolutionmode', 'menu', [('input', 'Follow Input'), ('custom', 'Custom')], 0),
    ('Resolution', 'wh', (1280, 720)),
]

# --- animation: absTime only (makes the preview example move; there is no Loop page) ---
PEXPR = "((absTime.seconds/8.0) % 1.0)"     # 0..1 over 8 s
LENEXPR = "8"
FREXPR = "240"
def uP(extra=0):
    return ('uP', [PEXPR, 8, 240, extra])

# --- resolution: Resolutionmode 'input' follows in1 (or Resolutionw/h when unconnected), 'custom' uses Resolutionw/h ---
def res_chop(c):
    k = c.create(td.constantCHOP, 'res')
    conn = "parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections and op('in1').width>0"
    k.par.name0 = 'w'; k.par.value0.expr = "(op('in1').width if (%s) else parent().par.Resolutionw)" % conn
    k.par.name1 = 'h'; k.par.value1.expr = "(op('in1').height if (%s) else parent().par.Resolutionh)" % conn
    return k

def new_demo(c):
    """Base COMP 'demo': holds every preview-only source. Not selected (so not cooking) when in1 is connected."""
    return c.create(td.baseCOMP, 'demo')

def demo_out(d, top, name='demo_out'):
    o = d.create(td.outTOP, name); o.inputConnectors[0].connect(top); return o

HASIN = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"

def v2_input(c, comp=None, srcfile='src.glsl', extra_vecs=()):
    """in1 (In TOP) + demo COMP (animated default source) -> Switch 'src' sized by 'res'."""
    res_chop(c)
    i = c.create(td.inTOP, 'in1')
    d = new_demo(c)
    code = (rd(comp, srcfile) if comp else open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read())
    g = glsl(d, 'defsrc', code, vecs=[uP()] + list(extra_vecs), res=True)
    demo_out(d, g)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d.outputConnectors[0]); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = HASIN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

# --- optional modulation In CHOP (must be the LAST input). channels band1-4, beat ---
def add_mod(c, name):
    """name e.g. 'in3'. Creates In CHOP + Null 'modin'. Use MOD('band1') in expressions."""
    i = c.create(td.inCHOP, name); n = c.create(td.nullCHOP, 'modin'); n.inputConnectors[0].connect(i)
    return n
def MOD(ch, default=0):
    return "(op('modin')['%s'].eval() if (op('modin') and op('modin').numChans and op('modin')['%s'] is not None) else %s)" % (ch, ch, default)

# --- tail: Mix (dry/wet vs src), Bypass, out1 ---
def finish_v2(c, name, result, src, label='result', extra_outs=()):
    """result = effect TOP, src = dry input switch. Adds Mix cross, Bypass switch, out1 (+ extra_outs=[(top,'label'),..] as out2..)."""
    mx = c.create(td.crossTOP, 'mixer')
    mx.inputConnectors[0].connect(src); mx.inputConnectors[1].connect(result)
    mx.par.cross.expr = 'parent().par.Mix'
    setres(mx); mx.par.format = 'rgba16float'
    bp = c.create(td.switchTOP, 'bypass')
    bp.inputConnectors[0].connect(mx); bp.inputConnectors[1].connect(src)
    bp.par.index.expr = 'parent().par.Bypass'
    setres(bp); bp.par.format = 'rgba16float'
    o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(bp); o.comment = label
    for k, (t, lab) in enumerate(extra_outs):
        n = c.create(td.nullTOP, 'out%d' % (k + 2)); n.inputConnectors[0].connect(t); n.comment = lab
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    c.save(p)
    print('saved', p)
# ======================= end v2 additions =======================

COMP = 'TOP_dof_motionblur'
c = new_comp(COMP)
add_pars(c, [
    ('Speed', 'float', 1.0, 0, 8),
    ('Depthmode', 'menu', [('auto', 'Auto (in2, else radial)'), ('in2', 'in2 TOP'), ('luma', 'Luminance'), ('radial', 'Radial mask')], 0),
    ('Invertdepth', 'toggle', 0),
    ('Focus', 'float', 0.5, 0, 1),
    ('Range', 'float', 0.08, 0, 0.5),
    ('Falloff', 'float', 0.4, 0.02, 1),
    ('Maxblur', 'float', 28, 0, 100),
    ('Quality', 'int', 64, 8, 160),
    ('Boost', 'float', 2.0, 0, 20),
    ('Blades', 'int', 6, 0, 12),
    ('Bladerot', 'float', 0.2, 0, 6.28),
    ('Modamount', 'float', 0.5, 0, 2),
    *COMMON,
])
add_pars(c, [
    ('Mbactive', 'toggle', 1),
    ('Shutter', 'float', 0.55, 0, 0.97),
    ('Velscale', 'float', 1.0, 0, 20),
    ('Velsamples', 'int', 24, 4, 63),
    ('Reset', 'pulse'),
], page='Motion')
add_pars(c, [('Showdepth', 'toggle', 0), ('Showcoc', 'toggle', 0)], page='Output')
P = 'parent().par.'
PH = "((absTime.seconds*parent().par.Speed/8.0) % 1.0)"
PHD = "((absTime.seconds*parent(2).par.Speed/8.0) % 1.0)"
HAS1 = "1 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0"
HAS2 = "1 if (len(parent().inputConnectors[1].connections)+0*absTime.frame) else 0"
HAS3 = "1 if (len(parent().inputConnectors[2].connections)+0*absTime.frame) else 0"
res_chop(c)
i1 = c.create(td.inTOP, 'in1'); i2 = c.create(td.inTOP, 'in2'); i3 = c.create(td.inTOP, 'in3')
add_mod(c, 'in4')
dm = new_demo(c)
dcol = glsl(dm, 'defcolor', rd(COMP, 'src.glsl'), vecs=[('uA', [PHD, 0, 0, 0])], res=True)
ddep = glsl(dm, 'defdepth', rd(COMP, 'src.glsl'), vecs=[('uA', [PHD, 1, 0, 0])], res=True)
demo_out(dm, dcol, 'demo_color'); demo_out(dm, ddep, 'demo_depth')
def sw(nm, a, b, expr):
    s = c.create(td.switchTOP, nm); s.inputConnectors[0].connect(a); s.inputConnectors[1].connect(b)
    s.par.index.expr = expr
    setres(s); s.par.format = 'rgba16float'
    return s
src = sw('src', dm.outputConnectors[0], i1, HAS1)
nod = c.create(td.constantTOP, 'nodepth'); setres(nod); nod.par.format = 'rgba16float'
nod.par.colorr = nod.par.colorg = nod.par.colorb = 0; nod.par.alpha = 1
dsrc = sw('depthsrc', dm.outputConnectors[1], i2, "1 if (len(parent().inputConnectors[1].connections)+0*absTime.frame) else (2 if (len(parent().inputConnectors[0].connections)+0*absTime.frame) else 0)")
dsrc.inputConnectors[2].connect(nod)
prep = glsl(c, 'prep', rd(COMP, 'prep.glsl'), inputs=[src, dsrc], res=True,
            vecs=[('uA', [P + 'Depthmode.menuIndex', HAS1, HAS2, '1 if ' + P + 'Invertdepth else 0'])])
FOC = "min(1,max(0,%sFocus+%sModamount*%s*0.5))" % (P, P, MOD('band1'))
RS = "op('res')['h']/720.0"
dof = glsl(c, 'dof', rd(COMP, 'dof.glsl'), inputs=[src, prep], res=True, vecs=[
    ('uA', [FOC, P + 'Range', P + 'Falloff', P + 'Maxblur']),
    ('uB', [P + 'Quality', P + 'Boost', P + 'Blades', P + 'Bladerot']),
    ('uC', [RS, 0, 0, 0])])
dof.par.inputextenduv = 'hold'
mb = glsl(c, 'mblur', rd(COMP, 'mblur.glsl'), inputs=[dof, i3], res=True,
          vecs=[('uA', [P + 'Velscale*' + P + 'Mbactive', P + 'Velsamples', HAS3, 0])])
mb.par.inputextenduv = 'hold'
blk = c.create(td.constantTOP, 'blank'); setres(blk)
blk.par.format = 'rgba16float'; blk.par.colorr = blk.par.colorg = blk.par.colorb = 0; blk.par.alpha = 1
fb = c.create(td.feedbackTOP, 'feedback'); fb.inputConnectors[0].connect(blk)
fb.par.format = 'rgba16float'
fb.par.reset.expr = P + 'Reset'
acc = glsl(c, 'accum', rd(COMP, 'accum.glsl'), inputs=[fb, mb], res=True,
           vecs=[('uA', [P + 'Shutter', '1 if ' + P + 'Mbactive else 0', 0, 0])])
nul = c.create(td.nullTOP, 'accum_out'); nul.inputConnectors[0].connect(acc)
fb.par.top = nul
vis = glsl(c, 'viewsel', """out vec4 fragColor;
uniform vec4 uV; // showdepth, showcoc, focus, range
uniform vec4 uW; // falloff
void main(){
  vec2 uv = vUV.st;
  vec3 col = texture(sTD2DInputs[0], uv).rgb;
  float d = texture(sTD2DInputs[1], uv).r;
  if(uV.x > 0.5) col = vec3(d);
  if(uV.y > 0.5){ float x = smoothstep(0.0,1.0,(abs(d-uV.z)-uV.w)/max(uW.x,1e-3)); col = mix(vec3(0.05,0.9,0.2), vec3(1.0,0.1,0.1), x) * 0.7+0.0; }
  fragColor = TDOutputSwizzle(vec4(col,1.0));
}
""", inputs=[nul, prep], res=True, vecs=[
    ('uV', ['1 if ' + P + 'Showdepth else 0', '1 if ' + P + 'Showcoc else 0', FOC, P + 'Range']),
    ('uW', [P + 'Falloff', 0, 0, 0])])
finish_v2(c, COMP, vis, src, extra_outs=[(prep, 'depth')])
report(c)
