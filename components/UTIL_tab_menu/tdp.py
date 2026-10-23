# UTIL_tab_menu module (Text DAT `tdp`, used as <comp>/tdp.module).
# Adds a "td-plugins" tab to the OP Create dialog (/ui/dialogs/menu_op) by patching it at runtime
# and restores it exactly on uninstall. See README.md ("Implementation") for the full list of patches.
import os, re, json

C = parent()                                  # the UTIL_tab_menu component
_ROOT = op('/')                               # op() needs a live context; this keeps working while we are being destroyed


def _op(path):
    return _ROOT.op(path)

MENU = '/ui/dialogs/menu_op'
MB = '# >>> td-plugins UTIL_tab_menu >>>'
ME = '# <<< td-plugins UTIL_tab_menu <<<'
BLOCK_RE = re.compile(r'[ \t]*' + re.escape(MB) + r'[^\r\n]*\r?\n.*?[ \t]*' + re.escape(ME) + r'[ \t]*\r?\n', re.S)
OWNER_RE = re.compile(re.escape(MB) + r' owner=(\S+)')
KEY_RE = re.compile(re.escape(MB) + r' owner=\S+ key=(\S+)')
STOCK = ('COMP', 'TOP', 'CHOP', 'SOP', 'POP', 'MAT', 'DAT', 'Custom', 'OP.default')
FAM_ORDER = ['TOP', 'POP', 'GEN', 'SDF', 'MAT', 'UTIL']
SDF_PRIMITIVES = ('box', 'sphere', 'torus', 'plane', 'gyroid', 'fractal', 'from_POP')
TAB_COLOR = (0.70, 0.40, 0.24)               # copper; the dialog derives hover/select/disabled shades from it
PLACE = True                                 # False in tests: skip the interactive placement

# anchors in the stock dialog that the patches rely on (checked by check() before patching)
A_COOK = '\tcurrFamily = scriptOp.inputs[0][0,0].val'
A_CREATE = 'if($custom == "custom")'
A_LAUNCH = 'cvar source = $source'
A_HELP = "\tty = op('current').text.strip()"
TEXT_TARGETS = (('script', 'nodetable/script1_callbacks'), ('create_node', 'create_node'), ('launch', 'launch_menu_op'), ('help', 'panelexec1'))


def D(rel):
    return _op(MENU + '/' + rel)


def key():
    """Internal family key (= the visible tab label): Tablabel as a legal operator name."""
    return tdu.legalName(C.par.Tablabel.eval().strip()) or 'td_plugins'


_STATE = {}          # mirror of what is needed to undo the patches when the component is already gone (parent destroyed)


def _alive():
    try:
        return bool(C.valid)
    except Exception:
        return False


def _path():
    return C.path if _alive() else _STATE.get('path', '')


def _fetch(name, default=None):
    return C.fetch(name, default) if _alive() else _STATE.get(name, default)


def status(msg):
    if _alive():
        C.par.Status = msg
    return msg


def _nl(t):
    return '\r\n' if '\r\n' in t else '\n'


# --------------------------------------------------------------------------------------------- scan
def root():
    lr = getattr(C.par, 'Libraryroot', None)       # About page (added by conform); fall back before that
    return os.path.expanduser(lr.eval() if lr is not None else (os.environ.get('TD_PLUGINS_HOME') or '~/software/td-plugins'))


def scan():
    """List the components in <Libraryroot>/tox/*/*.tox -> [dict(name, family, tox, label, description)]."""
    r = root()
    desc = {}
    try:
        for m in json.load(open(os.path.join(r, 'components.json'))):
            desc[m['name']] = m.get('description', '')
    except Exception:
        pass
    out = []
    tdir = os.path.join(r, 'tox')
    if os.path.isdir(tdir):
        for fam in sorted(os.listdir(tdir)):
            if fam.startswith('_') or fam.startswith('.'):
                continue
            fd = os.path.join(tdir, fam)
            if not os.path.isdir(fd):
                continue
            for f in sorted(os.listdir(fd)):
                if not f.endswith('.tox'):
                    continue
                name = f[:-4]
                d = desc.get(name, '')
                if not d:
                    try:
                        d = json.load(open(os.path.join(r, 'components', name, 'meta.json'))).get('description', '')
                    except Exception:
                        pass
                short = name.split('_', 1)[1] if '_' in name else name
                out.append(dict(name=name, family=fam, tox=os.path.join(fd, f), label=short.replace('_', ' '), description=d))
    rank = {f: i for i, f in enumerate(FAM_ORDER)}
    out.sort(key=lambda e: (rank.get(e['family'], 99), e['family'], e['label'].lower()))
    return out


