# helper module for type_overlay (lives in a Text DAT named 'lib'; call via op('lib').module.fn())
import random, math

def _c(): return parent()

def W(): return int(op('res')['w'].eval())
def H(): return int(op('res')['h'].eval())

def mod(ch):
    m = op('modin')
    return float(m[ch].eval()) if (m and m.numChans and m[ch] is not None) else 0.0

def seconds():
    return absTime.seconds

def tick(salt=0):
    """integer tick index at Tickrate ticks per second"""
    return int(absTime.seconds * _c().par.Tickrate.eval())

def timecode():
    fps = max(1, _c().par.Fps.eval())
    s = seconds()
    f = int(s * fps)
    return '%02d:%02d:%02d:%02d' % (f // (fps * 3600) % 100, f // (fps * 60) % 60, f // fps % 60, f % fps), f

def split_title():
    t = _c().par.Title.eval().replace('\\n', '\n')
    lines = t.split('\n')
    bold = [(ln[1:] or ' ') if ln.startswith('*') else ' ' for ln in lines]
    reg = [' ' if ln.startswith('*') else (ln if ln else ' ') for ln in lines]
    return '\n'.join(bold), '\n'.join(reg)

def title_bold(): return split_title()[0]
def title_reg():  return split_title()[1]

def tl():
    tc, f = timecode()
    p = _c().par
    return ' \nTC  %s\nFRM %06d\n%d FPS  %dx%d' % (tc, f, p.Fps.eval(), W(), H())

def rec():
    p = _c().par
    on = int(seconds() * 2) % 2 == 0
    return ('\u25cf' if on else ' ') + ' REC\n \n \n '

def cols(salt, n, fmt_idx=0):
    t = tick()
    r = random.Random(t * 7919 + salt * 104729)
    rows = []
    for i in range(n):
        a = r.randint(0, 9999); b = r.random() * 100; c = r.randint(0, 255)
        rows.append('%04d %7.3f %02X' % (a, b, c))
    return '\n'.join(rows)

def tr():
    n = int(_c().par.Telelines.eval())
    return cols(1, n)

def bl():
    t = tick()
    r = random.Random(t * 31 + 7)
    x = r.uniform(-1, 1); y = r.uniform(-1, 1); z = r.uniform(0, 1)
    p = _c().par
    return 'X %+.4f\nY %+.4f\nZ %+.4f' % (x, y, z)

def br():
    p = _c().par
    return 'T %.2fs\nRATE %.1f/s\nIDX %05d' % (absTime.seconds, p.Tickrate.eval(), tick() % 100000)

# ---- layout presets: (x, y, alignx, aligny) in 0..1 fractions (margin added via m) ----
LAYOUTS = ['rendah', 'center', 'poster', 'minimal', 'data']
# per element per layout: (x, y, ax, ay, size_mult, visible)
TABLE = {
 'title': {'rendah': (0.0, 0.0, 'left', 'bottom', 1.0, 1), 'center': (0.5, 0.5, 'center', 'center', 1.2, 1),
           'poster': (0.0, 1.0, 'left', 'top', 1.6, 1), 'minimal': (0.0, 0.0, 'left', 'bottom', 0.35, 1), 'data': (0.0, 1.0, 'left', 'top', 0.5, 1)},
 'tl': {'rendah': (0.0, 1.0, 'left', 'top', 1, 1), 'center': (0.0, 1.0, 'left', 'top', 1, 1), 'poster': (0.0, 0.0, 'left', 'bottom', 1, 1),
        'minimal': (0.0, 1.0, 'left', 'top', 1, 1), 'data': (0.0, 0.5, 'left', 'center', 1, 1)},
 'rec': {'rendah': (0.0, 1.0, 'left', 'top', 1, 1), 'center': (0.0, 1.0, 'left', 'top', 1, 1), 'poster': (0.0, 0.0, 'left', 'bottom', 1, 1),
         'minimal': (0.0, 1.0, 'left', 'top', 1, 1), 'data': (0.0, 0.5, 'left', 'center', 1, 1)},
 'tr': {'rendah': (1.0, 1.0, 'right', 'top', 1, 1), 'center': (1.0, 1.0, 'right', 'top', 1, 1), 'poster': (1.0, 1.0, 'right', 'top', 1, 1),
        'minimal': (1.0, 1.0, 'right', 'top', 1, 0), 'data': (1.0, 1.0, 'right', 'top', 1, 1)},
 'bl': {'rendah': (0.0, 0.0, 'left', 'bottom', 1, 0), 'center': (0.0, 0.0, 'left', 'bottom', 1, 1), 'poster': (0.0, 0.0, 'left', 'bottom', 1, 0),
        'minimal': (0.0, 0.0, 'left', 'bottom', 1, 0), 'data': (0.0, 0.0, 'left', 'bottom', 1, 1)},
 'br': {'rendah': (1.0, 0.0, 'right', 'bottom', 1, 1), 'center': (1.0, 0.0, 'right', 'bottom', 1, 1), 'poster': (1.0, 0.0, 'right', 'bottom', 1, 1),
        'minimal': (1.0, 0.0, 'right', 'bottom', 1, 1), 'data': (1.0, 0.0, 'right', 'bottom', 1, 1)},
}

def lay(elem):
    return TABLE[elem][_c().par.Layout.eval()]

def pos(elem, axis):
    x, y, ax, ay, sz, vis = lay(elem)
    m = _c().par.Margin.eval()
    W_ = W(); H_ = H()
    if axis == 'x':
        return (m * H_ / W_) * (1 - 2 * x)
    return m * (1.8 if elem == 'title' else 1.0) * (1 - 2 * y)

def stack_offset(elem):
    """Vertical nudge so tl and rec do not collide, etc."""
    return 0.0

def align(elem, which):
    return lay(elem)[2 if which == 'x' else 3]

def vis(elem):
    return lay(elem)[5]

def size(elem):
    p = _c().par
    m = p.Modamount.eval()
    if elem == 'title':
        return H() * p.Titlesize.eval() * lay('title')[4] * (1 + m * 0.3 * mod('band1'))
    return H() * 0.0165 * p.Telesize.eval() * (1 + m * 0.4 * mod('band2'))
