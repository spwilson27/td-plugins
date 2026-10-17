c = new_comp(COMP)
add_pars(c, [
 ('Layout','menu',[('rendah','Rendah (title bottom-left)'),('center','Center'),('poster','Poster (title top-left)'),('minimal','Minimal'),('data','Data heavy')],0),
 ('Title','str','*PHANTOM\n*SIGNAL\nfield recordings\nvol. 07 / 2026'),
 ('Titlesize','float',0.085,0.01,0.3), ('Telemetry','toggle',1), ('Telesize','float',1.0,0.4,3), ('Telelines','int',6,1,16),
 ('Tickrate','float',8.0,0.5,60), ('Fps','int',24,1,120),
 ('Marks','toggle',1), ('Border','toggle',1), ('Edgeticks','toggle',1), ('Crosshair','toggle',1), ('Borderwidth','float',1.0,0.5,6),
 ('Margin','float',0.045,0.0,0.2), ('Textcolor','rgb',(0.93,0.91,0.86)), ('Accent','toggle',1), ('Accentcolor','rgb',(0.90,0.07,0.05)),
 ('Opacity','float',1.0,0,1,True), ('Modamount','float',0.5,0,2),
 *COMMON,
], 'Controls')
loop_pars(c, beats=0, seconds=8)
res_chop(c)
add_mod(c, 'in2')
# Make Title a multi-line-friendly string: leave as Str; '\n' (backslash-n) also accepted.
lib = mkdat(c, 'lib', rd(COMP, 'lib.py'))
inp = c.create(td.inTOP, 'in1')
blk = c.create(td.constantTOP, 'black'); setres(blk); blk.par.format = 'rgba16float'
for k in ('colorr','colorg','colorb'): blk.par[k] = 0
blk.par.alpha = 1
bsw = c.create(td.switchTOP, 'base')
bsw.inputConnectors[0].connect(blk); bsw.inputConnectors[1].connect(inp)
bsw.par.index.expr = "1 if parent().inputConnectors[0].connections else 0"
setres(bsw); bsw.par.format = 'rgba16float'

M = "op('lib').module."
def text(name, elem, fn, bold=False, accent=False, tele=True, dx=0.0, dy=0.0):
    t = c.create(td.textTOP, name)
    t.par.text.expr = M + fn + '()'
    t.par.outputresolution = 'custom'; setres(t)
    t.par.format = 'rgba16float'
    t.par.fontautosize = 'nofit'
    t.par.fontsizexunit = 'pixels'
    t.par.fontsizex.expr = M + "size('%s')" % elem
    t.par.font = 'Menlo'
    t.par.positionunit = 'fraction'
    t.par.positionx.expr = M + "pos('%s','x')" % elem + (" + %g*%ssize('%s')/op('res')['w']" % (dx, M, elem) if dx else '')
    t.par.positiony.expr = M + "pos('%s','y')" % elem + (" + %g*%ssize('%s')/op('res')['h']" % (dy, M, elem) if dy else '')
    t.par.alignx.expr = M + "align('%s','x')" % elem
    t.par.aligny.expr = M + "align('%s','y')" % elem
    t.par.alignxmode = 'metrics'
    cr = 'Accentcolor' if accent else 'Textcolor'
    for k in 'rgb': t.par['fontcolor' + k].expr = "parent().par.%s%s" % (cr, k)
    gate = (" * parent().par.Telemetry" if tele else "")
    t.par.fontalpha.expr = M + "vis('%s') * parent().par.Opacity" % elem + gate
    t.par.bgalpha = 0
    t.par.linespacing = 0 if False else t.par.linespacing.eval()
    return t
# TD cannot select Menlo Bold, so 'bold' is faux-bold: three copies nudged by ~2% of the font size
tb = text('title_bold', 'title', 'title_bold', tele=False, dx=0.022)
tb2 = text('title_bold2', 'title', 'title_bold', tele=False, dx=-0.022)
tb3 = text('title_bold3', 'title', 'title_bold', tele=False, dy=0.022)
tr_ = text('title_reg', 'title', 'title_reg', tele=False)
tl = text('tele_tl', 'tl', 'tl'); rc = text('tele_rec', 'rec', 'rec', accent=True)
trt = text('tele_tr', 'tr', 'tr'); blt = text('tele_bl', 'bl', 'bl'); brt = text('tele_br', 'br', 'br')
# accent toggle: rec turns bone when Accent off
for k in 'rgb':
    rc.par['fontcolor' + k].expr = "parent().par.Accentcolor%s if parent().par.Accent else parent().par.Textcolor%s" % (k, k)

mk = glsl(c, 'marks', rd(COMP, 'marks.glsl'), vecs=[
  ('uRes', ["op('res')['w']", "op('res')['h']", "parent().par.Margin*op('res')['h']", 'parent().par.Borderwidth']),
  ('uCol', ['parent().par.Textcolorr', 'parent().par.Textcolorg', 'parent().par.Textcolorb', 'parent().par.Opacity']),
  ('uAcc', ['parent().par.Accentcolorr', 'parent().par.Accentcolorg', 'parent().par.Accentcolorb', 'parent().par.Accent']),
  ('uF', ['parent().par.Marks', 'parent().par.Border', 'parent().par.Edgeticks', 'parent().par.Crosshair']),
], fmt='rgba16float', res=True)

comp = c.create(td.compositeTOP, 'comp')
comp.par.operand = 'over'
comp.par.outputresolution = 'custom'; setres(comp); comp.par.format = 'rgba16float'
for s in (mk, brt, blt, trt, rc, tl, tb, tb2, tb3, tr_, bsw):   # TD Composite: first input is on top
    s.outputConnectors[0].connect(comp)
finish_v2(c, COMP, comp, bsw)
report(c)
