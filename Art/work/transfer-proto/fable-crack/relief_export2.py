"""Export 2 (Virginie 2026-11-08: 'la séparation des jambes aussi', 'regénère le squelette intérieur'): the shaded relief of
shade3d as a closed mesh like relief_export.py, plus
  - the two legs as separate rings below the crotch notch (rows where the silhouette has two runs),
  - landmark rows (world y) for the skeleton of the viewer: top, shoulder tip, apex, fold, navel, sex, crotch.
Output out/relief3d-shade5.json {R,U,bodies:{b:{rows:[R][2U*3], legs:{L:[n][2U*3],R:[...]}|null, lm:{name:y}}}}.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python relief_export2.py [Body ...]"""
import os
import pathlib
import sys, json
import numpy as np
from scipy import ndimage as ndi
import crack as c1, explain5b as e5
import relief3d as r3
import shade3d  # noqa: F401  (patches r3.height and r3.silhouette)

N = c1.N
R, U = 360, 44
# Keep roughly the former 4 px vertical smoothing span now that rings are
# sampled every ~0.65 source pixel instead of every ~1.6 pixels.
SIGMA_ROWS = 6.0
BODIES = ["Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female"]
RIB_LEVELS = 12
SIDE_MARGIN = 10.0
FRONT_MARGIN = 7.0
BACK_MARGIN = 12.0
SKIN_MARGIN = 5.0
CAGE_FADE = float(os.environ.get("CAGE_FADE", 14.0))  # source px over which the cage floor fades out
# Row-wise smoothing of the silhouette extents (source rows); 0 = raw stair steps.
PROFILE_SIGMA = float(os.environ.get("PROFILE_SIGMA", 2.0))
_NO_SMOOTH = [None]


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0] - 1))


_SMOOTH = {}


def smooth_extents(mask, sigma=PROFILE_SIGMA):
    """Per-row left/right extents with the sprite's 4 px stair-steps removed.

    The 128 px source is upscaled, so the raw extents step every few rows and
    carve horizontal bands into the lit mesh.  A small 1-D Gaussian along the
    rows only (never across) keeps the profile within a pixel or two.
    """
    key = id(mask)
    if key not in _SMOOTH:
        lo = np.full(mask.shape[0], np.nan)
        hi = np.full(mask.shape[0], np.nan)
        for y in np.where(mask.any(axis=1))[0]:
            xs = np.flatnonzero(mask[y])
            lo[y], hi[y] = xs[0], xs[-1]
        ok = np.isfinite(lo)
        idx = np.flatnonzero(ok)
        for arr in (lo, hi):
            arr[idx[0]:idx[-1] + 1] = np.interp(np.arange(idx[0], idx[-1] + 1), idx, arr[idx])
            arr[idx[0]:idx[-1] + 1] = ndi.gaussian_filter1d(arr[idx[0]:idx[-1] + 1], sigma, mode="nearest")
        _SMOOTH[key] = (lo, hi, mask)
    return _SMOOTH[key][:2]


def extent_at(mask, y):
    """Linearly interpolate the left/right silhouette limits at a sub-pixel row."""
    if PROFILE_SIGMA > 0 and mask is not _NO_SMOOTH[0]:
        lo, hi = smooth_extents(mask)
        y = float(np.clip(y, 0, mask.shape[0] - 1))
        if not np.isfinite(lo[int(round(y))]):
            return None, None
        return float(np.interp(y, np.arange(len(lo)), lo)), float(np.interp(y, np.arange(len(hi)), hi))
    y = float(np.clip(y, 0, mask.shape[0] - 1))
    low, high = int(np.floor(y)), int(np.ceil(y))
    a, b = r3.extent(mask, low), r3.extent(mask, high)
    if a[0] is None:
        return b
    if b[0] is None:
        return a
    t = y - low
    return ((1 - t) * a[0] + t * b[0], (1 - t) * a[1] + t * b[1])


