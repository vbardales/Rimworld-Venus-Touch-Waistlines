"""WDI body as core + masses, captured in the WDI drawing style (2026-11-09).

Requirement (Virginie): one 3D model per body type; captured from the front, the back and
the side it must give an image very close to the WDI sprite, and it must respect bone,
muscle and fat (see ANATOMY-LAYERS.md).

Model (front field in the south frame, back field in the north frame, depth in east px):
  1. Profile: front and back edges of the east silhouette per row (row-smoothed).
  2. Core (bone-bearing trunk): polyline through the PROFILE LANDMARK rows neck -> waist ->
     leg bottom, in front and behind.  Never above the profile.
  3. Masses: what the profile shows in front of / behind the core (chest or breasts, belly,
     upper back, buttocks).  Their thickness per row comes from the profile; their lateral
     footprint is a left/right lobe pair with a midline notch (ANATOMY-LAYERS section 5),
     placed from the south / north landmarks.  The mass is rescaled per row so the model's
     own profile is exactly the east silhouette.
  4. Local signed patches of shade3d.py on top (neck, navel, groin, abs, spine ...).
Capture: the three views are rendered from those fields (the east view is the side of the
same solid) with a WDI-style shader: white fill, light from the top of the sprite, flat grey
on down-facing skin (toon step), ink in hollows narrower than CLOSE (depth under the rim),
areola albedo, constant black outline.  A board and a luminance score against the real texture are written.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python wdi3d.py [Body ...]
Board: Art/work/captures/2026-11-09_wdi3d-<Body>.png ; scores: out/wdi3d-report.json
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import crack as c1
import explain5b as e5
import relief3d as r3
import shade3d

N = c1.N
HERE = pathlib.Path(__file__).parent
CAPT = HERE.parents[1] / "captures"
BODIES = ("Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female")


# ---------------------------------------------------------------- inputs
def load(body):
    imgs = r3.views(body, False)                     # real WDI textures when present
    M = {f: shade3d.silhouette_full(imgs[f]) for f in imgs}
    P = {}
    for f in imgs:
        s, _, names = e5.named_pairs(body, f)
        P[f] = {n: (float(s[i][0]), float(s[i][1])) for i, n in enumerate(names)}
    return imgs, M, P


def extents(mask, sigma=2.0):
    lo = np.full(N, np.nan); hi = np.full(N, np.nan)
    ys = np.where(mask.any(axis=1))[0]
    for y in ys:
        xs = np.flatnonzero(mask[y]); lo[y], hi[y] = xs[0], xs[-1]
    sl = slice(ys[0], ys[-1] + 1)
    lo[sl] = ndi.gaussian_filter1d(lo[sl], sigma, mode="nearest")
    hi[sl] = ndi.gaussian_filter1d(hi[sl], sigma, mode="nearest")
    return lo, hi, int(ys[0]), int(ys[-1])


def sect(t, p):
    t = np.clip(np.abs(t), 0, 1)
    return (1.0 - t ** p) ** (1.0 / p)


def smooth01(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


def find(P, *keys):
    for k in P:
        if any(k.startswith(q) or q in k for q in keys):
            return P[k]
    return None


# ---------------------------------------------------------------- profile, core, masses
class Profile:
    """East silhouette edges, core polylines and centre plane, indexed by east row."""

    def __init__(self, me, pe):
        self.zb, self.zf, self.e0, self.e1 = extents(me)
        rows = np.arange(N)

        def poly(names, edge, sign):
            ys = [pe[n][1] for n in names if n in pe]
            ys = sorted(set(float(np.clip(y, self.e0, self.e1)) for y in ys))
            core = edge.copy()
            if len(ys) >= 2:
                xs = [float(np.interp(y, rows, np.nan_to_num(edge))) for y in ys]
                inside = (rows >= ys[0]) & (rows <= ys[-1])
                line = np.interp(rows, ys, xs)
                core[inside] = line[inside]
            # never outside the silhouette
            return np.minimum(core, edge) if sign > 0 else np.maximum(core, edge)

        self.cf = poly(("neck front", "waist front", "leg bottom front"), self.zf, +1)
        self.cb = poly(("neck back", "waist back (small of the back)", "leg bottom back"), self.zb, -1)
        zc = 0.5 * (self.cf + self.cb)
        sl = slice(self.e0, self.e1 + 1)
        zc[sl] = ndi.gaussian_filter1d(zc[sl], 6.0, mode="nearest")
        self.zc = zc
        self.pe = pe

    def at(self, arr, ye):
        return np.interp(ye, np.arange(self.e0, self.e1 + 1), arr[self.e0:self.e1 + 1])

    def row(self, name, default):
        return self.pe[name][1] if name in self.pe else default


def params(body):
    fl = {"female": "Female" in body, "fat": body.startswith("Fat"), "hulk": body.startswith("Hulk"),
          "thin": body.startswith("Thin")}
    p = dict(core_p=2.6, edge_q=3.0, sternum=0.22, alba=0.10, groin=0.55, spine=0.22, cleft=0.80,
             breast_rx=0.95, breast_p=2.6, breast=False)
    if fl["hulk"]:
        p.update(core_p=3.0, sternum=0.30, alba=0.16, spine=0.32)
    if fl["thin"]:
        p.update(core_p=2.7, sternum=0.18, alba=0.10, spine=0.25)
    if fl["fat"]:
        p.update(core_p=2.3, edge_q=2.6, sternum=0.12, alba=0.03, spine=0.10, groin=0.45)
    if fl["female"]:
        p.update(breast=True, sternum=0.10, alba=0.06)
    if fl["fat"] and not fl["female"]:
        p.update(breast=True, breast_rx=1.05, breast_p=2.2)   # hanging male chest: two lobes too
    return fl, p


def fit_mass(core_row, lobe_row, depth):
    """Scale the mass so that the row's maximum is exactly the profile depth."""
    if depth <= core_row.max() + 1e-6 or lobe_row.max() <= 1e-6:
        return 0.0
    m = (depth - core_row.max()) / lobe_row.max()
    for _ in range(4):
        k = int(np.argmax(core_row + m * lobe_row))
        if lobe_row[k] <= 1e-6:
            break
        m = max((depth - core_row[k]) / lobe_row[k], 0.0)
    return m


