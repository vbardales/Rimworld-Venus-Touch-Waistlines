"""Round 2 of the layered rebuild (Fable, 2026-11-06): parametric neck opening in a landmark frame, fitted strokes,
ring buttons, borrowed-calibration run on the five bodies without drawn garments.
Reuses crack.py (round 1) for loading, TPS, shading, calibration, scoring and tiles.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack2.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

import crack as c1
import neck, lines

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE; VAN = c1.VAN
DRAWN = ["Fat_Female", "Hulk_Female", "Thin_Female"]
FACINGS = ["south", "east", "north"]
GARMENTS = ["ShirtButton", "ShirtBasic"]
DONOR = {"Fat": "Fat_Female", "Hulk": "Hulk_Female", "Thin": "Thin_Female", "Male": "Thin_Female", "Female": "Thin_Female"}


def alpha_of(path, size=None):
    return c1.load(path, size)[..., 3] > 0.5


def measure_profiles():
    """vanilla and WDI opening profiles in the landmark frame, for the drawn pairs"""
    pv, pw = {}, {}
    for body in DRAWN:
        vb = c1.VANILLA_OF[body]
        for facing in FACINGS:
            xs = neck.XS[facing]
            fv = neck.frame(body, facing, 0, 1); fw = neck.frame(body, facing, 1, 4)
            vba = alpha_of(rf"{VAN}\vanilla-{vb}-{facing}.png"); wba = alpha_of(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
            for g in GARMENTS:
                hv = neck.hole_mask(vba, alpha_of(rf"{CORE}\{g}_{vb.capitalize()}_{facing}.png"), fv, band=neck.BAND[facing], centre_w=neck.CENTRE[facing])
                hw = neck.hole_mask(wba, alpha_of(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", N), fw, band=neck.BAND[facing], centre_w=neck.CENTRE[facing])
                pv[(body, facing, g)] = neck.profile(hv, vba, fv, xs)
                pw[(body, facing, g)] = neck.profile(hw, wba, fw, xs)
    return pv, pw


def neck_models(pv, pw):
    """A: garment hold-out, linear map fitted on ShirtBasic per facing, applied to the vanilla ShirtButton profile.
       B: body hold-out, the WDI profile of the other drawn bodies (per facing and garment), mean.
       ALL: mean of the three drawn bodies (for the bodies without drawings)."""
    A, B, ALL, maps = {}, {}, {}, {}
    for facing in FACINGS:
        xs = neck.XS[facing]
        m = neck.fit_map([(pv[(b, facing, "ShirtBasic")], pw[(b, facing, "ShirtBasic")]) for b in DRAWN], xs)
        maps[facing] = m
        for g in GARMENTS:
            ALL[(facing, g)] = pool([pw[(b, facing, g)] for b in DRAWN], xs)
            for body in DRAWN:
                A[(body, facing, g)] = neck.apply_map(pv[(body, facing, g)], m, xs)
                B[(body, facing, g)] = pool([pw[(b, facing, g)] for b in DRAWN if b != body], xs)
    return A, B, ALL, maps


def pool(profiles, xs):
    """combine the reference bodies: mean of the bottom inside the opening (|x'| <= 0.7), but a bare shoulder strip
    (|x'| > 0.7) and a collar band (top row) only where every reference body has them (min)"""
    P = np.stack(profiles)
    out = P.mean(axis=0)
    outer = np.abs(np.asarray(xs)) > 0.7
    out[1, outer] = P[:, 1, outer].min(axis=0)
    out[0] = P[:, 0].min(axis=0)
    return out


def rebuild2(body, facing, garment, cal, U, V, shade, body_a, prof):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg); vba = Vb[..., 3] > 0.5
    s_out = c1.edge_run(va, vl, ~va)
    fv = neck.frame(body, facing, 0, 1); fw = neck.frame(body, facing, 1, 4)
    hole_v = neck.hole_mask(vba, va, fv, band=neck.BAND[facing], centre_w=neck.CENTRE[facing])
    s_hole = min(c1.edge_run(va, vl, hole_v), s_out) if hole_v.sum() else 0.0
    # 1. coverage
    d = int(round(max(0.0, cal["d"])))
    body_d = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    coverage = body_d.copy()
    if c1.bbox(va)[3] < c1.bbox(vba)[3] - 2:
        cov_v = c1.clean_mask(c1.sample128(va.astype(np.float32), U, V))
        hem = np.full(N, -1.0)
        for x in range(N):
            ys = np.where(cov_v[:, x])[0]
            if len(ys): hem[x] = ys.max()
        ok = hem >= 0
        if ok.sum() > 10:
            hem[~ok] = np.interp(np.where(~ok)[0], np.where(ok)[0], hem[ok])
            hem = ndi.median_filter(hem, size=15) + 4
            coverage &= np.arange(N)[:, None] <= hem[None, :]
    # 2. neck opening: the parametric curve in the WDI landmark frame
    if prof is not None:
        prof = prof.copy()
        thin = prof[0] * fw[3] < 8.0                 # a collar band under 8 px would be all stroke: open it
        prof[0, thin] = 0.0
    hole = neck.render(fw, neck.XS[facing], prof, body_a) if prof is not None and prof.max() > 0.02 else np.zeros((N, N), bool)
    alpha = coverage & ~hole
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1)); alpha = lab == (1 + int(np.argmax(sizes)))
    # 3. strokes
    cov, din = c1.soft_edge(alpha)
    w_out = cal["w_out"]
    w_hole = w_out * (s_hole / s_out) if s_out > 0 else w_out * 0.5
    d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
    d_outer = ndi.distance_transform_edt(coverage)
    # the outer stroke never eats more than 45 % of a thin band (the collar band above the opening)
    w_loc = np.minimum(w_out, np.maximum(4.0, 0.45 * (d_outer + d_hole)))
    outline = np.clip(w_loc + 0.5 - d_outer, 0, 1)
    outline = np.maximum(outline, np.clip(w_hole + 0.5 - d_hole, 0, 1))
    # 4. shading
    fabric = np.interp(shade, cal["lut_x"], cal["lut_y"])
    # 5. details: dark lines of the vanilla garment, warped, then fitted as smooth strokes and rings
    inner_v = ndi.binary_erosion(va, iterations=int(s_out) + 1) & ~ndi.binary_dilation(hole_v, iterations=int(s_hole) + 1)
    bg = ndi.grey_closing(np.where(va, vl, 1.0), size=(7, 7))
    dark = np.clip((bg - vl) / 0.30, 0, 1) * inner_v
    dark_w = c1.sample128(dark.astype(np.float32), U, V, order=1)
    det = (dark_w > 0.30) & alpha & (d_outer > w_out + 1) & (d_hole > w_hole + 1)
    lab, n = ndi.label(det, structure=np.ones((3, 3)))
    if n:
        sizes = ndi.sum(det, lab, range(1, n + 1)); det &= np.isin(lab, 1 + np.where(sizes >= 10)[0])
    strokes, buttons, npoly = lines.render(det)
    strokes *= alpha
    # 6. composite
    rgb = fabric * (1 - strokes) + c1.LINE_LUM * strokes
    rgb = rgb * (1 - outline) + c1.OUTLINE_RGB * outline
    out = np.zeros((N, N, 4), dtype=np.float32)
    out[..., 0] = out[..., 1] = out[..., 2] = rgb; out[..., 3] = cov
    return out, {"buttons": len(buttons), "strokes": npoly, "d": d, "w_out": w_out, "w_hole": w_hole}


