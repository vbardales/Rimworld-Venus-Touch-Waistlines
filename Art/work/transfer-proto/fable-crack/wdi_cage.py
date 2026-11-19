"""A controllable exterior cage for WDI Male.

This is deliberately not an anatomical stack.  The WDI south, east and north silhouettes
are the truth; their extents are sampled at semantic torso sections, then joined by smooth,
asymmetric rings.  The result is a single surface intended to become the garment atlas
carrier.  Bones, muscles and fat may later sit *inside* it and add only local relief.

The board overlays the three source outlines in red.  It also includes the useful camera
for garment checking: south/front, 30 degrees from above.  No garment is warped here.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python wdi_cage.py
Board: Art/work/captures/2026-11-18_wdi-m-cage.png
"""
from __future__ import annotations

import pathlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.interpolate import PchipInterpolator

import wdi3d


HERE = pathlib.Path(__file__).parent
CAPT = HERE.parents[1] / "captures"
N = 512
SIZE = 320
RINGS = 120
AROUND = 96

# Readable, adjustable torso stations.  The interpolation is monotonic between stations:
# unlike a blurred stack it cannot create an accidental spherical belly or erase the waist.
SECTIONS = (
    ("neck", 0.00), ("girdle", 0.12), ("shoulders", 0.26), ("armpits", 0.43),
    ("under_pec", 0.53), ("waist", 0.63), ("navel", 0.70), ("iliac", 0.76),
    ("pelvis", 0.85), ("gluteal", 0.93), ("thigh crop", 1.00),
)


def extents(mask: np.ndarray):
    """Left/right outline and occupied vertical range, with no texture/shading involved."""
    lo = np.full(N, np.nan); hi = np.full(N, np.nan)
    for y in np.flatnonzero(mask.any(axis=1)):
        x = np.flatnonzero(mask[y]); lo[y], hi[y] = x[0], x[-1]
    ys = np.flatnonzero(mask.any(axis=1))
    return lo, hi, int(ys[0]), int(ys[-1])


def sample(lo, hi, y0, y1, t):
    y = y0 + np.asarray(t) * (y1 - y0)
    rows = np.arange(N)
    left = np.interp(y, rows, np.nan_to_num(lo, nan=np.nanmedian(lo[y0:y1 + 1])))
    right = np.interp(y, rows, np.nan_to_num(hi, nan=np.nanmedian(hi[y0:y1 + 1])))
    return 0.5 * (right - left), 0.5 * (right + left)


class Cage:
    """Asymmetric super-elliptic rings, sampled from the three WDI projections."""

    def __init__(self, body="Male"):
        self.body = body
        self.images, masks, _points = wdi3d.load(body)
        self.masks = masks
        self.bounds = {f: extents(m) for f, m in masks.items()}
        tc = np.array([t for _, t in SECTIONS])
        sf, cf = sample(*self.bounds["south"], tc)
        sn, cn = sample(*self.bounds["north"], tc)
        # East x grows from back to front.  Keep both separately: this is what stops a
        # profile from becoming the symmetric "blob" made by the old smooth envelope.
        de, ce = sample(*self.bounds["east"], tc)
        front = (ce + de) - ce
        back = ce - (ce - de)
        # The front/north silhouettes are nearly equal in width.  Their mean makes one
        # continuous flank rather than placing two incompatible outlines on opposite sides.
        width = 0.5 * (sf + sn)
        # Explicit anatomical edits, in source-pixel units, stay very small.  The source
        # profile supplies chest/belly/buttock projection; stations supply continuity.
        self.controls = dict(t=tc, width=width, front=front, back=back, centre=ce,
                             south_width=sf, north_width=sn, south_centre=cf, north_centre=cn)
        self.height = float(np.mean([b[3] - b[2] for b in self.bounds.values()]))

    def rings(self, count=RINGS, around=AROUND):
        t = np.linspace(0, 1, count)
        c = self.controls
        interp = lambda a: PchipInterpolator(c["t"], a)(t)
        w, front, back, zc = map(interp, (c["width"], c["front"], c["back"], c["centre"]))
        # A broad squircle rather than an ellipse preserves the WDI torso's flat-ish
        # flanks and avoids the pinched teardrop read from a circular tube.
        a = np.linspace(0, 2 * np.pi, around, endpoint=False)
        sine, cosine = np.sin(a)[None, :], np.cos(a)[None, :]
        x = w[:, None] * np.sign(sine) * np.abs(sine) ** 0.55
        z = zc[:, None] + np.maximum(cosine, 0) ** 0.75 * front[:, None] - np.maximum(-cosine, 0) ** 0.75 * back[:, None]
        y = -self.height * t[:, None] * np.ones_like(x)
        return np.stack([x, y, z], -1)