def build_field(body, view, M, P, prof):
    """Height field of the front (south) or back (north) surface above the centre plane."""
    fl, pr = params(body)
    m = M[view]; pts = P[view]
    lo, hi, y0, y1 = extents(m)
    xs = np.arange(N, dtype=float)
    field = np.zeros((N, N))
    e_of = lambda y: prof.e0 + (y - y0) / max(y1 - y0, 1) * (prof.e1 - prof.e0)
    inv = lambda ye: y0 + (ye - prof.e0) / max(prof.e1 - prof.e0, 1) * (y1 - y0)
    front = view == "south"
    midx_default = 0.5 * (np.nanmean(lo[y0:y1 + 1]) + np.nanmean(hi[y0:y1 + 1]))
    if front:
        cleav = find(pts, "cleavage") or find(pts, "jugular notch")
        midx = cleav[0] if cleav else midx_default
        apex_l, apex_r = pts.get("breast apex L"), pts.get("breast apex R")
        fold = pts.get("under-breast fold L")
        y_waist = inv(prof.row("waist front", prof.e0 + 0.6 * (prof.e1 - prof.e0)))
        y_neck = inv(prof.row("neck front", prof.e0))
        sex = pts.get("sex"); crotch = pts.get("crotch point")
    else:
        top = pts.get("top"); midx = top[0] if top else midx_default
        y_waist = inv(prof.row("waist back (small of the back)", prof.e0 + 0.45 * (prof.e1 - prof.e0)))
        crotch = pts.get("crotch point")
    for y in range(y0, y1 + 1):
        ye = e_of(y)
        zc = prof.at(prof.zc, ye)
        if front:
            depth = prof.at(prof.zf, ye) - zc; core = prof.at(prof.cf, ye) - zc
        else:
            depth = zc - prof.at(prof.zb, ye); core = zc - prof.at(prof.cb, ye)
        depth = max(depth, 0.5); core = float(np.clip(core, 0.25, depth))
        c = 0.5 * (lo[y] + hi[y]); w = max(0.5 * (hi[y] - lo[y]), 1.0)
        t = (xs - c) / w
        inside = np.abs(t) <= 1
        core_row = core * sect(t, pr["core_p"]) * inside
        s = np.abs(xs - midx)
        W = 2 * w
        if front:
            if y < y_waist:                                   # chest: pecs or breasts
                notch = pr["sternum"]
                lobe = 1.0 - notch * np.exp(-(s / (0.06 * W + 2)) ** 2)
                if pr["breast"] and apex_l and apex_r and fold:
                    ya = 0.5 * (apex_l[1] + apex_r[1]); yf = fold[1]
                    dm = max(0.5 * abs(apex_r[0] - apex_l[0]), 6.0)
                    # teardrop: broad near the clavicle, radius dm at the apex, narrow at the fold
                    if y <= ya:
                        k = smooth01((y - y_neck) / max(ya - y_neck, 1))
                        rx = dm * (3.0 + (pr["breast_rx"] - 3.0) * k)
                    else:
                        k = smooth01((y - ya) / max(yf - ya, 1))
                        rx = dm * (pr["breast_rx"] + (0.62 - pr["breast_rx"]) * k)
                    two = np.maximum(np.exp(-np.abs((xs - apex_l[0]) / rx) ** pr["breast_p"]),
                                     np.exp(-np.abs((xs - apex_r[0]) / rx) ** pr["breast_p"]))
                    below = smooth01((y - yf) / max(0.35 * (y_waist - yf), 1))   # under the fold: rib cage again
                    lobe = (1 - below) * two + below * lobe
            else:                                             # belly, pubis, thigh roots
                ys_sex = sex[1] if sex else y1
                k = smooth01((y - ys_sex) / max(y1 - ys_sex, 1) + 0.15) if y > ys_sex - 6 else 0.0
                notch = pr["alba"] + (pr["groin"] - pr["alba"]) * k
                lobe = 1.0 - notch * np.exp(-(s / (0.05 * W + 2)) ** 2)
        else:
            if y < y_waist:                                   # upper back: spine groove between the erectors
                lobe = 1.0 - pr["spine"] * np.exp(-(s / (0.05 * W + 2)) ** 2)
            else:                                             # buttocks: cleft deepens downward
                k = smooth01((y - y_waist) / max(0.55 * (y1 - y_waist), 1))
                notch = pr["spine"] + (pr["cleft"] - pr["spine"]) * k
                lobe = 1.0 - notch * np.exp(-(s / (0.035 * W + 2)) ** 2)
        lobe_row = lobe * sect(t, pr["edge_q"]) * inside
        mass = fit_mass(core_row, lobe_row, depth)
        field[y] = core_row + mass * lobe_row
    # local signed anatomy patches of shade3d (kept, laid over the base)
    yy, xx = np.mgrid[0:N, 0:N]
    shade3d.BODY[0] = body
    anchors = shade3d._anchors(pts)
    flags = shade3d._body_flags()
    detail = shade3d._front_torso_patches(xx, yy, anchors, flags) if front else shade3d._back_torso_patches(xx, yy, anchors, flags)
    field = ndi.gaussian_filter(field, (1.2, 1.0)) + ndi.gaussian_filter(detail, 0.7)
    return np.maximum(field, 0.0) * m


