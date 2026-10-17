# ---- v2: Clock CHOP parameter (Loop page) ----
import td as _td
CLOCK_CB = '''def sync(c):
    clk = c.par.Clock.eval()
    if clk:
        c.par.Phase.expr = "me.par.Clock.eval()['phase'].eval() if me.par.Clock.eval() and me.par.Clock.eval()['phase'] is not None else 0"
    elif c.par.Phase.mode == ParMode.EXPRESSION:
        c.par.Phase.expr = ''
        c.par.Phase.mode = ParMode.CONSTANT
        c.par.Phase.val = 0.0

def onValueChange(par, prev):
    sync(par.owner)
    return
'''
def add_clock(c):
    pg = [p for p in c.customPages if p.name == 'Loop'][0]
    p = pg.appendCHOP('Clock', label='Clock (CHOP, phase channel)')[0]
    cb = c.create(_td.parameterexecuteDAT, 'clock_exec')
    cb.text = CLOCK_CB
    cb.par.op = '..'; cb.par.pars = 'Clock'; cb.par.valuechange = True; cb.par.onpulse = False
    cb.par.custom = True; cb.par.builtin = False
# ---- end v2 clock ----
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

def setres(o, w='parent().par.Resolutionw', h='parent().par.Resolutionh'):
    o.par.outputresolution = 'custom'
    o.par.resolutionw.expr = w; o.par.resolutionh.expr = h

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

def finish(c, name):
    c.layout()
    p = os.path.join(ROOT, 'tox', '_raw', name + '.tox')
    c.save(p)
    print('saved', p)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])

# ---- signal_lib: loop params + periodic default source (appended after lib.py) ----
LENEXPR = "max(0.25,(parent().par.Loopseconds if parent().par.Loopseconds>0 else parent().par.Loopbeats*60.0/max(1.0,parent().par.Bpm)))"
PEXPR = "((parent().par.Phase if parent().par.Timesource=='phase' else absTime.seconds/%s) %% 1.0)" % LENEXPR
FREXPR = "max(2,2*round(%s*15))" % LENEXPR
def uP(extra=0):
    return ('uP', [PEXPR, LENEXPR, FREXPR, extra])

def loop_pars(c, beats=8):
    add_pars(c, [
        ('Timesource', 'menu', [('abstime', 'Abs Time'), ('phase', 'Phase')], 0),
        ('Phase', 'float', 0, 0, 1),
        ('Loopbeats', 'float', beats, 1, 64),
        ('Bpm', 'float', 120, 30, 300),
        ('Loopseconds', 'float', 0, 0, 60),
    ], page='Loop')

def sig_input(c):
    i = c.create(td.inTOP, 'in1')
    d = glsl(c, 'defsrc', open(os.path.join(ROOT, 'components/_lib/signal_src.glsl')).read(), vecs=[uP()], res=True)
    sw = c.create(td.switchTOP, 'src')
    sw.inputConnectors[0].connect(d); sw.inputConnectors[1].connect(i)
    sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
    setres(sw); sw.par.format = 'rgba16float'
    return sw
# ---- end signal_lib ----