def refresh():
    """Rescan the tox folder into the `entries` table (and `installed`/out1 when the tab is installed)."""
    ents = scan()
    t = C.op('entries')
    t.clear()
    t.appendRow(['name', 'family', 'tox', 'label', 'description'])
    for e in ents:
        t.appendRow([e['name'], e['family'], e['tox'], e['label'], e['description']])
    _list_installed(installed_by_me())
    if installed_by_me():
        fit_tab_width(C.fetch('tabkey', key()))
        try:
            D('nodetable/families').cook(force=True)
        except Exception:
            pass
    return len(ents)


def _list_installed(on):
    if not _alive():
        return
    t = C.op('installed')
    t.clear()
    t.appendRow(['name', 'family', 'tox'])
    if on:
        e = C.op('entries')
        for r in range(1, e.numRows):
            t.appendRow([e[r, 'name'].val, e[r, 'family'].val, e[r, 'tox'].val])


def _have_entries():
    e = C.op('entries')
    return e.numRows > 1 and e[0, 0].val == 'name'


def entries():
    e = C.op('entries')
    return [dict(name=e[r, 'name'].val, family=e[r, 'family'].val, tox=e[r, 'tox'].val, label=e[r, 'label'].val,
                 description=e[r, 'description'].val) for r in range(1, e.numRows)]


# ----------------------------------------------------------------------------- version guard / state
def check():
    """Return a list of reasons why the stock dialog does not look like what the patches expect."""
    bad = []
    m = _op(MENU)
    if m is None or not m.isCOMP:
        return ['%s not found' % MENU]
    need = {'insert1': 'insert', 'transpose1': 'transpose', 'colors': 'table', 'compatible': 'table', 'connectto': 'table',
            'nodetable/script1_callbacks': 'text', 'create_node': 'text', 'nodetable/layouts/master': 'base',
            'nodetable/families': 'script', 'families/family/layouts/replicator1': 'replicator', 'launch_menu_op': 'text', 'panelexec1': 'panelexec'}
    for p, t in need.items():
        o = D(p)
        if o is None:
            bad.append('missing operator ' + p)
        elif o.type != t:
            bad.append('%s is a %s DAT/OP, expected %s' % (p, o.type, t))
    if bad:
        return bad
    ts = D('transpose1')
    if not ts.inputs or ts.inputs[0].name not in ('insert1', 'tdp_insert'):
        bad.append('transpose1 is not fed by insert1')
    sc = D('nodetable/script1_callbacks').text
    if sc.count(A_COOK) != 1 and not MB in sc:
        bad.append('script1_callbacks: anchor "currFamily = scriptOp.inputs[0][0,0].val" not found once')
    if 'def cook(scriptOp):' not in sc:
        bad.append('script1_callbacks: no cook(scriptOp)')
    t = D('create_node').text           # (node_script, the Panel Execute that runs it, mirrors this text)
    if t.count(A_CREATE) != 1 and MB not in t:
        bad.append('create_node: anchor %s not found once' % A_CREATE)
    if '$operator' not in t or '$menu_pane' not in t:
        bad.append('create_node: no $operator/$menu_pane')
    t = D('launch_menu_op').text
    if t.count(A_LAUNCH) != 1 and MB not in t:
        bad.append('launch_menu_op: anchor "%s" not found once' % A_LAUNCH)
    if 'args pane type source index nodepath' not in t:
        bad.append('launch_menu_op: unexpected arguments')
    t = D('panelexec1').text
    if t.count(A_HELP) != 1 and MB not in t:
        bad.append('panelexec1: anchor "%s" not found once' % A_HELP.strip())
    if "op('help')" not in t:
        bad.append('panelexec1: no help text output')
    cm = D('compatible')
    if cm.numRows < 2 or cm.numCols < 2:
        bad.append('compatible table has an unexpected shape')
    return bad


