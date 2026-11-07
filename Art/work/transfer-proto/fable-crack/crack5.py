"""Round 5 (Fable, 2026-11-06): collar, shading band, buttons by rule, all facings, all eight bodies.
Numbers measured on the WDI artist's drawings (measure5.py):
  shading band: garment darker than the body-driven LUT by k (south 0.15, east 0.18, north 0.22) from the neck row,
                fading out by 0.9 jugular-to-cleavage units below it
  ShirtButton south: 3 px rim on the opening, 10 px collar band above the top arc bounded by a thin line and shaded
                darker, lapel outer line at 0.4 x opening half-width along the lower part of the V, placket line
                from the V point, 3 ring buttons from 0.35 below the point every 0.40 units, 13 px right of centre
  ShirtBasic: 8 px black rim around the opening plus a thin line 4 px further out
  creases: the LUT already gives 10 to 30 percent of the body's crease contrast in front and side, none at the back
East and north openings: round 2 profiles. South opening: round 4 closed loop with a fillet at the widest row.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack5.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import crack as c1, neck, lines, crack2, crack3, crack4

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE; VAN = c1.VAN
DRAWN = crack2.DRAWN; GARMENTS = crack2.GARMENTS; FACINGS = crack2.FACINGS
ALL_BODIES = ["Thin_Female", "Fat_Female", "Hulk_Female", "Male", "Female", "Thin", "Fat", "Hulk"]
BAND_K = {"south": 0.15, "east": 0.18, "north": 0.22}
BAND_END = 0.9
BTN_FIRST, BTN_STEP, BTN_N, BTN_DX = 0.35, 0.40, 3, 13.0
LAPEL_FRAC = 0.4
COLLAR_PX = 10.0
RIM = {"ShirtBasic": 8.0, "ShirtButton": 3.0}
LINE_FILL = 0.30


def fillet_loop(fr, kind, depth, W, tp, shape):
    """round 4 loop with the join at the widest row smoothed (fillet) and a rounded V point"""
    m = crack4.render_loop(fr, kind, depth, W, tp, shape, smooth=0)
    r = max(2, int(round(0.08 * W * abs(fr[2]))))
    m = ndi.binary_opening(m, structure=_disk(r)) | ndi.binary_erosion(m, iterations=1)
    m = ndi.binary_closing(m, structure=_disk(r))
    return ndi.gaussian_filter(m.astype(np.float32), 1.0) > 0.5


def _disk(r):
    y, x = np.ogrid[-r:r + 1, -r:r + 1]
    return (x * x + y * y) <= r * r


def classify_vanilla(body, garment):
    vb = c1.VANILLA_OF[body]; fv = neck.frame(body, "south", 0, 1)
    vba = crack2.alpha_of(rf"{VAN}\vanilla-{vb}-south.png")
    hv = neck.hole_mask(vba, crack2.alpha_of(rf"{CORE}\{garment}_{vb.capitalize()}_south.png"), fv, band=neck.BAND["south"], centre_w=neck.CENTRE["south"])
    return crack3.classify(neck.profile(hv, vba, fv, crack3.XS))[0]


def rebuild5(body, facing, garment, cal, U, V, shade, body_a, hole, kind):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg); vba = Vb[..., 3] > 0.5
    s_out = c1.edge_run(va, vl, ~va)
    fv = neck.frame(body, facing, 0, 1); fw = neck.frame(body, facing, 1, 4); ox, oy, xu, yu = fw
    hole_v = neck.hole_mask(vba, va, fv, band=neck.BAND[facing], centre_w=neck.CENTRE[facing])
    s_hole = min(c1.edge_run(va, vl, hole_v), s_out) if hole_v.sum() else 0.0
    d = int(round(max(0.0, cal["d"])))
    body_d = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    coverage = body_d.copy()
    hole = hole & ndi.binary_dilation(body_a, iterations=2)
    alpha = coverage & ~hole
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1)); alpha = lab == (1 + int(np.argmax(sizes)))
    cov, din = c1.soft_edge(alpha)
    w_out = cal["w_out"]
    d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
    d_outer = ndi.distance_transform_edt(coverage)
    w_loc = np.minimum(w_out, np.maximum(4.0, 0.45 * (d_outer + d_hole)))
    outline = np.clip(w_loc + 0.5 - d_outer, 0, 1)
    # rim of the opening: the artist's 8 px ring on ShirtBasic, 3 px line on ShirtButton
    w_rim = RIM[garment] if hole.sum() else 0.0
    outline = np.maximum(outline, np.clip(w_rim + 0.5 - d_hole, 0, 1))
    # shading: body through the LUT, then the artist's dark band across the top
    fabric = np.interp(shade, cal["lut_x"], cal["lut_y"])
    ys = (np.arange(N)[:, None] + 0.5 - oy) / yu * np.ones((1, N))
    ramp = np.clip((BAND_END - ys) / (BAND_END - 0.2), 0, 1)
    fabric = fabric - BAND_K[facing] * ramp
    thin = np.zeros((N, N), np.float32)
    hb = c1.bbox(hole) if hole.sum() else None
    buttons_n = 0
    if garment == "ShirtBasic" and hb is not None:
        thin = np.maximum(thin, np.clip(1.0 - np.abs(d_hole - (w_rim + 4.0)), 0, 1) * (alpha & (d_outer > w_out + 2)))
    if garment == "ShirtButton" and hb is not None and facing == "south" and kind in ("V", "round"):
        yw = hb[1] + 0.35 * (hb[3] - hb[1])
        W_px = 0.5 * (hb[2] - hb[0])
        c = np.where(np.arange(N)[:, None] < yw, COLLAR_PX, np.clip(COLLAR_PX + (np.arange(N)[:, None] - yw) / 20.0 * (LAPEL_FRAC * W_px - COLLAR_PX), min(COLLAR_PX, LAPEL_FRAC * W_px), max(COLLAR_PX, LAPEL_FRAC * W_px)))
        c = c * np.ones((1, N))
        band_in = (d_hole < c) & alpha & (d_outer > w_out + 1)
        top_band = band_in & (np.arange(N)[:, None] < yw)
        fabric = np.where(top_band, fabric - 0.22, fabric)                       # collar band shaded darker
        edge = np.clip(1.0 - np.abs(d_hole - c), 0, 1) * (alpha & (d_outer > w_out + 2) & (np.arange(N)[:, None] <= hb[3] + LAPEL_FRAC * W_px))
        thin = np.maximum(thin, edge)
        # placket from the V point down to the hem margin, and ring buttons by rule
        canvas = Image.new("L", (N * 4, N * 4), 0); dr = ImageDraw.Draw(canvas)
        y0 = hb[3] + 2; y1 = c1.bbox(alpha)[3] - w_out - 6
        dr.line([(ox * 4, y0 * 4), (ox * 4, y1 * 4)], fill=255, width=10)
        # three buttons: the artist's spacing (0.40 units) when the placket is long enough, else evenly down the placket
        first = hb[3] + 0.2 * yu; last = min(hb[3] + (BTN_FIRST + BTN_STEP * (BTN_N - 1)) * yu, y1 - 8)
        for i in range(BTN_N):
            by = first + (last - first) * i / (BTN_N - 1)
            if by < y1 - 6:
                bx = ox + BTN_DX; r = 5.0 * 4
                dr.ellipse([bx * 4 - r, by * 4 - r, bx * 4 + r, by * 4 + r], outline=255, width=8); buttons_n += 1
        thin = np.maximum(thin, np.asarray(canvas.resize((N, N), Image.BOX)).astype(np.float32) / 255.0 * alpha)
    elif garment == "ShirtButton" and facing != "south":
        # east and north: the warped vanilla details, fitted as strokes (round 2), restricted to the collar zone
        inner_v = ndi.binary_erosion(va, iterations=int(s_out) + 1) & ~ndi.binary_dilation(hole_v, iterations=int(s_hole) + 1)
        bg = ndi.grey_closing(np.where(va, vl, 1.0), size=(7, 7))
        dark = np.clip((bg - vl) / 0.30, 0, 1) * inner_v
        dark_w = c1.sample128(dark.astype(np.float32), U, V, order=1)
        det = (dark_w > 0.30) & alpha & (d_outer > w_out + 1) & (d_hole > w_rim + 1) & (d_hole < 60)
        if facing == "north":
            det &= np.abs((np.arange(N)[None, :] + 0.5 - ox) / abs(xu)) < 0.5
        lab, n = ndi.label(det, structure=np.ones((3, 3)))
        if n:
            sizes = ndi.sum(det, lab, range(1, n + 1)); det &= np.isin(lab, 1 + np.where(sizes >= 10)[0])
        strokes, _, _ = lines.render(det, button_max=0)        # no ring buttons on the side or the back
        thin = np.maximum(thin, strokes * alpha)
    rgb = np.clip(fabric, 0, 1) * (1 - thin) + LINE_FILL * thin
    rgb = rgb * (1 - outline) + c1.OUTLINE_RGB * outline
    out = np.zeros((N, N, 4), dtype=np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = rgb; out[..., 3] = cov
    return out, {"buttons": buttons_n, "kind": kind}


def main():
    pv, pw = crack2.measure_profiles()
    A, B, ALLP, maps = crack2.neck_models(pv, pw)
    loops = crack4.drawn_loops()
    table, how = crack4.load_table(loops)
    with open(rf"{OUT}\scores4.json") as f: s4 = json.load(f)
    with open(rf"{OUT}\scores2.json") as f: s2 = json.load(f)
    results, tiles = {}, {}
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    for body in ALL_BODIES:
        drawn = body in DRAWN
        donor = None if drawn else crack2.DONOR[body]
        tp = crack4.type_params(loops, exclude=body if drawn else None)
        kinds = {g: classify_vanilla(body, g) for g in GARMENTS}
        for facing in FACINGS:
            U, V, shade, body_a, cal = crack2.prep(body, facing, donor)
            fw = neck.frame(body, facing, 1, 4)
            for g in GARMENTS:
                kind = kinds[g]
                if facing == "south":
                    row = table[body]; depth = row["v_depth"] if kind == "V" else row["round_depth"]
                    hole = fillet_loop(fw, kind, depth, row["width"], tp[kind], (N, N)) if kind != "none" else np.zeros((N, N), bool)
                else:
                    prof = B[(body, facing, g)] if drawn else ALLP[(facing, g)]
                    prof = prof.copy(); prof[0, prof[0] * fw[3] < 8.0] = 0.0
                    hole = neck.render(fw, neck.XS[facing], prof, body_a) if prof.max() > 0.02 else np.zeros((N, N), bool)
                out, info = rebuild5(body, facing, g, cal, U, V, shade, body_a, hole, kind)
                c1.to_pil(out).save(rf"{OUT}\r5_{g}_{body}_{facing}.png")
                tiles[(body, facing, g)] = out
                if drawn:
                    ref = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", N)
                    tiles[(body, facing, g, "wdi")] = ref
                    iou, edge, mae = c1.score(out, ref)
                    prev = s4[body][g]["iou"] if facing == "south" else s2[f"{body}_{facing}"][f"{g}_B"]["iou"]
                    results[f"{body}_{facing}_{g}"] = {"iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3), "prev_iou": prev, **info}
                    print(body, facing, g, json.dumps(results[f"{body}_{facing}_{g}"]))
        print("done", body)
    with open(rf"{OUT}\scores5.json", "w") as f:
        json.dump(results, f, indent=1)
    S = 300; pad = 6; left = 170; top = 70
    for facing in FACINGS:
        cols = [("WDI body", lambda b: c1.load(rf"{WS}\Bodies\Naked_{b}_{facing}.png")),
                ("ROUND 5 ShirtButton", lambda b: tiles[(b, facing, "ShirtButton")]),
                ("WDI artist's ShirtButton", lambda b: tiles[(b, facing, "ShirtButton", "wdi")]),
                ("ROUND 5 ShirtBasic", lambda b: tiles[(b, facing, "ShirtBasic")]),
                ("WDI artist's ShirtBasic", lambda b: tiles[(b, facing, "ShirtBasic", "wdi")]),
                ("previous round ShirtButton", lambda b: c1.load(rf"{OUT}\r4_ShirtButton_{b}_south.png") if facing == "south" else c1.load(rf"{OUT}\r2_ShirtButton_{b}_{facing}_B.png"))]
        im = Image.new("RGB", (left + len(cols) * (S + pad), top + 3 * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((8, 8), f"Round 5, {facing}: collar and rim like the artist, dark band across the top, buttons by rule, creases through the LUT. Ours beside his.", fill=(0, 0, 0), font=fontb)
        for j, (name, _) in enumerate(cols):
            dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
        for r, b in enumerate(DRAWN):
            y = top + r * (S + pad)
            dr.text((8, y + 8), f"{b}\n{facing}", fill=(0, 0, 0), font=fontb)
            txt = ""
            for g in GARMENTS:
                s = results[f"{b}_{facing}_{g}"]
                txt += f"{g}:\n IoU prev {s['prev_iou']}\n     r5 {s['iou']} edge {s['edge_px']}\n lum {s['lum_mae']}\n"
            dr.text((8, y + 60), txt, fill=(0, 0, 0), font=font)
            for j, (_, get) in enumerate(cols):
                im.paste(c1.crop_tile(get(b), S).convert("RGB"), (left + j * (S + pad), y))
        p = rf"{CAPT}\2026-11-06_crack-round5-{facing}.png"; im.save(p); print("board", p)
    # final board: eight bodies x three facings x two garments, ours only
    cols = [(f, g) for f in FACINGS for g in GARMENTS]
    S2 = 240
    im = Image.new("RGB", (left + len(cols) * (S2 + pad), top + len(ALL_BODIES) * (S2 + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 5, all eight WDI bodies, three facings, two garments (rebuilt, no ground truth for the five bodies without drawings)", fill=(0, 0, 0), font=fontb)
    for j, (f, g) in enumerate(cols):
        dr.text((left + j * (S2 + pad), 40), f"{g} {f}", fill=(0, 0, 0), font=font)
    for r, b in enumerate(ALL_BODIES):
        y = top + r * (S2 + pad)
        dr.text((8, y + 8), f"{b}\n{'drawn by WDI' if b in DRAWN else 'donor ' + crack2.DONOR[b]}", fill=(0, 0, 0), font=font)
        for j, (f, g) in enumerate(cols):
            im.paste(c1.crop_tile(tiles[(b, f, g)], S2).convert("RGB"), (left + j * (S2 + pad), y))
    p = rf"{CAPT}\2026-11-06_crack-round5-all.png"; im.save(p); print("board", p)


if __name__ == "__main__":
    main()
