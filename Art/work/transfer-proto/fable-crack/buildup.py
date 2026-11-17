"""The trunk built up one piece at a time (2026-11-17, Virginie: 'pars de la colonne vertébrale et ajoute 1 à 1 les os,
puis les muscles, des plus profonds aux moins profonds, sans la silhouette en gris derrière'; then: multifidus apart
under the erectors, the posterior thoracolumbar fascia a thin membrane over them, psoas and iliacus deep and early, the
tensor fasciae latae late and superficial; after the muscles the general subcutaneous layer, the fat pads, the skin).

The Average stack (stack3d.build_male, Male frame). Each step shows what is built so far, front | side | back: the
pieces already there in their own colour, the piece added at this step in blue. No grey body behind.
The fat: proto.solve_fat on this stack for 23 % of the mass (prototype M), first the global layer alone, then the pads.

Board: Art/work/captures/2026-11-17_buildup-<preset>.png (preset M1 or M of proto.py: its body type, its fat share)
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python buildup.py [h]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import proto
import stack3d as s

# (stack part name prefix, French label), in the order they are added
BONES = [   # order of Virginie 2026-11-17
    ("femur", "fémurs proximaux (BodyParts3D, coupés au plan du moignon)"),
    ("spine", "rachis de T1 au coccyx (BodyParts3D)"),
    ("rib cage", "cage thoracique et sternum (BodyParts3D)"),
    ("clavicle", "clavicules (BodyParts3D)"),
    ("scapula", "scapulas (BodyParts3D)"),
    ("hip bone", "os coxaux (BodyParts3D)"),
]
MUSCLES = s.MUSCLE_ORDER   # deepest first (stack3d: the order settle() stacks them in)
PRESET_NAME = {"M1": "lean / athlétique stylisé, cible de calcul : gras 14 % (12-16), muscles superficiels 100 %",
               "M": "moyen, cible de calcul : gras 23 %, muscles superficiels 80-90 % de M1, gras surtout bas-ventre, flancs, bas du dos"}
FAT = (238, 206, 140)
SKIN = (226, 184, 156)
SKIN_PX = 0.8          # the skin drawn as a thin layer over the fat
NEW = (60, 150, 225)
BG = (244, 242, 238)


def fat_steps(G, S, target):
    """(label, field, colour) for the general subcutaneous layer, the pads, the skin."""
    un = {"bone": G.full(), "muscle": G.full(), "fat": G.full()}
    for name, layer, colour, sl, a in S.parts:
        if a is not None and layer in un:
            un[layer][sl] = np.minimum(un[layer][sl], a)
    F = {"bone": un["bone"], "muscle": un["muscle"], "pads": un["fat"], "lean": S.d, "fat": G.full()}
    grow, t, near, comp, ref = proto.solve_fat(G, F, S.d, S.zc(G.r), target)
    print(f"fat {target} %: global layer {t:.2f} px; " + ", ".join(f"{k} {v:.1f} %" for k, v in comp.items()))
    return [(f"couche sous-cutanée générale ({100 * t / ref:.1f} % de la demi-largeur d'épaules)", grow(t, 0.0), FAT),
            ("pads de gras : flancs, bas-ventre, supra-pubien, sous-fessiers médiaux", grow(t), FAT),
            ("peau", grow(t) - SKIN_PX, SKIN)]


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    preset = sys.argv[2] if len(sys.argv) > 2 else "M"
    G = s.Grid(h)
    proto.use_env(preset)
    S = s.build_male(G, s.Target("Male"), ty=proto.TY[preset])
    steps = []
    for key, lab in BONES + MUSCLES:
        f = G.full(); col = None
        for name, layer, colour, sl, a in S.parts:
            if a is not None and layer in ("bone", "muscle") and name.startswith(key):
                f[sl] = np.minimum(f[sl], a); col = colour
        if col is None:
            print("absent:", key)
            continue
        steps.append((lab, f, col if col != s.BONE else (226, 218, 196)))
    steps += fat_steps(G, S, proto.COMP[preset]["fat"])
    cum = G.full(); owner = np.zeros(G.shape, np.int16)
    pal = np.zeros((len(steps) + 2, 3)); pal[0] = BG
    tiles = []
    for i, (lab, f, col) in enumerate(steps, 1):
        # the pads thicken a layer that is already there: they own only where they add a visible amount
        m = f < cum - (0.5 if lab.startswith("pads") else 0.0)
        owner[m] = i; cum = np.minimum(cum, f)
        for k in range(1, i):
            pal[k] = steps[k - 1][2]
        pal[i] = NEW
        ims = [s.oblique(G, cum, owner, (pal.copy(),), a, 0.7)[0] for a in (0, 90, 180)]
        tiles.append((f"{i}. + {lab}", ims))
        print(i, lab, flush=True)
    pal[len(steps)] = steps[-1][2]                               # the finished torso, the skin in its own colour
    tiles.append(("résultat : le buste fini", [s.oblique(G, cum, owner, (pal.copy(),), a, 0.7)[0] for a in (0, 90, 180)]))
    tw = max(sum(im.width for im in t[1]) for t in tiles) + 16; th = max(max(im.height for im in t[1]) for t in tiles) + 24
    cols = 4
    out = Image.new("RGB", (cols * tw, -(-len(tiles) // cols) * th + 24), BG); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), f"{preset} ({PRESET_NAME[preset]}) : le buste monté pièce par pièce, os, muscles du plus profond au plus superficiel, graisse, peau. "
                    "Face | côté | dos. En bleu : la pièce ajoutée.", fill=(0, 0, 0), font=font)
    for j, (lab, ims) in enumerate(tiles):
        x0 = (j % cols) * tw; y0 = 24 + (j // cols) * th
        dr.text((x0 + 4, y0 + 2), lab, fill=(0, 0, 0), font=font)
        x = x0 + 2
        for im in ims:
            arr = np.asarray(im).copy()
            arr[(np.abs(arr.astype(int) - np.array([226, 226, 222])).sum(-1) < 4)] = BG
            out.paste(Image.fromarray(arr), (x, y0 + 20)); x += im.width + 4
    path = s.CAPT / f"2026-11-17_buildup-{preset}.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
