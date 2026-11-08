"""Untucked top, two options side by side (Virginie 2026-11-07, 'je peux voir les deux ?'):
  A: hem on min(B,C) + d_min, d_min measured from min(B,C) (current rule 1)
  B: hem on max(B,C) + d_min, d_min measured from max(B,C) (her proposal)
Trousers under to min(B,C) (rule 4), top over. Orange = bottom of the boxers, green = the hem line, red = where d_min is taken.
Board: Art/work/captures/2026-11-07_untucked-AB.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python untuck2.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, explain5b as e5, pantsnap as pn, rules4 as r4

N = c1.N
BODIES = ["Thin_Female", "Fat_Female"]; FACINGS = ["south", "east", "north"]


def dmin_from(line, bb, ok):
    gap = bb - line
    j = int(np.where(ok)[0][np.argmin(gap[ok])])
    return float(gap[j]), j


def main():
    font = ImageFont.load_default(size=13); fontb = ImageFont.load_default(size=16)
    T = 300; pad = 6; left = 110; top = 60; head = 20
    im = Image.new("RGB", (left + 6 * (T + pad), top + 2 * (2 * (T + head) + pad + 10)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Untucked: A = min(B,C) + d_min from min (now), B = max(B,C) + d_min from max (proposal). Trousers to min(B,C) under, top over.", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Orange = bottom of the boxers, green = hem line, red = where d_min is taken.", fill=(0, 0, 0), font=fontb)
    for bi, b in enumerate(BODIES):
        for oi, opt in enumerate("AB"):
            y = top + bi * (2 * (T + head) + pad + 10) + oi * (T + head)
            dr.text((8, y + head + 6), f"{b}\n{opt}", fill=(0, 0, 0), font=fontb)
            for fi, f in enumerate(FACINGS):
                pink = np.array([float(v) for v in open(rf"{e5.PROTO}\hemshift_{b}_{f}.pink.txt").read().strip().split(";")])
                _, _, bb, ok = r4.dmin_of(b, f, pink)
                if opt == "A":
                    line = pink
                else:
                    line, _ = pn.waist_line(b, f, "max")
                d, j = dmin_from(line, bb, ok)
                (tF, tS), body = r4.shirt_to(b, f, line + d)
                pF, pS = r4.trousers_to(b, f, "min")
                wb = np.zeros((N, N, 4), np.float32); wb[body] = (.8, .8, .8, 1)
                t = e5.pil(wb); r4.layer(t, pF, pS, (.45, .55, .75)); r4.layer(t, tF, tS, (1, 1, 1)); t = e5.on_bg(t)
                clean = t.copy(); dd = ImageDraw.Draw(t)
                xs = [x for x in range(N) if body[:, x].any()]
                dd.line([(x, float(bb[x])) for x in xs if not np.isnan(bb[x])], fill=(255, 140, 0), width=1)
                dd.line([(x, float(line[x] + d)) for x in xs], fill=(40, 200, 60), width=1)
                dd.line((j, float(line[j]), j, float(bb[j])), fill=(255, 0, 0), width=3)
                x0 = left + (2 * fi) * (T + pad)
                dr.text((x0, y + 2), f"{f}: d_min {d:.0f} px", fill=(0, 0, 0), font=font)
                im.paste(t.resize((T, T), Image.LANCZOS).convert("RGB"), (x0, y + head))
                im.paste(clean.resize((T, T), Image.LANCZOS).convert("RGB"), (x0 + T + pad, y + head))
                print(b, opt, f, round(d, 1))
    out = rf"{c1.CAPT}\2026-11-07_untucked-AB.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
