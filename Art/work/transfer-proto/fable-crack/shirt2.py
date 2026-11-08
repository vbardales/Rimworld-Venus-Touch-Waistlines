"""Shirt, step 2 with the current settings (2026-11-07, Virginie: 'et on a pas fini le haut').
Step 1 as in snapdraw.py (points on the OUTER edge of the artist's ShirtBasic, his drawing moved up when it starts under
the WDI top, 1 on the outer edge, 7 on the top of the opening); step 2: his sides down to the waist line min(panties,
boxers) (held flat past the shared span, pantsnap.waist_line), the hem along it, points added the same way; drawn 4 px
inward, over the trousers of pantsnap.py (U bottom). Shown for the three bodies he drew, three facings.
Board: Art/work/captures/2026-11-07_shirt-step2.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python shirt2.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, explain5b as e5, snapshirt as ss, pantsnap as pn

N = c1.N; STROKE_IN = 4
ss.EDGE = "outer"


def stroke_fill(curves, holes=()):
    fill = Image.new("L", (N, N), 0); df = ImageDraw.Draw(fill)
    df.polygon([tuple(p) for p in curves], fill=255)
    for h in holes:
        df.polygon([tuple(p) for p in h], fill=0)
    lines = Image.new("L", (N, N), 0); dl = ImageDraw.Draw(lines)
    dl.line([tuple(p) for p in curves] + [tuple(curves[0])], fill=255, width=2 * STROKE_IN + 1)
    for h in holes:
        dl.line([tuple(p) for p in h] + [tuple(h[0])], fill=255, width=2 * STROKE_IN + 1)
    F = np.asarray(fill) > 127
    return F, (np.asarray(lines) > 127) & F


def shirt(body, facing):
    res = ss.case(body, facing)
    art = res["art"]; body_a = res["body_a"]
    # Virginie 2026-11-07: the shirt follows min(B,C) = the pink line, EXTENDED with its own slope (hemshift .pink.txt),
    # not held flat: at the back the held line went wrong
    waist = np.array([float(v) for v in open(rf"{e5.PROTO}\hemshift_{body}_{facing}.pink.txt").read().strip().split(";")])
    filled = ndi.binary_fill_holes(art[..., 3] > 0.5)
    contour = ss.outer_contour(filled)
    xi = np.clip(np.round(contour[:, 0]).astype(int), 0, N - 1)
    arc2 = ss.arc_of(contour, contour[:, 1] <= waist[xi])
    seeds = res["src"][res["on"]]
    seeds = seeds[seeds[:, 1] <= np.nanmax(waist)]
    s2 = ss.fit(arc2, seeds)
    a, b = arc2[-1], arc2[0]
    xs = np.linspace(a[0], b[0], max(2, int(abs(b[0] - a[0]) // 2)))
    band = np.c_[xs, waist[np.clip(np.round(xs).astype(int), 0, N - 1)]]
    h2 = ss.fit(band, [])
    holes = [res["sN"][3]] if "sN" in res else []
    F, S = stroke_fill(np.r_[s2[3], h2[3]], holes)
    return dict(res=res, waist=waist, arc2=arc2, s2=s2, band=band, h2=h2, F=F, S=S)


def trousers(body, facing):
    r = pn.case(body, facing)
    F, S = stroke_fill(np.r_[r["s"][3], r["h"][3]])
    return F, S


def main():
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 320; pad = 6; left = 110; top = 74; head = 18
    cols = ["his ShirtBasic + points (step 2)", "ours: shirt (step 2) over the trousers (U)", "ours: shirt alone"]
    rows = [(b, f) for b in ss.BODIES for f in ss.FACINGS]
    im = Image.new("RGB", (left + 3 * (T + pad), top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Shirt step 2: points on his outer edge, his sides down to min(panties, boxers) extended with its slope, hem along it (magenta); trousers to max(panties, boxers).", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Middle: our shirt over our trousers (U bottom, same waist line). Yellow = your points, orange = added, magenta = waistband.", fill=(0, 0, 0), font=fontb)
    for j, t in enumerate(cols):
        dr.text((left + j * (T + pad), top - 18), t, fill=(0, 0, 0), font=font)
    for r_, (b, f) in enumerate(rows):
        y = top + r_ * (T + head + pad)
        try:
            s = shirt(b, f); PF, PS = trousers(b, f)
        except Exception as ex:
            print("FAIL", b, f, repr(ex)[:200]); continue
        body_a = s["res"]["body_a"]
        wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
        A = e5.pil(wb); A.alpha_composite(e5.pil(s["res"]["art"])); A = e5.on_bg(A); da = ImageDraw.Draw(A)
        da.line([(x, float(s["waist"][x])) for x in range(N) if body_a[:, x].any()], fill=(255, 60, 200), width=2)
        for j in s["s2"][0]:
            x, yy = s["arc2"][j]; col = (255, 140, 0) if j in s["s2"][2] else (255, 220, 0)
            da.ellipse((x - 6, yy - 6, x + 6, yy + 6), fill=col, outline=(0, 0, 0))
        for j in s["h2"][0]:
            x, yy = s["band"][j]; da.ellipse((x - 6, yy - 6, x + 6, yy + 6), fill=(255, 60, 200), outline=(0, 0, 0))
        pants = np.zeros((N, N, 4), np.float32); pants[PF] = (0.45, 0.55, 0.75, 1); pants[PS] = (0.02, 0.02, 0.03, 1)
        sh = np.zeros((N, N, 4), np.float32); sh[s["F"]] = (1, 1, 1, 1); sh[s["S"]] = (0.02, 0.02, 0.03, 1)
        B = e5.pil(wb); B.alpha_composite(e5.pil(pants)); B.alpha_composite(e5.pil(sh)); B = e5.on_bg(B)
        C = e5.pil(wb); C.alpha_composite(e5.pil(sh)); C = e5.on_bg(C)
        o, _, ad, _, mx, _ = s["s2"]
        dr.text((8, y + head + 6), f"{b}\n{f}", fill=(0, 0, 0), font=fontb)
        dr.text((left, y + 2), f"shirt {len(o)} points ({len(ad)} added), max {mx:.1f} px; waistband {len(s['h2'][0])} points", fill=(0, 0, 0), font=font)
        for j, p in enumerate((A, B, C)):
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
        print(b, f, len(o), len(ad), round(mx, 1))
    out = rf"{c1.CAPT}\2026-11-07_shirt-step2.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
