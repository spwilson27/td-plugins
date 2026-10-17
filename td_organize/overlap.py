"""Overlap / containment checks (pure Python, no TouchDesigner)."""


def _block_owner(nodes):
    byid = {n["id"]: n for n in nodes}
    owner = {}
    for n in nodes:
        cur, seen = n, set()
        while cur.get("docked_to") in byid and cur["id"] not in seen:
            seen.add(cur["id"])
            cur = byid[cur["docked_to"]]
        owner[n["id"]] = cur["id"]
    return owner


def find_overlaps(nodes, margin=10):
    """Pairs (id_a, id_b) of nodes whose rectangles, with `margin` of clearance
    required between them, intersect.  Nodes in the same host+docked block are
    never reported against each other, but docked children are checked against
    every other block."""
    owner = _block_owner(nodes)
    h = margin / 2.0
    items = sorted(
        ((n["x"] - h, n["x"] + n["w"] + h, n["y"] - h, n["y"] + n["h"] + h, n["id"])
        for n in nodes), key=lambda t: (t[0], str(t[4])))
    out = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if b[0] >= a[1]:
                break
            if b[2] < a[3] and a[2] < b[3] and owner[a[4]] != owner[b[4]]:
                out.append((a[4], b[4]))
    return out


def outside_groups(nodes, boxes):
    """Ids of nodes whose group box (x, y, w, h) does not fully contain them."""
    bad = []
    for n in nodes:
        g = n.get("group")
        if g is None or g not in boxes:
            continue
        x, y, w, h = boxes[g]
        if n["x"] < x or n["y"] < y or n["x"] + n["w"] > x + w or n["y"] + n["h"] > y + h:
            bad.append(n["id"])
    return bad
