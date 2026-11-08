"""Shape from the WDI shading (Virginie 2026-11-08: the WDI shadows were made with a zenithal light, so they tell the
volumes). Light from the top of the image (head side): a surface whose normal turns DOWN is darker, so the shading gives
the vertical slope of the height field where it is dark (the bright side saturates and tells nothing). Per column,
minimise  sum (h[y+1]-h[y]-t[y])^2 + MU * sum (h[y]-h0[y])^2  with t = h0's own slope plus  -K*darkness  where the
texture is darker than its lit white, h0 = relief3d.height (volume + lobes). Then a small 2D smoothing.
Used by patching relief3d.height; set RELIEF_TAG for the output names of overlay3d.py and relief_export.py.
Run: RELIEF_TAG=-shade uv run --with numpy --with pillow --with scipy --with scikit-image python shade3d.py [overlay|export] [Body ...]"""
import os, sys
import numpy as np
from scipy import ndimage as ndi
from scipy.sparse import diags
from scipy.sparse.linalg import spsolve
import relief3d as r3

K = float(os.environ.get("SHADE_K", 4.0))      # height per px at full darkness (slope, 1.4 = 54 degrees)
MU = float(os.environ.get("SHADE_MU", 0.003))   # pull back to the volume
_base_height = r3.base_height
NIPPLE = float(os.environ.get("NIPPLE", 7.0))   # px of height
SEX = float(os.environ.get("SEX", 9.0))
PEC = float(os.environ.get("PEC", 11.0))     # px of height of the pectoral muscle, male bodies
PEC_F = float(os.environ.get("PEC_F", 5.0))   # the same under the breast tissue, female bodies
BODY = [None]                                   # set by the views() wrapper below
NAVEL = float(os.environ.get("NAVEL", 8.0))
DETAIL_OUT = float(os.environ.get("DETAIL_OUT", 5.5))
DETAIL_IN = float(os.environ.get("DETAIL_IN", 4.0))


def chest_creases(out, m, pts):
    """Signed thoracic troughs that shading alone cannot retain reliably.

    They are anchored to the artist's existing landmarks rather than to pixel
    darkness, so their position survives smoothing and the later cage
    constraint. The cage floor in relief_export2.py is the final lower bound
    for these negative displacements.
    """
    yy, xx = np.mgrid[0:out.shape[0], 0:out.shape[1]]
    trough = np.zeros_like(out)
    required = ("breast apex L", "breast apex R", "shoulder tip L", "shoulder tip R", "under-breast fold L", "under-breast fold R")
    if not all(key in pts for key in required):
        return out

    left, right = pts["breast apex L"], pts["breast apex R"]
    midx = 0.5 * (left[0] + right[0])
    y_top = 0.5 * (pts["shoulder tip L"][1] + pts["shoulder tip R"][1]) + 12.0
    y_bottom = 0.5 * (pts["under-breast fold L"][1] + pts["under-breast fold R"][1]) - 4.0
    if y_bottom > y_top:
        in_sternum = (yy >= y_top) & (yy <= y_bottom)
        taper = np.sin(np.pi * np.clip((yy - y_top) / (y_bottom - y_top), 0, 1))
        trough -= 2.5 * np.exp(-((xx - midx) / 5.0) ** 2) * taper * in_sternum

    # The inferior pectoral / under-breast border is a line of attachment,
    # not a shadow-painted valley. Interpolate it between its two anchors.
    (x0, y0), (x1, y1) = pts["under-breast fold L"], pts["under-breast fold R"]
    dx, dy = x1 - x0, y1 - y0
    span2 = dx * dx + dy * dy
    if span2 > 1:
        t = np.clip(((xx - x0) * dx + (yy - y0) * dy) / span2, 0, 1)
        px, py = x0 + t * dx, y0 + t * dy
        dist = np.hypot(xx - px, yy - py)
        trough -= 2.0 * np.exp(-(dist / 4.0) ** 2) * (t > 0.06) * (t < 0.94)

    return out + trough * m


def silhouette_full(img):
    """the whole drawn body, black outline included (Virginie 2026-11-08: the outline is not to be removed, it is to be
    integrated: it is the rim where the surface turns away from the eye)"""
    a = img[..., 3] > 0.5
    m = ndi.binary_fill_holes(a)
    lab, n = ndi.label(m)
    if n > 1:
        m = lab == (1 + int(np.argmax(ndi.sum(m, lab, range(1, n + 1)))))
    return m


