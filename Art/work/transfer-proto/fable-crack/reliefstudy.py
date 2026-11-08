"""Points at regular intervals on the relief map, and a point added only where a weak zone resists (Virginie 2026-11-08:
'étudie surtout la manière d'obtenir des points à intervalles réguliers pour compléter la heatmap ... deux types de
points : en bordure, les points clé et dans les zones vides ... ajouter des points seulement là où une zone de faiblesse
résiste').

The relief map (reliefmap.build) is dense: every WDI pixel has its vanilla pixel. The points here do not drive it, they
SAMPLE it, so the weak zones (local area change) can be read at points instead of over a cloud:
  border   : across = -1 and +1 (the two edges), every STEP px of surface height on the vanilla body
  key      : her landmarks of the study (all the placed ones, the kept ones marked)
  empty    : a lattice inside, every STEP px across and down on the vanilla surface
Each sample is placed on the vanilla body (its surface coordinates) and on the WDI body (the WDI pixel whose vanilla
pixel is nearest), and reads the area ratio there: |log2| > WEAK (x1.5) is weak, measured relative to the facing's
median ratio (the whole WDI torso is smaller or larger on the surface: that global factor is not a weakness).

A weak zone RESISTS when a band of rows between two consecutive height anchors keeps more than RESIST of its samples
weak, in the same direction (all squeezed or all stretched on one side, the opposite on the other: the anchor between them
sits at the wrong height for the volumes). Then ONE point is added in that band: an extra height anchor at the band's
middle WDI row, whose vanilla row is the one with the same SURFACE AREA fraction between the two anchors (area, not
height: the point that equalises the squeeze on both sides). Round 2 reruns with the extras (reliefmap.EXTRA).

Outputs, per body: board Art/work/captures/2026-11-08_reliefstudy-<Body>.png
  row per facing: vanilla body with the samples | WDI body with the samples coloured by weakness (round 1) | the weak
  map round 1 with the anchors | the WDI samples round 2 (extras in yellow) | the weak map round 2
and out/reliefstudy.json (samples, weak counts, extras, per body and facing); the summary table printed.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python run_linux.py reliefstudy.py [Body ...|all]
"""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import crack as c1, explain5b as e5, relief3d as r3, reliefmap as rm, fullpass as fp

N = c1.N
STEP = 32           # px of vanilla surface between samples (8 vanilla px)
ACROSS = 5          # inside samples per row between the two edges (across = -2/3 .. +2/3)
WEAK = 0.58         # |log2 area ratio| above this is weak (x1.5), relative to the facing's median
RESIST = 0.35       # share of a band's samples weak in one direction for the band to resist
MIN_BAND = 24       # px: a band narrower than this gets no extra anchor
BODIES = ["Male", "Female", "Thin", "Fat", "Hulk", "Thin_Female", "Fat_Female", "Hulk_Female"]
fp.GROIN = False    # the groin creases are not height anchors (reliefmap.KEEP); their waistband fix needs the underwear sprites


def area_ratio(Xs, Ys, mw):
    """log2 of (WDI pixel area / the vanilla area it takes), on the WDI body"""
    Uy, Ux = np.gradient(np.where(mw, Xs, np.nan)); Vy, Vx = np.gradient(np.where(mw, Ys, np.nan))
    J = np.abs(Ux * Vy - Uy * Vx)
    return np.log2(np.clip(1.0 / np.maximum(np.nan_to_num(J, nan=1.0), 1e-6), 1 / 8, 8))


def samples(body, f, Rm):
    """the three kinds of samples: (kind, name, vanilla xy, WDI xy) at 512"""
    unv, vv, mv, mw = Rm["unv"], Rm["vv"], Rm["mv"], Rm["mw"]
    yv, xv = np.nonzero(mv)
    tree_v = cKDTree(np.c_[unv[yv, xv] * 100.0, vv[yv, xv]])      # across scaled so 0.01 ~ 1 px of height
    yw, xw = np.nonzero(mw)
    tree_w = cKDTree(np.c_[Rm["Xs"][yw, xw], Rm["Ys"][yw, xw]])
    out = []

    def place(kind, name, u, v):
        _, i = tree_v.query([u * 100.0, v]); pv = (int(xv[i]), int(yv[i]))
        _, j = tree_w.query([pv[0], pv[1]]); pw = (int(xw[j]), int(yw[j]))
        out.append((kind, name, pv, pw))

    vmax = float(np.nanmax(vv))
    for v in np.arange(STEP / 2, vmax, STEP):
        place("border", f"L{int(v)}", -1.0, v); place("border", f"R{int(v)}", 1.0, v)
        for u in np.linspace(-1, 1, ACROSS + 2)[1:-1]:          # the inside, ACROSS columns between the two edges
            place("empty", f"E{int(v)}_{u:+.2f}", u, v)
    s, d, names = e5.named_pairs(body, f)
    P = d * 4
    for i, n in enumerate(names):
        if n in ("top", "bottom", "leftmost", "rightmost"):
            continue
        x, y = int(round(P[i, 0])), int(round(P[i, 1]))
        if 0 <= y < N and 0 <= x < N and mv[y, x]:
            u, v = unv[y, x], vv[y, x]
            place("key" if n in rm.KEEP else "placed", n, u, v)
    return out


