"""Compare each exported body projection with its WDI source image.

The mesh itself is projected orthographically for south, north and east.  A
cyan source outline and a magenta mesh outline are written for every body/view
under ``out/body3d-compare``.  ``report.json`` is the machine-readable gate:
edge error is reported in source pixels after a harmless global translation
fit, so an incorrect silhouette cannot be hidden by changing viewer framing.

Run after ``relief_export2.py``:
    uv run --with numpy --with pillow --with scipy --with scikit-image python body3d_compare.py
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import crack as c1
import relief3d as r3
import shade3d  # noqa: F401 -- use the full alpha silhouette, including the source rim


BODIES = ("Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female")
VIEWS = ("south", "north", "east")
HERE = pathlib.Path(__file__).parent
DATA_PATH = HERE / "out" / "relief3d-shade5.json"
OUT_DIR = HERE / "out" / "body3d-compare"


def source_image(img):
    """Put the transparent source on a neutral opaque board."""
    alpha = img[..., 3:4]
    bg = np.full(img.shape[:2] + (3,), 226.0)
    rgb = np.clip(bg * (1 - alpha) + 255 * img[..., :3] * alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb, "RGB")


def row_extents(mask):
    """Return image-space left/right extent per source row, NaN outside it."""
    lo = np.full(mask.shape[0], np.nan)
    hi = np.full(mask.shape[0], np.nan)
    for y in np.where(mask.any(axis=1))[0]:
        xs = np.flatnonzero(mask[y])
        lo[y], hi[y] = xs[0], xs[-1]
    return lo, hi


def mesh_extents(vertices, view, source_mask):
    """Orthographically project mesh vertices to a left/right extent per row."""
    if view == "south":
        coordinate = vertices[..., 0]
    elif view == "north":
        # Camera north looks along +z, therefore its screen x is -world x.
        coordinate = -vertices[..., 0]
    else:
        coordinate = vertices[..., 2]
    # Each sprite has its own vertical framing.  Register only the top/bottom
    # span for this diagnostic projection; lateral shape is still measured in
    # native source pixels and cannot be hidden by this framing transform.
    raw_y = -vertices[..., 1]
    source_rows = np.flatnonzero(source_mask.any(axis=1))
    source_top, source_bottom = source_rows[0], source_rows[-1]
    mesh_top, mesh_bottom = raw_y.min(), raw_y.max()
    y = np.rint(source_top + (raw_y - mesh_top) / max(mesh_bottom - mesh_top, 1e-6) * (source_bottom - source_top)).astype(int)
    lo = np.full(c1.N, np.nan)
    hi = np.full(c1.N, np.nan)
    for yy in np.unique(y):
        if 0 <= yy < c1.N:
            values = coordinate[y == yy]
            lo[yy], hi[yy] = values.min(), values.max()
    known = np.flatnonzero(np.isfinite(lo))
    if len(known) < 2:
        raise ValueError("projected mesh has fewer than two sampled rows")
    start, stop = known[0], known[-1]
    rows = np.arange(start, stop + 1)
    lo[rows] = np.interp(rows, known, lo[known])
    hi[rows] = np.interp(rows, known, hi[known])
    return lo, hi


def compare(body, view, vertices, image):
    mask = r3.silhouette(image)
    src_lo, src_hi = row_extents(mask)
    mesh_lo, mesh_hi = mesh_extents(vertices, view, mask)
    valid = np.isfinite(src_lo) & np.isfinite(mesh_lo)
    if valid.sum() < 12:
        raise ValueError(f"{body}/{view}: too few comparable rows")

    # Translation is viewer framing, not body shape.  Fit it once per view.
    src_center = 0.5 * (src_lo[valid] + src_hi[valid])
    mesh_center = 0.5 * (mesh_lo[valid] + mesh_hi[valid])
    shift = float(np.median(src_center - mesh_center))
    mesh_lo += shift
    mesh_hi += shift
    left_error = mesh_lo[valid] - src_lo[valid]
    right_error = mesh_hi[valid] - src_hi[valid]
    errors = np.abs(np.concatenate((left_error, right_error)))

    board = source_image(image).convert("RGBA")
    rgba = np.asarray(board).copy()
    boundary = mask & ~ndi.binary_erosion(mask)
    rgba[boundary] = (0, 220, 255, 255)  # source
    board = Image.fromarray(rgba, "RGBA")
    draw = ImageDraw.Draw(board)
    rows = np.flatnonzero(valid)
    left = [(float(mesh_lo[y]), int(y)) for y in rows]
    right = [(float(mesh_hi[y]), int(y)) for y in rows]
    draw.line(left, fill=(255, 20, 180, 255), width=2)  # exported mesh
    draw.line(right, fill=(255, 20, 180, 255), width=2)
    return board, {
        "rows": int(valid.sum()),
        "translation_px": round(shift, 3),
        "edge_error_median_px": round(float(np.median(errors)), 3),
        "edge_error_p95_px": round(float(np.percentile(errors, 95)), 3),
        "edge_error_max_px": round(float(errors.max()), 3),
    }


def main():
    names = tuple(arg for arg in sys.argv[1:] if arg in BODIES) or BODIES
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    a = 2 * data["U"]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    report = {}
    for body in names:
        entry = data["bodies"][body]
        parts = [np.asarray(entry["rows"], dtype=float).reshape(-1, a, 3)]
        # The lower cut is exported as two separate leg-root strips.  They are
        # part of the visible silhouette and must participate in the framing
        # and edge comparison, otherwise every view is falsely stretched.
        if entry.get("legs"):
            parts.extend(
                np.asarray(entry["legs"][side], dtype=float).reshape(-1, a, 3)
                for side in ("L", "R")
            )
        rows = np.concatenate(parts, axis=0)
        images = r3.views(body, False)
        report[body] = {}
        for view in VIEWS:
            board, stats = compare(body, view, rows, images[view])
            board.save(OUT_DIR / f"{body}-{view}.png")
            report[body][view] = stats
            print(body, view, f"p95={stats['edge_error_p95_px']:.2f}px", flush=True)
    (OUT_DIR / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