def groin(m, lum, pt, ol):
    """footprint of the sex: convex hull of the black groin creases that meet at the sex point (Virginie 2026-11-08: the
    sex was badly modelled). Returns (hull mask, crease mask) or (None, None)"""
    from skimage.morphology import convex_hull_image
    px, py = pt
    n = m.shape[0]
    yy, xx = np.mgrid[0:n, 0:n]
    box = (np.abs(xx - px) < 30) & (yy > py - 26) & (yy < py + 6)
    dark = m & (lum < 0.25) & ~ol & box
    lab, k = ndi.label(dark)
    keep = [i for i in range(1, k + 1) if (lab == i).sum() >= 12]
    if not keep:
        return None, None
    cr = np.isin(lab, keep)
    hull = convex_hull_image(cr) & m
    return (hull, cr) if hull.sum() >= 60 else (None, None)


def outline_of(m, lum):
    """the black stroke along the edge: dark pixels connected to the edge of the silhouette"""
    # dark pixels within the stroke's width of the edge (13 px at 512): a crease that joins the stroke is NOT part of it
    return m & (lum < 0.2) & (ndi.distance_transform_edt(m) <= 15)


def legacy_height_shade(view, M, pts, lum):
    h0 = _base_height(view, M, pts, lum)
    m = M[view]
    n = h0.shape[0]
    ref = float(np.percentile(lum[m & (lum > 0.2)], 95))
    ol = ndi.binary_dilation(outline_of(m, lum), iterations=2)
    dark = np.clip(1.0 - lum / max(ref, 1e-3), 0, 1) * m * ~ol
    dark = ndi.gaussian_filter(dark, (1.0, 2.5)) * m
    # Virginie 2026-11-08: nipples and sex stand out, the navel is hollow. Front view only (the points exist there):
    # the shading is not read around them, then a bump or a dimple is added on the point.
    feats = []
    if view == "south":
        for nm in ("breast apex L", "breast apex R"):
            if nm in pts: feats.append((pts[nm], 7.0, +NIPPLE))
        if "sex" in pts: feats.append((pts["sex"], 13.0, 0.0))   # shading not read there; the dome comes from the groin()
        if "navel" in pts: feats.append((pts["navel"], 7.0, -NAVEL))
    yy, xx = np.mgrid[0:n, 0:n]
    for (px, py), r, a in feats:
        dark = dark * (((xx - px) ** 2 + (yy - py) ** 2) > (1.6 * r) ** 2)
    out = h0.copy()
    for x in np.where(m.any(axis=0))[0]:
        col = m[:, x]
        ys = np.where(col)[0]
        y0, y1 = ys.min(), ys.max() + 1
        k = y1 - y0
        if k < 6:
            continue
        hb = h0[y0:y1, x]
        t = np.diff(hb) - K * dark[y0:y1 - 1, x]
        # normal equations: D^T D h + MU h = D^T t + MU hb
        D = diags([-np.ones(k - 1), np.ones(k - 1)], [0, 1], shape=(k - 1, k))
        A = (D.T @ D + MU * diags([np.ones(k)], [0])).tocsc()
        b = D.T @ t + MU * hb
        out[y0:y1, x] = spsolve(A, b)
    out = ndi.gaussian_filter(out, (2, 4)) * m
    # Virginie 2026-11-08: the pectorals are muscles, not domes. Pectoralis major = a fan: it starts on the collarbone, the edge of
    # the sternum and the upper ribs and converges on the armpit. Thin by the sternum (the bone is a floor: the cleavage cannot
    # go deeper than it), thickest low and lateral, a crisp oblique lower border rising toward the armpit.
    need = ("armpit L", "armpit R", "shoulder tip L", "shoulder tip R", "under-breast fold L", "under-breast fold R")
    if view == "south" and all(k in pts for k in need):
        midx = 0.5 * (pts["breast apex L"][0] + pts["breast apex R"][0]) if "breast apex L" in pts else 0.5 * (pts["armpit L"][0] + pts["armpit R"][0])
        ysh = 0.5 * (pts["shoulder tip L"][1] + pts["shoulder tip R"][1])
        yfo = 0.5 * (pts["under-breast fold L"][1] + pts["under-breast fold R"][1])
        amp = PEC if BODY[0] and "Female" not in BODY[0] else PEC_F
        inc = np.zeros_like(out)
        for nm in ("armpit L", "armpit R"):
            ax, ay_ = pts[nm]
            w = abs(ax - midx) - 6
            if w < 12 or yfo - ysh < 30:
                continue
            sg = 1 if ax > midx else -1
            u = (np.abs(xx - midx) - 6) / w * ((xx - midx) * sg > 0)
            ytop = ysh + 22 - 12 * np.clip(u, 0, 1)          # the collarbone climbs from the notch to the shoulder
            ylow = (yfo + 4) + ((ay_ + 10) - (yfo + 4)) * np.clip(u, 0, 1.2) ** 1.2
            v = (yy - ytop) / np.maximum(ylow - ytop, 1.0)
            inside = (u > 0) & (u < 1.0) & (v > 0) & (v < 1.0)
            Au = 0.30 + 0.70 * np.clip(u, 0, 1) ** 0.8
            tv = np.clip(v / 0.70, 0, 1)
            Av = tv * tv * (3 - 2 * tv)                      # smoothstep: no ridge along the collarbone
            s_low = np.clip((1 - v) * (ylow - ytop) / (4.0 if amp == PEC else 14.0), 0, 1)
            s_lat = np.clip((1 - u) * w / 10.0, 0, 1)
            s_med = np.clip(u * w / 5.0, 0, 1)
            inc = np.maximum(inc, amp * Au * Av * s_low * s_lat * s_med * inside)
        out = out + ndi.gaussian_filter(inc, 1.2) * m
    out = chest_creases(out, m, pts) if view == "south" else out
    if view == "south" and "sex" in pts:
        hull, cr = groin(m, lum, pts["sex"], ol)
        if hull is not None:
            wd = np.ptp(np.where(hull)[1]) + 1
            amp = SEX * float(np.clip(wd / 40.0, 0.6, 1.6))
            d = ndi.distance_transform_edt(hull)
            dome = ndi.gaussian_filter(amp * np.sqrt(np.clip(d / max(d.max(), 1e-3), 0, 1)), 2.0)
            groove = 0.15 * amp * ndi.gaussian_filter(ndi.binary_dilation(cr).astype(float), 2.0)
            out = out + (dome - groove) * m
        else:
            px, py = pts["sex"]
            out = out + SEX * np.exp(-(((xx - px) ** 2 + (yy - py) ** 2) / (2 * 6.5 ** 2))) * m
    for (px, py), r, a in feats:
        out = out + a * np.exp(-(((xx - px) ** 2 + (yy - py) ** 2) / (2 * (r / 2) ** 2))) * m
    # _height0 already owns the silhouette-calibrated base, its chest lobes,
    # and the broad artist-separated zones.  The shaded solution and named
    # features are surface detail only: letting them add another full volume
    # made the chest and abdomen into stacked balloons.  Bound their signed
    # displacement, preserving creases and the named relief without a second
    # (or third) extrusion of the torso.
    raw_detail = out - h0
    # A hard clip creates a visible normal crease at its threshold.  A tanh
    # saturation has the same finite limits but eases into them, so the
    # renderer sees soft tissue rather than horizontal terraces.
    detail = np.where(
        raw_detail >= 0,
        DETAIL_OUT * np.tanh(raw_detail / DETAIL_OUT),
        DETAIL_IN * np.tanh(raw_detail / DETAIL_IN),
    )
    return np.maximum(h0 + detail, 0) * m


# Stable public hook while the structured surface pass is built separately.
# relief_export2 imports this module for its monkey-patch below.
def height_shade(view, M, pts, lum):
    return legacy_height_shade(view, M, pts, lum)


_views0 = r3.views


def _views(body, vanilla):
    BODY[0] = body
    return _views0(body, vanilla)


r3.views = _views
r3.height = height_shade
r3.silhouette = silhouette_full

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("overlay", "export") else "overlay"
    sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a not in ("overlay", "export")]
    if what == "overlay":
        import overlay3d; overlay3d.main()
    else:
        import relief_export; relief_export.main()
