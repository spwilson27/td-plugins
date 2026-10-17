# ---- v3 helpers (self-contained; copy into each build.py) ----
import os, td
ROOT = os.path.expanduser('~/software/td-plugins')
COMP = 'TOP_video_synth'

def rd(comp, fn): return open(os.path.join(ROOT, 'components', comp, fn)).read()
def new_comp(name):
    b = op('/build') or op('/').create(td.baseCOMP, 'build')
    old = b.op(name)
    if old: old.destroy()
    return b.create(td.baseCOMP, name)
def mkdat(c, name, s):
    d = c.create(td.textDAT, name); d.text = s; return d

# resolution of the effect: follows in1 when connected and Resolutionmode == input, else custom
RW = "((0*absTime.frame)+parent().op('in1').width if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionw)"
RH = "((0*absTime.frame)+parent().op('in1').height if (parent().par.Resolutionmode=='input' and parent().inputConnectors[0].connections) else parent().par.Resolutionh)"
CONN = "(len(parent().inputConnectors[0].connections) + 0*absTime.frame)"
def setres(o):
    o.par.outputresolution = 'custom'; o.par.resolutionw.expr = RW; o.par.resolutionh.expr = RH
def CH(n): return "parent().op('mod')['%s'].eval()" % n

def glsl(c, name, code, inputs=(), vecs=(), fmt='rgba16float', res=True):
    g = c.create(td.glslTOP, name)
    g.par.pixeldat = mkdat(c, name + '_code', code)
    for i, s in enumerate(inputs[:3]): g.inputConnectors[i].connect(s)
    if vecs: g.seq.vec.numBlocks = len(vecs)
    for i, (n, vals) in enumerate(vecs):
        g.par['vec%dname' % i] = n
        for j, v in enumerate(vals):
            p = g.par['vec%dvalue%s' % (i, 'xyzw'[j])]
            if isinstance(v, str): p.expr = v
            else: p.val = v
    g.par.format = fmt
    if res: setres(g)
    return g

def add_pars(c, specs, page='Controls'):
    pg = c.appendCustomPage(page)
    for s in specs:
        n, k = s[0], s[1]
        if k == 'float':
            p = pg.appendFloat(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]
            if len(s) > 5 and s[5]: p.clampMin = p.clampMax = True
        elif k == 'int':
            p = pg.appendInt(n)[0]; p.default = s[2]; p.val = s[2]; p.min = s[3]; p.max = s[4]; p.normMin = s[3]; p.normMax = s[4]; p.clampMin = p.clampMax = True
        elif k == 'toggle':
            p = pg.appendToggle(n)[0]; p.default = s[2]; p.val = s[2]
        elif k == 'pulse': pg.appendPulse(n)
        elif k == 'menu':
            p = pg.appendMenu(n)[0]; p.menuNames = [m[0] for m in s[2]]; p.menuLabels = [m[1] for m in s[2]]
            p.default = s[2][s[3]][0]; p.val = s[2][s[3]][0]
        elif k == 'wh':
            for q, v in zip(pg.appendWH(n), s[2]):
                q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
        elif k == 'rgb':
            for q, v in zip(pg.appendRGB(n), s[2]):
                q.default = v; q.val = v; q.min = 0; q.max = 1; q.normMin = 0; q.normMax = 1
        elif k == 'str':
            p = pg.appendStr(n)[0]; p.default = s[2]; p.val = s[2]
    return pg

def std_top_pars(c):
    """Mix / Bypass / Resolutionmode / Resolution on the Controls page (call after the component pars)."""
    pg = [p for p in c.customPages if p.name == 'Controls'][0]
    p = pg.appendFloat('Mix')[0]; p.default = 1; p.val = 1; p.min = 0; p.max = 1; p.normMin = 0; p.normMax = 1; p.clampMin = p.clampMax = True
    pg.appendToggle('Bypass')
    p = pg.appendMenu('Resolutionmode')[0]; p.menuNames = ['input', 'custom']; p.menuLabels = ['Follow input', 'Custom']; p.default = 'input'; p.val = 'input'
    for q, v in zip(pg.appendWH('Resolution'), (1280, 720)):
        q.default = v; q.val = v; q.min = 16; q.max = 8192; q.normMin = 16; q.normMax = 4096
    c.par.Resolutionw.enableExpr = "me.par.Resolutionmode=='custom'"
    c.par.Resolutionh.enableExpr = "me.par.Resolutionmode=='custom'"

