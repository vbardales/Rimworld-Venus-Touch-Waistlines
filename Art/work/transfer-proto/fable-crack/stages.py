"""How a prototype is reached, stage by stage (2026-11-17, Virginie: 'montre-moi par étape comment tu arrives là').

The same steps as proto.proto_board, each drawn front | side | back in plain grey:
  1 the lean stack (bones and settled muscles) in the Male frame;
  WDI-M then fits that stack beneath the WDI Male silhouette and measures its existing soft tissue.  It deliberately
  does not call solve_comp(), which would fill the remaining interior by dilating muscles.
  4 the smooth envelope of 3 (closing, smoothing), with the muscles thickened and the bones counted for the composition;
  5 plus the global fat layer;
  6 plus the pads;
  7 the widths brought to the prototype's ratios (M only);
  8 plus the shape edits: rib cage stretched, pectorals raised, buttocks reworked (M only).

Board: Art/work/captures/2026-11-17_stages-<preset>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python stages.py [WDI-M|M|M1] [h]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import proto as p
import stack3d as s

BG = (244, 242, 238)


def views(G, d):
    own = np.ones(G.shape, np.int16)
    pal = np.array([BG, (214, 212, 206), (214, 212, 206)], float)
    out = []
    for a in (0, 90, 180):
        arr = np.asarray(s.oblique(G, d, own, (pal,), a, 0.7)[0]).copy()
        arr[(np.abs(arr.astype(int) - np.array([226, 226, 222])).sum(-1) < 4)] = BG
        out.append(Image.fromarray(arr))
    return out


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "M"
    h = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
    p.use_env(name)
    K, F = p.make_body(name, h)
    G, T, G0, S = K["G"], K["T"], K["G0"], K["S"]
    stages = [("le buste maigre : os et muscles empilés, cadre Male", G0, S.d.copy())]
    if p.WDI_FIT[name]:
        stages.append(("posé sur la silhouette source WDI (rangs repères, affine par rang, ajustement fin)", G, F["lean"]))
        comp = p.composition(F, K["d"], G.h)
        stages.append((f"enveloppe sous-cutanée WDI lissée ; masses mesurées : gras {comp['fat'] + comp['fat pads']:.1f} %, "
                       f"muscles explicites {comp['muscle']:.1f} %, os solides {comp['bone']:.1f} %", G, K["d"]))
    else:
        d00 = K["d"]
        zc = np.interp(G.r, T.rows, T.zc)
        grow, t, near, comp, ref, m, c = p.solve_comp(G, F, d00, zc, p.COMP[name])
        stages.append((f"l'enveloppe lisse (bouchage {p.ENV_CLOSE:.0f} px, lissage {p.ENV_SMOOTH:.0f} px) ; dedans, muscles "
                       f"épaissis de {m:.1f} px, os comptés à {100 * c:.0f} % de leur volume", G, grow(0.0, 0.0)))
        stages.append((f"+ la couche de gras globale : {t:.1f} px ({100 * t / ref:.1f} % de la demi-largeur d'épaules)", G, grow(t, 0.0)))
        fin = grow(t)
        stages.append((f"+ les pads (x{p.PAD_GAIN} sur {p.PAD_REACH:.0f} px) : gras {comp['fat'] + comp['fat pads']:.1f} %, "
                       f"muscle {comp['muscle']:.1f} %, os {comp['bone']:.1f} %", G, fin))
        tgt = p.PROTO[name]
        if tgt is not None:
            rows, k = p.width_scale(G, fin, tgt)
            Go = s.Grid(G.h, x1=float(G.x[-1]) * max(max(k), 1.0) + 4.0, r0=float(G.r[0]), r1=float(G.r[-1]) + 8.0,
                        z0=float(G.z[0]) - 8.0, z1=float(G.z[-1]))
            for _ in range(10):
                d, = p.shaped(Go, G, [(fin, 1)], rows, k, (T.rows, T.zc), p.SHAPE[name])
                xm = np.nan_to_num(np.nanmax(s.last_cross(d, 1, Go.x), axis=1))
                hw = lambda r: float(np.interp(r, Go.r, xm))
                sh = hw(p.WROWS["shoulders"])
                k = [kk * tgt[n] * sh / hw(p.WROWS[n]) for kk, n in zip(k, p.WROWS)]
            flat = {key: 0.0 for key in p.SHAPE[name]}
            d7, = p.shaped(Go, G, [(fin, 1)], rows, k, (T.rows, T.zc), flat)
            stages.append((f"largeurs ramenées aux rapports de {name} : " + " / ".join(f"{tgt[n]:g}" for n in p.WROWS), Go, d7))
            d8, = p.shaped(Go, G, [(fin, 1)], rows, k, (T.rows, T.zc), p.SHAPE[name])
            sh_ = p.SHAPE[name]
            stages.append((f"+ cage étirée de {sh_['cage']:.0f} px, pectoraux remontés de {sh_['pecs']:.0f} px, fessiers "
                           f"repris de {sh_['glutes']:.0f} px : {name} fini", Go, d8))
    tiles = []
    for i_, (lab, Gx, d) in enumerate(stages, 1):
        tiles.append((f"{i_}. {lab}", views(Gx, d)))
        print(lab, flush=True)
    tw = max(sum(im.width for im in t_[1]) for t_ in tiles) + 16
    th = max(max(im.height for im in t_[1]) for t_ in tiles) + 26
    cols = 2
    out = Image.new("RGB", (cols * tw, -(-len(tiles) // cols) * th + 26), BG); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), f"{name} : comment on arrive au buste fini, étape par étape. Face | côté | dos.", fill=(0, 0, 0), font=font)
    for j, (lab, ims) in enumerate(tiles):
        x0 = (j % cols) * tw; y0 = 26 + (j // cols) * th
        dr.text((x0 + 4, y0 + 2), lab, fill=(0, 0, 0), font=font)
        x = x0 + 2
        for im in ims:
            out.paste(im, (x, y0 + 22)); x += im.width + 4
    path = s.CAPT / f"2026-11-17_stages-{name}.png"
    out.save(path)
    print(path)


if __name__ == "__main__":
    main()
