# UTIL_tab_menu: adds a "td-plugins" tab to TouchDesigner's OP Create dialog (Tab menu) that lists every
# library component and creates it like a built-in operator. Runs inside TouchDesigner (tools/build.sh).
# The module code lives in tdp.py (embedded into the Text DAT `tdp`, so the tox is self-contained).
import os, td

NAME = 'UTIL_tab_menu'
ROOT = os.path.expanduser(os.environ.get('TD_PLUGINS_HOME', '~/software/td-plugins'))

h = op('/build') or op('/').create(td.baseCOMP, 'build')
old = h.op(NAME)
if old: old.destroy()
c = h.create(td.baseCOMP, NAME)

# ---- parameters
pg = c.appendCustomPage('Controls')
p = pg.appendPulse('Install', label='Install')[0]
p = pg.appendPulse('Uninstall', label='Uninstall')[0]
p = pg.appendToggle('Autoinstall', label='Auto Install')[0]; p.default = True; p.val = True
p = pg.appendPulse('Refresh', label='Refresh List')[0]
p = pg.appendStr('Tablabel', label='Tab Label')[0]; p.default = 'td-plugins'; p.val = 'td-plugins'
p = pg.appendMenu('Createmode', label='Create Mode')[0]
p.menuNames = ['embed', 'link']; p.menuLabels = ['Embed (copy of the tox)', 'Link (external tox)']
p.default = 'embed'; p.val = 'embed'
p = pg.appendStr('Status', label='Status')[0]; p.val = 'not installed'; p.default = 'not installed'; p.readOnly = True

# ---- module + data
tdp = c.create(td.textDAT, 'tdp')
tdp.text = open(os.path.join(ROOT, 'components', NAME, 'tdp.py')).read()
tdp.comment = 'module: scan / install / uninstall / cook / create (generated from components/UTIL_tab_menu/tdp.py)'

ent = c.create(td.tableDAT, 'entries')
ent.clear()
ent.appendRow(['name', 'family', 'tox', 'label', 'description'])
ent.comment = 'catalogue of <Libraryroot>/tox/*/*.tox (Refresh rescans)'
ins = c.create(td.tableDAT, 'installed')
ins.clear()
ins.appendRow(['name', 'family', 'tox'])
out = c.create(td.outDAT, 'out1'); out.inputConnectors[0].connect(ins)
out.comment = 'entries installed in the OP Create dialog'

cr = c.create(td.textDAT, 'create')
cr.text = ("# run by the patched OP Create dialog (tscript `run`): args[0] = 'pane~operator~nodepath~connectmode~type~connector'\n"
           "op('tdp').module.create(args)\n")
cr.comment = 'entry point called from the dialog'

cb = c.create(td.parameterexecuteDAT, 'callbacks')
cb.text = '''# Install / Uninstall / Refresh pulses, Tablabel changes -> tdp module

def onPulse(par):
    m = op('tdp').module
    if par.name == 'Install':
        m.install()
    elif par.name == 'Uninstall':
        m.uninstall()
    elif par.name == 'Refresh':
        m.refresh()
        if m.installed_by_me():
            m.status('installed: tab "%s", %d entries' % (m.key(), op('entries').numRows - 1))
    return

def onValueChange(par, prev):
    if par.name == 'Tablabel':
        m = op('tdp').module
        if m.installed_by_me():
            m.uninstall(_quiet=True)
            m.install()
    return
'''
cb.par.op = '..'
cb.par.pars = 'Install Uninstall Refresh Tablabel'
cb.par.onpulse = True
cb.par.valuechange = True
cb.par.custom = True
cb.par.builtin = False

ex = c.create(td.executeDAT, 'start')
ex.text = '''# project start / creation -> install when Autoinstall is on (a few frames later, once the project is up)

def _later():
    run("p = op(%r)\\nif p is not None and p.par.Autoinstall: p.op('tdp').module.install()" % parent().path,
        delayFrames=3, delayRef=op.TDResources)

def onStart():
    _later()
    return

def onCreate():
    _later()
    return

def onProjectPreSave():
    op('tdp').module.park()
    return

def onProjectPostSave():
    op('tdp').module.unpark()
    return
'''
for n in ('start', 'create', 'exit', 'framestart', 'frameend', 'playstatechange', 'devicechange', 'projectpresave', 'projectpostsave'):
    if hasattr(ex.par, n): setattr(ex.par, n, n in ('start', 'create', 'projectpresave', 'projectpostsave'))

ext = c.create(td.textDAT, 'ext')
ext.text = '''# Extension: when this component is destroyed (or its extensions are re-initialised) the OP Create dialog is restored.

class TabMenuExt:
    def __init__(self, ownerComp):
        self.ownerComp = ownerComp
        self.mod = ownerComp.op('tdp').module      # keep the module: the component's operators may already be gone when this runs

    def __delTD__(self):
        try:
            self.mod.uninstall(_quiet=True)
        except Exception as e:
            print('td-plugins tab menu: restore on destroy failed:', e)
'''
c.par.ext.sequence.numBlocks = 1
c.par.ext0object = "op('./ext').module.TabMenuExt(me)"
c.par.ext0name = 'TabMenuExt'
c.par.ext0promote = False
c.par.reinitextensions.pulse()

wt = c.create(td.opexecuteDAT, 'watch')
wt.text = '''# Renaming/moving the component re-points the patches (destroying it is handled by the extension in `ext`).

def onNameChange(changeOp):
    _rebind()
    return

def onPathChange(changeOp):
    _rebind()
    return

def _rebind():
    m = op('tdp').module
    if m.owner() and m.owner() != parent().path and m.C.fetch('owner', '') == m.owner():
        m.uninstall(_quiet=True)
        m.install()
'''
wt.par.op = '..'
for pn in ('precook', 'postcook', 'flagchange', 'wirechange', 'uichange', 'numchildrenchange', 'childrename', 'currentchildchange', 'extensionchange', 'parvaluechange'):
    if hasattr(wt.par, pn): setattr(wt.par, pn, False)
for pn in ('namechange', 'pathchange'):
    if hasattr(wt.par, pn): setattr(wt.par, pn, True)
print([q.name for q in wt.pars() if q.isToggle][:30])

c.save(os.path.join(ROOT, 'tox', '_raw', NAME + '.tox'))
print('saved')
