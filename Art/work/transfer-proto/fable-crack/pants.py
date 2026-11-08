"""Trousers on the WDI bodies, same hybrid as the shirt (round 8), first pass (2026-11-06, night run).

  fit      : silhouette = WDI body dilated by the body's d (shirt calibration, donor for the borrowed bodies), kept
             from the WAIST line down to the body bottom (crotch notch included, as the artist's own garments do)
  waist    : the top edge of WDI's boxers (UWUnderwear, drawn for all eight bodies and three facings), smoothed and
             extended to the silhouette width. It plays the part of the YELLOW line.
  interior : the trousers texture at 128 px, x4, warped by the landmark TPS plus contour correspondences, extended
             to the silhouette, WDI body shading multiplied at 0.30, WDI outline on every edge (the waist too)
  source   : Art\\work\\pants\\<Name>_<Male|Female|Thin|Fat|Hulk>_<facing>.png when present (AB, XND, catMonke
             Pants as VTW redraws them). NOT PRESENT TONIGHT: a stand-in is synthesised from the vanilla body (a
             bowl from the vanilla hip row to the bottom, grey 0.45, 2 px stroke, flat top) and the boards say so.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python pants.py [Name]
Outputs out\\p1_<Name>_<Body>_<facing>.png, board Art\\work\\captures\\2026-11-06_crack-pants1.png
"""
import os, sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

import crack as c1, neck, crack2, crack5, crack6

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; VAN = c1.VAN
PANTS = c1.MOD + r"\Art\work\pants"
FACINGS = crack2.FACINGS; ALL_BODIES = crack5.ALL_BODIES; DRAWN = crack2.DRAWN
SHADE_K = 0.30
STANDIN_GREY = 0.45


def boxers(body, facing):
    # on Virginie's machine: the workshop item's Textures\UWUnderwear\boxers (png beside the dds, or converted)
    for p in (rf"{WS}\Apparel\boxers\boxers_{body}_{facing}.png", rf"{WS}\..\..\..\UWUnderwear\boxers\boxers_{body}_{facing}.png"):
        if os.path.exists(p):
            return c1.load(p, N)
    return None


def waist_curve(body, facing, S):
    """row of the waist per column over the silhouette width: the boxers' top edge, smoothed, extended sideways"""
    bx = boxers(body, facing)
    ba = bx[..., 3] > 0.5
    top = np.full(N, np.nan)
    for x in range(N):
        ys = np.where(ba[:, x])[0]
        if ys.size:
            top[x] = ys.min()
    ok = ~np.isnan(top)
    xs = np.where(ok)[0]
    top[~ok] = np.interp(np.where(~ok)[0], xs, top[ok])
    top = ndi.gaussian_filter1d(top, 3.0)
    return top


def standin_128(vb, facing):
    """a trousers texture made up from the vanilla body: a bowl from the hip row down, flat top, 2 px stroke"""
    Vb = c1.load(rf"{VAN}\vanilla-{vb}-{facing}.png")
    vba = Vb[..., 3] > 0.5
    ys, xs = np.where(vba)
    bot = ys.max(); top = ys.min()
    hip = int(round(top + 0.70 * (bot - top)))              # roughly where AB's Pants start (rows 88 to 107 of 128)
    cloth = vba.copy(); cloth[:hip, :] = False
    stroke = cloth & ~ndi.binary_erosion(cloth, iterations=2)
    out = np.zeros((128, 128, 4), np.float32)
    out[..., :3] = STANDIN_GREY; out[stroke, :3] = 0.05
    out[..., 3] = cloth.astype(np.float32)
    # a lighter fold line down the middle and a belt line under the top stroke, so the warp has something to show
    cx = int(np.median(xs))
    out[hip + 2:hip + 3, :, :3] = np.where(cloth[hip + 2:hip + 3, :, None], 0.20, out[hip + 2:hip + 3, :, :3])
    out[hip + 3:bot - 2, cx, :3] = np.where(cloth[hip + 3:bot - 2, cx, None], 0.30, out[hip + 3:bot - 2, cx, :3])
    return out


def load_source(name, vb, facing):
    p = rf"{PANTS}\{name}_{vb.capitalize()}_{facing}.png"
    if os.path.exists(p):
        return c1.load(p), False
    return standin_128(vb, facing), True


