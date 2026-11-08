"""The whole process step by step for one body, one board per facing (Virginie 2026-11-07: 'remontre-moi Male étape par étape').
Top row, Part A (once per body and facing): A1 points, A2 lines, A3 d_min, A4 target outline, A5 rule 1.
Bottom row, Part B (vanilla ShirtBasic, rule 1): B1 source to B6 outline (fullpass.py).
Steps named as in docs/GARMENT-FIT-PROCESS.md.
Boards: Art/work/captures/2026-11-07_steps-<Body>-<facing>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python stepboard.py [Body]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, crack2, explain5b as e5, snapshirt as ss, rules4 as r4, pantsnap as pn, fullpass as fp

N = c1.N
ss.EDGE = "outer"


def part_a(body, facing):
    drawn = body in crack2.DRAWN
    _, _, _, body_a, _ = crack2.prep(body, facing, None if drawn else crack2.DONOR[body])
    Vb = c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    raw = src.copy()
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    font = ImageFont.load_default(size=15)
    tiles = []
    # A1 points: hollow = before the recalibration, filled = after
    t = e5.on_bg(e5.pil(wb)); d = ImageDraw.Draw(t)
    for i, ((ax, ay), (x, y)) in enumerate(zip(raw, src)):
        d.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), outline=(30, 60, 220), width=2)
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 220, 0), outline=(0, 0, 0))
        d.text((x + 7, y - 9), str(i + 1), fill=(0, 0, 0), font=font, stroke_width=2, stroke_fill=(255, 255, 255))
    tiles.append(t)
    # A2 lines: raw tops of boxers (blue) and panties (pink), kept part thick; min magenta, max cyan, extended
    B = pn.top_line(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png")
    P = pn.top_line(rf"{e5.WDI_TEX}\UWUnderwear\panties\panties_{body}_{facing}.png")
    bt = pn.trimmed_top(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png")
    pt = pn.trimmed_top(rf"{e5.WDI_TEX}\UWUnderwear\panties\panties_{body}_{facing}.png")
    mn, mx, span = pn.lines(body, facing)
    t = e5.on_bg(e5.pil(wb)); d = ImageDraw.Draw(t)
    cols = [x for x in range(N) if body_a[:, x].any()]
    for line, kept, col in ((B, bt, (40, 90, 255)), (P, pt, (255, 60, 200))):
        d.line([(x, float(line[x])) for x in range(N) if line[x] >= 0], fill=col, width=1)
        d.line([(x, float(kept[x])) for x in range(N) if not np.isnan(kept[x])], fill=col, width=3)
    d.line([(x, float(mn[x]) + 3) for x in cols], fill=(150, 0, 110), width=2)
    d.line([(x, float(mx[x]) - 3) for x in cols], fill=(0, 160, 200), width=2)
    tiles.append(t)
    # A3 d_min: boxers, leg line (green), d_min (red)
    dmin, j, bb, ok = r4.dmin_of(body, facing, mn)
    bx = c1.load(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png", N)
    t = e5.pil(wb); t.alpha_composite(e5.pil(bx)); t = e5.on_bg(t); d = ImageDraw.Draw(t)
    d.line([(x, float(mn[x])) for x in cols], fill=(255, 60, 200), width=2)
    for x in range(N):
        if ok[x]:
            d.rectangle((x, bb[x] - 1, x, bb[x] + 2), fill=(0, 200, 60))
    d.line((j, float(mn[j]), j, float(bb[j])), fill=(255, 0, 0), width=4)
    d.text((j + 6, float(mn[j] + bb[j]) / 2 - 8), f"d_min {dmin:.0f}", fill=(200, 0, 0), font=font, stroke_width=2, stroke_fill=(255, 255, 255))
    tiles.append(t)
    # A4 target outline: reference shirt (pale), snapped points (yellow), added points (orange), curve
    res = ss.case(body, facing)
    t = e5.pil(wb); a = res["art"].copy(); a[..., 3] *= 0.45; t.alpha_composite(e5.pil(a)); t = e5.on_bg(t); d = ImageDraw.Draw(t)
    arc = res["arc1"]; order, seeded, added, curve, _, _ = res["s1"]
    d.line([tuple(p) for p in curve], fill=(0, 0, 0), width=3)
    for k in order:
        x, y = arc[k]; colr = (255, 140, 0) if k in added else (255, 220, 0)
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=colr, outline=(0, 0, 0))
    if "sN" in res:
        oc = res["arcN"]; o2, _, _, cN, _, _ = res["sN"]
        d.line([tuple(p) for p in cN], fill=(0, 0, 0), width=3)
        for k in o2:
            x, y = oc[k]; d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 140, 0), outline=(0, 0, 0))
    tiles.append(t)
    # A5 rule 1: the hem min + d_min (green) and the outline cut there
    (F, St), _ = r4.shirt_to(body, facing, mn + dmin)
    tg = np.zeros((N, N, 4), np.float32); tg[F] = (1, 1, 1, 0.9); tg[St] = (0.02, 0.02, 0.03, 1)
    t = e5.pil(wb); t.alpha_composite(e5.pil(tg)); t = e5.on_bg(t); d = ImageDraw.Draw(t)
    d.line([(x, float(mn[x])) for x in cols], fill=(255, 60, 200), width=2)
    d.line([(x, float(mn[x] + dmin)) for x in cols], fill=(40, 200, 60), width=3)
    tiles.append(t)
    return tiles, dmin


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else "Male"
    font = ImageFont.load_default(size=14); fontb = ImageFont.load_default(size=18)
    T = 440; pad = 8; left = 10; top = 80; head = 40
    A = ["A1 points: hollow blue = before, yellow = recalibrated (top on the silhouette top)",
         "A2 lines: blue boxers top, pink panties top (thick = kept, walls dropped); dark magenta min(B,C), dark cyan max(B,C), extended",
         "A3 d_min: magenta min(B,C), green = boxers' leg line (slope <= 0.3), red = d_min",
         "A4 target outline: pale = reference shirt, yellow = her points snapped, orange = added, black = curve",
         "A5 rule 1: hem on min(B,C) + d_min (green), outline cut there"]
    Bt = ["B1 source: vanilla shirt x4, the pairs numbered", "B2 garment alone: red = the black outline removed by thickness (outer edge only; the neck hole keeps its thin line), nothing filled",
          "B3 pairs applied" + ("" if fp.NOLEGS else " (blue ring = before the legs press)"),
          ("B4 warp, no press to the hem (no legs); green = hem where B5 cuts" if fp.B56 else ("B4 point warp = the result (option pointwarp); green = rule hem" if fp.POINTWARP else "B4 relief map (Part C) = the result, no cut; green = rule hem; the pairs are not used")) if fp.NOLEGS else "B4 warp; green = hem, grey = start row y0",
          "B5 clipped at the hem, gaps filled with the fabric smoothed, shading 0.30", "B6 outline 4 px inward"]
    for f in ["south", "east", "north"]:
        ta, dmin = part_a(body, f)
        tb, info = fp.facing_row(body, f)
        im = Image.new("RGB", (left + max(len(ta), len(tb)) * (T + pad), top + 2 * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((10, 10), f"{body} {f}, step by step (docs/GARMENT-FIT-PROCESS.md). Part A: once per body and facing. Part B: vanilla {fp.G}, rule 1 (top alone).", fill=(0, 0, 0), font=fontb)
        dr.text((10, 40), f"d_min {dmin:.0f} px; {info}", fill=(0, 0, 0), font=font)
        for row, (tiles, titles) in enumerate(((ta, A), (tb, Bt))):
            y = top + row * (T + head + pad)
            for j, (p, ttl) in enumerate(zip(tiles, titles)):
                x = left + j * (T + pad)
                words = ttl.split(" "); lines, cur = [], ""
                for w in words:
                    if len(cur) + len(w) + 1 > 62:
                        lines.append(cur); cur = w
                    else:
                        cur = (cur + " " + w).strip()
                lines.append(cur)
                dr.text((x, y), "\n".join(lines[:2]), fill=(0, 0, 0), font=font)
                im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (x, y + head))
        out = rf"{c1.CAPT}\2026-11-07_steps-{body}-{f}{"" if fp.G == "ShirtBasic" else "-" + fp.G}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
