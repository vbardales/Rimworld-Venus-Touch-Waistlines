"""Texture over relief, to see which drawn volumes the relief does not carry (Virginie 2026-11-08).
Columns per facing: texture | relief lit (relief3d.height) | texture 50 % over the relief, drawn lines in red.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python overlay3d.py [Body ...]
Boards: Art/work/captures/2026-11-08_overlay-<Body>.png (three facings), 2026-11-08_overlay-south-all.png"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, explain5b as e5
import relief3d as r3

N = c1.N
BODIES = ["Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female"]


def tri(body):
    imgs = r3.views(body, False)
    M = {f: r3.silhouette(imgs[f]) for f in imgs}
    out = {}
    for f in ("south", "east", "north"):
        s, d, names = e5.named_pairs(body, f)
        pts = {n: tuple(s[i]) for i, n in enumerate(names)}
        h = r3.height(f, M, pts, c1.lum(imgs[f]))
        lit = r3.lit(h, M[f])
        tex = imgs[f]
        a = M[f]
        base = np.full((N, N, 3), 0.92, np.float32)
        base[a] = lit[..., :3][a]
        t = np.full((N, N, 3), 0.92, np.float32)
        ta = tex[..., 3] > 0.5
        t[ta] = tex[..., :3][ta]
        ov = base.copy()
        ov[ta] = 0.5 * base[ta] + 0.5 * tex[..., :3][ta]
        lines = ndi.binary_dilation((c1.lum(tex) < 0.45) & a)
        ov[lines] = (0.85, 0.1, 0.1)
        out[f] = (t, base, ov, a | ta)
    return out


def tile(arr, box):
    im = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8)).crop(box)
    return im


def main():
    names = [a for a in sys.argv[1:] if a in BODIES] or BODIES
    font = ImageFont.load_default(size=16)
    south = []
    for b in names:
        print(b, flush=True)
        o = tri(b)
        m = o["south"][3] | o["east"][3] | o["north"][3]
        ys, xs = np.nonzero(m)
        box = (max(0, xs.min() - 10), max(0, ys.min() - 10), min(N, xs.max() + 10), min(N, ys.max() + 10))
        w, h = box[2] - box[0], box[3] - box[1]
        im = Image.new("RGB", (3 * w + 40, 3 * h + 60), (235, 235, 230))
        d = ImageDraw.Draw(im)
        d.text((10, 8), f"{b}: texture | relief lit | texture 50 % over relief (red = drawn lines)", fill=(0, 0, 0), font=font)
        for r, f in enumerate(("south", "east", "north")):
            for c in range(3):
                im.paste(tile(o[f][c], box), (10 + c * (w + 10), 30 + r * (h + 10)))
        im.save(rf"{c1.CAPT}\2026-11-08_overlay-{b}.png")
        south.append((b, tile(o["south"][2], box)))
    if len(south) > 1:
        w = max(t.width for _, t in south); h = max(t.height for _, t in south)
        im = Image.new("RGB", (4 * (w + 10) + 10, 2 * (h + 30) + 10), (235, 235, 230))
        d = ImageDraw.Draw(im)
        for i, (b, t) in enumerate(south):
            x = 10 + (i % 4) * (w + 10); y = 10 + (i // 4) * (h + 30)
            d.text((x, y), b, fill=(0, 0, 0), font=font); im.paste(t, (x, y + 20))
        im.save(rf"{c1.CAPT}\2026-11-08_overlay-south-all.png")
    print("ok")


if __name__ == "__main__":
    main()
