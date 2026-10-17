# L-system expansion + turtle interpretation. Runs ONLY when relevant parameters change.
import math
PRESETS = {
 'plant': dict(Axiom='X', Rule1='X=F+[[X]-X]-F[-FX]+X', Rule2='F=FF', Rule3='', Iterations=5, Angle=25, Lengthscale=1.0, Heading=65),
 'tree':  dict(Axiom='X', Rule1='X=F[+X][-X]', Rule2='F=F', Rule3='', Iterations=9, Angle=27, Lengthscale=0.78, Heading=90),
 'bush':  dict(Axiom='F', Rule1='F=FF+[+F-F-F]-[-F+F+F]', Rule2='', Rule3='', Iterations=4, Angle=22.5, Lengthscale=1.0, Heading=90),
 'koch':  dict(Axiom='F++F++F', Rule1='F=F-F++F-F', Rule2='', Rule3='', Iterations=4, Angle=60, Lengthscale=1.0, Heading=0),
 'dragon':dict(Axiom='FX', Rule1='X=X+YF+', Rule2='Y=-FX-Y', Rule3='', Iterations=11, Angle=90, Lengthscale=1.0, Heading=0),
}
MAX_SEGS = 16000
MAX_CHARS = 600000
DRAW = set('FGAB01')

def parse_rules(c):
    rules = {}
    for n in ('Rule1', 'Rule2', 'Rule3'):
        s = str(c.par[n].eval()).strip()
        if '=' in s:
            k, v = s.split('=', 1)
            k = k.strip()
            if len(k) == 1:
                rules[k] = v.strip()
    return rules

def rewrite(axiom, rules, iters):
    s = axiom
    for _ in range(iters):
        out = []
        n = 0
        for ch in s:
            r = rules.get(ch, ch)
            out.append(r); n += len(r)
            if n > MAX_CHARS: break
        s = ''.join(out)
        if len(s) > MAX_CHARS:
            s = s[:MAX_CHARS]; break
    return s

def turtle(s, angle, shrink, heading):
    a = math.radians(angle)
    x = y = 0.0; h = math.radians(heading); step = 1.0
    key = 0.0; depth = 0
    stack = []
    segs = []   # x0,y0,x1,y1,k0,k1,depth
    for ch in s:
        if ch in DRAW:
            nx = x + math.cos(h) * step; ny = y + math.sin(h) * step
            segs.append((x, y, nx, ny, key, key + step, depth))
            x, y, key = nx, ny, key + step
            if len(segs) >= MAX_SEGS: break
        elif ch == 'f':
            x += math.cos(h) * step; y += math.sin(h) * step
        elif ch == '+': h += a
        elif ch == '-': h -= a
        elif ch == '|': h += math.pi
        elif ch == '[':
            stack.append((x, y, h, step, key, depth))
            step *= shrink; depth += 1
        elif ch == ']':
            if stack: x, y, h, step, key, depth = stack.pop()
    return segs

def expand(c):
    rules = parse_rules(c)
    s = rewrite(str(c.par.Axiom.eval()), rules, int(c.par.Iterations.eval()))
    segs = turtle(s, float(c.par.Angle.eval()), float(c.par.Lengthscale.eval()), float(c.par.Heading.eval()))
    if not segs:
        segs = [(0, 0, 0, 0, 0, 1e-6, 0)]
    xs = [v for sg in segs for v in (sg[0], sg[2])]; ys = [v for sg in segs for v in (sg[1], sg[3])]
    cx = (min(xs) + max(xs)) / 2; cy = (min(ys) + max(ys)) / 2
    ext = max(max(xs) - min(xs), max(ys) - min(ys), 1e-9)
    kmax = max(sg[5] for sg in segs) or 1.0
    A = [['x0', 'y0', 'x1', 'y1']]; B = [['k0', 'k1', 'depth', 'pad']]
    for x0, y0, x1, y1, k0, k1, d in segs:
        A.append([round((x0 - cx) / ext, 6), round((y0 - cy) / ext, 6), round((x1 - cx) / ext, 6), round((y1 - cy) / ext, 6)])
        B.append([round(k0 / kmax, 6), round(k1 / kmax, 6), d, 0])
    for nm, rows in (('segs_a', A), ('segs_b', B)):
        t = c.op(nm); t.clear(); t.appendRows(rows)
    c.op('info').text = 'segments: %d  string: %d chars' % (len(segs), len(s))

def apply_preset(c, name):
    p = PRESETS.get(name)
    if not p: return
    c.store('lsys_busy', True)
    try:
        for k, v in p.items(): c.par[k] = v
    finally:
        c.store('lsys_busy', False)