def owner():
    """Path of the UTIL_tab_menu that patched the dialog (from the marker), '' if not patched."""
    o = D('nodetable/script1_callbacks')
    mm = OWNER_RE.search(o.text if o is not None else '')
    return mm.group(1) if mm else ''


def patched_parts():
    """Which patches are currently in /ui (names), independent of who owns them."""
    m = _op(MENU)
    parts = []
    if m is None:
        return parts
    for n, o in ((n, D(p)) for n, p in TEXT_TARGETS):
        if o is not None and MB in o.text:
            parts.append(n)
    if D('tdp_insert') is not None:
        parts.append('insert')
    return parts


def installed_by_me():
    return bool(patched_parts()) and owner() == C.path


# ------------------------------------------------------------------------------------------ patches
def _insert_after(text, anchor, block_lines):
    """Insert the block on the line after the one containing `anchor`."""
    nl = _nl(text)
    blk = MB + ' owner=%s key=%s' % (C.path, C.fetch('tabkey', '')) + nl + nl.join(block_lines) + nl + ME + nl
    i = text.index(anchor)
    j = text.find('\n', i)
    j = len(text) if j < 0 else j + 1
    if j > 0 and text[j - 1] != '\n':
        blk = nl + blk
    return text[:j] + blk + text[j:]


def _insert_before(text, anchor, block_lines):
    nl = _nl(text)
    blk = MB + ' owner=%s key=%s' % (C.path, C.fetch('tabkey', '')) + nl + nl.join(block_lines) + nl + ME + nl
    i = text.index(anchor)
    return text[:i] + blk + text[i:]


def _cook_block(k):
    return ['\tif currFamily == %r:' % k,
            '\t\ttry:',
            '\t\t\top(%r).module.cook(scriptOp, currFamily)' % (C.path + '/tdp'),
            '\t\texcept Exception as e:',
            '\t\t\tprint("td-plugins tab menu:", e)',
            '\t\treturn']


def _create_block(k):
    return ['if ($custom == "tdplugins")',
            '\tset tdp_cm = `tabnr("connectto")`',
            '\tset tdp_ct = `tab("connectto",0,0)`',
            '\tset tdp_cn = `tab("connectto",0,1)`',
            '\trun %s "$menu_pane~$operator~$tdp_nodepath~$tdp_cm~$tdp_ct~$tdp_cn~$tdp_index"' % (C.path + '/create'),
            '\texit',
            'endif']


def _launch_block():
    # remember which wire the dialog was opened from (the stock script only keeps pane/type/source)
    return ['cvar tdp_nodepath = "$nodepath"', 'cvar tdp_index = "$index"']


def _help_block(k):
    # hovering a cell: the stock valueChange looks up summaries[<tab> <label>]; ours asks the module
    return ['\tif ty == %r:' % k,
            '\t\ttry:',
            "\t\t\top('help').text = op(%r).module.help(op('op_table')[int(panelValue) + 1, 'name'], n)" % (C.path + '/tdp'),
            '\t\texcept Exception as e:',
            "\t\t\top('help').text = ' '",
            '\t\treturn']


def _strip(text):
    return BLOCK_RE.sub('', text)


def install(force=False):
    """Patch the OP Create dialog. Idempotent; refuses (Status says why) when the dialog doesn't match."""
    try:
        return _install(force)
    except Exception as e:
        try:
            uninstall(_quiet=True)
        except Exception:
            pass
        print('td-plugins tab menu: install failed:', e)
        return status('error: %s' % e)


_PARKED = {}


def park():
    """Before the project is saved: take the (large, session-only) originals out of the component's storage."""
    for n in ('orig',):
        v = C.fetch(n, None)
        if v is not None:
            _PARKED[n] = v
            C.unstore(n)


def unpark():
    for n, v in list(_PARKED.items()):
        C.store(n, v)
        del _PARKED[n]