def project(rings, yaw, pitch, target=None, fit=None):
    """Orthographic camera.  Negative pitch is a camera above the front looking down."""
    x, y, z = rings[..., 0], rings[..., 1], rings[..., 2]
    ref = rings if fit is None else fit
    rx, ry, rz = ref[..., 0], ref[..., 1], ref[..., 2]
    a, b = np.radians(yaw), np.radians(pitch)
    sx, dep = x * np.cos(a) + z * np.sin(a), -x * np.sin(a) + z * np.cos(a)
    sy, depth = y * np.cos(b) - dep * np.sin(b), y * np.sin(b) + dep * np.cos(b)
    rsx, rdep = rx * np.cos(a) + rz * np.sin(a), -rx * np.sin(a) + rz * np.cos(a)
    rsy = ry * np.cos(b) - rdep * np.sin(b)
    if target is None:
        scale = 0.88 * min(SIZE / max(np.ptp(rsx), 1), SIZE / max(np.ptp(rsy), 1))
        px = (sx - 0.5 * (rsx.min() + rsx.max())) * scale + 0.5 * SIZE
        # World Y grows toward the head while pixel Y grows toward the feet.
        # Keep the free-camera diagnostics upright, like the target-fit branch below.
        py = (0.5 * (rsy.min() + rsy.max()) - sy) * scale + 0.5 * SIZE
        return np.stack([px, py, depth], -1), None
    lo, hi, y0, y1 = extents(target)
    target_w = float(np.nanmax(hi - lo)); mid = 0.5 * (np.nanmin(lo) + np.nanmax(hi))
    px = (sx - 0.5 * (rsx.min() + rsx.max())) * target_w / max(np.ptp(rsx), 1e-6) + mid
    # Keep the source's vertical placement; this lets the outline error expose wrong stations.
    # Both the new cage (top at 0) and the historical mesh (all world y negative)
    # are valid inputs; normalise between their actual top and bottom rather than
    # assuming the former coordinate convention.
    py = y0 + (y - rsy.max()) / min(rsy.min() - rsy.max(), -1e-6) * (y1 - y0)
    return np.stack([px, py, depth], -1), (lo, hi, y0, y1)


def project_marks(marks, rings, yaw, pitch, target):
    """Project 3D surface anchors by the same camera/fit as their carrier, for review only."""
    if not marks:
        return np.empty((0, 2))
    pieces = rings if isinstance(rings, (tuple, list)) else (rings,)
    fit = np.concatenate(pieces, axis=0)
    points = np.asarray([m["world"] for m in marks], float)
    a, b = np.radians(yaw), np.radians(pitch)
    sx = points[:, 0] * np.cos(a) + points[:, 2] * np.sin(a)
    dep = -points[:, 0] * np.sin(a) + points[:, 2] * np.cos(a)
    sy = points[:, 1] * np.cos(b) - dep * np.sin(b)
    rx = fit[..., 0] * np.cos(a) + fit[..., 2] * np.sin(a)
    ry = fit[..., 1] * np.cos(b) - (-fit[..., 0] * np.sin(a) + fit[..., 2] * np.cos(a)) * np.sin(b)
    lo, hi, y0, y1 = extents(target)
    width, mid = float(np.nanmax(hi - lo)), 0.5 * (np.nanmin(lo) + np.nanmax(hi))
    px = (sx - 0.5 * (rx.min() + rx.max())) * width / max(np.ptp(rx), 1e-6) + mid
    py = y0 + (sy - ry.max()) / min(ry.min() - ry.max(), -1e-6) * (y1 - y0)
    return np.stack([px, py], -1)


def triangles(rows):
    nr, na, _ = rows.shape
    for i in range(nr - 1):
        for j in range(na):
            k = (j + 1) % na
            yield (i, j), (i + 1, j), (i, k)
            yield (i, k), (i + 1, j), (i + 1, k)


