"""Pure layered (Sugiyama-style) layout for TouchDesigner networks.

No TouchDesigner dependency.  Coordinates follow TD: x right, y UP, and a node's
(x, y) is its bottom-left corner.

Node dict keys: id, w, h, x, y, docked_to (id|None), group (str|None), kind.
Edges: (src_id, dst_id), data flows src -> dst (left -> right).
"""

DEFAULTS = dict(
    col_gap=60,       # horizontal gap between columns (beyond node width)
    row_gap=60,       # vertical gap between rows (beyond node height)
    dock_gap=20,      # vertical gap between a host and its docked nodes
    band_gap=100,     # gap between the main graph and the disconnected band
    group_gap=100,    # horizontal gap between group blocks
    group_pad=30,     # padding of group boxes (left/right/bottom)
    group_title=60,   # extra padding at the top of group boxes (title bar)
    group_titles=None,  # {group: height or callable(box_width) -> height}, e.g. Annotate title + body text
    sweeps=4,         # barycenter sweeps
)


def _opts(kw):
    o = dict(DEFAULTS)
    for k, v in kw.items():
        if k not in o:
            raise TypeError("unknown layout option %r" % k)
        o[k] = v
    return o


# ---------------------------------------------------------------- graph utils

def _acyclic(ids, edges):
    """Drop self loops, duplicates and DFS back edges (feedback). Deterministic."""
    idset = set(ids)
    out = {i: [] for i in ids}
    seen = set()
    for a, b in edges:
        if a == b or a not in idset or b not in idset or (a, b) in seen:
            continue
        seen.add((a, b))
        out[a].append(b)
    state = {}
    kept = []
    for root in ids:
        if root in state:
            continue
        stack = [(root, iter(out[root]))]
        state[root] = 1
        while stack:
            n, it = stack[-1]
            adv = False
            for m in it:
                s = state.get(m, 0)
                if s == 1:
                    continue          # back edge: feedback, ignored for layout
                kept.append((n, m))
                if s == 0:
                    state[m] = 1
                    stack.append((m, iter(out[m])))
                    adv = True
                    break
            if not adv:
                state[n] = 2
                stack.pop()
    return kept


def _longest_path(ids, edges):
    """ids: ordered list. Returns ({id: layer}, kept_edges)."""
    kept = _acyclic(ids, edges)
    preds = {i: [] for i in ids}
    succs = {i: [] for i in ids}
    indeg = {i: 0 for i in ids}
    for a, b in kept:
        preds[b].append(a)
        succs[a].append(b)
        indeg[b] += 1
    layer = {i: 0 for i in ids}
    queue = [i for i in ids if indeg[i] == 0]
    while queue:
        n = queue.pop(0)
        for m in succs[n]:
            layer[m] = max(layer[m], layer[n] + 1)
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)
    return layer, kept


# ---------------------------------------------------------------- blocks

class _Block(object):
    """A host node plus the nodes docked under it, treated as one rectangle."""

    def __init__(self, host, members, dock_gap):
        self.id = host["id"]
        self.kind = host.get("kind")
        self.members = [host] + members
        self.offsets = {}     # member id -> (dx, dy) from block top-left, y down
        y = 0
        w = 0
        for i, m in enumerate(self.members):
            if i:
                y += dock_gap
            self.offsets[m["id"]] = (0, y)
            y += m["h"]
            w = max(w, m["w"])
        self.w = w
        self.h = y
        self.ox = host.get("x", 0)
        self.oy = host.get("y", 0) + host["h"]    # original top-left (y up)
        self.x = 0
        self.y = 0   # top-left of block after layout, y up


def _make_blocks(nodes, dock_gap):
    byid = {}
    for n in nodes:
        if n["id"] in byid:
            raise ValueError("duplicate node id %r" % (n["id"],))
        byid[n["id"]] = n

    def root(n):
        seen = set()
        while n.get("docked_to") in byid and n["id"] not in seen:
            seen.add(n["id"])
            n = byid[n["docked_to"]]
        return n

    kids = {}
    for n in nodes:
        r = root(n)
        if r is not n:
            kids.setdefault(r["id"], []).append(n)
    blocks = []
    owner = {}
    for n in nodes:
        if root(n) is n:
            ms = sorted(kids.get(n["id"], []), key=lambda m: (-m.get("y", 0), str(m["id"])))
            b = _Block(n, ms, dock_gap)
            blocks.append(b)
            for m in b.members:
                owner[m["id"]] = b.id
    return blocks, owner