def side_field(M, prof, Hs, Hn):
    """Side view of the same solid: half-width visible at each (east row, depth)."""
    ms, mn, me = M["south"], M["north"], M["east"]
    slo, shi, s0, s1 = extents(ms); nlo, nhi, n0, n1 = extents(mn)
    out = np.zeros((N, N)); zgrid = np.arange(N, dtype=float)
    for ye in range(prof.e0, prof.e1 + 1):
        f = (ye - prof.e0) / max(prof.e1 - prof.e0, 1)
        ys = s0 + f * (s1 - s0); yn = n0 + f * (n1 - n0)
        xl = np.interp(ys, np.arange(N), np.nan_to_num(slo)); xr = np.interp(ys, np.arange(N), np.nan_to_num(shi))
        nl = np.interp(yn, np.arange(N), np.nan_to_num(nlo)); nr = np.interp(yn, np.arange(N), np.nan_to_num(nhi))
        c = 0.5 * (xl + xr)
        x = np.linspace(c, xr, 256)
        zf = ndi.map_coordinates(Hs, [np.full_like(x, ys), x], order=1)
        xn = nr - (x - xl) / max(xr - xl, 1) * (nr - nl)
        zb = ndi.map_coordinates(Hn, [np.full_like(x, yn), xn], order=1)
        zc = prof.zc[ye]
        ok = (zgrid[:, None] <= zc + zf[None, :]) & (zgrid[:, None] >= zc - zb[None, :])
        val = np.where(ok, (x - c)[None, :], -1.0).max(axis=1)
        out[ye] = np.maximum(val, 0.0)
    return out * me


