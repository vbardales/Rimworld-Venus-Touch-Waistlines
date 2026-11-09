"""South/North/East shaded renders of the exported mesh beside the real WDI texture.

Writes Art/work/captures/2026-11-09_body3d-render-<Body>.png (rows south, north, east;
columns: WDI source | mesh lit from upper left | mesh edge over source).
Run after relief_export2.py:
    uv run --with numpy --with pillow --with scipy --with scikit-image python body3d_render.py [Body ...]
"""
import json
import pathlib
import sys

import numpy as np
from PIL import Image, ImageDraw

import crack as c1
import relief3d as r3
import shade3d  # noqa: F401
import body3d_compare as bc

HERE = pathlib.Path(__file__).parent
CAPT = HERE.parents[1] / "captures"
S = 2  # supersample


def quads(rows):
    r, a, _ = rows.shape
    tris = []
    ii, kk = np.meshgrid(np.arange(r - 1), np.arange(a), indexing="ij")
    k2 = (kk + 1) % a
    v00, v01 = ii * a + kk, ii * a + k2
    v10, v11 = (ii + 1) * a + kk, (ii + 1) * a + k2
    tris = np.concatenate([np.stack([v00, v10, v01], -1).reshape(-1, 3), np.stack([v01, v10, v11], -1).reshape(-1, 3)])
    return tris


def project(rows, view):
    x, y, z = rows[..., 0], -rows[..., 1], rows[..., 2]
    if view == "south":
        return x, y, z
    if view == "north":
        return -x, y, -z
    return z, y, x  # east: face to the right


def render(parts, view, mask, shift_to):
    """Return (rgb image N*S square, coverage) with 1 source px = S px.

    All parts (body rings, then leg strips) share one vertical registration.
    """
    ymin = min(float((-p[..., 1]).min()) for p in parts)
    ymax = max(float((-p[..., 1]).max()) for p in parts)
    src_rows = np.flatnonzero(mask.any(axis=1))
    top, bottom = src_rows[0], src_rows[-1]
    size = c1.N * S
    zbuf = np.full((size, size), -1e9)
    img = np.zeros((size, size))
    cov = np.zeros((size, size), bool)
    light = np.array([-0.45, -0.55, 0.70])
    light /= np.linalg.norm(light)
    jobs = []
    for rows in parts:
        sx, sy, depth = project(rows, view)
        sy = top + (sy - ymin) / max(ymax - ymin, 1e-6) * (bottom - top)
        sx = sx + shift_to
        P = np.stack([sx.reshape(-1), sy.reshape(-1), depth.reshape(-1)], -1)
        pts3 = np.stack([sx, sy, depth], -1)
        dv = np.gradient(pts3, axis=0)
        du = np.roll(pts3, -1, axis=1) - np.roll(pts3, 1, axis=1)
        n = np.cross(du, dv)
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-9)
        n = n.reshape(-1, 3)
        n[n[:, 2] < 0] *= -1  # face the camera (+depth)
        jobs.append((rows, P, np.clip(n @ light, 0, 1)))
    for rows, P, shade in jobs:
      for t in quads(rows):
        p = P[t]
        xs, ys = p[:, 0] * S, p[:, 1] * S
        x0, x1 = int(np.floor(xs.min())), int(np.ceil(xs.max()))
        y0, y1 = int(np.floor(ys.min())), int(np.ceil(ys.max()))
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, size - 1), min(y1, size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-9:
            continue
        w0 = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        w1 = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            continue
        z = w0 * p[0, 2] + w1 * p[1, 2] + w2 * p[2, 2]
        sh = w0 * shade[t[0]] + w1 * shade[t[1]] + w2 * shade[t[2]]
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = inside & (z > sub)
        sub[upd] = z[upd]
        img[y0:y1 + 1, x0:x1 + 1][upd] = sh[upd]
        cov[y0:y1 + 1, x0:x1 + 1] |= upd
    out = np.full((size, size, 3), 226, np.uint8)
    out[cov] = np.clip((0.22 + 0.78 * img[cov, None]) * 255, 0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGB"), cov


def main():
    names = tuple(a for a in sys.argv[1:] if a in bc.BODIES) or bc.BODIES
    data = json.loads(bc.DATA_PATH.read_text(encoding="utf-8"))
    a = 2 * data["U"]
    CAPT.mkdir(exist_ok=True)
    for body in names:
        entry = data["bodies"][body]
        parts = [np.asarray(entry["rows"], float).reshape(-1, a, 3)]
        for side in ("L", "R"):
            if entry.get("legs"):
                parts.append(np.asarray(entry["legs"][side], float).reshape(-1, a, 3))
        imgs = r3.views(body, False)
        tiles = []
        for view in bc.VIEWS:
            mask = r3.silhouette(imgs[view])
            full = np.concatenate(parts[:1], 0)
            # centre mesh on the source silhouette (same translation fit as the contour gate)
            lo, hi = bc.row_extents(mask)
            mlo, mhi = bc.mesh_extents(np.concatenate(parts, 0), view, mask)
            valid = np.isfinite(lo) & np.isfinite(mlo)
            shift = float(np.median(0.5 * (lo[valid] + hi[valid]) - 0.5 * (mlo[valid] + mhi[valid])))
            lit, cov = render(parts, view, mask, shift)
            src = bc.source_image(imgs[view]).convert("RGB").resize((c1.N * S, c1.N * S), Image.LANCZOS)
            ys, xs = np.nonzero(mask)
            box = ((max(0, xs.min() - 12)) * S, max(0, ys.min() - 12) * S, min(c1.N, xs.max() + 13) * S, min(c1.N, ys.max() + 13) * S)
            ov = np.asarray(src).copy()
            edge = cov & ~__import__("scipy.ndimage", fromlist=["x"]).binary_erosion(cov, iterations=2)
            ov[edge] = (255, 20, 180)
            tiles.append([src.crop(box), lit.crop(box), Image.fromarray(ov).crop(box)])
        W = sum(t.width for t in tiles[0]) + 24
        H = sum(t[0].height + 20 for t in tiles) + 24
        board = Image.new("RGB", (max(W, 10), H), (235, 235, 230))
        d = ImageDraw.Draw(board)
        d.text((4, 4), f"{body}: WDI texture | mesh lit | mesh edge (magenta) on WDI -- rows south, north, east", fill=(0, 0, 0))
        y = 22
        for view, row in zip(bc.VIEWS, tiles):
            x = 0
            d.text((2, y), view, fill=(0, 0, 0))
            for t in row:
                board.paste(t, (x, y + 12)); x += t.width + 12
            y += row[0].height + 20
        path = CAPT / f"2026-11-09_body3d-render-{body}.png"
        board.save(path)
        print(path, flush=True)


if __name__ == "__main__":
    main()
