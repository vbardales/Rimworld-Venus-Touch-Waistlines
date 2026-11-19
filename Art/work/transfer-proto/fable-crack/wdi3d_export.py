"""Mesh and maps of the wdi3d model for the 3D viewer (2026-11-10).

Reads the fitted fields of wdi3d.py (out/wdi3d-<Body>.npz) and writes out/wdi3d-mesh.json in the
format of relief_export2.py (same rings, legs, landmark rows, cage), plus per body:
  - the mesh is built from the crease-free volumes closed(field) of the south and north views;
  - "tex": three 512 px maps (south, north, east), colour = areola albedo x (1 - ink), ink being the
    crease depth under the rim of the fitted field (the same quantity the wdi3d shader inks);
  - "frame": what the viewer needs to project a mesh point back into each sprite frame.
The creases are 2 to 14 px wide and the mesh has one vertex every 4 px across, so they are carried
as maps, not as geometry.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python wdi3d_export.py [Body ...]
then: uv run python body3d_build.py
"""
import base64
import io
import json
import os
import pathlib
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import relief_export2 as rx
import wdi3d as w

HERE = pathlib.Path(__file__).parent
N = w.N


def data_uri(rgb):
    buf = io.BytesIO()
    Image.fromarray(np.clip(255 * rgb + 0.5, 0, 255).astype(np.uint8)).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def rgba_uri(rgb, alpha):
    """Original WDI pixels with their body mask as alpha, for an opt-in comparison overlay in the viewer."""
    out = np.empty((*rgb.shape[:2], 4), np.uint8)
    out[..., :3] = np.clip(255 * rgb[..., :3] + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = np.clip(255 * alpha + 0.5, 0, 255).astype(np.uint8)
    buf = io.BytesIO()
    Image.fromarray(out, "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def ink_map(h, img, m):
    """Albedo x (1 - ink) of one view; white outside the creases and the areolae."""
    ink = np.clip((w.closed(h) - h) * m / w.GROOVE, 0, 1)
    albedo = np.ones((N, N, 3))
    yy, xx = np.mgrid[0:N, 0:N]
    for (x, y, r, col) in w.areolae(img, m):
        a = np.clip(r + 0.5 - np.hypot(xx - x, yy - y), 0, 1)[..., None]
        albedo = albedo * (1 - a) + col * a
    return albedo * (1 - ink[..., None])


GATE_LUM = 0.93   # sprite luminance under which the artist painted a grey (or ink)


def grey_gate(img, m):
    """0..1 where the sprite has grey or ink, soft edge: the viewer lets the mesh light grey the skin only there.

    The mesh keeps the profile steps (under-breast shelf, buttock fold) as full-width facets; the drawing
    greys only a wedge of them. Extent comes from the drawing, tone and slope from the mesh.
    """
    g = ((w.c1.lum(img) < GATE_LUM) & (m > 0)).astype(float)
    g = ndi.maximum_filter(g, size=9)
    return np.clip(1.6 * ndi.gaussian_filter(g, 4.0), 0, 1)


BAKE_MAX = 0.6     # loss range of the baked tone map (the shader caps the loss there too)


def baked_loss(h, m):
    """Tone lost by the capture of wdi3d.py (top light on the crease-free volumes), 0..1 = 0..BAKE_MAX.

    At the three sprite views the viewer shows exactly this tone, so it equals the 2D capture; turned away from
    a view, it falls back to the lit mesh.
    """
    return np.clip((1.0 - w.tone_of_slope(w.closed(h))) * m / BAKE_MAX, 0, 1)


def baked_open(h, m):
    """Same tone as baked_loss for a field that is already crease-free (the hollowed mesh field): no closing, so the
    valleys the mesh carries are in the three sprite views too and match the 3/4 views."""
    return np.clip((1.0 - w.tone_of_slope(h)) * m / BAKE_MAX, 0, 1)


def gray_uri(g):
    buf = io.BytesIO()
    Image.fromarray(np.clip(255 * g + 0.5, 0, 255).astype(np.uint8)).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


# Depths (px) of the notches, from ANATOMY-LAYERS.md sections 1, 3 and 5: the sternum is a bone floor (shallow dip between the
# pecs), the linea alba is a faint notch, the spine groove is shallow under the trapezius and deeper at the low back, the
# intergluteal cleft is the deep and narrow notch. Fat fills the notches. No numbers in the sources: set by eye.
HOLLOW = float(os.environ.get("HOLLOW", 10.0))        # px, blur of the artist's strokes (seams between volumes)
CHEST = float(os.environ.get("CHEST", 14.0))          # sternal dip between the pecs / breasts
ABS = float(os.environ.get("ABS", 5.0))               # linea alba
SPINE = float(os.environ.get("SPINE", 8.0))           # spine groove, low back
CLEFT = float(os.environ.get("CLEFT", 10.0))          # intergluteal cleft
CURL = float(os.environ.get("CURL", 8.0))            # lower edge of the lobes curls under (gluteal fold)
FAT_FILL = {"Fat": 0.6, "Fat_Female": 0.6}            # fraction of the notch depth left on bodies whose fat fills the notches
HOLLOW_SIGMA = float(os.environ.get("HOLLOW_SIGMA", 9.0))


def ramp(t, a, b):
    return np.clip((t - a) / max(b - a, 1e-6), 0, 1)


def notch_profile(t, back, chest=CHEST):
    """Depth (px) and half-width (fraction of the row width) of the median notch at height t (0 top .. 1 bottom of the sprite)."""
    if not back:
        e = ramp(t, 0.10, 0.18) * (1 - ramp(t, 0.38, 0.46))
        a = ramp(t, 0.38, 0.46) * (1 - ramp(t, 0.74, 0.82))
        return chest * e + ABS * a, 0.06 * e + 0.03 * a + 0.03 * (1 - e - a)
    sp = ramp(t, 0.20, 0.55) * (1 - ramp(t, 0.64, 0.70))
    cl = ramp(t, 0.82, 0.93)
    return SPINE * sp + CLEFT * cl, 0.04 * sp + 0.022 * cl + 0.04 * (1 - sp - cl)


def curve_between(points, left, right, middle_y, fallback):
    """A softly curved screen-space fold line between two named WDI points."""
    a, b = points.get(left), points.get(right)
    if a is None or b is None:
        return np.full(N, fallback, float), (0.5 * N, 0.45 * N)
    mid = 0.5 * (a[0] + b[0])
    x = np.array((a[0], mid, b[0]), float); y = np.array((a[1], middle_y, b[1]), float)
    order = np.argsort(x)
    curve = np.interp(np.arange(N), x[order], y[order], left=fallback, right=fallback)
    return ndi.gaussian_filter1d(curve, 2.0), (mid, 0.5 * abs(b[0] - a[0]))


def skin_folds(h, m, body, points, back=False):
    """Fat only: a roll above a crease, never a line engraved into a smooth balloon."""
    if not body.startswith("Fat"):
        return h
    ys, xs = np.nonzero(m); y0, y1 = int(ys.min()), int(ys.max())
    yy, xx = np.mgrid[0:N, 0:N]

    def add_fold(out, curve, center, halfspan, roll, trough):
        d = yy - curve[None, :]
        lateral = np.clip(1.0 - ((xx - center) / max(halfspan, 8.0)) ** 6, 0.0, 1.0)
        # A wide forward roll followed by a shorter trough: the pair alters the
        # surface normal under oblique lighting, unlike a dark line stamped into it.
        ridge = roll * np.exp(-0.5 * ((d + 9.0) / 10.0) ** 2)
        valley = trough * np.exp(-0.5 * (d / 4.8) ** 2)
        return out + (ridge - valley) * lateral * m

    if not back:
        # The fat chest folds over the upper abdomen.  The points are shared with the
        # pectoral curve when WDI drew them; a smooth fallback keeps other Fat variants valid.
        curve, (center, span) = curve_between(points, "under-breast fold L", "under-breast fold R",
                                               y0 + 0.53 * (y1 - y0), y0 + 0.45 * (y1 - y0))
        h = add_fold(h, curve, center, span + 28.0, 13.0, 5.5)
        navel, sex = points.get("navel"), points.get("sex")
        if navel is not None and sex is not None:
            belly = np.full(N, 0.52 * (navel[1] + sex[1]))
            h = add_fold(h, belly, 0.5 * (navel[0] + sex[0]), 0.42 * (m.any(axis=0).sum()), 8.0, 3.5)
    else:
        hip, crotch = points.get("hip L"), points.get("crotch point")
        if hip is not None and crotch is not None:
            glute = np.full(N, hip[1] + 0.55 * (crotch[1] - hip[1]))
            h = add_fold(h, glute, crotch[0], 0.45 * m.any(axis=0).sum(), 11.0, 4.8)
    return np.maximum(h, 0.0) * m


def male_front_landmarks(h, m, points):
    """Carry the male front's named junctions as restrained surface relief.

    These are not texture lines: the inter-pectoral seam, xiphoid/linea alba,
    inguinal folds and external genital silhouette are finite height fields.
    Their locations come only from the WDI landmarks and they stay small enough
    for an Average body rather than reading as an ecorche.
    """
    apex_l, apex_r = points.get("breast apex L"), points.get("breast apex R")
    fold_l, fold_r = points.get("under-breast fold L"), points.get("under-breast fold R")
    navel, sex, crotch = points.get("navel"), points.get("sex"), points.get("crotch point")
    if not all((apex_l, apex_r, fold_l, fold_r, navel, sex, crotch)):
        return h
    yy, xx = np.mgrid[0:N, 0:N]
    midx = 0.5 * (apex_l[0] + apex_r[0])

    def gauss(cx, cy, sx, sy, amp):
        return amp * np.exp(-0.5 * (((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2))

    def segment(a, b, radius, amp):
        ax, ay = a; bx, by = b
        dx, dy = bx - ax, by - ay
        t = np.clip(((xx - ax) * dx + (yy - ay) * dy) / max(dx * dx + dy * dy, 1e-6), 0.0, 1.0)
        px, py = ax + t * dx, ay + t * dy
        return amp * np.exp(-0.5 * (((xx - px) ** 2 + (yy - py) ** 2) / radius ** 2))

    fold_y = 0.5 * (fold_l[1] + fold_r[1])
    # A narrow sternal seam ends in a soft xiphoid point, then becomes the
    # shallower linea alba.  It never broadens into the former spoon hollow.
    h -= segment((midx, min(apex_l[1], apex_r[1]) - 4.0), (midx, fold_y + 5.0), 4.5, 4.2)
    # The little downward point where the lower pecs meet is broad enough to
    # survive atlas-scale resampling as a surface transition, not drawn ink.
    h -= gauss(midx, fold_y + 5.0, 8.5, 7.5, 4.1)
    # The lower point returns briefly into the abdominal plane; it is not a
    # trench from the chest all the way to the navel.
    h -= segment((midx, fold_y + 6.0), (midx, min(fold_y + 24.0, navel[1] - 8.0)), 3.2, 1.25)

    # The visible under-pec boundary is a shallow curved skin fold.  It rises
    # into both axillae instead of cutting the torso with a horizontal bar.
    fold_curve, (fold_mid, fold_half) = curve_between(
        points, "under-breast fold L", "under-breast fold R", fold_y + 4.0, fold_y)
    d_fold = yy - fold_curve[None, :]
    fold_span = np.clip(1.0 - ((xx - fold_mid) / max(fold_half + 17.0, 8.0)) ** 8, 0.0, 1.0)
    h -= 3.0 * np.exp(-0.5 * (d_fold / 3.8) ** 2) * fold_span

    # The pubic mound, shaft and paired scrotal volume match the low-detail
    # WDI male reference.  Two finite inguinal folds and the medial cleft keep
    # the upper-thigh crop structurally legible without detached thigh tubes.
    groin_l, groin_r = points.get("groin crease L"), points.get("groin crease R")
    h += gauss(midx, sex[1] - 13.0, 20.0, 12.0, 3.2)
    h += gauss(midx, sex[1] - 1.0, 4.6, 10.0, 4.0)
    h += gauss(midx - 6.0, sex[1] + 6.0, 7.0, 7.5, 3.1)
    h += gauss(midx + 6.0, sex[1] + 6.0, 7.0, 7.5, 3.1)
    for groin in (groin_l, groin_r):
        if groin is not None:
            h -= segment(groin, sex, 5.0, 3.4)
    h -= segment(sex, crotch, 4.2, 4.5)
    h -= gauss(midx, crotch[1] + 2.0, 5.0, 9.0, 3.4)
    return np.maximum(h, 0.0) * m


def male_front_muscle_bubbles(h, m, points):
    """Last surface pass: low rounded muscles, masked away from the named folds.

    This is an operational ordering, not an anatomical claim that muscle lies over
    skin.  It prevents smoothing, profile fitting and crease construction from
    erasing the few intentional Average-Male muscle volumes.
    """
    apex_l, apex_r = points.get("breast apex L"), points.get("breast apex R")
    fold_l, fold_r = points.get("under-breast fold L"), points.get("under-breast fold R")
    navel, sex = points.get("navel"), points.get("sex")
    if not all((apex_l, apex_r, fold_l, fold_r, navel, sex)):
        return h
    yy, xx = np.mgrid[0:N, 0:N]
    midx = 0.5 * (apex_l[0] + apex_r[0])
    fold_y = 0.5 * (fold_l[1] + fold_r[1])

    # The WDI's faint upper stroke runs from each armpit to the cleavage;
    # its strong lower stroke is the under-pectoral fold.  Make the pectoral
    # a shallow *ramp between those two drawn boundaries*, not an oval stamp.
    # It rises towards the lower stroke, then fades directly beneath it.
    bubble = np.zeros_like(h)
    lower_curve, _ = curve_between(points, "under-breast fold L", "under-breast fold R", fold_y + 4.0, fold_y)
    for armpit, apex, sign in ((points.get("armpit L"), apex_l, -1.0),
                                (points.get("armpit R"), apex_r, 1.0)):
        if armpit is None:
            continue
        if sign < 0:
            upper = np.interp(np.arange(N), (armpit[0], apex[0], midx),
                              (armpit[1], apex[1], 0.5 * (apex_l[1] + apex_r[1])))
            footprint = w.smooth01((xx - armpit[0]) / 9.0) * w.smooth01((midx - xx) / 11.0)
        else:
            upper = np.interp(np.arange(N), (midx, apex[0], armpit[0]),
                              (0.5 * (apex_l[1] + apex_r[1]), apex[1], armpit[1]))
            footprint = w.smooth01((xx - midx) / 11.0) * w.smooth01((armpit[0] - xx) / 9.0)
        depth = np.maximum(lower_curve - upper, 7.0)
        rise = w.smooth01((yy - upper[None, :]) / depth[None, :])
        fall = 1.0 - w.smooth01((yy - lower_curve[None, :]) / 8.0)
        bubble += 17.0 * rise * fall * footprint

    # Very restrained lower rectus supports: no six-pack subdivision.
    cy, rectus = 0.55 * navel[1] + 0.45 * sex[1], np.zeros_like(h)
    for cx in (midx - 19.0, midx + 19.0):
        rectus += 3.8 * np.exp(-0.5 * (((xx - cx) / 15.0) ** 2 + ((yy - cy) / 18.0) ** 2))
    rectus *= 1.0 - 0.80 * np.exp(-0.5 * ((xx - midx) / 5.5) ** 2)
    return np.maximum(h + bubble + rectus, 0.0) * m


def male_front_flat_planes(h, m, points):
    """Quiet the green WDI planes without flattening the yellow pec masses.

    The upper thorax is a supported cage plane.  It keeps its broad silhouette
    but loses small muscle-like undulations before the lower pectoral pair is
    added back by ``male_front_landmarks``.
    """
    apex_l, apex_r = points.get("breast apex L"), points.get("breast apex R")
    neck_l, neck_r = points.get("neck base L"), points.get("neck base R")
    if not all((apex_l, apex_r, neck_l, neck_r)):
        return h
    yy, xx = np.mgrid[0:N, 0:N]
    midx = 0.5 * (apex_l[0] + apex_r[0])
    y0 = 0.5 * (neck_l[1] + neck_r[1]) + 16.0
    y1 = min(apex_l[1], apex_r[1]) - 10.0
    if y1 <= y0 + 8.0:
        return h
    vertical = np.clip((yy - y0) / 10.0, 0.0, 1.0) * np.clip((y1 - yy) / 10.0, 0.0, 1.0)
    half = 0.55 * abs(apex_r[0] - apex_l[0]) + 30.0
    lateral = np.clip(1.0 - ((xx - midx) / half) ** 6, 0.0, 1.0)
    support = m.astype(float)
    smooth = ndi.gaussian_filter(h * support, (5.0, 14.0)) / np.maximum(ndi.gaussian_filter(support, (5.0, 14.0)), 1e-6)
    flat = 0.72 * vertical * lateral * m
    return (h * (1.0 - flat) + smooth * flat) * m


def hollowed(h, img, m, width, body, points, back=False, fill=1.0, chest=CHEST):
    """Crease-free volume with soft hollows: the blur of the artist's strokes plus the median notch of the torso.

    The three sprite views keep the baked tone; the 3/4 views get the valleys.  All depths are scaled by local height so
    they die at the silhouette.
    """
    L = w.wdi_lines(img, m, width)
    b = ndi.gaussian_filter(L, HOLLOW_SIGMA)
    b = np.clip(b / max(float(np.percentile(b[m > 0], 99)), 1e-6), 0, 1)
    hc = w.closed(h)
    rel = np.clip(hc / max(float(hc.max()), 1e-6) * 2.0, 0, 1)
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    notch = np.zeros((N, N))
    cols = np.arange(N)
    for y in range(y0, y1 + 1):
        r = np.nonzero(m[y])[0]
        if len(r) < 8:
            continue
        depth, sig = notch_profile((y - y0) / max(y1 - y0, 1), back, chest)
        notch[y] = fill * depth * np.exp(-0.5 * ((cols - 0.5 * (r[0] + r[-1])) / max(sig * (r[-1] - r[0]), 2.0)) ** 2)
    yy = np.mgrid[0:N, 0:N][0]
    t = (yy - y0) / max(y1 - y0, 1)
    curl = fill * CURL * ramp(t, 0.92, 1.0) ** 2 if back else 0.0
    # WDI line ink is useful for a lean crease.  On Fat, most of the same marks are
    # skin folds, so retain only a quarter of the engraving then give them a roll above it.
    # Male Average uses the WDI illustration as albedo, not a literal map of
    # engraved anatomy.  Its persistent creases are added from named landmarks
    # immediately after this pass; the remaining ink must not turn into bands.
    line_depth = HOLLOW * (0.12 if body == "Male" else (0.25 if body.startswith("Fat") else 1.0))
    base = np.maximum(hc - line_depth * b * rel - (notch + curl) * rel, 0.0) * m
    out = skin_folds(base, m, body, points, back)
    if body == "Male" and not back:
        structured = male_front_landmarks(male_front_flat_planes(out, m, points), m, points)
        return male_front_muscle_bubbles(structured, m, points)
    return out


def nipple_marks(mesh, img, mask):
    """Areola centres carried onto the front surface as actual 3D anchors, not texture-only pixels."""
    rows = np.asarray(mesh["rows"], float).reshape(len(mesh["rows"]), 2 * rx.U, 3)
    front = rows[:, :rx.U]
    cx = float(mesh["frame"]["cxs"])
    out = []
    for x, y, radius, _colour in w.areolae(img, mask):
        i = int(np.argmin(np.abs(-front[:, 0, 1] - y)))
        j = int(np.argmin(np.abs(front[i, :, 0] - (x - cx))))
        q = front[i, j]
        out.append({"kind": "nipple", "source": [round(x, 2), round(y, 2)],
                    "world": [round(float(v), 2) for v in q], "radius": round(radius, 2)})
    return out


def one(body):
    z = np.load(HERE / "out" / f"wdi3d-{body}.npz")
    imgs, M, P = w.load(body)
    zf = {f: z[f] for f in ("south", "north", "east")}
    wd = {f: w.outline_width(imgs[f], M[f]) for f in imgs}
    # Male already has the one shallow sternum transition in its fitted field.  Adding
    # CHEST again made the 3/4 carrier look scooped between otherwise plausible pecs.
    chest = 0.0 if body in ("Male", "Fat") else CHEST
    fields = {"south": hollowed(zf["south"], imgs["south"], M["south"], wd["south"], body, P["south"], fill=FAT_FILL.get(body, 1.0), chest=chest), "north": hollowed(zf["north"], imgs["north"], M["north"], wd["north"], body, P["north"], back=True, fill=FAT_FILL.get(body, 1.0), chest=chest), "zc": z["zc"]}
    e = rx.one(body, fields)
    e["marks"] = nipple_marks(e, imgs["south"], M["south"])
    e["tex"] = {f[0]: data_uri(ink_map(z[f], imgs[f], M[f])) for f in ("south", "north", "east")}
    e["wdi"] = {f[0]: rgba_uri(imgs[f], M[f]) for f in ("south", "north", "east")}
    e["bake"] = {"s": gray_uri(baked_open(fields["south"], M["south"])), "n": gray_uri(baked_open(fields["north"], M["north"])), "e": gray_uri(baked_loss(zf["east"], M["east"]))}
    e["gate"] = {f[0]: gray_uri(grey_gate(imgs[f], M[f])) for f in ("south", "north", "east")}
    e["outline"] = round(float(np.mean([w.outline_width(imgs[f], M[f]) for f in imgs])), 1)
    return e


def main():
    names = [a for a in sys.argv[1:] if a in w.BODIES] or w.BODIES
    out = {}
    for b in names:
        out[b] = one(b)
        print(b, "legs", None if out[b]["legs"] is None else len(out[b]["legs"]["L"]), "frame", out[b]["frame"], flush=True)
    (HERE / "out" / "wdi3d-mesh.json").write_text(json.dumps({"R": rx.R, "U": rx.U, "bodies": out}, separators=(",", ":")), encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
