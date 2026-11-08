"""Rebuild a vanilla top garment as a WDI style garment: layered method (Fable, 2026-11-06).

  silhouette : WDI body alpha, dilated by d (calibrated), minus the neck hole
  neck hole  : vanilla hole warped onto the WDI body by a regularised thin plate spline through her landmarks,
               then the hole affine (scale, offset) calibrated on the ShirtBasic pair
  outline    : re-stroked at the WDI width (calibrated), colour 4,4,4; hole stroke = vanilla ratio x WDI width
  shading    : WDI body luminance through a monotone LUT calibrated on the ShirtBasic pair (nipples inpainted,
               body outline zone extended from the nearest inner pixel)
  details    : dark lines of the vanilla garment (collar, placket, buttons) warped by the TPS, thresholded,
               skeletonised, re-stroked 3 px (crisp)
Hold-out: every calibrated number comes from ShirtBasic; the result is scored against WDI's own ShirtButton.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack.py [neck|noneck|both]
"""
import os, sys, re, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.ndimage import map_coordinates
from skimage.morphology import skeletonize

MOD = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines"
WS = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike"
CORE = MOD + r"\Art\work\core17"
VAN = MOD + r"\Art\work\vanilla"
POINTS = MOD + r"\Art\work\captures\2026-11-03_points"
FIT = MOD + r"\Art\work\transfer-proto\fit"
OUT = MOD + r"\Art\work\transfer-proto\fable-crack\out"
CAPT = MOD + r"\Art\work\captures"
os.makedirs(OUT, exist_ok=True)

N = 512
VANILLA_OF = {"Thin_Female": "thin", "Fat_Female": "fat", "Hulk_Female": "hulk",
              "Male": "male", "Female": "female", "Thin": "thin", "Fat": "fat", "Hulk": "hulk"}
LINE_LUM = 0.30          # grey of the thin detail lines (WDI draws them dark grey, not black)
LINE_W = 1               # dilation radius of the skeleton: 1 -> 3 px lines at 512 (WDI thin lines are 2 px)
OUTLINE_RGB = 4 / 255.0


