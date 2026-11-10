"""Export of the stack model (stack3d.py) for the 3D viewer (2026-11-10).

Writes out/stack3d-mesh.json: {"R", "bodies": {"Male": entry}}; body3d_build.py puts each entry in the place of the wdi3d
body of the same name (the wdi3d one stays in the list as "<Body> (wdi3d)"). The entry has the fields of
wdi3d_export.py, all computed from the geometry of the stack, nothing read from the drawing except the areola colour:
  rows   R rings of A points, cast from the axis of each row to the skin (so the mesh has the same density all around);
  horns, legs   the same for the rows above the neck dip and below the crotch, where a row has two pieces;
  tex    areola albedo x (1 - ink), ink = depth of the narrow hollows of the stack's own surface;
  bake   tone of the top light on that surface (same transfer as wdi3d.py); gate = 1 (no gate from the drawing);
  layers the bones and each muscle and fat pad as their own meshes (right half; the viewer mirrors them).

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python stack3d_export.py [h]
then: uv run python body3d_build.py
"""
import json
import sys

import numpy as np
from scipy import ndimage as ndi
from skimage import measure

import stack3d as s
import wdi3d as w
import wdi3d_export as we

R_RINGS = 360
A_RING = 240
STEP = 0.5          # px along a ray


def sample(G, d, r, x, z):
    co = np.stack([(r - G.r[0]) / G.h, np.abs(x) / G.h, (z - G.z[0]) / G.h])
    return ndi.map_coordinates(d, co, order=1, mode="nearest")


def ring_stack(G, d, rows, cx, cz, first, rmax=130.0):
    """Rings of A_RING points around the axis (cx, cz) of each row. first: take the first exit along the ray (a piece
    beside another one), else the outermost one. Order: left, front, right, back, as relief_export2."""
    phi = -np.pi / 2 + 2 * np.pi * np.arange(A_RING) / A_RING
    rho = np.arange(0.0, rmax, STEP)
    rr = rows[:, None, None] + 0 * phi[None, :, None] + 0 * rho[None, None, :]
    xx = cx[:, None, None] + rho[None, None, :] * np.sin(phi)[None, :, None]
    zz = cz[:, None, None] + rho[None, None, :] * np.cos(phi)[None, :, None]
    v = sample(G, d, rr, xx, zz)
    inside = v < 0
    if first:
        idx = np.argmax(~inside, axis=2) - 1                  # last inside sample before the first exit
        idx = np.where(inside[..., 0], idx, 0)
    else:
        idx = v.shape[2] - 1 - np.argmax(inside[..., ::-1], axis=2)
    idx = np.clip(idx, 0, v.shape[2] - 2)
    a = np.take_along_axis(v, idx[..., None], 2)[..., 0]; b = np.take_along_axis(v, idx[..., None] + 1, 2)[..., 0]
    t = np.clip(a / np.minimum(a - b, -1e-6), 0, 1)
    rad = np.where(inside.any(axis=2), rho[idx] + t * STEP, 0.0)
    out = np.zeros((len(rows), A_RING, 3))
    out[..., 0] = cx[:, None] + rad * np.sin(phi)[None, :]
    out[..., 1] = rows[:, None]
    out[..., 2] = cz[:, None] + rad * np.cos(phi)[None, :]
    return out


def pieces(G, d):
    """Per grid row: is the midline inside, and the centroid of the x > 0 part of the section."""
    ins = d < 0
    mid = ins[:, 0, :].any(axis=1)
    cnt = ins.sum(axis=(1, 2)).astype(float)
    cx = (ins * G.x[None, :, None]).sum(axis=(1, 2)) / np.maximum(cnt, 1)
    cz = (ins * G.z[None, None, :]).sum(axis=(1, 2)) / np.maximum(cnt, 1)
    zmid = np.array([G.z[np.flatnonzero(c)].mean() if c.any() else np.nan for c in ins[:, 0, :]])
    return mid, cnt > 0, cx, cz, zmid


