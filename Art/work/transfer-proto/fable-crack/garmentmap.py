"""A real garment through the relief map (Virginie 2026-11-08, 'oui, essaie'): the vanilla garment, prepared as in B2, is
carried by the relief map (reliefmap.build, with EASE px past the body edge for the garment's ease) onto the WDI body,
next to the same garment carried by the point warp (B4).
One row per garment, per facing: relief map | point warp. No clip, no outline (B5, B6 are out).
Board: Art/work/captures/2026-11-08_garmentmap-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python garmentmap.py [Body] nolegs
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, explain5b as e5, fullpass as fp, reliefmap as rm

N = c1.N
GARMENTS = ("ShirtBasic", "LabCoat")


def main():
    body = next((a for a in sys.argv[1:] if "=" not in a and a not in ("nolegs", "nogroin", "fulllen", "b56")), "Male")
    font = ImageFont.load_default(size=16)
    maps = {f: rm.build(body, f, rm.EASE) for f in ("south", "east", "north")}
    rows = []
    for g in GARMENTS:
        fp.G = g
        tiles = []
        for f in ("south", "east", "north"):
            Mp = maps[f]
            vb = c1.VANILLA_OF[body]
            Vg = c1.load(rf"{c1.CORE}\{g}_{vb.capitalize()}_{f}.png")
            Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{f}.png")
            Gp = fp.prepared(Vg, Vb)
            B = Mp["imw"][f]
            t = e5.pil(B); t.alpha_composite(e5.pil(e5.warp(Gp, Mp["U"], Mp["V"]))); a = e5.on_bg(t)
            fp.facing_row(body, f); L = fp.LAST
            keep = np.array([k != (150, 150, 150) for k in L["kind"]])
            U2, V2 = c1.warp_field(c1.TPS(L["S"][keep], L["D"][keep], lam=fp.LAM))
            t = e5.pil(B); t.alpha_composite(e5.pil(e5.warp(Gp, U2, V2))); b = e5.on_bg(t)
            ys, xs = np.nonzero(Mp["D"] | e5.x4(Vb[..., 3] > 0.5))
            box = (max(0, xs.min() - 20), max(0, ys.min() - 20), min(N, xs.max() + 20), min(N, ys.max() + 20))
            for im, lab in ((a, "relief map"), (b, "point warp")):
                c = im.crop(box); c = c.resize((c.width * 2, c.height * 2), Image.LANCZOS)
                ImageDraw.Draw(c).text((6, 4), f"{f}: {lab}", fill=(255, 255, 255), font=font)
                tiles.append(c)
        rows.append((g, tiles))
    W = max(sum(t.width for t in r_) + 10 * len(r_) for _, r_ in rows) + 120
    H = sum(max(t.height for t in r_) + 40 for _, r_ in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: vanilla garment through the relief map (ease {rm.EASE} px) against the point warp (B4); no clip, no outline",
            fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 46
    for g, ts in rows:
        dr.text((10, y + 4), g, fill=(0, 0, 0), font=font); x = 120
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += max(t.height for t in ts) + 40
    out = rf"{c1.CAPT}\2026-11-08_garmentmap-{body}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
