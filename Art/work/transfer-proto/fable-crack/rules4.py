"""Her four rules for a top and trousers (2026-11-07):
  1. top alone      : down to min(B,C) + d_min, d_min = the smallest gap, over the columns where both sprites are drawn,
                      between min(B,C) and the bottom of the boxers' legs (so the hem is never below the boxers)
  2. trousers + top : the trousers go up to max(B,C)
  3. tucked top     : the top is cropped at min(B,C), under the trousers (which go up to max(B,C), drawn over it)
  4. trousers alone : stop at min(B,C)
plus the untucked case: trousers to min(B,C) under, the top over down to max(B,C) + d_min, d_min measured from max(B,C)
(Virginie 2026-11-07: top alone on min, top over trousers untucked on max).
min(B,C) = per column the lower of the boxers (B) and panties (C) tops on screen, extended with its slope for the top
(hemshift .pink.txt); max(B,C) = the higher one, held flat past the shared span (pantsnap.waist_line).
Board: Art/work/captures/2026-11-07_four-rules.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python rules4.py
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import crack as c1, explain5b as e5, snapshirt as ss, pantsnap as pn, shirt2 as s2m
from pantsnap import trimmed_top, extend, lines

N = c1.N
ss.EDGE = "outer"
LEG_SLOPE = 0.3


def boxers_bottom(body, facing):
    a = c1.load(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{facing}.png", N)[..., 3] > 0.16
    line = np.full(N, np.nan)
    for x in range(N):
        ys = np.where(a[:, x])[0]
        if ys.size:
            line[x] = ys.max()
    return line


def dmin_of(body, facing, pink):
    """Smallest gap between min(B,C) and the boxers' leg line, over the shared span. Only the columns where the boxers'
    bottom runs across (slope <= LEG_SLOPE): the side walls of the sprite, where the bottom climbs to meet the top, are not
    the leg line (they gave 11 px on Thin_Female east and the side edge on north, Virginie 2026-11-07). 0.3, not 1: the
    slanted hip sides of the Fat_Female boxers (slope 0.7 to 1) are not the leg line either"""
    bb = boxers_bottom(body, facing)
    _, span = pn.waist_line(body, facing, "min")
    x = np.arange(N)
    with np.errstate(invalid="ignore"):
        ok = (x >= span[0]) & (x <= span[1]) & ~np.isnan(bb) & (np.abs(np.gradient(bb)) <= LEG_SLOPE)
    gap = bb - pink
    j = int(np.where(ok)[0][np.argmin(gap[ok])])
    return float(gap[j]), j, bb, ok


def max_ext(body, facing, pink=None):
    """max(B,C) for the top, extended with its own slope (see lines)"""
    return lines(body, facing)[1]


def untucked_hem(body, facing, pink):
    """Virginie 2026-11-07: top alone on min(B,C) + d_min; top over trousers, untucked, on max(B,C) + the SAME d_min
    (measured from min, rule 1): the hem sits higher by the gap between the two lines and a little more of the trousers
    shows. Returns (hem line, d_min, column of d_min, max line)."""
    line = max_ext(body, facing, pink)
    d, j, _, _ = dmin_of(body, facing, pink)
    return line + d, d, j, line


def shirt_to(body, facing, hem, parts=False):
    """the shirt outline of step 1 (outer edge, moved up) with its sides down to the line `hem` and the hem along it"""
    res = ss.case(body, facing)
    filled = ndi.binary_fill_holes(res["art"][..., 3] > 0.5)
    contour = ss.outer_contour(filled)
    xi = np.clip(np.round(contour[:, 0]).astype(int), 0, N - 1)
    arc = ss.arc_of(contour, contour[:, 1] <= hem[xi])
    seeds = res["src"][res["on"]]; seeds = seeds[seeds[:, 1] <= np.nanmax(hem)]
    s = ss.fit(arc, seeds)
    a, b = arc[-1], arc[0]
    xs = np.linspace(a[0], b[0], max(2, int(abs(b[0] - a[0]) // 2)))
    band = np.c_[xs, hem[np.clip(np.round(xs).astype(int), 0, N - 1)]]
    h = ss.fit(band, [])
    holes = [res["sN"][3]] if "sN" in res else []
    if parts:
        return s2m.stroke_fill(np.r_[s[3], h[3]], holes), res["body_a"], (s[3], h[3])
    return s2m.stroke_fill(np.r_[s[3], h[3]], holes), res["body_a"]


def trousers_to(body, facing, which):
    r = pn.case(body, facing, which)
    return s2m.stroke_fill(np.r_[r["s"][3], r["h"][3]])


def drop_hem_stroke(F, S, hem, under, curves):
    """Tucked: where the top's crop line (hem) and the trousers' top (under) are within one stroke of each other, the two
    4 px strokes sit side by side as an 8 px band. Virginie 2026-11-07: 'garde bas', keep the lower one (the trousers'
    waistband): the top's hem stroke is turned back into fabric there. A stroke pixel belongs to the hem when it is
    nearer the hem curve than the side curve (curves = (sides, hem) from shirt_to(parts=True)); the side walls stay."""
    k = s2m.STROKE_IN
    S = S.copy()
    close = (hem - under) < k
    ys, xs = np.nonzero(S)
    p = np.c_[xs, ys].astype(float)
    d_side = cKDTree(curves[0]).query(p)[0]; d_hem = cKDTree(curves[1]).query(p)[0]
    hit = close[xs] & (d_hem < d_side) & (ys >= hem[xs] - 2 * k - 3)     # band test: keeps the side wall at the corner
    S[ys[hit], xs[hit]] = False
    return S


def waistband_on_top(pS, hem, under):
    """the trousers' waistband stroke, in the columns where it is kept ('garde bas'): drawn again over the top so the
    top's fill does not hide part of it where hem sits a few px under the trousers' top (north)"""
    k = s2m.STROKE_IN
    close = (hem - under) < k
    rows = np.arange(N)[:, None]
    return pS & close[None, :] & (rows <= under[None, :] + 2 * k + 1)


def tucked(body, facing, pink):
    """Rule 3, validated on Thin_Female (three facings) 2026-11-07: trousers under, top on top.
    Trousers' top = max(B,C), or min(B,C) where the two are within one stroke ('garde bas'). Top cropped at min(B,C),
    never above the trousers' top (no body showing between them). Where the two lines are close, a single stroke: the
    trousers' waistband."""
    tk, _ = pn.waist_line(body, facing, "tucked")
    k = s2m.STROKE_IN
    # where the lines are close (not the east side) the crop goes onto the (smoothed) trousers' top + 1.5 px, so no row of
    # body shows; elsewhere it stays on min(B,C). The switch is a smoothed weight, as for the trousers' line: a hard switch
    # left steps in the hem on Hulk_Female north (Virginie 2026-11-07, 'il manque un lissage')
    s = ndi.gaussian_filter1d(np.clip((2 * k - np.abs(tk - pink)) / k, 0, 1), 4.0)
    crop = pink + s * (np.maximum(tk + 1.5, pink) - pink)
    crop = np.where(s > 0.02, ndi.gaussian_filter1d(crop, 3.0), crop)
    # never above the trousers' top: on east the extended min climbs at the back while the trousers' line is held flat,
    # and the body showed between them at the back corner
    crop = np.maximum(crop, tk + 1.5)
    (tF, tS), _, cur = shirt_to(body, facing, crop, parts=True)
    pF, pS = trousers_to(body, facing, "tucked")
    tS = drop_hem_stroke(tF, tS, crop, tk, cur)
    return pF, pS, tF, tS, waistband_on_top(pS, crop, tk)