STROKE = 12         # px at 512: the WDI outline's width; a border sample reads the map on the fabric side of it


def weak_at(S, r, mw):
    """the area ratio at each sample's WDI position (median of 5 x 5), relative to the facing's median. A border sample
    reads it STROKE px towards the row's middle: the black stroke itself (4 px on vanilla, 12 on WDI) is stretched by
    construction, the garment's own edge is redrawn there, so what matters is the fabric next to it"""
    inside = ndi.binary_erosion(mw, iterations=2)
    med = float(np.nanmedian(r[inside]))
    rr = np.where(mw, r, np.nan)
    vals = []
    for kind, name, pv, (x, y) in S:
        if kind == "border":
            xl, xr = r3.extent(mw, y); x = x + STROKE if x - xl < xr - x else x - STROKE
        w = rr[max(0, y - 2):y + 3, max(0, x - 2):x + 3]
        vals.append(float(np.nanmedian(w)) - med if np.isfinite(w).any() else 0.0)
    return np.array(vals), med


def filled(Rm):
    """the border check: every WDI edge pixel takes a vanilla pixel INSIDE the vanilla silhouette (the border is filled
    by the map, no edge pixel left pointing outside the vanilla art)"""
    mw, mv = Rm["mw"], Rm["mv"]
    edge = mw & ~ndi.binary_erosion(mw)
    ys, xs = np.nonzero(edge)
    xv = np.clip(Rm["Xs"][ys, xs].round().astype(int), 0, N - 1); yv = np.clip(Rm["Ys"][ys, xs].round().astype(int), 0, N - 1)
    ok = mv[yv, xv]
    return int(ok.sum()), int(len(ok))


def anchors_rows(body, f, Rm):
    """{name: (vanilla row, WDI row)} of the height anchors in use (common names, both views)"""
    cache = rm.build.__defaults__[1]
    imw, imv, Mw, Mv = cache[body]
    Rw = rm.landmark_rows(body, f, False, Mw); Rv = rm.landmark_rows(body, f, True, Mv)
    out = {n: (Rv[n], Rw[n]) for n in Rw if n in Rv}
    y0w, y1w = r3.rows_of(Mw[f]); y0v, y1v = r3.rows_of(Mv[f])
    out["_top"] = (float(y0v), float(y0w)); out["_bottom"] = (float(y1v), float(y1w))
    return out


def surface_area_cum(h, m):
    """cumulative surface area down the rows (sum over the row of the surface element)"""
    hy, hx = np.gradient(h)
    hx = np.clip(hx, -5, 5); hy = np.clip(hy, -5, 5)
    el = np.sqrt(1 + hx ** 2 + hy ** 2) * m
    return np.cumsum(el.sum(axis=1))


