"""Where the skin of the stack lies on what is under it, and where it hangs loose (2026-11-14, Virginie: 'un effet de gravité
pour mettre en évidence les endroits où la peau est bien collée vers l'intérieur par ce qui gêne, et ceux où elle est lâche').

Gravity here = the skin dropped inward along the depth axis until it meets something, front and back: for each (row, x)
the skin surface (K['d'], after the fit) is compared with the surface of what supports it: the fat solid (K['fat']: stack
plus fat), the lean stack (bones, viscera, muscles, named pads: frame-warped stack d) and the bones alone.
  loose gap  = skin - fat surface (px). 0 = the skin rests on the fat; large = it bridges a hollow, nothing holds it.
  rests on   = bone if the bone is within 1.5 px of the skin, else muscle/pad (lean within 1.5 px), else fat (fat within
               1 px), else loose.
A negative gap (the support pokes out of the skin) is shown in magenta: a model defect (skin cut by a muscle).
Board: Art/work/captures/2026-11-14_gravity-<tag>.png, one row per body: front rests-on | front loose gap | back rests-on | back loose gap.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python gapview.py [Male Hulk Female] [tag=x]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stack3d as s

SC = 2
KIND = {0: (30, 30, 34), 1: (236, 232, 214), 2: (196, 92, 84), 3: (240, 214, 150), 4: (60, 90, 200), 5: (230, 0, 230)}   # off, bone, muscle, fat, loose, support through the skin
NAMES = {1: "bone", 2: "muscle / pad", 3: "fat", 4: "loose (skin 1 px or more above the fat)", 5: "support pokes through the skin"}


def surfaces(K):
    G, G0, S, fr = K["G"], K["G0"], K["S"], K["frame"]
    lean = fr.warp(G0, S.d, 1, G)
    bone = fr.warp(G0, S.layer_d["bone"], 1, G)
    out = {}
    for side, outward in (("front", True), ("back", False)):
        sg = 1.0 if outward else -1.0
        z = {n: s.last_cross(f, 2, G.z, outward=outward) for n, f in (("skin", K["d"]), ("fat", K["fat"]), ("lean", lean), ("bone", bone))}
        out[side] = {n: sg * v for n, v in z.items()}                 # front = z, back = -z, so 'higher' is always 'further out'
    return out


def maps(K):
    sf = surfaces(K)
    res = {}
    for side in ("front", "back"):
        z = sf[side]
        skin = z["skin"]
        ok = np.isfinite(skin)
        gap = np.where(ok & np.isfinite(z["fat"]), skin - z["fat"], np.nan)
        kind = np.full(skin.shape, 4, np.int8)
        kind[np.isfinite(gap) & (gap <= 1.0)] = 3
        kind[np.isfinite(z["fat"]) & (np.abs(skin - z["fat"]) <= 1.0)] = 3
        kind[np.isfinite(z["lean"]) & (np.abs(skin - z["lean"]) <= 1.5)] = 2
        kind[np.isfinite(z["bone"]) & (np.abs(skin - z["bone"]) <= 1.5)] = 1
        kind[np.isfinite(gap) & (gap < -1.0)] = 5
        kind[np.isfinite(z["lean"]) & (np.abs(skin - z["lean"]) <= 1.5)] = 2
        kind[np.isfinite(z["bone"]) & (np.abs(skin - z["bone"]) <= 1.5)] = 1
        kind[~ok] = 0
        res[side] = (kind, gap)
    return res


def gap_rgb(gap, vmax=8.0):
    out = np.zeros(gap.shape + (3,), np.uint8)
    out[:] = KIND[0]
    g = np.nan_to_num(gap, nan=0.0)
    t = np.clip(g / vmax, 0, 1)
    out[..., 0] = (40 + 215 * t).astype(np.uint8)
    out[..., 1] = (80 + 120 * (1 - np.abs(t - 0.4) * 1.6).clip(0, 1)).astype(np.uint8)
    out[..., 2] = (220 * (1 - t)).astype(np.uint8)
    out[g < -0.7] = (230, 0, 230)
    out[~np.isfinite(gap)] = KIND[0]
    return out


def mirror(a):
    return np.concatenate([a[:, :0:-1], a], axis=1)


def panel(arr, label, font, extra=None):
    im = Image.fromarray(mirror(arr)).resize((mirror(arr).shape[1] * SC, mirror(arr).shape[0] * SC), Image.NEAREST)
    d = ImageDraw.Draw(im)
    d.text((6, 4), label, fill=(255, 255, 255), font=font)
    if extra:
        for i, t in enumerate(extra):
            d.text((6, 20 + 14 * i), t, fill=(255, 255, 255), font=font)
    return im


def main():
    names = [a for a in sys.argv[1:] if a in s.TYPES] or ["Male", "Hulk", "Female"]
    tag = next((a[4:] for a in sys.argv[1:] if a.startswith("tag=")), "t")
    font = ImageFont.load_default(size=13)
    rows = []
    for b in names:
        K = s.make(b, 1.0, ghost=False)
        M = maps(K)
        ims = []
        r0 = r1 = None
        for side in ("front", "back"):
            kind, gap = M[side]
            rr = np.nonzero((kind > 0).any(axis=1))[0]
            r0, r1 = (rr[0], rr[-1]) if r0 is None else (min(r0, rr[0]), max(r1, rr[-1]))
        for side in ("front", "back"):
            kind, gap = M[side]
            k = kind[r0:r1 + 1]; g = gap[r0:r1 + 1]
            inside = k > 0
            share = {n: 100.0 * float((k == n).sum()) / max(inside.sum(), 1) for n in (1, 2, 3, 4, 5)}
            loose = g[np.isfinite(g)]
            ex = [f"{NAMES[n]}: {share[n]:.0f} %" for n in (1, 2, 3, 4, 5)] + [f"gap > 3 px: {100 * (loose > 3).mean():.0f} %, > 6 px: {100 * (loose > 6).mean():.0f} %"]
            col = np.array([KIND[i] for i in range(6)], np.uint8)[k]
            ims.append(panel(col, f"{b} {side}: what the skin rests on", font, ex))
            ims.append(panel(gap_rgb(g), f"{b} {side}: loose gap, blue 0 px to red 8 px (magenta: support through the skin)", font))
            print(b, side, {NAMES[n]: round(share[n], 1) for n in share}, "gap>3:", round(100 * (loose > 3).mean(), 1), "gap<-0.7:", round(100 * (loose < -0.7).mean(), 2))
        rows.append(ims)
    tw, th = rows[0][0].size
    board = Image.new("RGB", (4 * tw + 50, len(rows) * (th + 10) + 10), (235, 235, 230))
    for i, ims in enumerate(rows):
        for j, im in enumerate(ims):
            board.paste(im, (10 + j * (tw + 10), 10 + i * (th + 10)))
    p = rf"{s.CAPT}\2026-11-14_gravity-{tag}.png"
    board.save(p); print(p)


if __name__ == "__main__":
    main()
