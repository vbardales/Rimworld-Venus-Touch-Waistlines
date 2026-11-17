"""Body prototypes M, W, T, H, F, C (2026-11-17, Virginie): all start equal to the Male average (the Male stack on
the Male sprite, with its fat), then each gets its own targets: fat, muscle and bone share of the mass, and the widths of
shoulders, upper chest, waist and pelvis relative to the shoulders.

This first part measures the Male average: the composition of the torso stack (volumes of bone, viscera, muscle, fat
pads, fat and the rest under the skin, masses with tissue densities) and the half-width profile of the skin.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python proto.py [h]
"""
import sys

import numpy as np

import stack3d as s

DENS = {"bone": 1.85, "viscera": 1.04, "muscle": 1.06, "fat pads": 0.92, "fat": 0.92, "rest": 1.10}   # g/cm3


def carry(K, a):
    out = K["steps"][0].warp(K["G0"], a, 1, K["G"])
    for f in K["steps"][1:]:
        out = f.warp(K["G"], out, 1)
    return out


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 1.5
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
