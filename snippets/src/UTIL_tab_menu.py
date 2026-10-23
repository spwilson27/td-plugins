exec(open(__import__('os').path.expanduser('~/software/td-plugins/snippets/src/_snip.py')).read())

def readme(ex, name, txt, row=0, h=420):
    """Text TOP with the instructions (the OP Create dialog itself can't be captured here)."""
    t = ex.create(td.textTOP, name, row=row)
    t.par.text = txt
    t.par.outputresolution = 'custom'; t.par.resolutionw = 960; t.par.resolutionh = h
    t.par.fontsizex = 24; t.par.alignx = 'left'; t.par.aligny = 'center'
    t.par.bgcolorr = t.par.bgcolorg = t.par.bgcolorb = 0.06; t.par.bgalpha = 1
    return t

s = begin('UTIL_tab_menu')

ex = example(s, 1, 'A td-plugins tab in the Tab menu',
  'Pulse Install on ex1_UTIL_tab_menu (Status says what happened), then open the OP Create dialog\n'
  '(Tab key or double-click in any network): the last tab lists every library component by family.\n'
  'Pick one and it is created like a built-in operator. Uninstall (or deleting the component) restores the dialog.')
a = instance(ex, 'UTIL_tab_menu')
a.par.Autoinstall = False        # the snippet must not patch the dialog by itself
out(ex, 1, readme(ex, 'readme',
  '1. Pulse Install on ex1_UTIL_tab_menu\n'
  '2. Press Tab in a network: choose the "td_plugins" tab\n'
  '3. Pick e.g. glitch (TOP) or auto arrange (UTIL)\n'
  '   -> a Base COMP TOP_glitch1 with the tox is placed\n'
  'Uninstall: pulse Uninstall or delete the component.', h=520))

ex = example(s, 2, 'Link to the library instead of embedding',
  'Create Mode link makes each new component point at the library tox (External Tox), so it follows library\n'
  'updates; embed (default) puts a copy inside your project. Refresh List rescans <Library Root>/tox/*/*.tox.\n'
  'Keep this component in your project (or a startup template): the dialog is rebuilt on every launch.')
b = instance(ex, 'UTIL_tab_menu')
b.par.Autoinstall = False
b.par.Createmode = 'link'
out(ex, 2, readme(ex, 'readme2',
  'Create Mode: link\n'
  'new components get External Tox = <library>/tox/<FAMILY>/<NAME>.tox\n'
  '\n'
  'Refresh List: rescan the tox folder\n'
  'Tab Label: name of the tab (td-plugins -> td_plugins)\n'
  'out1: table of the installed entries', h=520))

finish(s)
