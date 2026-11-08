"""Grid diagnostic (Virginie 2026-11-07: 'créer un vêtement pour pawn vanilla avec une grille ... pour voir où chaque point
tombe'): a grid garment covering the vanilla body is carried through the current warp (the pairs of the full pass, the
same points left out). Row per facing: vanilla grid on the vanilla body | the same grid warped onto the WDI body, with
the pair points | local area change (blue = squeezed, red = stretched, white = as vanilla).
The grid adds no point: it shows how the warp behaves where there is none (back, profile, belly).
Board: Art/work/captures/2026-11-07_grid-<Body>[-<garment>].png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python gridboard.py [Body] nolegs [garment=X]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, explain5b as e5, fullpass as fp

N = c1.N
STEP = 16          # px at 512 (4 px at 128)


def grid_garment(Vb):
    """the vanilla body silhouette (x4) filled with a grid: light cells, dark lines every STEP px, every 4th line red"""
    a = e5.x4(Vb[..., 3] > 0.5)
    g = np.zeros((N, N, 4), np.float32)
    g[a] = (0.93, 0.93, 0.90, 1)
    yy, xx = np.mgrid[0:N, 0:N]
    line = ((yy % STEP) < 2) | ((xx % STEP) < 2)
    major = ((yy % (4 * STEP)) < 2) | ((xx % (4 * STEP)) < 2)
    g[a & line] = (0.25, 0.25, 0.30, 1)
    g[a & major] = (0.80, 0.15, 0.15, 1)
    return g


def main():
    body = next((a for a in sys.argv[1:] if "=" not in a and a not in ("nolegs", "nogroin", "fulllen", "b56")), "Male")
    font = ImageFont.load_default(size=16)
    rows = []
    for f in ["south", "east", "north"]:
        fp.facing_row(body, f); L = fp.LAST
        keep = np.array([k != (150, 150, 150) for k in L["kind"]])
        U, V = c1.warp_field(c1.TPS(L["S"][keep], L["D"][keep], lam=fp.LAM))
        G = grid_garment(L["Vb"])
        Wg = e5.warp(G, U, V)
        wb = np.zeros((N, N, 4), np.float32); wb[L["body_a"]] = (0.55, 0.55, 0.55, 1)
        vb = e5.x4(L["Vb"]); vb[..., :3] = vb[..., :3] * 0.5 + 0.2
        a = e5.pil(vb); a.alpha_composite(e5.pil(G)); a = e5.on_bg(a)
        b = e5.pil(wb); b.alpha_composite(e5.pil(Wg)); b = e5.on_bg(b); d = ImageDraw.Draw(b)
        for i, (x, y) in enumerate(L["S"]):
            if keep[i]:
                d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=L["kind"][i], outline=(0, 0, 0))
        # local area change: WDI pixel area / vanilla area it samples (x16 for 128 -> 512); 1 = as vanilla
        Uy, Ux = np.gradient(U * 4); Vy, Vx = np.gradient(V * 4)
        J = np.abs(Ux * Vy - Uy * Vx)                 # vanilla area per WDI pixel
        r = np.log2(np.clip(1.0 / np.maximum(J, 1e-6), 1 / 8, 8))   # > 0 stretched on WDI, < 0 squeezed
        inside = Wg[..., 3] > 0.5
        hm = np.zeros((N, N, 4), np.float32)
        t = np.clip(r / 1.5, -1, 1)
        hm[..., 0] = np.where(t > 0, 1, 1 + t); hm[..., 1] = 1 - np.abs(t); hm[..., 2] = np.where(t < 0, 1, 1 - t)
        hm[..., 3] = inside
        c = e5.pil(wb); c.alpha_composite(e5.pil(hm)); c = e5.on_bg(c); dc = ImageDraw.Draw(c)
        q = np.percentile(r[inside], [5, 50, 95]) if inside.any() else [0, 0, 0]
        dc.text((8, 8), f"area x{2 ** q[0]:.2f} (5%) x{2 ** q[1]:.2f} (median) x{2 ** q[2]:.2f} (95%)", fill=(255, 255, 255), font=font)
        ys, xs = np.nonzero(L["body_a"] | e5.x4(L["Vb"][..., 3] > 0.5))
        box = (max(0, xs.min() - 20), max(0, ys.min() - 20), min(N, xs.max() + 20), min(N, ys.max() + 20))
        rows.append((f, [im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for im in (a, b, c)]))
    W = max(sum(t.width for t in r_) + 40 for _, r_ in rows) + 100
    H = sum(r_[0].height + 40 for _, r_ in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}, {fp.G} pairs: vanilla grid | grid through the warp (pair points) | area change (blue squeezed, red stretched)",
            fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 46
    for f, ts in rows:
        dr.text((10, y + 4), f, fill=(0, 0, 0), font=font); x = 100
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 40
    tag = "" if fp.G == "ShirtBasic" else "-" + fp.G
    out = rf"{c1.CAPT}\2026-11-07_grid-{body}{tag}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