def propose(body, f, Rm, S, w, A):
    """one extra anchor per band that resists: (name, vanilla row, WDI row), with the band's reading"""
    cache = rm.build.__defaults__[1]
    imw, imv, Mw, Mv = cache[body]
    hw = rm.cloth(r3.height(f, Mw, rm.pts_of(body, f, False), c1.lum(imw[f])), Mw[f])
    hv = rm.cloth(r3.height(f, Mv, rm.pts_of(body, f, True), c1.lum(imv[f])), Mv[f])
    # the profile has a height scale per half (front, back): its bands are judged and anchored per half; the WDI
    # sample's side is its across sign (east: the front is on the right, across > 0)
    unw, _ = rm.surface_uv(hw, Mw[f]); unv, _ = rm.surface_uv(hv, Mv[f])
    halves = [("", None, None, None)] if f != "east" else \
        [("front", lambda n: "back" not in n, unw > 0, unv > 0), ("back", lambda n: "front" not in n, unw < 0, unv < 0)]
    extras, bands = {}, []
    for tag, keepf, hw_m, hv_m in halves:
        Aw = surface_area_cum(hw, Mw[f] if hw_m is None else (Mw[f] & hw_m))
        Av = surface_area_cum(hv, Mv[f] if hv_m is None else (Mv[f] & hv_m))
        rows = sorted((t for n, t in A.items() if keepf is None or keepf(n) or n.startswith("_")), key=lambda t: t[1])
        rows = [rows[0]] + [t for p, t in zip(rows, rows[1:]) if t[1] > p[1] + 2 and t[0] > p[0] + 2]
        side = np.array([True if hw_m is None else bool(hw_m[pw[1], pw[0]]) for _, _, _, pw in S])
        for (rv0, rw0), (rv1, rw1) in zip(rows, rows[1:]):
            if rw1 - rw0 < MIN_BAND:
                continue
            inb = np.array([rw0 <= pw[1] < rw1 for _, _, _, pw in S]) & side
            if inb.sum() < 4:
                continue
            ww = w[inb]
            sq, st = float(np.mean(ww < -WEAK)), float(np.mean(ww > WEAK))
            bands.append((tag, int(rw0), int(rw1), int(inb.sum()), sq, st))
            if max(sq, st) < RESIST:
                continue
            # the band's middle WDI row; the vanilla row with the same area fraction between the two anchors
            rw = 0.5 * (rw0 + rw1)
            aw0, aw1 = Aw[int(rw0)], Aw[int(rw1)]
            t = (np.interp(rw, np.arange(N), Aw) - aw0) / max(aw1 - aw0, 1e-6)
            seg = Av[int(rv0):int(rv1) + 1]
            rv = rv0 + float(np.interp(t, (seg - seg[0]) / max(seg[-1] - seg[0], 1e-6), np.arange(len(seg))))
            name = f"X:{tag}:{int(rw)}" if tag else f"X:{int(rw)}"
            extras[name] = (round(rv, 1), round(rw, 1))
    return extras, bands


def heat(r, mw, med):
    tt = np.clip(np.where(mw, r - med, 0), -1, 1)
    hm = np.zeros((N, N, 4), np.float32)
    hm[..., 0] = np.where(tt > 0, 1, 1 + tt); hm[..., 1] = 1 - np.abs(tt); hm[..., 2] = np.where(tt < 0, 1, 1 - tt)
    hm[..., 3] = mw
    return e5.on_bg(e5.pil(hm))


def dots(im, S, w, side, extra_rows=(), anchors=None, font=None):
    dr = ImageDraw.Draw(im)
    if anchors:
        for n, (rv, rw) in anchors.items():
            y = rv if side == 0 else rw
            dr.line((0, y, N, y), fill=(255, 200, 0) if n.startswith("X:") else (90, 90, 90), width=1)
    for (kind, name, pv, pw), ww in zip(S, w):
        x, y = pv if side == 0 else pw
        col = (60, 200, 60)
        if ww > WEAK: col = (230, 40, 40)
        if ww < -WEAK: col = (40, 60, 230)
        r_ = {"border": 4, "empty": 3, "key": 5, "placed": 5}[kind]
        if kind in ("key", "placed"):
            dr.rectangle((x - r_, y - r_, x + r_, y + r_), fill=col if kind == "key" else None, outline=(0, 0, 0) if kind == "key" else col, width=2)
        elif kind == "border":
            dr.ellipse((x - r_, y - r_, x + r_, y + r_), fill=col, outline=(0, 0, 0))
        else:
            dr.ellipse((x - r_, y - r_, x + r_, y + r_), fill=col)
    return im


