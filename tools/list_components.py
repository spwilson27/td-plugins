#!/usr/bin/env python3
"""Print every component name: components.json plus any components/<NAME>/meta.json not yet merged in.
Order: dependencies first (components other builds embed), then alphabetical by family."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
names = [m['name'] for m in json.loads((ROOT / 'components.json').read_text())]
for meta in sorted((ROOT / 'components').glob('*/meta.json')):
    n = meta.parent.name
    if n not in names:
        names.append(n)
names = [n for n in names if (ROOT / 'components' / n / 'build.py').exists()]
FIRST = ('TOP_fluid', 'SDF_sphere')
names.sort(key=lambda n: (n not in FIRST, n.split('_')[0], n))
print(' '.join(names))
