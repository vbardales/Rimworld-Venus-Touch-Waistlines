"""What step 5 of round 8 does, in pictures (2026-11-07, Virginie: 'je ne comprends pas l'étape 5').
Per case: (A) her points on the vanilla body, (B) the same points on the WDI body, (C) the edge pairs the warp adds,
(D) the warp with her points only, (E) the warp with her points plus the edge pairs (= step 5 of round 8).
A grid drawn on the vanilla garment shows how the space is bent. Board: Art/work/captures/2026-11-07_step5-explained.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python explain5.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import crack as c1, crack2, crack8

N = c1.N; CAPT = c1.CAPT; CORE = c1.CORE; VAN = c1.VAN
CASES = [("Fat_Female", "south", "ShirtButton"), ("Fat_Female", "south", "CorsetRoyal"), ("Fat_Female", "south", "FlakVest")]
BG = (78, 98, 78, 255)


def x4(img):
    return np.repeat(np.repeat(img, 4, axis=0), 4, axis=1)


def rgba(arr):
    return c1.to_pil(np.clip(arr, 0, 1))


def on_bg(img):
    b = Image.new("RGBA", (N, N), BG); b.alpha_composite(img); return b


def grid_layer():
    """a red grid every 8 vanilla pixels, as a 512 RGBA layer in vanilla x4 space"""
    g = np.zeros((N, N, 4), np.float32)
    for k in range(0, N, 32):
        g[k:k + 2, :, :] = (0.9, 0.1, 0.1, 1.0); g[:, k:k + 2, :] = (0.9, 0.1, 0.1, 1.0)
    return g


def warp(img512, U, V):
    coords = [V * 4 - 0.5, U * 4 - 0.5]
    return np.stack([ndi.map_coordinates(img512[..., k], coords, order=1, mode="constant", cval=0.0) for k in range(4)], axis=-1)


def case(body, facing, g):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{g}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg)
    s_out = int(c1.edge_run(va, vl, ~va))
    drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
    U0, V0, shade, body_a, cal = crack2.prep(body, facing, donor)
    d = int(round(max(0.0, cal["d"])))
    S = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    src, dst = c1.landmarks(body, facing)            # src = WDI (512), dst = vanilla (128)
    tps0 = c1.TPS(src, dst)
    outer_v = crack8.contour_pts(ndi.binary_fill_holes(ndi.binary_erosion(va, iterations=max(1, s_out))))
    S_pts = crack8.contour_pts(S)[::8]
    _, j = cKDTree(outer_v).query(tps0(S_pts)); q = outer_v[j]
    tps = c1.TPS(np.r_[src, S_pts], np.r_[dst, q], lam=4000.0)
    G4 = crack8.upscale4(Vg, crack8.UPSCALE)
    grid = grid_layer() * x4(va.astype(np.float32))[..., None]
    garm_grid = G4.copy(); m = grid[..., 3] > 0; garm_grid[m] = grid[m]
    panels = []
    # A: vanilla body + garment + her points (vanilla side)
    vt = Vb.copy(); vt[..., :3] = vt[..., :3] * 0.6 + 0.4
    a = rgba(x4(vt)); a.alpha_composite(rgba(garm_grid)); a = on_bg(a); dr = ImageDraw.Draw(a)
    for (vx, vy) in dst:
        dr.ellipse((vx * 4 - 7, vy * 4 - 7, vx * 4 + 7, vy * 4 + 7), fill=(255, 220, 0), outline=(0, 0, 0))
    panels.append(("A  vanilla: your points (yellow) and a red grid drawn on the garment", a))
    # B: WDI body + her points (WDI side), arrows from the vanilla position
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.85, 0.85, 0.85, 1); wb[S & ~body_a] = (0.95, 0.75, 0.75, 1)
    b = on_bg(rgba(wb)); dr = ImageDraw.Draw(b)
    for (wx, wy), (vx, vy) in zip(src, dst):
        dr.line((vx * 4, vy * 4, wx, wy), fill=(255, 220, 0), width=2)
        dr.ellipse((wx - 7, wy - 7, wx + 7, wy + 7), fill=(255, 220, 0), outline=(0, 0, 0))
    panels.append(("B  WDI body: the same points; the line shows where each one comes from", b))
    # C: edge pairs: each blue dot on the WDI shape is tied to the nearest garment edge (white dot)
    c = rgba(x4(vt)); c.alpha_composite(rgba(G4)); c = on_bg(c)
    sil = np.zeros((N, N, 4), np.float32); edge = S & ~ndi.binary_erosion(S, iterations=3); sil[edge] = (0.2, 0.5, 1, 1)
    c.alpha_composite(rgba(sil)); dr = ImageDraw.Draw(c)
    for (sx, sy), (qx, qy) in zip(S_pts, q):
        dr.line((sx, sy, qx * 4, qy * 4), fill=(80, 160, 255), width=2)
        dr.ellipse((qx * 4 - 4, qy * 4 - 4, qx * 4 + 4, qy * 4 + 4), fill=(255, 255, 255), outline=(0, 0, 0))
    panels.append(("C  added by the warp: every blue point of the WDI edge pulls the nearest garment edge (white) to it", c))
    # D and E
    for title, t in (("D  warp with your points only", tps0), ("E  warp with your points + the edge pulls = step 5", tps)):
        U, V = c1.warp_field(t)
        w = warp(garm_grid, U, V)
        im = rgba(wb * np.array([1, 1, 1, 0.35])); im.alpha_composite(rgba(w)); im = on_bg(im)
        panels.append((title, im))
    return panels


def main():
    font = ImageFont.load_default(size=14); fontb = ImageFont.load_default(size=18)
    T = 360; pad = 8; left = 140; top = 46; head = 40
    rows = [(f"{g}\n{b}\n{f}", case(b, f, g)) for b, f, g in CASES]
    im = Image.new("RGB", (left + 5 * (T + pad), top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Step 5 explained: the warp moves each pixel of the vanilla garment to the WDI body. Grey = WDI body, pink = its margin.", fill=(0, 0, 0), font=fontb)
    for r, (label, panels) in enumerate(rows):
        y = top + r * (T + head + pad)
        dr.text((8, y + head), label, fill=(0, 0, 0), font=fontb)
        for j, (title, p) in enumerate(panels):
            x = left + j * (T + pad)
            words, line, lines = title.split(), "", []
            for w in words:
                if len(line) + len(w) > 46:
                    lines.append(line); line = w
                else:
                    line = (line + " " + w).strip()
            lines.append(line)
            dr.text((x, y), "\n".join(lines[:2]), fill=(0, 0, 0), font=font)
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (x, y + head))
    out = rf"{CAPT}\2026-11-07_step5-explained.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