# ---------------------------------------------------------------- creases drawn by the artist
GROOVE = 4.0     # px of depth of a fully black drawn crease
DIFFUSE = 260    # barrier-diffusion steps (about 10 px of spread inside a zone)


def wdi_lines(img, m, width):
    """Strength 0..1 of the THIN dark strokes of the sprite (creases, seams between volumes).

    Broad grey shading is not read: it has to come from the volumes and the light.  The
    black outline band is excluded.
    """
    lum = c1.lum(img)
    inner = ndi.distance_transform_edt(m) > width + 1.0
    dark = np.clip((0.82 - lum) / 0.55, 0, 1) * inner
    broad = ndi.grey_opening(dark, size=(11, 11))
    black = np.clip((0.45 - lum) / 0.3, 0, 1) * inner          # black paint is ink whatever its width
    return np.clip(np.maximum(dark - broad, black), 0, 1)


def diffuse(h, m, lines, steps=DIFFUSE):
    """Smooth each volume inside its zone; the drawn creases are barriers.

    A row-wise profile step (pec shelf, under-breast fold, buttock fold) then sits on the
    drawn crease instead of on a horizontal row.
    """
    k = (1.0 - np.clip(2.0 * lines, 0, 1)) * m
    h = h.copy()
    for _ in range(steps):
        acc = np.zeros_like(h); wsum = np.zeros_like(h)
        for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
            kn = np.roll(k, sh, axis=ax); hn = np.roll(h, sh, axis=ax)
            c = np.minimum(k, kn)
            acc += c * (hn - h); wsum += c
        h += 0.2 * acc
    return h * m


SLOPE_K = 0.50   # tone lost per unit of downward slope beyond the toon step (shared by the model fit and the shader)
SLOPE_0 = 0.15   # downward slope where the grey starts
TOON_G = 0.15    # flat WDI grey (luminance 0.85, the mode of the sprite greys): reached over TOON_D of slope
TOON_D = 0.10
CLOSE = 19       # px: a hollow narrower than this is a crease (ink); wider is a volume (shaded by its slope)
MU = 0.001       # pull of the fitted surface back to the profile-built volumes (length scale about 16 px)


def wdi_shade(img, m, width):
    """Broad grey paint 0..1 (1 = black) inside the outline, thin strokes removed."""
    lum = c1.lum(img)
    inner = ndi.distance_transform_edt(m) > width + 1.0
    g = np.clip(1.0 - lum, 0, 1)
    g = ndi.grey_opening(g, size=(7, 7))
    return np.clip(ndi.gaussian_filter(g, 0.5), 0, 0.6) * inner


