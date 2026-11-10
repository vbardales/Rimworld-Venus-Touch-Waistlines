"""Torso-pelvis as a stack: skeleton, viscera, muscle volumes, thin fat; the skin is the outside of the stack (2026-11-10).

Virginie's direction change (BODY3D.md, "Direction change"): nothing is drawn on a base volume any more. The muscles ARE
the volume. Male first; the other bodies adapt from it later; the fit to WDI comes last and is done by parameters.

Space: x = south column - 258 (0 = midline, the body is symmetric so only x >= 0 is computed), r = south row (down),
z = east column (front = larger). Everything is a signed distance field on a voxel grid [r, x, z]:
  1. bones: spine with spinous processes, rib barrel (lofted, kyphosis, slanted inlet, costal arch), sternum, clavicle,
     scapula with its spine and acromion, humerus stub, pelvis (iliac wings, sacrum, pubis, ischium), femur stub;
  2. viscera: the abdominal cavity between the barrel and the pelvis (filler under the abdominal wall);
  3. muscles: finite volumes between their attachments. Sheets that lie on the trunk are lenses on the layers below them
     (thickness along the normal of what they lie on, footprint = a polygon in the front, back, side or unwrapped
     projection, rounded border); masses are ellipsoids and round cones. Each one is unioned with a small radius, so
     seams stay creases;
  4. fat: a thin layer everywhere, a floor over bare bone, and the male pads (flank, lower abdomen, pubis, lower medial
     gluteal). Fat bridges the narrow hollows except along the skin tethers; a small blur of the field is the skin
     tension (creases keep a finite radius);
  5. fit: a row-wise affine of the whole stack (width, front depth, back depth, smooth along the rows) onto the three
     WDI silhouettes. It moves bones, muscles and skin together; its size is reported.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python stack3d.py [h] [tag] [nofit]
  h = voxel size in px (2 for tuning, 1 for the export). Writes captures/2026-11-10_stack3d-<tag>-Male-views.png (WDI |
  toon capture of the stack | outlines, three views) and ...-lit.png (lit previews, plain and coloured by muscle, at
  0, 35, 90, 145, 180 degrees), and prints the residual of the model against the silhouettes before and after the fit.
  FIT_SIGMAS="6,4" sets the row smoothing of the two fit passes.
The export for the viewer is stack3d_export.py. Notes and scores: BODY3D.md, "Stack model for Male".
"""
import os
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

import wdi3d as w

HERE = pathlib.Path(__file__).parent
CAPT = w.CAPT
N = w.N
CX = 258.0          # south midline column
BIG = 1e3
RW = 78.0           # px per radian of the unwrapped (W) projection


# ---------------------------------------------------------------- grid
class Grid:
    def __init__(self, h=1.0, x1=110.0, r0=176.0, r1=438.0, z0=168.0, z1=348.0):
        self.h = float(h)
        self.x = np.arange(0.0, x1 + h, h, dtype=np.float32)
        self.r = np.arange(r0, r1 + h, h, dtype=np.float32)
        self.z = np.arange(z0, z1 + h, h, dtype=np.float32)
        self.shape = (len(self.r), len(self.x), len(self.z))

    def box(self, lo, hi, pad=6.0):
        """Index slices of the box lo..hi (x, r, z), padded; x is folded onto x >= 0."""
        x0 = 0.0 if lo[0] < 0 else lo[0]
        x1 = max(abs(lo[0]), abs(hi[0])) if lo[0] < 0 else hi[0]
        out = []
        for ax, a, b in ((self.r, lo[1], hi[1]), (self.x, x0, x1), (self.z, lo[2], hi[2])):
            i0 = max(int(np.searchsorted(ax, a - pad)) - 1, 0)
            i1 = min(int(np.searchsorted(ax, b + pad)) + 1, len(ax))
            out.append(slice(i0, max(i1, i0 + 2)))
        return tuple(out)

    def coords(self, sl):
        return (self.x[sl[1]][None, :, None], self.r[sl[0]][:, None, None], self.z[sl[2]][None, None, :])

    def full(self, v=BIG):
        return np.full(self.shape, v, np.float32)


def smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(k - np.abs(a - b), 0, None) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    return -smin(-a, -b, k)


def sstep(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


def rotm(front=0.0, side=0.0, top=0.0):
    """Local-to-world rotation. front: the lower end of the local r axis goes to +x (south view); side: it goes to +z
    (east view); top: the local x axis goes to +z."""
    f, s, t = np.radians([front, side, top])
    rf = np.array([[np.cos(f), np.sin(f), 0], [-np.sin(f), np.cos(f), 0], [0, 0, 1]])
    rs = np.array([[1, 0, 0], [0, np.cos(s), -np.sin(s)], [0, np.sin(s), np.cos(s)]])
    rt = np.array([[np.cos(t), 0, -np.sin(t)], [0, 1, 0], [np.sin(t), 0, np.cos(t)]])
    return rf @ rs @ rt


# ---------------------------------------------------------------- primitives: (fn(X, R, Z) -> d, lo, hi)
def ell(c, rad, rad2=None, rot=None):
    """Ellipsoid; rad2 = radii on the negative side of each local axis (x, r, z), for eggs and half domes."""
    c = np.asarray(c, float); rad = np.asarray(rad, float)
    rad2 = rad if rad2 is None else np.asarray(rad2, float)
    m = np.eye(3) if rot is None else rotm(*rot)

    def fn(X, R, Z):
        P = (X - c[0], R - c[1], Z - c[2])
        k0 = 0.0; k1 = 0.0
        for i in range(3):
            p = m[0, i] * P[0] + m[1, i] * P[1] + m[2, i] * P[2]
            rr = np.where(p >= 0, rad[i], rad2[i])
            k0 = k0 + (p / rr) ** 2; k1 = k1 + (p / (rr * rr)) ** 2
        k0 = np.sqrt(k0); k1 = np.sqrt(k1)
        return (k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)).astype(np.float32)

    e = float(max(rad.max(), rad2.max())) if rot is not None else np.maximum(rad, rad2)
    return fn, c - e, c + e


def cone(a, b, ra, rb):
    """Round cone from a (radius ra) to b (radius rb)."""
    a = np.asarray(a, float); b = np.asarray(b, float); ba = b - a; bb = float(ba @ ba)

    def fn(X, R, Z):
        P = (X - a[0], R - a[1], Z - a[2])
        t = np.clip((P[0] * ba[0] + P[1] * ba[1] + P[2] * ba[2]) / bb, 0, 1)
        d = np.sqrt((P[0] - ba[0] * t) ** 2 + (P[1] - ba[1] * t) ** 2 + (P[2] - ba[2] * t) ** 2)
        return (d - (ra + (rb - ra) * t)).astype(np.float32)

    e = max(ra, rb)
    return fn, np.minimum(a, b) - e, np.maximum(a, b) + e


def tube(pts, radii):
    """Chain of round cones through pts (x, r, z); radii per point or one number."""
    pts = [np.asarray(p, float) for p in pts]
    radii = [float(radii)] * len(pts) if np.isscalar(radii) else list(radii)
    parts = [cone(pts[i], pts[i + 1], radii[i], radii[i + 1]) for i in range(len(pts) - 1)]

    def fn(X, R, Z):
        d = parts[0][0](X, R, Z)
        for p in parts[1:]:
            d = np.minimum(d, p[0](X, R, Z))
        return d

    return fn, np.min([p[1] for p in parts], axis=0), np.max([p[2] for p in parts], axis=0)


def tri(a, b, c, th):
    """Triangle plate of half thickness th (distance to the triangle minus th)."""
    a, b, c = (np.asarray(v, float) for v in (a, b, c))
    ba, cb, ac = b - a, c - b, a - c
    nor = np.cross(ba, ac)

    def dot(u, v):
        return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]

    def edge(P, e):
        t = np.clip(dot(e, P) / float(e @ e), 0, 1)
        q = (P[0] - e[0] * t, P[1] - e[1] * t, P[2] - e[2] * t)
        return dot(q, q)

    def fn(X, R, Z):
        pa = (X - a[0], R - a[1], Z - a[2]); pb = (X - b[0], R - b[1], Z - b[2]); pc = (X - c[0], R - c[1], Z - c[2])
        s = (np.sign(dot(np.cross(ba, nor), pa)) + np.sign(dot(np.cross(cb, nor), pb)) + np.sign(dot(np.cross(ac, nor), pc)))
        d2 = np.where(np.abs(s) < 2.0, np.minimum(np.minimum(edge(pa, ba), edge(pb, cb)), edge(pc, ac)), dot(nor, pa) ** 2 / float(nor @ nor))   # either winding
        return (np.sqrt(d2) - th).astype(np.float32)

    return fn, np.min([a, b, c], axis=0) - th, np.max([a, b, c], axis=0) + th


