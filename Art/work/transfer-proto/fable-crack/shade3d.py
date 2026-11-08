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


def outline_of(m, lum):
    """the black stroke along the edge: dark pixels connected to the edge of the silhouette"""
    dark = m & (lum < 0.2)
    lab, n = ndi.label(dark)
    if n == 0:
        return dark
    edge = m & ~ndi.binary_erosion(m, iterations=2)
    keep = np.unique(lab[edge & dark]); keep = keep[keep > 0]
    return np.isin(lab, keep)


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
        if "sex" in pts: feats.append((pts["sex"], 13.0, +SEX))
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
