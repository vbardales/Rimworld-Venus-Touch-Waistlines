"""Her WDI points on the WDI artist's own garments (2026-11-07, Virginie: 'mets les points jaunes sur le vêtement WDI
de l'artiste'). The three bodies he drew, three facings, his ShirtBasic and ShirtButton on the WDI body, her points
recalibrated (yellow, numbered), and the round neckline measured on his ShirtBasic (orange L, B, R, front only).
Board: Art/work/captures/2026-11-07_points-on-artist.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python artistpoints.py
"""
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import crack as c1, crack2, explain5b as e5, pseudoshirt as ps

N = c1.N
BODIES = ["Thin_Female", "Fat_Female", "Hulk_Female"]; FACINGS = ["south", "east", "north"]; GARMENTS = ["ShirtBasic", "ShirtButton"]


def tile(body, facing, g, font):
    _, _, _, body_a, _ = crack2.prep(body, facing, None)
    vb = c1.VANILLA_OF[body]; Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    im = e5.pil(wb); im.alpha_composite(e5.pil(c1.load(rf"{e5.WDI_TEX}\Things\Pawn\Humanlike\Apparel\{g}\{g}_{body}_{facing}.png", N)))
    im = e5.on_bg(im); dr = ImageDraw.Draw(im)
    op = ps.opening(body, facing, body_a) if facing == "south" else None
    if op is not None:
        cx, top_y, bot_y, hw, how = op
        for (px, py, lab) in ((cx, bot_y, "B"), (cx - hw, top_y, "L"), (cx + hw, top_y, "R")):
            dr.ellipse((px - 8, py - 8, px + 8, py + 8), fill=(255, 140, 0), outline=(0, 0, 0))
            dr.text((px - 4, py - 7), lab, fill=(0, 0, 0), font=font)
    for i, (x, y) in enumerate(src):
        dr.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(255, 220, 0), outline=(0, 0, 0))
        dr.text((x - 5 if i < 9 else x - 8, y - 7), str(i + 1), fill=(0, 0, 0), font=font)
    return im, [f"{i + 1} {n}" for i, n in enumerate(names)]


def main():
    font = ImageFont.load_default(size=11); fontb = ImageFont.load_default(size=16); fl = ImageFont.load_default(size=12)
    T = 360; pad = 8; left = 120; top = 64; LEG = 210
    cols = [(b, g) for b in BODIES for g in GARMENTS]
    im = Image.new("RGB", (left + len(cols) * (T + pad), top + 3 * (T + pad) + 330), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Your WDI points (recalibrated, yellow) on the WDI artist's own shirts. Orange L, B, R = the round neckline measured on his ShirtBasic (front).", fill=(0, 0, 0), font=fontb)
    for j, (b, g) in enumerate(cols):
        dr.text((left + j * (T + pad), top - 20), f"{b} {g}", fill=(0, 0, 0), font=fontb)
    legends = {}
    for r, f in enumerate(FACINGS):
        y = top + r * (T + pad); dr.text((8, y + 8), f, fill=(0, 0, 0), font=fontb)
        for j, (b, g) in enumerate(cols):
            t, leg = tile(b, f, g, font); legends[(b, f)] = leg
            im.paste(t.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y))
    y = top + 3 * (T + pad) + 6
    for k, f in enumerate(FACINGS):
        dr.text((left + k * 3 * (T + pad) // 2, y), f + " (Fat_Female numbering)\n" + "\n".join(legends[("Fat_Female", f)]), fill=(0, 0, 0), font=fl)
    out = rf"{c1.CAPT}\2026-11-07_points-on-artist.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
