"""Bodies without fat and without ghost limbs, then one Average body varied by ratios per body type (2026-11-17).

Virginie's method: (1) show the bodies without the ghost limbs and without fat; (2) start again from one Average form,
the same for every body type; (3) vary that Average by ratios per body type and show the result, without fitting it to
the WDI sprites yet (that is a second step).

Board 1 (lean-wdi): the lean stack (bones, viscera, muscles; no fat pads, no fat, no skin) carried onto each WDI body by
the frame fit and the fine fits, as the export does it. South, east, north, coloured by volume.
Board 2 (average): the Average lean stack in the Male frame (the Male anatomy, muscle thickness 1), then each body type
= that Average with the ratios of RATIOS: a width scale and a depth scale per control row (shoulders, chest, waist,
hips), and a thickness scale of the sheet muscles. No WDI sprite is read for board 2.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python average.py [h] [lean|avg|both]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

import stack3d as s
import wdi3d as w

# Control rows of the Male frame (south rows of the Male sprite): neck base, shoulder (acromion), chest, under-chest
# fold, waist, iliac crest, hip (trochanter), crotch.
ROWS = [200.0, 232.0, 270.0, 322.0, 340.0, 358.0, 385.0, 422.0]
ONE = [1.0] * len(ROWS)
# Sex ratios (female / male, adults, same height): shoulders 0.87 (biacromial 36 / 41 cm), chest 0.90, waist 0.84,
# iliac crest 0.97, hips 1.05 (bitrochanteric, wider pelvis), crotch 1.04; depth a little less at the chest and the
# waist, a little more at the buttocks.
FEMALE_X = [0.86, 0.87, 0.90, 0.88, 0.84, 0.97, 1.05, 1.04]
FEMALE_Z = [0.92, 0.92, 0.92, 0.92, 0.90, 0.95, 1.03, 1.03]
# Build ratios (on top of the sex ratios): Thin narrower and shallower all over; Hulk much wider at the shoulders and
# chest, less at the waist and hips (the V); Fat lean only slightly larger (a fat body is mostly fat, added later).
BUILD = {
    "Average": (ONE, ONE),
    "Thin": ([0.84] * 8, [0.84] * 8),
    "Fat": ([1.04, 1.05, 1.05, 1.05, 1.05, 1.05, 1.05, 1.04], [1.06] * 8),
    "Hulk": ([1.18, 1.30, 1.25, 1.16, 1.08, 1.06, 1.05, 1.05], [1.14, 1.15, 1.16, 1.12, 1.08, 1.06, 1.08, 1.06]),
}
# muscle thickness: the values of stack3d.TYPES (ms)
TYPE_OF = {"Male": "Average", "Female": "Average", "Thin": "Thin", "Thin_Female": "Thin", "Fat": "Fat",
           "Fat_Female": "Fat", "Hulk": "Hulk", "Hulk_Female": "Hulk"}


def ratios(body):
    bx, bz = BUILD[TYPE_OF[body]]
    if "Female" in body:
        bx = [a * b for a, b in zip(bx, FEMALE_X)]; bz = [a * b for a, b in zip(bz, FEMALE_Z)]
    return np.array(bx), np.array(bz), float(s.TYPES[body]["ms"])


def lean_of(body, h):
    """Average lean stack (Male anatomy) with the muscle thickness of the body type, in the Male frame."""
    G0 = s.Grid(h)
    TM = s.Target("Male")
    ty = dict(s.TYPES["Male"]); ty["ms"] = s.TYPES[body]["ms"]
    S = s.build_male(G0, TM, ty=ty)
    return G0, TM, S, S.layer_d["muscle"]


def vary(G0, TM, a, owner, sx, sz):
    """The field a of the Male frame with x scaled by sx(r) and z by sz(r) around the centre plane, on a grid wide
    enough for the largest ratio."""
    k = float(max(sx.max(), sz.max()))
    Go = s.Grid(G0.h, x1=float(G0.x[-1]) * k + 4.0, r0=float(G0.r[0]), r1=float(G0.r[-1]),
                z0=250.0 - (250.0 - float(G0.z[0])) * k, z1=250.0 + (float(G0.z[-1]) - 250.0) * k)
    r = Go.r.astype(float)
    fx = np.interp(r, ROWS, sx); fz = np.interp(r, ROWS, sz); zm = np.interp(r, TM.rows, TM.zc)
    co = np.empty((3,) + Go.shape, np.float32)
    co[0] = ((r - G0.r[0]) / G0.h)[:, None, None]
    co[1] = ((Go.x[None, :] / fx[:, None]) / G0.h)[:, :, None]
    co[2] = ((zm[:, None] + (Go.z[None, :] - zm[:, None]) / fz[:, None] - G0.z[0]) / G0.h)[:, None, :]
    f = ndi.map_coordinates(a, co, order=1, mode="nearest", cval=s.BIG).astype(np.float32)
    o = ndi.map_coordinates(owner.astype(np.float32), co, order=0, mode="nearest").astype(np.int16)
    return Go, f, o


def views(G, d, owner, pal):
    return [s.oblique(G, d, owner, (pal,), a, 1.0)[0] for a in (0, 90, 180)]


def board(cols, title, path):
    """cols: list of (label, [south, east, north]) images; one column per body, one row per view."""
    cw = max(im.width for _, ims in cols for im in ims) + 8
    rh = [max(ims[i].height for _, ims in cols) + 6 for i in range(3)]
    out = Image.new("RGB", (cw * len(cols), sum(rh) + 34), (244, 242, 238)); dr = ImageDraw.Draw(out)
    dr.text((4, 2), title, fill=(0, 0, 0))
    for j, (lab, ims) in enumerate(cols):
        dr.text((j * cw + 4, 18), lab, fill=(0, 0, 0))
        y = 32
        for i, im in enumerate(ims):
            out.paste(im, (j * cw + (cw - im.width) // 2, y + rh[i] - 6 - im.height)); y += rh[i]
    out.save(path)
    print(path, flush=True)


def lean_wdi(h):
    cols = []
    for b in w.BODIES:
        K = s.make(b, h)
        G = K["G"]; S = K["S"]
        lean = K["steps"][0].warp(K["G0"], S.layer_d["muscle"], 1, G)
        for f in K["steps"][1:]:
            lean = f.warp(G, lean, 1)
        cols.append((b, views(G, lean, K["owner"], s.palette_of(S))))
        print("lean", b, flush=True)
    board(cols, "Bodies without fat and without ghost limbs: bones, viscera, muscles carried onto each WDI body (south | east | north)",
          s.CAPT / "2026-11-17_lean-wdi.png")


def average(h):
    cols = []
    cache = {}
    for b in ["Average"] + list(w.BODIES):
        ms = 1.0 if b == "Average" else s.TYPES[b]["ms"]
        if ms not in cache:
            cache[ms] = lean_of("Male" if b == "Average" else b, h)
        G0, TM, S, a = cache[ms]
        if b == "Average":
            sx, sz = np.array(ONE), np.array(ONE)
        else:
            sx, sz, _ = ratios(b)
        Go, f, o = vary(G0, TM, a, S.owner, sx, sz)
        lab = "Average (ms 1.00)" if b == "Average" else f"{b} (ms {ms:.2f}) x {sx[1]:.2f}/{sx[4]:.2f}/{sx[6]:.2f}"
        cols.append((lab, views(Go, f, o, s.palette_of(S))))
        print("avg", b, flush=True)
    board(cols, "One Average lean body (no fat), varied per body type: label = muscle thickness, width ratio shoulders/waist/hips (south | east | north)",
          s.CAPT / "2026-11-17_average-ratios.png")


def main():
    args = sys.argv[1:]
    h = float(args[0]) if args else 1.5
    what = args[1] if len(args) > 1 else "both"
    if what in ("avg", "both"):
        average(h)
    if what in ("lean", "both"):
        lean_wdi(h)


if __name__ == "__main__":
    main()
