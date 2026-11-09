"""Landmark-led surface relief for the WDI bodies.

The active surface is deliberately *not* reconstructed from a column-by-column
luminance integral.  The WDI sprites use broad white and grey areas for style,
so treating every tonal transition as height made horizontal terraces and
``pillow`` torsos.  Instead we start from the smooth three-silhouette envelope
in :func:`relief3d.base_height` and add a small set of signed, local anatomical
patches.  Each patch is tied to artist-measured landmarks (rather than a shade
threshold): collar/neck, armpit, attached breast or pectoral, sternum, navel,
pubis/groin, abdomen, hips and the posterior gluteal mass.

``RELIEF_MODE=legacy`` retains the previous luminance solver as an explicit
fallback for comparison.  ``structured`` is the default and is the only mode
used by ``relief_export2.py`` normally.
"""
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
RELIEF_MODE = os.environ.get("RELIEF_MODE", "structured").lower()


def _point(pts, name):
    """Return a named point as floats, or ``None`` when a study omitted it."""
    p = pts.get(name)
    return None if p is None else (float(p[0]), float(p[1]))


def _gauss(xx, yy, point, sx, sy, amp=1.0):
    """A compact smooth signed patch centred on a measured landmark."""
    if point is None or sx <= 0 or sy <= 0:
        return np.zeros_like(xx, dtype=float)
    x, y = point
    return amp * np.exp(-0.5 * (((xx - x) / sx) ** 2 + ((yy - y) / sy) ** 2))


def _segment(xx, yy, a, b, width, amp=1.0, end_taper=0.0):
    """A rounded signed crease along the finite segment ``a``--``b``.

    Unlike a row-wide dark-band conversion this has finite ends and therefore
    cannot turn an under-breast fold, collarbone or groin crease into a stripe
    across the whole torso.
    """
    if a is None or b is None or width <= 0:
        return np.zeros_like(xx, dtype=float)
    ax, ay = a; bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 < 1e-6:
        return _gauss(xx, yy, a, width, width, amp)
    t = ((xx - ax) * dx + (yy - ay) * dy) / length2
    tc = np.clip(t, 0.0, 1.0)
    px, py = ax + tc * dx, ay + tc * dy
    patch = amp * np.exp(-0.5 * ((np.hypot(xx - px, yy - py) / width) ** 2))
    if end_taper:
        patch *= np.clip(np.minimum(t, 1.0 - t) / end_taper, 0.0, 1.0)
    return patch


def _curve(xx, yy, a, control, b, width, amp=1.0, end_taper=0.0):
    """A rounded crease along a short quadratic Bezier arc.

    The source's attachment lines are usually shallow arcs.  A single straight
    segment made their lighting read as a hard horizontal rail even when its
    endpoints were measured correctly.  Sampling this tiny curve is cheap at
    the sprite resolution and keeps the depression local and anatomical.
    """
    if a is None or control is None or b is None or width <= 0:
        return np.zeros_like(xx, dtype=float)
    # Measure against short *segments*, not isolated samples.  The latter
    # creates a visible dotted ridge where nearest samples exchange ownership.
    ts = np.linspace(0.0, 1.0, 17)
    ax, ay = a; cx, cy = control; bx, by = b
    px = (1.0 - ts) ** 2 * ax + 2.0 * (1.0 - ts) * ts * cx + ts ** 2 * bx
    py = (1.0 - ts) ** 2 * ay + 2.0 * (1.0 - ts) * ts * cy + ts ** 2 * by
    sx, sy = px[:-1], py[:-1]
    vx, vy = px[1:] - sx, py[1:] - sy
    rx, ry = xx[..., None] - sx, yy[..., None] - sy
    t = np.clip((rx * vx + ry * vy) / (vx * vx + vy * vy), 0.0, 1.0)
    dx, dy = rx - t * vx, ry - t * vy
    distance2 = np.min(dx * dx + dy * dy, axis=-1)
    patch = amp * np.exp(-0.5 * distance2 / (width * width))
    if end_taper:
        # Rounded caps taper only inside a few crease widths, preserving a
        # continuous derivative along the entire arc.
        cap_distance2 = np.minimum((xx - ax) ** 2 + (yy - ay) ** 2,
                                   (xx - bx) ** 2 + (yy - by) ** 2)
        cap_width = max(width * (1.0 + 4.0 * end_taper), width)
        patch *= 1.0 - np.exp(-0.5 * cap_distance2 / (cap_width * cap_width))
    return patch


