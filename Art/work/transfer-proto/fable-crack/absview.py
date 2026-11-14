"""The abdomen of the stack, front skin, depth in bands of 1 px, rows 318-404 and x 0-60 (2026-11-14, abs factor of TYPES).
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python absview.py [Male Hulk]
Board: Art/work/captures/2026-11-14_abs-<tag>.png (tag = argv 'tag=...'), one panel per body, mirrored, plus the ripple along x=8."""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import stack3d as s

SC = 6
R0, R1, XM = 318, 404, 60


def panel(body, font):
    K = s.make(body, 1.0, ghost=False)
    G = K["G"]
    zf = s.last_cross(K["d"], 2, G.z)
    i0, i1 = int(np.argmin(np.abs(G.r - R0))), int(np.argmin(np.abs(G.r - R1)))
    j1 = int(np.argmin(np.abs(G.x - XM)))
    z = zf[i0:i1 + 1, :j1 + 1]
    hp = z - ndi.uniform_filter(z, size=(15, 15), mode="nearest")        # relief on top of the smooth belly
    v = np.clip(hp / 2.5, -1, 1)                                           # +-2.5 px
    rgb = np.zeros(v.shape + (3,), np.float32)
    rgb[..., 0] = 0.5 + 0.5 * np.clip(v, 0, 1) - 0.5 * np.clip(-v, 0, 1)
    rgb[..., 1] = 0.5 + 0.5 * np.clip(v, 0, 1) - 0.5 * np.clip(-v, 0, 1)
    rgb[..., 2] = 0.5 + 0.5 * np.clip(v, 0, 1) + 0.0 * v - 0.2 * np.clip(-v, 0, 1)
    full = np.concatenate([rgb[:, :0:-1], rgb], axis=1)
    im = Image.fromarray((np.clip(full, 0, 1) * 255).astype(np.uint8)).resize((full.shape[1] * SC, full.shape[0] * SC), Image.NEAREST)
    col = zf[i0:i1 + 1, 8]
    rip = col - ndi.uniform_filter1d(col, 13, mode="nearest")
    ImageDraw.Draw(im).text((6, 4), f"{body}: front skin relief (light = proud, dark = hollow, +-2.5 px), x 0..{XM}, rows {R0}..{R1}", fill=(255, 0, 0), font=font)
    ImageDraw.Draw(im).text((6, 22), f"ripple along x=8: {np.nanmax(rip) - np.nanmin(rip):.2f} px peak to peak", fill=(255, 0, 0), font=font)
    return im


def main():
    names = [a for a in sys.argv[1:] if a in s.TYPES] or ["Male", "Hulk"]
    tag = next((a[4:] for a in sys.argv[1:] if a.startswith("tag=")), "after")
    if "abs1" in sys.argv:                                                  # the old drawing, for the comparison
        for b in names:
            s.TYPES[b] = dict(s.TYPES[b], abs=1.0)
    font = ImageFont.load_default(size=14)
    ims = [panel(b, font) for b in names]
    W = sum(i.width for i in ims) + 10 * (len(ims) + 1)
    board = Image.new("RGB", (W, ims[0].height + 20), (235, 235, 230))
    x = 10
    for i in ims:
        board.paste(i, (x, 10)); x += i.width + 10
    p = rf"{s.CAPT}\2026-11-14_abs-{tag}.png"
    board.save(p); print(p)


if __name__ == "__main__":
    main()
