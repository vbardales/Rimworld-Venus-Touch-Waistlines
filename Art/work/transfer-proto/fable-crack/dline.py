"""The D line put in place on the eight WDI bodies, three facings (2026-11-07, Virginie: 'pour les pantalons, il faut
déjà mettre la ligne D en place'). D = C' of 2026-11-05/06: per column, WDI pink line (min(B,C): the higher of the boxers
and panties tops, extended with its own slope past the sprites) minus the vanilla naked body bottom, centred, smoothed;
tables hemshift_<Body>_<facing>.txt (D) and .pink.txt (the extended pink line), Art/work/transfer-proto.
Drawn: WDI body (grey), boxers (light blue) and panties (light purple) of the WDI artist, the pink line (magenta),
the vanilla body bottom (cyan, same frame x4) and the D line = vanilla bottom moved by D (green), arrows every 32 px.
Board: Art/work/captures/2026-11-07_D-line.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python dline.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, crack2, crack5, explain5b as e5

N = c1.N
BODIES = crack5.ALL_BODIES; FACINGS = ["south", "east", "north"]


def table(body, facing, kind=""):
    p = rf"{e5.PROTO}\hemshift_{body}_{facing}{kind}.txt"
    return np.array([float(v) for v in open(p).read().strip().split(";")]) if os.path.exists(p) else None


def tile(body, facing, font):
    drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
    _, _, _, body_a, _ = crack2.prep(body, facing, donor)
    vb = c1.VANILLA_OF[body]; Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png", N)[..., 3] > 0.5
    D = table(body, facing); pink = table(body, facing, ".pink")
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    for kind, col in (("boxers", (0.62, 0.78, 0.95, 0.9)), ("panties", (0.80, 0.68, 0.95, 0.9))):
        p = rf"{e5.WDI_TEX}\UWUnderwear\{kind}\{kind}_{body}_{facing}.png"
        if os.path.exists(p):
            a = c1.load(p, N)[..., 3] > 0.5; wb[a] = col
    im = e5.on_bg(e5.pil(wb)); dr = ImageDraw.Draw(im)
    if pink is None or D is None:
        dr.text((10, 10), "no table", fill=(255, 255, 255), font=font); return im, "no table"
    xs = [x for x in range(N) if Vb[:, x].any() or body_a[:, x].any()]
    vbot = {x: float(np.where(Vb[:, x])[0].max()) for x in range(N) if Vb[:, x].any()}
    dr.line([(x, float(pink[x])) for x in xs], fill=(255, 60, 200), width=3)
    dr.line([(x, vbot[x]) for x in sorted(vbot)], fill=(0, 220, 255), width=2)
    dline = [(x, vbot[x] + float(D[x])) for x in sorted(vbot)]
    dr.line(dline, fill=(40, 200, 60), width=3)
    for x in sorted(vbot)[::32]:
        dr.line((x, vbot[x], x, vbot[x] + float(D[x])), fill=(40, 200, 60), width=1)
    mid = sorted(vbot)[len(vbot) // 2]
    off = float(pink[mid] - (vbot[mid] + D[mid]))
    return im, f"D {D[min(vbot)]:+.0f} .. {D[mid]:+.0f} .. {D[max(vbot)]:+.0f}; pink - D line at centre {off:+.0f} px"


def main():
    font = ImageFont.load_default(size=11); fontb = ImageFont.load_default(size=16)
    T = 300; pad = 6; left = 80; top = 70; head = 16
    im = Image.new("RGB", (left + len(BODIES) * (T + pad), top + 3 * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "The D line: magenta = WDI pink line min(B,C) (boxers / panties tops, extended), cyan = vanilla body bottom, green = vanilla bottom moved by D.", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Light blue = WDI boxers, light purple = WDI panties, grey = WDI body. D is centred (no offset), so the green line follows the pink one's shape, not its height.", fill=(0, 0, 0), font=fontb)
    for j, b in enumerate(BODIES):
        dr.text((left + j * (T + pad), top - 18), b, fill=(0, 0, 0), font=fontb)
    for r, f in enumerate(FACINGS):
        y = top + r * (T + head + pad); dr.text((8, y + 20), f, fill=(0, 0, 0), font=fontb)
        for j, b in enumerate(BODIES):
            try:
                t, txt = tile(b, f, font)
            except Exception as ex:
                print("FAIL", b, f, repr(ex)[:200]); continue
            dr.text((left + j * (T + pad), y), txt, fill=(0, 0, 0), font=font)
            im.paste(t.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
            print(b, f, txt)
    out = rf"{c1.CAPT}\2026-11-07_D-line.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
