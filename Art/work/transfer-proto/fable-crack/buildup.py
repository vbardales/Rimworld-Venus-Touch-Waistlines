"""The trunk built up one piece at a time (2026-11-17, Virginie: 'pars de la colonne vertébrale et ajoute 1 à 1 les os,
puis les muscles, des plus profonds aux moins profonds, sans la silhouette en gris derrière').

The Average stack (stack3d.build_male, Male frame). Each step shows what is built so far, front | side | back: the
pieces already there in their own colour, the piece added at this step in blue. No skin, no fat, no grey body behind.

Board: Art/work/captures/2026-11-17_buildup.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python buildup.py [h]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stack3d as s

# (stack part name prefix, French label), in the order they are added
BONES = [   # order of Virginie 2026-11-17
    ("femur", "fémurs proximaux (fait main)"),
    ("spine", "rachis de T1 au coccyx (BodyParts3D)"),
    ("rib cage", "cage thoracique et sternum (BodyParts3D)"),
    ("clavicle", "clavicules (BodyParts3D)"),
    ("scapula", "scapulas (BodyParts3D)"),
    ("hip bone", "os coxaux (BodyParts3D)"),
]
MUSCLES = [   # deepest first
    ("thoracolumbar fascia, multifidus", "multifide, fascia thoraco-lombaire"),
    ("erector spinae", "érecteurs du rachis"),
    ("tensor fasciae latae, hip flexors", "psoas, iliaque, tenseur du fascia lata"),
    ("gluteus medius", "moyen et petit fessiers"),
    ("serratus", "dentelé antérieur"),
    ("infraspinatus, teres, rhomboid", "rhomboïdes, supra- et infra-épineux, ronds"),
    ("rectus abdominis", "grand droit de l'abdomen"),
    ("external oblique", "oblique externe"),
    ("thigh stump, front (vastus medialis", "cuisse : vastes médial et intermédiaire"),
    ("thigh stump, inside", "cuisse : adducteurs"),
    ("thigh stump, back", "cuisse : ischio-jambiers"),
    ("thigh stump, front (vastus lateralis)", "cuisse : vaste latéral"),
    ("thigh stump, front (rectus femoris, vasti)", "cuisse : droit fémoral"),
    ("gluteus maximus", "grand fessier"),
    ("pectoralis major", "grand pectoral"),
    ("latissimus dorsi", "grand dorsal"),
    ("trapezius (middle, lower)", "trapèze, parties moyenne et basse"),
    ("trapezius (upper)", "trapèze, partie haute"),
]
NEW = (60, 150, 225)
BG = (244, 242, 238)


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    G = s.Grid(h)
    S = s.build_male(G, s.Target("Male"))
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
    cum = G.full(); owner = np.zeros(G.shape, np.int16)
    pal = np.zeros((len(steps) + 2, 3)); pal[0] = BG
    tiles = []
    for i, (lab, f, col) in enumerate(steps, 1):
        m = f < cum
        owner[m] = i; cum = np.minimum(cum, f)
        for k in range(1, i):
            pal[k] = steps[k - 1][2]
        pal[i] = NEW
        ims = [s.oblique(G, cum, owner, (pal.copy(),), a, 0.7)[0] for a in (0, 90, 180)]
        tiles.append((f"{i}. + {lab}", ims))
        print(i, lab, flush=True)
    tw = max(sum(im.width for im in t[1]) for t in tiles) + 16; th = max(max(im.height for im in t[1]) for t in tiles) + 24
    cols = 4
    out = Image.new("RGB", (cols * tw, -(-len(tiles) // cols) * th + 24), BG); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), "Le buste monté pièce par pièce : os, puis muscles du plus profond au plus superficiel. Face | côté | dos. En bleu : la pièce ajoutée.",
            fill=(0, 0, 0), font=font)
    for j, (lab, ims) in enumerate(tiles):
        x0 = (j % cols) * tw; y0 = 24 + (j // cols) * th
        dr.text((x0 + 4, y0 + 2), lab, fill=(0, 0, 0), font=font)
        x = x0 + 2
        for im in ims:
            arr = np.asarray(im).copy()
            arr[(np.abs(arr.astype(int) - np.array([226, 226, 222])).sum(-1) < 4)] = BG
            out.paste(Image.fromarray(arr), (x, y0 + 20)); x += im.width + 4
    path = s.CAPT / "2026-11-17_buildup.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
