"""Export 2 (Virginie 2026-11-08: 'la séparation des jambes aussi', 'regénère le squelette intérieur'): the shaded relief of
shade3d as a closed mesh like relief_export.py, plus
  - the two legs as separate rings below the crotch notch (rows where the silhouette has two runs),
  - landmark rows (world y) for the skeleton of the viewer: top, shoulder tip, apex, fold, navel, sex, crotch.
Output out/relief3d-shade5.json {R,U,bodies:{b:{rows:[R][2U*3], legs:{L:[n][2U*3],R:[...]}|null, lm:{name:y}}}}.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python relief_export2.py [Body ...]"""
import sys, json
import numpy as np
from scipy import ndimage as ndi
import crack as c1, explain5b as e5
import relief3d as r3
import shade3d  # noqa: F401  (patches r3.height and r3.silhouette)

N = c1.N
R, U = 150, 44
SIGMA_ROWS = 2.5
BODIES = ["Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female"]


def runs(row):
    d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
    return list(zip(np.where(d == 1)[0], np.where(d == -1)[0] - 1))


def one(body):
    imgs = r3.views(body, False)
    M = {f: r3.silhouette(imgs[f]) for f in imgs}
    H, P = {}, {}
    for f in ("south", "east", "north"):
        s, d, names = e5.named_pairs(body, f)
        pts = {n: tuple(s[i]) for i, n in enumerate(names)}
        if f == "south":
            P = pts
        H[f] = r3.height(f, M, pts, c1.lum(imgs[f]))
    ms, me, mn = M["south"], M["east"], M["north"]
    s0, s1 = r3.rows_of(ms)
    cx = np.mean([np.mean(r3.extent(ms, y)) for y in range(s0, s1 + 1)])
    # the split row: first row under the crotch point where the silhouette has two runs
    cy = int(P["crotch point"][1]) if "crotch point" in P else int(0.9 * (s1 - s0) + s0)
    ysplit = None
    for y in range(cy - 8, s1 + 1):
        rr = [r for r in runs(ms[y]) if r[1] - r[0] >= 4]
        if len(rr) >= 2:
            ysplit = y
            break
    zc_all = {}

    def ring(y, xa, xb, xl, xr):
        ye = int(np.clip(r3.map_row(y, ms, me), 0, N - 1)); zb, zf = r3.extent(me, ye)
        yn = int(np.clip(r3.map_row(y, ms, mn), 0, N - 1)); nl, nr = r3.extent(mn, yn)
        if zb is None or nl is None:
            return None
        zc = 0.5 * (zb + zf)
        out = np.zeros((2 * U, 3))
        for k in range(U):
            u = k / (U - 1)
            xs = xa + u * (xb - xa)
            hf = ndi.map_coordinates(H["south"], [[y], [xs]], order=1)[0]
            xn = nr - ((xs - xl) / max(xr - xl, 1)) * (nr - nl)
            hb = ndi.map_coordinates(H["north"], [[yn], [xn]], order=1)[0]
            out[k] = (xs - cx, -y, zc + hf)
            out[2 * U - 1 - k] = (xs - cx, -y, zc - hb)
        return out

    ytop = ysplit if ysplit is not None else s1
    rows = []
    for i in range(R):
        y = int(round(s0 + (ytop - s0) * i / (R - 1)))
        xl, xr = r3.extent(ms, y)
        rg = None if xl is None else ring(y, xl, xr, xl, xr)
        rows.append(rg if rg is not None else (rows[-1] if rows else np.zeros((2 * U, 3))))
    rows = ndi.gaussian_filter1d(np.array(rows), SIGMA_ROWS, axis=0, mode="nearest")
    zmean = float(np.mean(rows[..., 2]))
    rows[..., 2] -= zmean
    legs = None
    if ysplit is not None and s1 - ysplit >= 2:
        L, Rr = [], []
        for y in range(ysplit - 1, s1 + 1):
            xl, xr = r3.extent(ms, y)
            rr = [r for r in runs(ms[y]) if r[1] - r[0] >= 3]
            if xl is None or len(rr) < 2:
                continue
            a, b = rr[0], rr[-1]
            ra = ring(y, a[0], a[1], xl, xr); rb = ring(y, b[0], b[1], xl, xr)
            if ra is None or rb is None:
                continue
            L.append(ra); Rr.append(rb)
        if len(L) >= 2:
            L = np.array(L); Rr = np.array(Rr)
            L[..., 2] -= zmean; Rr[..., 2] -= zmean
            legs = {"L": np.round(L.reshape(len(L), -1), 1).tolist(), "R": np.round(Rr.reshape(len(Rr), -1), 1).tolist()}
    lm = {"top": -float(s0), "bottom": -float(s1)}
    for key, nm in (("apex", "breast apex L"), ("fold", "under-breast fold L"), ("navel", "navel"), ("sex", "sex"),
                    ("crotch", "crotch point"), ("shoulder", "shoulder tip L"), ("armpit", "armpit L")):
        if nm in P:
            lm[key] = -float(P[nm][1])
    if ysplit is not None:
        lm["split"] = -float(ysplit)
    return {"rows": np.round(rows.reshape(R, -1), 1).tolist(), "legs": legs, "lm": lm}


def main():
    names = [a for a in sys.argv[1:] if a in BODIES] or BODIES
    out = {}
    for b in names:
        print(b, flush=True)
        out[b] = one(b)
        print("  split", out[b]["lm"].get("split"), "legs", None if out[b]["legs"] is None else len(out[b]["legs"]["L"]), flush=True)
    json.dump({"R": R, "U": U, "bodies": out}, open(rf"{c1.OUT}\relief3d-shade5.json", "w"), separators=(",", ":"))
    print("ok")


if __name__ == "__main__":
    main()