def map_row_at(y, src_mask, dst_mask):
    """Continuous counterpart of relief3d.map_row for the dense mesh rings."""
    a0, a1 = r3.rows_of(src_mask)
    b0, b1 = r3.rows_of(dst_mask)
    return b0 + (float(y) - a0) / max(a1 - a0, 1) * (b1 - b0)


def east_profile_bounds(world_y, south_mask, east_mask, zmean):
    """Return the east-view back/front limits for a world-space mesh row."""
    y = -float(world_y)
    ye = map_row_at(y, south_mask, east_mask)
    back, front = extent_at(east_mask, ye)
    if back is None:
        return None
    center = 0.5 * (back + front) - zmean
    half_depth = 0.5 * (front - back)
    return center - half_depth, center + half_depth


def constrain_east_profile(rows, south_mask, east_mask, zmean):
    """Keep relief inside the measured east-view envelope.

    The base ellipsoid already reaches both profile edges.  Adding a front or
    back relief directly on top of it made the mesh 11--13 px too deep in the
    profile.  Per row, rescale only the depth deviation around the measured
    east centre so the visible relief survives but neither side crosses its
    source outline.
    """
    constrained = 0
    for row in rows:
        bounds = east_profile_bounds(row[0, 1], south_mask, east_mask, zmean)
        if bounds is None:
            continue
        back, front = bounds
        center = 0.5 * (back + front)
        half_depth = 0.5 * (front - back)
        radius = max(float(row[:, 2].max() - center), float(center - row[:, 2].min()))
        if radius > half_depth + 1e-6:
            row[:, 2] = center + (row[:, 2] - center) * (half_depth / radius)
            constrained += 1
    return constrained


def correct_east_profile(rows, south_mask, east_mask, zmean, sigma):
    """Pull the front and back of each ring onto the measured east profile, both ways, with a row-smoothed correction.

    The fitted wdi3d fields drift from the profile (the fit follows the drawn shading), up to 10-20 px at p95.
    The hard cap of constrain_east_profile cured only the too-deep rows and, row by row, cut horizontal bands
    into the lit mesh. Here the per-row shift of the front and of the back is smoothed along the rows
    (sigma in rows), then the ring is remapped piecewise-linearly around its mid depth.
    """
    n = len(rows)
    f = rows[:, :, 2].max(axis=1)
    b = rows[:, :, 2].min(axis=1)
    df = np.zeros(n)
    db = np.zeros(n)
    ok = np.zeros(n, bool)
    for i, row in enumerate(rows):
        bounds = east_profile_bounds(row[0, 1], south_mask, east_mask, zmean)
        if bounds is None:
            continue
        db[i] = bounds[0] - b[i]
        df[i] = bounds[1] - f[i]
        ok[i] = True
    if ok.any():
        idx = np.arange(n)
        df = np.interp(idx, idx[ok], df[ok])
        db = np.interp(idx, idx[ok], db[ok])
    if sigma > 0:
        df = ndi.gaussian_filter1d(df, sigma, mode="nearest")
        db = ndi.gaussian_filter1d(db, sigma, mode="nearest")
    for i, row in enumerate(rows):
        m = 0.5 * (f[i] + b[i])
        z = row[:, 2]
        up = np.clip((z - m) / max(f[i] - m, 1e-6), 0, 1)
        dn = np.clip((m - z) / max(m - b[i], 1e-6), 0, 1)
        row[:, 2] = z + up * df[i] + dn * db[i]
    return int(ok.sum())


def _smooth(values, radius=2):
    """Five-level edge-preserving box smoothing, matching the viewer cage."""
    padded = np.pad(np.asarray(values, float), (radius, radius), mode="edge")
    return np.convolve(padded, np.full(2 * radius + 1, 1 / (2 * radius + 1)), mode="valid")


