"""Neck opening as a parametric curve in a landmark frame (Fable, 2026-11-06, round 2).

Frame (per facing), built from her landmarks on either body:
  south/north: origin = midpoint of neck base L/R, x unit = half neck width,
               y unit = cleavage row - neck row (south) or shoulder tip row - neck row (north)
  east:        origin = neck front, x unit = neck front x - neck back x (positive forward),
               y unit = chest front row - neck row
The opening is described by its lower boundary B(x') at K control abscissae x' (depth in y units, 0 = none).
Mapping vanilla -> WDI, per facing: B_w(x') = a * B_v(x' / s) + c, fitted on the drawn pairs.

Run alone to print the measured profiles: uv run --with numpy --with pillow --with scipy python neck.py
"""
import re
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

POINTS = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points"
XS = {"south": np.linspace(-1.0, 1.0, 21), "north": np.linspace(-1.0, 1.0, 21), "east": np.linspace(-1.0, 1.0, 17)}
BAND = {"south": 1.05, "north": 1.05, "east": 1.9}        # how far from the origin (x units) an opening may reach
CENTRE = {"south": None, "north": None, "east": 0.35}     # east: the opening must cross this central strip


def landmarks_both(body, facing):
    """name -> ((vanilla x, y) in 128 units, (WDI x, y) in 128 units)"""
    out = {}
    with open(rf"{POINTS}\delta-{facing}-points.txt", encoding="utf-8-sig") as f:
        for raw in f:
            p = raw.strip().split("|")
            if len(p) < 6 or not p[1].startswith(body + "/"):
                continue
            m1 = re.search(r"vanilla (\d+),(\d+)", p[4]); m2 = re.search(r"WDI (\d+),(\d+)", p[5])
            if m1 and m2:
                out[p[3]] = ((int(m1.group(1)) + 0.5, int(m1.group(2)) + 0.5), (int(m2.group(1)) + 0.5, int(m2.group(2)) + 0.5))
    return out


def frame(body, facing, which, scale):
    """(ox, oy, xu, yu) in pixels of the image at `scale` px per 128 unit; which = 0 vanilla, 1 WDI"""
    lm = {k: v[which] for k, v in landmarks_both(body, facing).items()}
    if facing == "east":
        nf, nb, cf = lm["neck front"], lm["neck back"], lm["chest front"]
        ox, oy = nf; xu = nf[0] - nb[0]; yu = cf[1] - nf[1]
    else:
        L, R = lm["neck base L"], lm["neck base R"]
        SL, SR = lm["shoulder tip L"], lm["shoulder tip R"]
        ox, oy = 0.5 * (L[0] + R[0]), 0.5 * (L[1] + R[1]); xu = 0.5 * (SR[0] - SL[0])     # x unit = shoulder half width
        low = lm["cleavage"] if facing == "south" else lm["shoulder tip L"]
        yu = low[1] - oy
    yu = max(yu, 2.0)
    return ox * scale, oy * scale, xu * scale, yu * scale


def profile(hole, body_a, fr, xs, band_frac=0.02):
    """(top, bottom) of the bare region per control abscissa, measured from the body's own top row in that column,
    in y units. 0,0 where the garment follows the body top; top > 0 means a collar band sits above the opening."""
    ox, oy, xu, yu = fr
    out = np.zeros((2, len(xs)))
    H, W = hole.shape
    for i, xn in enumerate(xs):
        x0 = int(round(ox + (xn - band_frac) * abs(xu))); x1 = int(round(ox + (xn + band_frac) * abs(xu)))
        x0, x1 = max(0, min(x0, x1)), min(W - 1, max(x0, x1))
        bys = np.where(body_a[:, x0:x1 + 1].any(axis=1))[0]
        hys = np.where(hole[:, x0:x1 + 1].any(axis=1))[0]
        if len(bys) and len(hys):
            btop = bys.min()
            out[0, i] = max(0.0, (hys.min() - btop) / yu)
            out[1, i] = max(0.0, (hys.max() + 1 - btop) / yu)
    return out


def hole_mask(body_a, gar_a, fr, frac=0.45, min_area=4, band=1.0, centre_w=0.15):
    """neck opening of a garment on its body: enclosed regions (a cap closes an open V) or uncovered body,
    upper part of the garment, clipped to the neck band of the frame"""
    if gar_a.sum() == 0:
        return np.zeros_like(gar_a)
    ys_, xs_ = np.where(gar_a); top, bot = ys_.min(), ys_.max()
    cap = np.zeros_like(gar_a); cap[:max(0, top), :] = True
    enclosed = ndi.binary_fill_holes(gar_a | cap) & ~gar_a & ~cap
    cand = enclosed | (body_a & ~gar_a)
    ox, oy, xu, yu = fr
    xx = np.arange(gar_a.shape[1])[None, :]
    cand &= (xx >= ox - band * abs(xu)) & (xx <= ox + band * abs(xu))
    lab, n = ndi.label(cand)
    keep = np.zeros_like(cand)
    centre = None if centre_w is None else (xx >= ox - centre_w * abs(xu)) & (xx <= ox + centre_w * abs(xu))
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < min_area or (centre is not None and not (comp & centre).any()):
            continue
        if np.where(comp)[0].mean() < top + frac * (bot - top):
            keep |= comp
    return keep


