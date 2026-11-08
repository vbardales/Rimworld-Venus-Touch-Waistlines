"""Collar zoom (2026-11-07, Virginie: 'les points du col sur WDI ne semblent pas bien calés').
For the three bodies the WDI artist drew, south and north: his ShirtButton (and ShirtBasic), her WDI neck and shoulder
points (yellow, numbered as in the step 5 board), and our strokes after step 5 (red). Top of the body only, x2.
Board: Art/work/captures/2026-11-07_collar-zoom.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python collarzoom.py
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, crack2, explain5b as e5

N = c1.N; CORE = c1.CORE
CASES = [(b, f, g) for f in ("south", "north") for b in ("Fat_Female", "Hulk_Female", "Thin_Female") for g in ("ShirtButton", "ShirtBasic")]
RECAL = "recal" in sys.argv[1:]
KEEP = ("neck", "jugular", "shoulder", "top", "armpit", "upper back")


def tile(body, facing, g, font):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{g}_{vb.capitalize()}_{facing}.png")
    _, _, _, body_a, _ = crack2.prep(body, facing, None)
    src, dst, names = e5.named_pairs(body, facing)
    if RECAL:
        Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
        src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    U, V = c1.warp_field(c1.TPS(src, dst, lam=2000.0))
    wg = e5.warp(e5.peeled(Vg), U, V)
    art = c1.load(rf"{e5.WDI_TEX}\Things\Pawn\Humanlike\Apparel\{g}\{g}_{body}_{facing}.png", N)
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.82, 0.82, 0.82, 1)
    im = e5.pil(wb); im.alpha_composite(e5.pil(art)); im = e5.on_bg(im)
    ours = (wg[..., 3] > 0.5) & (c1.lum(wg) < 0.45)
    red = np.zeros((N, N, 4), np.float32); red[ours] = (0.95, 0.05, 0.05, 0.85)
    im.alpha_composite(e5.pil(red))
    ys = np.where(body_a.any(axis=1))[0]; y0 = int(ys.min()) - 12
    xs = np.where(body_a.any(axis=0))[0]; x0, x1 = int(xs.min()) - 12, int(xs.max()) + 12
    box = (x0, y0, x1, y0 + 170)
    crop = im.crop(box).resize(((x1 - x0) * 2, 340), Image.NEAREST)
    dr = ImageDraw.Draw(crop)
    for i, ((wx, wy), n) in enumerate(zip(src, names)):
        if not any(k in n for k in KEEP):
            continue
        x, y = (wx - x0) * 2, (wy - y0) * 2
        if 0 <= y < 340:
            dr.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 220, 0), outline=(0, 0, 0))
            dr.text((x - 6 if i < 9 else x - 9, y - 8), str(i + 1), fill=(0, 0, 0), font=font)
    return crop, [f"{i + 1} {n}" for i, n in enumerate(names) if any(k in n for k in KEEP)]


def main():
    font = ImageFont.load_default(size=13); fontb = ImageFont.load_default(size=16)
    tiles = [(f"{g} {b} {f}", *tile(b, f, g, font)) for b, f, g in CASES]
    W = max(t[1].width for t in tiles); H = 340; pad = 10; cols = 2
    rows = (len(tiles) + cols - 1) // cols
    im = Image.new("RGB", (cols * (W + 230 + pad) + 10, 40 + rows * (H + 40)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Collar zoom x2: the WDI artist's drawing, your WDI neck/shoulder points (yellow), our strokes after step 5 (red).", fill=(0, 0, 0), font=fontb)
    for k, (title, crop, legend) in enumerate(tiles):
        r, c = divmod(k, cols); x = 10 + c * (W + 230 + pad); y = 40 + r * (H + 40)
        dr.text((x, y), title, fill=(0, 0, 0), font=fontb)
        im.paste(crop.convert("RGB"), (x, y + 22))
        dr.text((x + crop.width + 8, y + 22), "\n".join(legend), fill=(0, 0, 0), font=font)
    out = rf"{c1.CAPT}\2026-11-07_collar-zoom" + ("-recal" if RECAL else "") + ".png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
