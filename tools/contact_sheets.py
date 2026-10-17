#!/usr/bin/env python3
"""contact_sheets.py -> validation/sheet_previews.png (node-viewer previews) and validation/sheet_snippets.png (example 1 of each snippet)"""
import json
from pathlib import Path
from PIL import Image, ImageDraw
ROOT = Path(__file__).resolve().parent.parent
names = [m['name'] for m in json.loads((ROOT / 'components.json').read_text())]

def sheet(out, paths):
    W, H, cols = 240, 150, 6
    rows = (len(paths) + cols - 1) // cols
    im = Image.new('RGB', (W * cols, (H + 16) * rows), (20, 20, 20)); d = ImageDraw.Draw(im)
    for i, (label, p) in enumerate(paths):
        x, y = (i % cols) * W, (i // cols) * (H + 16)
        if p.exists():
            t = Image.open(p).convert('RGB'); t.thumbnail((W, H)); im.paste(t, (x + (W - t.width) // 2, y + 16 + (H - t.height) // 2))
        else:
            d.text((x + 4, y + 40), 'no image', fill=(160, 160, 160))
        d.text((x + 3, y + 2), label, fill=(230, 230, 230))
    im.save(out)

sheet(ROOT / 'validation' / 'sheet_previews.png', [(n, ROOT / 'validation' / f'{n}.png') for n in names])
sheet(ROOT / 'validation' / 'sheet_snippets.png', [(n, ROOT / 'validation' / 'snippets' / f'{n}_example1.png') for n in names])
print('ok')