def sd_poly(px, py, V):
    """Signed distance (negative inside) to the polygon V (n, 2), any orientation."""
    V = np.asarray(V, float); n = len(V)
    d = np.full(np.broadcast(px, py).shape, 1e12); s = np.ones(d.shape)
    for i in range(n):
        j = (i - 1) % n
        ex, ey = V[j, 0] - V[i, 0], V[j, 1] - V[i, 1]
        wx, wy = px - V[i, 0], py - V[i, 1]
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        d = np.minimum(d, (wx - ex * t) ** 2 + (wy - ey * t) ** 2)
        c1 = py >= V[i, 1]; c2 = py < V[j, 1]; c3 = ex * wy > ey * wx
        s = np.where((c1 & c2 & c3) | (~c1 & ~c2 & ~c3), -s, s)
    return s * np.sqrt(d)


def chaikin(V, n=2):
    V = np.asarray(V, float)
    for _ in range(n):
        Q = 0.75 * V + 0.25 * np.roll(V, -1, axis=0); Rr = 0.25 * V + 0.75 * np.roll(V, -1, axis=0)
        V = np.stack([Q, Rr], axis=1).reshape(-1, 2)
    return V


def spline(pts):
    pts = np.asarray(pts, float)
    return PchipInterpolator(pts[:, 0], pts[:, 1], extrapolate=True)


# ---------------------------------------------------------------- WDI targets (anchors of the skeleton, fit targets)
class Target:
    """The three silhouettes of a body as functions of the south row: half width, front and back of the east profile."""

    def __init__(self, body):
        self.body = body
        self.imgs, self.M, self.P = w.load(body)
        slo, shi, self.s0, self.s1 = w.extents(self.M["south"])
        nlo, nhi, self.n0, self.n1 = w.extents(self.M["north"])
        elo, ehi, self.e0, self.e1 = w.extents(self.M["east"])
        rows = np.arange(N, dtype=float)
        self.cxs = float(np.nanmean(0.5 * (slo + shi)[self.s0:self.s1 + 1]))
        self.cxn = float(np.nanmean(0.5 * (nlo + nhi)[self.n0:self.n1 + 1]))
        rs = np.arange(self.s0, self.s1 + 1, dtype=float)
        f = (rs - self.s0) / (self.s1 - self.s0)
        hw_s = 0.5 * (shi - slo)[self.s0:self.s1 + 1]
        hw_n = np.interp(self.n0 + f * (self.n1 - self.n0), rows[self.n0:self.n1 + 1], 0.5 * (nhi - nlo)[self.n0:self.n1 + 1])
        re = self.e0 + f * (self.e1 - self.e0)
        self.rows = rs
        self.hw_s, self.hw_n = hw_s, hw_n
        self.hw = 0.5 * (hw_s + hw_n)                         # one solid for two masks that differ by 1 to 2 px
        self.zb = np.interp(re, rows[self.e0:self.e1 + 1], elo[self.e0:self.e1 + 1])
        self.zf = np.interp(re, rows[self.e0:self.e1 + 1], ehi[self.e0:self.e1 + 1])
        self.zc = ndi.gaussian_filter1d(0.5 * (self.zb + self.zf), 8.0, mode="nearest")

    def at(self, arr, r):
        return np.interp(r, self.rows, arr)

    def e_of(self, r):
        return self.e0 + (np.asarray(r, float) - self.s0) / (self.s1 - self.s0) * (self.e1 - self.e0)

    def n_of(self, r):
        return self.n0 + (np.asarray(r, float) - self.s0) / (self.s1 - self.s0) * (self.n1 - self.n0)


# ---------------------------------------------------------------- the stack
class Stack:
    """Accumulates the layers. d = current outside of the stack; parts = display volumes of each bone and muscle."""

    def __init__(self, G, zc, ms=1.0, ps=1.0):
        self.ms, self.ps = ms, ps                              # thickness scale of the sheet muscles and of the fat pads
        self.G = G
        self.zc = zc                                           # centre plane z as a function of r (callable)
        self.d = G.full()
        self.owner = np.zeros(G.shape, np.int16)
        self.parts = []                                        # (name, layer, colour, slices, display field)
        self.layer_d = {}

    def _eval(self, prim, pad, km=0.0):
        fn, lo, hi = prim
        sl = self.G.box(lo, hi, pad)
        X, R, Z = self.G.coords(sl)
        a = np.broadcast_to(fn(X, R, Z), tuple(s.stop - s.start for s in sl)).astype(np.float32)
        if lo[0] < pad:                                        # reaches the midline: union with its mirror image
            a = smin(a, np.broadcast_to(fn(-X, R, Z), a.shape).astype(np.float32), km)
        return sl, a

    def add(self, name, layer, prim, k=0.0, colour=(200, 200, 200), km=0.0, show=True):
        """Free volume (ellipsoid, cone, tube, plate ...), unioned with radius k; km = radius of the union with its mirror."""
        sl, a = self._eval(prim, 6.0 + k, km)
        cur = self.d[sl]
        self.owner[sl][a < cur] = len(self.parts) + 1
        self.d[sl] = smin(cur, a, k)
        self.parts.append((name, layer, colour, sl, a if show else None))
        return sl, a

    def lens(self, name, layer, proj, poly, T, wd, mod=None, colour=(200, 200, 200), prof=2.0, rnd=2, pad=14.0, on="stack", k=0.0):
        """Sheet muscle: thickness T inside the polygon, rounded over wd px at its border, laid on what is below it.

        on: "stack" = on everything built so far (a superficial sheet adds to the deeper ones); a layer name ("core",
        "bone") = thickness measured from that layer, then unioned with the stack (radius k).
        proj: 'F' / 'B' polygon in (x, r) on the front / back half; 'S' polygon in (z, r) on the flank; 'W' polygon in
        (s, r), s = RW x angle around the trunk axis (0 = front midline, RW*pi = back midline).
        mod(u, v) -> factor on T (u, v = the polygon coordinates). prof: 2 = quarter-circle shoulder, lower = softer.
        """
        V = chaikin(poly, rnd) if rnd else np.asarray(poly, float)
        T = T * (self.ms if layer == "muscle" else self.ps if layer == "fat" else 1.0)
        G = self.G
        if proj in ("F", "B"):
            sgn = 1.0 if proj == "F" else -1.0
            lo = (V[:, 0].min(), V[:, 1].min(), G.z[0] if proj == "B" else 230.0)
            hi = (V[:, 0].max(), V[:, 1].max(), G.z[-1] if proj == "F" else 270.0)
        elif proj == "S":
            lo = (20.0, V[:, 1].min(), V[:, 0].min()); hi = (G.x[-1], V[:, 1].max(), V[:, 0].max())
        else:
            lo = (0.0, V[:, 1].min(), G.z[0]); hi = (G.x[-1], V[:, 1].max(), G.z[-1])
        sl = G.box(lo, hi, pad if proj != "W" else 4.0)
        shp = tuple(s.stop - s.start for s in sl)
        X, R, Z = (np.broadcast_to(a, shp) for a in G.coords(sl))
        base = (self.d if on == "stack" else self.layer_d[on])[sl].copy()
        near = (base < 1.6 * T + 2.0) & (base > -8.0)          # only the shell where the sheet can exist
        t = np.zeros(shp, np.float32)
        if near.any():
            x, r, z = X[near].astype(float), R[near].astype(float), Z[near].astype(float)
            zc = self.zc(r)
            if proj in ("F", "B"):
                u, v = x, r
                sd = sd_poly(u, v, V)
                if V[:, 0].min() < wd + 2:                     # the pair meets at the midline
                    sd = np.minimum(sd, sd_poly(-u, v, V))
                side = sstep((sgn * (z - zc) + 4.0) / 12.0)
            elif proj == "S":
                u, v = z, r
                sd = sd_poly(u, v, V)
                side = sstep((x - 22.0) / 16.0)
            else:
                u = np.arctan2(x, z - zc) * RW; v = r
                sd = sd_poly(u, v, V)
                if V[:, 0].min() < wd + 2:
                    sd = np.minimum(sd, sd_poly(-u, v, V))
                if V[:, 0].max() > RW * np.pi - wd - 2:
                    sd = np.minimum(sd, sd_poly(2 * RW * np.pi - u, v, V))
                side = 1.0
            e = np.clip(-sd / wd, 0, 1)
            tt = T * (1.0 - (1.0 - e) ** prof) ** (1.0 / prof) * side
            if mod is not None:
                tt = tt * mod(u, v)
            t[near] = tt
        new = base - t
        cur = self.d[sl]
        self.owner[sl][(t > 0.6) & (base > -3.0) & (new < cur + 0.3)] = len(self.parts) + 1
        self.d[sl] = new if on == "stack" else smin(cur, new, k)
        disp = np.maximum(np.maximum(new, -base - 2.0), 0.3 * T - t)   # the sheet alone, cut where it thins out
        self.parts.append((name, layer, colour, sl, disp))

    def mark(self, layer):
        self.layer_d[layer] = self.d.copy()


