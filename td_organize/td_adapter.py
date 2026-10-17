"""Glue that runs INSIDE TouchDesigner.

Duck-typed against the TD OP API (no ``import td``), so it can also be unit
tested with fake ops.  Public API:

    organize(comp, recursive=True, annotate_groups=True) -> {comp_path: stats}
    check(comp, recursive=True) -> [problem dict, ...]
"""
from .layout import layout
from .overlap import find_overlaps, outside_groups
from .layout import text_header_height


def _is_annotate(o):
    return getattr(o, "type", None) == "annotate"


def _has_external_tox(o):
    try:
        p = o.par.externaltox
    except Exception:
        return False
    try:
        return bool(str(p.eval()).strip())
    except Exception:
        return False


SKIP_TAG = "no_arrange"


def _skipped(c):
    """COMPs tagged 'no_arrange' are left alone (and not recursed into), e.g. deliberately messy demo networks."""
    return SKIP_TAG in (getattr(c, "tags", None) or ())


def _child_comps(comp):
    """Child COMPs we recurse into (not Annotates, not externaltox-owned, not tagged no_arrange)."""
    out = []
    for c in comp.children:
        if getattr(c, "isCOMP", False) and not _is_annotate(c) and not _has_external_tox(c) and not _skipped(c):
            out.append(c)
    return out


def _edges(ops, paths):
    edges = []
    seen = set()

    def add(a, b):
        if a != b and a in paths and b in paths and (a, b) not in seen:
            seen.add((a, b))
            edges.append((a, b))

    for o in ops:
        for attr, forward in (("inputConnectors", False), ("outputConnectors", True),
                              ("inputCOMPConnectors", False), ("outputCOMPConnectors", True)):
            try:
                conns = getattr(o, attr, None) or []
                for c in conns:
                    for other in c.connections:
                        oo = other.owner
                        if forward:
                            add(o.path, oo.path)
                        else:
                            add(oo.path, o.path)
            except Exception:
                continue
    return edges


def _gather(comp, annotate_groups):
    kids = list(comp.children)
    annotates = [c for c in kids if _is_annotate(c)]
    ops = [c for c in kids if not _is_annotate(c)]
    paths = set(o.path for o in ops)
    group_of = {}
    if annotate_groups and annotates:
        # smallest enclosing annotate wins (innermost)
        for a in sorted(annotates, key=lambda a: (a.nodeWidth * a.nodeHeight, a.name)):
            try:
                enclosed = list(a.enclosedOPs)
            except Exception:
                enclosed = []
            for e in enclosed:
                if e.path in paths and e.path not in group_of:
                    group_of[e.path] = a.path
    nodes = []
    for o in ops:
        dock = None
        try:
            d = o.dock
            if d is not None and d.path in paths:
                dock = d.path
        except Exception:
            pass
        nodes.append(dict(id=o.path, w=o.nodeWidth, h=o.nodeHeight, x=o.nodeX, y=o.nodeY,
                          docked_to=dock, group=group_of.get(o.path),
                          kind=o.type if o.type in ("in", "out") else None))
    return nodes, _edges(ops, paths), annotates


def _par(o, name, default=None):
    p = getattr(getattr(o, "par", None), name, None)
    try:
        return p.eval() if p is not None else default
    except Exception:
        return default


def annotate_header(a):
    """Callable width -> header height (title bar + wrapped body text) for an Annotate COMP."""
    title_h = _par(a, "Titleheight", 30) or 30
    font = _par(a, "Bodyfontsize", 9) or 9
    text = _par(a, "Bodytext", "") or ""
    wrap = bool(_par(a, "Bodywordwrap", True))
    maxw = _par(a, "Bodymaxwidth", None) if _par(a, "Bodylimitwidth", False) else None
    return lambda width: text_header_height(title_h, font, text, width, wrap, maxw)


def _annotate_headers(annotates):
    return dict((a.path, annotate_header(a)) for a in annotates)


def _organize_one(comp, annotate_groups):
    nodes, edges, annotates = _gather(comp, annotate_groups)
    before = len(find_overlaps(nodes))
    pos, boxes = layout(nodes, edges, return_groups=True, group_titles=_annotate_headers(annotates))
    by_path = dict((c.path, c) for c in comp.children)
    ordered = sorted(nodes, key=lambda n: n["docked_to"] is not None)
    for n in ordered:
        o = by_path[n["id"]]
        x, y = pos[n["id"]]
        o.nodeX = int(round(x))
        o.nodeY = int(round(y))
    for a in annotates:
        b = boxes.get(a.path)
        if b is None:
            continue
        a.nodeX = int(round(b[0]))
        a.nodeY = int(round(b[1]))
        a.nodeWidth = int(round(b[2]))
        a.nodeHeight = int(round(b[3]))
    new_nodes = []
    for n in nodes:
        m = dict(n)
        m["x"], m["y"] = int(round(pos[n["id"]][0])), int(round(pos[n["id"]][1]))
        new_nodes.append(m)
    after = len(find_overlaps(new_nodes))
    return dict(nodes=len(nodes), edges=len(edges), groups=len(boxes),
                overlaps_before=before, overlaps_after=after)


def organize(comp, recursive=True, annotate_groups=True):
    """Lay out comp's children (and child COMPs when recursive)."""
    if isinstance(comp, str):
        comp = op(comp)  # noqa: F821
    stats = {}
    todo = [comp]
    while todo:
        c = todo.pop(0)
        stats[c.path] = _organize_one(c, annotate_groups)
        if recursive:
            todo.extend(_child_comps(c))
    return stats


def _check_one(comp):
    nodes, _, _ = _gather(comp, False)
    return [dict(comp=comp.path, a=a, b=b, kind="overlap")
            for a, b in find_overlaps(nodes)]


def check(comp, recursive=True):
    """Return a list of overlap problems ({comp, a, b, kind}) in the tree."""
    if isinstance(comp, str):
        comp = op(comp)  # noqa: F821
    problems = []
    todo = [comp]
    while todo:
        c = todo.pop(0)
        problems.extend(_check_one(c))
        if recursive:
            todo.extend(_child_comps(c))
    return problems
