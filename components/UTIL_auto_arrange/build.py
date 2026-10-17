# UTIL_auto_arrange: lay out a network so no nodes overlap and data flows left -> right.
# Runs inside TouchDesigner (tools/build.sh). Embeds td_organize/td_runtime.py so the tox is self-contained.
import os, td

NAME = 'UTIL_auto_arrange'
ROOT = os.path.expanduser(os.environ.get('TD_PLUGINS_HOME', '~/software/td-plugins'))

h = op('/build') or op('/').create(td.baseCOMP, 'build')
old = h.op(NAME)
if old: old.destroy()
c = h.create(td.baseCOMP, NAME)

pg = c.appendCustomPage('Controls')
p = pg.appendCOMP('Target', label='Target')[0]
p.help = 'COMP whose network to arrange. Empty = the network this component sits in.'
p = pg.appendPulse('Arrange', label='Arrange')[0]
p.help = 'Lay out the target network: left-to-right data flow, docked DATs under their hosts, unwired nodes in a band below, no overlaps.'
p = pg.appendPulse('Check', label='Check')[0]
p.help = 'Only report overlapping nodes (see the report output / node viewer). Nothing is moved.'
p = pg.appendToggle('Recursive', label='Recursive')[0]; p.default = True; p.val = True
p.help = 'Also arrange the networks inside child COMPs (skips COMPs that load an external tox, and COMPs tagged no_arrange).'
p = pg.appendToggle('Annotategroups', label='Annotate Groups')[0]; p.default = True; p.val = True
p.help = 'Keep nodes that sit inside an Annotate box together, lay out each box separately and resize it to fit.'

rt = c.create(td.textDAT, 'runtime')
rt.text = open(os.path.join(ROOT, 'td_organize', 'td_runtime.py')).read()
rt.comment = 'td_organize runtime (generated from td_organize/; rebuilt with the component)'

rep = c.create(td.tableDAT, 'report')
rep.clear()
rep.appendRow(['network', 'nodes', 'overlaps_before', 'overlaps_after'])
out = c.create(td.nullDAT, 'out1'); out.inputConnectors[0].connect(rep)
out.comment = 'arrange report'

pe = c.create(td.parameterexecuteDAT, 'arrange_callbacks')
pe.text = '''# Arrange / Check pulses -> td_organize runtime; results go to the report table (out1).

def _runtime():
    ns = {'op': op}
    exec(op('runtime').text, ns)
    return ns

def _target(c):
    return c.par.Target.eval() or c.parent()

def run(c, mode):
    ns = _runtime()
    tgt = _target(c)
    rep = op('report')
    rep.clear(keepFirstRow=True)
    if mode == 'arrange':
        before = {}
        for prob in ns['check'](tgt, recursive=bool(c.par.Recursive.eval())):
            before[prob['comp']] = before.get(prob['comp'], 0) + 1
        stats = ns['organize'](tgt, recursive=bool(c.par.Recursive.eval()),
                               annotate_groups=bool(c.par.Annotategroups.eval()))
        for path, s in stats.items():
            rep.appendRow([path, s.get('nodes', ''), s.get('overlaps_before', before.get(path, 0)), s.get('overlaps_after', 0)])
    else:
        counts = {}
        for prob in ns['check'](tgt, recursive=bool(c.par.Recursive.eval())):
            counts[prob['comp']] = counts.get(prob['comp'], 0) + 1
        if not counts:
            rep.appendRow([tgt.path, '', 0, 0])
        for path, n in counts.items():
            rep.appendRow([path, '', n, n])
    return rep

def onPulse(par):
    if par.name == 'Arrange':
        run(par.owner, 'arrange')
    elif par.name == 'Check':
        run(par.owner, 'check')
    return
'''
pe.par.op = '..'
pe.par.pars = 'Arrange Check'
pe.par.onpulse = True
pe.par.valuechange = False
pe.par.custom = True
pe.par.builtin = False

c.save(os.path.join(ROOT, 'tox', '_raw', NAME + '.tox'))
print('saved')
