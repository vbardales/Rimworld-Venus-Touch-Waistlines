"""Pseudo shirt drawn from her points (2026-11-07, Virginie: 'dessine-moi sur WDI les points et relie certains pour
faire un pseudo vêtement façon simple shirt'). Her WDI points, recalibrated (highest on the silhouette top), are
joined in order: neck base, shoulder tip, armpit, waist, hip, then the hem on the bottom of WDI's boxers (untucked
shirt, never lower), and back up the other side; the neckline closes through the jugular notch in front, straight
across at the back. Where the WDI artist drew a ShirtBasic, its outline is shown in blue for comparison.
Board: Art/work/captures/2026-11-07_pseudo-shirt.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python pseudoshirt.py
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, crack2, crack5, explain5b as e5

N = c1.N
BODIES = crack5.ALL_BODIES; FACINGS = ["south", "east", "north"]


def find(names, src, key):
    for i, n in enumerate(names):
        if key in n.split(" / ") or n.startswith(key):
            return src[i]
    for i, n in enumerate(names):
        if key in n:
            return src[i]
    return None


def hem_line(body, facing):
    bx = c1.load(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png", N)[..., 3] > 0.5
    pink = np.array([float(v) for v in open(rf"{e5.PROTO}\hemshift_{body}_{facing}.pink.txt").read().strip().split(";")])
    line = pink.copy()
    for x in range(N):
        ys = np.where(bx[:, x])[0]
        if ys.size:
            line[x] = max(pink[x], float(ys.max()))
    return ndi.gaussian_filter1d(line, 3)


def chain(names, src, facing, hem, body_a):
    """the ordered outline of the pseudo shirt and the neckline, as lists of (x, y) in 512 px"""
    def p(k):
        return find(names, src, k)
    if facing in ("south", "north"):
        left = [p("neck base L"), p("shoulder tip L"), p("armpit L"), p("waist L"), p("hip L")]
        right = [p("hip R"), p("waist R"), p("armpit R"), p("shoulder tip R"), p("neck base R")]
        left = [q for q in left if q is not None]; right = [q for q in right if q is not None]
        xl = left[-1][0]; xr = right[0][0]
    else:
        left = [p("neck back"), p("upper back"), p("waist back"), p("buttock back")]
        right = [p("belly front"), p("waist front"), p("chest front"), p("neck front")]
        left = [q for q in left if q is not None]; right = [q for q in right if q is not None]
        xl = left[-1][0]; xr = right[0][0]
    # hem: from the last point of the left side down to the hem line, along it, then up to the right side
    xs = np.arange(int(round(min(xl, xr))), int(round(max(xl, xr))) + 1, 4)
    if xl > xr:
        xs = xs[::-1]
    bottom = [(float(x), float(hem[int(x)])) for x in xs]
    left = [q for q in left if q[1] <= hem[int(round(q[0]))]]
    right = [q for q in right if q[1] <= hem[int(round(q[0]))]]
    outline = [tuple(q) for q in left] + bottom + [tuple(q) for q in right]
    neck = []
    if facing == "south":
        j = p("jugular notch")
        if j is not None and p("neck base L") is not None and p("neck base R") is not None:
            neck = [tuple(p("neck base R")), tuple(j), tuple(p("neck base L"))]
    return outline, neck


MEASURED = {}


def opening(body, facing, body_a):
    """the round neckline (ShirtBasic), in 512 px: (centre x, top y, bottom y, half width, how).
    Drawn bodies: measured on the artist's ShirtBasic, the region of the WDI body his shirt leaves bare above the chest,
    the component under the neck. Others: neck_table.json (round depth, width) in the landmark frame."""
    import os, json
    ox, oy, xu, yu = __import__("neck").frame(body, facing, 1, 4)
    art = rf"{e5.WDI_TEX}\Things\Pawn\Humanlike\Apparel\ShirtBasic\ShirtBasic_{body}_{facing}.png"
    if os.path.exists(art):
        a = c1.load(art, N)[..., 3] > 0.5
        bare = body_a & ~a
        bare[int(oy + 2.2 * yu):, :] = False
        lab, n = ndi.label(bare)
        if n:
            ys, xs = np.where(bare)
            k = lab[int(np.clip(oy + 0.4 * yu, 0, N - 1)), int(ox)]
            if k:
                m = lab == k
                ys, xs = np.where(m)
                r = (float(ox), float(ys.min()), float(ys.max()), 0.5 * float(xs.max() - xs.min()), "measured on the artist")
                MEASURED[body] = r
                return r
    t = json.load(open(rf"{c1.MOD}\Art\work\transfer-proto\fable-crack\neck_table.json")).get(body)
    if t:
        return (float(ox), float(oy), float(oy + t["round_depth"] * yu), float(t["width"] * xu), "from neck_table")
    return None


def tile(body, facing, font):
    drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
    _, _, _, body_a, _ = crack2.prep(body, facing, donor)
    vb = c1.VANILLA_OF[body]; Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    hem = hem_line(body, facing)
    outline, neck = chain(names, src, facing, hem, body_a)
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    im = e5.on_bg(e5.pil(wb))
    shirt = Image.new("RGBA", (N, N), (0, 0, 0, 0)); ds = ImageDraw.Draw(shirt)
    poly = outline + (neck if neck else [])
    if len(poly) >= 3:
        ds.polygon(poly, fill=(255, 255, 255, 200))
    op = opening(body, facing, body_a) if facing == "south" else None
    if op is not None:                    # the neckline measured on the artist's oval (or from the table): cut out
        cx, top_y, bot_y, hw, how = op
        ds.ellipse((cx - hw, top_y - (bot_y - top_y), cx + hw, bot_y), fill=(0, 0, 0, 0))
    im.alpha_composite(shirt)
    dr = ImageDraw.Draw(im)
    dr.line([(x, float(hem[x])) for x in range(N) if body_a[:, x].any()], fill=(220, 60, 200), width=2)
    art = rf"{e5.WDI_TEX}\Things\Pawn\Humanlike\Apparel\ShirtBasic\ShirtBasic_{body}_{facing}.png"
    import os
    if os.path.exists(art):
        a = c1.load(art, N)[..., 3] > 0.5
        edge = a & ~ndi.binary_erosion(a, iterations=2)
        blue = np.zeros((N, N, 4), np.float32); blue[edge] = (0.1, 0.35, 1.0, 1)
        im.alpha_composite(e5.pil(blue)); dr = ImageDraw.Draw(im)
    if len(poly) >= 3:
        dr.line(poly + [poly[0]], fill=(0, 0, 0), width=4)
    if op is not None:
        cx, top_y, bot_y, hw, how = op
        dr.arc((cx - hw, top_y - (bot_y - top_y), cx + hw, bot_y), 0, 180, fill=(0, 0, 0), width=4)
        for (px, py, lab) in ((cx, bot_y, "B"), (cx - hw, top_y, "L"), (cx + hw, top_y, "R")):
            dr.ellipse((px - 8, py - 8, px + 8, py + 8), fill=(255, 140, 0), outline=(0, 0, 0))
            dr.text((px - 4, py - 7), lab, fill=(0, 0, 0), font=font)
        dr.text((8, N - 40), f"neckline ({how}): bottom {bot_y / 4:.1f}, half-width {hw / 4:.1f} px vanilla", fill=(255, 255, 255), font=font)
    # Virginie 2026-11-07: the matching vanilla points in cyan (same frame, x4), a thin line to their WDI point
    for (x, y), (vx, vy) in zip(src, dst):
        dr.line((vx * 4, vy * 4, x, y), fill=(0, 200, 230), width=2)
    for i, (vx, vy) in enumerate(dst):
        dr.ellipse((vx * 4 - 6, vy * 4 - 6, vx * 4 + 6, vy * 4 + 6), fill=(0, 230, 255), outline=(0, 0, 0))
    for i, (x, y) in enumerate(src):
        dr.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(255, 220, 0), outline=(0, 0, 0))
        dr.text((x - 5 if i < 9 else x - 8, y - 7), str(i + 1), fill=(0, 0, 0), font=font)
    return im


def main():
    font = ImageFont.load_default(size=11); fontb = ImageFont.load_default(size=16)
    T = 330; pad = 8; left = 110; top = 64
    im = Image.new("RGB", (left + len(BODIES) * (T + pad), top + 3 * (T + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Pseudo shirt from your points (recalibrated): neck base, shoulder tip, armpit, waist, hip, hem on the bottom of the boxers (magenta), neckline (orange L, B, R) = the round opening measured on the artist (or from neck_table).", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Black = the pseudo shirt, yellow = your WDI points, cyan = the matching vanilla points (line = how far each one moves), blue = the WDI artist's ShirtBasic where he drew one.", fill=(0, 0, 0), font=fontb)
    for j, b in enumerate(BODIES):
        dr.text((left + j * (T + pad), top - 18), b, fill=(0, 0, 0), font=fontb)
    for r, f in enumerate(FACINGS):
        y = top + r * (T + pad); dr.text((8, y + 8), f, fill=(0, 0, 0), font=fontb)
        for j, b in enumerate(BODIES):
            try:
                t = tile(b, f, font)
            except Exception as ex:
                print("FAIL", b, f, repr(ex)[:160]); continue
            im.paste(t.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y))
            print("tile", b, f)
    out = rf"{c1.CAPT}\2026-11-07_pseudo-shirt.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