def prep(body, facing, donor=None):
    """body shading, landmarks, TPS, calibration (own or borrowed)"""
    B = c1.load(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
    shade, body_a, rim, body_inner = c1.body_shading(B)
    src, dst = c1.landmarks(body, facing)
    tps = c1.TPS(src, dst); U, V = c1.warp_field(tps)
    if donor is None:
        cal, _ = c1.calibrate(body, facing, tps, U, V, B, shade, body_a, body_inner)
    else:
        Bd = c1.load(rf"{WS}\Bodies\Naked_{donor}_{facing}.png")
        sd, ad, _, innerd = c1.body_shading(Bd)
        srcd, dstd = c1.landmarks(donor, facing); tpsd = c1.TPS(srcd, dstd); Ud, Vd = c1.warp_field(tpsd)
        cal, _ = c1.calibrate(donor, facing, tpsd, Ud, Vd, Bd, sd, ad, innerd)
    return U, V, shade, body_a, cal


def run_holdout():
    pv, pw = measure_profiles()
    A, B, ALL, maps = neck_models(pv, pw)
    with open(rf"{OUT}\scores.json") as f:
        prev = json.load(f)
    results, tiles = {}, {}
    for body in DRAWN:
        for facing in FACINGS:
            U, V, shade, body_a, cal = prep(body, facing)
            key = f"{body}_{facing}"
            results[key] = {"neck_map_A": maps[facing]}
            for g in GARMENTS:
                ref = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", N)
                tiles[(body, facing, g, "wdi")] = ref
                for tag, prof in (("B", B[(body, facing, g)]), ("A", A[(body, facing, g)]), ("O", pw[(body, facing, g)])):
                    out, info = rebuild2(body, facing, g, cal, U, V, shade, body_a, prof)
                    c1.to_pil(out).save(rf"{OUT}\r2_{g}_{body}_{facing}_{tag}.png")
                    iou, edge, mae = c1.score(out, ref)
                    results[key][f"{g}_{tag}"] = {"iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3), **info}
                    tiles[(body, facing, g, tag)] = out
                results[key][f"{g}_round1"] = prev[key][f"{g}_plainneck"]
                results[key][f"{g}_profile_B"] = np.round(B[(body, facing, g)], 2).tolist()
                results[key][f"{g}_profile_truth"] = np.round(pw[(body, facing, g)], 2).tolist()
                results[key][f"{g}_profile_A"] = np.round(A[(body, facing, g)], 2).tolist()
            r = results[key]
            print(key, "ShirtButton IoU/edge: round1", r["ShirtButton_round1"]["iou"], r["ShirtButton_round1"]["edge_px"],
                  "| B", r["ShirtButton_B"]["iou"], r["ShirtButton_B"]["edge_px"], "| A", r["ShirtButton_A"]["iou"], r["ShirtButton_A"]["edge_px"],
                  "| oracle", r["ShirtButton_O"]["iou"], r["ShirtButton_O"]["edge_px"],
                  "| ShirtBasic B", r["ShirtBasic_B"]["iou"], "round1", r["ShirtBasic_round1"]["iou"],
                  "| strokes", r["ShirtButton_B"]["strokes"], "buttons", r["ShirtButton_B"]["buttons"])
    with open(rf"{OUT}\scores2.json", "w") as f:
        json.dump(results, f, indent=1)
    return results, tiles, ALL


def board_holdout(results, tiles):
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    cols = [("vanilla ShirtButton x4", lambda b, f: c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{c1.VANILLA_OF[b].capitalize()}_{f}.png"))),
            ("WDI body (input)", lambda b, f: c1.load(rf"{WS}\Bodies\Naked_{b}_{f}.png")),
            ("ROUND 2: neck from the other two bodies (B)", lambda b, f: tiles[(b, f, "ShirtButton", "B")]),
            ("WDI artist's ShirtButton (truth)", lambda b, f: tiles[(b, f, "ShirtButton", "wdi")]),
            ("ROUND 2: neck map learned on ShirtBasic (A)", lambda b, f: tiles[(b, f, "ShirtButton", "A")]),
            ("ROUND 2: this body's own measured profile (oracle)", lambda b, f: tiles[(b, f, "ShirtButton", "O")]),
            ("ROUND 1 (vanilla opening through the TPS)", lambda b, f: c1.load(rf"{OUT}\ShirtButton_{b}_{f}_plainneck.png")),
            ("ROUND 2 ShirtBasic (B)", lambda b, f: tiles[(b, f, "ShirtBasic", "B")]),
            ("WDI artist's ShirtBasic", lambda b, f: tiles[(b, f, "ShirtBasic", "wdi")])]
    S = 300; pad = 6; left = 160; top = 70
    im = Image.new("RGB", (left + len(cols) * (S + pad), top + 9 * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 2: neck opening redrawn as a spline in the landmark frame, strokes fitted (Douglas-Peucker + Catmull-Rom), buttons as rings. B = body hold-out, A = garment hold-out.", fill=(0, 0, 0), font=fontb)
    for j, (name, _) in enumerate(cols):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    r = 0
    for b in DRAWN:
        for f in FACINGS:
            y = top + r * (S + pad); sc = results[f"{b}_{f}"]
            dr.text((8, y + 8), f"{b}\n{f}", fill=(0, 0, 0), font=fontb)
            s1, sB, sA, sO = sc["ShirtButton_round1"], sc["ShirtButton_B"], sc["ShirtButton_A"], sc["ShirtButton_O"]
            dr.text((8, y + 70), f"round 1:\n IoU {s1['iou']}  edge {s1['edge_px']}\nround 2 B:\n IoU {sB['iou']}  edge {sB['edge_px']}\n lum {sB['lum_mae']}\nround 2 A:\n IoU {sA['iou']}  edge {sA['edge_px']}\noracle:\n IoU {sO['iou']}  edge {sO['edge_px']}\nstrokes {sB['strokes']}\nbuttons {sB['buttons']}", fill=(0, 0, 0), font=font)
            for j, (_, get) in enumerate(cols):
                im.paste(c1.crop_tile(get(b, f), S).convert("RGB"), (left + j * (S + pad), y))
            r += 1
    path = rf"{CAPT}\2026-11-06_crack-round2.png"; im.save(path); print("board", path)


def run_borrowed(ALL):
    bodies = ["Male", "Female", "Thin", "Fat", "Hulk"]; facing = "south"
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    cols = ["vanilla ShirtButton x4", "WDI body (input)", "REBUILT ShirtButton", "REBUILT ShirtBasic", "vanilla ShirtBasic x4"]
    S = 300; pad = 6; left = 160; top = 70
    im = Image.new("RGB", (left + len(cols) * (S + pad), top + len(bodies) * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Borrowed calibration, south, no ground truth: outline, dilation and shading LUT from the donor body, neck profile = mean of the three drawn bodies.", fill=(0, 0, 0), font=fontb)
    for j, name in enumerate(cols):
        dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, body in enumerate(bodies):
        donor = DONOR[body]
        U, V, shade, body_a, cal = prep(body, facing, donor)
        y = top + r * (S + pad)
        dr.text((8, y + 8), f"{body}\n{facing}\ndonor {donor}\nd={int(round(max(0, cal['d'])))} w_out={cal['w_out']:.0f}", fill=(0, 0, 0), font=font)
        vb = c1.VANILLA_OF[body]
        panels = [c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{vb.capitalize()}_{facing}.png")), c1.load(rf"{WS}\Bodies\Naked_{body}_{facing}.png")]
        for g in GARMENTS:
            out, info = rebuild2(body, facing, g, cal, U, V, shade, body_a, ALL[(facing, g)])
            c1.to_pil(out).save(rf"{OUT}\r2_{g}_{body}_{facing}_borrowed.png")
            panels.append(out)
        panels.append(c1.nearest4(c1.load(rf"{CORE}\ShirtBasic_{vb.capitalize()}_{facing}.png")))
        for j, t in enumerate(panels):
            im.paste(c1.crop_tile(t, S).convert("RGB"), (left + j * (S + pad), y))
        print("borrowed", body, "done")
    path = rf"{CAPT}\2026-11-06_crack-borrowed.png"; im.save(path); print("board", path)


if __name__ == "__main__":
    results, tiles, ALL = run_holdout()
    board_holdout(results, tiles)
    run_borrowed(ALL)