def raster(rings, yaw, pitch, target=None, smooth=False, light_yaw=None, light_pitch=None):
    """Fill only the nearest triangle, so a later garment map can use the same visibility rule."""
    pieces = rings if isinstance(rings, (tuple, list)) else (rings,)
    fit = np.concatenate(pieces, axis=0)
    bounds = project(pieces[0], yaw, pitch, target, fit)[1]
    side = N if target is not None else SIZE
    zbuf = np.full((side, side), -np.inf)
    rgb = np.full((side, side, 3), 244, np.uint8)
    # The camera direction, in world coordinates.  Lighting each visible facet from this
    # direction makes chest, waist and gluteal planes readable without inventing texture.
    a_cam, b_cam = np.radians(yaw), np.radians(pitch)
    light_a = np.radians(yaw if light_yaw is None else light_yaw)
    light_b = np.radians(pitch if light_pitch is None else light_pitch)
    light = np.array((-np.sin(light_a) * np.cos(light_b), np.sin(light_b), np.cos(light_a) * np.cos(light_b)))
    zmid = float(np.median(fit[..., 2]))
    vertex_shades = []
    if smooth:
        # A zenithal check needs the carrier's continuous curvature, not the
        # per-triangle normal bands used by the technical silhouette panels.
        for piece in pieces:
            along = np.gradient(piece, axis=0)
            around = 0.5 * (np.roll(piece, -1, axis=1) - np.roll(piece, 1, axis=1))
            normals = np.cross(along, around)
            normals /= np.maximum(np.linalg.norm(normals, axis=2, keepdims=True), 1e-8)
            radial = piece - np.stack((np.zeros_like(piece[..., 0]),
                                       np.mean(piece[..., 1], axis=1, keepdims=True) + np.zeros_like(piece[..., 1]),
                                       np.full_like(piece[..., 2], zmid)), axis=2)
            normals[np.sum(normals * radial, axis=2) < 0] *= -1
            vertex_shades.append(np.clip(152 + 88 * np.maximum(normals @ light, 0.0), 152, 240))
    for piece_index, piece in enumerate(pieces):
      p, _ = project(piece, yaw, pitch, target, fit)
      for tri in triangles(p):
        ii = np.asarray([v[0] for v in tri]); jj = np.asarray([v[1] for v in tri])
        q = p[ii, jj]
        x, y = q[:, 0], q[:, 1]
        x0, x1 = max(int(np.floor(x.min())), 0), min(int(np.ceil(x.max())), side - 1)
        y0, y1 = max(int(np.floor(y.min())), 0), min(int(np.ceil(y.max())), side - 1)
        den = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
        if x1 < x0 or y1 < y0 or abs(den) < 1e-9:
            continue
        xx, yy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a = ((y[1] - y[2]) * (xx - x[2]) + (x[2] - x[1]) * (yy - y[2])) / den
        b = ((y[2] - y[0]) * (xx - x[2]) + (x[0] - x[2]) * (yy - y[2])) / den
        inside = (a >= 0) & (b >= 0) & (1 - a - b >= 0)
        depth = a * q[0, 2] + b * q[1, 2] + (1 - a - b) * q[2, 2]
        cell = zbuf[y0:y1 + 1, x0:x1 + 1]; take = inside & (depth > cell)
        if not take.any():
            continue
        cell[take] = depth[take]
        # A deliberately quiet light: form is visible without pretending this is WDI's painted texture.
        if smooth:
            values = vertex_shades[piece_index][ii, jj]
            shade = a * values[0] + b * values[1] + (1 - a - b) * values[2]
            shade = np.uint8(np.clip(shade, 0, 255))
        else:
            q3 = piece[ii, jj]
            normal = np.cross(q3[1] - q3[0], q3[2] - q3[0]); normal /= max(np.linalg.norm(normal), 1e-8)
            radial = q3.mean(axis=0) - np.array((0.0, q3[:, 1].mean(), zmid))
            if normal @ radial < 0:
                normal = -normal
            shade = int(np.clip(138 + 102 * max(float(normal @ light), 0.0), 138, 240))
        tile = rgb[y0:y1 + 1, x0:x1 + 1]
        if smooth:
            tile[take] = np.repeat(shade[take, None], 3, axis=1)
        else:
            tile[take] = (shade, shade, shade)
    return Image.fromarray(rgb), zbuf > -np.inf, bounds