def _mid(a, b, fallback=(256.0, 256.0)):
    if a is not None and b is not None:
        return ((a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5)
    return a or b or fallback


def _body_flags():
    """Small semantic body classes; never infer them from pixel brightness."""
    name = BODY[0] or ""
    return {
        "female": "Female" in name,
        "fat": "Fat" in name,
        "hulk": "Hulk" in name,
        # ``Male`` is the project's Average body (there is no Average asset).
        "average": name == "Male",
    }


def _anchors(pts):
    """Collect the measurements shared by all local patch recipes."""
    neck_l, neck_r = _point(pts, "neck base L"), _point(pts, "neck base R")
    shoulder_l, shoulder_r = _point(pts, "shoulder tip L"), _point(pts, "shoulder tip R")
    armpit_l, armpit_r = _point(pts, "armpit L"), _point(pts, "armpit R")
    apex_l, apex_r = _point(pts, "breast apex L"), _point(pts, "breast apex R")
    fold_l, fold_r = _point(pts, "under-breast fold L"), _point(pts, "under-breast fold R")
    hip_l, hip_r = _point(pts, "hip L"), _point(pts, "hip R")
    return {
        "neck_l": neck_l, "neck_r": neck_r,
        "notch": _point(pts, "jugular notch") or _mid(neck_l, neck_r),
        "shoulder_l": shoulder_l, "shoulder_r": shoulder_r,
        "armpit_l": armpit_l, "armpit_r": armpit_r,
        "apex_l": apex_l, "apex_r": apex_r,
        "cleavage": _point(pts, "cleavage") or _mid(apex_l, apex_r),
        "fold_l": fold_l, "fold_r": fold_r,
        "fold": _mid(fold_l, fold_r),
        "navel": _point(pts, "navel"),
        "waist_l": _point(pts, "waist L"), "waist_r": _point(pts, "waist R"),
        "hip_l": hip_l, "hip_r": hip_r, "hips": _mid(hip_l, hip_r),
        "groin_l": _point(pts, "groin crease L"),
        "groin_r": _point(pts, "groin crease R"),
        "sex": _point(pts, "sex"),
        "crotch": _point(pts, "crotch point"),
    }


def _front_torso_patches(xx, yy, a, flags):
    """Signed front anatomy, entirely delimited by the 2026-11-03 points."""
    out = np.zeros_like(xx, dtype=float)
    notch, fold = a["notch"], a["fold"]
    midx = a["cleavage"][0] if a["cleavage"] is not None else notch[0]

    # Neck root, clavicles and axillary hollows.  The small finite segments
    # make the neck legible without mistaking a grey chest plane for depth.
    out += _segment(xx, yy, a["neck_l"], a["neck_r"], 4.2, -2.1, 0.13)
    for shoulder in (a["shoulder_l"], a["shoulder_r"]):
        if notch is not None and shoulder is not None:
            out += _segment(xx, yy, notch, shoulder, 3.8, -1.9, 0.14)
    for armpit in (a["armpit_l"], a["armpit_r"]):
        out += _gauss(xx, yy, armpit, 7.5, 6.5, -3.0)

    # The sternum is a finite valley between notch and fold.  It is distinct
    # from the cleavage below, so female skin can return to the rib cage.
    if notch is not None and fold is not None:
        sternum_end = (midx, min(fold[1] - 4.0, notch[1] + 0.80 * (fold[1] - notch[1])))
        out += _segment(xx, yy, notch, sternum_end, 4.2, -1.65, 0.15)

    breast_pairs = ((a["apex_l"], a["fold_l"], a["armpit_l"]),
                    (a["apex_r"], a["fold_r"], a["armpit_r"]))
    if flags["female"]:
        # A breast is a supported teardrop: the lobe is anchored between its
        # apex, fold and armpit, then the fold and cleavage cut it back into
        # the cage.  This deliberately has no free spherical "add-on".
        lift = 4.5 if flags["fat"] else 3.8
        for apex, fold_side, armpit in breast_pairs:
            if apex is None:
                continue
            half = max(abs(apex[0] - midx), 15.0)
            drop = max((fold_side[1] - apex[1]) if fold_side is not None else 20.0, 12.0)
            # A hanging breast widens and remains full *below* the apex.  A
            # symmetric ellipse here was still reading as a sphere glued to
            # the chest, especially on Fat_Female.  This anisotropic patch is
            # narrow/high at its attachment and broad/low only as it falls.
            dy = yy - apex[1]
            vertical = np.where(dy < 0, dy / (0.52 * drop), dy / (1.18 * drop))
            width = half * (0.42 + 0.27 * np.clip((dy + 0.20 * drop) / (1.25 * drop), 0.0, 1.0))
            lobe = lift * np.exp(-0.5 * (vertical ** 2 + ((xx - apex[0]) / width) ** 2))
            # The upper/lateral attachment spreads toward the clavicle and
            # armpit with only a fraction of the breast volume.
            if armpit is not None:
                support = ((0.45 * apex[0] + 0.55 * armpit[0]),
                           0.55 * apex[1] + 0.45 * armpit[1])
                lobe += _gauss(xx, yy, support, 0.52 * half, max(drop, 14.0), 0.28 * lift)
            # Do not let a hanging lobe rise as a ball above its attachment.
            lobe *= 1.0 / (1.0 + np.exp(-(yy - (apex[1] - 0.30 * drop)) / 3.5))
            if fold_side is not None:
                # The fold is an attachment, not a sawed-off shelf: tissue
                # may hang slightly below it but fades over a local span.
                lobe *= 1.0 / (1.0 + np.exp((yy - (fold_side[1] + 0.55 * drop)) / 4.5))
            out += lobe
        # Each breast owns its attachment crease.  Joining both points with a
        # single trough made a rigid horizontal rail across soft chests.
        for fold_side in (a["fold_l"], a["fold_r"]):
            if fold_side is None:
                continue
            sign = -1.0 if fold_side[0] < midx else 1.0
            inner = (midx + sign * 5.5, fold_side[1] - 0.5)
            # The fold dips a little under the hanging lobe, then climbs
            # into the sternum; it must not become a ruler-straight shelf.
            control = ((fold_side[0] + inner[0]) * 0.5, fold_side[1] + 3.5)
            # The inked source fold is a useful *location*, but its dark value
            # is not its depth.  Keep just enough depression to attach the
            # mass without converting the whole painted fold into a rail.
            out += _curve(xx, yy, fold_side, control, inner, 4.4, -0.65, 0.20)
        if a["cleavage"] is not None and fold is not None:
            out += _segment(xx, yy, a["cleavage"], fold, 4.3, -2.15, 0.16)
    else:
        # Pectorals are fan-shaped local masses, bounded inferiorly by the
        # measured fold line.  Hulk gets greater relief, Average stays clear
        # but restrained; Thin receives only the attachment structure.
        amp = 5.0 if flags["hulk"] else 3.2 if flags["average"] else 2.9 if flags["fat"] else 1.7
        for apex, fold_side, armpit in breast_pairs:
            if apex is None or armpit is None:
                continue
            half = max(abs(apex[0] - midx), 12.0)
            height = max(abs(armpit[1] - apex[1]), 15.0)
            center = (0.42 * midx + 0.36 * apex[0] + 0.22 * armpit[0],
                      0.35 * apex[1] + 0.65 * armpit[1])
            # A fat male chest falls more broadly than a pec: same landmarks,
            # a lower and taller soft-tissue patch rather than a second kind
            # of generic sphere.
            if flags["fat"]:
                center = (center[0], center[1] + 0.20 * height)
                out += _gauss(xx, yy, center, 0.74 * half, 1.06 * height, amp)
            else:
                out += _gauss(xx, yy, center, 0.68 * half, 0.70 * height, amp)
            if fold_side is not None:
                inner = (midx + (-1.0 if fold_side[0] < midx else 1.0) * 5.0, fold_side[1] - 0.5)
                control = ((fold_side[0] + inner[0]) * 0.5, fold_side[1] + 2.5)
                out += _curve(xx, yy, fold_side, control, inner, 4.2, -0.45, 0.20)

    # Navel is a true dimple rather than an inverted luminance speck.  A very
    # small rim keeps it readable under the skin shader without adding a band.
    navel = a["navel"]
    if navel is not None:
        out += _gauss(xx, yy, navel, 3.4, 3.8, -6.2)
        out += _gauss(xx, yy, navel, 7.2, 7.5, 1.35)

    # Structured (paired) abdominal pads, not a periodic row solver.  The
    # lower pair is deliberately retained for Hulk/Average bodies.
    if (flags["hulk"] or flags["average"]) and fold is not None and navel is not None:
        top, bottom = fold[1] + 4.0, navel[1] - 5.0
        lower_bottom = (a["sex"] or a["crotch"] or navel)[1] - 5.0
        half = max(abs(a["waist_l"][0] - midx) if a["waist_l"] is not None else 26.0, 18.0)
        amp = 3.8 if flags["hulk"] else 2.35
        for y0, y1, local_amp in ((top, bottom, amp), (navel[1] + 5.0, lower_bottom, 0.88 * amp)):
            if y1 <= y0 + 6:
                continue
            cy = 0.5 * (y0 + y1)
            for sign in (-1, 1):
                out += _gauss(xx, yy, (midx + sign * 0.42 * half, cy), 0.33 * half, 0.34 * (y1 - y0), local_amp)
            out += _segment(xx, yy, (midx, y0), (midx, y1), 3.0, -1.15, 0.14)
        # A pair of short tendinous intersections reads as abdominal structure
        # without producing the old full-width horizontal band.
        for sign in (-1, 1):
            out += _segment(
                xx, yy,
                (midx + sign * 0.10 * half, bottom),
                (midx + sign * 0.56 * half, bottom),
                2.7, -0.42, 0.22,
            )

    # Pubis, sex, groin and leg roots are separate named forms.  Fat bodies
    # get a broad low, soft apron (not a hard horizontal shelf); every body
    # gets the two finite inguinal creases terminating at its sex point.
    sex, crotch = a["sex"], a["crotch"]
    if sex is not None:
        groin_y = np.mean([p[1] for p in (a["groin_l"], a["groin_r"]) if p is not None]) if any(p is not None for p in (a["groin_l"], a["groin_r"])) else sex[1] - 9.0
        hips = max(abs(a["hip_l"][0] - midx) if a["hip_l"] is not None else 30.0, 18.0)
        if flags["fat"]:
            apron_center = (midx, 0.58 * groin_y + 0.42 * sex[1])
            apron_width = 0.52 * hips if flags["female"] else 0.44 * hips
            apron_amp = 3.7 if flags["female"] else 2.9
            out += _gauss(xx, yy, apron_center, apron_width, max(9.0, 0.58 * abs(sex[1] - groin_y) + 8.0), apron_amp)
        else:
            out += _gauss(xx, yy, (midx, 0.58 * groin_y + 0.42 * sex[1]), 0.34 * hips, 9.0, 2.6 if flags["fat"] else 2.1)
        out += _gauss(xx, yy, sex, 3.8, 5.0, 1.6)
        for crease in (a["groin_l"], a["groin_r"]):
            if crease is not None:
                out += _curve(
                    xx, yy, crease,
                    ((crease[0] + sex[0]) * 0.5, crease[1] + 3.0), sex,
                    3.8, -2.05, 0.14,
                )
        if crotch is not None:
            out += _segment(xx, yy, sex, crotch, 3.2, -1.45, 0.16)
    return out


def _back_torso_patches(xx, yy, a, flags):
    """Back-side patches: spine, scapulae, hips and rounded gluteal masses."""
    out = np.zeros_like(xx, dtype=float)
    neck_mid = _mid(a["neck_l"], a["neck_r"])
    hips = a["hips"]
    crotch = a["crotch"]
    if neck_mid is not None and hips is not None:
        out += _segment(xx, yy, neck_mid, hips, 2.8, -2.3, 0.06)
    # The north point table deliberately has no fictitious breast points.  Use
    # only shoulder/armpit geometry for scapulae.
    for shoulder, armpit in ((a["shoulder_l"], a["armpit_l"]), (a["shoulder_r"], a["armpit_r"])):
        if shoulder is None or armpit is None:
            continue
        center = (0.58 * shoulder[0] + 0.42 * armpit[0], 0.45 * shoulder[1] + 0.55 * armpit[1])
        out += _gauss(xx, yy, center, 10.0, 13.0, 2.8 if flags["hulk"] else 1.25)
    if hips is not None and crotch is not None:
        spread = max(abs(a["hip_l"][0] - hips[0]) if a["hip_l"] is not None else 22.0, 16.0)
        height = max(abs(crotch[1] - hips[1]), 14.0)
        amp = 4.3 if flags["fat"] else 3.0
        for sign in (-1, 1):
            out += _gauss(xx, yy, (hips[0] + sign * 0.43 * spread, hips[1] + 0.48 * height), 0.44 * spread, 0.52 * height, amp)
        out += _segment(xx, yy, hips, crotch, 2.7, -3.1, 0.08)
    return out


def _profile_patches(xx, yy, pts, flags):
    """Side-view-only local planes; useful for viewer normals and diagnosis."""
    out = np.zeros_like(xx, dtype=float)
    front, back = _point(pts, "neck front"), _point(pts, "neck back")
    if front is not None and back is not None:
        out += _segment(xx, yy, back, front, 2.8, -2.8, 0.08)
    chest = _point(pts, "chest front")
    belly = _point(pts, "belly front")
    waist_front = _point(pts, "waist front")
    small_back = _point(pts, "waist back (small of the back)")
    buttock = _point(pts, "buttock back")
    if chest is not None:
        chest_amp = 3.4 if flags["female"] else 3.0 if flags["hulk"] else 2.7 if flags["fat"] else 1.7
        out += _gauss(xx, yy, chest, 8.0, 11.0, chest_amp)
    if belly is not None:
        out += _gauss(xx, yy, belly, 10.0, 12.0, 2.8 if flags["fat"] else 1.1)
    if waist_front is not None:
        out += _gauss(xx, yy, waist_front, 6.0, 7.0, -1.6)
    if small_back is not None:
        out += _gauss(xx, yy, small_back, 6.0, 8.0, -2.0)
    if buttock is not None:
        out += _gauss(xx, yy, buttock, 10.0, 12.0, 3.8 if flags["fat"] else 2.2)
    return out


def structured_height(view, M, pts, lum):
    """Active anatomy pass: smooth envelope plus signed landmark patches.

    ``lum`` remains an argument for API compatibility but is intentionally not
    sampled here.  Flat light/grey regions in the sprites are paint, not an
    instruction to extrude a full row of skin.
    """
    base = _base_height(view, M, pts, lum)
    yy, xx = np.mgrid[0:base.shape[0], 0:base.shape[1]]
    flags = _body_flags()
    if view == "south":
        detail = _front_torso_patches(xx, yy, _anchors(pts), flags)
    elif view == "north":
        detail = _back_torso_patches(xx, yy, _anchors(pts), flags)
    else:
        detail = _profile_patches(xx, yy, pts, flags)
    # Only joins between nearby named forms are softened.  Broad filtering was
    # the other source of the prior horizontal bands.
    detail = ndi.gaussian_filter(detail, 0.7) * M[view]
    return np.maximum(base + detail, 0.0) * M[view]


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


def height_shade(view, M, pts, lum):
    """Select the landmark surface, retaining the old solver for A/B work."""
    if RELIEF_MODE in ("legacy", "luminance", "column"):
        return legacy_height_shade(view, M, pts, lum)
    if RELIEF_MODE not in ("structured", "patches", "landmark"):
        raise ValueError(f"unknown RELIEF_MODE={RELIEF_MODE!r}; use structured or legacy")
    return structured_height(view, M, pts, lum)


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