def study(body, font):
    rows = []; rep = {}
    for f in ("south", "east", "north"):
        rm.EXTRA.pop((body, f), None)
        R1 = rm.build(body, f)
        r1 = area_ratio(R1["Xs"], R1["Ys"], R1["mw"])
        S = samples(body, f, R1)
        w1, med1 = weak_at(S, r1, R1["mw"])
        A1 = anchors_rows(body, f, R1)
        ex, bands = propose(body, f, R1, S, w1, A1)
        rm.EXTRA[(body, f)] = ex
        R2 = rm.build(body, f) if ex else R1
        r2 = area_ratio(R2["Xs"], R2["Ys"], R2["mw"])
        # the same vanilla samples, placed again on the WDI side of round 2
        yw, xw = np.nonzero(R2["mw"]); tw = cKDTree(np.c_[R2["Xs"][yw, xw], R2["Ys"][yw, xw]])
        S2 = []
        for kind, name, pv, pw in S:
            _, j = tw.query([pv[0], pv[1]]); S2.append((kind, name, pv, (int(xw[j]), int(yw[j]))))
        w2, med2 = weak_at(S2, r2, R2["mw"])
        A2 = anchors_rows(body, f, R2)
        inside = ndi.binary_erosion(R1["mw"], iterations=2)
        def stats(w, r, med):
            k = np.array([s[0] for s in S])
            return {"median_ratio": round(2 ** med, 3),
                    "weak_share_map": round(float(np.mean(np.abs(r[inside] - med) > WEAK)), 3),
                    "weak": {kind: [int(np.sum((k == kind) & (w > WEAK))), int(np.sum((k == kind) & (w < -WEAK))), int(np.sum(k == kind))]
                             for kind in ("border", "key", "placed", "empty")}}
        rep[f] = {"round1": stats(w1, r1, med1), "round2": stats(w2, r2, med2), "extras": ex,
                  "border_filled": list(filled(R1)),
                  "bands": [{"half": b[0], "wdi_rows": [b[1], b[2]], "samples": b[3], "squeezed": round(b[4], 2), "stretched": round(b[5], 2)} for b in bands],
                  "anchors": {n: [round(a, 1), round(b, 1)] for n, (a, b) in A1.items()},
                  "samples": [{"kind": k, "name": n, "vanilla": pv, "wdi": pw, "r1": round(float(a), 2), "r2": round(float(b), 2)}
                              for (k, n, pv, pw), a, b in zip(S, w1, w2)]}
        Vb = e5.x4(c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{f}.png"))
        t0 = dots(e5.on_bg(e5.pil(Vb)), S, w1, 0, anchors=A1)
        t1 = dots(e5.on_bg(e5.pil(R1["imw"][f])), S, w1, 1, anchors=A1)
        t2 = dots(heat(r1, R1["mw"], med1), S, w1, 1, anchors=A1)
        t3 = dots(e5.on_bg(e5.pil(R2["imw"][f])), S2, w2, 1, anchors=A2)
        t4 = dots(heat(r2, R2["mw"], med2), S2, w2, 1, anchors=A2)
        ys, xs = np.nonzero(R1["mw"] | (Vb[..., 3] > 0.5))
        box = (max(0, xs.min() - 16), max(0, ys.min() - 16), min(N, xs.max() + 16), min(N, ys.max() + 16))
        tiles = [t.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for t in (t0, t1, t2, t3, t4)]
        s1, s2 = rep[f]["round1"], rep[f]["round2"]
        fo, ft = rep[f]["border_filled"]
        lab = (f"{f}: median x{s1['median_ratio']}, weak {100 * s1['weak_share_map']:.0f}% of the body, border filled {fo}/{ft}; samples weak "
               f"border {sum(s1['weak']['border'][:2])}/{s1['weak']['border'][2]} key {sum(s1['weak']['key'][:2])}/{s1['weak']['key'][2]} "
               f"empty {sum(s1['weak']['empty'][:2])}/{s1['weak']['empty'][2]}  ->  round 2 ({len(ex)} added): weak {100 * s2['weak_share_map']:.0f}%, "
               f"border {sum(s2['weak']['border'][:2])} key {sum(s2['weak']['key'][:2])} empty {sum(s2['weak']['empty'][:2])}")
        rows.append((lab, tiles))
        print(body, lab, "extras", ex)
    W = max(sum(t.width + 10 for t in ts) for _, ts in rows) + 20
    H = sum(ts[0].height + 44 for _, ts in rows) + 60
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((10, 8), f"{body}: samples every {STEP} px of vanilla surface (border o, key [], placed [ ], empty .), green as the median, red stretched, blue squeezed (x1.5). "
            f"Vanilla | WDI round 1 | weak map round 1, anchors (grey) | WDI round 2, extras (yellow) | weak map round 2", fill=(0, 0, 0), font=ImageFont.load_default(size=18))
    y = 40
    for lab, ts in rows:
        dr.text((10, y), lab, fill=(0, 0, 0), font=font); x = 10; y += 22
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 22
    out = rf"{c1.CAPT}\2026-11-08_reliefstudy-{body}.png"; im.save(out); print(out)
    return rep


def main():
    args = [a for a in sys.argv[1:] if "=" not in a]
    bodies = BODIES if (not args or args == ["all"]) else args
    font = ImageFont.load_default(size=15)
    path = rf"{c1.OUT}\reliefstudy.json"
    rep = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            rep = json.load(fh)
    for b in bodies:
        rep[b] = study(b, font)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(rep, fh, indent=1)
    print("body        facing  median  weak1  weak2  added  border1 key1 empty1 | border2 key2 empty2")
    for b in bodies:
        for f in ("south", "east", "north"):
            s1, s2 = rep[b][f]["round1"], rep[b][f]["round2"]
            k = lambda s, kind: sum(s["weak"][kind][:2])
            print(f"{b:11s} {f:7s} x{s1['median_ratio']:<5} {100 * s1['weak_share_map']:4.0f}%  {100 * s2['weak_share_map']:4.0f}%  {len(rep[b][f]['extras']):5d}  "
                  f"{k(s1, 'border'):7d} {k(s1, 'key'):4d} {k(s1, 'empty'):6d} | {k(s2, 'border'):7d} {k(s2, 'key'):4d} {k(s2, 'empty'):6d}")


if __name__ == "__main__":
    main()
