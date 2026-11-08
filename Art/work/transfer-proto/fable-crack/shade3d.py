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
_height0 = r3.height
NIPPLE = float(os.environ.get("NIPPLE", 7.0))   # px of height
SEX = float(os.environ.get("SEX", 9.0))
PEC = float(os.environ.get("PEC", 8.0))      # px of height of each pectoral lobe
NAVEL = float(os.environ.get("NAVEL", 8.0))


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


def height_shade(view, M, pts, lum):
    h0 = _height0(view, M, pts, lum)
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
    # Virginie 2026-11-08: two pectorals that share the chest (like the two testes in one sac): two lobes from the
    # sternum to the armpit, from under the collarbone to the fold, a groove on the midline
    need = ("armpit L", "armpit R", "shoulder tip L", "shoulder tip R", "under-breast fold L", "under-breast fold R")
    if view == "south" and all(k in pts for k in need):
        midx = 0.5 * (pts["breast apex L"][0] + pts["breast apex R"][0]) if "breast apex L" in pts else 0.5 * (pts["armpit L"][0] + pts["armpit R"][0])
        ysh = 0.5 * (pts["shoulder tip L"][1] + pts["shoulder tip R"][1])
        yfo = 0.5 * (pts["under-breast fold L"][1] + pts["under-breast fold R"][1])
        for nm in ("armpit L", "armpit R"):
            ax = pts[nm][0]
            half = 0.5 * (abs(ax - midx) - 6)
            if half < 8 or yfo - ysh < 30:
                continue
            sg = 1 if ax > midx else -1
            cxp, cyp = midx + sg * (6 + half), 0.5 * (ysh + 12 + yfo)
            ay = 0.5 * (yfo - ysh - 12)
            rr = ((xx - cxp) / half) ** 2 + ((yy - cyp) / ay) ** 2
            out = out + PEC * np.clip(1 - rr, 0, 1) ** 0.7 * m
        band = np.exp(-(((yy - 0.5 * (ysh + yfo)) / (0.5 * (yfo - ysh))) ** 6))
        out = out - 0.5 * PEC * np.exp(-(((xx - midx) / 5.0) ** 2)) * band * m
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
    return np.clip(out, 0, None) if not any(a < 0 for _, _, a in feats) else np.clip(out, -20, None) * m


r3.height = height_shade
r3.silhouette = silhouette_full

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] in ("overlay", "export") else "overlay"
    sys.argv = [sys.argv[0]] + [a for a in sys.argv[1:] if a not in ("overlay", "export")]
    if what == "overlay":
        import overlay3d; overlay3d.main()
    else:
        import relief_export; relief_export.main()