def _install(force):
    try:
        C.ext.TabMenuExt                               # make sure the extension exists: its __delTD__ restores /ui when we are destroyed
    except Exception:
        pass
    cur = owner()
    if cur and cur != C.path:
        o = _op(cur)
        if o is not None and hasattr(o.par, 'Tablabel') and not force:
            return status('active via %s (it owns the patch; Uninstall there first, or delete it)' % cur)
        _revert_structural()                              # stale marker (owner gone): clean up first
    elif patched_parts() and not cur:
        _revert_structural()                              # partial leftovers
    if installed_by_me():
        if C.fetch('tabkey', '') == key():
            if not _have_entries():
                refresh()
            return status('installed: tab "%s", %d entries' % (key(), C.op('entries').numRows - 1))
        uninstall(_quiet=True)                           # label changed
    bad = check()
    if bad:
        msg = 'INCOMPATIBLE OP Create dialog, not patched: ' + '; '.join(bad)
        print('td-plugins tab menu: ' + msg)
        return status(msg)
    k = key()
    m = _op(MENU)
    fams = tdp_families()
    if k in fams:
        msg = 'tab name "%s" is already a TouchDesigner family; change Tablabel' % k
        print('td-plugins tab menu: ' + msg)
        return status(msg)
    if not _have_entries():
        refresh()
    # ---- remember the originals (exactly) before touching anything
    orig = {'colors': D('colors').text, 'compatible': D('compatible').text,
            'script': D('nodetable/script1_callbacks').text,
            'create_node': D('create_node').text,
            'launch': D('launch_menu_op').text,
            'help': D('panelexec1').text,
            }
    C.store('orig', orig)
    C.store('tabkey', k)
    C.store('owner', C.path)
    _STATE.update(path=C.path, orig=orig, tabkey=k, owner=C.path)
    # ---- 1. colour row (the dialog derives hover/select/disabled shades for it)
    t = D('colors')
    t.appendRow(["'%s'" % k, TAB_COLOR[0], TAB_COLOR[1], TAB_COLOR[2]])
    # ---- 2. compatible: our column + row = 'x' (all operators allowed, also when dragging a wire out of a node)
    t = D('compatible')
    nr, nc = t.numRows, t.numCols
    t.appendCol([k] + ['x'] * (nr - 1))
    t.appendRow([k] + ['x'] * nc)
    # ---- 3. scripts
    D('nodetable/script1_callbacks').text = _insert_after(orig['script'], A_COOK, _cook_block(k))
    D('create_node').text = _insert_before(orig['create_node'], A_CREATE, _create_block(k))
    D('launch_menu_op').text = _insert_after(orig['launch'], A_LAUNCH, _launch_block())
    D('panelexec1').text = _insert_after(orig['help'], A_HELP, _help_block(k))
    # ---- 4. layout for our entries (same structure as the stock per-family layouts, colour from `colors`)
    lay = D('nodetable/layouts')
    if lay.op(k) is None:
        n = lay.copy(lay.op('master'), name=k)
        n.allowCooking = True
        n.nodeX, n.nodeY = lay.op('master').nodeX + 200, lay.op('master').nodeY
    # ---- 5. the tab itself: one Insert DAT between insert1 (adds "Custom") and transpose1
    ins = m.create(insertDAT, 'tdp_insert')
    ins.par.insert = 'col'
    ins.par.at = 'end'
    ins.par.contents = k
    ins.inputConnectors[0].connect(D('insert1'))
    D('transpose1').inputConnectors[0].connect(ins)
    ins.nodeX, ins.nodeY = D('insert1').nodeX + 160, D('insert1').nodeY - 100
    ins.comment = 'td-plugins UTIL_tab_menu: adds the "%s" tab' % k
    _finish_layouts(k)
    _list_installed(True)
    try:
        D('nodetable/families').cook(force=True)
    except Exception:
        pass
    n = C.op('entries').numRows - 1
    print('td-plugins tab menu: installed tab "%s" (%d components)' % (k, n))
    return status('installed: tab "%s", %d entries' % (k, n))


def tdp_families():
    try:
        return list(families.keys()) + ['Custom']
    except Exception:
        return ['COMP', 'TOP', 'CHOP', 'SOP', 'POP', 'MAT', 'DAT', 'Custom']


def _finish_layouts(k):
    """The stock replicator builds families/family/layouts/<tab> from the family list; make sure it exists."""
    rep = D('families/family/layouts/replicator1')
    try:
        rep.cook(force=True)
    except Exception:
        pass
    lay = D('families/family/layouts')
    if lay.op(k) is None:
        n = lay.copy(lay.op('master'), name=k)
        n.allowCooking = True
        C.store('famlayout_manual', True)
    fit_tab_width(k)


