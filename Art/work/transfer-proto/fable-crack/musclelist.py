"""Every muscle of the trunk stack, one tile each (2026-11-17, Virginie: 'montre et nomme-moi tous les muscles présents').

The Average lean stack (stack3d.build_male, Male frame, no fit to WDI). Each tile: the muscle alone in colour over the
whole lean stack in pale grey, seen from the front, the side (east) and the back. Parts that make one muscle (the four
blocks of the rectus, the four digitations of the serratus) share a tile.

Board: Art/work/captures/2026-11-17_muscles.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python musclelist.py [h]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stack3d as s

# stack name prefix -> French name shown on the board
NAMES = [
    ("trapezius (upper)", "trapèze, partie haute"),
    ("trapezius (middle, lower)", "trapèze, parties moyenne et basse"),
    ("serratus", "dentelé antérieur (4 digitations)"),
    ("pectoralis major", "grand pectoral"),
    ("rectus abdominis", "grand droit de l'abdomen (4 blocs)"),
    ("external oblique", "oblique externe"),
    ("erector spinae", "érecteurs du rachis"),
    ("infraspinatus, teres, rhomboid", "infra-épineux, grand et petit ronds, rhomboïdes"),
    ("latissimus dorsi", "grand dorsal"),
    ("thoracolumbar fascia, multifidus", "fascia thoraco-lombaire, multifide"),
    ("gluteus medius", "moyen fessier"),
    ("gluteus maximus", "grand fessier"),
    ("tensor fasciae latae, hip flexors", "tenseur du fascia lata, fléchisseurs de hanche"),
    ("thigh stump", "moignon de cuisse (quadriceps, adducteurs, ischio-jambiers)"),
]
BG = np.array([226, 226, 222])


def views(G, d, colour):
    own = np.ones(G.shape, np.int16)
    pal = np.array([[236.0] * 3, colour, colour], float)
    return [np.asarray(s.oblique(G, d, own, (pal,), a, 1.0)[0]) for a in (0, 90, 180)]


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    G = s.Grid(h)
    S = s.build_male(G, s.Target("Male"))
    base = views(G, S.d, (250, 250, 248))
    tiles = []
    for i, (key, fr) in enumerate(NAMES, 1):
        f = G.full(); col = None
        for name, layer, colour, sl, a in S.parts:
            if layer == "muscle" and a is not None and name.startswith(key):
                f[sl] = np.minimum(f[sl], a); col = colour
        if col is None:
            continue
        ims = []
        for b, m in zip(base, views(G, f, col)):
            out = np.where((np.abs(b.astype(int) - BG).sum(-1) < 4)[..., None], BG, 0.55 * b + 0.45 * 236).astype(np.uint8)
            hit = np.abs(m.astype(int) - BG).sum(-1) >= 4
            out[hit] = m[hit]
            ims.append(Image.fromarray(out))
        tiles.append((f"{i}. {fr}", ims))
        print(i, key, flush=True)
    tw = sum(im.width for im in tiles[0][1]) + 12; th = max(im.height for im in tiles[0][1]) + 22
    cols = 3
    W = cols * tw; H = -(-len(tiles) // cols) * th + 22
    out = Image.new("RGB", (W, H), (244, 242, 238)); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), "Muscles du buste (Average, sans membres fantômes) : face | côté | dos. Gris pâle = le reste du buste. Vue en transparence : le muscle est montré même quand il est derrière.", fill=(0, 0, 0), font=font)
    for j, (lab, ims) in enumerate(tiles):
        x0 = (j % cols) * tw; y0 = 22 + (j // cols) * th
        dr.text((x0 + 4, y0 + 2), lab, fill=(0, 0, 0), font=font)
        x = x0 + 2
        for im in ims:
            out.paste(im, (x, y0 + 18)); x += im.width + 4
    path = s.CAPT / "2026-11-17_muscles.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