# ---------------------------------------------------------------- lofted solids (rib barrel, viscera)
def loft(G, ctrl, p=2.3, cap_top=6.0, cap_bot=6.0, cut=None):
    """Solid whose section at row r is a superellipse: half width a(r), front zf(r), back zb(r).

    ctrl: rows of (r, a, zf, zb). The ends are closed by a dome. cut(theta, R) -> signed distance of an oblique lower
    edge (costal arch). Returns (slices, distance): the implicit function divided by its gradient.
    """
    ctrl = np.asarray(ctrl, float)
    fa, ff, fb = (spline(ctrl[:, (0, i)]) for i in (1, 2, 3))
    r0, r1 = ctrl[0, 0], ctrl[-1, 0]
    amax = ctrl[:, 1].max()
    sl = G.box((0.0, r0 - cap_top, ctrl[:, 3].min()), (amax, r1 + cap_bot, ctrl[:, 2].max()), 26.0)
    X, R, Z = G.coords(sl)
    rc = np.clip(R, r0, r1)
    a = fa(rc); zf = ff(rc); zb = fb(rc)
    zm = 0.5 * (zf + zb); c = 0.5 * (zf - zb)
    dr = np.where(R < r0, (r0 - R) / cap_top, np.where(R > r1, (R - r1) / cap_bot, 0.0))
    f = (np.abs(X / a) ** p + np.abs((Z - zm) / c) ** p + dr ** p) ** (1.0 / p) - 1.0
    f = np.broadcast_to(f, tuple(s.stop - s.start for s in sl)).astype(np.float32)
    g = np.gradient(f, G.h)
    # f + 1 is homogeneous in the row plane, so the in-plane gradient is constant along a ray from the axis while the
    # row gradient grows with the radius: take the row gradient at the surface (divide by f + 1), otherwise the distance
    # collapses far from a part whose section changes fast (the slanted inlet)
    gr = np.where((R >= r0) & (R <= r1), g[0] / np.maximum(f + 1.0, 0.3), g[0])
    d = f / np.maximum(np.sqrt(gr ** 2 + g[1] ** 2 + g[2] ** 2), 1e-3)
    if cut is not None:
        th = np.arctan2(X, Z - zm)
        d = smax(d, np.broadcast_to(cut(th, R), d.shape).astype(np.float32), 3.0)
    return sl, d.astype(np.float32), (fa, ff, fb)


def add_raw(S, name, layer, sl, a, k=0.0, colour=(200, 200, 200), show=True, disp=None):
    cur = S.d[sl]
    S.owner[sl][a < cur] = len(S.parts) + 1
    S.d[sl] = smin(cur, a, k)
    S.parts.append((name, layer, colour, sl, (a if disp is None else disp) if show else None))


# ---------------------------------------------------------------- Male
BONE = (233, 228, 212)
COL = {
    "pec": (196, 92, 84), "delt": (214, 122, 86), "trap": (170, 86, 98), "neck": (186, 110, 110), "rectus": (204, 104, 92),
    "obl": (188, 96, 78), "serr": (222, 140, 110), "lat": (160, 82, 76), "erec": (146, 70, 70), "scap": (200, 112, 96),
    "glmax": (186, 84, 84), "glmed": (208, 116, 100), "tfl": (224, 150, 120), "thigh": (176, 98, 90), "arm": (190, 120, 104),
    "visc": (214, 190, 170), "fat": (240, 214, 150),
}

MALE = dict(
    # spinous tips (r, z); the vertebral bodies sit in front of them
    sp=[(198, 215), (210, 204), (222, 197.5), (235, 194), (250, 194.5), (268, 196.5), (285, 198.5), (300, 199.5), (318, 200),
        (334, 199.5)],
    # rib barrel: r, half width, front (sternum line), back (rib angles). Slanted inlet from T1 (back, r 212) to the
    # manubrium (front, r 250); widest at the lower ribs.
    cage=[(208, 8, 224, 214), (214, 26, 246, 203), (222, 40, 270, 198), (232, 50, 292, 195.5), (242, 57, 308, 195),
          (250, 61, 319, 195.5), (260, 65, 322, 197), (272, 69, 323, 200), (285, 72, 322.5, 202.5), (300, 73, 320, 204.5),
          (312, 72.5, 315, 206), (324, 70.5, 310, 207.5), (336, 66, 303, 209), (346, 62, 297, 211)],
    cage_p=2.7,
    # abdominal cavity: r, half width, front, back
    visc=[(308, 60, 306, 206), (320, 64, 311.5, 206), (332, 65.5, 311.5, 206), (345, 63.5, 310.5, 206), (357, 61, 307, 205),
          (369, 58, 300, 206), (382, 53, 293.5, 210), (394, 44, 287.5, 216), (402, 34, 283, 224)],
    fat=2.5,          # thin layer over the muscles (ghost limbs; the body's own fat is solved per body)
    fat_bone=3.5,     # floor over bare bone
    fill_gap=0.3,     # fat fills the notches up to this depth under their rims (their width is the type's "fill")
    # skin tethers: lines where the skin is tied to what is below it, so the fat does not bridge the crease there
    # (side, radius px, points (x, r)); ANATOMY-LAYERS section 3: a fold is where a pad meets a bone-tied band
    tethers=[
        ("P", 5.0, [(4, 312.5), (12, 318), (26, 324.5), (42, 327.5), (56, 325), (68, 317), (76, 308)]),   # lower border of the pectoral (front; not on a body with breasts)
        ("F", 4.0, [(48, 357), (36, 371), (26, 385), (12, 397)]),                                      # inguinal ligament
        ("B", 4.0, [(19, 214), (19, 246), (24, 259), (44, 263.5), (66, 265.5)]),                       # medial and inferior border of the scapula
        ("B", 3.0, [(0, 368), (0, 412)]),                                                              # intergluteal cleft
        ("S", 4.0, [(268, 258), (271, 284), (280, 308)]),                                              # front border of the arm against the pectoral
        ("B", 5.0, [(2, 404), (20, 407), (40, 405), (52, 399)]),                                       # gluteal fold
    ],
    skin_blur=1.0,    # skin tension
    navel=(7.0, 3.2, 6.0, 7.0),     # rows below the navel landmark, half width, half height, depth
    lm=(184.0, 298.0, 322.0, 358.0, 422.0, 429.0),   # south rows: top, armpit, under-chest fold, navel, crotch, bottom
)

# Body types. ms: thickness of the sheet muscles; pads: named fat pads; tf: fat the frame fit leaves room for (px);
# tmin: least fat anywhere; fill: width of the notches the fat bridges (px); breast: two lobes at the apex landmarks;
# lim: (least, most width scale, most depth shift px) of the frame for the bodies whose size is fat, not bone.
TYPES = {
    "Male": dict(ms=1.0, pads=1.0, tf=2.5, tmin=2.0, fill=5.0),
    "Thin": dict(ms=0.6, pads=0.4, tf=1.8, tmin=1.5, fill=4.0),
    "Hulk": dict(ms=1.35, pads=0.8, tf=2.5, tmin=2.0, fill=4.5),
    "Fat": dict(ms=0.9, pads=1.0, tf=6.0, tmin=4.0, fill=9.0, breast=True, lim=(0.85, 1.15, 12.0)),
    "Female": dict(ms=0.7, pads=1.5, tf=4.0, tmin=3.0, fill=7.0, breast=True),
    "Thin_Female": dict(ms=0.55, pads=0.8, tf=2.5, tmin=2.0, fill=6.0, breast=True),
    "Fat_Female": dict(ms=0.8, pads=1.2, tf=7.0, tmin=4.5, fill=10.0, breast=True, lim=(0.85, 1.15, 12.0)),
    "Hulk_Female": dict(ms=1.15, pads=1.0, tf=3.0, tmin=2.5, fill=5.0, breast=True),
}


