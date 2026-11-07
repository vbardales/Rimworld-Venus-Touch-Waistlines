"""Round 3 (Fable, 2026-11-06): Virginie's rule for the FRONT opening.
  - each garment keeps its opening TYPE (round or V), classified from the vanilla opening in the vanilla landmark frame
  - the DEPTH is one setting per body type, in neck_table.json (editable): round_depth, v_depth (in units of
    jugular-to-cleavage, from the body top), shoulders = covered | bare
  - the type's SHAPE comes from the drawn bodies (leave-one-body-out for the drawn ones), scaled by the depth
  - when the V is deeper than the vanilla one, lapel lines are redrawn along the V edge
East and north are exactly round 2.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack3.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import crack as c1, neck, lines, crack2

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE; VAN = c1.VAN
DRAWN = crack2.DRAWN; GARMENTS = crack2.GARMENTS
TABLE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "neck_table.json")
XS = neck.XS["south"]; MID = int(np.argmin(np.abs(XS))); INNER = np.abs(XS) <= 0.7; OUTER = ~INNER
LAPEL_INSET = 9.0


# ---------------------------------------------------------------- table
def measure_table(pw):
    rows = {}
    for b in DRAWN:
        r = pw[(b, "south", "ShirtBasic")]; v = pw[(b, "south", "ShirtButton")]
        bare = float(max(r[1, OUTER].max(), v[1, OUTER].max()))
        rows[b] = {"round_depth": round(float(r[1, MID]), 2), "v_depth": round(float(v[1, MID]), 2),
                   "shoulders": "bare" if bare > 0.15 else "covered", "measured_bare_shoulders": round(bare, 2), "source": "measured on the WDI drawings"}
    mean = {k: round(float(np.mean([rows[b][k] for b in DRAWN])), 2) for k in ("round_depth", "v_depth")}
    for b, src in (("Thin", "Thin_Female"), ("Fat", "Fat_Female"), ("Hulk", "Hulk_Female")):
        rows[b] = {"round_depth": rows[src]["round_depth"], "v_depth": rows[src]["v_depth"], "shoulders": "covered", "source": f"default from {src}, hand-editable"}
    for b in ("Male", "Female"):
        rows[b] = {"round_depth": mean["round_depth"], "v_depth": mean["v_depth"], "shoulders": "covered", "source": "default = mean of the three drawn bodies, hand-editable"}
    # the drawn bodies: shoulders covered by default too, unless edited (Virginie's rule)
    for b in DRAWN:
        rows[b]["shoulders"] = "covered"
    return rows


def load_table(pw):
    if os.path.exists(TABLE):
        with open(TABLE) as f:
            return json.load(f), "read"
    rows = measure_table(pw)
    with open(TABLE, "w") as f:
        json.dump({"_doc": "front (south) neck opening per body type; depths in units of jugular-to-cleavage measured from the body top; shoulders: covered | bare", **rows}, f, indent=1)
    return rows, "written"


# ---------------------------------------------------------------- type and shape
def classify(pv_prof):
    """V or round from the vanilla bottom profile: a V falls off quickly away from the centre"""
    b = pv_prof[1]; m = b.max()
    if b[MID] <= 0:
        return "none", 1.0
    side = np.mean([np.interp(0.3, XS, b), np.interp(-0.3, XS, b)])
    r = side / b[MID]
    fine = np.linspace(-1, 1, 401); bf = np.interp(fine, XS, b)
    flat = (bf >= 0.9 * m).sum() / max(1, (bf >= 0.5 * m).sum())      # a round opening is flat-bottomed
    return ("V" if (flat < 0.58 and r < 0.87) else "round"), float(r)


def templates(pw, exclude=None):
    """per type: inner shape (bottom / centre depth, mean over the reference bodies), top band (min), bare shoulders
    (max over the reference bodies, used only when a table row says bare)"""
    t = {}
    for kind, g in (("round", "ShirtBasic"), ("V", "ShirtButton")):
        refs = [pw[(b, "south", g)] for b in DRAWN if b != exclude]
        norm = [p[1] / max(p[1, MID], 1e-6) for p in refs]
        shape = np.mean(norm, axis=0)
        shape[OUTER] = 0.0
        shape[np.min(norm, axis=0) < 0.12] = 0.0      # the opening extends only where every reference body opens
        top = np.min([p[0] for p in refs], axis=0); top[OUTER] = 0.0
        bare = np.max([p[1] for p in refs], axis=0); bare[INNER] = 0.0
        t[kind] = {"shape": shape, "top": top, "bare": bare}
    return t


def south_profile(kind, row, tpl):
    if kind == "none":
        return None
    depth = row["v_depth"] if kind == "V" else row["round_depth"]
    prof = np.zeros((2, len(XS)))
    prof[1] = tpl[kind]["shape"] * depth
    prof[0] = tpl[kind]["top"]
    if row.get("shoulders") == "bare":
        prof[1, OUTER] = tpl[kind]["bare"][OUTER]
    return prof


# ---------------------------------------------------------------- rebuild (round 2 pipeline plus lapels)
def rebuild3(body, garment, cal, U, V, shade, body_a, prof, kind):
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
    if prof is not None:
        prof = prof.copy(); prof[0, prof[0] * fw[3] < 8.0] = 0.0
    hole = neck.render(fw, XS, prof, body_a) if prof is not None and prof.max() > 0.02 else np.zeros((N, N), bool)
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
    outline = np.maximum(outline, np.clip(w_hole + 0.5 - d_hole, 0, 1))
    fabric = np.interp(shade, cal["lut_x"], cal["lut_y"])
    # details from the vanilla garment
    inner_v = ndi.binary_erosion(va, iterations=int(s_out) + 1) & ~ndi.binary_dilation(hole_v, iterations=int(s_hole) + 1)
    bg = ndi.grey_closing(np.where(va, vl, 1.0), size=(7, 7))
    dark = np.clip((bg - vl) / 0.30, 0, 1) * inner_v
    dark_w = c1.sample128(dark.astype(np.float32), U, V, order=1)
    det = (dark_w > 0.30) & alpha & (d_outer > w_out + 1) & (d_hole > w_hole + 1)
    lab, n = ndi.label(det, structure=np.ones((3, 3)))
    if n:
        sizes = ndi.sum(det, lab, range(1, n + 1)); det &= np.isin(lab, 1 + np.where(sizes >= 10)[0])
    # lapels: when the V is deeper than the vanilla opening carried over, redraw the lapel lines along the V edge
    lapels = False
    if kind == "V" and hole.sum():
        hv_w = c1.clean_mask(c1.sample128(hole_v.astype(np.float32), U, V))
        vb_bottom = c1.bbox(hv_w)[3] if hv_w.sum() else 0
        hb = c1.bbox(hole)
        if hb[3] > vb_bottom + 6:
            lapels = True
            ys, xs = np.mgrid[0:N, 0:N]
            xn = (xs + 0.5 - fw[0]) / abs(fw[2])
            zone = (np.abs(xn) <= 0.6) & (ys < hb[3] + 2)
            det &= ~zone                                                  # the warped vanilla collar is replaced
            band = (d_hole >= LAPEL_INSET - 0.6) & (d_hole < LAPEL_INSET + 0.6) & alpha & zone & (ys >= hb[1] + 3) & (ys <= hb[3] + LAPEL_INSET)
            det |= band
    strokes, buttons, npoly = lines.render(det)
    strokes *= alpha
    rgb = fabric * (1 - strokes) + c1.LINE_LUM * strokes
    rgb = rgb * (1 - outline) + c1.OUTLINE_RGB * outline
    out = np.zeros((N, N, 4), dtype=np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = rgb; out[..., 3] = cov
    return out, {"buttons": len(buttons), "strokes": npoly, "lapels": lapels, "d": d}


# ---------------------------------------------------------------- runs
def main():
    pv, pw = crack2.measure_profiles()
    table, how = load_table(pw)
    print("table", TABLE, how)
    with open(rf"{OUT}\scores.json") as f: s1 = json.load(f)
    with open(rf"{OUT}\scores2.json") as f: s2 = json.load(f)
    results, tiles = {}, {}
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    # validation on the drawn bodies, south
    for body in DRAWN:
        U, V, shade, body_a, cal = crack2.prep(body, "south")
        tpl = templates(pw, exclude=body)
        results[body] = {"table": table[body]}
        for g in GARMENTS:
            kind, ratio = classify(pv[(body, "south", g)])
            prof = south_profile(kind, table[body], tpl)
            out, info = rebuild3(body, g, cal, U, V, shade, body_a, prof, kind)
            c1.to_pil(out).save(rf"{OUT}\r3_{g}_{body}_south.png")
            ref = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_south.png", N)
            iou, edge, mae = c1.score(out, ref)
            results[body][g] = {"kind": kind, "ratio": round(ratio, 3), "iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3),
                                "round1_iou": s1[f"{body}_south"][f"{g}_plainneck"]["iou"], "round2B_iou": s2[f"{body}_south"][f"{g}_B"]["iou"], **info}
            tiles[(body, g, "r3")] = out; tiles[(body, g, "wdi")] = ref
            print(body, g, json.dumps(results[body][g]))
    with open(rf"{OUT}\scores3.json", "w") as f:
        json.dump(results, f, indent=1)
    # board 1: validation
    cols = [("vanilla ShirtButton x4", lambda b: c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{c1.VANILLA_OF[b].capitalize()}_south.png"))),
            ("WDI body", lambda b: c1.load(rf"{WS}\Bodies\Naked_{b}_south.png")),
            ("ROUND 3 ShirtButton (type V, table depth)", lambda b: tiles[(b, "ShirtButton", "r3")]),
            ("WDI artist's ShirtButton", lambda b: tiles[(b, "ShirtButton", "wdi")]),
            ("ROUND 2 B", lambda b: c1.load(rf"{OUT}\r2_ShirtButton_{b}_south_B.png")),
            ("ROUND 1", lambda b: c1.load(rf"{OUT}\ShirtButton_{b}_south_plainneck.png")),
            ("ROUND 3 ShirtBasic (type round)", lambda b: tiles[(b, "ShirtBasic", "r3")]),
            ("WDI artist's ShirtBasic", lambda b: tiles[(b, "ShirtBasic", "wdi")])]
    S = 300; pad = 6; left = 170; top = 70
    im = Image.new("RGB", (left + len(cols) * (S + pad), top + 3 * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 3, south: each garment keeps its opening type (classified from vanilla), depth per body from neck_table.json, shape from the other drawn bodies, lapels redrawn along a deeper V.", fill=(0, 0, 0), font=fontb)
    for j, (name, _) in enumerate(cols):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, b in enumerate(DRAWN):
        y = top + r * (S + pad); R = results[b]
        dr.text((8, y + 8), f"{b}\nsouth", fill=(0, 0, 0), font=fontb)
        txt = f"table: round {R['table']['round_depth']} V {R['table']['v_depth']}\n{R['table']['shoulders']}\n"
        for g in GARMENTS:
            s = R[g]
            txt += f"{g}: {s['kind']} (r {s['ratio']})\n IoU r1 {s['round1_iou']} r2 {s['round2B_iou']}\n     r3 {s['iou']} edge {s['edge_px']}\n lapels {s['lapels']} buttons {s['buttons']}\n"
        dr.text((8, y + 60), txt, fill=(0, 0, 0), font=font)
        for j, (_, get) in enumerate(cols):
            im.paste(c1.crop_tile(get(b), S).convert("RGB"), (left + j * (S + pad), y))
    p1 = rf"{CAPT}\2026-11-06_crack-round3.png"; im.save(p1); print("board", p1)
    # board 2: borrowed bodies
    bodies = ["Male", "Female", "Thin", "Fat", "Hulk"]
    tpl = templates(pw)
    cols2 = ["vanilla ShirtButton x4", "WDI body", "ROUND 3 ShirtButton", "ROUND 3 ShirtBasic", "vanilla ShirtBasic x4"]
    im2 = Image.new("RGB", (left + len(cols2) * (S + pad), top + len(bodies) * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im2)
    dr.text((8, 8), "Round 3, borrowed bodies, south, no ground truth: calibration from the donor, opening type from vanilla, depth from neck_table.json.", fill=(0, 0, 0), font=fontb)
    for j, name in enumerate(cols2):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, body in enumerate(bodies):
        donor = crack2.DONOR[body]
        U, V, shade, body_a, cal = crack2.prep(body, "south", donor)
        vb = c1.VANILLA_OF[body]; fv = neck.frame(body, "south", 0, 1)
        vba = crack2.alpha_of(rf"{VAN}\vanilla-{vb}-south.png")
        y = top + r * (S + pad)
        panels = [c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{vb.capitalize()}_south.png")), c1.load(rf"{WS}\Bodies\Naked_{body}_south.png")]
        txt = f"{body}\ndonor {donor}\nround {table[body]['round_depth']} V {table[body]['v_depth']}\n{table[body]['shoulders']}\n"
        for g in GARMENTS:
            hv = neck.hole_mask(vba, crack2.alpha_of(rf"{CORE}\{g}_{vb.capitalize()}_south.png"), fv, band=neck.BAND["south"], centre_w=neck.CENTRE["south"])
            kind, ratio = classify(neck.profile(hv, vba, fv, XS))
            prof = south_profile(kind, table[body], tpl)
            out, info = rebuild3(body, g, cal, U, V, shade, body_a, prof, kind)
            c1.to_pil(out).save(rf"{OUT}\r3_{g}_{body}_south_borrowed.png")
            panels.append(out); txt += f"{g}: {kind} (r {ratio:.2f}) lapels {info['lapels']}\n"
        panels.append(c1.nearest4(c1.load(rf"{CORE}\ShirtBasic_{vb.capitalize()}_south.png")))
        dr.text((8, y + 8), txt, fill=(0, 0, 0), font=font)
        for j, t in enumerate(panels):
            im2.paste(c1.crop_tile(t, S).convert("RGB"), (left + j * (S + pad), y))
        print("borrowed", body, txt.replace(chr(10), " | "))
    p2 = rf"{CAPT}\2026-11-06_crack-round3-borrowed.png"; im2.save(p2); print("board", p2)


if __name__ == "__main__":
    main()