def _row_at_y(rows, y):
    """Interpolate a ring at world y; exported rows run from top to bottom."""
    ys = rows[:, 0, 1]
    out = np.empty_like(rows[0])
    for point in range(rows.shape[1]):
        for axis in range(3):
            out[point, axis] = np.interp(y, ys[::-1], rows[::-1, point, axis])
    return out


def apply_rib_cage_floor(rows, lm, profile_bounds=None):
    """Keep thoracic skin outside a rigid rib cage before it reaches the viewer.

    This ports the former viewer-only floor. It constrains only the thorax;
    pelvis and femurs stay diagnostic until they have equivalent landmarks.
    """
    required = ("top", "apex", "fold", "navel")
    if any(key not in lm for key in required):
        return rows, {"moved": 0, "reason": "missing thorax landmarks"}

    top, apex, fold, navel = (lm[key] for key in required)
    cage_top = top - 0.20 * (top - fold)
    cage_bottom = apex - 0.85 * (apex - navel)
    if cage_top <= cage_bottom:
        return rows, {"moved": 0, "reason": "invalid thorax range"}

    levels = []
    for index in range(RIB_LEVELS):
        t = index / (RIB_LEVELS - 1)
        y = cage_top + (cage_bottom - cage_top) * t
        ring = _row_at_y(rows, y)
        x = ring[:, 0]
        front = ring[:U, 2]
        back = ring[U:, 2]
        center_x = 0.5 * (x.min() + x.max())
        side = 0.5 * (x.max() - x.min()) - SIDE_MARGIN
        front_skin = front.max() - FRONT_MARGIN
        back_skin = back.min() + BACK_MARGIN
        if side <= 1 or front_skin <= back_skin:
            continue
        width_factor = 0.45 + 0.55 * np.sin(t / 0.65 * np.pi / 2) if t <= 0.65 else 1 - 0.12 * ((t - 0.65) / 0.35)
        depth_factor = 0.50 + 0.50 * np.sin(t / 0.60 * np.pi / 2) if t <= 0.60 else 1 - 0.10 * ((t - 0.60) / 0.40)
        levels.append({"y": y, "x": center_x, "side": side, "front": front_skin, "back": back_skin,
                       "width_factor": width_factor, "depth_factor": depth_factor})

    if len(levels) != RIB_LEVELS:
        return rows, {"moved": 0, "reason": "cage does not fit all rib levels"}

    front = _smooth([level["front"] for level in levels])
    back = _smooth([level["back"] for level in levels])
    # Fit a rigid sternum rather than following every skin dimple. Raising the
    # line to the 60th residual percentile preserves a genuine median groove.
    level_index = np.arange(RIB_LEVELS, dtype=float)
    slope, intercept = np.polyfit(level_index, front, 1)
    residuals = front - (slope * level_index + intercept)
    front = slope * level_index + intercept + np.quantile(residuals, 0.60)
    scale_x = np.quantile([level["side"] / level["width_factor"] for level in levels], 0.40)

    for index, level in enumerate(levels):
        level["a"] = min(level["side"], scale_x * level["width_factor"])
        level["back"] = back[index]
        level["depth"] = (front[index] - back[index]) * level["depth_factor"]
        if profile_bounds is not None:
            bounds = profile_bounds(level["y"])
            if bounds is not None:
                back_limit, front_limit = bounds
                level["back"] = max(level["back"], back_limit + SKIN_MARGIN)
                level["depth"] = min(level["depth"], front_limit - SKIN_MARGIN - level["back"])

    moved = 0
    for row in rows:
        y = row[0, 1]
        if y > cage_top + CAGE_FADE or y < cage_bottom - CAGE_FADE:
            continue
        # Past either end the last rib level is held and its push fades out,
        # so the floor does not leave a step in the skin at the cage edge.
        overshoot = max(y - cage_top, cage_bottom - y, 0.0)
        fade = 1.0 - overshoot / CAGE_FADE
        fade = fade * fade * (3 - 2 * fade)
        u = (cage_top - y) / (cage_top - cage_bottom) * (RIB_LEVELS - 1)
        u = float(np.clip(u, 0, RIB_LEVELS - 1))
        low = min(RIB_LEVELS - 2, max(0, int(np.floor(u))))
        weight = np.clip(u - low, 0, 1)
        a = (1 - weight) * levels[low]["a"] + weight * levels[low + 1]["a"]
        center_x = (1 - weight) * levels[low]["x"] + weight * levels[low + 1]["x"]
        back_z = (1 - weight) * levels[low]["back"] + weight * levels[low + 1]["back"]
        depth = (1 - weight) * levels[low]["depth"] + weight * levels[low + 1]["depth"]
        if a <= 1 or depth <= 1:
            continue
        bounds = profile_bounds(y) if profile_bounds is not None else None
        back_limit, front_limit = bounds if bounds is not None else (-np.inf, np.inf)
        for point_index, point in enumerate(row):
            q = 1 - ((point[0] - center_x) / a) ** 2
            if q <= 0:
                continue
            half_depth = 0.5 * depth * np.sqrt(q)
            center_z = back_z + 0.5 * depth
            if point_index < U:
                floor = center_z + half_depth + SKIN_MARGIN
                if point[2] < floor:
                    point[2] = point[2] + fade * (min(floor, front_limit) - point[2])
                    moved += 1
            else:
                floor = center_z - half_depth - SKIN_MARGIN
                if point[2] > floor:
                    point[2] = point[2] + fade * (max(floor, back_limit) - point[2])
                    moved += 1

    return rows, {
        "moved": moved,
        "top": round(cage_top, 1),
        "bottom": round(cage_bottom, 1),
        # Store the actual constraint so the viewer renders the same cage that
        # limited this mesh instead of independently fitting a second one.
        "levels": [
            {key: round(float(level[key]), 3) for key in ("y", "x", "a", "back", "depth")}
            for level in levels
        ],
    }