def build_male(G, T, prm=MALE, ty=None):
    """The lean stack in the Male frame: bones, viscera, muscles, then the named fat pads. ty = body type (TYPES):
    it scales the sheet muscles and the pads; the fat layer itself is solved per body afterwards (fat_field)."""
    ty = ty or TYPES["Male"]
    zc = lambda R: np.interp(R, T.rows, T.zc).astype(np.float32)
    S = Stack(G, zc, ty["ms"], ty["pads"])
    fsp = spline(prm["sp"])
    th = RW * np.pi / 180.0
    deg = lambda pts: [(a * th, r) for a, r in pts]

    # ---- bones
    # spine: vertebral bodies in front of the spinous tips, one capsule per vertebra from the body to the tip
    vr = np.concatenate([np.linspace(200, 304, 13), np.linspace(310, 334, 5)])
    body_pts = []
    for i, r in enumerate(vr):
        zs = float(fsp(r)); zb = zs + (17 if r > 306 else 14)
        body_pts.append((0, r, zb))
        S.add(f"vertebra {i}", "bone", cone((0, r - 1.5, zb - 3), (0, r + 2.0, zs + 2.2), 4.2, 2.2), colour=BONE, show=False)
    S.add("spine", "bone", tube(body_pts, [6.5] * 13 + [7.8] * 5), colour=BONE)
    S.add("spinous processes", "bone", tube([(0, r + 2.0, float(fsp(r)) + 2.4) for r in vr], 2.3), colour=BONE)

    def costal(a, R):                                         # lower edge of the barrel: xiphoid, flank, 12th rib
        a = np.abs(a)
        front = 318.0 + 20.0 * (1 - np.cos(2 * np.minimum(a, np.pi / 2))) / 2
        back = 312.0 + 26.0 * (1 + np.cos(2 * (a - np.pi / 2))) / 2
        return (R - np.where(a < np.pi / 2, front, back)) * 0.9

    csl, cd, (ca, cf, cb) = loft(G, prm["cage"], p=prm["cage_p"], cap_top=5.0, cap_bot=4.0, cut=costal)
    X, R, Z = G.coords(csl)                                   # display: ribs = a shell of the barrel cut into slanted bands
    q = (R - 0.22 * (Z - 200.0)) / 11.5
    ribs = np.maximum(np.abs(cd + 2.6) - 2.6, (np.abs(q - np.round(q)) - 0.30) * 9.0).astype(np.float32)
    add_raw(S, "rib cage", "bone", csl, cd, colour=BONE, disp=ribs)
    S.add("sternum", "bone", tube([(0, 249, float(cf(249)) + 0.5), (0, 285, float(cf(285)) + 0.5), (0, 314, float(cf(314)) - 2.0)], [5.2, 4.6, 3.0]), colour=BONE)
    S.add("clavicle", "bone", tube([(5, 251, 321), (22, 253, 321.5), (44, 247, 316), (60, 241, 302), (74, 236, 281)], [4.2, 3.6, 3.4, 3.4, 3.8]), colour=BONE)
    # scapula: blade on the back of the barrel, spine of the scapula up to the acromion
    sup, inf, gle, med = (21, 209, 199.5), (25, 258, 196.5), (63, 240, 228), (19.5, 224, 195.5)
    S.add("scapula", "bone", tri(sup, inf, gle, 1.8), colour=BONE)
    S.add("scapula medial", "bone", tri(sup, med, inf, 1.8), colour=BONE, show=False)
    S.add("scapular spine", "bone", tube([(20, 221, 193.5), (48, 226, 200), (70, 232, 228), (76, 234.5, 262), (74, 236, 280)], [2.6, 3.0, 3.6, 4.0, 3.6]), colour=BONE)
    S.add("humerus", "bone", tube([(76, 252, 256), (79, 272, 252), (81, 296, 250)], [12.0, 6.5, 6.0]), colour=BONE)
    # pelvis
    psis, crest1, crest2, tub, asis = (13, 330, 200.5), (36, 323, 210), (56, 328, 233), (63, 337, 256), (51, 352, 286)
    acet, pub, isch = (37, 387, 250), (0, 400, 284), (27, 411, 233)
    S.add("iliac crest", "bone", tube([psis, crest1, crest2, tub, asis], [4.0, 3.6, 3.6, 3.8, 4.2]), colour=BONE)
    for i, (a, b) in enumerate(((psis, crest1), (crest1, crest2), (crest2, tub), (tub, asis))):
        S.add(f"iliac wing {i}", "bone", tri(a, b, acet, 2.4), colour=BONE)
    S.add("sacrum", "bone", tri((-13, 330, 199.5), (13, 330, 199.5), (0, 372, 203), 4.5), colour=BONE)
    S.add("coccyx", "bone", cone((0, 372, 203), (0, 388, 214), 3.2, 2.0), colour=BONE)
    S.add("pubis", "bone", tube([pub, (18, 394, 276), acet], [5.0, 4.6, 6.0]), colour=BONE)
    S.add("ischium", "bone", tube([acet, isch, (6, 406, 262), pub], [6.0, 6.5, 3.6, 4.0]), colour=BONE)
    S.add("femur", "bone", tube([acet, (47, 388, 247), (52, 391, 245), (46, 405, 247)], [11.0, 7.0, 7.5, 5.5]), colour=BONE)
    S.mark("bone")

    # ---- viscera
    vsl, vd, _ = loft(G, prm["visc"], p=2.3, cap_top=10.0, cap_bot=8.0)
    add_raw(S, "viscera", "viscera", vsl, vd, colour=COL["visc"])
    S.mark("core")

    # ---- deep masses: arm stump, and the WDI dome above the clavicle and the scapular spine (neck base, upper trapezius)
    S.add("arm stump (humerus muscles)", "muscle", ell((81, 278, 251), (11.5, 27, 16)), k=2.0, colour=COL["arm"])
    S.add("neck base", "muscle", ell((0, 240, 246), (46, 30, 70), rad2=(46, 49, 58)), k=2.0, colour=COL["neck"])
    S.add("trapezius (upper)", "muscle", ell((37, 240, 234), (55, 60, 88), rad2=(55, 53.5, 49)), k=8.0, colour=COL["trap"], km=8.0)

    # ---- trunk, front
    def serr(i, zc_, rc_):
        ax = rotm(side=-32.0) @ np.array([0, 1.0, 0])          # fingers run down and forward along the ribs
        V = [(zc_ + ax[2] * a * 13 + ax[1] * b * 4.5, rc_ + ax[1] * a * 13 - ax[2] * b * 4.5) for a, b in
             ((-1, 0), (-0.6, 0.85), (0.3, 1), (0.9, 0.5), (1, 0), (0.9, -0.5), (0.3, -1), (-0.6, -0.85))]
        S.lens(f"serratus {i}", "muscle", "S", V, 1.4, 4.5, colour=COL["serr"], rnd=1, prof=1.5)

    for i, (z_, r_) in enumerate(((270, 297), (274, 307), (277, 317), (279, 327))):
        serr(i, z_, r_)

    # the two pectorals meet on the sternum (the polygon crosses the midline, so the pair is one sheet there); they thin
    # toward it, which leaves the sternal furrow as a shallow valley and not a bare strip of bone
    pec = [(-1, 255), (-1, 309), (11, 316), (26, 322.5), (42, 325.5), (56, 323), (68, 315), (76, 305), (80, 288), (80, 268),
           (78, 252), (72, 243), (60, 244.5), (44, 250), (24, 256), (8, 255)]
    S.lens("pectoralis major", "muscle", "F", pec, 11.5, 5.5, colour=COL["pec"],
           mod=lambda u, v: (0.7 + 0.3 * sstep((v - (255.0 - 0.17 * np.abs(u))) / 38.0)) * (0.68 + 0.32 * sstep(np.abs(u) / 14.0)))

    # rectus abdominis: four blocks a side, tendinous intersections between them, linea alba at the midline
    xo = lambda r: 26.0 - 9.0 * sstep((r - 330.0) / 68.0)
    for i, (ra, rb) in enumerate(((325.0, 340.7), (341.0, 353.8), (354.1, 369.8), (370.1, 399.0))):
        V = [(0.5, ra), (xo(ra), ra), (xo(rb), rb), (0.5, rb)]
        S.lens(f"rectus abdominis {i}", "muscle", "F", V, 3.2 if i < 3 else 2.8, 9.0, colour=COL["rectus"], rnd=1, prof=1.3, on="core")

    # external oblique: from the lower ribs (thin, under the pectoral border) to the iliac crest and the inguinal ligament;
    # its medial edge runs under the rectus sheath
    obl = [(20, 327), (60, 327), (100, 330), (140, 332), (172, 329), (172, 344), (135, 350), (110, 354), (88, 362), (62, 374),
           (42, 388), (20, 392)]
    S.lens("external oblique", "muscle", "W", obl, 8.0, 12.0, colour=COL["obl"], prof=1.3, on="core",
           mod=lambda u, v: (0.4 + 0.6 * sstep((u - 30.0) / 55.0)) * (0.45 + 0.55 * sstep((v - 322.0) / 18.0)))

    # ---- trunk, back
    er = [(6.5, 224, 5.0, 4.5), (7, 250, 6.0, 4.5), (8.5, 285, 8.0, 6.5), (10.5, 310, 10.0, 8.5), (9.5, 332, 8.5, 6.7), (6.5, 346, 5.0, 5.5)]
    S.add("erector spinae", "muscle", tube([(x, r, float(fsp(r)) + dz) for x, r, rad, dz in er], [p[2] for p in er]), k=1.5,
          colour=COL["erec"], km=1.0)

    scap = [(19, 208), (19, 246), (24, 258), (44, 262), (66, 264), (84, 254), (88, 238), (72, 222), (44, 212)]
    S.lens("infraspinatus, teres, rhomboid", "muscle", "B", scap, 4.8, 7.0, colour=COL["scap"], on="core",
           mod=lambda u, v: 1.0 - 0.3 * sstep((v - 236.0) / 26.0))

    # latissimus dorsi: one fan. Origin on the spine from T7 down to the sacrum and along the iliac crest, free border
    # up the flank, all fibres converging on the humerus behind the armpit; thinner over its lumbar aponeurosis
    lat = [(181, 262), (181, 340), (150, 343), (122, 343), (102, 336), (97, 314), (98, 298), (103, 286), (112, 277), (130, 266),
           (154, 258)]
    S.lens("latissimus dorsi", "muscle", "W", deg(lat), 8.0, 10.0, colour=COL["lat"], prof=1.25,
           mod=lambda u, v: 0.55 + 0.45 * sstep((228.0 - u) / 70.0))

    trap = [(-1, 215), (30, 215), (62, 224), (80, 234), (62, 240), (38, 236), (22, 246), (9, 272), (-1, 302)]
    S.lens("trapezius (middle, lower)", "muscle", "B", trap, 2.6, 10.0, colour=COL["trap"], prof=1.2)
    # thoracolumbar fascia with the multifidus under it: from the lumbar erectors onto the sacrum, between the two PSIS
    S.lens("thoracolumbar fascia, multifidus", "muscle", "B", [(-1, 296), (24, 302), (38, 318), (30, 332), (15, 341), (-1, 354)], 2.6, 11.0,
           colour=COL["erec"], prof=1.2)

    # ---- shoulder
    S.add("deltoid", "muscle", ell((78, 264, 254), (16.5, 38, 30), rad2=(16.5, 30, 30)), k=1.5, colour=COL["delt"])

    # ---- pelvis and thigh stump
    S.add("gluteus medius", "muscle", ell((48, 346, 236), (24, 25, 34), rot=(12, 0, 0)), k=3.0, colour=COL["glmed"])
    S.add("gluteus maximus", "muscle", ell((23, 370, 224.5), (30, 36, 36.5), rad2=(30, 52, 37.5), rot=(18, 0, 0)), k=2.5, colour=COL["glmax"], km=6.0)
    S.add("tensor fasciae latae, hip flexors", "muscle", ell((55, 372, 264), (13.5, 27, 21)), k=6.0, colour=COL["tfl"])
    S.add("thigh stump (quadriceps, adductors, hamstrings)", "muscle", ell((35, 396, 242.5), (19, 36, 44), rad2=(19, 36, 47), rot=(-46, 0, 0)), k=6.0,
          colour=COL["thigh"], km=2.0)
    S.mark("muscle")

    # ---- named fat pads (the fat layer itself is solved per body: fat_field)
    soft = dict(prof=1.0, rnd=2, colour=COL["fat"])
    S.lens("fat pad, flank", "fat", "W", deg([(88, 324), (130, 318), (156, 332), (136, 354), (98, 358), (80, 342)]), 2.5, 16.0, **soft)
    S.lens("fat pad, lower abdomen", "fat", "F", [(0, 362), (26, 362), (40, 378), (30, 394), (12, 399), (0, 399)], 2.2, 16.0, **soft)
    S.lens("fat pad, pubis", "fat", "F", [(0, 392), (10, 392), (16, 400), (9, 409), (0, 409)], 4.0, 7.0, **soft)
    S.lens("fat pad, lower medial gluteal", "fat", "B", [(4, 382), (24, 379), (40, 390), (30, 402), (8, 404)], 2.5, 12.0, **soft)
    return S