def fit_tab_width(k):
    """The stock tab buttons are a fixed ~58 px wide, too narrow for 'td_plugins': let our tab grow with its label.
    (Edits only our own copy of the layout, which is removed again on uninstall.)"""
    n = D('families/family/layouts/' + k)
    if n is None:
        return
    for d in n.children:
        if d.isDAT and d.type == 'text' and 'par.Buttonsizew' in d.text and 'max(parent.Family' not in d.text:
            d.text = d.text.replace('parent.Family.par.Buttonsizew', 'max(parent.Family.par.Buttonsizew, 8 * len(family) + 14)')


def uninstall(_quiet=False):
    """Restore everything we patched, exactly."""
    cur = owner()
    if cur and cur != _path() and cur != _fetch('owner', '') and _op(cur) is not None:
        return status('not installed here (the patch belongs to %s)' % cur)
    problems = _revert(_my_orig(cur))
    if _alive():
        for n in ('orig', 'tabkey', 'owner', 'famlayout_manual'):
            C.unstore(n)
    _STATE.clear()
    _list_installed(False)
    if not _quiet:
        print('td-plugins tab menu: uninstalled' + ('' if not problems else ' (differences: %s)' % problems))
    return status('not installed' if not problems else 'uninstalled, but differs from original: %s' % problems)


def _my_orig(cur):
    """The stored originals, if they belong to the patch currently in /ui."""
    return _fetch('orig', None) if (not cur or _fetch('owner', '') == cur) else None


def _revert_structural():
    return _revert(_my_orig(owner()))


def _revert(orig):
    """Undo patches. With `orig` (stored texts) the restore is exact; without, the patches are stripped structurally."""
    problems = []
    m = _op(MENU)
    if m is None:
        return problems
    k = _fetch('tabkey', None) or ''
    if not k:
        mm = KEY_RE.search(D('nodetable/script1_callbacks').text or '')
        k = mm.group(1) if mm else ''
    if k in STOCK:
        k = ''
    cur = D('current')
    lt = D('last')
    was_selected = bool(k) and ((cur is not None and cur.text.strip() == k) or (lt is not None and lt.numRows and lt.numCols and lt[0, 0].val == k))
    # tab: transpose1 back to insert1, drop the Insert DAT
    ins = D('tdp_insert')
    if ins is not None:
        if D('transpose1') is not None and D('insert1') is not None:
            D('transpose1').inputConnectors[0].connect(D('insert1'))
        ins.destroy()
    # if our tab was the active one, go back to the first tab (the dialog does this itself on start)
    if was_selected:
        try:
            lt = D('last')
            if lt is not None and lt.numRows and lt.numCols and lt[0, 0].val == k:
                lt[0, 0].val = ''
            D('families/family').click(0, 1)
        except Exception as e:
            print('td-plugins tab menu: could not reset the active tab:', e)
    # layouts we created/that the replicator made for the tab
    for rel in ('nodetable/layouts', 'families/family/layouts'):
        if k and D(rel) is not None and D(rel).op(k) is not None:
            try:
                D(rel).cook(force=True)
                D('families/family/layouts/replicator1').cook(force=True)
            except Exception:
                pass
    for rel in ('nodetable/layouts', 'families/family/layouts'):
        if k and D(rel) is not None and D(rel).op(k) is not None:
            D(rel).op(k).destroy()
    # tables
    pairs = [('colors', 'colors', D('colors')), ('compatible', 'compatible', D('compatible'))]
    for name, okey, t in pairs:
        if t is None:
            continue
        if orig and orig.get(okey) is not None:
            t.text = orig[okey]
        elif k:
            _drop_table_key(t, k)
    # texts
    for name, o in ((n, D(p)) for n, p in TEXT_TARGETS):
        if o is None or MB not in o.text:
            continue
        if orig and orig.get(name) is not None:
            o.text = orig[name]
        else:
            if MB in o.text:
                o.text = _strip(o.text)
    if orig:
        for name, o in [('colors', D('colors')), ('compatible', D('compatible'))] + [(n, D(p)) for n, p in TEXT_TARGETS]:
            if o is not None and orig.get(name) is not None and o.text != orig[name]:
                problems.append(name)
    try:
        D('nodetable/families').cook(force=True)
    except Exception:
        pass
    return problems


