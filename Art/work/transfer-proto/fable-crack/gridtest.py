"""A grid dropped on the body: how the relief map deforms a regular grid (2026-11-14, Virginie: 'essaie déjà de voir la
déformation d'une grille', Male and Female first).

The vanilla body silhouette of each facing is covered with a grid (lines every 8 px of the 128 px vanilla frame, every
fourth line thicker, horizontals red and verticals blue so a fold or a stretch reads at once), prepared as a shirt is
(fp.prepared), then carried by reliefmap.build exactly as garment3d.py does: once with the relief read from the drawing,
once with the relief read from the 3D mesh. Nothing new in the mapping: only the garment is a grid.

Board: Art/work/captures/2026-11-14_grid-<Body>.png, per facing: WDI sprite with the grid from the drawing | with the
grid from the mesh | the area ratio of the map (stretch: green = 1, red = stretched, blue = squeezed) from the mesh.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python gridtest.py [Male Female]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import crack as c1, explain5b as e5, fullpass as fp, reliefmap as rm, relief3d as r3
import garment3d as g3
from reliefstudy import area_ratio

N = c1.N


def grid_garment(vb, f):
    """grid on the vanilla body silhouette, prepared as a shirt (the top of the body down to the hip row)"""
    Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{f}.png")
    a = Vb[..., 3] > 0.5
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = 0.93
    hor, ver = (yy % 8 == 0), (xx % 8 == 0)
    hot, vet = (yy % 32 == 0), (xx % 32 == 0)
    img[hor, :3] = (0.85, 0.15, 0.15); img[ver, :3] = (0.15, 0.25, 0.85)
    img[hot, :3] = (0.55, 0.0, 0.0); img[vet, :3] = (0.0, 0.05, 0.55)
    img[..., 3] = a.astype(np.float32)
    fp.G = g3.SHIRT
    return fp.prepared(img, Vb)


def stretch_colors(R):
    """area ratio of the map, per pixel: green near the median, red above (stretched), blue below (squeezed)"""
    r = area_ratio(R["Xs"], R["Ys"], R["mw"])
    inside = ndi.binary_erosion(R["mw"], iterations=2)
    med = float(np.nanmedian(r[inside]))
    r = np.where(np.isfinite(r) & (r > 1e-4), r, med)
    d = np.clip(np.log2(r / med), -1, 1)
    out = np.zeros((N, N, 4), np.float32)
    out[..., 0] = np.clip(d, 0, 1); out[..., 2] = np.clip(-d, 0, 1); out[..., 1] = 1 - np.abs(d)
    out[..., 3] = inside.astype(np.float32)
    return out


def one(body, font):
    imw = r3.views(body, False)
    M = {k: ndi.binary_fill_holes(imw[k][..., 3] > 0.5) for k in imw}
    mesh = g3.mesh_heights(body, M)
    vb = c1.VANILLA_OF[body]
    tiles = []
    for f in g3.FACINGS:
        Gp = grid_garment(vb, f)
        Rd, Rm = g3.build(body, f, None), g3.build(body, f, mesh)
        for lab, R in (("grid, relief from the drawing", Rd), ("grid, relief from the mesh", Rm)):
            W = e5.warp(Gp, R["U"], R["V"])
            t = e5.pil(imw[f]); t.alpha_composite(e5.pil(W))
            tiles.append((f"{f}: {lab}", e5.on_bg(t)))
        S = stretch_colors(Rm)
        base = e5.pil(imw[f])
        base.alpha_composite(e5.pil(S))
        tiles.append((f"{f}: stretch of the mesh map (red = stretched, blue = squeezed)", e5.on_bg(base)))
    ys, xs = np.nonzero(np.any([M[f] for f in g3.FACINGS], axis=0))
    box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(N, xs.max() + 6), min(N, ys.max() + 6))
    cr = []
    for lab, im in tiles:
        c = im.crop(box); c = c.resize((int(c.width * 1.5), int(c.height * 1.5)), Image.LANCZOS)
        ImageDraw.Draw(c).text((6, 4), lab, fill=(255, 255, 255), font=font); cr.append(c)
    tw, th = cr[0].size
    board = Image.new("RGB", (3 * tw + 40, 3 * th + 60), (235, 235, 230)); d = ImageDraw.Draw(board)
    d.text((10, 10), f"{body}: a grid (8 px lines, thick every 32) dropped on the body through the relief map, ease {rm.EASE} px. "
           f"Rows: south, east, north.", fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    for i, c in enumerate(cr):
        board.paste(c.convert("RGB"), (10 + (i % 3) * (tw + 10), 44 + (i // 3) * (th + 8)))
    out = rf"{c1.CAPT}\2026-11-14_grid-{body}.png"; board.save(out); print(out)


def main():
    bodies = [a for a in sys.argv[1:] if "=" not in a] or ["Male", "Female"]
    font = ImageFont.load_default(size=15)
    for b in bodies:
        one(b, font)


if __name__ == "__main__":
    main()