COMP = 'GEN_video_synth'
c = new_comp(COMP)
SHP = [('sine', 'Sine'), ('square', 'Square'), ('saw', 'Saw')]
PRESETS = {
 'bone_waves':  dict(Freqa=6,Synca=1,Rota=0,Shapea='sine',Freqb=9,Syncb=-1,Rotb=90,Shapeb='sine',Freqc=3,Syncc=2,Rotc=45,Shapec='saw',Modulate=.35,Kaleid=0,Feedback=.5,Echozoom=1.02,Echorot=1,Colorize=0,Palette='bone',Hue=0,Contrast=1.4,Rotspeed=0,Gamma=2),
 'chrome_moire':dict(Freqa=24,Synca=1,Rota=0,Shapea='sine',Freqb=25,Syncb=-1,Rotb=3,Shapeb='sine',Freqc=40,Syncc=2,Rotc=90,Shapec='sine',Modulate=.12,Kaleid=0,Feedback=.35,Echozoom=1.01,Echorot=.5,Colorize=0.3,Gamma=2.2,Palette='chrome',Hue=0,Contrast=1.6,Rotspeed=1),
 'red_kaleid':  dict(Freqa=5,Synca=1,Rota=0,Shapea='square',Freqb=7,Syncb=-2,Rotb=60,Shapeb='sine',Freqc=3,Syncc=1,Rotc=120,Shapec='saw',Modulate=.6,Kaleid=8,Feedback=.4,Echozoom=1.03,Echorot=3,Colorize=0,Gamma=2.4,Palette='red',Hue=0,Contrast=1.3,Rotspeed=1),
 'acid_mod':    dict(Freqa=3,Synca=1,Rota=0,Shapea='sine',Freqb=4,Syncb=2,Rotb=30,Shapeb='saw',Freqc=10,Syncc=-1,Rotc=75,Shapec='sine',Modulate=1.3,Kaleid=0,Feedback=.5,Echozoom=1.02,Echorot=2,Colorize=.7,Gamma=3,Palette='acid',Hue=0,Contrast=1.1,Rotspeed=0),
 'scanner':     dict(Freqa=30,Synca=1,Rota=0,Shapea='square',Freqb=12,Syncb=-1,Rotb=0,Shapeb='square',Freqc=2,Syncc=1,Rotc=90,Shapec='sine',Modulate=.2,Kaleid=0,Feedback=.5,Echozoom=1.01,Echorot=0,Gamma=2.2,Colorize=0,Palette='bone',Hue=0,Contrast=1.5,Rotspeed=0),
 'tunnel':      dict(Freqa=8,Synca=-2,Rota=0,Shapea='saw',Freqb=6,Syncb=1,Rotb=45,Shapeb='sine',Freqc=12,Syncc=3,Rotc=90,Shapec='sine',Modulate=.5,Kaleid=6,Feedback=.6,Echozoom=.97,Echorot=4,Colorize=0,Gamma=2.6,Palette='red',Hue=0,Contrast=1.4,Rotspeed=-1),
}
add_pars(c, [
    ('Mode', 'menu', [('custom', 'Custom')] + [(k, k.replace('_', ' ').title()) for k in PRESETS], 1),
    ('Freqa', 'float', 6, 0, 80), ('Synca', 'int', 1, -8, 8), ('Rota', 'float', 0, -180, 180), ('Shapea', 'menu', SHP, 0),
    ('Freqb', 'float', 9, 0, 80), ('Syncb', 'int', -1, -8, 8), ('Rotb', 'float', 90, -180, 180), ('Shapeb', 'menu', SHP, 0),
    ('Freqc', 'float', 3, 0, 80), ('Syncc', 'int', 2, -8, 8), ('Rotc', 'float', 45, -180, 180), ('Shapec', 'menu', SHP, 2),
    ('Modulate', 'float', .35, 0, 3),
    ('Kaleid', 'int', 0, 0, 24),
    ('Feedback', 'float', .5, 0, .95),
    ('Echozoom', 'float', 1.02, .8, 1.2), ('Echorot', 'float', 1, -20, 20), ('Echospacing', 'float', .01, .001, .1),
    ('Colorize', 'float', 0, 0, 1),
    ('Palette', 'menu', [('bone', 'Bone'), ('chrome', 'Chrome'), ('red', 'Red'), ('rainbow', 'Rainbow'), ('acid', 'Acid')], 0),
    ('Hue', 'float', 0, 0, 1), ('Contrast', 'float', 1.4, .2, 4),
    ('Scale', 'float', 1, .1, 4), ('Gamma', 'float', 2.0, .5, 4), ('Rotspeed', 'int', 0, -4, 4),
    ('Inputmix', 'float', 0, 0, 1), ('Inputdisplace', 'float', .5, 0, 2),
])
add_pars(c, [('Resolution', 'wh', (1280, 720))], page='Render')
loop_pars(c, beats=8)
mkdat(c, 'presets', repr(PRESETS))
pe = c.create(td.parameterexecuteDAT, 'preset_exec')
pe.text = '''def onValueChange(par, prev):
    if par.name != 'Mode' or str(par) == 'custom':
        return
    d = eval(parent().op('presets').text)
    for k, v in d.get(str(par), {}).items():
        parent().par[k] = v
'''
pe.par.op = c; pe.par.pars = 'Mode'; pe.par.valuechange = True
for k, v in PRESETS['bone_waves'].items(): c.par[k] = v
# input: black when unconnected
i = c.create(td.inTOP, 'in1')
blk = c.create(td.constantTOP, 'black'); blk.par.colorr = 0; blk.par.colorg = 0; blk.par.colorb = 0
sw = c.create(td.switchTOP, 'src'); sw.inputConnectors[0].connect(blk); sw.inputConnectors[1].connect(i)
sw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"; setres(sw)
p = lambda n: 'parent().par.' + n
sh = lambda s: p(s) + '.menuIndex'
g = glsl(c, 'synth', rd(COMP, 'synth.glsl'), inputs=[sw], res=True, vecs=[
    uP(),
    ('uO0', [p('Freqa'), p('Synca'), p('Rota'), sh('Shapea')]),
    ('uO1', [p('Freqb'), p('Syncb'), p('Rotb'), sh('Shapeb')]),
    ('uO2', [p('Freqc'), p('Syncc'), p('Rotc'), sh('Shapec')]),
    ('uM', [p('Modulate'), p('Kaleid'), p('Feedback'), p('Colorize')]),
    ('uN', [p('Scale'), p('Hue'), p('Contrast'), sh('Palette')]),
    ('uQ', [p('Rotspeed'), p('Inputmix'), p('Echozoom'), p('Echorot')]),
    ('uR', [p('Echospacing'), p('Inputdisplace'), '1 if parent().inputConnectors[0].connections else 0', p('Gamma')]),
])
o = c.create(td.outTOP, 'out1'); o.inputConnectors[0].connect(g); o.comment = 'render'
add_clock(c)
finish(c, COMP)
report(c)