def build_ghost(G, T, prm=MALE):
    """The limbs the sprite cuts off: neck, arms to the elbow, thighs to the knee. Real anatomy that continues the
    stack outside the WDI frame; its own stack, never unioned with the body, so the viewer can take it away."""
    zc = lambda R: np.interp(R, T.rows, T.zc).astype(np.float32)
    S = Stack(G, zc)
    # ---- neck: cervical spine, the column of deep neck muscles, sternocleidomastoid, the trapezius up to the skull
    csp = spline([(125, 230), (140, 229), (160, 226), (180, 221), (198, 215)])
    cr = np.linspace(128, 196, 7)
    S.add("cervical spine", "bone", tube([(0, r, float(csp(r)) + 13) for r in cr], 6.0), colour=BONE)
    S.add("cervical spinous processes", "bone", tube([(0, r + 2.0, float(csp(r)) + 2.4) for r in cr], 2.2), colour=BONE)
    # a neck is about a third of the shoulder width; the two bumps on top of the sprite (40 px each side) are the
    # trapezius, not the neck
    nsl, nd, _ = loft(G, [(120, 16, 256, 222), (150, 16.5, 258, 221), (180, 18, 262, 219), (200, 22, 268, 216), (228, 30, 284, 210)], p=2.2, cap_top=3.0, cap_bot=6.0)
    add_raw(S, "neck (scalenes, levator, splenius)", "muscle", nsl, nd, colour=COL["neck"])
    S.add("trapezius (neck part)", "muscle", cone((40, 214, 226), (12, 134, 229), 17.0, 7.0), k=8.0, colour=COL["trap"], km=6.0)
    S.add("sternocleidomastoid", "muscle", cone((17, 128, 236), (6, 249, 316), 4.5, 4.0), k=1.5, colour=COL["pec"])
    # ---- arm: humerus to the elbow, biceps in front, triceps behind
    S.add("humerus (shaft)", "bone", tube([(81, 290, 250), (86, 350, 251), (90, 402, 252)], [6.0, 5.5, 8.5]), colour=BONE)
    S.add("biceps, brachialis", "muscle", ell((86, 346, 261), (10.0, 50, 11.0), rot=(5, 0, 0)), k=2.0, colour=COL["arm"])
    S.add("triceps", "muscle", ell((87, 340, 242), (10.5, 56, 12.5), rot=(5, 0, 0)), k=2.0, colour=COL["delt"])
    # ---- thigh: femur to the knee, quadriceps, hamstrings, adductors
    S.add("femur (shaft)", "bone", tube([(47, 400, 247), (44, 470, 250), (42, 540, 252)], [6.0, 6.0, 10.0]), colour=BONE)
    S.add("quadriceps", "muscle", ell((41, 468, 263), (21.0, 80, 21.0)), k=3.0, colour=COL["thigh"])
    S.add("hamstrings", "muscle", ell((37, 470, 233), (19.5, 78, 19.0)), k=3.0, colour=COL["glmax"])
    S.add("adductors", "muscle", ell((19, 446, 249), (15.0, 52, 22.0), rot=(-6, 0, 0)), k=3.0, colour=COL["tfl"], km=1.0)
    S.mark("muscle")
    bone = G.full()
    for name, layer, colour, sl, a in S.parts:
        if layer == "bone" and a is not None:
            bone[sl] = np.minimum(bone[sl], a)
    d = np.minimum(S.d - prm["fat"], bone - prm["fat_bone"])
    S.skin = ndi.gaussian_filter(np.clip(d, -20, 20), 1.5 / G.h, mode=SYM).astype(np.float32)
    return S


SYM = ("nearest", "mirror", "nearest")     # x = 0 is the mirror plane of the half grid [r, x, z]


def breast_rows(T):
    """(top row, apex row, fold row, apex half spacing) of the breast lobes from the south landmarks, or None."""
    P = T.P["south"]
    if "breast apex L" not in P or "under-breast fold L" not in P:
        return None
    xa = abs(P["breast apex L"][0] - T.cxs); ra = P["breast apex L"][1]; rf = P["under-breast fold L"][1]
    return ra - 2.2 * (rf - ra), ra, rf, xa


def frame_target(T, ty):
    """Silhouettes the frame (bones and muscles) is fitted to. On a body with breasts the front is bridged over the
    breast rows, so the frame follows the chest wall and the lobes are left to the fat."""
    zf = T.zf.copy()
    br = breast_rows(T) if ty.get("breast") else None
    if br:
        a, b = br[0], br[2] + 6.0
        sel = (T.rows >= a) & (T.rows <= b)
        za, zb = T.at(T.zf, a), T.at(T.zf, b)
        zf[sel] = np.minimum(zf[sel], za + (T.rows[sel] - a) / (b - a) * (zb - za))
    return T.hw, zf, T.zb


def redistance(G, d, keep=4.0):
    """A field that is a distance everywhere: the stack's own field near its surface (it is exact there), the
    Euclidean distance to that surface beyond. The fat of a fat body is thicker than the range of the stack's field."""
    inside = d < 0
    far = (ndi.distance_transform_edt(~inside) - ndi.distance_transform_edt(inside)) * G.h
    far = ndi.gaussian_filter(far - 0.5 * G.h * np.sign(far), 1.0, mode=SYM)
    w_ = sstep((np.abs(far) - keep) / keep)
    return (np.clip(d, -3 * keep, 3 * keep) * (1 - w_) + far * w_).astype(np.float32)


