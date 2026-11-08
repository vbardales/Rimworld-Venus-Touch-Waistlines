"""Redraw the artist's shirt from the points (2026-11-07, Virginie: 'replacer les points sur le bord WDI, résoudre le
mélange 1/7, puis dessiner avec des courbes de 4px d'épaisseur vers l'intérieur, pour voir si on retombe sur le dessin
de l'artiste').
Points on the OUTER edge of his ShirtBasic (outside of his black), 1 'top' on that edge at the midline, 7 'jugular
notch' on the top of the opening at the midline; curves through the points (points added where they stray over 3 px);
the shirt filled white, a 4 px black stroke drawn inward along every curve. Compared with his drawing above the hips
(his bottom is left out): green = both, red = ours only, blue = his only.
Board: Art/work/captures/2026-11-07_snap-draw.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python snapdraw.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, explain5b as e5, snapshirt as ss

N = c1.N; STROKE_IN = 4
ss.EDGE = "outer"


def render(res):
    curve = res["s1"][3]
    fill = Image.new("L", (N, N), 0); ImageDraw.Draw(fill).polygon([tuple(p) for p in curve], fill=255)
    lines = Image.new("L", (N, N), 0); dl = ImageDraw.Draw(lines)
    dl.line([tuple(p) for p in curve], fill=255, width=2 * STROKE_IN + 1)
    if "sN" in res:
        nc = res["sN"][3]
        ImageDraw.Draw(fill).polygon([tuple(p) for p in nc], fill=0)
        dl.line([tuple(p) for p in nc] + [tuple(nc[0])], fill=255, width=2 * STROKE_IN + 1)
    F = np.asarray(fill) > 127
    # the closing line across the hips is not an edge: no stroke there
    cut = float(curve[:, 1].max())
    S = (np.asarray(lines) > 127) & F
    S[int(cut) - STROKE_IN - 1:, :] &= False
    return F, S, cut


def tiles(body, facing, font):
    res = ss.case(body, facing)
    art = res["art"]; body_a = res["body_a"]
    F, S, cut = render(res)
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    # A: his drawing with the points
    a = e5.pil(wb); a.alpha_composite(e5.pil(art)); a = e5.on_bg(a); da = ImageDraw.Draw(a)
    arc = res["arc1"]
    for j in res["s1"][0]:
        x, y = arc[j]; col = (255, 140, 0) if j in res["s1"][2] else (255, 220, 0)
        da.ellipse((x - 6, y - 6, x + 6, y + 6), fill=col, outline=(0, 0, 0))
    if "sN" in res:
        for j in res["sN"][0]:
            x, y = res["arcN"][j]; da.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(255, 140, 0), outline=(0, 0, 0))
    for i, nm in enumerate(res["names"]):          # 1 and 7 labelled where they now sit
        if nm.startswith("top"):
            x, y = arc[min(res["s1"][0], key=lambda j: np.hypot(*(arc[j] - res["src"][i])))]
            da.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 220, 0), outline=(0, 0, 0)); da.text((x - 4, y - 7), "1", fill=(0, 0, 0), font=font)
    if "jugular" in res:
        x, y = res["jugular"]; da.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(0, 230, 255), outline=(0, 0, 0)); da.text((x - 4, y - 7), "7", fill=(0, 0, 0), font=font)
    # B: our redraw
    ours = np.zeros((N, N, 4), np.float32); ours[F] = (1, 1, 1, 1); ours[S] = (0.02, 0.02, 0.03, 1)
    b = e5.pil(wb); b.alpha_composite(e5.pil(ours)); b = e5.on_bg(b)
    # C: comparison above the hips
    H = ndi.binary_fill_holes(art[..., 3] > 0.5)
    if "sN" in res:
        H &= ~ndi.binary_fill_holes(res["arcN_mask"]) if "arcN_mask" in res else H
        bare = body_a & ~(art[..., 3] > 0.5); H &= ~bare
    rows = np.arange(N)[:, None] <= cut
    Hc, Fc = H & rows, F & rows
    cm = np.zeros((N, N, 4), np.float32)
    cm[Hc & Fc] = (0.55, 0.85, 0.55, 1); cm[Fc & ~Hc] = (0.95, 0.2, 0.2, 1); cm[Hc & ~Fc] = (0.2, 0.4, 1.0, 1)
    c = e5.pil(wb * np.array([1, 1, 1, 0.4])); c.alpha_composite(e5.pil(cm)); c = e5.on_bg(c)
    iou = float((Hc & Fc).sum()) / max(1, float((Hc | Fc).sum()))
    # D: his stroke vs ours, overlaid (his black in blue, ours in red)
    hs = (art[..., 3] > 0.5) & (c1.lum(art) < 0.08) & rows
    d = np.zeros((N, N, 4), np.float32); d[hs] = (0.2, 0.4, 1.0, 1); d[S] = (0.95, 0.15, 0.15, 1); d[hs & S] = (0.4, 0.1, 0.5, 1)
    dd = e5.pil(wb * np.array([1, 1, 1, 0.4])); dd.alpha_composite(e5.pil(d)); dd = e5.on_bg(dd)
    o, _, ad, _, mx, mn = res["s1"]
    txt = f"{len(o)} points ({len(ad)} added), max {mx:.1f} px; shape IoU above the hips {iou:.3f}"
    if "sN" in res:
        txt += f"; neckline {len(res['sN'][0])} points"
    return [a, b, c, dd], txt


def main():
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 300; pad = 6; left = 110; top = 74; head = 22
    titles = ["his drawing + points (1 top, 7 jugular)", "ours: curves, 4 px inward", "shape: green both, red ours, blue his", "strokes: blue his black, red ours"]
    rows = [(b, f) for f in ss.FACINGS for b in ss.BODIES]
    im = Image.new("RGB", (left + 4 * (T + pad), top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Redraw of the artist's ShirtBasic from the points on his OUTER edge (outside his black), curves stroked 4 px inward.", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "1 'top' on the outer edge at the midline; 7 'jugular notch' on the top of the opening. Compared above the hips only.", fill=(0, 0, 0), font=fontb)
    for j, t in enumerate(titles):
        dr.text((left + j * (T + pad), top - 18), t, fill=(0, 0, 0), font=font)
    for r, (b, f) in enumerate(rows):
        y = top + r * (T + head + pad)
        try:
            P, txt = tiles(b, f, font)
        except Exception as ex:
            print("FAIL", b, f, repr(ex)[:200]); continue
        dr.text((8, y + head + 6), f"{b}\n{f}", fill=(0, 0, 0), font=fontb)
        dr.text((left, y + 2), txt, fill=(0, 0, 0), font=font)
        for j, p in enumerate(P):
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
        print(b, f, txt)
    out = rf"{c1.CAPT}\2026-11-07_snap-draw.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