def _drop_table_key(t, k):
    rows = [[c.val for c in t.row(r)] for r in range(t.numRows)]
    if not rows:
        return
    hdr = rows[0]
    drop = hdr.index(k) if k in hdr else None
    out = []
    for r in rows:
        if r and r[0] in (k, "'%s'" % k):
            continue
        out.append([v for i, v in enumerate(r) if i != drop])
    t.clear()
    for r in out:
        t.appendRow(r)


# ----------------------------------------------------------------------------- the tab's content
def cook(scriptOp, k):
    """Fill the dialog's script DAT (same columns as the stock cook) for the td-plugins tab."""
    rows = max(int(scriptOp.par.Rows.eval() or 1), 1)
    q = scriptOp.par.Search.eval().lower().strip()
    ents = entries()
    fams = [f for f in FAM_ORDER if any(e['family'] == f for e in ents)]
    fams += sorted({e['family'] for e in ents} - set(FAM_ORDER))
    # One continuous list (headings inline, a blank row before each heading): the dialog is only ~6 columns wide,
    # so unlike the COMP tab we don't start every group in a new column.
    count = 0
    for gi, f in enumerate(fams):
        if count:
            scriptOp.appendRow()
            count += 1
            if count % rows == rows - 1:                  # don't leave a heading alone at the bottom of a column
                scriptOp.appendRow()
                count += 1
        scriptOp.appendRow(['', f, 'layouts/%s/defLabel' % k])
        count += 1
        for e in (x for x in ents if x['family'] == f):
            name, label, dsc = e['name'], e['label'], e['description']
            lname, llab = name.lower(), label.lower()
            score = 0
            if not q:
                score = 1
            elif q == llab:
                score = 5
            elif q == lname:
                score = 4
            elif llab.startswith(q) or lname.startswith(q):
                score = 3
            elif q in llab.split(' ') or any(w.startswith(q) for w in llab.split(' ')):
                score = 2
            elif q in lname or q in f.lower() + ' ' + llab:
                score = 1.5
            elif q in dsc.lower():
                score = 1
            filt = f in ('TOP', 'POP', 'CHOP', 'SOP') or (f == 'SDF' and not name.split('_', 1)[-1].startswith(SDF_PRIMITIVES))
            kind = 'defFilter' if filt else 'defGenerator'
            if q and score == 0:
                kind += 'Disable'
            scriptOp.appendRow([name, label, 'layouts/%s/%s' % (k, kind), gi, 0, 1 if filt else 0, 'tdplugins', 0, '', 1, score, k, ''])
            count += 1
    if count % rows:
        for _ in range(rows - count % rows):
            scriptOp.appendRow()


FAM_HELP = {'TOP': 'TOP_: image filters and effects (in1 = image)', 'POP': 'POP_: geometry (POP) filters',
            'GEN': 'GEN_: generators, no required input', 'SDF': 'SDF_: signed distance field building blocks (wire = DAT)',
            'MAT': 'MAT_: materials (out1 = Out MAT)', 'UTIL': 'UTIL_: utilities that act on your network'}


def help(name, label):
    """One-line summary + inputs/outputs for the dialog's description area (hover). Headings get a family blurb."""
    name = getattr(name, 'val', name) or ''
    label = getattr(label, 'val', label) or ''
    if not name:
        return FAM_HELP.get(label, ' ')
    e = next((x for x in entries() if x['name'] == name), None)
    if e is None:
        return ' '
    txt = e['description'] or name
    try:
        lb = json.load(open(os.path.join(root(), 'components', name, 'labels.json')))
    except Exception:
        try:
            lb = json.load(open(os.path.join(root(), 'io_labels.json'))).get(name, {})
        except Exception:
            lb = {}
    ins = ', '.join(v for k, v in sorted((lb.get('inputs') or {}).items()))
    outs = ', '.join(v for k, v in sorted((lb.get('outputs') or {}).items()))
    io = '  '.join(x for x in (('In: ' + ins) if ins else '', ('Out: ' + outs) if outs else '') if x)
    return '%s (%s)\n%s%s' % (e['label'], name, txt, ('\n' + io) if io else '')


