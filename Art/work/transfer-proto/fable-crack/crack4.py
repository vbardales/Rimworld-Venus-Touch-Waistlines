"""Round 4 (Fable, 2026-11-06): the FRONT opening is a closed loop inside the garment, with a collar band above it.
In the landmark frame (origin = neck base midpoint, x unit = shoulder half-width, y unit = jugular-to-cleavage):
  top arc apex at y_top, widest at y_wide with half-width W, bottom at y_bot
  upper part: quarter ellipse from the apex to the widest row; lower part: half ellipse (round) or straight sides (V)
Per body (neck_table.json): round_depth, v_depth (= y_bot), width (= W); per type (fitted on the drawn openings):
y_top and the position of the widest row. Shoulders covered on every row. East and north untouched (round 2).

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack4.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import crack as c1, neck, lines, crack2, crack3

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE; VAN = c1.VAN
DRAWN = crack2.DRAWN; GARMENTS = crack2.GARMENTS
TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neck_table.json")
KIND_OF = {"ShirtBasic": "round", "ShirtButton": "V"}
COLLAR = 10.0          # collar band width around a V opening (ShirtButton), px at 512


# ---------------------------------------------------------------- measuring the drawn openings
def measure_loop(hole, fr):
    """(y_top, y_wide, y_bot, W) of the central opening, frame units"""
    ox, oy, xu, yu = fr
    rows = np.where(hole.any(axis=1))[0]
    if len(rows) == 0:
        return None
    half = np.zeros(len(rows))
    for i, y in enumerate(rows):
        xs = np.where(hole[y])[0]; half[i] = 0.5 * (xs.max() - xs.min() + 1)
    W = half.max()
    wide_rows = rows[half >= 0.95 * W]
    y_wide = float(np.median(wide_rows))
    return {"y_top": (rows.min() - oy) / yu, "y_wide": (y_wide - oy) / yu, "y_bot": (rows.max() + 1 - oy) / yu, "W": W / abs(xu)}


def drawn_loops():
    loops = {}
    for b in DRAWN:
        fw = neck.frame(b, "south", 1, 4)
        wba = crack2.alpha_of(rf"{WS}\Bodies\Naked_{b}_south.png")
        for g in GARMENTS:
            ga = crack2.alpha_of(rf"{WS}\Apparel\{g}\{g}_{b}_south.png", N)
            hole = neck.hole_mask(wba, ga, fw, band=1.05, centre_w=0.15)
            hole = ndi.binary_opening(hole, iterations=4)           # thin bare-shoulder strips drop off the loop
            lab, n = ndi.label(hole)
            if n > 1:
                sizes = ndi.sum(hole, lab, range(1, n + 1)); hole = lab == (1 + int(np.argmax(sizes)))
            loops[(b, g)] = measure_loop(hole, fw)
    return loops


def type_params(loops, exclude=None):
    """per type: y_top (mean) and f_wide = (y_wide - y_top) / (y_bot - y_top) (mean) over the reference bodies"""
    t = {}
    for g, kind in KIND_OF.items():
        refs = [loops[(b, g)] for b in DRAWN if b != exclude and loops[(b, g)]]
        t[kind] = {"y_top": float(np.mean([l["y_top"] for l in refs])),
                   "f_wide": float(np.mean([(l["y_wide"] - l["y_top"]) / max(1e-6, l["y_bot"] - l["y_top"]) for l in refs]))}
    return t


def make_table(loops):
    rows = {}
    for b in DRAWN:
        r, v = loops[(b, "ShirtBasic")], loops[(b, "ShirtButton")]
        rows[b] = {"round_depth": round(r["y_bot"], 2), "v_depth": round(v["y_bot"], 2), "width": round(0.5 * (r["W"] + v["W"]), 2),
                   "shoulders": "covered", "source": "measured on the WDI drawings (round W %.2f, V W %.2f)" % (r["W"], v["W"])}
    mean = {k: round(float(np.mean([rows[b][k] for b in DRAWN])), 2) for k in ("round_depth", "v_depth", "width")}
    for b, src in (("Thin", "Thin_Female"), ("Fat", "Fat_Female"), ("Hulk", "Hulk_Female")):
        rows[b] = {k: rows[src][k] for k in ("round_depth", "v_depth", "width")} | {"shoulders": "covered", "source": f"default from {src}, hand-editable"}
    for b in ("Male", "Female"):
        rows[b] = dict(mean) | {"shoulders": "covered", "source": "default = mean of the three drawn bodies, hand-editable"}
    return rows


def load_table(loops):
    if os.path.exists(TABLE):
        with open(TABLE) as f:
            t = json.load(f)
        if all("width" in v for k, v in t.items() if not k.startswith("_")):
            return t, "read"
    rows = make_table(loops)
    with open(TABLE, "w") as f:
        json.dump({"_doc": "front (south) neck opening per body type, landmark frame: depths = bottom of the opening below the neck base row in units of jugular-to-cleavage; width = opening half-width in shoulder half-width units; shoulders: covered | bare", **rows}, f, indent=1)
    return rows, "written"


# ---------------------------------------------------------------- rendering the loop
def render_loop(fr, kind, depth, W, tp, shape, smooth=1.0):
    ox, oy, xu, yu = fr
    H, Wd = shape
    y_top = tp["y_top"]; y_bot = depth; y_wide = y_top + tp["f_wide"] * (y_bot - y_top)
    ys = (np.arange(H) + 0.5 - oy) / yu
    w = np.zeros(H)
    up = (ys >= y_top) & (ys < y_wide)
    t = (y_wide - ys[up]) / max(1e-6, y_wide - y_top)
    w[up] = W * np.sqrt(np.clip(1 - t * t, 0, 1))
    lo = (ys >= y_wide) & (ys <= y_bot)
    t = (ys[lo] - y_wide) / max(1e-6, y_bot - y_wide)
    w[lo] = W * (np.sqrt(np.clip(1 - t * t, 0, 1)) if kind == "round" else np.clip(1 - t, 0, 1))
    xs = (np.arange(Wd) + 0.5 - ox) / abs(xu)
    mask = np.abs(xs)[None, :] < w[:, None]
    if smooth:
        mask = ndi.gaussian_filter(mask.astype(np.float32), smooth) > 0.5
    return mask


# ---------------------------------------------------------------- rebuild
def rebuild4(body, garment, cal, U, V, shade, body_a, kind, row, tp):
    facing = "south"
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg); vba = Vb[..., 3] > 0.5
    s_out = c1.edge_run(va, vl, ~va)
    fv = neck.frame(body, facing, 0, 1); fw = neck.frame(body, facing, 1, 4)
    hole_v = neck.hole_mask(vba, va, fv, band=neck.BAND[facing], centre_w=neck.CENTRE[facing])
    s_hole = min(c1.edge_run(va, vl, hole_v), s_out) if hole_v.sum() else 0.0
    d = int(round(max(0.0, cal["d"])))
    body_d = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    coverage = body_d.copy()
    depth = row["v_depth"] if kind == "V" else row["round_depth"]
    hole = render_loop(fw, kind, depth, row["width"], tp[kind], (N, N)) if kind != "none" else np.zeros((N, N), bool)
    hole &= ndi.binary_dilation(body_a, iterations=2)          # never outside the body
    alpha = coverage & ~hole
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1)); alpha = lab == (1 + int(np.argmax(sizes)))
    cov, din = c1.soft_edge(alpha)
    w_out = cal["w_out"]
    w_hole = w_out * (s_hole / s_out) if s_out > 0 else w_out * 0.5
    d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
    d_outer = ndi.distance_transform_edt(coverage)
    w_loc = np.minimum(w_out, np.maximum(4.0, 0.45 * (d_outer + d_hole)))
    outline = np.clip(w_loc + 0.5 - d_outer, 0, 1)
    outline = np.maximum(outline, np.clip(w_hole + 0.5 - d_hole, 0, 1))          # inner rim of the collar band
    fabric = np.interp(shade, cal["lut_x"], cal["lut_y"])
    # details from the vanilla garment, kept only on the placket (below the opening) and in the collar zone
    inner_v = ndi.binary_erosion(va, iterations=int(s_out) + 1) & ~ndi.binary_dilation(hole_v, iterations=int(s_hole) + 1)
    bg = ndi.grey_closing(np.where(va, vl, 1.0), size=(7, 7))
    dark = np.clip((bg - vl) / 0.30, 0, 1) * inner_v
    dark_w = c1.sample128(dark.astype(np.float32), U, V, order=1)
    det = (dark_w > 0.30) & alpha & (d_outer > w_out + 1) & (d_hole > w_hole + 1)
    ys, xs = np.mgrid[0:N, 0:N]
    xn = (xs + 0.5 - fw[0]) / abs(fw[2])
    hb = c1.bbox(hole) if hole.sum() else (0, 0, 0, 0)
    placket = (np.abs(xs + 0.5 - fw[0]) < max(22.0, 0.15 * abs(fw[2]))) & (ys > hb[3])
    det &= placket                                              # strays elsewhere are dropped
    lab, n = ndi.label(det, structure=np.ones((3, 3)))
    if n:
        sizes = ndi.sum(det, lab, range(1, n + 1)); det &= np.isin(lab, 1 + np.where(sizes >= 10)[0])
    # collar: for a V the band's outer curve, a parallel of the opening at COLLAR px, around the top arc and the sides
    if kind == "V" and hole.sum():
        band = (d_hole >= COLLAR - 0.6) & (d_hole < COLLAR + 0.6) & alpha & (d_outer > w_out + 2) & (ys <= hb[3] + COLLAR)
        det |= band
    def keep(P):
        """a stroke is either the placket (clearly vertical) or part of the collar curve"""
        w = float(np.ptp(P[:, 0])) + 1; h = float(np.ptp(P[:, 1])) + 1
        if h > 1.8 * w:
            return True
        ix = np.clip(P[:, 0].astype(int), 0, N - 1); iy = np.clip(P[:, 1].astype(int), 0, N - 1)
        return bool(np.abs(d_hole[iy, ix] - COLLAR).mean() < 2.5)
    strokes, buttons, npoly = lines.render(det, keep=keep)
    strokes *= alpha
    rgb = fabric * (1 - strokes) + c1.LINE_LUM * strokes
    rgb = rgb * (1 - outline) + c1.OUTLINE_RGB * outline
    out = np.zeros((N, N, 4), dtype=np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = rgb; out[..., 3] = cov
    return out, {"buttons": len(buttons), "strokes": npoly, "d": d, "depth": depth, "width": row["width"]}


# ---------------------------------------------------------------- runs
def main():
    pv, pw = crack2.measure_profiles()
    loops = drawn_loops()
    for k, v in loops.items():
        print("loop", k, {a: round(b, 2) for a, b in v.items()})
    table, how = load_table(loops)
    print("table", TABLE, how)
    with open(rf"{OUT}\scores.json") as f: s1 = json.load(f)
    with open(rf"{OUT}\scores3.json") as f: s3 = json.load(f)
    results, tiles = {}, {}
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    for body in DRAWN:
        U, V, shade, body_a, cal = crack2.prep(body, "south")
        tp = type_params(loops, exclude=body)
        results[body] = {"table": table[body], "type_params": tp}
        for g in GARMENTS:
            kind, ratio = crack3.classify(pv[(body, "south", g)])
            out, info = rebuild4(body, g, cal, U, V, shade, body_a, kind, table[body], tp)
            c1.to_pil(out).save(rf"{OUT}\r4_{g}_{body}_south.png")
            ref = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_south.png", N)
            iou, edge, mae = c1.score(out, ref)
            results[body][g] = {"kind": kind, "iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3),
                                "round1_iou": s1[f"{body}_south"][f"{g}_plainneck"]["iou"], "round3_iou": s3[body][g]["iou"], **info}
            tiles[(body, g, "r4")] = out; tiles[(body, g, "wdi")] = ref
            print(body, g, json.dumps(results[body][g]))
    with open(rf"{OUT}\scores4.json", "w") as f:
        json.dump(results, f, indent=1)
    cols = [("vanilla ShirtButton x4", lambda b: c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{c1.VANILLA_OF[b].capitalize()}_south.png"))),
            ("WDI body", lambda b: c1.load(rf"{WS}\Bodies\Naked_{b}_south.png")),
            ("ROUND 4 ShirtButton (closed V loop, collar)", lambda b: tiles[(b, "ShirtButton", "r4")]),
            ("WDI artist's ShirtButton", lambda b: tiles[(b, "ShirtButton", "wdi")]),
            ("ROUND 3", lambda b: c1.load(rf"{OUT}\r3_ShirtButton_{b}_south.png")),
            ("ROUND 1", lambda b: c1.load(rf"{OUT}\ShirtButton_{b}_south_plainneck.png")),
            ("ROUND 4 ShirtBasic (closed round loop)", lambda b: tiles[(b, "ShirtBasic", "r4")]),
            ("WDI artist's ShirtBasic", lambda b: tiles[(b, "ShirtBasic", "wdi")])]
    S = 300; pad = 6; left = 175; top = 70
    im = Image.new("RGB", (left + len(cols) * (S + pad), top + 3 * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 4, south: the opening is a closed loop (top arc at the neck base, collar band above), width and depth per body from neck_table.json, type from vanilla, collar rim drawn, strays dropped.", fill=(0, 0, 0), font=fontb)
    for j, (name, _) in enumerate(cols):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, b in enumerate(DRAWN):
        y = top + r * (S + pad); R = results[b]
        dr.text((8, y + 8), f"{b}\nsouth", fill=(0, 0, 0), font=fontb)
        txt = f"table: round {R['table']['round_depth']}\n V {R['table']['v_depth']} width {R['table']['width']}\n"
        for g in GARMENTS:
            s = R[g]
            txt += f"{g}: {s['kind']}\n IoU r1 {s['round1_iou']} r3 {s['round3_iou']}\n     r4 {s['iou']} edge {s['edge_px']}\n buttons {s['buttons']}\n"
        dr.text((8, y + 60), txt, fill=(0, 0, 0), font=font)
        for j, (_, get) in enumerate(cols):
            im.paste(c1.crop_tile(get(b), S).convert("RGB"), (left + j * (S + pad), y))
    p1 = rf"{CAPT}\2026-11-06_crack-round4.png"; im.save(p1); print("board", p1)
    # borrowed
    bodies = ["Male", "Female", "Thin", "Fat", "Hulk"]
    tp = type_params(loops)
    cols2 = ["vanilla ShirtButton x4", "WDI body", "ROUND 4 ShirtButton", "ROUND 4 ShirtBasic", "vanilla ShirtBasic x4"]
    im2 = Image.new("RGB", (left + len(cols2) * (S + pad), top + len(bodies) * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im2)
    dr.text((8, 8), "Round 4, borrowed bodies, south, no ground truth: closed-loop opening, width and depth from neck_table.json, calibration from the donor.", fill=(0, 0, 0), font=fontb)
    for j, name in enumerate(cols2):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, body in enumerate(bodies):
        donor = crack2.DONOR[body]
        U, V, shade, body_a, cal = crack2.prep(body, "south", donor)
        vb = c1.VANILLA_OF[body]; fv = neck.frame(body, "south", 0, 1)
        vba = crack2.alpha_of(rf"{VAN}\vanilla-{vb}-south.png")
        y = top + r * (S + pad)
        panels = [c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{vb.capitalize()}_south.png")), c1.load(rf"{WS}\Bodies\Naked_{body}_south.png")]
        txt = f"{body}\ndonor {donor}\nround {table[body]['round_depth']} V {table[body]['v_depth']}\nwidth {table[body]['width']}\n"
        for g in GARMENTS:
            hv = neck.hole_mask(vba, crack2.alpha_of(rf"{CORE}\{g}_{vb.capitalize()}_south.png"), fv, band=neck.BAND["south"], centre_w=neck.CENTRE["south"])
            kind, ratio = crack3.classify(neck.profile(hv, vba, fv, crack3.XS))
            out, info = rebuild4(body, g, cal, U, V, shade, body_a, kind, table[body], tp)
            c1.to_pil(out).save(rf"{OUT}\r4_{g}_{body}_south_borrowed.png")
            panels.append(out); txt += f"{g}: {kind} buttons {info['buttons']}\n"
        panels.append(c1.nearest4(c1.load(rf"{CORE}\ShirtBasic_{vb.capitalize()}_south.png")))
        dr.text((8, y + 8), txt, fill=(0, 0, 0), font=font)
        for j, t in enumerate(panels):
            im2.paste(c1.crop_tile(t, S).convert("RGB"), (left + j * (S + pad), y))
        print("borrowed", body, txt.replace(chr(10), " | "))
    p2 = rf"{CAPT}\2026-11-06_crack-round4-borrowed.png"; im2.save(p2); print("board", p2)


if __name__ == "__main__":
    main()