DISK = np.hypot(*np.mgrid[-(CLOSE // 2):CLOSE // 2 + 1, -(CLOSE // 2):CLOSE // 2 + 1]) <= CLOSE / 2


def closed(h):
    """The volumes without their creases: every hollow narrower than CLOSE is filled to its rim.

    Hollows shallower than about 1 px are left alone: a flat closing lays square plateaus on
    any saddle of a smooth surface, and their edges would shade as blocks.
    """
    cav = ndi.grey_closing(h, footprint=DISK) - h
    return h + cav * smooth01((cav - 0.3) / 0.7)


def loss_of_slope(s):
    """Tone lost at downward slope s: a toon step to the flat WDI grey, then linear (darker under overhangs)."""
    t = np.clip((s - SLOPE_0) / TOON_D, 0, 1)
    return np.clip(TOON_G * t + SLOPE_K * np.clip(s - SLOPE_0 - TOON_D, 0, None), 0, 0.6)


def slope_of_loss(g):
    """Inverse of loss_of_slope (used by the fit to step in slope units)."""
    g = np.clip(g, 0, 0.6)
    return np.where(g <= TOON_G, SLOPE_0 + TOON_D * g / TOON_G, SLOPE_0 + TOON_D + (g - TOON_G) / SLOPE_K)


def tone_of_slope(hc):
    """Top light on the crease-free volumes: skin that faces down goes grey (shared with the shader)."""
    gy, _ = np.gradient(ndi.gaussian_filter(hc, 0.6))
    return 1.0 - loss_of_slope(-gy)


def fit_shading(h, m, grey, rounds=24):
    """Fit the volumes so that their top-lit capture has the sprite's broad shading.

    Unknown: the surface u.  It stays as close as possible to the profile-built volumes h
    (screened Poisson, pull MU) while its vertical slope is corrected, round after round,
    by the difference between the captured tone and the painted tone.  A shadow therefore
    becomes a change of volume across the shadow, never a hollow; white skin that the
    volumes would render grey is flattened.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import factorized
    gy, gx = np.gradient(h)
    target = 1.0 - grey
    near = ndi.maximum_filter(grey > 0.02, size=9)
    wy = np.where(grey > 0.02, 4.0, 1.5); wx = np.where(near, 0.3, 1.0)
    idx = -np.ones(h.shape, int); ys, xs = np.nonzero(m); n = len(ys); idx[ys, xs] = np.arange(n)
    rows, cols, vals, edges = [], [], [], []
    diag = np.full(n, MU)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        y2, x2 = ys + dy, xs + dx
        ok = (y2 >= 0) & (y2 < N) & (x2 >= 0) & (x2 < N)
        ok[ok] &= m[y2[ok], x2[ok]]
        j = idx[y2[ok], x2[ok]]; i = np.flatnonzero(ok)
        wt = wy if dy else wx
        we = 0.5 * (wt[ys[ok], xs[ok]] + wt[y2[ok], x2[ok]])
        rows.append(i); cols.append(j); vals.append(-we); diag[i] += we
        edges.append((dy, dx, i, ys[ok], xs[ok], y2[ok], x2[ok], we))
    rows.append(np.arange(n)); cols.append(np.arange(n)); vals.append(diag)
    A = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsc()
    solve = factorized(A)
    inner = grey_inner = ndi.binary_erosion(m, iterations=3)
    gy_t = gy.copy(); out = h.copy(); best = (1e9, h)
    for _ in range(rounds):
        rhs = MU * h[ys, xs]
        for dy, dx, i, ya, xa, yb, xb, we in edges:
            g = (0.5 * (gy_t[ya, xa] + gy_t[yb, xb]) * dy) if dy else (0.5 * (gx[ya, xa] + gx[yb, xb]) * dx)
            np.subtract.at(rhs, i, we * g)
        out = np.zeros_like(h); out[ys, xs] = solve(rhs)
        out = np.maximum(out, 0.0) * m
        err = (tone_full(out, m) - target) * inner             # > 0: captured too light
        e = float(np.abs(err).mean())
        if e < best[0]:
            best = (e, out)
        # step in slope units through the inverse transfer.  Rejected: stepping on the measured slope with a
        # margin on each side of the toon step (diverges unclipped; clipped it bands and loses wedges).
        step = slope_of_loss(grey) - slope_of_loss(1.0 - tone_of_slope(closed(out)))   # > 0: needs more downward slope
        gy_t = np.clip(gy_t - 0.7 * ndi.gaussian_filter(step * inner, 0.5), -2.0, 2.0)
    return closed(best[1]) * m


def fit_grooves(h, m, lines, img, width, rounds=8):
    """Depth of each drawn crease, adjusted until the captured ink has the painted tone."""
    lum = c1.lum(img)
    dark = 1.0 - lum
    faint = (dark - ndi.grey_opening(dark, size=(11, 11))) > 0.03   # thin pale strokes too (spine, cleft)
    sel = ((lines > 0.04) | faint) & (ndi.distance_transform_edt(m) > width + 1.0)   # stroke pixels: flat floor, full width
    depth = GROOVE * np.clip(1.0 - lum, 0, 1) * sel
    best = (1e9, h)
    for _ in range(rounds):
        out = np.maximum(h - depth, 0.0) * m
        err = (tone_full(out, m) - lum) * sel                  # > 0: captured too light
        e = float(np.abs(err).sum())
        if e < best[0]:
            best = (e, out)
        depth = np.clip(depth + 0.8 * GROOVE * err, 0, 16.0) * sel
    return best[1]


def tone_full(h, m):
    """Shader: slope tone of the crease-free volumes, ink in the creases (depth under the rim, black at GROOVE)."""
    hc = closed(h)
    return np.minimum(tone_of_slope(hc), 1.0 - np.clip((hc - h) * m / GROOVE, 0, 1))


def carve(h, m, lines):
    return np.maximum(h - GROOVE * ndi.gaussian_filter(lines, 0.8), 0.0) * m


# ---------------------------------------------------------------- WDI-style capture
def outline_width(img, m):
    lum = c1.lum(img)
    d = ndi.distance_transform_edt(m)
    ol = m & (lum < 0.2) & (d <= 18)
    return float(np.percentile(d[ol], 95)) + 1.0 if ol.sum() > 50 else 13.0


def areolae(img, m):
    """Pink patches of the sprite as discs (x, y, radius, colour): skin colour, not relief."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    pink = (r > 0.8) & (r - b > 0.04) & m
    lab, n = ndi.label(pink)
    out = []
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) >= 30:
            out.append((float(xs.mean()), float(ys.mean()), float(np.sqrt(len(ys) / np.pi)), np.median(img[ys, xs, :3], axis=0)))
    return out


def capture(h, m, width, nipples=()):
    """White skin, top light, grey down-facing, crease ink, black outline; the areola is an albedo under the ink."""
    tone = tone_full(h, m)
    albedo = np.ones((N, N, 3))
    yy, xx = np.mgrid[0:N, 0:N]
    for (x, y, r, col) in nipples:
        a = np.clip(r + 0.5 - np.hypot(xx - x, yy - y), 0, 1)[..., None]
        albedo = albedo * (1 - a) + col * a
    rgb = tone[..., None] * albedo
    d = ndi.distance_transform_edt(m)
    edge = np.clip(width - d + 0.5, 0, 1)[..., None]
    rgb = rgb * (1 - edge)
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = rgb; out[..., 3] = m
    return out


def score(cap, img, m, width):
    """Mean absolute luminance difference inside the outline, after a 2 px blur; and the same for blank white."""
    inner = ndi.distance_transform_edt(m) > width + 2
    a = ndi.gaussian_filter(c1.lum(img), 2.0); b = ndi.gaussian_filter(c1.lum(cap), 2.0)
    if inner.sum() < 50:
        return 0.0, 0.0
    return float(np.abs(a - b)[inner].mean()), float(np.abs(a - 1.0)[inner].mean())


def on_bg(img):
    a = img[..., 3:4]
    return np.clip(226 * (1 - a) + 255 * img[..., :3] * a, 0, 255).astype(np.uint8)


def one(body):
    imgs, M, P = load(body)
    prof = Profile(M["east"], P["east"])
    Hs = build_field(body, "south", M, P, prof)
    Hn = build_field(body, "north", M, P, prof)
    width = {f: outline_width(imgs[f], M[f]) for f in imgs}
    lines = {f: wdi_lines(imgs[f], M[f], width[f]) for f in imgs}
    # volumes: smooth inside the zones the artist separates, steps on his creases
    Hs = diffuse(Hs, M["south"], lines["south"]); Hn = diffuse(Hn, M["north"], lines["north"])
    He = side_field(M, prof, Hs, Hn)
    He = ndi.gaussian_filter1d(He, 2.0, axis=0) * M["east"]          # rows are built one by one: no row bands
    He = diffuse(He, M["east"], lines["east"], 60)
    base = {"south": Hs, "north": Hn, "east": He}
    fields = {}; moved = {}
    for f in base:
        fitted = fit_shading(base[f], M[f], wdi_shade(imgs[f], M[f], width[f]))
        fields[f] = fit_grooves(fitted, M[f], lines[f], imgs[f], width[f])
        inner = ndi.distance_transform_edt(M[f]) > width[f] + 2
        moved[f] = (float(np.abs(fitted - base[f])[inner].mean()), float(np.percentile(np.abs(fitted - base[f])[inner], 95)))
    tiles, rep = [], {}
    for f in ("south", "north", "east"):
        w = width[f]
        cap = capture(fields[f], M[f], w, areolae(imgs[f], M[f]))
        mae, blank = score(cap, imgs[f], M[f], w)
        rep[f] = {"mae": round(mae, 4), "blank_white": round(blank, 4), "outline_px": round(w, 1),
                  "moved_mean_px": round(moved[f][0], 2), "moved_p95_px": round(moved[f][1], 2)}
        ys, xs = np.nonzero(M[f])
        box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(N, xs.max() + 7), min(N, ys.max() + 7))
        tiles.append((f, Image.fromarray(on_bg(imgs[f])).crop(box), Image.fromarray(on_bg(cap)).crop(box)))
    W = sum(a.width * 2 + 16 for _, a, _ in tiles); H = max(a.height for _, a, _ in tiles) + 18
    board = Image.new("RGB", (W, H), (235, 235, 230)); d = ImageDraw.Draw(board); x = 0
    for f, a, b in tiles:
        d.text((x + 2, 2), f"{body} {f}: WDI | capture  mae {rep[f]['mae']:.3f} (blank {rep[f]['blank_white']:.3f})", fill=(0, 0, 0))
        board.paste(a, (x, 16)); board.paste(b, (x + a.width + 4, 16)); x += a.width * 2 + 16
    CAPT.mkdir(exist_ok=True)
    board.save(CAPT / f"2026-11-09_wdi3d-{body}.png")
    np.savez_compressed(HERE / "out" / f"wdi3d-{body}.npz", south=fields["south"].astype(np.float32), north=fields["north"].astype(np.float32),
                        east=fields["east"].astype(np.float32), zc=prof.zc.astype(np.float32))
    return rep


def overview(width=1500):
    boards = [Image.open(CAPT / f"2026-11-09_wdi3d-{b}.png") for b in BODIES]
    k = width / max(b.width for b in boards)
    boards = [b.resize((max(int(b.width * k), 1), max(int(b.height * k), 1)), Image.LANCZOS) for b in boards]
    out = Image.new("RGB", (width, sum(b.height + 4 for b in boards)), (235, 235, 230)); y = 0
    for b in boards:
        out.paste(b, (0, y)); y += b.height + 4
    out.save(CAPT / "2026-11-09_wdi3d-overview.png")


def main():
    names = [a for a in sys.argv[1:] if a in BODIES] or BODIES
    path = HERE / "out" / "wdi3d-report.json"
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    for b in names:
        report[b] = one(b)
        print(b, " ".join(f"{f} {v['mae']:.3f}/{v['blank_white']:.3f}" for f, v in report[b].items()), flush=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    overview()


if __name__ == "__main__":
    main()