def one(body, fields=None):
    """fields: optional {"south", "north", "zc"} from wdi3d.py; they replace the shade3d height fields."""
    imgs = r3.views(body, False)
    M = {f: r3.silhouette(imgs[f]) for f in imgs}
    H, B, P = {}, {}, {}
    for f in ("south", "east", "north"):
        s, d, names = e5.named_pairs(body, f)
        pts = {n: tuple(s[i]) for i, n in enumerate(names)}
        if f == "south":
            P = pts
        lum = c1.lum(imgs[f])
        # Keep the explicit three-silhouette base so the east landmarks can
        # contribute a small signed profile correction to the closed mesh.
        # Previously H["east"] was calculated but never reached a vertex.
        B[f] = shade3d._base_height(f, M, pts, lum)
        H[f] = r3.height(f, M, pts, lum)
    if fields is not None:
        H["south"], H["north"] = fields["south"], fields["north"]
        H["east"] = B["east"]                        # the wdi3d fields already carry the profile
    ms, me, mn = M["south"], M["east"], M["north"]
    s0, s1 = r3.rows_of(ms)
    cx_south = np.mean([np.mean(r3.extent(ms, y)) for y in range(s0, s1 + 1)])
    n0, n1 = r3.rows_of(mn)
    cx_north = np.mean([np.mean(r3.extent(mn, y)) for y in range(n0, n1 + 1)])
    # Prefer the drawn crotch notch. Four WDI bodies are drawn as a continuous
    # lower silhouette, even though their crotch landmark still defines two
    # legs. In that case, split only the mesh's medial seam: the outer source
    # projection remains unchanged and no gap is invented in the sprite.
    cy = int(P["crotch point"][1]) if "crotch point" in P else int(0.9 * (s1 - s0) + s0)
    ysplit = None
    split_mode = None
    for y in range(cy - 8, s1 + 1):
        rr = [r for r in runs(ms[y]) if r[1] - r[0] >= 4]
        if len(rr) >= 2:
            ysplit = y
            split_mode = "silhouette-notch"
            break
    if ysplit is None and cy < s1 - 1:
        ysplit = min(max(cy, s0), s1 - 1)
        split_mode = "crotch-landmark"
    east_detail = H["east"] - B["east"]

    def _signed_peak(values):
        """Keep the largest signed local profile patch, never a row average."""
        if not len(values):
            return 0.0
        lo, hi = float(np.min(values)), float(np.max(values))
        return hi if abs(hi) >= abs(lo) else lo

    def profile_detail(y):
        """Front/back detail at one source row from the east-view patches.

        The profile landmarks live slightly inside the black outline.  Taking
        the signed local peak on each half preserves a chest/belly projection
        or a waist/small-back hollow without allowing paint variation to
        change the measured profile silhouette.
        """
        ye = map_row_at(y, ms, me)
        zb, zf = extent_at(me, ye)
        if zb is None:
            return 0.0, 0.0
        row = east_detail[int(np.clip(round(ye), 0, N - 1))]
        mid = int(round(0.5 * (zb + zf)))
        back = row[int(max(0, np.floor(zb))):max(mid, 1)]
        front = row[min(mid, N - 1):int(min(N, np.ceil(zf) + 1))]
        return _signed_peak(front), _signed_peak(back)

    def ring(y, xa, xb, xl, xr):
        ye = map_row_at(y, ms, me); zb, zf = extent_at(me, ye)
        yn = map_row_at(y, ms, mn); nl, nr = extent_at(mn, yn)
        if zb is None or nl is None:
            return None
        zc = 0.5 * (zb + zf)
        if fields is not None:                       # wdi3d measures its fields from its own centre plane
            zw = float(np.interp(ye, np.arange(N), fields["zc"]))
            zc = zw if np.isfinite(zw) else zc
        front_profile, back_profile = profile_detail(y)
        out = np.zeros((2 * U, 3))
        for k in range(U):
            u = k / (U - 1)
            xs = xa + u * (xb - xa)
            hf = ndi.map_coordinates(H["south"], [[y], [xs]], order=1)[0]
            xn = nr - ((xs - xl) / max(xr - xl, 1)) * (nr - nl)
            hb = ndi.map_coordinates(H["north"], [[yn], [xn]], order=1)[0]
            # The east patches are intentionally a small correction: the
            # south/north maps provide the primary surface while the measured
            # east envelope remains a hard cap below.
            section = np.sqrt(max(0.0, 1.0 - (2.0 * u - 1.0) ** 2))
            out[k] = (xs - cx_south, -y, zc + hf + 0.16 * front_profile * section)
            # The north sprite is viewed from the opposite camera direction:
            # x must be mirrored into world space.  Previously xn affected
            # only the sampled height, so every rear contour was silently
            # projected from the south sprite instead of its own source.
            out[2 * U - 1 - k] = (cx_north - xn, -y, zc - hb - 0.16 * back_profile * section)
        return out

    ytop = ysplit if ysplit is not None else s1
    rows = []
    for i in range(R):
        y = s0 + (ytop - s0) * i / (R - 1)
        xl, xr = extent_at(ms, y)
        rg = None if xl is None else ring(y, xl, xr, xl, xr)
        rows.append(rg if rg is not None else (rows[-1] if rows else np.zeros((2 * U, 3))))
    rows = ndi.gaussian_filter1d(np.array(rows), SIGMA_ROWS if fields is None else 3.0, axis=0, mode="nearest")
    zmean = float(np.mean(rows[..., 2]))
    rows[..., 2] -= zmean
    cap_mode = os.environ.get("WDI_CAP", "smooth")
    if fields is None or cap_mode == "hard":
        profile_rows = constrain_east_profile(rows, ms, me, zmean)
    elif cap_mode == "smooth":
        profile_rows = correct_east_profile(rows, ms, me, zmean, float(os.environ.get("WDI_CAP_SIGMA", 3.0)))
    else:
        profile_rows = 0
    legs = None
    if ysplit is not None and s1 - ysplit >= 2:
        L, Rr = [], []
        for y in range(ysplit - 1, s1 + 1):
            xl, xr = r3.extent(ms, y)
            rr = [r for r in runs(ms[y]) if r[1] - r[0] >= 3]
            if xl is None:
                continue
            if split_mode == "silhouette-notch":
                if len(rr) < 2:
                    continue
                a, b = rr[0], rr[-1]
            else:
                mid = 0.5 * (xl + xr)
                a, b = (xl, mid), (mid, xr)
                if a[1] - a[0] < 3 or b[1] - b[0] < 3:
                    continue
            ra = ring(y, a[0], a[1], xl, xr); rb = ring(y, b[0], b[1], xl, xr)
            if ra is None or rb is None:
                continue
            L.append(ra); Rr.append(rb)
        if len(L) >= 2:
            L = np.array(L); Rr = np.array(Rr)
            L[..., 2] -= zmean; Rr[..., 2] -= zmean
            constrain_east_profile(L, ms, me, zmean)
            constrain_east_profile(Rr, ms, me, zmean)
            legs = {
                "L": np.round(L.reshape(len(L), -1), 1 if fields is None else 2).tolist(),
                "R": np.round(Rr.reshape(len(Rr), -1), 1 if fields is None else 2).tolist(),
                "mode": split_mode,
            }
    lm = {"top": -float(s0), "bottom": -float(s1)}
    for key, nm in (("apex", "breast apex L"), ("fold", "under-breast fold L"), ("navel", "navel"), ("sex", "sex"),
                    ("crotch", "crotch point"), ("shoulder", "shoulder tip L"), ("armpit", "armpit L")):
        if nm in P:
            lm[key] = -float(P[nm][1])
    if ysplit is not None:
        lm["split"] = -float(ysplit)
    profile_bounds = lambda world_y: east_profile_bounds(world_y, ms, me, zmean)
    if fields is None:
        rows, cage = apply_rib_cage_floor(rows, lm, profile_bounds)
    else:                                            # fitted surface kept as is: the cage is only drawn
        _, cage = apply_rib_cage_floor(rows.copy(), lm, profile_bounds)
    cage["profile_rows_constrained"] = profile_rows
    e0, e1 = r3.rows_of(me)
    frame = {"s": [int(s0), int(s1)], "n": [int(n0), int(n1)], "e": [int(e0), int(e1)],
             "cxs": round(float(cx_south), 2), "cxn": round(float(cx_north), 2), "zmean": round(zmean, 2)}
    if fields is not None:
        # centre plane per south row (viewer: the light is taken relative to it, as in the wdi3d capture);
        # 0.01 px vertices: at 0.1 px the ring-to-ring slope noise is as large as the toon step
        ye = [map_row_at(y, ms, me) for y in range(s0, s1 + 1)]
        frame["zc"] = np.round(np.interp(ye, np.arange(N), np.nan_to_num(fields["zc"], nan=zmean)) - zmean, 2).tolist()
    return {"rows": np.round(rows.reshape(R, -1), 1 if fields is None else 2).tolist(), "legs": legs, "lm": lm, "cage": cage, "frame": frame}


def main():
    names = [a for a in sys.argv[1:] if a in BODIES] or BODIES
    out = {}
    for b in names:
        print(b, flush=True)
        out[b] = one(b)
        print("  split", out[b]["lm"].get("split"), "legs", None if out[b]["legs"] is None else len(out[b]["legs"]["L"]), flush=True)
    # Keep this export runnable directly on Cloud as well as through the
    # historical Windows-path launcher.  The out directory lives beside this
    # script in both environments.
    output = pathlib.Path(__file__).with_name("out") / "relief3d-shade5.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as handle:
        json.dump({"R": R, "U": U, "bodies": out}, handle, separators=(",", ":"))
    print("ok")


if __name__ == "__main__":
    main()
