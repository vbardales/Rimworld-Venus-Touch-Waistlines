"""Step 5 in detail, current settings (2026-11-07): black edges peeled at step 4, warp driven by her points only.
Per case: (A) her numbered points on the vanilla body with a red grid on the garment, (B) the same points on the WDI
body with an arrow from where each one was on the vanilla body, (C) the grid alone after the warp (how the space is
bent), (D) the garment and grid after the warp, (E) the garment alone after the warp; then the legend of the points.
Board: Art/work/captures/2026-11-07_step5-detail.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python explain5b.py
"""
import re, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, crack2, crack8

N = c1.N; CAPT = c1.CAPT; CORE = c1.CORE; VAN = c1.VAN; POINTS = c1.POINTS
CASES = [("Fat_Female", "south", "ShirtButton"), ("Fat_Female", "east", "ShirtButton"), ("Female", "north", "ShirtButton"),
         ("Fat_Female", "south", "CorsetRoyal"), ("Hulk_Female", "south", "Jacket"), ("Fat_Female", "south", "FlakVest")]
BG = (78, 98, 78, 255)
LEGS = "legs" in sys.argv[1:]   # Virginie 2026-11-07: WDI bottom raised to the pink line to leave the legs
PROTO = c1.MOD + r"\Art\work\transfer-proto"
RECAL = "recal" in sys.argv[1:]         # every mark moved up so the highest sits on its silhouette top (both sides)
UNTUCKED = "untucked" in sys.argv[1:]   # with legs: the limit is the bottom of WDI's boxers (shirt worn out), not the waistband
WDI_TEX = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures"
LAM = 1.0 if "exact" in sys.argv[1:] else 2000.0   # TPS smoothing: 2000 = round 8, 1 = passes exactly through every point


def named_pairs(body, facing):
    """same pairs and order as crack.landmarks, with the point names"""
    pairs, names = {}, {}
    with open(rf"{POINTS}\delta-{facing}-points.txt", encoding="utf-8-sig") as f:
        for raw in f:
            p = raw.strip().split("|")
            if len(p) < 6 or not p[1].startswith(body + "/") or p[2] == "axis":
                continue
            m1 = re.search(r"vanilla (\d+),(\d+)", p[4]); m2 = re.search(r"WDI (\d+),(\d+)", p[5])
            if not (m1 and m2):
                continue
            k = ((int(m2.group(1)) + 0.5) * 4, (int(m2.group(2)) + 0.5) * 4)
            pairs.setdefault(k, []).append((int(m1.group(1)) + 0.5, int(m1.group(2)) + 0.5))
            names.setdefault(k, []).append(p[3])
    src = np.array(list(pairs.keys())); dst = np.array([np.mean(v, axis=0) for v in pairs.values()])
    return src, dst, [" / ".join(dict.fromkeys(names[k])) for k in pairs]


def x4(img):
    return np.repeat(np.repeat(img, 4, axis=0), 4, axis=1)


def pil(arr):
    return c1.to_pil(np.clip(arr, 0, 1))


def on_bg(img):
    b = Image.new("RGBA", (N, N), BG); b.alpha_composite(img); return b


def peeled(Vg):
    va = Vg[..., 3] > 0.5
    s_out = int(c1.edge_run(va, c1.lum(Vg), ~va))
    G4 = crack8.upscale4(Vg, crack8.UPSCALE)
    a = G4[..., 3] > 0.5; dark = c1.lum(G4) < crack8.PEEL_LUM
    for _ in range((min(4, max(1, s_out)) + 1) * 4):
        rim = a & ~ndi.binary_erosion(a); rm = rim & dark
        if not rm.any():
            break
        a &= ~rm
    out = G4.copy(); out[..., 3] = out[..., 3] * a
    return out


def warp(img512, U, V):
    coords = [V * 4 - 0.5, U * 4 - 0.5]
    return np.stack([ndi.map_coordinates(img512[..., k], coords, order=1, mode="constant", cval=0.0) for k in range(4)], axis=-1)


def dots(img, pts, font, scale=1.0):
    dr = ImageDraw.Draw(img)
    for i, (x, y) in enumerate(pts):
        x, y = x * scale, y * scale
        dr.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(255, 220, 0), outline=(0, 0, 0))
        dr.text((x - 6 if i < 9 else x - 9, y - 8), str(i + 1), fill=(0, 0, 0), font=font)


def recal(src, dst, body_a, van_a):
    """Virginie 2026-11-07 ('recaler tous les points'): every mark moves up so the highest one sits on the top of its
    silhouette, on both sides (vanilla points in 128 units, WDI points in 512 units)."""
    wtop = float(np.where(body_a.any(axis=1))[0].min()) + 0.5
    vtop = float(np.where(van_a.any(axis=1))[0].min()) + 0.5
    src = src.copy(); dst = dst.copy()
    src[:, 1] -= src[:, 1].min() - wtop
    dst[:, 1] -= dst[:, 1].min() - vtop
    return src, dst