def _reading_key(b):
    return (-b.oy, b.ox, str(b.id))


# ---------------------------------------------------------------- one scope

def _layout_scope(blocks, edges, o):
    """Lay out blocks (with block-level edges). Positions are relative: the
    layout's top-left is (0, 0) and y decreases downward. Sets b.x / b.y.
    Returns (width, height)."""
    blocks = sorted(blocks, key=_reading_key)
    ids = [b.id for b in blocks]
    byid = {b.id: b for b in blocks}
    linked = set()
    for a, b in edges:
        if a != b and a in byid and b in byid:
            linked.add(a)
            linked.add(b)
    main = [b for b in blocks if b.id in linked]
    rest = [b for b in blocks if b.id not in linked]

    width = 0
    height = 0
    if main:
        mids = [b.id for b in main]
        layer, kept = _longest_path(mids, edges)
        ncols = max(layer.values()) + 1
        for b in main:
            if b.kind == "out":
                layer[b.id] = ncols - 1
            elif b.kind == "in":
                layer[b.id] = 0
        cols = [[] for _ in range(ncols)]
        for b in main:
            cols[layer[b.id]].append(b)
        # edges between kept layer-ordered nodes (forced in/out never reverses an edge
        # in a sane network; reversed ones are simply drawn backwards)
        nbr = {i: [] for i in mids}
        for a, b in kept:
            nbr[a].append(b)
            nbr[b].append(a)

        def stack(col):
            ys = {}
            cur = 0
            for b in col:
                ys[b.id] = cur
                cur += b.h + o["row_gap"]
            return ys, max(cur - o["row_gap"], 0)

        pos = {}   # id -> center y (down positive)
        for col in cols:
            ys, _ = stack(col)
            for b in col:
                pos[b.id] = ys[b.id] + b.h / 2.0

        def sweep(order):
            for ci in order:
                col = cols[ci]
                keyed = []
                for k, b in enumerate(col):
                    ns = [n for n in nbr[b.id] if layer[n] != ci]
                    if ns:
                        bc = sum(pos[n] for n in ns) / float(len(ns))
                    else:
                        bc = pos[b.id]
                    keyed.append((bc, k, b))
                keyed.sort(key=lambda t: (t[0], t[1]))
                col[:] = [t[2] for t in keyed]
                ys, _ = stack(col)
                for b in col:
                    pos[b.id] = ys[b.id] + b.h / 2.0

        fwd = list(range(ncols))
        for _ in range(o["sweeps"]):
            sweep(fwd)
            sweep(fwd[::-1])

        colw = [max(b.w for b in c) if c else 0 for c in cols]
        heights = [stack(c)[1] for c in cols]
        height = max(heights)
        x = 0
        for ci, col in enumerate(cols):
            ys, h = stack(col)
            top = (height - h) / 2.0
            for b in col:
                b.x = x
                b.y = -(top + ys[b.id])
            x += colw[ci] + o["col_gap"]
        width = x - o["col_gap"]

    if rest:
        def rk(b):
            r = 0 if b.kind == "in" else (2 if b.kind == "out" else 1)
            return (r,) + _reading_key(b)
        rest.sort(key=rk)
        target = max(width, 1200 if not main else 0, max(b.w for b in rest))
        top = -(height + (o["band_gap"] if main else 0))
        cx = 0
        rowh = 0
        cy = top
        maxw = 0
        for b in rest:
            if cx > 0 and cx + b.w > target:
                cy -= rowh + o["row_gap"]
                cx = 0
                rowh = 0
            b.x = cx
            b.y = cy
            cx += b.w + o["col_gap"]
            maxw = max(maxw, cx - o["col_gap"])
            rowh = max(rowh, b.h)
        width = max(width, maxw)
        height = -(cy - rowh)
    return width, height


# ---------------------------------------------------------------- public

