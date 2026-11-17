"""How much the pieces of the trunk stack go into each other (2026-11-17, Virginie: 'parfois tu fonds deux muscles l'un
dans l'autre, à la place d'empiler proprement').

The Average stack (stack3d.build_male). Each displayed piece (muscle or bone) is a solid; for every pair that touches, the
volume they share, as a share of the smaller one, and the deepest point of one inside the other (px). Pieces of one muscle
(the four rectus blocks) are one piece here.

Board: Art/work/captures/2026-11-17_overlap.png (the ten worst muscle pairs, shared volume in red)
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python overlap.py [h]
"""
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import stack3d as s


def pieces(G, S):
    out = {}
    for name, layer, colour, sl, a in S.parts:
        if a is None or layer not in ("muscle", "bone"):
            continue
        key = re.sub(r" \d+$", "", name)
        if key not in out:
            out[key] = (layer, colour, np.zeros(G.shape, bool))
        out[key][2][sl] |= a < 0
    return out


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    G = s.Grid(h)
    S = s.build_male(G, s.Target("Male"))
    P = pieces(G, S)
    names = list(P)
    vol = {n: int(P[n][2].sum()) for n in names}
    rows = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            both = P[a][2] & P[b][2]
            n = int(both.sum())
            if n == 0:
                continue
            # deepest point of the shared part: its distance to the outside of the shared region
            depth = float(ndi.distance_transform_edt(both).max()) * h * 2.0
            rows.append((n / min(vol[a], vol[b]), n * h ** 3, depth, a, b, P[a][0], P[b][0]))
    rows.sort(reverse=True)
    mm = [r for r in rows if r[5] == "muscle" and r[6] == "muscle"]
    bm = [r for r in rows if {r[5], r[6]} == {"muscle", "bone"}]
    print(f"muscle-muscle pairs that share volume: {len(mm)}; muscle-bone: {len(bm)}")
    print("share of the smaller | shared px3 | thickness px | pair")
    for r in mm[:25]:
        print(f"  {100 * r[0]:5.1f} % | {r[1]:8.0f} | {r[2]:4.1f} | {r[3]}  x  {r[4]}")
    print("muscle-bone, worst 10:")
    for r in bm[:10]:
        print(f"  {100 * r[0]:5.1f} % | {r[1]:8.0f} | {r[2]:4.1f} | {r[3]}  x  {r[4]}")
    # board: the ten worst muscle pairs, the two pieces in their colours, the shared volume in red, front | side | back
    tiles = []
    for r in mm[:10]:
        a, b = r[3], r[4]
        own = np.zeros(G.shape, np.int16)
        own[P[a][2]] = 1; own[P[b][2]] = 2; own[P[a][2] & P[b][2]] = 3
        d = np.where(own > 0, -1.0, 1.0).astype(np.float32)
        d = ndi.gaussian_filter(d, 0.7)
        pal = np.array([[244, 242, 238], [190, 190, 186], [120, 160, 210], [220, 30, 30]], float)
        ims = [s.oblique(G, d, own, (pal,), ang, 0.7)[0] for ang in (0, 90, 180)]
        tiles.append((f"{100 * r[0]:.0f} % de {'l' if vol[a] < vol[b] else 'l'}a plus petite, {r[2]:.0f} px : {a}  x  {b}", ims))
    tw = max(sum(im.width for im in t[1]) for t in tiles) + 16; th = max(max(im.height for im in t[1]) for t in tiles) + 24
    cols = 2
    out = Image.new("RGB", (cols * tw, -(-len(tiles) // cols) * th + 24), (244, 242, 238)); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), "Muscles qui se pénètrent : gris = premier, bleu = second, rouge = volume commun. Face | côté | dos.",
            fill=(0, 0, 0), font=font)
    for j, (lab, ims) in enumerate(tiles):
        x0 = (j % cols) * tw; y0 = 24 + (j // cols) * th
        dr.text((x0 + 4, y0 + 2), lab, fill=(0, 0, 0), font=font)
        x = x0 + 2
        for im in ims:
            out.paste(im, (x, y0 + 20)); x += im.width + 4
    path = s.CAPT / "2026-11-17_overlap.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
