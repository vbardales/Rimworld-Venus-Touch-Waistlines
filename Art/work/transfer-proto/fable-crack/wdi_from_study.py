"""Stand-in WDI body textures, rebuilt from the study boards of 2026-11-03 (cloud session 2026-11-08).
The cloud container has no Steam folder: the WDI bodies (Naked_<Body>_<facing>.png, workshop 3527486510) are not in
any branch (Art/work keeps WDI-derived art out of git). What IS on the cloud-work branch: the study boards
Art/work/captures/2026-11-03_points/[east-|north-]1-wdi-<Body>.png, which show each WDI body at 8x (1024 px) with
her points and labels drawn over it, and the E_<Body>_<facing>.png masks (the WDI silhouette 4 px inset, 512 px).
This script registers the board on the E mask (scale exactly 1/2, translation by cross-correlation of the outline),
takes the colours from the board, paints out the coloured marks (dots, label boxes, the dashed midline: anything
saturated, the body is grey), re-blackens the outline band, and writes a 512 px RGBA stand-in to
<repo>/../ws/Bodies/Naked_<Body>_<facing>.png, where run_linux.py sends the Windows WS path.
On Virginie's machine the real textures are read instead: nothing here changes the pipeline's inputs.
Board: Art/work/captures/2026-11-08_wdi-standin.png (stand-in | marks that were painted out | E mask)
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python wdi_from_study.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.signal import fftconvolve
from skimage.restoration import inpaint_biharmonic

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
REPO = os.path.abspath(os.path.join(WORK, "..", ".."))
WS = os.path.join(os.path.dirname(REPO), "ws")
BODIES = ["Male", "Female", "Thin", "Fat", "Hulk", "Thin_Female", "Fat_Female", "Hulk_Female"]
PRE = {"south": "", "east": "east-", "north": "north-"}
N = 512
BEIGE = np.array([200, 196, 182])
EDGE = 4            # E is the silhouette inset by this much (px at 512)
BAND = 9            # the outline band re-blackened inside the outer edge (the WDI stroke is 10 to 12 px)


def rebuild(body, f):
    E = np.array(Image.open(os.path.join(WORK, "transfer-proto", f"E_{body}_{f}.png")))[..., 3] > 127
    yy, xx = np.mgrid[-EDGE:EDGE + 1, -EDGE:EDGE + 1]
    outer = ndi.binary_dilation(E, structure=(xx ** 2 + yy ** 2) <= EDGE ** 2)
    board = np.array(Image.open(os.path.join(WORK, "captures", "2026-11-03_points", f"{PRE[f]}1-wdi-{body}.png")).convert("RGB")).astype(np.float32)
    # the board (1060 x 862) is smaller than the 1024 px texture window: padded with its background
    P = 2 * N
    board = np.pad(board, ((P, P), (P, P), (0, 0)), constant_values=0) + np.pad(np.zeros(board.shape[:2] + (3,), np.float32), ((P, P), (P, P), (0, 0)), constant_values=1) * BEIGE
    sat = board.max(axis=2) - board.min(axis=2)
    dark = (board.max(axis=2) < 60) & (sat < 25)
    # registration: the board is the texture at 8x of 128 = 2x of 512; the offset by correlating the board's dark
    # pixels with the outline band of the E-based silhouette, upsampled x2
    ring = outer & ~ndi.binary_erosion(outer, iterations=BAND)
    ring2 = np.kron(ring.astype(np.float32), np.ones((2, 2), np.float32))
    corr = fftconvolve(dark.astype(np.float32), ring2[::-1, ::-1], mode="valid")
    oy, ox = np.unravel_index(np.argmax(corr), corr.shape)
    crop = board[oy:oy + 2 * N, ox:ox + 2 * N]
    satc = sat[oy:oy + 2 * N, ox:ox + 2 * N]
    # marks: anything saturated (the body is grey; the nipples' pale pink goes with them), grown by 3 px at 1024
    # (the dots have a dark rim, unsaturated: grown by 7 px at 1024 so the rim goes with the dot)
    marks = satc > 28
    marks = ndi.binary_dilation(marks, iterations=7)
    # to 512 (box filter), the mark mask by 'any'
    rgb = crop.reshape(N, 2, N, 2, 3).mean(axis=(1, 3))
    mk = marks.reshape(N, 2, N, 2).any(axis=(1, 3))
    g = rgb.mean(axis=2) / 255.0
    # the outline band: black, unconditionally (grey label boxes sit on it: 'leftmost', 'rightmost', 'top')
    g[ring] = 4 / 255.0
    inside = outer & ~ring
    holes = mk & inside
    if holes.any():
        # inpaint over the whole filled silhouette (biharmonic), outside pixels fixed at the current grey
        g = inpaint_biharmonic(np.where(outer, g, 0.9), holes & outer)
    g = np.clip(g, 0, 1)
    out = np.zeros((N, N, 4), np.float32)
    out[..., :3] = g[..., None]
    out[..., 3] = outer
    # the stroke itself keeps the texture's own pure black (4,4,4 as crack.OUTLINE_RGB)
    out[ring, :3] = 4 / 255.0
    return out, holes & outer, E, (oy, ox)


def main():
    os.makedirs(os.path.join(WS, "Bodies"), exist_ok=True)
    font = ImageFont.load_default(size=16)
    tiles = []
    for body in BODIES:
        row = []
        for f in ("south", "east", "north"):
            out, holes, E, off = rebuild(body, f)
            Image.fromarray((out * 255).round().astype(np.uint8), "RGBA").save(os.path.join(WS, "Bodies", f"Naked_{body}_{f}.png"))
            ys, xs = np.nonzero(out[..., 3] > 0)
            box = (max(0, xs.min() - 8), max(0, ys.min() - 8), min(N, xs.max() + 8), min(N, ys.max() + 8))
            t = Image.new("RGB", (N, N), (80, 100, 80)); t.paste(Image.fromarray((out * 255).astype(np.uint8), "RGBA"), (0, 0), Image.fromarray((out[..., 3] * 255).astype(np.uint8)))
            m = (out * 255).astype(np.uint8).copy(); m[holes] = (255, 40, 40, 255)
            t2 = Image.new("RGB", (N, N), (80, 100, 80)); t2.paste(Image.fromarray(m, "RGBA"), (0, 0), Image.fromarray(m[..., 3]))
            d = ImageDraw.Draw(t); d.text((box[0] + 2, box[1] + 2), f"{body} {f} off {off} holes {int(holes.sum())}", fill=(255, 255, 0), font=font)
            row += [t.crop(box), t2.crop(box)]
            print(body, f, "offset", off, "painted-out px", int(holes.sum()))
        tiles.append(row)
    W = max(sum(t.width + 6 for t in r) for r in tiles) + 20; H = sum(max(t.height for t in r) + 6 for r in tiles) + 40
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), "WDI stand-in bodies rebuilt from the 2026-11-03 study boards (cloud, no Steam folder): stand-in | the marks painted out (red). Per body: south, east, north.", fill=(0, 0, 0), font=font)
    y = 34
    for r in tiles:
        x = 10
        for t in r:
            im.paste(t, (x, y)); x += t.width + 6
        y += max(t.height for t in r) + 6
    out = os.path.join(WORK, "captures", "2026-11-08_wdi-standin.png"); im.save(out); print(out)


if __name__ == "__main__":
    main()
