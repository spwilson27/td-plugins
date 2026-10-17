#!/usr/bin/env python3
"""check_help.py [NAME ...] -> report custom parameters (from validation/parlist.json) missing in components/<NAME>/help.json.
About-page and Applyto help is supplied by conform.py. Exit 1 if anything is missing or help.json has unknown keys."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
pl = json.loads((ROOT / 'validation' / 'parlist.json').read_text())
CONFORM = {'Applyto'}
names = sys.argv[1:] or sorted(pl)
bad = 0
for n in names:
    hf = ROOT / 'components' / n / 'help.json'
    h = json.loads(hf.read_text()) if hf.exists() else {}
    want = {p['name'] for p in pl.get(n, [])} - CONFORM
    have_build = {p['name'] for p in pl.get(n, []) if p.get('help')}
    missing = sorted(want - set(h) - have_build)
    unknown = sorted(set(h) - want - CONFORM)
    empty = sorted(k for k, v in h.items() if not str(v).strip())
    if missing or unknown or empty:
        bad += 1
        print(f"{n}: missing={missing} unknown={unknown} empty={empty}")
print(f"{len(names) - bad}/{len(names)} complete")
sys.exit(1 if bad else 0)
