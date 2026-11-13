"""Garments through the relief map, the relief of the WDI body taken from the 3D mesh (2026-11-13, BODY3D.md: 'garment
fitting on Male and Hulk, whose base is good, using the mesh for the relief map and the three baked views as reference').

Same path as garmentmap.py (vanilla garment prepared as in B2, carried by reliefmap.build with EASE px of ease, no clip,
no outline). The only change: on the WDI side the height field is no longer relief3d.height (three-view envelope plus
zones read from the drawing) but the skin of the stack model, read from out/stack3d-mesh.json:
  south  height = z of the front half of each ring above the ring's rim (its two side extremes)
  north  the same for the back half, columns mirrored
  east   height = |x| (the half width at each depth)
The ring points are put in the sprite frame of each view (frame.cxs, cxn, zmean; rows matched by the silhouette's top
and bottom, as reliefmap does) and interpolated. reliefmap.cloth then bridges the hollows, as before. The vanilla side is
unchanged (the vanilla body has no mesh).

Garments: ShirtBasic (vanilla, core17) and trousers. No trousers art is in this tree (vanilla has none, the other mods'
art has no licence), so the trousers are the stand-in of pants.py (a bowl from the vanilla hip row down): they prove
the map below the waist, not a look.

Board per body: Art/work/captures/2026-11-13_garment-map-<Body>.png
  row 1 per facing: WDI sprite | mesh relief lit, sprite silhouette edge in red
  then per garment, per facing: relief from the drawing (as garmentmap.py) | relief from the mesh
Numbers printed and written to out/garment3d.json.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python garment3d.py [Male Hulk]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.interpolate import griddata

import crack as c1, explain5b as e5, fullpass as fp, reliefmap as rm, relief3d as r3
from reliefstudy import area_ratio, WEAK

N = c1.N
fp.GROIN = False
FACINGS = ("south", "east", "north")
SHIRT = "ShirtBasic"
MESH = rf"{c1.OUT}\stack3d-mesh.json"
_BODIES = {}


def entry(body):
    """rings of one body from the big mesh file, cached as out/garment3d-rings-<Body>.npz (the json is 170 MB)"""
    p = rf"{c1.OUT}\garment3d-rings-{body}.npz"
    if os.path.exists(p) and os.path.getmtime(p) >= os.path.getmtime(MESH):
        z = np.load(p)
        return z["pts"], z["ring"], z["seg"], json.loads(str(z["frame"]))
    if not _BODIES:
        with open(MESH, encoding="utf-8") as fh:
            _BODIES.update(json.load(fh)["bodies"])
    e = _BODIES[body]
    stacks = [np.array(e["rows"])]
    for k in ("horns", "legs"):
        if e.get(k):
            stacks += [np.array(e[k]["L"]), np.array(e[k]["R"])]
    pts, ring, seg, n = [], [], [], 0
    for s in stacks:
        s = s.reshape(len(s), -1, 3); seg.append((n, n + len(s)))
        pts.append(s.reshape(-1, 3)); ring.append(np.repeat(np.arange(len(s)) + n, s.shape[1])); n += len(s)
    pts, ring = np.concatenate(pts), np.concatenate(ring)
    np.savez_compressed(p, pts=pts, ring=ring, seg=np.array(seg), frame=json.dumps(e["frame"]))
    return pts, ring, np.array(seg), e["frame"]


def mesh_heights(body, M):
    """{facing: height field in the sprite frame of that facing, over its silhouette M[facing]}"""
    pts, ring, seg, fr = entry(body)
    x, r, z = pts[:, 0], -pts[:, 1], pts[:, 2] + fr["zmean"]
    nr = ring.max() + 1
    # rim of each ring: z at its two side extremes
    zrim = np.zeros(nr)
    for k in range(nr):
        s = ring == k
        zk, xk = z[s], x[s]
        zrim[k] = 0.5 * (zk[np.argmax(xk)] + zk[np.argmin(xk)])
    # the extremes jump from ring to ring (they are single ring points): smoothed along each ring stack, or the height
    # is striped row by row
    for a, b in seg:
        zrim[a:b] = ndi.gaussian_filter1d(ndi.median_filter(zrim[a:b], 9, mode="nearest"), 6.0, mode="nearest")
    dz = z - zrim[ring]
    a0, a1 = r3.rows_of(M["south"])
    out = {}
    for f in FACINGS:
        b0, b1 = r3.rows_of(M[f])
        row = b0 + (r - a0) / max(a1 - a0, 1) * (b1 - b0)
        if f == "south":
            sel = dz >= 0; col = fr["cxs"] + x; h = dz
        elif f == "north":
            sel = dz <= 0; col = fr["cxn"] - x; h = -dz
        else:
            sel = np.ones(len(x), bool); col = z; h = np.abs(x)
        yy, xx = np.mgrid[0:N, 0:N]
        # the outermost point of each pixel first (in profile the inner side of a thigh lies under the outer one)
        ci, ri = np.round(col[sel]).astype(int), np.round(row[sel]).astype(int)
        ok = (ci >= 0) & (ci < N) & (ri >= 0) & (ri < N)
        top = np.full((N, N), -1.0); np.maximum.at(top, (ri[ok], ci[ok]), h[sel][ok])
        py, px = np.nonzero(top >= 0)
        P = np.c_[px, py]; hv = top[py, px]
        g = griddata(P, hv, (xx, yy), method="linear")
        foot = ndi.binary_fill_holes(ndi.binary_closing(top >= 0, iterations=3))   # footprint of the mesh in this view
        g = np.where(np.isfinite(g), g, griddata(P, hv, (xx, yy), method="nearest"))
        out[f] = (ndi.gaussian_filter(np.maximum(g, 0.0), 1.0) * M[f], foot)
    return out


def edge_gap(foot, m):
    """p95 distance (px) between the mesh footprint's edge and the sprite silhouette's edge, both ways"""
    ed = lambda a: a & ~ndi.binary_erosion(a)
    ea, eb = ed(foot), ed(m)
    da, db = ndi.distance_transform_edt(~ea), ndi.distance_transform_edt(~eb)
    return float(np.percentile(np.r_[db[ea], da[eb]], 95))


def build(body, f, mesh):
    """reliefmap.build with the WDI height from the mesh (mesh = {facing: (h, foot)}) or from the drawing (None)"""
    orig = rm.body_side

    def side(b, ff, vanilla, M, imgs):
        if vanilla or mesh is None:
            return orig(b, ff, vanilla, M, imgs)
        un, v = rm.surface_uv(rm.cloth(mesh[ff][0], M[ff]), M[ff])
        return un, v, rm.landmark_rows(b, ff, vanilla, M)

    rm.body_side = side
    try:
        return rm.build(body, f, rm.EASE)
    finally:
        rm.body_side = orig


def weak_of(R):
    r = area_ratio(R["Xs"], R["Ys"], R["mw"])
    inside = ndi.binary_erosion(R["mw"], iterations=2)
    med = float(np.nanmedian(r[inside]))
    return float(np.mean(np.abs(r[inside] - med) > WEAK)), 2 ** med


def trousers_128(vb, f):
    """the stand-in of pants.standin_128 (copied: importing pants.py pulls the whole crack chain)"""
    Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{f}.png")
    vba = Vb[..., 3] > 0.5
    ys, xs = np.where(vba)
    bot, top = ys.max(), ys.min()
    hip = int(round(top + 0.70 * (bot - top)))
    cloth = vba.copy(); cloth[:hip, :] = False
    stroke = cloth & ~ndi.binary_erosion(cloth, iterations=2)
    out = np.zeros((128, 128, 4), np.float32)
    out[..., :3] = (0.33, 0.40, 0.55); out[stroke, :3] = 0.05
    out[..., 3] = cloth.astype(np.float32)
    cx = int(np.median(xs))
    out[hip + 2:hip + 3, :, :3] = np.where(cloth[hip + 2:hip + 3, :, None], 0.15, out[hip + 2:hip + 3, :, :3])
    out[hip + 3:bot - 2, cx, :3] = np.where(cloth[hip + 3:bot - 2, cx, None], 0.20, out[hip + 3:bot - 2, cx, :3])
    return e5.x4(out)


def garment(name, vb, f):
    if name == "Trousers":
        return trousers_128(vb, f)
    Vg = c1.load(rf"{c1.CORE}\{name}_{vb.capitalize()}_{f}.png")
    Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{f}.png")
    fp.G = name
    return fp.prepared(Vg, Vb)


def one(body, font):
    imw = r3.views(body, False)
    M = {k: ndi.binary_fill_holes(imw[k][..., 3] > 0.5) for k in imw}
    mesh = mesh_heights(body, M)
    vb = c1.VANILLA_OF[body]
    stats = {}
    maps = {}
    for f in FACINGS:
        maps[f] = (build(body, f, None), build(body, f, mesh))
        wd, md = weak_of(maps[f][0]); wm, mm = weak_of(maps[f][1])
        stats[f] = {"edge_p95": round(edge_gap(mesh[f][1], M[f]), 2), "weak_drawing": round(wd, 3), "weak_mesh": round(wm, 3),
                    "median_drawing": round(md, 2), "median_mesh": round(mm, 2)}
    ys, xs = np.nonzero(np.any([maps[f][1]["D"] for f in FACINGS], axis=0))
    box = (max(0, xs.min() - 6), max(0, ys.min() - 6), min(N, xs.max() + 6), min(N, ys.max() + 6))

    def tile(im, lab):
        c = im.crop(box); c = c.resize((int(c.width * 1.5), int(c.height * 1.5)), Image.LANCZOS)
        ImageDraw.Draw(c).text((6, 4), lab, fill=(255, 255, 255), font=font)
        return c

    rows = []
    ref = []
    for f in FACINGS:
        ref.append(tile(e5.on_bg(e5.pil(imw[f])), f"{f}: WDI sprite"))
        L = r3.lit(mesh[f][0], M[f])
        edge = M[f] & ~ndi.binary_erosion(M[f])
        L[edge] = (1.0, 0.1, 0.1, 1.0)
        ref.append(tile(e5.on_bg(e5.pil(L)), f"{f}: mesh relief, edge gap p95 {stats[f]['edge_p95']:.1f} px"))
    rows.append(("3D body", ref))
    for g in (SHIRT, "Trousers"):
        tiles = []
        for f in FACINGS:
            Gp = garment(g, vb, f)
            cover = {}
            for key, Mp, lab in (("drawing", maps[f][0], "relief from the drawing"), ("mesh", maps[f][1], "relief from the mesh")):
                W = e5.warp(Gp, Mp["U"], Mp["V"])
                t = e5.pil(imw[f]); t.alpha_composite(e5.pil(W))
                cover[key] = float((np.asarray(e5.pil(W))[..., 3] > 127).sum())
                wk = stats[f]["weak_" + key]
                tiles.append(tile(e5.on_bg(t), f"{f}: {lab}, weak {100 * wk:.0f}%"))
            stats[f][f"{g}_area_mesh_over_drawing"] = round(cover["mesh"] / max(cover["drawing"], 1.0), 3)
        rows.append((g if g != "Trousers" else "Trousers\n(stand-in)", tiles))
    W_ = max(sum(t.width + 8 for t in ts) for _, ts in rows) + 130
    H_ = sum(max(t.height for t in ts) + 10 for _, ts in rows) + 50
    im = Image.new("RGB", (W_, H_), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 10), f"{body}: vanilla garment through the relief map (ease {rm.EASE} px), WDI relief from the drawing against relief from the 3D mesh "
            f"(stack3d). No clip, no outline. Trousers are a stand-in shape.", fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 44
    for lab, ts in rows:
        dr.multiline_text((10, y + 4), lab, fill=(0, 0, 0), font=font); x = 125
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 8
        y += max(t.height for t in ts) + 10
    out = rf"{c1.CAPT}\2026-11-13_garment-map-{body}.png"; im.save(out); print(out)
    for f in FACINGS:
        print(f"  {body:5s} {f:5s}", stats[f])
    return stats


def main():
    bodies = [a for a in sys.argv[1:] if "=" not in a] or ["Male", "Hulk"]
    font = ImageFont.load_default(size=15)
    p = rf"{c1.OUT}\garment3d.json"
    S = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    for b in bodies:
        S[b] = one(b, font)
        with open(p, "w", encoding="utf-8") as fh:
            json.dump(S, fh, indent=1)


if __name__ == "__main__":
    main()