def mod_chop(c, name):
    """optional modulation In CHOP (band1..4, beat) merged over zeros so every channel always exists"""
    im = c.create(td.inCHOP, name)
    mz = c.create(td.constantCHOP, 'modzero')
    for i, n in enumerate(['band1', 'band2', 'band3', 'band4', 'beat']):
        setattr(mz.par, 'name%d' % i, n); setattr(mz.par, 'value%d' % i, 0)
    mg = c.create(td.mergeCHOP, 'mod'); mg.inputConnectors[0].connect(im); mg.inputConnectors[1].connect(mz)
    mg.par.duplicate = 'first'; mg.par.align = 'start'
    return mg

def demo_switch(c, demo_out, name='src', in1='in1'):
    """Switch TOP: index 0 = demo (gated), 1 = in1. Index is 1 when in1 is connected."""
    sw = c.create(td.switchTOP, name)
    sw.inputConnectors[0].connect(demo_out); sw.inputConnectors[1].connect(c.op(in1))
    sw.par.index.expr = "1 if %s else 0" % CONN
    setres(sw); sw.par.format = 'rgba16float'
    return sw

def mix_bypass(c, dry, wet, out_name='out1'):
    x = c.create(td.crossTOP, 'mixfx'); x.inputConnectors[0].connect(dry); x.inputConnectors[1].connect(wet)
    x.par.cross.expr = 'parent().par.Mix'; x.par.format = 'rgba16float'; x.par.outputresolution = 'useinput'
    bp = c.create(td.switchTOP, 'bypass'); bp.inputConnectors[0].connect(x); bp.inputConnectors[1].connect(c.op('in1'))
    bp.par.index.expr = "1 if (parent().par.Bypass and %s) else 0" % CONN
    o = c.create(td.outTOP, out_name); o.inputConnectors[0].connect(bp)
    return o

def finish(c, name):
    c.layout()
    os.makedirs(os.path.join(ROOT, 'tox', '_raw'), exist_ok=True)
    c.save(os.path.join(ROOT, 'tox', '_raw', name + '.tox'))
    print('saved raw', name)

def report(c):
    for o in [c] + c.findChildren():
        for k, s in (('err', o.errors()), ('warn', o.warnings()), ('script', o.scriptErrors())):
            if s: print(k, o.path, s[:300])