def fat_field(G, lean, bone, T, ty, prm=MALE):
    """Fat solved per body: per row, what the three silhouettes show beyond the lean stack is fat, spread around the
    section (front, flanks, back), never under the type's least thickness, never under the floor over bare bone.
    On a body with breasts the front fat of the breast rows gathers in two lobes at the apex landmarks."""
    hw, zf, zb = profiles(G, lean)
    ok = np.isfinite(hw) & np.isfinite(zf)
    i0, i1 = np.flatnonzero(ok)[[0, -1]]
    r = G.r.astype(float)
    es = np.interp(r, T.rows, T.hw) - hw; ef = np.interp(r, T.rows, T.zf) - zf; eb = zb - np.interp(r, T.rows, T.zb)
    # near the two tips the surface is almost horizontal, a depth difference there is not a thickness: taper to the base fat
    edge = sstep((r - r[i0]) / 16.0) * sstep((r[i1] - r) / 16.0)
    out = []
    for e in (es, ef, eb):
        e = np.where(ok, e, 0.0); e[:i0] = e[i0]; e[i1 + 1:] = e[i1]
        e = ty["tf"] + (e - ty["tf"]) * edge
        out.append(ndi.gaussian_filter1d(e, 5.0 / G.h, mode="nearest"))
    es, ef, eb = (e[:, None, None] for e in out)
    X, R, Z = G.coords((slice(None), slice(None), slice(None)))
    zc = np.interp(R, T.rows, T.zc)
    rho = np.maximum(np.hypot(X, Z - zc), 1e-3)
    c = (Z - zc) / rho; s2 = (X / rho) ** 2
    wf = np.clip(c, 0, 1) ** 2; wb = np.clip(-c, 0, 1) ** 2
    br = breast_rows(T) if ty.get("breast") else None
    if br:
        top, ra, rf, xa = br
        rowgate = sstep((R - top) / max(ra - top, 1.0)) * (1.0 - sstep((R - rf) / max(0.4 * (rf - ra), 5.0)))
        lobes = np.exp(-((X - xa) / (0.72 * xa)) ** 2)        # two lobes (the mirror gives the other), a cleavage between them
        wf = wf * (1.0 - rowgate) + rowgate * (0.25 * wf + 0.75 * lobes * (c > 0))
    t = np.maximum(ef * wf + eb * wb + es * s2, ty["tmin"])
    return np.minimum(redistance(G, lean) - t, bone - prm["fat_bone"]).astype(np.float32)


def skin_of(G, d, T, ty, frame, prm=MALE):
    """Skin = outside of the stack with its fat. Fat fills the notches (a narrow hollow is bridged, a ridge is kept)
    except along the skin tethers, the navel is a pit tied to the linea alba, and the skin tension is a small blur
    (a crease keeps a finite radius). frame: the Fit that put the Male frame on this body (tethers follow it)."""
    zc = np.interp(G.r, T.rows, T.zc)
    sig = ty["fill"]
    if sig > 0:
        # 1 = the fat may bridge, 0 = tethered; front and back maps in (r, x), flank map in (r, z)
        free = {"F": np.ones(d.shape[:2], np.float32), "B": np.ones(d.shape[:2], np.float32), "S": np.ones((d.shape[0], d.shape[2]), np.float32)}
        R2 = G.r[:, None].astype(float)
        teth = []
        for side, rho, pts in prm.get("tethers", ()):
            if side == "P":                                    # pectoral border: only where no breast hides it
                if ty.get("breast"):
                    continue
                side = "F"
            a = np.asarray(pts, float)
            if side == "S":
                _, rr, zz = frame.forward(np.full(len(a), 60.0), a[:, 1], a[:, 0])
                teth.append((side, rho, np.stack([zz, rr], 1)))
            else:
                xx, rr, _ = frame.forward(a[:, 0], a[:, 1], np.full(len(a), 260.0))
                teth.append((side, rho, np.stack([xx, rr], 1)))
        br = breast_rows(T) if ty.get("breast") else None
        if br:                                                 # the under-breast fold
            top, ra, rf, xa = br
            teth.append(("F", 4.0, np.array([(0.3 * xa, rf - 1.0), (xa, rf + 1.5), (1.7 * xa, rf - 2.0)])))
        for side, rho, pts in teth:
            U2 = (G.z if side == "S" else G.x)[None, :].astype(float)
            dist = np.full((R2.shape[0], U2.shape[1]), 1e9)
            for (xa_, ra_), (xb_, rb_) in zip(pts[:-1], pts[1:]):
                ex, er = xb_ - xa_, rb_ - ra_
                t = np.clip(((U2 - xa_) * ex + (R2 - ra_) * er) / (ex * ex + er * er), 0, 1)
                dist = np.minimum(dist, np.hypot(U2 - xa_ - ex * t, R2 - ra_ - er * t))
            free[side] = np.minimum(free[side], sstep((dist - 0.5 * rho) / rho))
        front = (G.z[None, None, :] > zc[:, None, None])
        wgt = np.where(front, free["F"][:, :, None], free["B"][:, :, None])
        wgt = np.where(G.x[None, :, None] > 45.0, np.minimum(wgt, free["S"][:, None, :]), wgt)
        band = 2.0 * sig                                       # the field is only a distance near the stack: clamp it before the blur
        d = np.minimum(d, ndi.gaussian_filter(np.clip(d, -band, band), sig / G.h, mode=SYM) + prm["fill_gap"] + 8.0 * (1.0 - wgt))
    P = T.P["south"]
    if prm.get("navel") and "navel" in P:
        k = (T.s1 - T.s0) / 245.0
        dr, a, b, c = prm["navel"]
        r0 = P["navel"][1] + dr * k
        i = int(np.argmin(np.abs(G.r - r0)))
        zs = float(last_cross(d[i:i + 1, 0:1, :], 2, G.z)[0, 0])
        if np.isfinite(zs):
            fn, lo, hi = ell((0, r0, zs + 0.5), (a * k, b * k, c * k))
            sl = G.box(lo, hi, 4.0)
            d = d.copy()
            d[sl] = smax(d[sl], -np.broadcast_to(fn(*G.coords(sl)), d[sl].shape).astype(np.float32), 1.5)
    if prm["skin_blur"] > 0:
        d = ndi.gaussian_filter(d, prm["skin_blur"] / G.h, mode=SYM)
    return d.astype(np.float32)


# ---------------------------------------------------------------- reading a field
def last_cross(d, axis, coords, outward=True):
    """Coordinate along `axis` of the outermost inside-to-outside crossing (NaN where the line misses the solid)."""
    d = np.moveaxis(d, axis, -1)
    if not outward:
        d = d[..., ::-1]; coords = coords[::-1]
    inside = d < 0
    n = d.shape[-1]
    idx = n - 1 - np.argmax(inside[..., ::-1], axis=-1)
    hit = inside.any(axis=-1)
    idx = np.clip(idx, 0, n - 2)
    a = np.take_along_axis(d, idx[..., None], -1)[..., 0]; b = np.take_along_axis(d, idx[..., None] + 1, -1)[..., 0]
    t = np.clip(a / np.minimum(a - b, -1e-6), 0, 1)
    out = coords[idx] + t * (coords[idx + 1] - coords[idx])
    return np.where(hit, out, np.nan)


def profiles(G, d):
    """Half width, front and back of the solid per grid row."""
    xmax = last_cross(d, 1, G.x)                              # (r, z)
    zf = last_cross(d, 2, G.z)                                # (r, x)
    zb = last_cross(d, 2, G.z, outward=False)
    with np.errstate(all="ignore"):
        return np.nanmax(xmax, axis=1), np.nanmax(zf, axis=1), np.nanmin(zb, axis=1)


# ---------------------------------------------------------------- fit: row-wise affine of the whole stack onto the silhouettes
def lin(x, xp, fp):
    """np.interp with linear extrapolation past both ends."""
    xp = np.asarray(xp, float); fp = np.asarray(fp, float); x = np.asarray(x, float)
    y = np.interp(x, xp, fp)
    s0 = (fp[1] - fp[0]) / (xp[1] - xp[0]); s1 = (fp[-1] - fp[-2]) / (xp[-1] - xp[-2])
    return np.where(x < xp[0], fp[0] + (x - xp[0]) * s0, np.where(x > xp[-1], fp[-1] + (x - xp[-1]) * s1, y))