def render(fr, xs, prof, body_d, smooth=1.0):
    """bare mask from a (top, bottom) profile: in each column, rows from body top + T to body top + B are uncovered.
    The splines through the control points close to zero one step beyond the band."""
    H, W = body_d.shape
    ox, oy, xu, yu = fr
    xn = np.asarray(xs); step = float(xn[1] - xn[0])
    xe = np.r_[xn[0] - step, xn, xn[-1] + step]
    cols = (np.arange(W) + 0.5 - ox) / abs(xu)
    inside = (cols >= xe[0]) & (cols <= xe[-1])
    curves = []
    for d in prof:
        de = np.r_[0.0, np.maximum(np.asarray(d, dtype=np.float64), 0), 0.0]
        spl = PchipInterpolator(xe, de)                 # monotone cubic: no overshoot at the V corners
        curves.append(np.where(inside, np.maximum(spl(np.clip(cols, xe[0], xe[-1])), 0.0), 0.0))
    T, B = curves
    top = np.full(W, np.inf)
    has = body_d.any(axis=0)
    top[has] = body_d.argmax(axis=0)[has]
    rows = np.arange(H)[:, None] + 0.5
    lo = top[None, :] + T[None, :] * yu; hi = top[None, :] + B[None, :] * yu
    mask = (rows >= lo) & (rows < hi) & ((B - T)[None, :] > 0.02)
    if smooth:
        mask = ndi.gaussian_filter(mask.astype(np.float32), smooth) > 0.5
    return mask


def fit_map(pairs, xs):
    """pairs: list of (vanilla profile (2,K), WDI profile (2,K)). Per row (top, bottom): B_w(x) = a * B_v(x / s) + c,
    least squares over a grid of s"""
    out = []
    for r in range(2):
        best = None
        for s in np.linspace(0.8, 2.0, 25):
            A, Y = [], []
            for pv, pw in pairs:
                pv_s = np.interp(xs / s, xs, pv[r], left=0.0, right=0.0)
                A.append(np.c_[pv_s, np.ones(len(xs))]); Y.append(pw[r])
            A = np.vstack(A); Y = np.concatenate(Y)
            sol, res, *_ = np.linalg.lstsq(A, Y, rcond=None)
            err = ((A @ sol - Y) ** 2).sum()
            if best is None or err < best[0]:
                best = (err, sol[0], sol[1], s)
        out.append({"a": float(best[1]), "c": float(best[2]), "s": float(best[3]), "sse": float(best[0])})
    return out


def apply_map(pv, maps, xs):
    rows = []
    for r, m in enumerate(maps):
        pv_s = np.interp(xs / m["s"], xs, pv[r], left=0.0, right=0.0)
        rows.append(np.maximum(m["a"] * pv_s + m["c"], 0.0))
    return np.array(rows)


if __name__ == "__main__":
    from PIL import Image
    WS = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike"
    CORE = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17"
    VAN = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\vanilla"
    V_OF = {"Thin_Female": "thin", "Fat_Female": "fat", "Hulk_Female": "hulk"}

    def alpha(path, size=None):
        im = Image.open(path).convert("RGBA")
        if size and im.size[0] != size:
            im = im.resize((size, size), Image.BILINEAR)
        return np.asarray(im)[..., 3] > 127

    for facing in ["south", "east", "north"]:
        xs = XS[facing]
        print(f"=== {facing}  x' = {np.round(xs, 2)}")
        for garment in ["ShirtBasic", "ShirtButton"]:
            for body in ["Thin_Female", "Fat_Female", "Hulk_Female"]:
                vb = V_OF[body]
                fv = frame(body, facing, 0, 1); fw = frame(body, facing, 1, 4)
                vba = alpha(rf"{VAN}\vanilla-{vb}-{facing}.png"); wba = alpha(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
                hv = hole_mask(vba, alpha(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png"), fv, band=BAND[facing], centre_w=CENTRE[facing])
                hw = hole_mask(wba, alpha(rf"{WS}\Apparel\{garment}\{garment}_{body}_{facing}.png", 512), fw, band=BAND[facing], centre_w=CENTRE[facing])
                pv = profile(hv, vba, fv, xs); pw = profile(hw, wba, fw, xs)
                print(f"{garment:11s} {body:12s} frame v xu {fv[2]:.1f} yu {fv[3]:.1f} | w xu {fw[2]:.0f} yu {fw[3]:.0f}")
                print(f"   vanilla top {np.round(pv[0], 2)}\n           bot {np.round(pv[1], 2)}")
                print(f"   WDI     top {np.round(pw[0], 2)}\n           bot {np.round(pw[1], 2)}")
