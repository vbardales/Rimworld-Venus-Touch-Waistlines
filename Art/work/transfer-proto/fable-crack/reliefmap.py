"""Vanilla -> flat -> WDI relief (Virginie 2026-11-07: 'partir d'une grille orthogonale SUR VANILLA, la passer en plate et la
repasser sur le relief WDI').
Each body gets surface coordinates from its relief (relief3d.height): u across each row from its middle, v down each
column, both measured ON the surface. Made comparable between the two bodies:
  across: u / the row's half surface width on that side  -> -1 .. +1 (left edge to right edge)
  down  : v laid between her landmarks common to both bodies (same names, rows of her study), piecewise linear
Every WDI pixel then takes the vanilla pixel with the same (across, down): a dense map, no point pairs.
Row per facing: orthogonal grid on vanilla | the same grid laid flat (across, down) | carried onto the WDI relief by the
map | carried by the current point warp (for comparison).
Board: Art/work/captures/2026-11-07_reliefmap-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python reliefmap.py [Body] nolegs
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import crack as c1, explain5b as e5, relief3d as r3, fullpass as fp
from gridboard import grid_garment

N = c1.N


def surface_uv(h, m):
    hy, hx = np.gradient(h)
    hx = np.clip(hx, -5, 5); hy = np.clip(hy, -5, 5)
    sx = np.sqrt(1 + hx ** 2) * m; sy = np.sqrt(1 + hy ** 2) * m
    u = np.full((N, N), np.nan); v = np.full((N, N), np.nan); un = np.full((N, N), np.nan)
    top = r3.rows_of(m)[0]
    for y in np.where(m.any(axis=1))[0]:
        xl, xr = r3.extent(m, y); c = int(round(0.5 * (xl + xr)))
        cs = np.cumsum(sx[y]); u[y] = cs - cs[c]
        left, right = -(u[y, xl]), u[y, xr]
        un[y] = np.where(u[y] < 0, u[y] / max(left, 1e-3), u[y] / max(right, 1e-3))
    for x in np.where(m.any(axis=0))[0]:
        ys = np.where(m[:, x])[0]; y0 = ys.min()
        cs = np.cumsum(sy[:, x]); v[:, x] = cs - cs[y0] + (y0 - top)
    un[~m] = np.nan; v[~m] = np.nan
    return un, v


# landmarks used to make 'down' comparable (Virginie 2026-11-07, 'oui, applique'): only the points she PLACED in the study
# (delta tables: 'both placed' / 'one placed'), plus the armpits and the neck front and back, detected on a real corner of
# the silhouette. The detected extremes (top, bottom, leftmost, rightmost, shoulder tip, chest front, shoulder blade, buttock,
# hips, leg bottoms) mean different things on a flat vanilla body and a muscled WDI one: profile 'chest front' high on the
# flat vanilla chest (y 226), at the pec apex on WDI (278), so the grid crowded under the pecs.
# the under-breast fold is out: the cloth hides it (it falls from the pec apex over the fold), and it made the band under the pecs
# the waist and the profile's belly front are out too: on WDI Male they sit right under the big pecs (waist 338, belly front
# 306, the apex at 302), on vanilla much further below the apex (334, 302, the apex at 278): the whole stretch between the
# apex and them was squeezed into a band; without them the squeeze spreads from the apex to the navel
# the pec apex is out of the heights as well (it stays in the relief's chest lobes): on vanilla it sits above the armpits,
# on WDI below them, so the front dropped it anyway, and in profile it squeezed the apex-to-navel stretch x0.61 into a band
KEEP = {"neck base L", "neck base R", "jugular notch",
        "navel", "sex", "armpit L", "armpit R",
        "neck front", "neck back"}
# heights shared between the views, taken from the front view's rows (the views' rows matched by the silhouette's top and
# bottom): the chest, the navel and the sex exist on the side and back views too, the study only named them on the front
SHARED = ("armpit L", "navel", "sex")


def anchors(m, v, rows, half=None):
    """{name: the row's median surface height (over `half`, a column mask, when given) at that row} + top and bottom"""
    sel = m if half is None else (m & half)
    vv = np.where(sel, v, np.nan)
    out = {"_top": 0.0, "_bottom": float(np.nanmax(vv))}
    y0, y1 = r3.rows_of(m)
    for n, y in rows.items():
        y = int(round(y))
        if y0 < y < y1 and np.isfinite(vv[y]).any():
            out[n] = float(np.nanmedian(vv[y]))
    return out


def landmark_rows(body, f, vanilla, M):
    """{name: row} of the kept landmarks of this view, the shared front rows mapped onto it, the groin fix on WDI"""
    s, d, names = e5.named_pairs(body, f)
    P = (d * 4) if vanilla else s.copy()
    ix = {n: i for i, n in enumerate(names)}
    if not vanilla and fp.GROIN and "navel" in ix:
        # the study's groin creases sit at the navel's height on WDI: on the waistband min(B,C) at 0.72 (fullpass B3)
        mnl = __import__("pantsnap").lines(body, f)[0]
        for k in ("groin crease L", "groin crease R"):
            if k in ix:
                g = ix[k]; x = P[ix["navel"], 0] + fp.GROIN_X * (P[g, 0] - P[ix["navel"], 0])
                P[g] = (x, float(mnl[int(round(x))]))
    rows = {n: float(P[i, 1]) for i, n in enumerate(names) if n in KEEP}
    if f != "south":
        s2, d2, n2 = e5.named_pairs(body, "south")
        P2 = (d2 * 4) if vanilla else s2
        for i, n in enumerate(n2):
            if n in SHARED:
                rows["S:" + n] = float(r3.map_row(P2[i, 1], M["south"], M[f]))
    return rows


def pts_of(body, f, vanilla):
    s, d, names = e5.named_pairs(body, f)
    P = (d * 4) if vanilla else s
    return {n: tuple(P[i]) for i, n in enumerate(names) if n not in ("top", "bottom", "leftmost", "rightmost")}


CLOSE_R = 14       # px: hollows narrower than this are bridged by the cloth
HANG = 0.6         # the cloth falls from a bump at this slope at most (height px per row)


def cloth(h, m):
    """the CLOTH's surface, not the skin's (Virginie 2026-11-07, 'oui, essaie'): a garment does not follow the fold under
    the pecs, the small of the back or the cleft of the buttocks, it bridges them. Hollows narrower than CLOSE_R are closed
    (grey closing), and going down each column the cloth falls from a bump no faster than HANG (it hangs from the pec apex)"""
    yy, xx = np.mgrid[-CLOSE_R:CLOSE_R + 1, -CLOSE_R:CLOSE_R + 1]
    c = ndi.grey_closing(np.where(m, h, 0.0), footprint=(xx ** 2 + yy ** 2) <= CLOSE_R ** 2)
    c = np.where(m, np.maximum(c, h), 0.0)
    for y in range(1, N):
        c[y] = np.where(m[y], np.maximum(c[y], np.where(m[y - 1], c[y - 1] - HANG, 0.0)), 0.0)
    return ndi.gaussian_filter(c, 1.5) * m


def body_side(body, f, vanilla, M, imgs):
    h = cloth(r3.height(f, M, pts_of(body, f, vanilla), c1.lum(imgs[f])), M[f])
    un, v = surface_uv(h, M[f])
    return un, v, landmark_rows(body, f, vanilla, M)


def common_scale(Aw, Av, only=None):
    """matching anchor lists, both increasing (an anchor out of order on either side is dropped)"""
    names = [n for n in Aw if n in Av and (only is None or only(n))]
    names.sort(key=lambda n: Aw[n])
    kw, kv = [], []
    for n in names:
        if (not kw or (Aw[n] > kw[-1] + 2 and Av[n] > kv[-1] + 2)):
            kw.append(Aw[n]); kv.append(Av[n])
    return np.array(kw), np.array(kv)


def scale_fn(kw, kv):
    """WDI down -> vanilla down, piecewise linear between the anchors, extended linearly past the ends"""
    def to_van(vals):
        out = np.interp(vals, kw, kv)
        lo, hi = vals < kw[0], vals > kw[-1]
        if len(kw) > 1:
            out[lo] = kv[0] + (vals[lo] - kw[0]) * (kv[1] - kv[0]) / max(kw[1] - kw[0], 1e-3)
            out[hi] = kv[-1] + (vals[hi] - kw[-1]) * (kv[-1] - kv[-2]) / max(kw[-1] - kw[-2], 1e-3)
        return out
    return to_van


EASE = 28           # px past the body edge the map reaches (the garment's ease), at 512


def extend(un, v, m, ease, Wb):
    """coordinates past the body edge (up to `ease` px): those of the nearest body pixel, plus the screen offset (across
    divided by the body's half width Wb, down in px), so a garment's ease keeps its distance to the body"""
    D = ndi.binary_dilation(m, iterations=ease) if ease else m
    _, (iy, ix) = ndi.distance_transform_edt(~m, return_indices=True)
    yy, xx = np.mgrid[0:N, 0:N]
    out_u = np.where(m, un, un[iy, ix] + (xx - ix) / Wb)
    out_v = np.where(m, v, v[iy, ix] + (yy - iy))
    out_u[~D] = np.nan; out_v[~D] = np.nan
    return out_u, out_v, D


def build(body, f, ease=0, cache={}):
    """the relief map of one view: (U, V) backward map in vanilla 128 units over the WDI body (+ ease), the X, Y smoothed in
    512 px, the WDI region, the common landmark count"""
    if body not in cache:
        imw, imv = r3.views(body, False), r3.views(body, True)
        # the WHOLE silhouette, its black outline included, on both bodies: the vanilla garment covers the vanilla body's
        # outline, so the map must reach the WDI body's outline too (Virginie 2026-11-07: 'on voit encore des zones noires
        # ... il n'en faut justement pas'); the relief's drawn zones still come from the light inside (relief3d.height)
        full = lambda img: ndi.binary_fill_holes(img[..., 3] > 0.5)
        cache[body] = (imw, imv, {k: full(imw[k]) for k in imw}, {k: full(imv[k]) for k in imv})
    imw, imv, Mw, Mv = cache[body]
    unw, vw, Rw = body_side(body, f, False, Mw, imw)
    unv, vv, Rv = body_side(body, f, True, Mv, imv)
    mv = Mv[f]; mw = Mw[f]
    xs_v = np.nonzero(mv)[1]; xs_w = np.nonzero(mw)[1]
    Wv = 0.5 * (xs_v.max() - xs_v.min()); Ww = 0.5 * (xs_w.max() - xs_w.min())
    if f == "east":
        # profile: the front landmarks for the front half (east: the front is on the right, across > 0), the back ones
        # for the back half, the shared rows for both; blended across the middle
        fr = lambda n: "back" not in n
        bk = lambda n: "front" not in n
        Fs = scale_fn(*common_scale(anchors(mw, vw, Rw, unw > 0), anchors(mv, vv, Rv, unv > 0), fr))
        Bs = scale_fn(*common_scale(anchors(mw, vw, Rw, unw < 0), anchors(mv, vv, Rv, unv < 0), bk))
        def down_of(u, vals):
            t = np.clip((u + 0.3) / 0.6, 0, 1)
            return t * Fs(vals) + (1 - t) * Bs(vals)
    else:
        sc = scale_fn(*common_scale(anchors(mw, vw, Rw), anchors(mv, vv, Rv)))
        down_of = lambda u, vals: sc(vals)
    kw = common_scale(anchors(mw, vw, Rw), anchors(mv, vv, Rv))[0]
    euv, evv, Dv = extend(unv, vv, mv, ease, Wv)
    euw, evw, Dw = extend(unw, vw, mw, ease, Ww)
    yv, xv = np.nonzero(Dv); yw, xw = np.nonzero(Dw)
    tree = cKDTree(np.c_[euv[yv, xv] * Wv, evv[yv, xv]])
    _, idx = tree.query(np.c_[euw[yw, xw] * Wv, down_of(euw[yw, xw], evw[yw, xw])])
    X = np.full((N, N), np.nan); Y = np.full((N, N), np.nan)
    X[yw, xw] = xv[idx]; Y[yw, xw] = yv[idx]
    wgt = ndi.gaussian_filter(Dw.astype(float), 3)
    Xs = ndi.gaussian_filter(np.nan_to_num(X) * Dw, 3) / np.maximum(wgt, 1e-3)
    Ys = ndi.gaussian_filter(np.nan_to_num(Y) * Dw, 3) / np.maximum(wgt, 1e-3)
    U = np.where(Dw, Xs / 4, -100.0); V = np.where(Dw, Ys / 4, -100.0)
    return dict(U=U, V=V, Xs=Xs, Ys=Ys, D=Dw, mw=mw, mv=mv, unv=unv, vv=vv, nk=len(kw), imw=imw, imv=imv)


WEAK = []


def main():
    body = next((a for a in sys.argv[1:] if "=" not in a and a not in ("nolegs", "nogroin", "fulllen", "b56")), "Male")
    font = ImageFont.load_default(size=16)
    rows = []
    for f in ("south", "east", "north"):
        Rm = build(body, f)
        U, V, Xs, Ys, mw, mv, unv, vv, imw = Rm["U"], Rm["V"], Rm["Xs"], Rm["Ys"], Rm["mw"], Rm["mv"], Rm["unv"], Rm["vv"], Rm["imw"]
        kw = range(Rm["nk"])
        yv, xv = np.nonzero(mv)
        Vb = c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{f}.png")
        G = grid_garment(Vb)
        # 1 vanilla grid on the vanilla body
        vb4 = e5.x4(Vb); vb4[..., :3] = vb4[..., :3] * 0.5 + 0.2
        t1 = e5.pil(vb4); t1.alpha_composite(e5.pil(G)); t1 = e5.on_bg(t1)
        # 2 flat: every vanilla pixel at (across, down)
        Hf = 420; Wf = 360
        flat = np.zeros((Hf, Wf, 4), np.float32)
        vmin, vmax = np.nanmin(vv), np.nanmax(vv)
        px = np.clip(((unv[yv, xv] + 1) / 2 * (Wf - 1)).round().astype(int), 0, Wf - 1)
        py = np.clip(((vv[yv, xv] - vmin) / max(vmax - vmin, 1) * (Hf - 1)).round().astype(int), 0, Hf - 1)
        flat[py, px] = G[yv, xv]
        have = flat[..., 3] > 0
        _, (iy, ix) = ndi.distance_transform_edt(~have, return_indices=True)
        dist = ndi.distance_transform_edt(~have)
        flat = flat[iy, ix]; flat[..., 3] = (dist <= 4).astype(np.float32)
        t2 = Image.new("RGBA", (N, N), (0, 0, 0, 0)); t2.alpha_composite(e5.pil(flat), ((N - Wf) // 2, (N - Hf) // 2)); t2 = e5.on_bg(t2)
        # 3 carried onto the WDI relief, over the WDI body
        Bw = imw[f].copy()
        t3 = e5.pil(Bw); t3.alpha_composite(e5.pil(e5.warp(G, U, V))); t3 = e5.on_bg(t3)
        # the weak zones (Virginie 2026-11-07: 'c'est les zones de faiblesse'): local area change of the relief map, WDI pixel
        # area over the vanilla area it takes; blue squeezed, red stretched, white as vanilla (x2 = full colour)
        Uy, Ux = np.gradient(np.where(mw, Xs, np.nan)); Vy, Vx = np.gradient(np.where(mw, Ys, np.nan))
        J = np.abs(Ux * Vy - Uy * Vx)
        r = np.log2(np.clip(1.0 / np.maximum(np.nan_to_num(J, nan=1.0), 1e-6), 1 / 8, 8))
        inside = ndi.binary_erosion(mw, iterations=2)
        tt = np.clip(r, -1, 1)
        hm = np.zeros((N, N, 4), np.float32)
        hm[..., 0] = np.where(tt > 0, 1, 1 + tt); hm[..., 1] = 1 - np.abs(tt); hm[..., 2] = np.where(tt < 0, 1, 1 - tt)
        hm[..., 3] = mw
        t5 = e5.on_bg(e5.pil(hm)); d5 = ImageDraw.Draw(t5)
        q = np.percentile(r[inside], [2, 50, 98])
        d5.text((8, 8), f"x{2 ** q[0]:.2f} / x{2 ** q[1]:.2f} / x{2 ** q[2]:.2f} (2 %, median, 98 %)", fill=(255, 255, 255), font=font)
        WEAK.append((f, float(2 ** q[0]), float(2 ** q[2]), float(np.mean(np.abs(r[inside]) > 0.58))))
        # 4 the current point warp
        fp.facing_row(body, f); L = fp.LAST
        keep = np.array([k != (150, 150, 150) for k in L["kind"]])
        U2, V2 = c1.warp_field(c1.TPS(L["S"][keep], L["D"][keep], lam=fp.LAM))
        t4 = e5.pil(Bw); t4.alpha_composite(e5.pil(e5.warp(G, U2, V2))); t4 = e5.on_bg(t4)
        ys, xs = np.nonzero(mw | e5.x4(Vb[..., 3] > 0.5))
        box = (max(0, xs.min() - 30), max(0, ys.min() - 30), min(N, xs.max() + 30), min(N, ys.max() + 30))
        tiles = [t.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for t in (t1, t3, t5, t4)]
        fl = t2.crop(((N - Wf) // 2 - 10, (N - Hf) // 2 - 10, (N + Wf) // 2 + 10, (N + Hf) // 2 + 10))
        fl = fl.resize((int(fl.width * tiles[0].height / fl.height), tiles[0].height), Image.LANCZOS)
        rows.append((f, [tiles[0], fl, tiles[1], tiles[2], tiles[3]], len(kw)))
    W = max(sum(t.width for t in r_) + 50 for _, r_, _ in rows) + 100
    H = sum(r_[0].height + 40 for _, r_, _ in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: orthogonal grid on vanilla | laid flat (across -1..1, down on the surface) | onto the WDI relief | weak zones (blue squeezed, red stretched) | current point warp",
            fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 46
    for f, ts, nk in rows:
        dr.text((10, y + 4), f"{f}\n{nk} landmarks", fill=(0, 0, 0), font=font); x = 100
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 40
    out = rf"{c1.CAPT}\2026-11-07_reliefmap-{body}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