def legs_room(src, names, body, facing, body_a):
    """Virginie 2026-11-07: the bottom of the WDI silhouette goes up to leave the legs. Below the start row y0 (the navel,
    else the belly front, else the hips), each WDI point is compressed so the body bottom of its column lands on the pink
    line (WDI underwear waistband, hemshift_<Body>_<facing>.pink.txt = D's reference line)."""
    pink = np.array([float(v) for v in open(rf"{PROTO}\hemshift_{body}_{facing}.pink.txt").read().strip().split(";")])
    if UNTUCKED:
        # untucked shirt (Virginie 2026-11-05 and 2026-11-07): the hem goes down to the bottom of WDI's boxers, never below;
        # where the boxers do not reach (the sides), the pink line stays the limit
        bx = c1.load(rf"{WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png", N)[..., 3] > 0.5
        line = pink.copy()
        for x in range(N):
            ys = np.where(bx[:, x])[0]
            if ys.size:
                line[x] = max(pink[x], float(ys.max()))
        pink = ndi.gaussian_filter1d(line, 3)
    pick = [i for i, n in enumerate(names) if "navel" in n] or [i for i, n in enumerate(names) if "belly" in n] \
        or [i for i, n in enumerate(names) if n.startswith("hip")]
    y0 = float(np.mean(src[pick, 1])) if pick else float(np.median(src[:, 1]))
    cols = np.where(body_a.any(axis=0))[0]
    y0 = min(y0, float(pink[cols].min()) - 24)        # the start row always stays above the pink line (north: hips at the waistband)
    rows = np.arange(N)
    out = src.copy()
    for i, (x, y) in enumerate(src):
        xi = int(np.clip(round(x), 0, N - 1))
        col = body_a[:, max(0, xi - 2):xi + 3].any(axis=1)
        if y <= y0 or not col.any():
            continue
        ybot = float(rows[col].max()); yp = float(pink[xi])
        if ybot <= y0 + 1 or yp <= y0:
            continue
        out[i, 1] = y0 + (y - y0) * (yp - y0) / (ybot - y0)
    return out, pink, y0


