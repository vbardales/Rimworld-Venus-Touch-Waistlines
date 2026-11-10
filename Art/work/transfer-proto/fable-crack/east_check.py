"""East-profile agreement of the exported wdi3d mesh: per mesh row, front/back z extent against the east sprite mask.

uv run --with numpy --with pillow --with scipy --with scikit-image python east_check.py [mesh.json]
Prints per body the mean / p95 / max abs error (px) of front and back, and of the width (south mask) .
"""
import json
import pathlib
import sys

import numpy as np

import relief3d as r3
import relief_export2 as rx

here = pathlib.Path(__file__).parent
path = here / "out" / (sys.argv[1] if len(sys.argv) > 1 else "wdi3d-mesh.json")
d = json.load(open(path))
R = d["R"]
for body, e in d["bodies"].items():
    imgs = r3.views(body, False)
    ms = r3.silhouette(imgs["south"])
    me = r3.silhouette(imgs["east"])
    fr = e["frame"]
    rows = np.array(e["rows"]).reshape(R, -1, 3)
    s0, s1 = fr["s"]
    zmean = fr["zmean"]
    err_f, err_b = [], []
    for i in range(R):
        y = -rows[i, 0, 1]
        ye = rx.map_row_at(y, ms, me)
        zb, zf = rx.extent_at(me, ye)
        if zb is None:
            continue
        err_f.append(rows[i, :, 2].max() - (zf - zmean))
        err_b.append((zb - zmean) - rows[i, :, 2].min())
    f, b = np.array(err_f), np.array(err_b)
    a = np.abs(np.concatenate([f, b]))
    print(f"{body:12s} front mean {f.mean():6.2f} abs95 {np.percentile(np.abs(f), 95):5.2f} | back mean {b.mean():6.2f} abs95 {np.percentile(np.abs(b), 95):5.2f} | p95 {np.percentile(a, 95):5.2f} max {a.max():5.2f}")
