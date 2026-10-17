import random
import subprocess
import sys
from pathlib import Path

import pytest

from td_organize import find_overlaps, layout, outside_groups

ROOT = Path(__file__).resolve().parent.parent


def rand_graph(seed, n=40, p=0.08, docked=True, groups=0, feedback=True):
    r = random.Random(seed)
    nodes = []
    for i in range(n):
        nodes.append(dict(id="n%d" % i, w=r.choice([100, 200, 300]), h=r.choice([80, 100, 160]),
                          x=r.randint(0, 300), y=r.randint(0, 300), docked_to=None,
                          group=None, kind=None))
    edges = [("n%d" % i, "n%d" % j) for i in range(n) for j in range(i + 1, n) if r.random() < p]
    if docked:
        for i in range(0, n, 7):
            for k in range(r.randint(1, 3)):
                nodes.append(dict(id="d%d_%d" % (i, k), w=200, h=100, x=r.randint(0, 300),
                                  y=r.randint(0, 300), docked_to="n%d" % i, group=None, kind=None))
    if groups:
        for k, nd in enumerate(nodes):
            nd["group"] = "g%d" % (k % groups) if nd["docked_to"] is None and k % 5 else None
    # feedback edges too
    if n > 5 and feedback:
        edges.append(("n%d" % (n - 1), "n0"))
    return nodes, edges


def apply(nodes, pos):
    return [dict(nd, x=pos[nd["id"]][0], y=pos[nd["id"]][1]) for nd in nodes]


@pytest.mark.parametrize("seed", range(15))
def test_no_overlaps(seed):
    nodes, edges = rand_graph(seed)
    new = apply(nodes, layout(nodes, edges))
    assert find_overlaps(new, margin=10) == []


@pytest.mark.parametrize("seed", range(8))
def test_edges_flow_left_to_right(seed):
    nodes, edges = rand_graph(seed, docked=False, feedback=False)
    pos = layout(nodes, edges)
    byid = {n["id"]: n for n in nodes}
    for a, b in edges:
        assert pos[a][0] + byid[a]["w"] < pos[b][0], (a, b)


def test_deterministic():
    nodes, edges = rand_graph(3, groups=3)
    assert layout(nodes, edges, return_groups=True) == layout(list(nodes), list(edges), return_groups=True)


def test_disconnected_below_main():
    nodes, edges = rand_graph(1, docked=False)
    linked = {i for e in edges for i in e}
    lone = [dict(id="lone%d" % i, w=200, h=100, x=0, y=0, docked_to=None, group=None, kind=None)
            for i in range(9)]
    pos = layout(nodes + lone, edges)
    main_bottom = min(pos[i][1] for i in linked)
    for n in lone:
        assert pos[n["id"]][1] + n["h"] < main_bottom
    new = apply(nodes + lone, pos)
    assert find_overlaps(new) == []


def test_docked_below_host():
    nodes = [dict(id="h", w=200, h=100, x=0, y=0, docked_to=None, group=None, kind=None),
             dict(id="a", w=200, h=100, x=0, y=0, docked_to=None, group=None, kind=None),
             dict(id="d1", w=150, h=60, x=0, y=0, docked_to="h", group=None, kind=None),
             dict(id="d2", w=150, h=60, x=0, y=0, docked_to="h", group=None, kind=None)]
    pos = layout(nodes, [("h", "a")])
    hx, hy = pos["h"]
    assert pos["d1"][0] == hx and pos["d2"][0] == hx
    assert pos["d1"][1] + 60 <= hy and pos["d2"][1] + 60 <= pos["d1"][1]
    assert find_overlaps(apply(nodes, pos)) == []


def test_in_out_columns():
    n = lambda i, k=None: dict(id=i, w=100, h=100, x=0, y=0, docked_to=None, group=None, kind=k)
    nodes = [n("in1", "in"), n("a"), n("b"), n("out1", "out"), n("out2", "out")]
    edges = [("in1", "a"), ("a", "b"), ("b", "out1"), ("a", "out2")]
    pos = layout(nodes, edges)
    assert pos["in1"][0] == min(p[0] for p in pos.values())
    assert pos["out1"][0] == pos["out2"][0] == max(p[0] for p in pos.values())


@pytest.mark.parametrize("seed", range(8))
def test_groups(seed):
    nodes, edges = rand_graph(seed, groups=3)
    pos, boxes = layout(nodes, edges, return_groups=True)
    new = apply(nodes, pos)
    assert find_overlaps(new) == []
    assert set(boxes) == {"g0", "g1", "g2"}
    assert outside_groups(new, boxes) == []
    # group boxes do not overlap each other and are left -> right separated
    bl = sorted(boxes.values())
    for a, b in zip(bl, bl[1:]):
        assert a[0] + a[2] < b[0]
    # title bar room
    for g, (bx, by, bw, bh) in boxes.items():
        top = max(n["y"] + n["h"] for n in new if n["group"] == g)
        assert by + bh - top >= 60


def test_find_overlaps_and_outside():
    a = dict(id="a", w=100, h=100, x=0, y=0)
    b = dict(id="b", w=100, h=100, x=105, y=0)   # 5px gap < margin 10
    c = dict(id="c", w=100, h=100, x=300, y=0)
    assert find_overlaps([a, b, c]) == [("a", "b")]
    assert find_overlaps([a, b, c], margin=0) == []
    d = dict(id="d", w=10, h=10, x=500, y=0, group="g")
    assert outside_groups([d], {"g": (0, 0, 100, 100)}) == ["d"]


def test_empty():
    assert layout([], []) == {}


def test_bundle_up_to_date():
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "bundle_organize.py"), "--check"],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stdout


def test_bundle_exec_separate_namespaces():
    g, l = {}, {}
    exec((ROOT / "td_organize" / "td_runtime.py").read_text(), g, l)
    assert callable(g["organize"]) and callable(g["check"])
