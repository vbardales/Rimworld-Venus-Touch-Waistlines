"""Sections of the stack model, 4 px under the front and the back (2026-11-14, Virginie: 'un plan en coupe à 4 px du bord
le plus en avant, et pareil à 4 px du plan le plus en arrière, au niveau des volumes').

The stack (stack3d.make) keeps, for every voxel of the grid (row r, half width x, depth z), the volume that owns it
(S.owner, an index into S.parts: name, layer, colour). Four panels per body, each a frontal map (rows down, x mirrored):
  1. plane z = (most forward point of the body) - 4 px: what a flat cut cuts there (only what pokes out furthest)
  2. the same at the back: z = (most backward point) + 4 px
  3. the surface offset: for each (row, x), the owner 4 px under the skin of the front
  4. the same 4 px under the skin of the back
The offset maps (3 and 4) are the useful ones for reading what lies just under the relief (rectus edges, the hollow
under the abs, the lateral line); the planes (1, 2) are the literal cut.
Dark line = border between two volumes. Colours = the part colour of stack3d. Legend: the largest volumes of each panel.

Board: Art/work/captures/2026-11-14_sections-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python sections3d.py [Male Female]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import stack3d as s

CAPT = s.CAPT
SC = 4
DEPTH = 4.0


def panels(body):
    K = s.make(body, 1.0, ghost=True)
    G, S, d = K["G"], K["S"], K["d"]
    inside = d < 0                                             # r, x, z
    own = K["owner"]
    zs = G.z
    zi = np.where(inside, zs[None, None, :], -1e9)
    zf = zi.max(axis=2)                                        # front-most z of each (r, x)
    zi = np.where(inside, zs[None, None, :], 1e9)
    zb = zi.min(axis=2)
    has = inside.any(axis=2)
    zfront = float(zf[has].max()); zback = float(zb[has].min())
    out = {}

    def plane(z):
        k = int(np.clip(np.round((z - zs[0]) / G.h), 0, len(zs) - 1))
        return np.where(inside[:, :, k], own[:, :, k], 0)

    def offset(zsurf, sign):
        k = np.clip(np.round((zsurf - sign * DEPTH - zs[0]) / G.h).astype(int), 0, len(zs) - 1)
        rr, xx = np.indices(zsurf.shape)
        o = own[rr, xx, k]; ins = inside[rr, xx, k] & has
        return np.where(ins, o, 0)

    out["plane front"] = plane(zfront - DEPTH)
    out["plane back"] = plane(zback + DEPTH)
    out["4 px under the front skin"] = offset(zf, +1)
    out["4 px under the back skin"] = offset(zb, -1)
    return G, S, out, (zfront, zback)


def render(G, S, own, label, font):
    h, w = own.shape
    rgb = np.full((h, w, 3), 40, np.uint8)
    cols = np.array([(40, 40, 40)] + [p[2] for p in S.parts], np.uint8)
    rgb[:] = cols[np.clip(own, 0, len(cols) - 1)]
    full = np.concatenate([rgb[:, :0:-1], rgb], axis=1)        # mirror x
    ow = np.concatenate([own[:, :0:-1], own], axis=1)
    im = Image.fromarray(full).resize((full.shape[1] * SC, full.shape[0] * SC), Image.NEAREST)
    owb = np.kron(ow, np.ones((SC, SC), ow.dtype))
    edge = (owb != np.roll(owb, 1, 0)) | (owb != np.roll(owb, 1, 1))
    a = np.asarray(im).copy(); a[edge] = (20, 20, 20)
    im = Image.fromarray(a)
    area = np.bincount(own.ravel(), minlength=len(S.parts) + 1)[1:]
    top = np.argsort(-area)[:10]
    d = ImageDraw.Draw(im)
    d.text((6, 4), label, fill=(255, 255, 255), font=font)
    y = 22
    for i in top:
        if area[i] == 0:
            continue
        c = tuple(int(v) for v in S.parts[i][2])
        d.rectangle([6, y, 18, y + 11], fill=c, outline=(255, 255, 255))
        d.text((24, y - 1), f"{S.parts[i][0]} ({S.parts[i][1]})", fill=(255, 255, 255), font=font)
        y += 15
    return im


def one(body, font):
    G, S, out, (zf, zb) = panels(body)
    r0, r1 = np.nonzero(np.any([o > 0 for o in out.values()], axis=0).any(axis=1))[0][[0, -1]]
    ims = [render(G, S, o[r0:r1 + 1], f"{body}: {k}" + (f" (z {zf:.0f} - {DEPTH:.0f})" if k == "plane front" else
                                                         f" (z {zb:.0f} + {DEPTH:.0f})" if k == "plane back" else ""), font)
           for k, o in out.items()]
    tw, th = ims[0].size
    board = Image.new("RGB", (2 * tw + 30, 2 * th + 30), (235, 235, 230))
    for i, im in enumerate(ims):
        board.paste(im, (10 + (i % 2) * (tw + 10), 10 + (i // 2) * (th + 10)))
    p = rf"{CAPT}\2026-11-14_sections-{body}.png"
    board.save(p); print(p, f"front z {zf:.1f}, back z {zb:.1f}")


def main():
    bodies = [a for a in sys.argv[1:] if "=" not in a] or ["Male", "Female"]
    font = ImageFont.load_default(size=14)
    for b in bodies:
        one(b, font)


if __name__ == "__main__":
    main()
