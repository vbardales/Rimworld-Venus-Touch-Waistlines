"""Trousers, first step (2026-11-07, Virginie: 'prends tout ça en compte + l'étude initiale sur les points').
Same method as the shirt (snapdraw.py), on the lower body:
  waist     : the line min(slip, caleçon) = per column the LOWER of the WDI panties and boxers tops (larger y), only
              where both are drawn (Nav.SetPink); past that span it is held flat, NOT extended with its slope (the
              extension climbed on Hulk / Hulk_Female and left the body in profile, D-line board of the same day)
  target    : the WDI artist's longjohns (UWUnderwear/longjohns, the only WDI drawing of the legs), below the waist
  points    : her WDI points of the lower body (recalibrated) snapped on that contour, curves through them, points
              added where the curve strays over 3 px, then the waistband along the waist line; drawn 4 px inward
  source    : AB's Pants on the vanilla body, with the points of her 2026-11-03 pants study (pants-<facing>-table.txt)
Boards: Art/work/captures/2026-11-07_pants-snap-<facing>.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python pantsnap.py
"""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from skimage.morphology import convex_hull_image
import crack as c1, crack2, crack5, explain5b as e5, snapshirt as ss

N = c1.N; STROKE_IN = 4
BODIES = crack5.ALL_BODIES; FACINGS = ["south", "east", "north"]
AB = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2986402536\Textures\Things\Pawn\Humanlike\Apparel\Pants"
STUDY = rf"{c1.MOD}\Art\work\captures\2026-11-03_points"
LOWER = ("hip", "groin", "sex", "crotch", "leg bottom", "bottom", "buttock", "belly", "waist", "leftmost", "rightmost")


def top_line(path):
    a = c1.load(path, N)[..., 3] > 0.16
    line = np.full(N, -1.0)
    for x in range(N):
        ys = np.where(a[:, x])[0]
        if ys.size:
            line[x] = ys.min()
    idx = np.where(line >= 0)[0]
    for s in range(2):                    # the outermost columns are the sprite's side edge (as Nav.TopLine)
        if idx.size > 2:
            line[idx[0]] = -1; line[idx[-1]] = -1; idx = idx[1:-1]
    return line


def trimmed_top(path, wall=2.0):
    """top edge of a WDI underwear sprite per column, without its side walls: from each end, columns are dropped while
    the top jumps by more than `wall` px from one column to the next (Hulk_Female panties: 383 then 396 at the south
    edge, 377 then 397 north; those columns bent min and max down at the ends, Virginie 2026-11-07)"""
    a = c1.load(path, N)[..., 3] > 0.16
    line = np.full(N, np.nan)
    for x in range(N):
        ys = np.where(a[:, x])[0]
        if ys.size:
            line[x] = ys.min()
    idx = np.where(~np.isnan(line))[0]
    lo, hi = int(idx[0]), int(idx[-1])
    # 1. a jump of 5 px or more within the 10 end columns: the rounded side pad of the panties; cut through it
    jl = [i + 1 for i in range(lo, lo + 10) if abs(line[i + 1] - line[i]) >= 5]
    jr = [i - 1 for i in range(hi, hi - 10, -1) if abs(line[i - 1] - line[i]) >= 5]
    lo = max(jl) if jl else lo           # the innermost jump
    hi = min(jr) if jr else hi
    # 2. then the wall itself: columns that still step by more than `wall` px
    while hi - lo > 4 and abs(line[lo + 1] - line[lo]) > wall:
        lo += 1
    while hi - lo > 4 and abs(line[hi - 1] - line[hi]) > wall:
        hi -= 1
    # 3. a gentle wall: the top still rises from the end to a corner (its highest point) near that end, then turns back
    # down; the side and back views have it (Thin_Female east back: 347 up to 331 over 8 columns, Hulk_Female east 36)
    near = max(10, int(0.35 * (hi - lo)))     # Hulk_Female east: the back wall runs 39 columns of 157
    # the corner must be a real turn: strictly inside the window, so a line that keeps rising inward is not cut
    # and the line must come back down by more than 2 px after it (a plateau on a slow frown is no corner)
    j = lo + int(np.argmin(line[lo:lo + near]))
    if lo < j < lo + near - 2 and np.all(np.diff(line[lo:j + 1]) <= 0) and line[j:lo + near].max() > line[j] + 2:
        lo = j
    j = hi - near + 1 + int(np.argmin(line[hi - near + 1:hi + 1]))
    if hi - near + 3 < j < hi and np.all(np.diff(line[j:hi + 1]) >= 0) and line[hi - near + 1:j + 1].max() > line[j] + 2:
        hi = j
    line[:lo] = np.nan; line[hi + 1:] = np.nan
    return line


def extend(w, span, k=12):
    """past the shared span, the line goes on with the slope of its last k columns (linear fit), on both sides"""
    out = w.copy(); s0, s1 = span
    x = np.arange(N)
    a = np.polyfit(np.arange(s0, s0 + k), w[s0:s0 + k], 1); out[:s0] = np.polyval(a, x[:s0])
    a = np.polyfit(np.arange(s1 - k + 1, s1 + 1), w[s1 - k + 1:s1 + 1], 1); out[s1 + 1:] = np.polyval(a, x[s1 + 1:])
    return out


