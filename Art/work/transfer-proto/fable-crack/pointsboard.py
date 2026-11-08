"""The warp pairs, large: vanilla points on the prepared vanilla shirt (left) and WDI points on the target (right), same numbers,
one row per facing (Virginie 2026-11-07: 'montre-moi les points vanilla et les points WDI').
Yellow = her contour point (snapped), cyan = her inner point, orange = point added on the WDI outline and its vanilla twin,
green = hem pairs (vanilla bottom edge to the WDI hem); blue ring on WDI = where a point was before the legs press.
Board: Art/work/captures/2026-11-07_points-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python pointsboard.py [Body]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, explain5b as e5, fullpass as fp

N = c1.N


def draw(img, P, kinds, font, moved=None):
    d = ImageDraw.Draw(img)
    if moved is not None:
        for (ax, ay), (bx, by) in zip(moved, P):
            if abs(ay - by) > 1 or abs(ax - bx) > 1:
                d.line((ax, ay, bx, by), fill=(30, 60, 220), width=2); d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), outline=(30, 60, 220), width=2)
    for i, (x, y) in enumerate(P):
        d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=kinds[i], outline=(0, 0, 0))
        d.text((x + 7, y - 10), str(i + 1), fill=(0, 0, 0), font=font, stroke_width=2, stroke_fill=(255, 255, 255))


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else "Male"
    font = ImageFont.load_default(size=13); fontb = ImageFont.load_default(size=18)
    Z = 2                                              # zoom on the body box
    rows = []
    for f in ["south", "east", "north"]:
        fp.facing_row(body, f); L = fp.LAST
        kinds = list(L["kind"]) + [(40, 200, 60)] * (len(L["S"]) - len(L["kind"]))
        kinds = [(40, 200, 60) if i >= len(L["S"]) - L["nhem"] else k for i, k in enumerate(kinds)]
        vbody = e5.x4(L["Vb"]); vbody[..., :3] = vbody[..., :3] * 0.5 + 0.45
        a = e5.pil(vbody); a.alpha_composite(e5.pil(L["Gp"])); a = e5.on_bg(a)
        draw(a, L["D"] * 4, kinds, font)
        wb = np.zeros((N, N, 4), np.float32); wb[L["body_a"]] = (0.80, 0.80, 0.80, 1)
        tg = np.zeros((N, N, 4), np.float32); tg[L["F"]] = (1, 1, 1, 0.9); tg[L["St"]] = (0.02, 0.02, 0.03, 1)
        # the WDI boxers under the WDI points (Virginie: 'essaie de mettre un boxer sous les points wdi'), outline drawn over
        bx = c1.load(rf"{e5.WDI_TEX}\UWUnderwear\boxers\boxers_{body}_{f}.png", N)
        tgo = tg.copy(); tgo[..., 3] = np.where(L["St"], 1.0, 0.0)
        # the WDI naked body drawn under the points (her own study board style): the anatomy shows where navel, groin and
        # pubis are; the boxers only as their outline (orange)
        import crack2
        naked = c1.load(rf"{crack2.WS}\Bodies\Naked_{body}_{f}.png", N)
        b = e5.pil(wb); b.alpha_composite(e5.pil(naked)); b.alpha_composite(e5.pil(tgo)); b = e5.on_bg(b); db = ImageDraw.Draw(b)
        ba = bx[..., 3] > 0.16; bedge = ba & ~__import__("scipy").ndimage.binary_erosion(ba)
        for yy, xx in zip(*np.nonzero(bedge)):
            db.point((int(xx), int(yy)), fill=(255, 140, 0))
        db.line([(x, float(L["hem"][x])) for x in range(N) if L["body_a"][:, x].any()], fill=(40, 200, 60), width=1)
        db.line((0, L["y0"], N, L["y0"]), fill=(120, 120, 120), width=1)
        draw(b, L["S"], kinds, font, L["S0"])
        ys, xs = np.nonzero(L["body_a"] | e5.x4(L["Vb"][..., 3] > 0.5))
        box = (max(0, xs.min() - 30), max(0, ys.min() - 30), min(N, xs.max() + 30), min(N, ys.max() + 30))
        a = a.crop(box); b = b.crop(box)
        a = a.resize((a.width * Z, a.height * Z), Image.LANCZOS); b = b.resize((b.width * Z, b.height * Z), Image.LANCZOS)
        rows.append((f, a, b))
    W = max(r[1].width + r[2].width for r in rows) + 140; H = sum(r[1].height for r in rows) + 60 * len(rows) + 60
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: the warp pairs. Left vanilla (prepared shirt), right WDI (boxers under, target outline), same numbers. Yellow her contour points, "
                      "cyan her inner points, orange added + twins, green hem pairs; blue ring = before the legs press.", fill=(0, 0, 0), font=fontb)
    y = 50
    for f, a, b in rows:
        dr.text((10, y + 4), f, fill=(0, 0, 0), font=fontb)
        im.paste(a.convert("RGB"), (110, y + 30)); im.paste(b.convert("RGB"), (110 + a.width + 20, y + 30))
        y += a.height + 60
    tag = ("-nolegs" if fp.NOLEGS else "") + ("-groin" if fp.GROIN else "") + ("" if fp.G == "ShirtBasic" else "-" + fp.G)
    out = rf"{c1.CAPT}\2026-11-07_points-{body}{tag}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
