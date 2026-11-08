"""Round 7 = round 6 hybrid plus: collar block nearest and capped x1.25, cut to its strokes; fabric brought to the
artist's tone and body shading at 0.30; back collar band at its own height. Outputs r7_*, scores7.json, round7 boards.

Round 6, the HYBRID (Fable, 2026-11-06): the vanilla garment's own hand-drawn pixels survive; only the fit is computed.
  fit     : WDI silhouette (body dilated by d), WDI outer outline, opening position and size from neck_table.json
  interior: vanilla garment upscaled x4 (ScaleNx, EPX with colour tolerance), warped by a regularised TPS driven by
            her landmark pairs plus contour correspondences (vanilla cloth edge -> WDI silhouette), gaps filled by
            extending the nearest cloth pixels
  collar  : the vanilla collar and its opening moved as one rigid block (uniform scale + translation) onto the opening
  volume  : WDI body shading multiplied lightly (one strength per facing), pelvis and back crease masked out
  side and back: same, the top closed by the cloth extension when the artist closes it

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python crack6.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

import crack as c1, neck, crack2, crack3, crack4, crack5

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE; VAN = c1.VAN
DRAWN = crack2.DRAWN; GARMENTS = crack2.GARMENTS; FACINGS = crack2.FACINGS; ALL_BODIES = crack5.ALL_BODIES
SHADE_K = {"south": 0.30, "east": 0.30, "north": 0.30}   # round 7: 0.55/0.45 before
EPX_TOL = 0.22


# ---------------------------------------------------------------- ScaleNx (EPX) with tolerance, applied twice = x4
def epx2x(img, tol=EPX_TOL):
    """img: H x W x 4 float, alpha premultiplied inside. Scale2x / EPX with a colour tolerance."""
    H, W, _ = img.shape
    P = np.pad(img, ((1, 1), (1, 1), (0, 0)), mode="edge")
    A = P[:-2, 1:-1]; Bv = P[1:-1, 2:]; C = P[1:-1, :-2]; D = P[2:, 1:-1]; Pc = P[1:-1, 1:-1]
    eq = lambda x, y: np.abs(x - y).sum(-1) < tol
    o1 = np.where((eq(C, A) & ~eq(C, D) & ~eq(A, Bv))[..., None], A, Pc)
    o2 = np.where((eq(A, Bv) & ~eq(A, C) & ~eq(Bv, D))[..., None], Bv, Pc)
    o3 = np.where((eq(D, C) & ~eq(D, Bv) & ~eq(C, A))[..., None], C, Pc)
    o4 = np.where((eq(Bv, D) & ~eq(Bv, A) & ~eq(D, C))[..., None], D, Pc)
    out = np.zeros((H * 2, W * 2, 4), np.float32)
    out[0::2, 0::2] = o1; out[0::2, 1::2] = o2; out[1::2, 0::2] = o3; out[1::2, 1::2] = o4
    return out


def scale4x(rgba):
    pm = rgba.copy(); pm[..., :3] *= pm[..., 3:4]
    up = epx2x(epx2x(pm))
    a = np.maximum(up[..., 3:4], 1e-6)
    out = up.copy(); out[..., :3] = np.clip(up[..., :3] / a, 0, 1); out[..., 3] = up[..., 3]
    return out


# ---------------------------------------------------------------- helpers
def contour_pts(mask):
    c = mask & ~ndi.binary_erosion(mask)
    ys, xs = np.where(c)
    return np.c_[xs + 0.5, ys + 0.5]


def hip_row(body, facing):
    lm = neck.landmarks_both(body, facing)
    if facing == "east":
        p = lm.get("buttock back") or lm.get("belly front")
        return p[1][1] * 4 if p else None
    L, R = lm.get("hip L"), lm.get("hip R")
    return 0.5 * (L[1][1] + R[1][1]) * 4 if L and R else None


def fill_nearest(rgb, have, where):
    """extend the cloth into `where`: multi-scale normalised convolution (smooth continuation of the nearby cloth,
    no radial streaks, never a flat colour)"""
    out = rgb.copy(); known = have.copy()
    for sigma in (2, 4, 8, 16, 32, 64):
        w = known.astype(np.float32)
        num = np.stack([ndi.gaussian_filter(out[..., k] * w, sigma) for k in range(3)], axis=-1)
        den = ndi.gaussian_filter(w, sigma)
        ok = (den > 1e-3) & where & ~known
        out[ok] = num[ok] / den[ok][:, None]
        known |= ok
    return out


def upscale4(rgba, mode="bilinear+unsharp"):
    if mode == "scalenx":
        return scale4x(rgba)
    im = c1.to_pil(rgba).resize((N, N), Image.BILINEAR)
    if mode == "bilinear+unsharp":
        from PIL import ImageFilter
        im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=110, threshold=0))
    return np.asarray(im).astype(np.float32) / 255.0


UPSCALE = "bilinear+unsharp"


# ---------------------------------------------------------------- the hybrid rebuild
def fabric_target(ref_body, facing):
    """median luminance of the artist's own ShirtBasic fabric (light pixels) on the drawn body or the donor"""
    G = c1.load(rf"{WS}\Apparel\ShirtBasic\ShirtBasic_{ref_body}_{facing}.png", N)
    l = c1.lum(G); m = (G[..., 3] > 0.5) & (l > 0.5)
    return float(np.median(l[m])) if m.any() else 0.9


