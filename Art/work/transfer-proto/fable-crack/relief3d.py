"""A body in relief from its three views (Virginie 2026-11-07: 'la grille n'a pas bien pris en compte les volumes, essaie
d'imaginer ce corps en relief, tu peux réutiliser les travaux dans le dossier points').
Volume: each row is a cross-section whose WIDTH comes from the front view (south) and whose DEPTH comes from the profile
(east: back edge to front edge, so the chest, the belly and the buttocks are in it). Rows of the views are matched by
the silhouette's top and bottom.
  south: the front half of the section; at the chest rows two lobes on her points (breast apex L/R, the cleavage between
         them lower, the under-breast fold as their lower edge)
  north: the back half (the profile's back edge: shoulder blades, small of the back, buttocks)
  east : the side, its height the front view's half width
plus the body's own shading as small bumps (RELIEF px). The draped grid steps STEP px ON that surface.
Board per facing: WDI relief (lit) | WDI draped grid | vanilla relief | vanilla draped grid.
Board: Art/work/captures/2026-11-07_relief3d-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python relief3d.py [Body]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, crack2, explain5b as e5
from gridboard import STEP

N = c1.N
RELIEF = 8.0       # px: height of a drawn volume (pec, abs block) of 60 px across or more


def silhouette(img):
    """the body without its black outline: the light inside, holes filled, largest piece"""
    a = img[..., 3] > 0.5
    m = ndi.binary_fill_holes(a & (c1.lum(img) > 0.2))
    yy, xx = np.mgrid[-6:7, -6:7]
    m = ndi.binary_closing(m, structure=(xx ** 2 + yy ** 2) <= 36) & ndi.binary_fill_holes(a)   # the drawn folds bridged
    lab, n = ndi.label(m)
    if n > 1:
        m = lab == (1 + int(np.argmax(ndi.sum(m, lab, range(1, n + 1)))))
    return m & a


def rows_of(m):
    ys = np.where(m.any(axis=1))[0]
    return ys.min(), ys.max()


def extent(m, y):
    xs = np.where(m[y])[0]
    return (xs.min(), xs.max()) if len(xs) else (None, None)


def map_row(y, src_m, dst_m):
    """row y of one view to the matching row of another (silhouette top and bottom)"""
    a0, a1 = rows_of(src_m); b0, b1 = rows_of(dst_m)
    return int(round(b0 + (y - a0) / max(a1 - a0, 1) * (b1 - b0)))


def height(view, M, pts, lum):
    """M: silhouettes {'south','east','north'}; pts: named points of this view; the visible surface height"""
    m = M[view]; h = np.zeros((N, N))
    ms, me = M["south"], M["east"]
    # the profile's centre line: middle of back and front edges, per east row
    for y in np.where(m.any(axis=1))[0]:
        xl, xr = extent(m, y)
        if view in ("south", "north"):
            ye = map_row(y, m, me); zb, zf = extent(me, min(max(ye, 0), N - 1))
            if zb is None:
                continue
            zc = 0.5 * (zb + zf)
            depth = (zf - zc) if view == "south" else (zc - zb)       # front half or back half
            c = 0.5 * (xl + xr); w = max(0.5 * (xr - xl), 1.0)
            t = np.clip((np.arange(N) - c) / w, -1, 1)
            h[y] = depth * np.sqrt(1 - t ** 2)
        else:
            ys_ = map_row(y, m, ms); xl_s, xr_s = extent(ms, min(max(ys_, 0), N - 1))
            if xl_s is None:
                continue
            a = 0.5 * (xr_s - xl_s)
            c = 0.5 * (xl + xr); w = max(0.5 * (xr - xl), 1.0)
            t = np.clip((np.arange(N) - c) / w, -1, 1)
            h[y] = a * np.sqrt(1 - t ** 2)
    h = ndi.gaussian_filter(h, (6, 3))          # rows smoothed: the 128 px vanilla steps striped it
    # the two chest lobes (front): the cleavage lower than the apexes, the fold as their lower edge
    if view == "south" and all(k in pts for k in ("breast apex L", "breast apex R", "under-breast fold L")):
        (xa, ya), (xb, yb) = pts["breast apex L"], pts["breast apex R"]
        yf = pts["under-breast fold L"][1]
        r = max(0.5 * abs(xb - xa), 8.0); hv = max(yf - ya, 6.0)
        yy, xx = np.mgrid[0:N, 0:N]
        lobe = np.zeros((N, N))
        for x0 in (xa, xb):
            d2 = ((xx - x0) / (0.8 * r)) ** 2 + np.where(yy < ya, ((yy - ya) / (2.2 * hv)) ** 2, ((yy - ya) / (1.2 * hv)) ** 2)
            lobe = np.maximum(lobe, np.exp(-d2))
        valley = np.exp(-(((xx - 0.5 * (xa + xb)) / (0.35 * r)) ** 2)) * np.exp(-(((yy - ya) / (1.6 * hv)) ** 2))
        hmax = float(h[int(ya)].max()) if h[int(ya)].max() > 0 else 20.0
        h = h + 0.18 * hmax * lobe - 0.12 * hmax * valley
    # the volumes the artist separates with his drawn lines (pecs, abs blocks, shoulder blades): each zone between the lines
    # bulges on its own, the lines are where two volumes meet. The shading as height made hollows of the shadows (Virginie
    # 2026-11-07: 'les ombres font des dépressions plutôt que de mettre en avant des différences de volume')
    lines = m & (lum < 0.45)
    lines = ndi.binary_dilation(lines) & m
    zones = m & ~lines
    lab, n = ndi.label(zones)
    bump = np.zeros((N, N))
    for k in range(1, n + 1):
        z = lab == k; area = int(z.sum())
        if area < 150:
            continue
        d = np.where(z, ndi.distance_transform_edt(z), 0.0)
        dm = float(d.max())
        if dm <= 0:
            continue
        amp = RELIEF * min(1.0, np.sqrt(area) / 60.0)
        bump += amp * np.sqrt(np.clip(d / dm, 0, 1))
    bump = ndi.gaussian_filter(bump, 2)
    return (h + bump) * m


def lit(h, m):
    hy, hx = np.gradient(h)
    n = np.stack([-hx, -hy, np.ones_like(h)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    l = np.array([-0.5, -0.6, 0.62]); l /= np.linalg.norm(l)
    s = np.clip(n @ l, 0, 1)
    out = np.zeros((N, N, 4), np.float32); out[..., :3] = (0.25 + 0.75 * s)[..., None]; out[..., 3] = m
    return out


def draped(h, m):
    hy, hx = np.gradient(h)
    hx = np.clip(hx, -5, 5); hy = np.clip(hy, -5, 5)
    sx = np.sqrt(1 + hx ** 2) * m; sy = np.sqrt(1 + hy ** 2) * m
    u = np.full((N, N), np.nan); v = np.full((N, N), np.nan)
    top = rows_of(m)[0]
    for y in np.where(m.any(axis=1))[0]:
        xl, xr = extent(m, y); c = int(round(0.5 * (xl + xr)))
        cs = np.cumsum(sx[y]); u[y] = cs - cs[c]
    for x in np.where(m.any(axis=0))[0]:
        ys = np.where(m[:, x])[0]; y0 = ys.min()
        cs = np.cumsum(sy[:, x]); v[:, x] = cs - cs[y0] + (y0 - top)
    # lines where the surface coordinate is within one screen pixel of a multiple of the step (u, v smoothed first)
    w = ndi.gaussian_filter(m.astype(float), 1.5)
    minor = np.zeros((N, N), bool); major = np.zeros((N, N), bool)
    for F in (u, v):
        Fs = ndi.gaussian_filter(np.nan_to_num(F) * m, 1.5) / np.maximum(w, 1e-3)
        gy, gx = np.gradient(Fs); g = np.maximum(np.hypot(gx, gy), 1e-3)
        for step, acc in ((STEP, minor), (4 * STEP, major)):
            fr = np.mod(Fs, step); d = np.minimum(fr, step - fr) / g
            acc |= d < 0.9
    inner = ndi.binary_erosion(m)
    return minor & inner, major & inner


def views(body, vanilla):
    out = {}
    for f in ("south", "east", "north"):
        img = e5.x4(c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{f}.png")) if vanilla else \
            c1.load(rf"{crack2.WS}\Bodies\Naked_{body}_{f}.png", N)
        out[f] = img
    return out


def main():
    body = next((a for a in sys.argv[1:] if "=" not in a and a not in ("nolegs",)), "Male")
    font = ImageFont.load_default(size=16)
    side = {}
    for vanilla in (False, True):
        imgs = views(body, vanilla)
        M = {f: silhouette(imgs[f]) for f in imgs}
        for f in ("south", "east", "north"):
            s, d, names = e5.named_pairs(body, f)
            P = (d * 4) if vanilla else s
            pts = {n: tuple(P[i]) for i, n in enumerate(names)}
            h = height(f, M, pts, c1.lum(imgs[f]))
            m = M[f]
            mi, mj = draped(h, m)
            g = imgs[f].copy(); g[m & mi, :3] = (0.25, 0.25, 0.30); g[m & mj, :3] = (0.80, 0.15, 0.15)
            side[(vanilla, f)] = (e5.on_bg(e5.pil(lit(h, m))), e5.on_bg(e5.pil(g)), m)
    rows = []
    for f in ("south", "east", "north"):
        m = side[(False, f)][2] | side[(True, f)][2]
        ys, xs = np.nonzero(m)
        box = (max(0, xs.min() - 20), max(0, ys.min() - 20), min(N, xs.max() + 20), min(N, ys.max() + 20))
        ts = [side[(False, f)][0], side[(False, f)][1], side[(True, f)][0], side[(True, f)][1]]
        rows.append((f, [t.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for t in ts]))
    W = max(sum(t.width for t in r_) + 50 for _, r_ in rows) + 100
    H = sum(r_[0].height + 40 for _, r_ in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: WDI relief (lit from top left) | WDI draped grid | vanilla relief | vanilla draped grid",
            fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 46
    for f, ts in rows:
        dr.text((10, y + 4), f, fill=(0, 0, 0), font=font); x = 100
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 40
    out = rf"{c1.CAPT}\2026-11-07_relief3d-{body}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