def lines(body, facing):
    """min(B,C) and max(B,C) per column (lower and higher of the boxers and panties tops), median of 3, on the span both
    sprites cover once their side walls are dropped, both EXTENDED with their slope past it (Virginie 2026-11-07: a line
    held flat, not extrapolated, made the hem drop back at the sides). max is never under min."""
    b = trimmed_top(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png")
    p = trimmed_top(rf"{e5.WDI_TEX}\UWUnderwear\panties\panties_{body}_{facing}.png")
    both = ~np.isnan(b) & ~np.isnan(p)
    idx = np.where(both)[0]; span = (int(idx[0]), int(idx[-1]))
    res = []
    for f in (np.fmax, np.fmin):
        w = np.where(both, f(b, p), np.nan)
        m = w.copy()
        for x in range(span[0] + 1, span[1]):
            m[x] = np.median(w[x - 1:x + 2])
        res.append(extend(m, span))
    mn, mx = res
    return mn, np.minimum(mx, mn), span


def waist_line(body, facing, which="max"):
    """Virginie 2026-11-07: the trousers follow max(B,C) = the HIGHER of the panties and boxers tops on screen (smaller y);
    the shirt follows min(B,C) = the lower one (larger y, the pink line of Nav.SetPink).
    which="tucked": max(B,C), except where it is within one stroke (4 px) of min(B,C): there the trousers take min(B,C)
    ('garde bas', same day), so the waistband sits where it sits on trousers alone"""
    if which == "tucked":
        (mx, span), (mn, _) = waist_line(body, facing, "max"), waist_line(body, facing, "min")
        # gap under one stroke: min; over two strokes: max; in between a linear blend, so the switch makes no step
        # (a hard switch left 4 px bumps on Hulk_Female north)
        # the weight itself is smoothed first and the line after (Virginie 2026-11-07, Hulk_Female north tucked: 'le
        # moyennage ... il manque un lissage', the blend left waves where the gap hovers around 4 to 8 px)
        t = ndi.gaussian_filter1d(np.clip((mn - mx - STROKE_IN) / STROKE_IN, 0, 1), 4.0)
        w = mn + t * (mx - mn)
        return ndi.gaussian_filter1d(w, 8.0), span
    # 2026-11-07 evening: the same lines as the top (sprite walls dropped, extended with their slope), no longer held flat
    # past the span: held flat, the trousers' line put a bump in the tucked hem at the back of Thin_Female east
    mn, mx, span = lines(body, facing)
    return ndi.gaussian_filter1d(mx if which == "max" else mn, 1.5), span


def study_points(vb, facing):
    pts = []
    f = rf"{STUDY}\pants-{facing}-table.txt"
    for raw in open(f, encoding="utf-8-sig"):
        p = raw.strip().split("|")
        if len(p) < 6 or not p[0].startswith(f"AB {vb.capitalize()} (") or not p[3] or not p[4]:
            continue
        if any(k in p[2] for k in LOWER):
            pts.append((float(p[3]), float(p[4]), p[2]))
    return pts


def case(body, facing, which="max"):
    drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
    _, _, _, body_a, _ = crack2.prep(body, facing, donor)
    vb = c1.VANILLA_OF[body]; Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    lj = c1.load(rf"{e5.WDI_TEX}\UWUnderwear\longjohns\longjohns_{body}_{facing}.png", N)
    waist, span = waist_line(body, facing, which)
    L = ndi.binary_fill_holes(lj[..., 3] > 0.5)
    rows = np.arange(N)[:, None]
    # target: his longjohns below the waist, united with the body there: on Male and Female his longjohns are narrower
    # than the body (up to about 490 px of body outside them, north), the trousers left the hips bare (Virginie
    # 2026-11-07, Female steps 2 and 3); on the three bodies he drew his longjohns already cover the body
    T = (L | body_a) & (rows >= waist[None, :])
    lab, n = ndi.label(T)
    if n > 1:
        T = lab == (1 + int(np.argmax(ndi.sum(T, lab, range(1, n + 1)))))
    # Virginie 2026-11-07: trousers end in a U, not the naked body's W: the crotch notch between the two leg lobes is
    # filled, the lower part of the target becomes its convex hull (bottom 40 % of its height)
    ys = np.where(T.any(axis=1))[0]
    zone = T & (rows >= ys.max() - int(0.4 * (ys.max() - ys.min())))
    T = T | convex_hull_image(zone)
    contour = ss.outer_contour(T)
    xi = np.clip(np.round(contour[:, 0]).astype(int), 0, N - 1)
    arc = ss.arc_of(contour, contour[:, 1] > waist[xi] + 1.5)   # everything but the waistband itself
    on = [i for i, nm in enumerate(names) if any(k in nm for k in LOWER) and src[i][1] > np.nanmin(waist) - 4]
    seeds = src[on]
    s = ss.fit(arc, seeds)
    a, b = arc[-1], arc[0]
    xs = np.linspace(a[0], b[0], max(2, int(abs(b[0] - a[0]) // 2)))
    band = np.c_[xs, waist[np.clip(np.round(xs).astype(int), 0, N - 1)]]
    h = ss.fit(band, [])
    return dict(body_a=body_a, lj=lj, waist=waist, span=span, T=T, arc=arc, s=s, band=band, h=h,
                src=src, on=on, vb=vb, Vb=Vb, study=study_points(vb, facing))


def panels(r, facing, font):
    body_a = r["body_a"]
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    # A: AB pants on the vanilla body with her study points
    vt = np.repeat(np.repeat(r["Vb"], 4, axis=0), 4, axis=1); vt[..., :3] = vt[..., :3] * 0.6 + 0.4
    A = e5.on_bg(e5.pil(vt)); ab = rf"{AB}\Pants_{r['vb'].capitalize()}_{facing}.png"
    if os.path.exists(ab):
        A.alpha_composite(e5.pil(c1.load(ab, N)))
    da = ImageDraw.Draw(A)
    for (x, y, nm) in r["study"]:
        da.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(0, 230, 255), outline=(0, 0, 0))
    # B: his longjohns, the waist line, the snapped points
    B = e5.pil(wb); B.alpha_composite(e5.pil(r["lj"])); B = e5.on_bg(B); db = ImageDraw.Draw(B)
    db.line([(x, float(r["waist"][x])) for x in range(N) if body_a[:, x].any()], fill=(255, 60, 200), width=3)
    arc = r["arc"]; order, seeded, added = r["s"][0], r["s"][1], r["s"][2]
    for j in order:
        x, y = arc[j]; col = (255, 140, 0) if j in added else (255, 220, 0)
        db.ellipse((x - 6, y - 6, x + 6, y + 6), fill=col, outline=(0, 0, 0))
    for j in r["h"][0]:
        x, y = r["band"][j]; db.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(255, 60, 200), outline=(0, 0, 0))
    for i in r["on"]:
        x, y = r["src"][i]; db.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(0, 230, 255))
    # C: ours, curves 4 px inward
    curve = np.r_[r["s"][3], r["h"][3]]
    fill = Image.new("L", (N, N), 0); ImageDraw.Draw(fill).polygon([tuple(p) for p in curve], fill=255)
    lines = Image.new("L", (N, N), 0); dl = ImageDraw.Draw(lines)
    dl.line([tuple(p) for p in curve] + [tuple(curve[0])], fill=255, width=2 * STROKE_IN + 1)
    F = np.asarray(fill) > 127; S = (np.asarray(lines) > 127) & F
    ours = np.zeros((N, N, 4), np.float32); ours[F] = (1, 1, 1, 1); ours[S] = (0.02, 0.02, 0.03, 1)
    C = e5.pil(wb); C.alpha_composite(e5.pil(ours)); C = e5.on_bg(C)
    # D: shape against his longjohns below the waist
    Tg = r["T"]
    cm = np.zeros((N, N, 4), np.float32)
    cm[Tg & F] = (0.55, 0.85, 0.55, 1); cm[F & ~Tg] = (0.95, 0.2, 0.2, 1); cm[Tg & ~F] = (0.2, 0.4, 1.0, 1)
    D = e5.pil(wb * np.array([1, 1, 1, 0.4])); D.alpha_composite(e5.pil(cm)); D = e5.on_bg(D)
    iou = float((Tg & F).sum()) / max(1, float((Tg | F).sum()))
    o, _, ad, _, mx, _ = r["s"]
    return [A, B, C, D], f"{len(o)} points ({len(ad)} added), max {mx:.1f} px; waistband {len(r['h'][0])} points; IoU {iou:.3f}"


def main():
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 260; pad = 6; left = 110; top = 74; head = 18
    titles = ["source: AB Pants on the vanilla body, study points", "his longjohns, waist max(panties, boxers), points", "ours: curves, 4 px inward", "shape: green both, red ours, blue his"]
    for f in FACINGS:
        im = Image.new("RGB", (left + 4 * (T + pad), top + len(BODIES) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((8, 8), f"Trousers, first step, {f}: the WDI longjohns below the waist line max(panties, boxers) (the higher one), bottom closed in a U (crotch notch filled), redrawn from your points.", fill=(0, 0, 0), font=fontb)
        dr.text((8, 30), "Yellow = your points snapped, orange = added (curve over 3 px off), magenta = waistband points, cyan dot = your point before.", fill=(0, 0, 0), font=fontb)
        for j, t in enumerate(titles):
            dr.text((left + j * (T + pad), top - 18), t, fill=(0, 0, 0), font=font)
        for r_, b in enumerate(BODIES):
            y = top + r_ * (T + head + pad)
            try:
                P, txt = panels(case(b, f), f, font)
            except Exception as ex:
                print("FAIL", b, f, repr(ex)[:200]); continue
            dr.text((8, y + head + 6), b, fill=(0, 0, 0), font=fontb)
            dr.text((left, y + 2), txt, fill=(0, 0, 0), font=font)
            for j, p in enumerate(P):
                im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
            print(b, f, txt)
        out = rf"{c1.CAPT}\2026-11-07_pants-snap-{f}.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
