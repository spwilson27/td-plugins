"""Adapter tests with fake TD operators (duck typed)."""
from td_organize import td_adapter as ta


class Conn:
    def __init__(self, owner):
        self.owner = owner
        self.connections = []


class Fake:
    def __init__(self, parent, name, type="x", x=0, y=0, w=200, h=100, comp=False):
        self.parent_, self.name, self.type = parent, name, type
        self.nodeX, self.nodeY, self.nodeWidth, self.nodeHeight = x, y, w, h
        self.isCOMP = comp
        self.children = []
        self.inputConnectors = [Conn(self)]
        self.outputConnectors = [Conn(self)]
        self.dock = None
        self.enclosedOPs = []
        self.path = (parent.path if parent else "") + "/" + name
        if parent:
            parent.children.append(self)

    def wire(self, dst):
        self.outputConnectors[0].connections.append(dst.inputConnectors[0])
        dst.inputConnectors[0].connections.append(self.outputConnectors[0])


def build():
    root = Fake(None, "root", comp=True)
    root.path = "/root"
    a = Fake(root, "a")
    b = Fake(root, "b")
    c = Fake(root, "c")
    a.wire(b)
    b.wire(c)
    d = Fake(root, "d")
    d.dock = b
    lone = Fake(root, "lone")
    ann = Fake(root, "ann", type="annotate", w=50, h=50, comp=True)
    ann.enclosedOPs = [b, c]
    sub = Fake(root, "sub", comp=True)
    Fake(sub, "s1"); Fake(sub, "s2")
    return root, dict(a=a, b=b, c=c, d=d, lone=lone, ann=ann, sub=sub)


def test_organize_and_check():
    root, o = build()
    stats = ta.organize(root)
    assert stats["/root"]["overlaps_after"] == 0
    assert "/root/sub" in stats
    assert o["a"].nodeX < o["b"].nodeX < o["c"].nodeX
    assert o["d"].nodeX == o["b"].nodeX and o["d"].nodeY < o["b"].nodeY
    ann = o["ann"]
    for n in (o["b"], o["c"]):
        assert ann.nodeX <= n.nodeX and n.nodeX + n.nodeWidth <= ann.nodeX + ann.nodeWidth
        assert ann.nodeY <= n.nodeY and n.nodeY + n.nodeHeight <= ann.nodeY + ann.nodeHeight
    assert ta.check(root) == []


def test_check_finds_overlaps_and_skips_external():
    root, o = build()
    ext = Fake(root, "ext", comp=True)

    class P:
        def eval(self):
            return "x.tox"
    ext.par = type("Par", (), {"externaltox": P()})()
    Fake(ext, "e1"); Fake(ext, "e2")
    probs = ta.check(root)
    assert any(p["comp"] == "/root" for p in probs)
    assert not any(p["comp"] == "/root/ext" for p in probs)


def test_no_arrange_tag_is_skipped():
    from td_organize import td_adapter

    class C:
        isCOMP = True
        def __init__(self, tags=()):
            self.tags = set(tags); self.children = []; self.par = type('P', (), {})()
            self.OPType = 'baseCOMP'
    parent = C(); keep = C(); skip = C(tags={'no_arrange'})
    parent.children = [keep, skip]
    assert td_adapter._child_comps(parent) == [keep]