def case(body, facing, g, font):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{g}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
    _, _, _, body_a, cal = crack2.prep(body, facing, donor)
    src, dst, names = named_pairs(body, facing)
    if RECAL:
        src, dst = recal(src, dst, body_a, Vb[..., 3] > 0.5)
    src0 = src.copy(); pink = None; y0 = None
    if LEGS:
        src, pink, y0 = legs_room(src, names, body, facing, body_a)
    U, V = c1.warp_field(c1.TPS(src, dst, lam=LAM))
    G = peeled(Vg)
    grid = np.zeros((N, N, 4), np.float32)
    for k in range(0, N, 32):
        grid[k:k + 2, :] = (0.9, 0.1, 0.1, 1); grid[:, k:k + 2] = (0.9, 0.1, 0.1, 1)
    vbody = x4(Vb); vbody[..., :3] = vbody[..., :3] * 0.5 + 0.45
    wbody = np.zeros((N, N, 4), np.float32); wbody[body_a] = (0.82, 0.82, 0.82, 1)
    if pink is not None:                  # legs zone: below the pink line, hatched blue
        rows = np.arange(N)[:, None]; legs = body_a & (rows > pink[None, :])
        hatch = ((np.arange(N)[:, None] + np.arange(N)[None, :]) // 6) % 2 == 0
        wbody[legs] = (0.62, 0.70, 0.86, 1); wbody[legs & hatch] = (0.52, 0.60, 0.80, 1)
    garm_grid = G.copy(); m = (grid[..., 3] > 0) & (G[..., 3] > 0.5); garm_grid[m] = grid[m]
    P = []
    a = pil(vbody); a.alpha_composite(pil(garm_grid)); a = on_bg(a); dots(a, dst, font, 4.0)
    P.append(("A  vanilla body, garment after step 4, your points, red grid on the garment", a))
    b = on_bg(pil(wbody)); dr = ImageDraw.Draw(b)
    if pink is not None:
        dr.line([(x, float(pink[x])) for x in range(N) if body_a[:, x].any()], fill=(255, 80, 200), width=3)
        dr.line((0, y0, N, y0), fill=(120, 120, 120), width=1)
        for (ax, ay), (bx, by) in zip(src0, src):
            if abs(ay - by) > 1:
                dr.line((ax, ay, bx, by), fill=(30, 60, 200), width=3)
                dr.ellipse((ax - 5, ay - 5, ax + 5, ay + 5), outline=(30, 60, 200), width=2)
    for (wx, wy), (vx, vy) in zip(src, dst):
        dr.line((vx * 4, vy * 4, wx, wy), fill=(255, 120, 0), width=3)
        dr.ellipse((vx * 4 - 4, vy * 4 - 4, vx * 4 + 4, vy * 4 + 4), fill=(255, 120, 0))
    dots(b, src, font)
    P.append(("B  WDI body, your points; orange = from the vanilla body" + (("; blue = moved for the legs, " + ("magenta = bottom of the boxers" if UNTUCKED else "pink = waistband")) if LEGS else ""), b))
    full_grid = grid.copy(); full_grid[..., 3] *= x4(Vb[..., 3] > 0.5)
    c = pil(wbody); c.alpha_composite(pil(warp(full_grid, U, V))); c = on_bg(c); dots(c, src, font)
    P.append(("C  the vanilla body's grid after the warp: how the space is bent between the points", c))
    d = pil(wbody); d.alpha_composite(pil(warp(garm_grid, U, V))); d = on_bg(d); dots(d, src, font)
    # where each vanilla point actually lands after the warp (the pixel whose sample is closest to it): cyan cross
    dd = ImageDraw.Draw(d)
    for (wx, wy), (vx, vy) in zip(src, dst):
        k = int(np.argmin((U - vx) ** 2 + (V - vy) ** 2)); ly, lx = divmod(k, N)
        dd.line((wx, wy, lx, ly), fill=(0, 230, 255), width=3)
        dd.line((lx - 8, ly, lx + 8, ly), fill=(0, 230, 255), width=3); dd.line((lx, ly - 8, lx, ly + 8), fill=(0, 230, 255), width=3)
    P.append(("D  after the warp: yellow = your WDI point, cyan cross = where the vanilla point really landed", d))
    e = pil(wbody); e.alpha_composite(pil(warp(G, U, V))); e = on_bg(e)
    P.append(("E  the garment alone after the warp, on the WDI body", e))
    # F: the artist's drawing with our warped strokes in red on top (only where he drew this garment)
    import os
    ap = rf"{WDI_TEX}\Things\Pawn\Humanlike\Apparel\{g}\{g}_{body}_{facing}.png"
    if os.path.exists(ap):
        art = c1.load(ap, N); wg = warp(G, U, V)
        f_ = pil(wbody); f_.alpha_composite(pil(art)); f_ = on_bg(f_)
        ours = (wg[..., 3] > 0.5) & (c1.lum(wg) < 0.45)
        red = np.zeros((N, N, 4), np.float32); red[ours] = (0.95, 0.05, 0.05, 0.9)
        f_.alpha_composite(pil(red))
        P.append(("F  the WDI artist's drawing; red = our strokes after step 5 laid on top", f_))
    else:
        P.append(("F  no drawing by the artist for this garment", on_bg(Image.new("RGBA", (N, N), (0, 0, 0, 0)))))
    legend = [f"{i + 1:>2} {n}  (moves {(wx / 4 - vx):+.0f}, {(wy / 4 - vy):+.0f} px)" for i, (n, (wx, wy), (vx, vy)) in enumerate(zip(names, src, dst))]
    return P, legend


def main():
    font = ImageFont.load_default(size=13); fontt = ImageFont.load_default(size=14); fontb = ImageFont.load_default(size=18)
    T = 400; pad = 8; left = 130; top = 50; head = 40; LEG = 330
    rows = []
    for b, f, g in CASES:
        P, legend = case(b, f, g, font); rows.append((f"{g}\n{b}\n{f}", P, legend)); print("case", b, f, g)
    im = Image.new("RGB", (left + 6 * (T + pad) + LEG, top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Step 5 in detail (black edges peeled at step 4, warp by your points only, " + ("EXACT: passes through every point" if LAM < 10 else "SMOOTHED lam 2000 as in round 8") + "). Grey = WDI body. Moves in vanilla pixels (x, y; + = right, down).", fill=(0, 0, 0), font=fontb)
    for r, (label, P, legend) in enumerate(rows):
        y = top + r * (T + head + pad)
        dr.text((8, y + head), label, fill=(0, 0, 0), font=fontb)
        for j, (title, p) in enumerate(P):
            x = left + j * (T + pad)
            words, line, lines = title.split(), "", []
            for w in words:
                if len(line) + len(w) > 52:
                    lines.append(line); line = w
                else:
                    line = (line + " " + w).strip()
            lines.append(line)
            dr.text((x, y), "\n".join(lines[:2]), fill=(0, 0, 0), font=fontt)
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (x, y + head))
        dr.text((left + 6 * (T + pad), y + head), "\n".join(legend), fill=(0, 0, 0), font=font)
    out = rf"{CAPT}\2026-11-07_step5-detail" + ("-exact" if LAM < 10 else "") + ("-legs" if LEGS else "") + ("-untucked" if UNTUCKED else "") + ("-recal" if RECAL else "") + ".png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
