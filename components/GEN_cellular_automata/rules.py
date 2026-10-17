import re
def bs(rule, text):
    """Return (Bmask, Smask) for a life-like rule. rule: menu index (0 = Game of Life, 4 = custom)."""
    if int(rule) != 4:
        return (1 << 3, (1 << 2) | (1 << 3))
    m = re.match(r'\s*B?\s*([0-8]*)\s*/\s*S?\s*([0-8]*)\s*$', text or '', re.I)
    if not m:
        m2 = re.match(r'\s*([0-8]*)\s*/\s*([0-8]*)\s*$', text or '')   # "23/3" S/B notation
        if not m2: return (8, 12)
        s_, b_ = m2.groups()
    else:
        b_, s_ = m.groups()
    bm = sum(1 << int(ch) for ch in set(b_)); sm = sum(1 << int(ch) for ch in set(s_))
    return (bm, sm)
