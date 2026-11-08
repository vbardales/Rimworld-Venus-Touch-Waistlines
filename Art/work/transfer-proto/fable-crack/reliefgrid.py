"""Grid with the body's relief (Virginie 2026-11-07: 'imagine la même grille sur Male en mappant les surfaces bombées ou
non bombées'), next to the grid carried by the warp.
Row per facing:
  1. grid through the warp, contour pairs only (her inner points left out)
  2. grid through the warp, all pairs (as the full pass)
  3. grid DRAPED on the WDI body: equal steps measured ON the surface, not on the screen
  4. the same draped grid on the vanilla body
Relief model: each row of the silhouette is a half ellipse (depth DEPTH x its half width: the torso is rounder than flat),
plus the body's own shading as small bumps (lit = raised, RELIEF px for the full contrast). A grid line every STEP px of
surface: across from the row's middle, down from the body's top. Where the surface turns away (sides, the slope of the
pecs, the shoulders) the lines close up on screen; over a bump they bow.
Board: Art/work/captures/2026-11-07_relief-grid-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python reliefgrid.py [Body] nolegs
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, crack2, explain5b as e5, fullpass as fp
from gridboard import grid_garment, STEP

N = c1.N
DEPTH = 0.55       # torso depth / width, per row
RELIEF = 10.0      # px of height for the full shading contrast


def height(mask, lum):
    h = np.zeros((N, N))
    for y in np.where(mask.any(axis=1))[0]:
        xs = np.where(mask[y])[0]
        c = 0.5 * (xs.min() + xs.max()); w = max(0.5 * (xs.max() - xs.min()), 1.0)
        t = np.clip((np.arange(N) - c) / w, -1, 1)
        h[y] = DEPTH * w * np.sqrt(1 - t ** 2)
    h = ndi.gaussian_filter(h, 4) * mask
    # the shading: lighter than its surroundings = raised (pecs, abs, buttocks), darker = a hollow or a crease
    L = np.where(mask, lum, np.nan)
    m = ndi.gaussian_filter(np.nan_to_num(L, nan=0.0), 20) / np.maximum(ndi.gaussian_filter(mask.astype(float), 20), 1e-3)
    loc = ndi.gaussian_filter(np.nan_to_num(L, nan=0.0) - m * mask, 3)
    span = max(float(np.percentile(np.abs(loc[mask]), 95)), 1e-3)
    return h + RELIEF * np.clip(loc / span, -1, 1) * mask


def draped(mask, lum):
    """line masks (minor, major) of a grid with equal steps on the surface"""
    h = height(mask, lum)
    hy, hx = np.gradient(h)
    hx = np.clip(hx, -4, 4); hy = np.clip(hy, -4, 4)
    sx = np.sqrt(1 + hx ** 2) * mask; sy = np.sqrt(1 + hy ** 2) * mask
    u = np.full((N, N), np.nan); v = np.full((N, N), np.nan)
    top = np.where(mask.any(axis=1))[0].min()
    for y in np.where(mask.any(axis=1))[0]:
        xs = np.where(mask[y])[0]; c = int(round(0.5 * (xs.min() + xs.max())))
        cs = np.cumsum(sx[y]); u[y] = cs - cs[c]
    for x in np.where(mask.any(axis=0))[0]:
        ys = np.where(mask[:, x])[0]; y0 = ys.min()
        cs = np.cumsum(sy[:, x]); v[:, x] = cs - cs[y0] + (y0 - top)
    minor = np.zeros((N, N), bool); major = np.zeros((N, N), bool)
    for F, ax in ((u, 1), (v, 0)):
        k = np.floor(np.nan_to_num(F, nan=-1e9) / STEP)
        k4 = np.floor(np.nan_to_num(F, nan=-1e9) / (4 * STEP))
        d1 = np.zeros((N, N), bool); d4 = np.zeros((N, N), bool)
        if ax == 1:
            d1[:, 1:] = k[:, 1:] != k[:, :-1]; d4[:, 1:] = k4[:, 1:] != k4[:, :-1]
        else:
            d1[1:] = k[1:] != k[:-1]; d4[1:] = k4[1:] != k4[:-1]
        minor |= d1; major |= d4
    inner = ndi.binary_erosion(mask, iterations=1)
    minor = ndi.binary_dilation(minor) & inner; major = ndi.binary_dilation(major) & inner
    return minor, major


def paint(base_rgba, mask, minor, major):
    g = base_rgba.copy()
    g[mask & minor, :3] = (0.25, 0.25, 0.30); g[mask & major, :3] = (0.80, 0.15, 0.15)
    return g


def main():
    body = next((a for a in sys.argv[1:] if "=" not in a and a not in ("nolegs", "nogroin", "fulllen", "b56")), "Male")
    font = ImageFont.load_default(size=16)
    rows = []
    for f in ["south", "east", "north"]:
        fp.facing_row(body, f); L = fp.LAST
        keep = np.array([k != (150, 150, 150) for k in L["kind"]])
        cont = keep & np.array([k != (0, 220, 255) for k in L["kind"]])
        G = grid_garment(L["Vb"])
        wb = np.zeros((N, N, 4), np.float32); wb[L["body_a"]] = (0.55, 0.55, 0.55, 1)
        tiles = []
        for sel in (cont, keep):
            U, V = c1.warp_field(c1.TPS(L["S"][sel], L["D"][sel], lam=fp.LAM))
            t = e5.pil(wb); t.alpha_composite(e5.pil(e5.warp(G, U, V))); tiles.append(e5.on_bg(t))
        # draped on the WDI body (its own texture under the lines)
        B = c1.load(rf"{crack2.WS}\Bodies\Naked_{body}_{f}.png", N)
        ma = L["body_a"]
        mi, mj = draped(ma, c1.lum(B))
        t = e5.on_bg(e5.pil(paint(B, ma, mi, mj))); tiles.append(t)
        Vb4 = e5.x4(L["Vb"]); mv = Vb4[..., 3] > 0.5
        mi, mj = draped(mv, c1.lum(Vb4))
        t = e5.on_bg(e5.pil(paint(Vb4, mv, mi, mj))); tiles.append(t)
        ys, xs = np.nonzero(ma | mv)
        box = (max(0, xs.min() - 20), max(0, ys.min() - 20), min(N, xs.max() + 20), min(N, ys.max() + 20))
        rows.append((f, [im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for im in tiles]))
    W = max(sum(t.width for t in r_) + 50 for _, r_ in rows) + 100
    H = sum(r_[0].height + 40 for _, r_ in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: warp, contour pairs only | warp, all pairs | grid draped on the WDI body (relief) | grid draped on the vanilla body",
            fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 46
    for f, ts in rows:
        dr.text((10, y + 4), f, fill=(0, 0, 0), font=font); x = 100
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 40
    out = rf"{c1.CAPT}\2026-11-07_relief-grid-{body}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