def load(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size and im.size != (size, size):
        im = im.resize((size, size), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255.0


def lum(img):
    return img[..., :3].mean(axis=2)


def bbox(m):
    ys, xs = np.where(m)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


# ---------------------------------------------------------------- landmarks and TPS
def landmarks(body, facing):
    """pairs (WDI xy in 512 units, vanilla xy in 128 units) from her delta file; duplicates averaged, axis dropped"""
    pairs = {}
    with open(rf"{POINTS}\delta-{facing}-points.txt", encoding="utf-8-sig") as f:
        for raw in f:
            p = raw.strip().split("|")
            if len(p) < 6 or not p[1].startswith(body + "/"):
                continue
            if p[2] == "axis":
                continue
            m1 = re.search(r"vanilla (\d+),(\d+)", p[4]); m2 = re.search(r"WDI (\d+),(\d+)", p[5])
            if not (m1 and m2):
                continue
            vx, vy = int(m1.group(1)) + 0.5, int(m1.group(2)) + 0.5
            wx, wy = (int(m2.group(1)) + 0.5) * 4, (int(m2.group(2)) + 0.5) * 4
            pairs.setdefault((wx, wy), []).append((vx, vy))
    src = np.array(list(pairs.keys()), dtype=np.float64)
    dst = np.array([np.mean(v, axis=0) for v in pairs.values()], dtype=np.float64)
    return src, dst


def named_landmarks(body, facing):
    """name -> (WDI x, WDI y) in 512 units"""
    out = {}
    with open(rf"{POINTS}\delta-{facing}-points.txt", encoding="utf-8-sig") as f:
        for raw in f:
            p = raw.strip().split("|")
            if len(p) < 6 or not p[1].startswith(body + "/"):
                continue
            m2 = re.search(r"WDI (\d+),(\d+)", p[5])
            if m2:
                out[p[3]] = ((int(m2.group(1)) + 0.5) * 4, (int(m2.group(2)) + 0.5) * 4)
    return out


def neck_band(body, facing, margin=0.35):
    """x range the neck opening may occupy: her neck base (front/back in profile) landmarks widened by margin"""
    lm = named_landmarks(body, facing)
    if facing == "east":
        pts = [lm.get("neck front"), lm.get("neck back")]
    else:
        pts = [lm.get("neck base L"), lm.get("neck base R")]
    if any(p is None for p in pts):
        return None
    xs = sorted(p[0] for p in pts); w = xs[1] - xs[0]
    return xs[0] - margin * w, xs[1] + margin * w


def v_target(body, facing):
    """row the neck knob pulls the opening down to: the cleavage (front) or chest front (profile)"""
    lm = named_landmarks(body, facing)
    p = lm.get("cleavage") if facing == "south" else lm.get("chest front") if facing == "east" else None
    return None if p is None else p[1]


class TPS:
    """regularised thin plate spline, 2D -> 2D, with far anchors from the affine fit so the far field stays sane"""
    def __init__(self, src, dst, lam=2000.0):
        # affine least squares for the anchors
        A = np.c_[src, np.ones(len(src))]
        M, *_ = np.linalg.lstsq(A, dst, rcond=None)
        corners = np.array([[-64, -64], [N + 64, -64], [-64, N + 64], [N + 64, N + 64],
                            [N / 2, -64], [N / 2, N + 64], [-64, N / 2], [N + 64, N / 2]], dtype=np.float64)
        src = np.r_[src, corners]
        dst = np.r_[dst, np.c_[corners, np.ones(len(corners))] @ M]
        self.src = src
        n = len(src)
        K = self._U(src[:, None, :], src[None, :, :]) + lam * np.eye(n)
        P = np.c_[np.ones(n), src]
        L = np.zeros((n + 3, n + 3)); L[:n, :n] = K; L[:n, n:] = P; L[n:, :n] = P.T
        Y = np.zeros((n + 3, 2)); Y[:n] = dst
        sol = np.linalg.solve(L, Y)
        self.w, self.a = sol[:n], sol[n:]

    @staticmethod
    def _U(a, b):
        r2 = ((a - b) ** 2).sum(-1)
        return np.where(r2 > 0, 0.5 * r2 * np.log(np.maximum(r2, 1e-12)), 0.0)

    def __call__(self, pts):
        pts = np.asarray(pts, dtype=np.float64)
        out = np.empty((len(pts), 2))
        for k in range(0, len(pts), 16384):        # in chunks: the whole 512 x 512 grid at once ran out of memory
            p = pts[k:k + 16384]
            U = self._U(p[:, None, :], self.src[None, :, :])
            out[k:k + 16384] = U @ self.w + np.c_[np.ones(len(p)), p] @ self.a
        return out

    def residual(self, src, dst):
        return np.sqrt(((self(src) - dst) ** 2).sum(1))


def warp_field(tps):
    """for every 512 pixel centre, the vanilla (128 units) coordinate it samples"""
    ys, xs = np.mgrid[0:N, 0:N]
    pts = np.c_[xs.ravel() + 0.5, ys.ravel() + 0.5]
    uv = tps(pts)
    return uv[:, 0].reshape(N, N), uv[:, 1].reshape(N, N)


def sample128(img, U, V, order=1):
    """bilinear sample of a 128 px float image at vanilla coordinates (pixel centres at i+0.5)"""
    return map_coordinates(img, [V - 0.5, U - 0.5], order=order, mode="constant", cval=0.0)


# ---------------------------------------------------------------- masks
def upper_hole(body_a, gar_a, frac=0.45, min_area=4):
    """the neck opening: regions enclosed by the garment (a cap row closes an open V) or body not covered,
    components whose centre lies in the upper part of the garment"""
    if gar_a.sum() == 0:
        return np.zeros_like(gar_a)
    top = bbox(gar_a)[1]
    cap = np.zeros_like(gar_a); cap[:max(0, top), :] = True
    enclosed = ndi.binary_fill_holes(gar_a | cap) & ~gar_a & ~cap
    cand = enclosed | (body_a & ~gar_a)
    lab, n = ndi.label(cand)
    if n == 0:
        return cand
    y0, y1 = bbox(gar_a)[1], bbox(gar_a)[3]
    keep = np.zeros_like(cand)
    for i in range(1, n + 1):
        comp = lab == i
        if comp.sum() < min_area:
            continue
        cy = np.where(comp)[0].mean()
        if cy < y0 + frac * (y1 - y0):
            keep |= comp
    return keep


def clean_mask(soft, sigma=1.5, thr=0.5, close=2):
    """warped soft mask -> smooth crisp binary"""
    m = ndi.gaussian_filter(soft.astype(np.float32), sigma) > thr
    if close:
        m = ndi.binary_closing(m, iterations=close)
    return ndi.binary_fill_holes(m)


def edge_run(alpha, l, mask_from, max_run=40):
    """median dark run from the edge of mask_from inward into alpha (stroke width), scanning rows and columns"""
    runs = []
    inside = alpha & ~mask_from
    for axis in (0, 1):
        A = inside if axis == 0 else inside.T
        D = (l < 0.5) if axis == 0 else (l < 0.5).T
        F = mask_from if axis == 0 else mask_from.T
        for y in range(A.shape[0]):
            row = A[y]; frow = F[y]; drow = D[y]
            for x in range(1, A.shape[1]):
                if frow[x - 1] and row[x]:          # entering the garment from the hole/outside, going right
                    n = 0
                    while x + n < A.shape[1] and row[x + n] and drow[x + n] and n < max_run: n += 1
                    if n: runs.append(n)
                if frow[x] and row[x - 1]:          # entering the garment going left
                    n = 0
                    while x - 1 - n >= 0 and row[x - 1 - n] and drow[x - 1 - n] and n < max_run: n += 1
                    if n: runs.append(n)
    return float(np.median(runs)) if runs else 0.0


def soft_edge(alpha):
    """anti-aliased coverage from the signed distance of a binary mask"""
    din = ndi.distance_transform_edt(alpha)
    dout = ndi.distance_transform_edt(~alpha)
    sd = np.where(alpha, din - 0.5, -(dout - 0.5))
    return np.clip(sd + 0.5, 0, 1), din


# ---------------------------------------------------------------- the pipeline
def body_shading(B):
    """WDI body luminance with nipples inpainted and the outline zone / outside filled from the nearest inner pixel"""
    a = B[..., 3] > 0.5
    l = lum(B)
    chroma = B[..., :3].max(axis=2) - B[..., :3].min(axis=2)
    nip = a & (chroma > 0.10)
    nip = ndi.binary_dilation(nip, iterations=3)
    din = ndi.distance_transform_edt(a)
    rim = edge_run(a, l, ~a)                       # body outline width
    inner = a & (din > rim + 3) & ~nip
    # fill nipples by the normalised blur of the inner luminance
    w = inner.astype(np.float32)
    num = ndi.gaussian_filter(l * w, 6); den = ndi.gaussian_filter(w, 6)
    filled = np.where(inner, l, num / np.maximum(den, 1e-6))
    # extend outward: nearest inner pixel
    _, idx = ndi.distance_transform_edt(~inner, return_indices=True)
    ext = filled[idx[0], idx[1]]
    return ext, a, rim, inner


def calibrate(body, facing, tps, U, V, B, shade, body_a, body_inner):
    """all the style numbers, from the ShirtBasic pair only"""
    G = load(rf"{WS}\Apparel\ShirtBasic\ShirtBasic_{body}_{facing}.png", N)
    ga = G[..., 3] > 0.5; gl = lum(G)
    g_din = ndi.distance_transform_edt(ga)
    cal = {}
    # outline width of the WDI garment
    cal["w_out"] = edge_run(ga, gl, ~ga)
    # dilation d: median signed distance of the garment's outer contour to the body edge (hole contour excluded)
    hole_w = upper_hole(body_a, ga, min_area=40)
    contour = ga & ~ndi.binary_erosion(ga)
    contour &= ~ndi.binary_dilation(hole_w, iterations=3)
    cal["hole_area_wdi"] = int(hole_w.sum())
    d_out = ndi.distance_transform_edt(~body_a); d_in = ndi.distance_transform_edt(body_a)
    sd = np.where(body_a, -d_in, d_out)
    cal["d"] = float(np.median(sd[contour]))
    # shading LUT: body luminance -> garment luminance (inside both, away from both outlines, no thin lines of the garment)
    both = ga & body_inner & (g_din > cal["w_out"] + 4) & (gl > 0.5)
    bl = shade[both]; gv = gl[both]
    bins = np.linspace(0.3, 1.0, 36)
    lut_x, lut_y = [], []
    for i in range(len(bins) - 1):
        sel = (bl >= bins[i]) & (bl < bins[i + 1])
        if sel.sum() > 30:
            lut_x.append(0.5 * (bins[i] + bins[i + 1])); lut_y.append(float(np.median(gv[sel])))
    lut_y = np.maximum.accumulate(np.array(lut_y))          # monotone
    cal["lut_x"], cal["lut_y"] = [float(v) for v in lut_x], [float(v) for v in lut_y]
    cal["base"] = float(np.median(gv))
    # neck hole affine: vanilla ShirtBasic hole warped vs WDI ShirtBasic hole (bbox based, about the top centre)
    vb = VANILLA_OF[body]
    Vg = load(rf"{CORE}\ShirtBasic_{vb.capitalize()}_{facing}.png")
    Vb = load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vba = Vb[..., 3] > 0.5
    hole_v = upper_hole(vba, va)
    hw = clean_mask(sample128(hole_v.astype(np.float32), U, V))
    cal["hole_area_warped"] = int(hw.sum())
    if hw.sum() > 50 and hole_w.sum() > 50:
        b1, b2 = bbox(hw), bbox(hole_w)
        cal["neck"] = {"sx": (b2[2] - b2[0] + 1) / (b1[2] - b1[0] + 1), "sy": (b2[3] - b2[1] + 1) / (b1[3] - b1[1] + 1),
                       "cx1": 0.5 * (b1[0] + b1[2]), "top1": b1[1], "cx2": 0.5 * (b2[0] + b2[2]), "top2": b2[1]}
    else:
        cal["neck"] = None
    return cal, (G, ga, gl)


def neck_warp(mask_or_img, cal, y_blend_from, blend_len=40.0, order=0):
    """apply the hole affine (scale about the hole top centre) as a backward warp, blended out below the collar"""
    nk = cal["neck"]
    if nk is None:
        return mask_or_img
    ys, xs = np.mgrid[0:N, 0:N].astype(np.float64)
    # target (x,y) -> source: inverse of x' = cx2 + sx (x - cx1), y' = top2 + sy (y - top1)
    sxs = nk["cx1"] + (xs - nk["cx2"]) / nk["sx"]
    sys_ = nk["top1"] + (ys - nk["top2"]) / nk["sy"]
    w = np.clip(1.0 - (ys - y_blend_from) / blend_len, 0, 1)
    SX = xs + (sxs - xs) * w; SY = ys + (sys_ - ys) * w
    out = map_coordinates(mask_or_img.astype(np.float32), [SY, SX], order=order, mode="constant", cval=0.0)
    return out


def rebuild(body, facing, garment, cal, tps, U, V, B, shade, body_a, use_neck=True):
    vb = VANILLA_OF[body]
    Vg = load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png")
    Vb = load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = lum(Vg); vba = Vb[..., 3] > 0.5
    # vanilla strokes
    s_out = edge_run(va, vl, ~va)
    hole_v = upper_hole(vba, va)
    s_hole = min(edge_run(va, vl, hole_v), s_out) if hole_v.sum() else 0.0
    # 1. coverage: body dilated by d; sides always from the body; the hem from the warped vanilla alpha only when the
    #    vanilla garment stops above the vanilla body's bottom (a shirt reaches the bottom: it covers the whole body)
    d = int(round(max(0.0, cal["d"])))
    body_d = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    coverage = body_d.copy()
    full_hem = bbox(va)[3] >= bbox(vba)[3] - 2
    if not full_hem:
        cov_v = clean_mask(sample128(va.astype(np.float32), U, V))
        hem = np.full(N, -1.0)
        for x in range(N):
            ys = np.where(cov_v[:, x])[0]
            if len(ys): hem[x] = ys.max()
        ok = hem >= 0
        if ok.sum() > 10:
            hem[~ok] = np.interp(np.where(~ok)[0], np.where(ok)[0], hem[ok])
            hem = ndi.median_filter(hem, size=15) + 4
            ys = np.arange(N)[:, None]
            coverage &= ys <= hem[None, :]
    # 2. neck hole: the vanilla opening carried onto the WDI body by the TPS, clipped to the neck band (the WDI artist
    #    covers the shoulders up to the top), smoothed crisp
    hole = clean_mask(sample128(hole_v.astype(np.float32), U, V))
    band = neck_band(body, facing)
    if band is not None and hole.sum():
        xs = np.arange(N)[None, :]
        hole &= (xs >= band[0]) & (xs <= band[1])
        hole = clean_mask(hole.astype(np.float32), sigma=1.0, close=1)
    y_hole_bottom = bbox(hole)[3] if hole.sum() else 0
    knob = None
    if use_neck and hole.sum():
        # neck knob (a per garment choice, not learned): stretch the opening so its bottom lands on the cleavage row
        yt = v_target(body, facing)
        if yt is not None and yt > y_hole_bottom + 4:
            top = bbox(hole)[1]
            sy = (yt - top) / max(1, y_hole_bottom - top)
            b = bbox(hole)
            knob = {"sx": sy ** 0.5, "sy": sy, "cx1": 0.5 * (b[0] + b[2]), "top1": top, "cx2": 0.5 * (b[0] + b[2]), "top2": top}
            hole = ndi.binary_fill_holes(neck_warp(hole, {"neck": knob}, y_hole_bottom) > 0.5)
            y_hole_bottom = bbox(hole)[3]
    alpha = coverage & ~hole
    # one component only (largest)
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1)); alpha = lab == (1 + int(np.argmax(sizes)))
    # 3. outline (outer) and hole stroke
    cov, din = soft_edge(alpha)
    w_out = cal["w_out"]
    w_hole = w_out * (s_hole / s_out) if s_out > 0 else w_out * 0.5
    d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
    d_outer = ndi.distance_transform_edt(coverage)       # distance to the outside of the coverage
    outline = np.clip(w_out + 0.5 - d_outer, 0, 1)                 # thick stroke along the outer edge
    outline = np.maximum(outline, np.clip(w_hole + 0.5 - d_hole, 0, 1))
    # 4. shading through the LUT
    fabric = np.interp(shade, cal["lut_x"], cal["lut_y"])
    # 5. details from the vanilla garment: dark pixels inside the eroded garment, not the strokes
    inner_v = ndi.binary_erosion(va, iterations=int(s_out) + 1) & ~ndi.binary_dilation(hole_v, iterations=int(s_hole) + 1)
    # darkness against the local fabric (grey closing), so faint anti-aliased 1 px lines count too
    vl_f = np.where(va, vl, 1.0)
    bg = ndi.grey_closing(vl_f, size=(7, 7))
    dark = np.clip((bg - vl) / 0.30, 0, 1) * inner_v
    dark_w = sample128(dark.astype(np.float32), U, V, order=1)
    if knob is not None:
        dark_w = neck_warp(dark_w, {"neck": knob}, int(knob["top1"] + knob["sy"] * (y_hole_bottom - knob["top1"]) / knob["sy"]), order=1)
    det = dark_w > 0.30
    det &= alpha & (d_outer > w_out + 1) & (d_hole > w_hole + 1)
    lab, n = ndi.label(det, structure=np.ones((3, 3)))
    if n:
        sizes = ndi.sum(det, lab, range(1, n + 1))
        det &= np.isin(lab, 1 + np.where(sizes >= 10)[0])
    sk = skeletonize(det)
    lines = ndi.binary_dilation(sk, iterations=LINE_W)
    # crisp but anti-aliased: 1 px soft rim
    lines_soft = np.clip(1.5 - ndi.distance_transform_edt(~lines), 0, 1) * lines.astype(np.float32)
    lines_soft = np.maximum(lines_soft, 0.5 * (ndi.distance_transform_edt(~lines) <= 1.0) * ~lines)
    # 6. composite
    rgb = fabric.copy()
    rgb = rgb * (1 - lines_soft) + LINE_LUM * lines_soft
    rgb = rgb * (1 - outline) + OUTLINE_RGB * outline
    out = np.zeros((N, N, 4), dtype=np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = rgb
    out[..., 3] = cov
    layers = {"coverage": coverage, "hole": hole, "outline": outline, "fabric": fabric, "lines": lines, "alpha": alpha,
              "d": d, "w_out": w_out, "w_hole": w_hole, "s_out": s_out, "s_hole": s_hole, "knob": knob}
    return out, layers


# ---------------------------------------------------------------- scoring
def score(ours, ref):
    oa = ours[..., 3] > 0.5; ra = ref[..., 3] > 0.5
    iou = (oa & ra).sum() / max(1, (oa | ra).sum())
    oc = oa & ~ndi.binary_erosion(oa); rc = ra & ~ndi.binary_erosion(ra)
    d_o = ndi.distance_transform_edt(~rc); d_r = ndi.distance_transform_edt(~oc)
    edge = 0.5 * (d_o[oc].mean() + d_r[rc].mean())
    both = oa & ra
    mae = np.abs(lum(ours)[both] - lum(ref)[both]).mean()
    return iou, edge, mae


def to_pil(img):
    return Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")


def nearest4(img128):
    return np.asarray(to_pil(img128).resize((N, N), Image.NEAREST)).astype(np.float32) / 255.0


# ---------------------------------------------------------------- main
def run(mode):
    bodies = ["Fat_Female", "Hulk_Female", "Thin_Female"]
    facings = ["south", "east", "north"]
    results = {}
    tiles = {}
    for body in bodies:
        for facing in facings:
            B = load(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
            shade, body_a, rim, body_inner = body_shading(B)
            src, dst = landmarks(body, facing)
            tps = TPS(src, dst)
            res = tps.residual(src, dst)
            U, V = warp_field(tps)
            cal, (Gb, gba, gbl) = calibrate(body, facing, tps, U, V, B, shade, body_a, body_inner)
            key = f"{body}_{facing}"
            results[key] = {"landmarks": int(len(src)), "tps_residual_px128": float(res.mean()),
                            "d": cal["d"], "w_out": cal["w_out"], "base": cal["base"], "neck": cal["neck"]}
            for garment in ["ShirtButton", "ShirtBasic"]:
                ref = load(rf"{WS}\Apparel\{garment}\{garment}_{body}_{facing}.png", N)
                for use_neck in ([True, False] if mode == "both" else [mode == "neck"]):
                    out, layers = rebuild(body, facing, garment, cal, tps, U, V, B, shade, body_a, use_neck)
                    tag = "knob" if use_neck else "plainneck"
                    to_pil(out).save(rf"{OUT}\{garment}_{body}_{facing}_{tag}.png")
                    iou, edge, mae = score(out, ref)
                    results[key][f"{garment}_{tag}"] = {"iou": round(float(iou), 3), "edge_px": round(float(edge), 2),
                                                        "lum_mae": round(float(mae), 3), "w_hole": layers["w_hole"],
                                                        "s_out": layers["s_out"], "s_hole": layers["s_hole"]}
                    tiles[(body, facing, garment, tag)] = out
                    if garment == "ShirtButton" and not use_neck:
                        tiles[(body, facing, "layers")] = layers
                # baseline: vanilla garment at 4x nearest, centred on the WDI body bbox (what a plain upscale gives)
                vb = VANILLA_OF[body]
                Vg = load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png")
                base = nearest4(Vg)
                iou, edge, mae = score(base, ref)
                results[key][f"{garment}_plain4x"] = {"iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3)}
                tiles[(body, facing, garment, "plain")] = base
                tiles[(body, facing, garment, "wdi")] = ref
            print(key, json.dumps(results[key]))
    with open(rf"{OUT}\scores.json", "w") as f:
        json.dump(results, f, indent=1)
    return results, tiles


def crop_tile(img, size=300, box=(76, 140, 436, 500), bg=(78, 98, 78)):
    pil = to_pil(img) if isinstance(img, np.ndarray) else img
    back = Image.new("RGBA", (N, N), bg + (255,))
    back.alpha_composite(pil)
    return back.crop(box).resize((size, size), Image.LANCZOS)


def board(results, tiles, mode):
    font = ImageFont.load_default(size=15)
    fontb = ImageFont.load_default(size=22)
    bodies = ["Fat_Female", "Hulk_Female", "Thin_Female"]; facings = ["south", "east", "north"]
    cols = [("vanilla ShirtButton x4", lambda b, f: tiles[(b, f, "ShirtButton", "plain")]),
            ("WDI body (input)", lambda b, f: load(rf"{WS}\Bodies\Naked_{b}_{f}.png")),
            ("REBUILT ShirtButton (hold-out)", lambda b, f: tiles[(b, f, "ShirtButton", "plainneck")]),
            ("WDI artist's ShirtButton (truth)", lambda b, f: tiles[(b, f, "ShirtButton", "wdi")]),
            ("REBUILT + neck knob (V to cleavage row, a choice)", lambda b, f: tiles[(b, f, "ShirtButton", "knob")]),
            ("REBUILT ShirtBasic (calibration set)", lambda b, f: tiles[(b, f, "ShirtBasic", "plainneck")]),
            ("WDI artist's ShirtBasic", lambda b, f: tiles[(b, f, "ShirtBasic", "wdi")]),
            ("her FIT step4 (2026-11-06)", lambda b, f: load(rf"{FIT}\ShirtButton_{b}_{f}_step4.png") if os.path.exists(rf"{FIT}\ShirtButton_{b}_{f}_step4.png") else None)]
    S = 300; pad = 6; left = 150; top = 70
    W = left + len(cols) * (S + pad); H = top + 9 * (S + pad)
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Layered rebuild: silhouette + shading from the WDI body, neck hole + details from the vanilla garment through a TPS on her landmarks, re-stroked crisp. Calibrated on ShirtBasic only, tested on ShirtButton.", fill=(0, 0, 0), font=fontb)
    for j, (name, _) in enumerate(cols):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    r = 0
    for b in bodies:
        for f in facings:
            y = top + r * (S + pad)
            sc = results[f"{b}_{f}"]
            dr.text((8, y + 8), f"{b}\n{f}", fill=(0, 0, 0), font=fontb)
            s1 = sc["ShirtButton_plainneck"]; s0 = sc["ShirtButton_plain4x"]; s2 = sc["ShirtButton_knob"]
            dr.text((8, y + 70), f"plain x4:\n IoU {s0['iou']}\n edge {s0['edge_px']} px\nrebuilt:\n IoU {s1['iou']}\n edge {s1['edge_px']} px\n lum {s1['lum_mae']}\nwith knob:\n IoU {s2['iou']}\n edge {s2['edge_px']} px", fill=(0, 0, 0), font=font)
            for j, (_, get) in enumerate(cols):
                t = get(b, f)
                if t is None:
                    continue
                im.paste(crop_tile(t, S).convert("RGB"), (left + j * (S + pad), y))
            r += 1
    path = rf"{CAPT}\2026-11-06_crack-holdout.png"
    im.save(path); print("board", path)
    # layers board: one row per body, south, showing the decomposition
    cols2 = ["WDI body", "shading (body through LUT)", "coverage, hole", "outline strokes", "detail lines (warped, re-stroked)", "result", "WDI truth"]
    H2 = top + 9 * (S + pad)
    im2 = Image.new("RGB", (left + len(cols2) * (S + pad), H2), (235, 235, 230)); dr = ImageDraw.Draw(im2)
    dr.text((8, 8), "The layers of the rebuild (ShirtButton, hold-out)", fill=(0, 0, 0), font=fontb)
    for j, name in enumerate(cols2):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    r = 0
    for b in bodies:
        for f in facings:
            y = top + r * (S + pad); L = tiles[(b, f, "layers")]
            dr.text((8, y + 8), f"{b}\n{f}\nd={L['d']} w_out={L['w_out']:.0f}\nw_hole={L['w_hole']:.1f}\nvanilla strokes\n out {L['s_out']:.0f} hole {L['s_hole']:.0f}", fill=(0, 0, 0), font=font)
            def grey(m, a=None):
                g = np.zeros((N, N, 4), np.float32); g[..., :3] = m[..., None]; g[..., 3] = 1.0 if a is None else a
                return g
            cov = L["coverage"].astype(np.float32); hole = L["hole"].astype(np.float32)
            covimg = np.zeros((N, N, 4), np.float32); covimg[..., 0] = cov; covimg[..., 1] = cov * (1 - hole) ; covimg[..., 2] = cov * (1 - hole); covimg[..., 3] = cov
            panels = [load(rf"{WS}\Bodies\Naked_{b}_{f}.png"), grey(L["fabric"], L["alpha"].astype(np.float32)), covimg,
                      grey(1 - L["outline"], np.clip(L["outline"], 0, 1)), grey(1 - L["lines"].astype(np.float32), L["lines"].astype(np.float32)),
                      tiles[(b, f, "ShirtButton", "plainneck")], tiles[(b, f, "ShirtButton", "wdi")]]
            for j, t in enumerate(panels):
                im2.paste(crop_tile(t, S).convert("RGB"), (left + j * (S + pad), y))
            r += 1
    path2 = rf"{CAPT}\2026-11-06_crack-layers.png"
    im2.save(path2); print("board", path2)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "both"
    results, tiles = run(mode)
    if mode == "both":
        board(results, tiles, mode)