class Fit:
    """x' = x * sx(r); z' moves the front by df(r) and the back by db(r), linearly from the mid depth; r' = rowmap(r).

    rowmap: (source rows, target rows), piecewise linear (default: top and bottom of the solid onto the sprite's).
    shrink: px taken off the target on every side (room left for the fat). tgt: (hw, zf, zb) on T.rows instead of
    T's own. lim: (least, most width scale, most depth shift) for a frame that must not grow with the fat.
    """

    def __init__(self, G, d, T, sigma=5.0, rowmap=None, shrink=0.0, tgt=None, lim=None, trim=0.0):
        hw, zf, zb = profiles(G, d)
        ok = np.isfinite(hw) & np.isfinite(zf)
        r = G.r[ok]
        if rowmap is None:
            rowmap = ([r[0], r[-1]], [T.s0, T.s1])
        self.rm = (np.asarray(rowmap[0], float), np.asarray(rowmap[1], float))
        rt = lin(G.r, *self.rm)                                # target row of each grid row
        thw, tzf, tzb = tgt if tgt is not None else (T.hw, T.zf, T.zb)
        hw_t = np.interp(rt, T.rows, thw) - shrink; zf_t = np.interp(rt, T.rows, tzf) - shrink; zb_t = np.interp(rt, T.rows, tzb) + shrink
        sx = np.where(ok, hw_t / np.maximum(hw, 1.0), 1.0)
        df = np.where(ok, zf_t - zf, 0.0); db = np.where(ok, zb_t - zb, 0.0)
        i0, i1 = np.flatnonzero(ok)[[0, -1]]
        j0, j1 = i0 + int(trim / G.h), i1 - int(trim / G.h)   # trim: the closing tips say nothing about the frame
        for a in (sx, df, db):
            a[:j0] = a[j0]; a[j1 + 1:] = a[j1]
        sg = sigma / G.h
        self.r = G.r.astype(float)
        self.sx = np.clip(ndi.gaussian_filter1d(sx, sg, mode="nearest"), 0.4, 2.2)
        self.df = ndi.gaussian_filter1d(df, sg, mode="nearest"); self.db = ndi.gaussian_filter1d(db, sg, mode="nearest")
        if lim:
            self.sx = np.clip(self.sx, lim[0], lim[1]); self.df = np.clip(self.df, -lim[2], lim[2]); self.db = np.clip(self.db, -lim[2], lim[2])
        self.zf = np.where(ok, zf, np.nan); self.zb = np.where(ok, zb, np.nan)
        for a in (self.zf, self.zb):
            a[:i0] = a[i0]; a[i1 + 1:] = a[i1]
        self.valid = (float(r[0]), float(r[-1]))               # source rows where the solid exists
        self.raw = dict(hw=np.where(ok, hw_t - hw, np.nan), df=np.where(ok, df, np.nan), db=np.where(ok, db, np.nan))

    def stats(self):
        out = {}
        for k, v in self.raw.items():
            v = np.abs(v[np.isfinite(v)])
            out[k] = (float(v.mean()), float(np.percentile(v, 95)), float(v.max()))
        return out

    def _row(self, r):
        sx = np.interp(r, self.r, self.sx); df = np.interp(r, self.r, self.df); db = np.interp(r, self.r, self.db)
        zf = np.interp(r, self.r, self.zf); zb = np.interp(r, self.r, self.zb); zm = 0.5 * (zf + zb)
        # the shift of one side never exceeds 3/4 of the half depth of its row: the map stays one to one at the tips
        hf = np.maximum(zf - zm, 1e-3); hb = np.maximum(zm - zb, 1e-3)
        return sx, np.maximum(df, -0.75 * hf), np.minimum(db, 0.75 * hb), zf, zb, zm, hf, hb

    def forward(self, x, r, z, rc=None):
        """Model point -> fitted point (arrays). rc: rows to read the width and depth correction from (default r)."""
        sx, df, db, zf, zb, zm, hf, hb = self._row(r if rc is None else rc)
        up = np.clip((z - zm) / hf, 0, 1); dn = np.clip((zm - z) / hb, 0, 1)
        return x * sx, lin(r, *self.rm), z + up * df + dn * db

    def warp(self, G, d, order=1, Gd=None):
        """The field of the fitted solid on the grid Gd (default: the same grid): inverse map, then resample."""
        Gd = Gd or G
        r_src = lin(Gd.r, self.rm[1], self.rm[0])
        sx, df, db, zf, zb, zm, hf, hb = self._row(r_src)
        kf = 1.0 + df / hf; kb = 1.0 - db / hb
        Z = Gd.z.astype(float)[None, :]
        zs = np.where(Z >= zm[:, None], zm[:, None] + (Z - zm[:, None]) / kf[:, None], zm[:, None] - (zm[:, None] - Z) / kb[:, None])
        zs = np.where(Z > (zf + df)[:, None], Z - df[:, None], zs); zs = np.where(Z < (zb + db)[:, None], Z - db[:, None], zs)
        ri = (r_src - G.r[0]) / G.h
        xi = (Gd.x.astype(float)[None, :] / sx[:, None]) / G.h
        zi = (zs - G.z[0]) / G.h
        co = np.empty((3,) + Gd.shape, np.float32)
        co[0] = ri[:, None, None]; co[1] = xi[:, :, None]; co[2] = zi[:, None, :]
        return ndi.map_coordinates(d, co, order=order, mode="nearest").astype(np.float32)


# ---------------------------------------------------------------- fields in the sprite frames
def sprite_fields(G, d, T):
    """Height fields of the solid in the three sprite frames (512 px), above the centre plane, and the model's masks."""
    zf = last_cross(d, 2, G.z); zb = last_cross(d, 2, G.z, outward=False); xm = last_cross(d, 1, G.x)
    rows = np.arange(N, dtype=float); cols = np.arange(N, dtype=float)

    def resample(a, rr, cc):
        """a on (G.r, axis) -> values at rows rr and axis coordinates cc (bilinear, NaN outside)."""
        ax = G.x if a.shape[1] == len(G.x) else G.z
        ri = (rr - G.r[0]) / G.h; ci = (cc - ax[0]) / G.h
        fin = np.isfinite(a).astype(np.float32)
        v = ndi.map_coordinates(np.nan_to_num(a), [ri[:, None] + 0 * ci[None, :], 0 * ri[:, None] + ci[None, :]], order=1, cval=0.0)
        wgt = ndi.map_coordinates(fin, [ri[:, None] + 0 * ci[None, :], 0 * ri[:, None] + ci[None, :]], order=1, cval=0.0)
        return np.where(wgt > 0.5, v / np.maximum(wgt, 1e-6), np.nan)

    zc_s = np.interp(rows, T.rows, T.zc)
    S = resample(zf, rows, np.abs(cols - T.cxs)) - zc_s[:, None]
    rn = T.s0 + (rows - T.n0) / (T.n1 - T.n0) * (T.s1 - T.s0)          # north row -> south row
    Nn = np.interp(rn, T.rows, T.zc)[:, None] - resample(zb, rn, np.abs(cols - T.cxn))
    re = T.s0 + (rows - T.e0) / (T.e1 - T.e0) * (T.s1 - T.s0)          # east row -> south row
    E = resample(xm, re, cols)
    out = {}
    for k, a in (("south", S), ("north", Nn), ("east", E)):
        m = np.isfinite(a)
        out[k] = (np.where(m, np.maximum(a, 0.0), 0.0), m)
    return out


def sil_error(m, ref):
    """Distances (px) between the boundaries of two masks, both ways."""
    ea = m & ~ndi.binary_erosion(m); eb = ref & ~ndi.binary_erosion(ref)
    da = ndi.distance_transform_edt(~eb)[ea]; db = ndi.distance_transform_edt(~ea)[eb]
    dd = np.concatenate([da, db])
    return float(np.percentile(dd, 95)), float(dd.mean()), float(dd.max())


# ---------------------------------------------------------------- previews
def lit(h, m, owner=None, palette=None):
    """Lambert preview of a height field (light upper left front), optionally tinted by the owning muscle."""
    gy, gx = np.gradient(ndi.gaussian_filter(np.where(m, h, 0.0), 0.7))
    n = np.stack([-gx, -gy, np.ones_like(gx)], -1); n /= np.linalg.norm(n, axis=-1, keepdims=True)
    L = np.array([-0.35, -0.60, 0.72]); L /= np.linalg.norm(L)
    sh = 0.22 + 0.78 * np.clip(n @ L, 0, 1)
    col = np.ones(h.shape + (3,)) * 0.93
    if owner is not None:
        col = palette[owner] / 255.0
    rgb = col * sh[..., None]
    rgb[~m] = np.array([226, 226, 222]) / 255.0
    return (255 * np.clip(rgb, 0, 1)).astype(np.uint8)


def oblique(G, d, owner, palettes, angle, scale=1.0):
    """Lit views (one per palette) of the solid turned by `angle` degrees around the vertical axis (0 = south, 180 = north)."""
    full = np.concatenate([d[:, :0:-1], d], axis=1)            # mirror onto x < 0
    own = np.concatenate([owner[:, :0:-1], owner], axis=1)
    rot = ndi.rotate(full, angle, axes=(1, 2), reshape=True, order=1, cval=BIG, mode="constant") if angle % 360 else full
    rown = ndi.rotate(own, angle, axes=(1, 2), reshape=True, order=0, cval=0, mode="constant") if angle % 360 else own
    zs = np.arange(rot.shape[2], dtype=float) * G.h
    zf = last_cross(rot, 2, zs)
    m = np.isfinite(zf)
    iz = np.clip(np.round(np.nan_to_num(zf) / G.h).astype(int) - 1, 0, rot.shape[2] - 1)
    ow = np.take_along_axis(rown, iz[..., None], 2)[..., 0]
    k = G.h * scale
    out = []
    for pal in palettes:
        im = Image.fromarray(lit(np.nan_to_num(zf) / G.h, m, ow, pal))
        out.append(im.resize((max(int(im.width * k), 1), max(int(im.height * k), 1)), Image.LANCZOS))
    return out