def rebuild_pants(body, facing, name, cal, shade, body_a):
    vb = c1.VANILLA_OF[body]
    Vg, standin = load_source(name, vb, facing)
    va = Vg[..., 3] > 0.5; vl = c1.lum(Vg)
    s_out = 2 if standin else int(min(5, max(1, c1.edge_run(va, vl, ~va))))   # the stroke width of the source
    d = int(round(max(0.0, cal["d"]))); w_out = cal["w_out"]
    Sd = ndi.binary_dilation(body_a, iterations=d) if d > 0 else body_a.copy()
    waist = waist_curve(body, facing, Sd)
    rows = np.arange(N)[:, None]
    S = Sd & (rows >= waist[None, :])
    lab, n = ndi.label(S)
    if n > 1:
        sizes = ndi.sum(S, lab, range(1, n + 1)); S = lab == (1 + int(np.argmax(sizes)))
    # the source cloth without its own stroke (the WDI outline replaces it)
    G4 = crack6.upscale4(Vg, crack6.UPSCALE)
    cloth_a4 = ndi.binary_erosion(G4[..., 3] > 0.5, iterations=max(1, s_out) * 4 + 2)
    # warp: landmarks plus contour correspondences (silhouette -> source cloth outer edge)
    src, dst = c1.landmarks(body, facing)
    tps0 = c1.TPS(src, dst)
    outer_v = crack6.contour_pts(ndi.binary_fill_holes(ndi.binary_erosion(va, iterations=max(1, s_out))))
    tree = cKDTree(outer_v)
    S_pts = crack6.contour_pts(S)[::6]
    q0 = tps0(S_pts)
    _, j = tree.query(q0)
    q = outer_v[j]
    tps = c1.TPS(np.r_[src, S_pts], np.r_[dst, q], lam=4000.0)
    U, V = c1.warp_field(tps)
    coords = [V * 4 - 0.5, U * 4 - 0.5]
    warped = np.stack([ndi.map_coordinates(G4[..., k], coords, order=1, mode="constant", cval=0.0) for k in range(4)], axis=-1)
    warped_a = ndi.map_coordinates(cloth_a4.astype(np.float32), coords, order=1, mode="constant", cval=0.0) > 0.5
    rgb = crack6.fill_nearest(warped[..., :3], warped_a & (c1.lum(warped) > 0.15), S & ~warped_a)
    # volume: the WDI body shading, lightly; the crease under the hip row softened as for the shirt
    sh = shade / max(1e-6, np.percentile(shade[body_a], 95))
    sh = np.clip(sh, 0.45, 1.05)
    hr = crack6.hip_row(body, facing)
    soft = ndi.gaussian_filter(sh, 14)
    if hr is not None:
        t = np.clip((np.arange(N)[:, None] - (hr - 16)) / 24.0, 0, 1) * np.ones((1, N))
        sh = sh * (1 - t) + soft * t
    rgb = rgb * (1 - SHADE_K * (1 - sh))[..., None]
    # outline on every edge of the trousers, the waist included
    cov, din = c1.soft_edge(S)
    d_in = ndi.distance_transform_edt(S)
    outline = np.clip(w_out + 0.5 - d_in, 0, 1)
    rgb = rgb * (1 - outline[..., None]) + c1.OUTLINE_RGB * outline[..., None]
    out = np.zeros((N, N, 4), np.float32); out[..., :3] = np.clip(rgb, 0, 1); out[..., 3] = cov
    return out, {"standin": standin, "d": d, "waist_mid": float(waist[N // 2])}


def over_body(body, facing, tile):
    B = c1.to_pil(c1.load(rf"{WS}\Bodies\Naked_{body}_{facing}.png"))
    back = Image.new("RGBA", (N, N), (78, 98, 78, 255)); back.alpha_composite(B); back.alpha_composite(c1.to_pil(tile))
    return back


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "Pants"
    tiles, info = {}, {}
    for body in ALL_BODIES:
        donor = None if body in DRAWN else crack2.DONOR[body]
        for facing in FACINGS:
            U, V, shade, body_a, cal = crack2.prep(body, facing, donor)
            out, inf = rebuild_pants(body, facing, name, cal, shade, body_a)
            c1.to_pil(out).save(rf"{OUT}\p1_{name}_{body}_{facing}.png")
            tiles[(body, facing)] = out; info[(body, facing)] = inf
            print(body, facing, inf)
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    S = 210; pad = 6; left = 170; top = 70
    cols = [(f, k) for f in FACINGS for k in ("body", "boxers", "ours", "alone")]
    im = Image.new("RGB", (left + len(cols) * (S + pad), top + len(ALL_BODIES) * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    standin = any(v["standin"] for v in info.values())
    dr.text((8, 8), f"Trousers pass 1, {name}: WDI silhouette from the artist's boxers waist down to the body bottom, hybrid interior, outline and shading WDI."
                    + ("  SOURCE = STAND-IN (no trousers texture under Art/work/pants tonight)" if standin else ""), fill=(0, 0, 0), font=fontb)
    labels = {"body": "WDI body", "boxers": "artist's boxers (waist reference)", "ours": "OURS over the body", "alone": "ours alone"}
    for j, (f, k) in enumerate(cols):
        dr.text((left + j * (S + pad), 40), f"{labels[k]} {f}", fill=(0, 0, 0), font=font)
    for r, b in enumerate(ALL_BODIES):
        y = top + r * (S + pad)
        dr.text((8, y + 8), f"{b}\n{'drawn by WDI' if b in DRAWN else 'donor ' + crack2.DONOR[b]}", fill=(0, 0, 0), font=font)
        for j, (f, k) in enumerate(cols):
            if k == "body":
                t = over_body(b, f, np.zeros((N, N, 4), np.float32))
            elif k == "boxers":
                t = over_body(b, f, boxers(b, f))
            elif k == "ours":
                t = over_body(b, f, tiles[(b, f)])
            else:
                t = Image.new("RGBA", (N, N), (78, 98, 78, 255)); t.alpha_composite(c1.to_pil(tiles[(b, f)]))
            im.paste(t.resize((S, S), Image.LANCZOS).convert("RGB"), (left + j * (S + pad), y))
    p = rf"{CAPT}\2026-11-06_crack-pants1.png"; im.save(p); print("board", p)


if __name__ == "__main__":
    main()