def outline(mask):
    return mask & ~ndi.binary_erosion(mask)


def score(solid, target):
    """Symmetric contour distance in source pixels; 0 would be an exact silhouette."""
    a, b = outline(solid), outline(target)
    da, db = ndi.distance_transform_edt(~a), ndi.distance_transform_edt(~b)
    d = np.r_[da[b], db[a]]
    return float(np.percentile(d, 95)) if d.size else float("inf")


def panel(cage, rings, label, yaw, pitch, target=None, marks=()):
    image, solid, _bounds = raster(rings, yaw, pitch, target)
    if target is not None:
        red = outline(target)
        a = np.asarray(image).copy(); a[red] = (188, 45, 40)
        image = Image.fromarray(a)
        err = score(solid, target)
        sub = f"silhouette p95 {err:.1f} px; contour WDI rouge"
        if marks:
            draw = ImageDraw.Draw(image)
            for x, y in project_marks(marks, rings, yaw, pitch, target):
                draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(178, 55, 135), outline=(255, 235, 245), width=1)
    else:
        sub = "visibilite z-buffer, sans contour source"
    # Reduce source-sized comparison panels to the diagnostic tile size.
    image.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    return label, sub, image


def ring_test_board():
    """Rejected control: silhouette-only rings, retained so the failure mode stays reproducible."""
    cage = Cage(); rings = cage.rings()
    tiles = [
        panel(cage, rings, "sud", 0, 0, cage.masks["south"]),
        panel(cage, rings, "est", 90, 0, cage.masks["east"]),
        panel(cage, rings, "nord", 180, 0, cage.masks["north"]),
        panel(cage, rings, "sud, 30 deg vu d'en haut", 0, -30),
    ]
    font = ImageFont.load_default(size=14)
    out = Image.new("RGB", (2 * SIZE + 30, 2 * SIZE + 82), (235, 235, 230)); dr = ImageDraw.Draw(out)
    dr.text((8, 7), "WDI-M : cage externe a sections. Rouge = contour source; gris = surface, pas muscles.", fill=(0, 0, 0), font=font)
    dr.text((8, 23), "Stations : " + " / ".join(n for n, _ in SECTIONS), fill=(0, 0, 0), font=font)
    for i, (label, sub, im) in enumerate(tiles):
        x, y = 8 + (i % 2) * (SIZE + 8), 43 + (i // 2) * (SIZE + 18)
        dr.text((x, y), label, fill=(0, 0, 0), font=font)
        dr.text((x, y + 14), sub, fill=(0, 0, 0), font=ImageFont.load_default(size=11))
        out.paste(im, (x, y + 30))
    CAPT.mkdir(exist_ok=True)
    path = CAPT / "2026-11-18_wdi-m-ring-test.png"; out.save(path)
    print(path)
    return path


def mesh_parts(data):
    """Trunk plus proximal-thigh strips; all share the same source registration."""
    rows = np.asarray(data["rows"], float).reshape(len(data["rows"]), -1, 3)[::4]
    parts = [rows]
    if data.get("legs"):
        for side in ("L", "R"):
            leg = np.asarray(data["legs"][side], float).reshape(len(data["legs"][side]), -1, 3)
            parts.append(leg[::2])
    return parts


def structural_cage_board(body="Male"):
    """The chosen WDI-M carrier: the existing source-fitted mass mesh through one z-buffer."""
    cage = Cage(body)
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    data = raw["bodies"][body]
    parts = mesh_parts(data)
    marks = data.get("marks", [])
    # This diagnostic rasteriser is intentionally simple; 90 rings retain all large masses while keeping the proof fast.
    tiles = [
        panel(cage, parts, "sud", 0, 0, cage.masks["south"], marks),
        panel(cage, parts, "est", 90, 0, cage.masks["east"]),
        panel(cage, parts, "nord", 180, 0, cage.masks["north"]),
        panel(cage, parts, "sud, 30 deg vu d'en haut", 0, -30),
    ]
    font = ImageFont.load_default(size=14)
    out = Image.new("RGB", (2 * SIZE + 30, 2 * SIZE + 82), (235, 235, 230)); dr = ImageDraw.Draw(out)
    dr.text((8, 7), f"WDI-{body} : cage structurale a masses. Rouge = contour source ; gris = surface porteuse.", fill=(0, 0, 0), font=font)
    dr.text((8, 23), "Cage thoracique, taille, bassin et fesses restent des volumes distincts avant tout atlas.", fill=(0, 0, 0), font=font)
    for i, (label, sub, im) in enumerate(tiles):
        x, y = 8 + (i % 2) * (SIZE + 8), 43 + (i // 2) * (SIZE + 18)
        dr.text((x, y), label, fill=(0, 0, 0), font=font)
        dr.text((x, y + 14), sub, fill=(0, 0, 0), font=ImageFont.load_default(size=11))
        out.paste(im, (x, y + 30))
    path = CAPT / f"2026-11-18_wdi-{body.lower()}-cage.png"; out.save(path); print(path)
    return path


def front_light_board(body="Male"):
    """Front camera; key light 30 degrees forward from zenith."""
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    # World Y grows toward the head, so +90 degrees is directly overhead.
    # A light 30 degrees forward from zenith is therefore +60 degrees.
    image, _solid, _bounds = raster(mesh_parts(raw["bodies"][body]), 0, 0, smooth=True, light_pitch=60)
    font, small = ImageFont.load_default(size=14), ImageFont.load_default(size=11)
    out = Image.new("RGB", (SIZE + 16, SIZE + 48), (235, 235, 230))
    draw = ImageDraw.Draw(out)
    draw.text((8, 7), f"WDI-{body} : face, zenith 30 deg avant", fill=(0, 0, 0), font=font)
    draw.text((8, 23), "normales lissees ; lumiere seule", fill=(0, 0, 0), font=small)
    out.paste(image, (8, 40))
    path = CAPT / f"2026-11-18_wdi-{body.lower()}-front-light30.png"; out.save(path); print(path)
    return path


def front_plan_board(body="Male"):
    """WDI and the untextured carrier, side by side in the same front frame."""
    cage = Cage(body)
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    # A front-facing but raking key reveals the *existing* height field.  A
    # nearly zenithal key made a chest whose lobes differ by 25 source units
    # look flat, which turned this comparison into a false negative.
    carrier, _solid, _bounds = raster(mesh_parts(raw["bodies"][body]), 0, 0, cage.masks["south"],
                                      smooth=True, light_yaw=32, light_pitch=35)
    source = Image.fromarray(wdi3d.on_bg(cage.images["south"]))
    font, small = ImageFont.load_default(size=14), ImageFont.load_default(size=11)
    out = Image.new("RGB", (2 * N + 28, N + 52), (235, 235, 230))
    draw = ImageDraw.Draw(out)
    draw.text((8, 7), f"WDI-{body} : face orthographique, meme cadre", fill=(0, 0, 0), font=font)
    draw.text((8, 23), "gauche : sprite WDI ; droite : volumes sans texture, lumiere laterale", fill=(0, 0, 0), font=small)
    draw.text((8, 39), "WDI", fill=(0, 0, 0), font=small)
    draw.text((N + 20, 39), "surface", fill=(0, 0, 0), font=small)
    out.paste(source, (8, 52)); out.paste(carrier, (N + 20, 52))
    path = CAPT / f"2026-11-18_wdi-{body.lower()}-front-plan.png"; out.save(path); print(path)
    return path


def source_tile(cage, facing):
    """The actual WDI painting on its neutral background; work capture only, never a committed mod asset."""
    image = Image.fromarray(wdi3d.on_bg(cage.images[facing]))
    image.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
    return image


def comparison_board(body="Male"):
    """Review board: source and carrier stay adjacent, especially for the profile."""
    cage = Cage(body)
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    data = raw["bodies"][body]
    parts = mesh_parts(data)
    marks = data.get("marks", [])
    views = (("sud", "south", 0), ("est", "east", 90), ("nord", "north", 180))
    font, small = ImageFont.load_default(size=14), ImageFont.load_default(size=11)
    out = Image.new("RGB", (2 * SIZE + 30, 3 * (SIZE + 42) + 42), (235, 235, 230)); dr = ImageDraw.Draw(out)
    dr.text((8, 7), f"WDI-{body} : comparaison directe. Source WDI a gauche ; cage structurale a droite.", fill=(0, 0, 0), font=font)
    for i, (label, facing, yaw) in enumerate(views):
        y = 28 + i * (SIZE + 42)
        source = source_tile(cage, facing)
        _label, detail, carrier = panel(cage, parts, label, yaw, 0, cage.masks[facing], marks if facing == "south" else ())
        dr.text((8, y), f"{label}: WDI source", fill=(0, 0, 0), font=font)
        dr.text((SIZE + 18, y), f"{label}: cage", fill=(0, 0, 0), font=font)
        dr.text((SIZE + 18, y + 14), detail, fill=(0, 0, 0), font=small)
        out.paste(source, (8, y + 28)); out.paste(carrier, (SIZE + 18, y + 28))
    dr.text((SIZE + 18, out.height - 15), "points roses : centres de tetons ancres sur la surface", fill=(110, 40, 85), font=small)
    path = CAPT / f"2026-11-18_wdi-{body.lower()}-cage-vs-wdi.png"; out.save(path); print(path)
    return path


def delta4(image, mask, cage_rgb):
    """Four-class error map for the WDI paint that a smooth cage does not yet explain.

    It treats WDI ink and broad WDI shading separately: an omitted ink line does not
    automatically become an anatomical groove, while a missing broad shadow is evidence
    for checking the surface normal or its supporting mass.
    """
    width = wdi3d.outline_width(image, mask)
    lines = wdi3d.wdi_lines(image, mask, width)
    shade = wdi3d.wdi_shade(image, mask, width)
    grey = np.asarray(cage_rgb, float).mean(axis=2) / 255.0
    # Compare only local visible relief.  The headlight naturally darkens the whole
    # curved flank, but that is not an extra WDI feature; subtract a large local
    # baseline and discard the outer outline band before assigning delta colours.
    baseline = ndi.gaussian_filter(grey, 22.0)
    inner = ndi.distance_transform_edt(mask) > width + 2.0
    cage_feature = np.clip((baseline - grey) / 0.11, 0, 1) * inner
    source_feature = np.maximum(shade, 1.2 * lines)

    # neutral / extra cage relief / WDI broad shade missing / WDI ink missing
    out = np.full((*mask.shape, 3), (242, 242, 238), np.uint8)
    neutral = mask
    out[neutral] = (63, 66, 74)
    extra = neutral & (cage_feature > source_feature + 0.16)
    broad = neutral & ~extra & (shade > 0.12) & (cage_feature < 0.62 * shade)
    ink = neutral & ~extra & (lines > 0.14) & (cage_feature < 0.56 * lines)
    out[extra] = (0, 183, 204)       # cyan: relief that WDI did not paint
    out[broad] = (247, 181, 0)       # gold: WDI broad shadow still unexplained
    out[ink] = (224, 47, 126)         # magenta: WDI thin mark, not yet surface-supported
    return Image.fromarray(out), lines, shade


def overlay_wdi_on_cage(image, mask, cage_rgb):
    """Put only WDI's internal shade and ink over the rendered carrier."""
    width = wdi3d.outline_width(image, mask)
    shade = wdi3d.wdi_shade(image, mask, width)[..., None]
    lines = wdi3d.wdi_lines(image, mask, width)[..., None]
    base = np.asarray(cage_rgb, float) / 255.0
    over = base * (1.0 - 0.58 * shade) * (1.0 - 0.86 * lines)
    out = np.full_like(over, 244.0)
    out[mask] = over[mask]
    return Image.fromarray(np.uint8(np.clip(out * 255, 0, 255)))


def delta_board(body="Male"):
    """Source, WDI-on-cage, and deliberately saturated four-colour delta per view."""
    cage = Cage(body)
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    parts = mesh_parts(raw["bodies"][body])
    views = (("sud", "south", 0), ("est", "east", 90), ("nord", "north", 180))
    font, small = ImageFont.load_default(size=14), ImageFont.load_default(size=11)
    out = Image.new("RGB", (3 * SIZE + 40, 3 * (SIZE + 40) + 70), (235, 235, 230)); dr = ImageDraw.Draw(out)
    dr.text((8, 7), f"WDI-{body} : delta des traits et ombres sur la cage.", fill=(0, 0, 0), font=font)
    legend = (("cyan: relief en trop", (0, 183, 204)), ("or: ombre large WDI absente", (247, 181, 0)),
              ("magenta: trait WDI absent", (224, 47, 126)), ("graphite: neutre", (63, 66, 74)))
    for i, (text, colour) in enumerate(legend):
        x = 8 + i * 238; dr.rectangle((x, 24, x + 11, 35), fill=colour); dr.text((x + 16, 23), text, fill=(0, 0, 0), font=small)
    for i, (label, facing, yaw) in enumerate(views):
        y = 46 + i * (SIZE + 40)
        rendered, _solid, _bounds = raster(parts, yaw, 0, cage.masks[facing])
        source = source_tile(cage, facing)
        over = overlay_wdi_on_cage(cage.images[facing], cage.masks[facing], np.asarray(rendered))
        delta, _lines, _shade = delta4(cage.images[facing], cage.masks[facing], np.asarray(rendered))
        for column, (title, tile) in enumerate((("WDI", source), ("WDI sur cage", over), ("delta 4 couleurs", delta))):
            x = 8 + column * (SIZE + 8)
            dr.text((x, y), f"{label}: {title}", fill=(0, 0, 0), font=font)
            tile.thumbnail((SIZE, SIZE), Image.Resampling.LANCZOS)
            out.paste(tile, (x, y + 18))
    path = CAPT / f"2026-11-18_wdi-{body.lower()}-cage-delta4.png"; out.save(path); print(path)
    return path


def front_multiply_board(body="Male"):
    """Front-only audit: source ink multiplied over the actual lit carrier.

    This is deliberately a diagnostic, never a production texture.  It reveals
    whether a WDI shadow falls where the carrier already changes normal, and
    classifies the remaining marks instead of blindly engraving all of them.
    """
    cage = Cage(body)
    raw = json.loads((HERE / "out" / "wdi3d-mesh.json").read_text(encoding="utf-8"))
    rendered, _solid, _bounds = raster(mesh_parts(raw["bodies"][body]), 0, 0, cage.masks["south"],
                                        smooth=True, light_yaw=32, light_pitch=35)
    source = Image.fromarray(wdi3d.on_bg(cage.images["south"]))
    multiplied = overlay_wdi_on_cage(cage.images["south"], cage.masks["south"], np.asarray(rendered))
    delta, _lines, _shade = delta4(cage.images["south"], cage.masks["south"], np.asarray(rendered))
    font, small = ImageFont.load_default(size=14), ImageFont.load_default(size=11)
    out = Image.new("RGB", (2 * N + 28, 2 * N + 76), (235, 235, 230)); dr = ImageDraw.Draw(out)
    dr.text((8, 7), f"WDI-{body} : audit de l'encre sur le volume", fill=(0, 0, 0), font=font)
    dr.text((8, 23), "or = ombre large WDI sans volume ; magenta = trait WDI sans relief ; cyan = relief en trop", fill=(0, 0, 0), font=small)
    for x, y, title, image in ((8, 43, "WDI", source), (N + 20, 43, "volume nu", rendered),
                               (8, N + 62, "WDI x volume", multiplied), (N + 20, N + 62, "ecarts a examiner", delta)):
        dr.text((x, y), title, fill=(0, 0, 0), font=font); out.paste(image, (x, y + 17))
    path = CAPT / f"2026-11-19_wdi-{body.lower()}-front-multiply.png"; out.save(path); print(path)
    return path


if __name__ == "__main__":
    if "rings" in sys.argv[1:]:
        ring_test_board()
    elif "technical" in sys.argv[1:]:
        structural_cage_board("Fat" if "Fat" in sys.argv[1:] else "Male")
    elif "delta" in sys.argv[1:]:
        delta_board("Fat" if "Fat" in sys.argv[1:] else "Male")
    elif "light30" in sys.argv[1:]:
        front_light_board("Fat" if "Fat" in sys.argv[1:] else "Male")
    elif "plan" in sys.argv[1:]:
        front_plan_board("Fat" if "Fat" in sys.argv[1:] else "Male")
    elif "multiply" in sys.argv[1:]:
        front_multiply_board("Fat" if "Fat" in sys.argv[1:] else "Male")
    else:
        comparison_board("Fat" if "Fat" in sys.argv[1:] else "Male")
