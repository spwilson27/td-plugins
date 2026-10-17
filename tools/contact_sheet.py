#!/usr/bin/env python3
"""contact_sheet.py out.png name1 name2 ...  -> grid of validation/<name>.png with labels"""
import sys
from PIL import Image, ImageDraw
out, names = sys.argv[1], sys.argv[2:]
W, H, cols = 320, 200, 4
rows = (len(names) + cols - 1) // cols
sheet = Image.new('RGB', (W * cols, (H + 18) * rows), (20, 20, 20))
d = ImageDraw.Draw(sheet)
for i, n in enumerate(names):
    x, y = (i % cols) * W, (i // cols) * (H + 18)
    try:
        im = Image.open(f'validation/{n}.png').convert('RGB'); im.thumbnail((W, H))
        sheet.paste(im, (x + (W - im.width) // 2, y + 18 + (H - im.height) // 2))
    except Exception as e:
        d.text((x + 4, y + 40), str(e)[:40], fill=(255, 80, 80))
    d.text((x + 4, y + 3), n, fill=(230, 230, 230))
sheet.save(out)
