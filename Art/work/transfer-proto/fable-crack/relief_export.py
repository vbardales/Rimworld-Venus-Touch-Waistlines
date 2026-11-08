"""Export the REAL relief of the WDI bodies (relief3d.height: width x depth volume, chest lobes on her points, drawn zones as
volumes) as a closed mesh for the 3D viewer. Front = south height field, back = north height field, joined at the
silhouette edge. Output: out/relief3d.json  {body: {R, U, pts:[row:[x,y,z]*2U]}}  (ring of 2U points per row).
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python relief_export.py [Body ...]
"""
import os, sys, json
import numpy as np
from scipy import ndimage as ndi
import crack as c1, crack2, explain5b as e5
import relief3d as r3

N = c1.N
R, U = 150, 44
SIGMA_ROWS = 2.5
BODIES = ["Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female"]


def one(body):
    imgs = r3.views(body, False)
    M = {f: r3.silhouette(imgs[f]) for f in imgs}
    H = {}
    for f in ("south", "east", "north"):
        s, d, names = e5.named_pairs(body, f)
        pts = {n: tuple(s[i]) for i, n in enumerate(names)}
        H[f] = r3.height(f, M, pts, c1.lum(imgs[f]))
    ms, me, mn = M["south"], M["east"], M["north"]
    s0, s1 = r3.rows_of(ms)
    cx = np.mean([np.mean(r3.extent(ms, y)) for y in range(s0, s1 + 1)])
    ring = np.zeros((R, 2 * U, 3))
    zref = None
    for i in range(R):
        y = int(round(s0 + (s1 - s0) * i / (R - 1)))
        xl, xr = r3.extent(ms, y)
        ye = int(np.clip(r3.map_row(y, ms, me), 0, N - 1)); zb, zf = r3.extent(me, ye)
        yn = int(np.clip(r3.map_row(y, ms, mn), 0, N - 1)); nl, nr = r3.extent(mn, yn)
        if xl is None or zb is None or nl is None:
            ring[i] = ring[i - 1] if i else 0
            continue
        zc = 0.5 * (zb + zf)
        for k in range(U):
            u = k / (U - 1)
            xs = xl + u * (xr - xl)
            hf = ndi.map_coordinates(H["south"], [[y], [xs]], order=1)[0]
            xn = nr - u * (nr - nl)            # the back view is mirrored
            hb = ndi.map_coordinates(H["north"], [[yn], [xn]], order=1)[0]
            ring[i, k] = (xs - cx, -y, zc + hf)
            ring[i, 2 * U - 1 - k] = (xs - cx, -y, zc - hb)
    ring = ndi.gaussian_filter1d(ring, SIGMA_ROWS, axis=0, mode="nearest")
    ring[..., 2] -= np.mean(ring[..., 2])
    return np.round(ring.reshape(R, -1), 1).tolist()


def main():
    names = [a for a in sys.argv[1:] if a in BODIES] or BODIES
    out = {}
    for b in names:
        print(b, flush=True)
        out[b] = one(b)
    json.dump({"R": R, "U": U, "bodies": out}, open(rf"{c1.OUT}\relief3d{os.environ.get("RELIEF_TAG","")}.json", "w"), separators=(",", ":"))
    print("ok")


if __name__ == "__main__":
    main()