def palette_of(S):
    pal = np.full((len(S.parts) + 2, 3), 236.0)
    for i, (name, layer, colour, sl, a) in enumerate(S.parts):
        pal[i + 1] = colour
    return pal


def board(S, G, d, T, tag, owner, extra=""):
    """Two boards: <tag>-views (WDI | toon capture of the stack | outlines, three views) and <tag>-lit (lit previews,
    plain and coloured by muscle, at 0, 35, 90, 145, 180 degrees)."""
    F = sprite_fields(G, d, T)
    tiles = []; rep = {}
    for f in ("south", "north", "east"):
        h, m = F[f]
        wd = w.outline_width(T.imgs[f], T.M[f])
        cap = w.capture(h, m, wd, w.areolae(T.imgs[f], T.M[f]))
        mae, blank = w.score(cap, T.imgs[f], T.M[f], wd)
        p95, mean, mx = sil_error(m, T.M[f])
        rep[f] = dict(mae=mae, blank=blank, p95=p95, mean=mean, max=mx)
        ys, xs = np.nonzero(T.M[f] | m)
        box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(N, xs.max() + 7), min(N, ys.max() + 7))
        a = Image.fromarray(w.on_bg(T.imgs[f])).crop(box); b = Image.fromarray(w.on_bg(cap)).crop(box)
        ov = np.full((N, N, 3), 236, np.uint8)
        ea = T.M[f] & ~ndi.binary_erosion(T.M[f]); eb = m & ~ndi.binary_erosion(m)
        ov[ea] = (220, 40, 40); ov[eb] = (40, 60, 220); ov[ea & eb] = (30, 30, 30)
        tiles.append((f, a, b, Image.fromarray(ov).crop(box)))
    Wd = sum(a.width * 3 + 16 for _, a, _, _ in tiles); Hh = max(a.height for _, a, _, _ in tiles) + 18
    out = Image.new("RGB", (Wd, Hh), (235, 235, 230)); dr = ImageDraw.Draw(out); x = 0
    for f, a, b, c in tiles:
        r = rep[f]
        dr.text((x + 2, 2), f"{f}: WDI | stack | outlines (red WDI, blue stack)  sil p95 {r['p95']:.1f} lum {r['mae']:.3f} (blank {r['blank']:.3f}) {extra}", fill=(0, 0, 0))
        out.paste(a, (x, 16)); out.paste(b, (x + a.width + 2, 16)); out.paste(c, (x + 2 * a.width + 4, 16)); x += a.width * 3 + 16
    CAPT.mkdir(exist_ok=True)
    path = CAPT / f"2026-11-10_stack3d-{tag}-{T.body}-views.png"
    out.save(path)
    pal = palette_of(S); white = np.full_like(pal, 236.0)
    cols_ = [oblique(G, d, owner, (white, pal), a, 1.3) for a in (0, 35, 90, 145, 180)]
    rows_ = [[c[j] for c in cols_] for j in (0, 1)]
    Wd = sum(o.width + 6 for o in rows_[0]); Hh = max(o.height for o in rows_[0])
    lit_ = Image.new("RGB", (Wd, 2 * Hh + 6), (235, 235, 230))
    for j, row in enumerate(rows_):
        x = 0
        for o in row:
            lit_.paste(o, (x, j * (Hh + 6))); x += o.width + 6
    lit_.save(CAPT / f"2026-11-10_stack3d-{tag}-{T.body}-lit.png")
    return rep, path


class Fits:
    """Passes of the row-wise affine on the finished skin: what the frame and the fat left."""

    def __init__(self, G, d, T, sigmas=None, order=1):
        sigmas = sigmas or tuple(float(v) for v in os.environ.get("FIT_SIGMAS", "6,4").split(","))
        self.steps = []
        for sg in sigmas:
            f = Fit(G, d, T, sg)
            d = f.warp(G, d, order)
            self.steps.append(f)
        self.d = d

    def stats(self):
        return self.steps[0].stats()


def chain_forward(steps, x, r, z, clamp=None):
    """A point of the Male frame through the frame fit and the skin fits. clamp = (lo, hi) rows of the Male frame:
    a ghost limb outside them takes the width and depth correction of the nearest row inside, and its own height."""
    rc = None if clamp is None else np.clip(r, *clamp)
    for f in steps:
        if rc is None:
            x, r, z = f.forward(x, r, z)
        else:
            x, r2, z = f.forward(x, r, z, rc)
            rc = lin(rc, *f.rm); r = r2
    return x, r, z


def body_grid(T, h):
    """Grid of a body: its sprite extents with a margin, voxels no finer than h and about five million of them."""
    x1 = float(T.hw.max()) + 14.0; z0 = float(T.zb.min()) - 14.0; z1 = float(T.zf.max()) + 14.0
    r0 = float(T.s0) - 12.0; r1 = float(T.s1) + 12.0
    hb = max(h, round(float((x1 * (r1 - r0) * (z1 - z0) / 5.5e6) ** (1 / 3)), 2))
    return Grid(hb, x1=x1, r0=r0, r1=r1, z0=z0, z1=z1)


def landmark_rows(T):
    """South rows: top, armpit, under-chest fold, navel, crotch, bottom (strictly increasing)."""
    P = T.P["south"]
    rows = [float(T.s0)]
    for nm in ("armpit L", "under-breast fold L", "navel", "crotch point"):
        rows.append(float(P[nm][1]))
    rows.append(float(T.s1))
    for i in range(1, len(rows)):
        rows[i] = max(rows[i], rows[i - 1] + 2.0)
    return rows


def make(body="Male", h=1.0, fit=True, ghost=False, order=1):
    """Build the stack of a body: the lean stack in the Male frame (muscles and pads scaled by the type), the frame
    put on the body by its landmark rows and a broad row-wise affine, the fat solved from the silhouettes, the skin,
    then the fine fit. Returns everything the boards and the export need."""
    ty = TYPES[body]
    TM = Target("Male")
    T = TM if body == "Male" else Target(body)
    G0 = Grid(h)
    S = build_male(G0, TM, ty=ty)
    G = body_grid(T, h)
    frame = Fit(G0, S.d, T, sigma=14.0, rowmap=(MALE["lm"], landmark_rows(T)), shrink=ty["tf"], tgt=frame_target(T, ty), lim=ty.get("lim"), trim=16.0)
    lean = frame.warp(G0, S.d, order, G); bone = frame.warp(G0, S.layer_d["bone"], order, G)
    d0 = skin_of(G, fat_field(G, lean, bone, T, ty), T, ty, frame)
    pre = Fit(G, d0, T, 1.0).stats()                           # the model against the silhouettes before the fine fit
    F = Fits(G, d0, T, order=order) if fit else None
    steps = [frame] + (F.steps if fit else [])
    d = F.d if fit else d0
    owner = frame.warp(G0, S.owner.astype(np.float32), 0, G)
    for f in steps[1:]:
        owner = f.warp(G, owner, 0)
    K = dict(body=body, ty=ty, T=T, G0=G0, G=G, S=S, d0=d0, d=d, steps=steps, pre=pre, owner=np.round(owner).astype(np.int16),
             left=Fit(G, d, T, 1.0).stats() if fit else pre, frame=frame)
    if ghost:
        K["G2"] = Grid(2.0, x1=126.0, r0=100.0, r1=566.0, z0=150.0, z1=360.0)   # the cut limbs are smooth: a coarser, taller grid
        K["ghost"] = build_ghost(K["G2"], TM)
    return K


def main():
    args = [a for a in sys.argv[1:] if a != "nofit"]
    h = float(args[0]) if args else 2.0
    tag = args[1] if len(args) > 1 else "t"
    names = [a for a in args[2:] if a in TYPES] or ["Male"]
    nofit = "nofit" in sys.argv
    fmt = lambda st: "  ".join(f"{k} {v[0]:.2f}/{v[1]:.2f}/{v[2]:.2f}" for k, v in st.items())
    for body in names:
        K = make(body, h, fit=not nofit)
        print(f"== {body}: grid h {K['G'].h}, frame width scale {K['frame'].sx.min():.2f} to {K['frame'].sx.max():.2f}")
        print("frame against the silhouettes less the fat (px, mean / p95 / max): " + fmt(K["frame"].stats()))
        print("skin before the fine fit: " + fmt(K["pre"]))
        print("left after the fine fit:  " + fmt(K["left"]))
        rep, path = board(K["S"], K["G"], K["d"], K["T"], tag, K["owner"], extra="(no fit)" if nofit else "")
        for f, r in rep.items():
            print(f"{f:6s} sil p95 {r['p95']:.2f} mean {r['mean']:.2f} max {r['max']:.1f} | lum {r['mae']:.4f} (blank {r['blank']:.4f})")
        print(path, flush=True)


if __name__ == "__main__":
    main()