def draw_tucked(img, tuck):
    pF, pS, tF, tS, wt = tuck
    layer(img, pF, pS, (0.45, 0.55, 0.75)); layer(img, tF, tS, (1, 1, 1)); layer(img, wt, wt, (0, 0, 0))


def layer(img, F, S, rgb):
    a = np.zeros((N, N, 4), np.float32); a[F] = (*rgb, 1); a[S] = (0.02, 0.02, 0.03, 1)
    img.alpha_composite(e5.pil(a))


def main():
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 280; pad = 6; left = 110; top = 74; head = 18
    cols = ["1. top alone: min(B,C) + d_min", "4. trousers alone: min(B,C)", "3. tucked: trousers to max under, top cut at min over", "untucked: trousers to min under, top to max + d_min over"]
    only = sys.argv[1] if len(sys.argv) > 1 else None
    rows = [(b, f) for b in (ss.BODIES if only is None else [only]) for f in ss.FACINGS]
    im = Image.new("RGB", (left + 4 * (T + pad), top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "The four rules. Lines: magenta = min(B,C) (lower top), cyan = max(B,C) (higher top), orange = bottom of the boxers' legs, green = min(B,C) + d_min.", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "White = top, blue = trousers, both drawn with a 4 px stroke inward. Bodies the WDI artist drew (his ShirtBasic gives the top's outline).", fill=(0, 0, 0), font=fontb)
    for j, t in enumerate(cols):
        dr.text((left + j * (T + pad), top - 18), t, fill=(0, 0, 0), font=font)
    for r_, (b, f) in enumerate(rows):
        y = top + r_ * (T + head + pad)
        try:
            pink = lines(b, f)[0]     # min(B,C) without the sprite walls, extended with its slope (replaces hemshift .pink.txt)
            dmin, jmin, bb, ok = dmin_of(b, f, pink)
            mx = lines(b, f)[1]      # max(B,C) extended, as the top uses it
            (tF1, tS1), body_a = shirt_to(b, f, pink + dmin)
            pF4, pS4 = trousers_to(b, f, "min")
            tuck = tucked(b, f, pink)
            uhem, udmin, uj, uline = untucked_hem(b, f, pink)
            (tFu, tSu), _ = shirt_to(b, f, uhem)
        except Exception as ex:
            print("FAIL", b, f, repr(ex)[:200]); continue
        wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
        tiles = []
        for case in range(4):
            t = e5.pil(wb)
            if case == 0:
                layer(t, tF1, tS1, (1, 1, 1))
            elif case == 1:
                layer(t, pF4, pS4, (0.45, 0.55, 0.75))
            elif case == 2:
                draw_tucked(t, tuck)
            else:
                layer(t, pF4, pS4, (0.45, 0.55, 0.75)); layer(t, tFu, tSu, (1, 1, 1))     # untucked: trousers to min under, top on max + d_min over
            t = e5.on_bg(t); d = ImageDraw.Draw(t)
            cols_x = [x for x in range(N) if body_a[:, x].any()]
            d.line([(x, float(pink[x])) for x in cols_x], fill=(255, 60, 200), width=1)
            d.line([(x, float(mx[x])) for x in cols_x], fill=(0, 220, 255), width=1)
            d.line([(x, float(bb[x])) for x in cols_x if not np.isnan(bb[x])], fill=(255, 140, 0), width=1)
            if case == 0:
                d.line([(x, float(pink[x] + dmin)) for x in cols_x], fill=(40, 200, 60), width=1)
                d.line((jmin, float(pink[jmin]), jmin, float(bb[jmin])), fill=(255, 0, 0), width=3)
            if case == 3:
                d.line([(x, float(uhem[x])) for x in cols_x], fill=(40, 200, 60), width=1)
                d.line((uj, float(uline[uj]), uj, float(uhem[uj])), fill=(255, 0, 0), width=3)
            tiles.append(t)
        dr.text((8, y + head + 6), f"{b}\n{f}", fill=(0, 0, 0), font=fontb)
        dr.text((left, y + 2), f"d_min = {dmin:.1f} px, min(B,C) to the boxers' leg line; top alone on min + d_min, untucked on max + d_min", fill=(0, 0, 0), font=font)
        for j, p in enumerate(tiles):
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
        print(b, f, "dmin", round(dmin, 1))
    out = rf"{c1.CAPT}\2026-11-07_four-rules{'-' + only if only else ''}.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
