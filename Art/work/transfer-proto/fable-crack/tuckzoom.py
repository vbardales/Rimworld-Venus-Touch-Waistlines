"""Zoom on the waist, Thin_Female (or argv[1]), three facings: top row trousers alone (rule 4), bottom row tucked (rule 3).
Board: Art/work/captures/2026-11-07_tucked-zoom-<body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python tuckzoom.py [Body]
"""
import sys
import numpy as np
from PIL import Image
import crack as c1, explain5b as e5, pantsnap as pn, rules4 as r4

b = sys.argv[1] if len(sys.argv) > 1 else "Thin_Female"
rows = []
for f in ["south", "east", "north"]:
    pink = r4.lines(b, f)[0]
    mx, _ = pn.waist_line(b, f, "max")
    _, body = r4.shirt_to(b, f, pink)
    tuck = r4.tucked(b, f, pink)
    p4F, p4S = r4.trousers_to(b, f, "min")
    wb = np.zeros((512, 512, 4), np.float32); wb[body] = (.8, .8, .8, 1)
    t = e5.pil(wb); r4.draw_tucked(t, tuck); t = e5.on_bg(t)
    u = e5.pil(wb); r4.layer(u, p4F, p4S, (.45, .55, .75)); u = e5.on_bg(u)
    ys, xs = np.nonzero(tuck[0]); cy = int(np.nanmedian(mx[xs]))
    box = (xs.min() - 15, cy - 50, xs.max() + 15, cy + 50); sz = ((xs.max() - xs.min() + 30) * 3, 300)
    rows.append((u.crop(box).resize(sz, Image.NEAREST), t.crop(box).resize(sz, Image.NEAREST)))
o = Image.new("RGB", (sum(a.width for a, _ in rows) + 20, 610), (235, 235, 230)); x = 0
for a, c in rows:
    o.paste(a.convert("RGB"), (x, 0)); o.paste(c.convert("RGB"), (x, 310)); x += a.width + 10
out = rf"{c1.CAPT}\2026-11-07_tucked-zoom-{b}.png"; o.save(out); print(out)