def layout(nodes, edges, return_groups=False, **kw):
    """Compute new positions.

    Returns {id: (x, y)}; with return_groups=True returns (positions, boxes)
    where boxes = {group: (x, y, w, h)} (bottom-left origin, includes padding and
    title bar) so a caller can resize Annotate COMPs.
    """
    o = _opts(kw)
    nodes = list(nodes)
    if not nodes:
        return ({}, {}) if return_groups else {}
    blocks, owner = _make_blocks(nodes, o["dock_gap"])
    bedges = []
    for a, b in edges:
        if a in owner and b in owner and owner[a] != owner[b]:
            bedges.append((owner[a], owner[b]))
    byid = {b.id: b for b in blocks}
    gof = {}
    for b in blocks:
        gof[b.id] = b.members[0].get("group")

    gnames = []
    for b in blocks:
        g = gof[b.id]
        if g not in gnames:
            gnames.append(g)
    # one scope per group (None = ungrouped)
    ext = {}
    for g in gnames:
        bs = [b for b in blocks if gof[b.id] == g]
        be = [e for e in bedges if gof[e[0]] == g and gof[e[1]] == g]
        w, h = _layout_scope(bs, be, o)
        ext[g] = (w, h, bs)

    anchor_x = min(n.get("x", 0) for n in nodes)
    anchor_y = max(n.get("y", 0) + n["h"] for n in nodes)
    boxes = {}
    if len(gnames) == 1 and gnames[0] is None:
        pass
    else:
        # order scopes left -> right by group-level data flow, then original x
        order = [g for g in gnames]
        order.sort(key=lambda g: (min(b.ox for b in ext[g][2]), str(g)))
        gedges = []
        for a, b in bedges:
            if gof[a] != gof[b]:
                gedges.append((gof[a], gof[b]))
        glayer, _ = _longest_path(order, gedges)
        order.sort(key=lambda g: (glayer[g], min(b.ox for b in ext[g][2]), str(g)))
        pad, title = o["group_pad"], o["group_title"]
        titles = o.get("group_titles") or {}
        cx = 0
        for g in order:
            w, h, bs = ext[g]
            if g is None:
                for b in bs:
                    b.x += cx
                cx += w + o["group_gap"]
            else:
                t = titles.get(g, title)
                if callable(t):          # header height may depend on the box width (wrapped text)
                    t = t(w + 2 * pad)
                t = max(title, t)
                for b in bs:
                    b.x += cx + pad
                    b.y -= t
                bw, bh = w + 2 * pad, h + pad + t
                boxes[g] = [cx, -bh, bw, bh]
                cx += bw + o["group_gap"]
                continue
                bw, bh = w + 2 * pad, h + pad + title
                boxes[g] = [cx, -bh, bw, bh]
                cx += bw + o["group_gap"]
    pos = {}
    for b in blocks:
        for m in b.members:
            dx, dy = b.offsets[m["id"]]
            pos[m["id"]] = (b.x + dx + anchor_x,
                            b.y - dy - m["h"] + anchor_y)
    out_boxes = {}
    for g, (x, y, w, h) in boxes.items():
        out_boxes[g] = (x + anchor_x, y + anchor_y, w, h)
    return (pos, out_boxes) if return_groups else pos


def text_header_height(title_h, font, text, width, wrap=True, max_width=None,
                       char_w=0.62, line_h=1.85, top_pad=12, bottom_pad=28):
    """Height (network units) an Annotate's title bar + body text occupies, so nodes can start below it.
    Calibrated against TouchDesigner's Annotate COMP: line height ~1.85 x Bodyfontsize, character width
    ~0.62 x Bodyfontsize (slightly conservative so it over- rather than under-estimates)."""
    if not text:
        return title_h + top_pad
    avail = width - 2 * 10
    if max_width:
        avail = min(avail, max_width)
    per_line = max(10, int(avail / (char_w * font)))
    lines = 0
    for para in str(text).split("\n"):
        if not wrap:
            lines += 1
            continue
        n, cur = 1, 0
        for word in para.split(" "):
            add = len(word) + (1 if cur else 0)
            if cur + add > per_line and cur:
                n += 1; cur = len(word)
            else:
                cur += add
        lines += n
    return title_h + top_pad + lines * line_h * font + bottom_pad
