exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())
import random

def messy(ex, name, seed):
    """A deliberately tangled network (tagged no_arrange so the library's own layout checks leave it alone)."""
    m = ex.create(td.baseCOMP, name, row=1)
    m.tags.add('no_arrange')
    rnd = random.Random(seed)
    n = m.create(td.noiseTOP, 'noise1'); prev = n
    chain = [td.levelTOP, td.blurTOP, td.hsvadjustTOP, td.transformTOP, td.edgeTOP, td.compositeTOP, td.nullTOP]
    for i, t in enumerate(chain):
        o = m.create(t, '%s%d' % (t.__name__.replace('TOP', ''), i + 1))
        o.inputConnectors[0].connect(prev); prev = o
    r = m.create(td.rampTOP, 'ramp1'); m.op('composite6').inputConnectors[1].connect(r)
    for i in range(3):
        d = m.create(td.textDAT, 'notes%d' % (i + 1)); d.text = 'loose DAT'
    for o in m.children:   # pile everything on top of each other
        o.nodeX = rnd.randint(0, 260); o.nodeY = rnd.randint(-120, 120)
    return m

def label(ex, txt):
    t = ex.create(td.textTOP, 'readme', row=0)
    t.par.text = txt
    t.par.outputresolution = 'custom'; t.par.resolutionw = 960; t.par.resolutionh = 300
    t.par.fontsizex = 26; t.par.alignx = 'left'; t.par.aligny = 'center'
    t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0.06; t.par.bgalpha = 1
    return t

s = begin('UTIL_auto_arrange')

ex = example(s, 1, 'Untangle a network',
  'messy_network is a pile of overlapping nodes (dive in to see). UTIL_auto_arrange targets it:\n'
  'pulse Arrange -> left-to-right data flow, unwired DATs in a band below, no overlaps.\n'
  'Empty Target = the network the component sits in. Recursive also tidies child COMPs.')
m = messy(ex, 'messy_network', 7)
a = instance(ex, 'UTIL_auto_arrange'); a.par.reloadcustom = False; a.par.reloadbuiltin = False
a.par.Target = m
out(ex, 1, label(ex, 'Pulse Arrange on ex1_UTIL_auto_arrange,\nthen dive into ex1_messy_network.'))

ex = example(s, 2, 'Check without moving anything',
  'Check only reports overlapping nodes; the report table is out1 (also shown in the node viewer).\n'
  'Here a Text TOP displays the report. Pulse Check, then Arrange, then Check again: overlaps -> 0.\n'
  'Annotate Groups keeps nodes inside Annotate boxes together and resizes the boxes.')
m2 = messy(ex, 'messy_network', 11)
a2 = instance(ex, 'UTIL_auto_arrange'); a2.par.reloadcustom = False; a2.par.reloadbuiltin = False
a2.par.Target = m2
t = ex.create(td.textTOP, 'report_view', row=0)
t.par.dat = a2.op('out1')
t.par.outputresolution = 'custom'; t.par.resolutionw = 960; t.par.resolutionh = 300
t.par.fontsizex = 22; t.par.alignx = 'left'; t.par.aligny = 'top'
t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0.06; t.par.bgalpha = 1
out(ex, 2, t)

finish(s)
