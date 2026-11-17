"""Body prototypes M, W, T, H, F, C (2026-11-17, Virginie): all start equal to the Male average (the Male stack on
the Male sprite, with its fat), then each gets its own targets: fat, muscle and bone share of the mass, and the widths of
shoulders, upper chest, waist and pelvis relative to the shoulders.

This first part measures the Male average: the composition of the torso stack (volumes of bone, viscera, muscle, fat
pads, fat and the rest under the skin, masses with tissue densities) and the half-width profile of the skin.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python proto.py [h]
"""
import sys

import numpy as np
from scipy import ndimage as ndi

import stack3d as s

DENS = {"bone": 1.85, "viscera": 1.04, "muscle": 1.06, "fat pads": 0.92, "fat": 0.92, "rest": 1.10}   # g/cm3


def carry(K, a):
    out = K["steps"][0].warp(K["G0"], a, 1, K["G"])
    for f in K["steps"][1:]:
        out = f.warp(K["G"], out, 1)
    return out


# Prototype targets: widths relative to the shoulders (Virginie 2026-11-17). Rows of the Male frame where each is read:
# shoulders = widest row (deltoid stump, 268), upper chest = under the armpits (298), waist = navel (358), pelvis = hips (382).
WROWS = {"shoulders": 268.0, "upper chest": 298.0, "waist": 358.0, "pelvis": 382.0}
PROTO = {"M": {"shoulders": 1.0, "upper chest": 0.8, "waist": 0.66, "pelvis": 0.76}}


def width_scale(G, d, target):
    """Row-wise width scale that brings the skin half widths at WROWS to target x shoulder width (1 above the
    shoulders, held below the pelvis)."""
    xm = np.nanmax(s.last_cross(d, 1, G.x), axis=1)
    hw = lambda r: float(np.interp(r, G.r, np.nan_to_num(xm)))
    sh = hw(WROWS["shoulders"])
    rows = [WROWS[k] for k in WROWS]
    k = [target[n] * sh / hw(WROWS[n]) for n in WROWS]
    return rows, k


# Shape edits on top of the widths (Virginie 2026-11-17 on M: 'étire la cage thoracique, remonte les pectoraux,
# retravaille les fesses'), all as smooth displacements of the finished stack (skin, muscles, bones move together):
#   cage: rows of the thorax stretched down: the costal margin (334) goes to 334 + cage, the crotch (422) stays;
#   pecs: the front of the chest (rows 250..345, x < 85) lifted by pecs px, most at the under-chest fold;
#   glutes: the back of the buttocks pushed back by glutes px and up by a third of it, round, centred on each cheek.
SHAPE = {"M": dict(cage=12.0, pecs=12.0, glutes=7.0)}