def lighten_to(rgb, where, target, lo=0.35, span=0.25, force_r=None):
    """round 7: bring the median of the light fabric pixels in `where` to `target`, strokes untouched
    (weight 0 under lum 0.35, 1 above 0.60); the darkness is compressed toward white, never clipped"""
    l = rgb.mean(axis=2)
    m = where & (l > 0.5)
    if not m.any():
        return rgb
    med = float(np.median(l[m]))
    if force_r is None and med >= target - 1e-3:
        return rgb
    r = force_r if force_r is not None else (1.0 - target) / max(1e-3, 1.0 - med)
    w = np.clip((l - lo) / span, 0, 1)[..., None]
    lit = 1.0 - (1.0 - rgb) * r
    return rgb * (1 - w) + lit * w


def rebuild6(body, facing, garment, cal, shade, body_a, target_hole, ref_body=None):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{CORE}\{garment}_{vb.capitalize()}_{facing}.png"); Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg); vba = Vb[..., 3] > 0.5
    s_out = int(c1.edge_run(va, vl, ~va))
    fv = neck.frame(body, facing, 0, 1); fw = neck.frame(body, facing, 1, 4)
    hole_v = neck.hole_mask(vba, va, fv, band=neck.BAND[facing], centre_w=0.15 if facing != "east" else 0.35)
    if hole_v.sum():
        lab, n = ndi.label(hole_v)
        if n > 1:
            sizes = ndi.sum(hole_v, lab, range(1, n + 1)); hole_v = lab == (1 + int(np.argmax(sizes)))
    # run 4: the collar block only in front. The artist closes the back and draws only a small front notch in profile,
    # so east and north use the rebuild's opening directly and the vanilla collar lines are warped with the cloth
    use_block = facing == "south"
    grey_src = bool((np.abs(Vg[..., 0] - Vg[..., 2])[va].max() < 0.08) and (np.abs(Vg[..., 0] - Vg[..., 1])[va].max() < 0.08))
    # 1. silhouette and outline (the fit)
    d = int(round(max(0.0, cal["d"])))
    S = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    w_out = cal["w_out"]
    # 2. the vanilla cloth: x4, outer stroke removed (the WDI outline replaces it); the collar zone is cut out of the
    #    base cloth (it comes back as the rigid block) so no collar line is warped twice
    G4 = upscale4(Vg, UPSCALE)
    cloth_a128 = ndi.binary_erosion(va, iterations=max(1, s_out) + 2)       # the dark shading under the vanilla stroke goes too
    cloth_a4 = ndi.binary_erosion(G4[..., 3] > 0.5, iterations=(max(1, s_out) + 2) * 4)
    # the garment's own outer stroke, on the full x4 image, with the opening closed by a cap so it is not eroded
    ga4 = G4[..., 3] > 0.5
    cap4 = np.zeros_like(ga4); cap4[:max(1, int(np.where(ga4.any(axis=1))[0].min())), :] = True
    outer4 = ndi.binary_fill_holes(ga4 | cap4) & ~cap4
    keep4 = ndi.binary_erosion(outer4, iterations=max(1, s_out) * 4) & ga4
    gb = c1.bbox(va)
    if use_block and hole_v.sum() > 4:
        hb_v = c1.bbox(hole_v); m = int(0.6 * (hb_v[2] - hb_v[0] + 1)) + 3
        bx0, bx1 = max(gb[0], hb_v[0] - m), min(gb[2], hb_v[2] + m); by1 = min(gb[3], hb_v[3] + 3)
        cz = np.zeros_like(cloth_a128); cz[:by1 + 1, bx0:bx1 + 1] = True
        cloth_a128 &= ~cz
        cz4 = np.zeros_like(cloth_a4); cz4[:(by1 + 1) * 4, bx0 * 4:(bx1 + 1) * 4] = True
        cloth_a4 &= ~cz4
    # round 7: at the back, a dark collar band drawn across the top of the vanilla garment is not warped with the
    # cloth (it was stretched over the whole top); it is pasted back at its own height, the top filled by light cloth
    band_h = 0
    if facing == "north":
        for y in range(gb[1], min(gb[3], gb[1] + 20) + 1):
            row = vl[y][va[y]]
            if row.size and np.median(row) < 0.5:
                band_h += 1
            else:
                break
        if band_h >= 2:
            cloth_a128[:gb[1] + band_h + 1, :] = False
            cloth_a4[:(gb[1] + band_h + 1) * 4, :] = False
        else:
            band_h = 0
    # 3. warp: landmarks plus contour correspondences (silhouette -> vanilla cloth outer edge)
    src, dst = c1.landmarks(body, facing)
    tps0 = c1.TPS(src, dst)
    outer_v = contour_pts(ndi.binary_fill_holes(ndi.binary_erosion(va, iterations=max(1, s_out))))
    tree = cKDTree(outer_v)
    S_pts = contour_pts(S)[::8]
    q0 = tps0(S_pts)
    _, j = tree.query(q0)
    q = outer_v[j]
    tps = c1.TPS(np.r_[src, S_pts], np.r_[dst, q], lam=4000.0)
    U, V = c1.warp_field(tps)
    coords = [V * 4 - 0.5, U * 4 - 0.5]
    warped = np.stack([ndi.map_coordinates(G4[..., k], coords, order=1, mode="constant", cval=0.0) for k in range(4)], axis=-1)
    warped_a = ndi.map_coordinates(cloth_a4.astype(np.float32), coords, order=1, mode="constant", cval=0.0) > 0.5
    # 4. extend the cloth to the silhouette (nearest cloth pixel, never flat colour)
    # run 4: the extension continues the fabric only, never the drawn strokes (dark pixels are not sampled)
    rgb = fill_nearest(warped[..., :3], warped_a & (c1.lum(warped) > 0.5), S & ~warped_a)
    # 5. the collar block: vanilla collar and opening as one rigid block, sized to the target opening's width
    hole = np.zeros((N, N), bool); block_used = False
    if not use_block and target_hole is not None:
        hole = target_hole.copy()
    if use_block and target_hole is not None and target_hole.sum() > 80 and hole_v.sum() > 4:
        hb_t = c1.bbox(target_hole); hb_v = c1.bbox(hole_v)
        w_t = hb_t[2] - hb_t[0] + 1; w_v4 = (hb_v[2] - hb_v[0] + 1) * 4
        s = float(np.clip(w_t / max(1, w_v4), 0.5, 1.25))    # round 7: never blown up beyond x1.25; the missing width
                                                               # of the collar zone is cloth, the opening is the drawing's
        if hb_t[3] - hb_t[1] >= 10:
            m = int(0.6 * (hb_v[2] - hb_v[0] + 1)) + 3
            x0, x1 = max(gb[0], hb_v[0] - m), min(gb[2], hb_v[2] + m)
            y0, y1 = gb[1], min(gb[3], hb_v[3] + 3)
            blk = G4[y0 * 4:(y1 + 1) * 4, x0 * 4:(x1 + 1) * 4].copy()
            # the block keeps its opening and collar lines; only the garment's outer stroke (computed on the full
            # image, so the crop edges are not edges) is removed
            blk[..., 3] = keep4[y0 * 4:(y1 + 1) * 4, x0 * 4:(x1 + 1) * 4].astype(np.float32) * blk[..., 3]
            bw, bh = int(round(blk.shape[1] * s)), int(round(blk.shape[0] * s))
            # round 7: nearest then a light blur, so the stroke keeps its edge instead of going grey
            im = c1.to_pil(blk).resize((bw, bh), Image.NEAREST)
            blk_s = np.asarray(im).astype(np.float32) / 255.0
            blk_s = np.stack([ndi.gaussian_filter(blk_s[..., k], 0.6) for k in range(4)], axis=-1)
            # place: vanilla hole top centre -> target hole top centre
            cx_v = (0.5 * (hb_v[0] + hb_v[2] + 1) - x0) * 4 * s; cy_v = (hb_v[1] - y0) * 4 * s
            cx_t = 0.5 * (hb_t[0] + hb_t[2] + 1); cy_t = hb_t[1]
            px, py = int(round(cx_t - cx_v)), int(round(cy_t - cy_v))
            canvas = np.zeros((N, N, 4), np.float32)
            sy0, sx0 = max(0, -py), max(0, -px); ty0, tx0 = max(0, py), max(0, px)
            h = min(bh - sy0, N - ty0); w = min(bw - sx0, N - tx0)
            if h > 0 and w > 0:
                canvas[ty0:ty0 + h, tx0:tx0 + w] = blk_s[sy0:sy0 + h, sx0:sx0 + w]
                region = np.zeros((N, N), bool); region[ty0:ty0 + h, tx0:tx0 + w] = True
                ca = canvas[..., 3]
                # the opening = the block's transparent pixels near the target opening (its own free-form shape)
                near = ndi.binary_dilation(target_hole, iterations=14)
                empty = region & (ca < 0.5) & near
                lab, n = ndi.label(empty)
                if n:
                    sizes = ndi.sum(empty & target_hole, lab, range(1, n + 1))
                    hole = np.isin(lab, 1 + np.where(sizes > 20)[0])
                    hole = ndi.binary_fill_holes(hole)
                # blend the block over the warped cloth: feathered on every side of its content, the opening rim hard
                content = ca > 0.3
                ctop = np.zeros_like(content)
                if content.any():
                    ctop[:int(np.where(content.any(axis=1))[0].min()) + 1, :] = True
                filled = ndi.binary_fill_holes(content | ctop) & ~ctop
                # run 5: no fade at the top (the vanilla collar touches the garment's top edge, fading there washed
                # out the collar points); the hard zone around the opening widened to the whole collar
                feather = ndi.distance_transform_edt(filled | ctop).astype(np.float32)
                wgt = np.clip(feather / 18.0, 0, 1) * content
                wgt = np.maximum(wgt, (ndi.distance_transform_edt(~hole) < 24) * content * 1.0) if hole.any() else wgt
                # round 7: the block is cut to its strokes. Only the collar (strokes plus the regions they close with
                # the opening) is pasted; the vanilla shading around it is dropped, the cloth shows there
                strokes = content & (canvas[..., :3].mean(axis=2) < 0.55)
                closed = ndi.binary_fill_holes(strokes | hole | ctop) & ~hole & ~ctop
                collar = (closed | strokes) & content
                lab_c, n_c = ndi.label(collar)
                if n_c:
                    near_hole = ndi.binary_dilation(hole, iterations=6) if hole.any() else np.zeros_like(hole)
                    touch = ndi.sum(collar & near_hole, lab_c, range(1, n_c + 1))
                    collar = np.isin(lab_c, 1 + np.where(touch > 0)[0])
                if collar.sum() > 0.15 * content.sum():
                    wgt = ndi.gaussian_filter(ndi.binary_dilation(collar, iterations=2).astype(np.float32), 1.0) * content
                else:
                    wgt = ndi.gaussian_filter(wgt, 1.5) * content
                rgb = rgb * (1 - wgt[..., None]) + canvas[..., :3] * wgt[..., None]
                block_used = True
    hole &= ndi.binary_dilation(body_a, iterations=2)
    if hole.any() and facing != "south":
        # run 5: where the opening reaches the silhouette border (profile and back), the dilation rim joins the
        # opening, otherwise a thin arc was left floating above the opening (run 5 left a 2 px white hairline:
        # the rim must start at the body itself, not at body + 2)
        rim = S & ~body_a
        hole |= rim & ndi.binary_dilation(hole, iterations=d + 4)
    alpha = S & ~hole
    lab, n = ndi.label(alpha)
    if n > 1:
        sizes = ndi.sum(alpha, lab, range(1, n + 1)); alpha = lab == (1 + int(np.argmax(sizes)))
    # round 7: the back collar band pasted at its own height (x4, no vertical stretch), fitted to the silhouette width
    if band_h:
        ys_s = np.where(S.any(axis=1))[0]; s_top = int(ys_s.min())
        bh4 = band_h * 4
        blkb = G4[gb[1] * 4:(gb[1] + band_h) * 4, gb[0] * 4:(gb[2] + 1) * 4].copy()
        blkb[..., 3] *= keep4[gb[1] * 4:(gb[1] + band_h) * 4, gb[0] * 4:(gb[2] + 1) * 4]
        row = S[min(N - 1, s_top + int(w_out) + bh4 // 2)]
        xs_s = np.where(row)[0]
        if xs_s.size > 8:
            tw = int(xs_s.max() - xs_s.min() + 1)
            bb = np.asarray(c1.to_pil(blkb).resize((tw, bh4), Image.BILINEAR)).astype(np.float32) / 255.0
            canvas_b = np.zeros((N, N, 4), np.float32)
            y0b = s_top + 2; x0b = int(xs_s.min())   # the outline is drawn after and covers the top of the band
            hgt = min(bh4, N - y0b); canvas_b[y0b:y0b + hgt, x0b:x0b + tw] = bb[:hgt]
            wb = canvas_b[..., 3] * S
            wb[y0b + hgt - 3:y0b + hgt, :] *= 0.5
            wb = ndi.gaussian_filter(wb, 0.8)
            rgb = rgb * (1 - wb[..., None]) + canvas_b[..., :3] * wb[..., None]
    # round 7: the fabric is brought to the artist's tone (measured on his ShirtBasic of the body or the donor)
    if ref_body is not None:
        # at the back only the true strokes are spared (the vanilla back is a mid grey flat that the artist paints light)
        # (a fixed compression of the back mid tones was tried: it lightens too much the bodies whose back the artist
        # shades, Fat_Female and Hulk_Female, so the back keeps the median rule; the grey top of the Thin and Female
        # backs is left for the next round)
        rgb = lighten_to(rgb, S & ~hole, fabric_target(ref_body, facing))
    # 6. volume: the WDI body shading, lightly, pelvis and back crease masked
    sh = shade / max(1e-6, np.percentile(shade[body_a], 95))
    sh = np.clip(sh, 0.45, 1.05)
    hr = hip_row(body, facing)
    soft = ndi.gaussian_filter(sh, 14)
    if hr is not None:
        t = np.clip((np.arange(N)[:, None] - (hr - 16)) / 24.0, 0, 1) * np.ones((1, N))
        sh = sh * (1 - t) + soft * t
    k = SHADE_K[facing]
    rgb = rgb * (1 - k * (1 - sh))[..., None]
    # 7. outline (WDI style) on the silhouette edge only
    cov, din = c1.soft_edge(alpha)
    d_outer = ndi.distance_transform_edt(S)
    d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
    w_loc = np.minimum(w_out, np.maximum(4.0, 0.45 * (d_outer + d_hole)))
    outline = np.clip(w_loc + 0.5 - d_outer, 0, 1)
    rgb = rgb * (1 - outline[..., None]) + c1.OUTLINE_RGB * outline[..., None]
    if grey_src:                                  # run 4: a grey vanilla garment stays neutral grey (no tint from resampling)
        rgb = np.repeat(rgb.mean(axis=2, keepdims=True), 3, axis=2)
    out = np.zeros((N, N, 4), np.float32); out[..., :3] = np.clip(rgb, 0, 1); out[..., 3] = cov
    return out, {"block": block_used, "d": d, "hole_px": int(hole.sum())}


# ---------------------------------------------------------------- runs
def target_opening(body, facing, garment, kind, table, tp, B, ALLP, fw, body_a, drawn):
    if facing == "south":
        if kind == "none":
            return None
        row = table[body]; depth = row["v_depth"] if kind == "V" else row["round_depth"]
        return crack5.fillet_loop(fw, kind, depth, row["width"], tp[kind], (N, N))
    prof = (B[(body, facing, garment)] if drawn else ALLP[(facing, garment)]).copy()
    prof[0, prof[0] * fw[3] < 8.0] = 0.0
    return neck.render(fw, neck.XS[facing], prof, body_a) if prof.max() > 0.02 else None


def main():
    pv, pw = crack2.measure_profiles()
    A, B, ALLP, maps = crack2.neck_models(pv, pw)
    loops = crack4.drawn_loops(); table, _ = crack4.load_table(loops)
    with open(rf"{OUT}\scores6.json") as f: s5 = json.load(f)
    results, tiles = {}, {}
    for body in ALL_BODIES:
        drawn = body in DRAWN; donor = None if drawn else crack2.DONOR[body]
        tp = crack4.type_params(loops, exclude=body if drawn else None)
        kinds = {g: crack5.classify_vanilla(body, g) for g in GARMENTS}
        for facing in FACINGS:
            U, V, shade, body_a, cal = crack2.prep(body, facing, donor)
            fw = neck.frame(body, facing, 1, 4)
            for g in GARMENTS:
                th = target_opening(body, facing, g, kinds[g], table, tp, B, ALLP, fw, body_a, drawn)
                out, info = rebuild6(body, facing, g, cal, shade, body_a, th, ref_body=body if drawn else donor)
                c1.to_pil(out).save(rf"{OUT}\r7_{g}_{body}_{facing}.png")
                tiles[(body, facing, g)] = out
                if drawn:
                    ref = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", N); tiles[(body, facing, g, "wdi")] = ref
                    iou, edge, mae = c1.score(out, ref)
                    key = f"{body}_{facing}_{g}"
                    results[key] = {"iou": round(float(iou), 3), "edge_px": round(float(edge), 2), "lum_mae": round(float(mae), 3),
                                    "r6_iou": s5[key]["iou"], "r6_lum": s5[key]["lum_mae"], **info}
                    print(key, json.dumps(results[key]))
        print("done", body)
    with open(rf"{OUT}\scores7.json", "w") as f:
        json.dump(results, f, indent=1)
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    S = 300; pad = 6; left = 170; top = 70
    for facing in FACINGS:
        cols = []
        for g in GARMENTS:
            cols += [(f"vanilla {g} x4", lambda b, g=g: c1.nearest4(c1.load(rf"{CORE}\{g}_{c1.VANILLA_OF[b].capitalize()}_{facing}.png"))),
                     (f"ROUND 7 {g} (hybrid)", lambda b, g=g: tiles[(b, facing, g)]),
                     (f"WDI artist's {g}", lambda b, g=g: tiles[(b, facing, g, "wdi")]),
                     (f"round 6 {g}", lambda b, g=g: c1.load(rf"{OUT}\r6_{g}_{b}_{facing}.png"))]
        im = Image.new("RGB", (left + len(cols) * (S + pad), top + 3 * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((8, 8), f"Round 7 hybrid, {facing}: vanilla pixels x4 (ScaleNx) warped onto the WDI silhouette, collar as a rigid block, body volume multiplied lightly.", fill=(0, 0, 0), font=fontb)
        for j, (name, _) in enumerate(cols):
            dr.text((left + j * (S + pad), 40), name, fill=(0, 0, 0), font=font)
        for r, b in enumerate(DRAWN):
            y = top + r * (S + pad)
            dr.text((8, y + 8), f"{b}\n{facing}", fill=(0, 0, 0), font=fontb)
            txt = ""
            for g in GARMENTS:
                s = results[f"{b}_{facing}_{g}"]
                txt += f"{g}:\n IoU r6 {s['r6_iou']} r7 {s['iou']}\n lum r6 {s['r6_lum']} r7 {s['lum_mae']}\n block {s['block']}\n"
            dr.text((8, y + 60), txt, fill=(0, 0, 0), font=font)
            for j, (_, get) in enumerate(cols):
                im.paste(c1.crop_tile(get(b), S).convert("RGB"), (left + j * (S + pad), y))
        p = rf"{CAPT}\2026-11-06_crack-round7-{facing}.png"; im.save(p); print("board", p)
    # zoom board: collar and placket, vanilla x4 nearest / ours / his, 2x
    Z = 170; zoom = 4
    im = Image.new("RGB", (left + 3 * (Z * zoom + pad), top + 3 * (Z * zoom + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 7 zoom x4 on the collar and placket, ShirtButton south: vanilla x4 nearest, ours (hybrid), the artist", fill=(0, 0, 0), font=fontb)
    for j, name in enumerate(["vanilla x4 nearest", "ROUND 7 hybrid", "WDI artist"]):
        dr.text((left + j * (Z * zoom + pad), 40), name, fill=(0, 0, 0), font=font)
    for r, b in enumerate(DRAWN):
        y = top + r * (Z * zoom + pad); fw = neck.frame(b, "south", 1, 4)
        cx, cy = int(fw[0]), int(fw[1] + 0.5 * fw[3])
        box = (max(0, cx - Z // 2), max(0, cy - Z // 2), min(N, cx + Z // 2), min(N, cy + Z // 2))
        dr.text((8, y + 8), f"{b}\nsouth", fill=(0, 0, 0), font=fontb)
        panels = [c1.nearest4(c1.load(rf"{CORE}\ShirtButton_{c1.VANILLA_OF[b].capitalize()}_south.png")), tiles[(b, "south", "ShirtButton")], tiles[(b, "south", "ShirtButton", "wdi")]]
        for j, t in enumerate(panels):
            back = Image.new("RGBA", (N, N), (78, 98, 78, 255)); back.alpha_composite(c1.to_pil(t))
            im.paste(back.crop(box).resize((Z * zoom, Z * zoom), Image.NEAREST).convert("RGB"), (left + j * (Z * zoom + pad), y))
    p = rf"{CAPT}\2026-11-06_crack-round7-zoom.png"; im.save(p); print("board", p)
    # upscaler board: a 96 px crop of the vanilla ShirtButton Fat collar at nearest, bilinear, ScaleNx, shown x3
    Vg = c1.load(rf"{CORE}\ShirtButton_Fat_south.png")
    crop = (40, 36, 88, 84)
    variants = [("nearest x4", np.asarray(c1.to_pil(Vg).resize((N, N), Image.NEAREST)).astype(np.float32) / 255.0),
                ("bilinear x4", np.asarray(c1.to_pil(Vg).resize((N, N), Image.BILINEAR)).astype(np.float32) / 255.0),
                ("ScaleNx (EPX, tol %.2f) x4" % EPX_TOL, scale4x(Vg)),
                ("bilinear + unsharp x4 (used)", upscale4(Vg, "bilinear+unsharp"))]
    T = (crop[2] - crop[0]) * 4 * 3
    im = Image.new("RGB", (len(variants) * (T + pad), 60 + T), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Upscaler pick, vanilla ShirtButton Fat collar, x4 then shown x3", fill=(0, 0, 0), font=fontb)
    for j, (name, img) in enumerate(variants):
        dr.text((j * (T + pad), 38), name, fill=(0, 0, 0), font=font)
        back = Image.new("RGBA", (N, N), (78, 98, 78, 255)); back.alpha_composite(c1.to_pil(img))
        im.paste(back.crop((crop[0] * 4, crop[1] * 4, crop[2] * 4, crop[3] * 4)).resize((T, T), Image.NEAREST).convert("RGB"), (j * (T + pad), 60))
    p = rf"{CAPT}\2026-11-06_crack-round7-upscalers.png"; im.save(p); print("board", p)
    # all bodies
    cols = [(f, g) for f in FACINGS for g in GARMENTS]; S2 = 240
    im = Image.new("RGB", (left + len(cols) * (S2 + pad), top + len(ALL_BODIES) * (S2 + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 7 hybrid, all eight WDI bodies, three facings, two garments", fill=(0, 0, 0), font=fontb)
    for j, (f, g) in enumerate(cols):
        dr.text((left + j * (S2 + pad), 40), f"{g} {f}", fill=(0, 0, 0), font=font)
    for r, b in enumerate(ALL_BODIES):
        y = top + r * (S2 + pad)
        dr.text((8, y + 8), f"{b}\n{'drawn by WDI' if b in DRAWN else 'donor ' + crack2.DONOR[b]}", fill=(0, 0, 0), font=font)
        for j, (f, g) in enumerate(cols):
            im.paste(c1.crop_tile(tiles[(b, f, g)], S2).convert("RGB"), (left + j * (S2 + pad), y))
    p = rf"{CAPT}\2026-11-06_crack-round7-all.png"; im.save(p); print("board", p)


if __name__ == "__main__":
    main()