# ------------------------------------------------------------------------------------- creating
def _pane(name):
    for p in ui.panes:
        if str(p.name) == name or str(p.id) == name:
            return p
    for p in ui.panes:
        if p.type == PaneType.NETWORKEDITOR:
            return p
    return None


def _free_name(net, base):
    i = 1
    while net.op('%s%d' % (base, i)) is not None:
        i += 1
    return '%s%d' % (base, i)


def _tox_par(path):
    """externaltox value: an expression honouring TD_PLUGINS_HOME when the file is under the default root."""
    r = os.path.expanduser('~/software/td-plugins')
    if path.startswith(r + '/'):
        return ("(__import__('os').environ.get('TD_PLUGINS_HOME') or __import__('os').path.expanduser('~/software/td-plugins'))"
                " + %r" % path[len(r):], True)
    return path, False


def create(args):
    """Entry point run by the patched dialog (tscript `run`): 'pane~operator~nodepath~connectmode~connecttype~connector'."""
    if isinstance(args, (list, tuple)):
        args = args[0] if args else ''
    p = (str(args).split('~') + [''] * 7)[:7]
    return create_component(p[1], pane=p[0], nodepath=p[2], connect=(p[3] not in ('', '0'), p[4], p[5], p[6]))


def create_component(name, pane=None, nodepath='', connect=(False, '', '', ''), network=None, mode=None):
    ent = next((e for e in entries() if e['name'] == name), None)
    if ent is None:
        ui.status = 'td-plugins: unknown component %s' % name
        return None
    if not os.path.isfile(ent['tox']):
        ui.status = 'td-plugins: %s not found (Refresh?)' % ent['tox']
        print('td-plugins tab menu: missing', ent['tox'])
        return None
    pn = pane if hasattr(pane, 'owner') else _pane(pane or '')
    net = network or (pn.owner if pn is not None else None)
    if net is None or not net.isCOMP:
        net = _op('/project1') or _op('/')
    mode = mode or C.par.Createmode.eval()
    ui.undo.startBlock('Create %s' % ent['label'])
    try:
        new = _free_name(net, name)
        if mode == 'link':
            comp = net.create(baseCOMP, new)
            v, isexpr = _tox_par(ent['tox'])
            if isexpr:
                comp.par.externaltox.expr = v
            else:
                comp.par.externaltox = v
            comp.par.enableexternaltoxpulse.pulse()
        else:
            comp = net.loadTox(ent['tox'])
            comp.name = new
        _wire(comp, nodepath, connect)
        comp.selected = True
        comp.current = True
        if pn is not None:
            try:
                _op(MENU).par.winclose.pulse()
            except Exception:
                pass
    finally:
        ui.undo.endBlock()
    if pn is not None and PLACE:
        try:
            pn.placeOPs([comp], undoName='Place %s' % ent['label'])
        except Exception as e:
            print('td-plugins tab menu: placement failed, centred instead:', e)
            comp.nodeCenterX, comp.nodeCenterY = pn.x, pn.y
    elif pn is not None:
        comp.nodeCenterX, comp.nodeCenterY = pn.x, pn.y
    return comp


def _fam_of(comp, kind):
    """Family of the first In/Out operator inside a component ('' if none)."""
    n = comp.op('in1' if kind == 'in' else 'out1')
    return n.family if n is not None else ''


def _wire(comp, nodepath, connect):
    """Best effort: connect the new component to the connector the dialog was opened from.
    connect = (opened_from_wire, connector_family, 'output'|'input', connector_index)."""
    on, ctype, cdir, idx = connect
    src = _op(nodepath) if nodepath and nodepath not in ('-', '') else None
    if not on or src is None:
        return False
    try:
        i = int(idx or 0)
    except ValueError:
        i = 0
    try:
        if cdir == 'output':                       # wire dragged out of src's output -> our first input
            if comp.inputConnectors and _fam_of(comp, 'in') == ctype and i < len(src.outputConnectors):
                src.outputConnectors[i].connect(comp.inputConnectors[0])
                return True
        else:                                      # wire dragged out of src's input -> our first output feeds it
            if comp.outputConnectors and _fam_of(comp, 'out') == ctype and i < len(src.inputConnectors):
                comp.outputConnectors[0].connect(src.inputConnectors[i])
                return True
    except Exception as e:
        print('td-plugins tab menu: could not wire:', e)
    return False