# ---- end helpers ----
c = new_comp(COMP)
SHP = [('sine', 'Sine'), ('square', 'Square'), ('saw', 'Saw')]
PRESETS = {
 'bone_waves':  dict(Freqa=6,Speeda=.15,Rota=0,Shapea='sine',Freqb=9,Speedb=-.1,Rotb=90,Shapeb='sine',Freqc=3,Speedc=.2,Rotc=45,Shapec='saw',Modulate=.35,Kaleid=0,Feedback=.4,Echozoom=1.02,Echorot=1,Colorize=.2,Palette='bone',Hue=0,Contrast=1.4,Rotspeed=0,Gamma=2,Pattern=.5,Mixmode='blend',Displace=.6),
 'chrome_moire':dict(Freqa=24,Speeda=.1,Rota=0,Shapea='sine',Freqb=25,Speedb=-.1,Rotb=3,Shapeb='sine',Freqc=40,Speedc=.2,Rotc=90,Shapec='sine',Modulate=.12,Kaleid=0,Feedback=.3,Echozoom=1.01,Echorot=.5,Colorize=.3,Gamma=2.2,Palette='chrome',Hue=0,Contrast=1.6,Rotspeed=3,Pattern=.55,Mixmode='multiply',Displace=.5),
 'red_kaleid':  dict(Freqa=5,Speeda=.2,Rota=0,Shapea='square',Freqb=7,Speedb=-.3,Rotb=60,Shapeb='sine',Freqc=3,Speedc=.1,Rotc=120,Shapec='saw',Modulate=.6,Kaleid=8,Feedback=.4,Echozoom=1.03,Echorot=3,Colorize=0,Gamma=2.4,Palette='red',Hue=0,Contrast=1.3,Rotspeed=8,Pattern=.4,Mixmode='blend',Displace=.9),
 'acid_displace':dict(Freqa=3,Speeda=.2,Rota=0,Shapea='sine',Freqb=4,Speedb=.3,Rotb=30,Shapeb='saw',Freqc=10,Speedc=-.15,Rotc=75,Shapec='sine',Modulate=1.3,Kaleid=0,Feedback=.3,Echozoom=1.02,Echorot=2,Colorize=.9,Gamma=3,Palette='acid',Hue=0,Contrast=1.1,Rotspeed=0,Pattern=.2,Mixmode='blend',Displace=1.6),
 'luma_key':    dict(Freqa=30,Speeda=.15,Rota=0,Shapea='square',Freqb=12,Speedb=-.1,Rotb=0,Shapeb='square',Freqc=2,Speedc=.1,Rotc=90,Shapec='sine',Modulate=.2,Kaleid=0,Feedback=.2,Echozoom=1.01,Echorot=0,Gamma=2.2,Colorize=.1,Palette='bone',Hue=0,Contrast=1.5,Rotspeed=0,Pattern=1.0,Mixmode='key',Displace=.3),
 'tunnel_echo': dict(Freqa=8,Speeda=-.3,Rota=0,Shapea='saw',Freqb=6,Speedb=.1,Rotb=45,Shapeb='sine',Freqc=12,Speedc=.3,Rotc=90,Shapec='sine',Modulate=.5,Kaleid=6,Feedback=.7,Echozoom=.97,Echorot=4,Colorize=.4,Gamma=2.6,Palette='red',Hue=0,Contrast=1.4,Rotspeed=-6,Pattern=.35,Mixmode='difference',Displace=.8),
}
add_pars(c, [
    ('Preset', 'menu', [('custom', 'Custom')] + [(k, k.replace('_', ' ').title()) for k in PRESETS], 1),
    ('Mixmode', 'menu', [('blend', 'Blend'), ('key', 'Luma key'), ('multiply', 'Multiply'), ('difference', 'Difference')], 0),
    ('Pattern', 'float', .5, 0, 1),
    ('Displace', 'float', .6, 0, 3),
    ('Colorize', 'float', .2, 0, 1),
    ('Hue', 'float', 0, 0, 1),
    ('Keylevel', 'float', .4, 0, 1),
    ('Kaleid', 'int', 0, 0, 24),
    ('Palette', 'menu', [('bone', 'Bone'), ('chrome', 'Chrome'), ('red', 'Red'), ('rainbow', 'Rainbow'), ('acid', 'Acid')], 0),
    ('Contrast', 'float', 1.4, .2, 4), ('Gamma', 'float', 2.0, .5, 4),
    ('Scale', 'float', 1, .1, 4), ('Rotspeed', 'float', 0, -90, 90),
])
std_top_pars(c)
add_pars(c, [
    ('Freqa', 'float', 6, 0, 80), ('Speeda', 'float', .15, -2, 2), ('Rota', 'float', 0, -180, 180), ('Shapea', 'menu', SHP, 0),
    ('Freqb', 'float', 9, 0, 80), ('Speedb', 'float', -.1, -2, 2), ('Rotb', 'float', 90, -180, 180), ('Shapeb', 'menu', SHP, 0),
    ('Freqc', 'float', 3, 0, 80), ('Speedc', 'float', .2, -2, 2), ('Rotc', 'float', 45, -180, 180), ('Shapec', 'menu', SHP, 2),
    ('Modulate', 'float', .35, 0, 3),
], page='Oscillators')
add_pars(c, [
    ('Feedback', 'float', .4, 0, .95),
    ('Echozoom', 'float', 1.02, .8, 1.2), ('Echorot', 'float', 1, -20, 20), ('Echospacing', 'float', .05, 0, 1),
], page='Echo')
mkdat(c, 'presets', repr(PRESETS))
pe = c.create(td.parameterexecuteDAT, 'preset_exec')
pe.text = """def apply(c, name):
    if name == 'custom':
        return
    d = eval(c.op('presets').text)
    for k, v in d.get(name, {}).items():
        c.par[k] = v

def onValueChange(par, prev):
    if par.name == 'Preset':
        apply(par.owner, str(par))
    return
"""
pe.par.op = '..'; pe.par.pars = 'Preset'; pe.par.valuechange = True; pe.par.onpulse = False
pe.par.custom = True; pe.par.builtin = False
for k, v in PRESETS['bone_waves'].items(): c.par[k] = v

i1 = c.create(td.inTOP, 'in1')
mod_chop(c, 'in2')
demo = c.create(td.baseCOMP, 'demo')
demo.comment = 'preview-only picture (used while in1 is unconnected; does not cook otherwise)'
# preview-only demo picture, native: colour rings (Ramp, circular) x vertical bars (Ramp) + thin bone lines (Ramp) + a drifting disc (Circle)
import math as _m
def keytable(name, rows):
    t = demo.create(td.tableDAT, name)
    t.clear(); t.appendRow(['pos', 'r', 'g', 'b', 'a'])
    for r_ in rows: t.appendRow(r_)
    return t