def sstep(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


def bump(v, c, wd):
    """1 at c, 0 at c +/- wd, smooth."""
    return sstep(1.0 - np.abs(v - c) / wd)


def shaped(G, Gs, fields, rows, k, zc, sh):
    """Fields of the Male stack, scaled in width (rows, k), then edited by SHAPE: inverse map from each output voxel."""
    X, R, Z = (np.broadcast_to(a, G.shape).astype(np.float32) for a in G.coords((slice(None),) * 3))
    zm = np.interp(R, *zc).astype(np.float32)
    front = sstep((Z - zm) / 12.0); back = sstep((zm - Z) / 12.0)
    # glutes (undone first: they are the last edit)
    g = sh["glutes"] * bump(R, 402.0, 28.0) * bump(X, 30.0, 34.0) * back
    Z = Z + g; R = R + g / 3.0
    # pecs: output at R shows what was lower
    p = sh["pecs"] * bump(R, 315.0, 55.0) * sstep((85.0 - X) / 20.0) * front
    R = R + p
    # cage: piecewise linear rows, output -> source
    R = np.interp(R, [0.0, 232.0, 334.0 + sh["cage"], 422.0, 1000.0], [0.0, 232.0, 334.0, 422.0, 1000.0]).astype(np.float32)
    # widths
    X = X / np.interp(R, rows, k).astype(np.float32)
    co = np.stack([(R - Gs.r[0]) / Gs.h, X / Gs.h, (Z - Gs.z[0]) / Gs.h])
    out = []
    for a, order in fields:
        out.append(ndi.map_coordinates(a.astype(np.float32), co, order=order, mode="nearest"))
    return out


def proto_board(name, h):
    """Prototype vs WDI: the Male stack (skin, fat, lean) scaled row by row in width to the prototype's ratios, drawn
    by stack3d.board next to the WDI Male (WDI | stack in WDI style | outlines)."""
    import average as av
    K = s.make("Male", h)
    G, T = K["G"], K["T"]
    rows, k = width_scale(G, K["d"], PROTO[name])
    print(f"{name}: width scale at {rows}: {[round(x, 3) for x in k]}")
    Go = s.Grid(G.h, x1=float(G.x[-1]) * max(max(k), 1.0) + 4.0, r0=float(G.r[0]), r1=float(G.r[-1]) + 8.0,
                z0=float(G.z[0]) - 8.0, z1=float(G.z[-1]))
    tgt = PROTO[name]
    for it in range(4):                                        # the shape edits move the rows: re-solve the widths on the result
        d, o = shaped(Go, G, [(K["d"], 1), (K["owner"], 0)], rows, k, (T.rows, T.zc), SHAPE[name])
        xm = np.nan_to_num(np.nanmax(s.last_cross(d, 1, Go.x), axis=1))
        hw = lambda r: float(np.interp(r, Go.r, xm))
        sh = hw(WROWS["shoulders"])
        k = [kk * tgt[n] * sh / hw(WROWS[n]) for kk, n in zip(k, WROWS)]
    d, o = shaped(Go, G, [(K["d"], 1), (K["owner"], 0)], rows, k, (T.rows, T.zc), SHAPE[name])
    o = np.round(o).astype(np.int16)
    rep, path = s.board(K["S"], Go, d, T, f"proto{name}", o, extra=f"prototype {name}")
    for f, r in rep.items():
        print(f"{f:6s} sil p95 {r['p95']:.2f} | lum {r['mae']:.4f}")
    xm = np.nanmax(s.last_cross(d, 1, Go.x), axis=1)
    sh = float(np.interp(WROWS["shoulders"], Go.r, np.nan_to_num(xm)))
    print("ratios now:", {n: round(float(np.interp(r, Go.r, np.nan_to_num(xm))) / sh, 3) for n, r in WROWS.items()})
    print(path)


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1][0].isdigit() else 1.5
    if len(sys.argv) > 2 and sys.argv[2] in PROTO:
        return proto_board(sys.argv[2], h)
    K = s.make("Male", h)
    G, S, d = K["G"], K["S"], K["d"]
    # the stack's own bone layer is a filled barrel (the rib cage as one solid): the bones are the display parts
    G0 = K["G0"]
    un = {"bone": G0.full(), "muscle": G0.full(), "fat": G0.full()}
    for name, layer, colour, sl, a in S.parts:
        if a is not None and layer in un:
            un[layer][sl] = np.minimum(un[layer][sl], a)
    bone = carry(K, un["bone"]) < 0
    musc = (carry(K, un["muscle"]) < 0) & ~bone
    pads = (carry(K, un["fat"]) < 0) & ~bone & ~musc
    lean = carry(K, S.d) < 0
    fat = K["fat"]
    for f in K["steps"][1:]:
        fat = f.warp(G, fat, 1)
    fat = fat < 0
    skin = d < 0
    vox = {"bone": bone, "muscle": musc, "fat pads": pads, "viscera": lean & ~bone & ~musc & ~pads,
           "fat": fat & ~lean & ~bone & ~musc & ~pads, "rest": skin & ~fat & ~lean & ~bone & ~musc & ~pads}
    v = {k: float((m & skin).sum()) * G.h ** 3 for k, m in vox.items()}
    mass = {k: v[k] * DENS[k] for k in v}
    tot = sum(mass.values())
    print("composition of the torso (share of mass; volume share in brackets):")
    vt = sum(v.values())
    for k in v:
        print(f"  {k:9s} {100 * mass[k] / tot:5.1f} %  ({100 * v[k] / vt:5.1f} % of volume)")
    xm = s.last_cross(d, 1, G.x)                                # half width of the skin per row
    print("half width of the skin per row (Male frame rows):")
    for r in range(190, 432, 6):
        i = int(round((r - G.r[0]) / G.h))
        print(f"  row {r}: {np.nanmax(xm[i]):6.1f}")


if __name__ == "__main__":
    main()
