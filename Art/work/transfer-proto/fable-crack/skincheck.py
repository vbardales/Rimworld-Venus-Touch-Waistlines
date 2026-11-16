"""Is the skin over everything? (2026-11-17, Virginie: check that the skin lies over the bones, the muscles and the fat.)

For each body, the bone field, the lean field (bones, viscera, muscles, pads) and the fat solid are carried onto the
body grid by the same frame fit and fine fits as the skin. A voxel inside one of them and outside the skin pokes
through. Per (row, x), the thickness that pokes through is summed along the depth, front half and back half apart.

Board per body, rows south (front) and north (back), columns bone | muscle (lean less bone) | fat: grey silhouette of
the skin, red where something pokes through (darker = thicker, scale in the title), with the share of the silhouette
touched and the worst thickness in px.

Board: Art/work/captures/2026-11-17_skincheck-<tag>.png (all bodies stacked)
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python skincheck.py [h] [tag] [Body ...]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

import stack3d as s
import wdi3d as w


def carry(K, a):
    """A field of the Male frame onto the body grid, through the frame fit then the fine fits."""
    G0, G, steps = K["G0"], K["G"], K["steps"]
    out = steps[0].warp(G0, a, 1, G)
    for f in steps[1:]:
        out = f.warp(G, out, 1)
    return out


def body_tiles(body, h):
    K = s.make(body, h)
    G, d, S = K["G"], K["d"], K["S"]
    bone = carry(K, S.layer_d["bone"])
    lean = carry(K, S.d)
    fat = K["fat"]
    for f in K["steps"][1:]:                                  # the fat is solved before the fine fits
        fat = f.warp(G, fat, 1)
    out_skin = d > 0
    zc = 0.5 * (s.last_cross(d, 2, G.z, True) + s.last_cross(d, 2, G.z, False))   # mid depth of each (row, x)
    front = G.z[None, None, :] >= np.nan_to_num(zc, nan=1e9)[:, :, None]
    sil = np.isfinite(zc)
    tiles, stats = [], {}
    for name, field in (("bone", bone < 0), ("muscle", (lean < 0) & ~(bone < 0)), ("fat", (fat < 0) & ~(lean < 0))):
        poke = field & out_skin
        for side, msk in (("front", front), ("back", ~front)):
            t = (poke & msk).sum(axis=2) * G.h                  # px poking through per (row, x)
            share = 100.0 * float((t[sil] > 0).mean()) if sil.any() else 0.0
            stats[(name, side)] = (share, float(t.max()))
            img = np.full(t.shape + (3,), 236, np.uint8)
            img[sil] = (205, 205, 200)
            k = np.clip(t / 4.0, 0, 1)
            red = np.stack([200 + 0 * k, 200 * (1 - k), 200 * (1 - k)], -1).astype(np.uint8)
            img[t > 0] = red[t > 0]
            full = np.concatenate([img[:, :0:-1], img], axis=1)        # mirror onto x < 0
            im = Image.fromarray(full).resize((int(full.shape[1] * G.h), int(full.shape[0] * G.h)), Image.NEAREST)
            tiles.append((name, side, im))
    return tiles, stats


def main():
    args = sys.argv[1:]
    h = float(args[0]) if args and args[0] not in s.TYPES else 2.0
    tag = args[1] if len(args) > 1 and args[1] not in s.TYPES else "t"
    names = [a for a in args if a in s.TYPES] or list(w.BODIES)
    rows = []
    for b in names:
        tiles, st = body_tiles(b, h)
        line = "  ".join(f"{n}/{sd} {st[(n, sd)][0]:.1f}% max {st[(n, sd)][1]:.0f}px" for n in ("bone", "muscle", "fat") for sd in ("front", "back"))
        print(f"{b:12s} {line}", flush=True)
        rows.append((b, tiles, line))
    tw = max(t[2].width for _, tl, _ in rows for t in tl); th = max(t[2].height for _, tl, _ in rows for t in tl)
    W = 6 * (tw + 4); H = len(rows) * (th + 30)
    out = Image.new("RGB", (W, H), (244, 242, 238)); dr = ImageDraw.Draw(out)
    for i, (b, tiles, line) in enumerate(rows):
        y = i * (th + 30)
        dr.text((4, y + 2), f"{b}: skin over bone | muscle | fat (red = pokes through, full red = 4 px or more)  {line}", fill=(0, 0, 0))
        order = [(n, sd) for n in ("bone", "muscle", "fat") for sd in ("front", "back")]
        for j, key in enumerate(order):
            im = next(t[2] for t in tiles if (t[0], t[1]) == key)
            out.paste(im, (j * (tw + 4), y + 16))
            dr.text((j * (tw + 4) + 4, y + 18), f"{key[0]} {key[1]}", fill=(60, 60, 60))
    path = s.CAPT / f"2026-11-17_skincheck-{tag}.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
