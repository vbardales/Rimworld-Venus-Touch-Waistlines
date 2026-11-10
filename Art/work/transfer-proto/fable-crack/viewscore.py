"""Score the viewer captures against the WDI sprites (full render, not contour only).

uv run --with numpy --with pillow --with scipy --with scikit-image python viewscore.py <tag>
Reads captures/2026-11-10_viewer-<tag>-<Body>.png (viewcap.py: south | east | north, 560x760 tiles).
Per body and view: silhouette p95 / mean (px of the 512 sprite, after fitting the bounding box of the render onto the
sprite's) and mean absolute luminance gap inside the outline (2 px blur), plus the blank-white gap for reference.
The fit is bounding box to bounding box, so a pure scale/offset error is hidden; the silhouette distance shows the rest.
"""
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import wdi3d as w

import os
DUMP = "DUMP" in os.environ
W, H = 560, 760
BG = np.array([244, 242, 238])
VIEWS = ("south", "east", "north")


def bbox(m):
    ys, xs = np.nonzero(m)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def edge_dist(a, b):
    """Distances (px) from the boundary of mask a to the boundary of mask b."""
    ea = a & ~ndi.binary_erosion(a)
    db = ndi.distance_transform_edt(~(b & ~ndi.binary_erosion(b)))
    return db[ea]


def main():
    tag = sys.argv[1]
    only = sys.argv[2:]
    res = {}
    for body in only or w.BODIES:
        im = np.asarray(Image.open(w.CAPT / f"2026-11-10_viewer-{tag}-{body}.png").convert("RGB")).astype(float)
        imgs, M, _ = w.load(body)
        width = {f: w.outline_width(imgs[f], M[f]) for f in imgs}
        out = []
        for i, v in enumerate(VIEWS):
            tile = im[:, i * W:(i + 1) * W]
            mr = ndi.binary_fill_holes(np.abs(tile - BG).sum(axis=2) > 24)
            x0, y0, x1, y1 = bbox(mr)
            sx0, sy0, sx1, sy1 = bbox(M[v])
            crop = tile[y0:y1, x0:x1].mean(axis=2) / 255.0
            mcrop = mr[y0:y1, x0:x1].astype(float)
            sw, sh = sx1 - sx0, sy1 - sy0
            lum = np.zeros((w.N, w.N)); mk = np.zeros((w.N, w.N))
            lum[sy0:sy1, sx0:sx1] = np.asarray(Image.fromarray((crop * 255).astype(np.uint8)).resize((sw, sh), Image.LANCZOS)) / 255.0
            mk[sy0:sy1, sx0:sx1] = np.asarray(Image.fromarray((mcrop * 255).astype(np.uint8)).resize((sw, sh), Image.BILINEAR)) / 255.0
            mk = mk > 0.5
            d = edge_dist(mk, M[v]); d2 = edge_dist(M[v], mk)
            dd = np.concatenate([d, d2])
            inner = ndi.distance_transform_edt(M[v]) > width[v] + 2
            ref = ndi.gaussian_filter(w.c1.lum(imgs[v]), 2.0)
            lum_b = ndi.gaussian_filter(np.where(mk, lum, 1.0), 2.0)
            gap = float(np.abs(ref - lum_b)[inner].mean()); blank = float(np.abs(ref - 1.0)[inner].mean())
            if DUMP:
                ref_i = np.where(M[v], w.c1.lum(imgs[v]), 0.9); ren_i = np.where(mk, lum, 0.9)
                ys, xs = np.nonzero(M[v] | mk)
                box = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
                a = np.stack([ref_i] * 3, -1)[box[1]:box[3], box[0]:box[2]]; b = np.stack([ren_i] * 3, -1)[box[1]:box[3], box[0]:box[2]]
                d = np.zeros_like(a); dl = (ref_i - ren_i)[box[1]:box[3], box[0]:box[2]]
                d[..., 0] = np.clip(0.9 + 3 * dl, 0, 1); d[..., 1] = np.clip(0.9 - 3 * np.abs(dl), 0, 1); d[..., 2] = np.clip(0.9 - 3 * dl, 0, 1)
                Image.fromarray((np.concatenate([a, b, d], 1) * 255).astype(np.uint8)).save(w.CAPT / f"2026-11-10_viewdiff-{tag}-{body}-{v}.png")
            out.append((v, float(np.percentile(dd, 95)), float(dd.mean()), gap, blank))
        res[body] = out
        print(f"{body:12s} " + " | ".join(f"{v[:1]} sil p95 {p:4.1f} mean {m:3.1f} lum {g:.3f} (blank {b:.3f})" for v, p, m, g, b in out), flush=True)
    return res


if __name__ == "__main__":
    main()
