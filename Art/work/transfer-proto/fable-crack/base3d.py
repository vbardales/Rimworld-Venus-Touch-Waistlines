"""Profile-led base envelope for the thorax-abdomen-pelvis (2026-11-09).

The former base (relief3d.base_height) gave every row an elliptical section
(sqrt(1 - t^2)) whatever the row, which reads as a pillow.  Here the section of
each south/north row is a superellipse whose exponent p is set from the EAST
(profile) landmarks: a flat chest plate and flat upper back (high p) that turns
to a rounder belly, waist and buttock (p near 2) as the profile landmarks
(chest front, waist, belly front, buttock back) say.  Depth per row still comes
from the east silhouette; the east view itself is delegated to the old base.

BASE_MODE=ellipse restores the old base for A/B.  Signed anatomical patches
(shade3d.py) are laid over this base unchanged.
"""
import os
import numpy as np
from scipy import ndimage as ndi

import crack as c1
import explain5b as e5
import relief3d as r3

N = c1.N
MODE = os.environ.get("BASE_MODE", "profile").lower()
BODY = [None]  # set by shade3d's views() wrapper


def _flags(body):
    body = body or ""
    return {"female": "Female" in body, "fat": body.startswith("Fat"),
            "hulk": body.startswith("Hulk"), "thin": body.startswith("Thin")}


def _exponents(fl):
    """(chest, waist, hip) exponents for the (front, back) halves."""
    if fl["fat"]:
        front = (2.3, 2.0, 2.2)
        back = (2.5, 2.1, 2.1)
    elif fl["hulk"]:
        front = (3.2, 2.6, 2.6)
        back = (3.2, 2.6, 2.3)
    elif fl["female"]:
        front = (2.7, 2.3, 2.4)
        back = (2.9, 2.4, 2.2)
    elif fl["thin"]:
        front = (2.8, 2.5, 2.5)
        back = (2.9, 2.5, 2.3)
    else:
        front = (3.0, 2.5, 2.5)
        back = (3.1, 2.5, 2.3)
    return front, back


def _east_rows(body, ms, me):
    """Profile landmark rows converted to south rows (None where absent)."""
    try:
        s, _, names = e5.named_pairs(body, "east")
    except Exception:
        return {}
    a0, a1 = r3.rows_of(ms)
    b0, b1 = r3.rows_of(me)
    out = {}
    for i, name in enumerate(names):
        out[name] = a0 + (float(s[i][1]) - b0) / max(b1 - b0, 1) * (a1 - a0)
    return out


def _section(t, p):
    t = np.clip(np.abs(t), 0, 1)
    return (1.0 - t ** p) ** (1.0 / p)


def profile_base(view, M, pts, lum):
    if MODE == "ellipse" or view == "east":
        return r3.base_height(view, M, pts, lum)
    m = M[view]
    ms, me = M["south"], M["east"]
    body = BODY[0]
    fl = _flags(body)
    pf, pb = _exponents(fl)
    lm = _east_rows(body, ms, me)
    s0, s1 = r3.rows_of(ms)
    top = lm.get("top", s0)
    chest = lm.get("chest front", s0 + 0.35 * (s1 - s0))
    waist = lm.get("waist front", s0 + 0.62 * (s1 - s0))
    hip = lm.get("buttock back", s0 + 0.72 * (s1 - s0))
    rows_anchor = np.array([top, chest, waist, max(hip, waist + 4), s1], float)
    order = np.argsort(rows_anchor)
    rows_anchor = rows_anchor[order]

    def pat(y, vals):
        v = np.array([vals[0], vals[0], vals[1], vals[2], vals[2]], float)[order]
        return float(np.interp(y, rows_anchor, v))

    ys = np.where(m.any(axis=1))[0]
    # per-row front/back depths and centre, smoothed along the rows only to
    # remove the sprite's stair stripes (the hard east cap is applied later)
    zc, front, back = {}, {}, {}
    for y in ys:
        ye = r3.map_row(y, m, me)
        zb, zf = r3.extent(me, int(np.clip(ye, 0, N - 1)))
        if zb is None:
            continue
        zc[y] = 0.5 * (zb + zf)
        front[y] = zf - zc[y]
        back[y] = zc[y] - zb
    keys = np.array(sorted(zc))
    if not len(keys):
        return np.zeros((N, N))
    fr = ndi.gaussian_filter1d(np.array([front[k] for k in keys]), 2.0, mode="nearest")
    bk = ndi.gaussian_filter1d(np.array([back[k] for k in keys]), 2.0, mode="nearest")
    h = np.zeros((N, N))
    xs = np.arange(N)
    for k, y in enumerate(keys):
        xl, xr = r3.extent(m, y)
        c = 0.5 * (xl + xr)
        w = max(0.5 * (xr - xl), 1.0)
        t = (xs - c) / w
        if view == "south":
            h[y] = fr[k] * _section(t, pat(y, pf))
        else:
            h[y] = bk[k] * _section(t, pat(y, pb))
    return ndi.gaussian_filter(h, (2.5, 1.5)) * m
