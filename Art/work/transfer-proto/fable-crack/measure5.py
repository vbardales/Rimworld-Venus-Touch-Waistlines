"""Round 5 measurements on the WDI artist's drawings (Fable, 2026-11-06).
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python measure5.py
"""
import numpy as np
from scipy import ndimage as ndi
import crack as c1, neck, crack2

N = c1.N; WS = c1.WS
DRAWN = crack2.DRAWN


def lum(img): return img[..., :3].mean(axis=2)


for facing in ["south", "east", "north"]:
    print(f"===================== {facing}")
    for body in DRAWN:
        B = c1.load(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
        shade, body_a, rim, body_inner = c1.body_shading(B)
        src, dst = c1.landmarks(body, facing); tps = c1.TPS(src, dst); U, V = c1.warp_field(tps)
        cal, _ = c1.calibrate(body, facing, tps, U, V, B, shade, body_a, body_inner)
        fw = neck.frame(body, facing, 1, 4); ox, oy, xu, yu = fw
        bl = lum(B)
        for g in ["ShirtBasic", "ShirtButton"]:
            G = c1.load(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", N)
            ga = G[..., 3] > 0.5; gl = lum(G)
            g_din = ndi.distance_transform_edt(ga)
            hole = neck.hole_mask(body_a, ga, fw, band=1.05 if facing != "east" else 1.9, centre_w=0.15 if facing != "east" else 0.35)
            hole = ndi.binary_opening(hole, iterations=3) if hole.sum() else hole
            d_hole = ndi.distance_transform_edt(~hole) if hole.sum() else np.full((N, N), 1e9)
            inner = ga & (g_din > cal["w_out"] + 3) & (d_hole > 3)
            pred = np.interp(shade, cal["lut_x"], cal["lut_y"])
            # (a) residual per y band (frame units below the neck row)
            ys = (np.arange(N)[:, None] + 0.5 - oy) / yu * np.ones((1, N))
            bands = [(-0.4, -0.2), (-0.2, 0.0), (0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0), (1.0, 1.3), (1.3, 1.6), (1.6, 2.0), (2.0, 2.5), (2.5, 3.2)]
            res = []
            for a, b in bands:
                sel = inner & (ys >= a) & (ys < b) & (gl > 0.5)
                res.append(f"{(gl[sel] - pred[sel]).mean():+.3f}" if sel.sum() > 50 else "  .   ")
            print(f"{body:12s} {g:11s} residual by y band {[f'{a:.1f}' for a, _ in bands]}\n{'':24s} {res}")
            # (b) crease softness: body creases (body lum < 0.6 inside) -> garment darkness there vs fabric
            fabric_sel = inner & (bl > 0.85) & body_inner; crease_sel = inner & (bl < 0.6) & body_inner
            if crease_sel.sum() > 30 and fabric_sel.sum() > 30:
                gf, gc, bf, bc = gl[fabric_sel].mean(), gl[crease_sel].mean(), bl[fabric_sel].mean(), bl[crease_sel].mean()
                print(f"{'':24s} crease: body {bf:.2f}->{bc:.2f} (drop {bf-bc:.2f}), garment {gf:.2f}->{gc:.2f} (drop {gf-gc:.2f}), ratio {(gf-gc)/max(1e-6,bf-bc):.2f}, n={int(crease_sel.sum())}")
            if facing == "south" and hole.sum():
                hb = c1.bbox(hole)
                # (c) thin dark lines near the opening: offset from the hole edge by vertical position t along the opening
                thin = ga & (gl < 0.6) & (g_din > cal["w_out"] + 2) & (d_hole > 2) & (d_hole < 45)
                t = (np.arange(N)[:, None] - hb[1]) / max(1, hb[3] - hb[1]) * np.ones((1, N))
                rows = []
                for a, b in [(-0.3, 0.0), (0.0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 1.2)]:
                    sel = thin & (t >= a) & (t < b)
                    rows.append(f"{np.median(d_hole[sel]):.0f}px(n{int(sel.sum())})" if sel.sum() > 10 else ".")
                print(f"{'':24s} thin lines offset from the hole edge by t along the opening: {rows}")
                # (f) collar band: lum along the centre column from the hole top upward
                x0 = int(ox); col = []
                for dy in range(2, 40, 4):
                    y = hb[1] - dy
                    if y >= 0 and ga[y, x0]: col.append(f"{dy}:{gl[y, x0]:.2f}")
                print(f"{'':24s} centre column above the hole top (px:lum): {col}")
                # (e) rim: dark run outward from the hole edge along the centre column below the hole bottom and at the sides
                runs = []
                for (yy, xx, dxx, dyy) in [(hb[3] + 1, x0, 0, 1), ((hb[1] + hb[3]) // 2, hb[0] - 1, -1, 0), ((hb[1] + hb[3]) // 2, hb[2] + 1, 1, 0)]:
                    n = 0; y, x = yy, xx
                    while 0 <= y < N and 0 <= x < N and ga[y, x] and gl[y, x] < 0.5 and n < 40: n += 1; y += dyy; x += dxx
                    runs.append(n)
                prof = []
                for dd in range(0, 36, 3):
                    sel = ga & (d_hole >= dd) & (d_hole < dd + 3) & (np.arange(N)[:, None] > hb[3] - 10)
                    prof.append(f"{gl[sel].mean():.2f}" if sel.sum() > 10 else ".")
                print(f"{'':24s} rim dark runs (below, left, right) {runs} px; lum by distance from the hole edge (3 px steps): {prof}")
                # (d) buttons: small dark rings below the hole
                lab, n = ndi.label((gl < 0.6) & ga & (g_din > cal["w_out"] + 2) & (np.arange(N)[:, None] > hb[3] + 4))
                btn = []
                for i in range(1, n + 1):
                    yy, xx = np.where(lab == i)
                    h, w = np.ptp(yy) + 1, np.ptp(xx) + 1
                    if 5 <= h <= 16 and 5 <= w <= 16 and 0.6 <= w / h <= 1.6:
                        btn.append((round((xx.mean() + 0.5 - ox) / abs(xu), 2), round((yy.mean() + 0.5 - hb[3]) / yu, 2)))
                print(f"{'':24s} buttons (x' in shoulder units, y below the hole bottom in y units): {btn}; hole bottom y'={(hb[3]-oy)/yu:.2f}")