def ramp(name, typ, rows, period, phase, inp=None, operand='multiply'):
    r_ = demo.create(td.rampTOP, name)
    r_.par.dat = keytable(name + '_keys', rows)
    r_.par.type = typ; r_.par.period = period
    if isinstance(phase, str): r_.par.phase.expr = phase
    else: r_.par.phase = phase
    r_.par.extendleft = 'repeat'; r_.par.fitaspect = 'fitvert' if typ == 'circular' else 'fithorz'
    r_.par.outputresolution = 'custom'; r_.par.resolutionw = 1280; r_.par.resolutionh = 720; r_.par.format = 'rgba16float'
    r_.par.interpnotches = 'linear'
    if inp is not None:
        r_.par.combineinput = 'compres'; r_.par.operand = operand; r_.inputConnectors[0].connect(inp)
    return r_
N = 24
rings_rows = [[i / N] + [0.5 + 0.5 * _m.cos(ph + 2 * _m.pi * i / N) for ph in (0.0, 2.1, 4.2)] + [1] for i in range(N + 1)]
rings = ramp('rings', 'circular', rings_rows, 2 * _m.pi / 3, '0.5*absTime.seconds/(2*math.pi)')
bars = ramp('bars', 'horizontal', [[0, .35, .35, .35, 1], [.49999, .35, .35, .35, 1], [.5, 1, 1, 1, 1], [1, 1, 1, 1, 1]], 0.25 * 720 / 1280, '0.3*math.sin(absTime.seconds*0.3)', inp=rings)
lines = ramp('lines', 'vertical', [[0, .92, .9, .8, 1], [.08, .92, .9, .8, 1], [.0801, .92, .9, .8, 0], [.9199, .92, .9, .8, 0], [.92, .92, .9, .8, 1], [1, .92, .9, .8, 1]], 0.2, 0.5, inp=bars, operand='over')
disc = demo.create(td.circleTOP, 'disc')
disc.par.outputresolution = 'custom'; disc.par.resolutionw = 1280; disc.par.resolutionh = 720; disc.par.format = 'rgba16float'
disc.par.radiusunit = 'pixels'; disc.par.radiusx = 0.16 * 720; disc.par.radiusy = 0.16 * 720
disc.par.centerunit = 'pixels'; disc.par.centerx.expr = '0.35*720*math.sin(absTime.seconds*0.6)'; disc.par.centery.expr = '0.2*720*math.cos(absTime.seconds*0.45)'
disc.par.softnessunit = 'pixels'; disc.par.softness = 14; disc.par.borderwidth = 0
disc.par.fillcolorr = 1.0; disc.par.fillcolorg = 0.25; disc.par.fillcolorb = 0.1; disc.par.fillalpha = 1
disc.par.bgalpha = 0; disc.par.borderalpha = 0; disc.par.premultrgbbyalpha = False
disc.par.combineinput = 'compres'; disc.par.operand = 'over'; disc.inputConnectors[0].connect(lines)
do = demo.create(td.outTOP, 'out1'); do.inputConnectors[0].connect(disc)
src = demo_switch(c, demo.outputConnectors[0], 'src')

p = lambda n: 'parent().par.' + n
sh = lambda s: p(s) + '.menuIndex'
g = glsl(c, 'synth', rd(COMP, 'synth.glsl'), inputs=[src], vecs=[
    ('uT', ['absTime.seconds', 0, 0, 0]),
    ('uO0', [p('Freqa') + '*(1+0.4*' + CH('band2') + ')', p('Speeda'), p('Rota'), sh('Shapea')]),
    ('uO1', [p('Freqb') + '*(1+0.4*' + CH('band2') + ')', p('Speedb'), p('Rotb'), sh('Shapeb')]),
    ('uO2', [p('Freqc'), p('Speedc'), p('Rotc'), sh('Shapec')]),
    ('uM', [p('Modulate'), p('Kaleid'), 'min(0.95,' + p('Feedback') + '+0.3*' + CH('band3') + ')', p('Colorize')]),
    ('uN', [p('Scale'), p('Hue'), p('Contrast'), sh('Palette')]),
    ('uQ', [p('Rotspeed'), p('Pattern'), p('Echozoom'), p('Echorot')]),
    ('uR', [p('Echospacing'), p('Displace') + '*(1+' + CH('band1') + ')', sh('Mixmode'), p('Gamma')]),
    ('uS', [p('Keylevel'), CH('beat'), 0, 0]),
])
o1 = mix_bypass(c, src, g)
finish(c, COMP)
report(c)