def mesh_of(field, sl, G, step):
    """Marching cubes of one display field (its sub-box) -> vertices (x, r, z) and triangles."""
    if field.min() >= 0 or min(field.shape) < 2 * step + 2:
        return None
    try:
        v, f, _, _ = measure.marching_cubes(field, 0.0, step_size=step, allow_degenerate=False)
    except (ValueError, RuntimeError):
        return None
    r = G.r[sl[0].start] + v[:, 0] * G.h; x = G.x[sl[1].start] + v[:, 1] * G.h; z = G.z[sl[2].start] + v[:, 2] * G.h
    return np.stack([x, r, z], 1), f


def one(h=1.0):
    K = s.make(h)
    T, G, S, d, F = K["T"], K["G"], K["S"], K["d"], K["fit"]
    st = F.stats()
    print("fit residual before the warp (px, mean / p95 / max): " + "  ".join(f"{k} {v[0]:.2f}/{v[1]:.2f}/{v[2]:.2f}" for k, v in st.items()), flush=True)
    mid, any_, cx, cz, zmid = pieces(G, d)
    rows_in = G.r[any_]; r_top, r_bot = float(rows_in[0]), float(rows_in[-1])
    rm = G.r[mid]; t0, t1 = float(rm[0]), float(rm[-1])       # rows where the section is one piece through the midline
    zc_fun = lambda r: np.interp(r, G.r[mid], ndi.gaussian_filter1d(zmid[mid], 4.0 / G.h, mode="nearest"))
    # torso
    rows = np.linspace(t0 + 0.4, t1 - 0.4, R_RINGS)
    rings = ring_stack(G, d, rows, np.zeros(R_RINGS), zc_fun(rows), first=False)
    zmean = float(rings[..., 2].mean())

    def two(ra, rb, n):
        """The right piece of the rows ra..rb as rings around its own centroid, and its mirror image."""
        rr = np.linspace(ra, rb, n)
        c_x = np.interp(rr, G.r, cx); c_z = np.interp(rr, G.r, cz)
        Rr = ring_stack(G, d, rr, c_x, c_z, first=True, rmax=90.0)
        L = Rr[:, ::-1].copy(); L[..., 0] *= -1
        L = np.roll(L, 1 - A_RING // 2, axis=1)               # same angular origin (left extreme) as the other rings
        return L, Rr

    def to_world(a):
        b = a.copy(); b[..., 1] = -a[..., 1]; b[..., 2] = a[..., 2] - zmean
        return b

    horns = legs = None
    if t0 - r_top > 1.0:
        L, Rr = two(r_top + 0.3, t0 + 0.4, max(int((t0 - r_top) / 0.5), 3))
        horns = {"L": np.round(to_world(L).reshape(len(L), -1), 2).tolist(), "R": np.round(to_world(Rr).reshape(len(Rr), -1), 2).tolist()}
    if r_bot - t1 > 1.0:
        L, Rr = two(t1 - 0.4, r_bot - 0.3, max(int((r_bot - t1) / 0.5), 3))
        legs = {"L": np.round(to_world(L).reshape(len(L), -1), 2).tolist(), "R": np.round(to_world(Rr).reshape(len(Rr), -1), 2).tolist(), "mode": "stack"}
    P = T.P["south"]
    lm = {"top": -r_top, "bottom": -r_bot, "split": -t1}
    for key, nm in (("apex", "breast apex L"), ("fold", "under-breast fold L"), ("navel", "navel"), ("sex", "sex"),
                    ("crotch", "crotch point"), ("shoulder", "shoulder tip L"), ("armpit", "armpit L")):
        if nm in P:
            lm[key] = -float(P[nm][1])
    frame = {"s": [int(T.s0), int(T.s1)], "n": [int(T.n0), int(T.n1)], "e": [int(T.e0), int(T.e1)],
             "cxs": round(T.cxs, 2), "cxn": round(T.cxn, 2), "zmean": round(zmean, 2),
             "zc": np.round(np.interp(np.arange(T.s0, T.s1 + 1), T.rows, T.zc) - zmean, 2).tolist()}
    # maps from the stack's own surface
    fields = s.sprite_fields(G, d, T)
    tex, bake, gate, rep = {}, {}, {}, {}
    for f in ("south", "north", "east"):
        hf, m = fields[f]
        ink = np.clip((w.closed(hf) - hf) * m / w.GROOVE, 0, 1)
        albedo = np.ones((w.N, w.N, 3))
        yy, xx = np.mgrid[0:w.N, 0:w.N]
        for (x, y, r, col) in w.areolae(T.imgs[f], T.M[f]):
            a = np.clip(r + 0.5 - np.hypot(xx - x, yy - y), 0, 1)[..., None]
            albedo = albedo * (1 - a) + col * a
        tex[f[0]] = we.data_uri(albedo * (1 - ink[..., None]))
        bake[f[0]] = we.gray_uri(we.baked_loss(hf, m))
        gate[f[0]] = we.gray_uri(np.ones((w.N, w.N)))
        wd = w.outline_width(T.imgs[f], T.M[f])
        cap = w.capture(hf, m, wd, w.areolae(T.imgs[f], T.M[f]))
        mae, blank = w.score(cap, T.imgs[f], T.M[f], wd)
        p95, mean, mx = s.sil_error(m, T.M[f])
        rep[f] = {"sil_p95": round(p95, 2), "sil_mean": round(mean, 2), "lum": round(mae, 4), "blank": round(blank, 4)}
        print(f"{f:6s} field vs sprite: sil p95 {p95:.2f} mean {mean:.2f} | lum {mae:.4f} (blank {blank:.4f})", flush=True)
    # layers: bones as one mesh, muscles, viscera and fat pads one mesh each (right half, fitted like the skin)
    step = max(int(round(3.0 / G.h)), 1)

    def pack(vf):
        v, f = vf
        x, r, z = F.forward(v[:, 0], v[:, 1], v[:, 2])
        return {"v": np.round(np.stack([x, -r, z - zmean], 1).reshape(-1), 1).tolist(), "i": f.reshape(-1).astype(int).tolist()}

    bone = G.full()
    layers = {"bone": None, "parts": []}
    for name, layer, colour, sl, a in S.parts:
        if a is None:
            continue
        if layer == "bone":
            bone[sl] = np.minimum(bone[sl], a)
            continue
        m_ = mesh_of(a, sl, G, step)
        if m_ is not None:
            layers["parts"].append({"n": name, "l": layer, "c": [int(c) for c in colour], **pack(m_)})
    full = (slice(0, G.shape[0]), slice(0, G.shape[1]), slice(0, G.shape[2]))
    layers["bone"] = pack(mesh_of(bone, full, G, max(step - 1, 1)))   # bones are thin: finer than the muscles
    e = {"rows": np.round(to_world(rings).reshape(R_RINGS, -1), 2).tolist(), "legs": legs, "horns": horns, "lm": lm,
         "cage": {"moved": 0}, "frame": frame, "tex": tex, "bake": bake, "gate": gate, "A": A_RING, "sn": 2, "layers": layers,
         "outline": round(float(np.mean([w.outline_width(T.imgs[f], T.M[f]) for f in T.imgs])), 1),
         "fit": {k: [round(x, 2) for x in v] for k, v in st.items()}, "score2d": rep}
    return e


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    out = {"Male": one(h)}
    path = s.HERE / "out" / "stack3d-mesh.json"
    path.write_text(json.dumps({"R": R_RINGS, "U": A_RING // 2, "bodies": out}, separators=(",", ":")), encoding="utf-8")
    e = out["Male"]
    print("ok", path, f"{path.stat().st_size / 1e6:.1f} MB", "parts", len(e["layers"]["parts"]),
          "horns", None if e["horns"] is None else len(e["horns"]["L"]), "legs", None if e["legs"] is None else len(e["legs"]["L"]))


if __name__ == "__main__":
    main()
