"""Points that redraw the WDI artist's shirt (2026-11-07, Virginie: 'étape 1 : replacer les points exactement pour qu'en
traçant des pseudo arcs, on obtienne le vêtement artiste (au delta du bas du vêtement). Puis altérer les points de la
ceinture pour obtenir la ligne min(B,C)').

Step 1: her contour points (recalibrated) are snapped onto the outer contour of the artist's ShirtBasic; a smooth curve
through them (centripetal Catmull-Rom = the 'pseudo arcs') is compared with his contour and a point is added where it
strays most, until it stays within TOL px (512 scale). The bottom is left out: the target stops at the hips.
Front: the neckline is done the same way on the opening his shirt leaves bare.
Step 2: the waistband: the sides follow his contour down to the min(B,C) line (pink, hemshift_<Body>_<facing>.pink.txt:
per column the LOWER of the boxers and panties tops (larger y), where both are drawn), then the hem follows that line, with points added the same way.
Board: Art/work/captures/2026-11-07_snap-shirt.png ; points: out/snap_points.json

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python snapshirt.py
"""
import os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
from skimage import measure
import crack as c1, crack2, explain5b as e5, pseudoshirt as ps

N = c1.N; TOL = 3.0; FABRIC_LUM = 0.08   # his black stroke is under 0.05; 0.25 also cut his dark folds (east, under the breast)
BODIES = ["Thin_Female", "Fat_Female", "Hulk_Female"]; FACINGS = ["south", "east", "north"]; G = "ShirtBasic"
SIDE = {"south": ("neck base", "shoulder tip", "armpit", "waist", "hip", "leftmost", "rightmost", "top"),
        "north": ("neck base", "shoulder tip", "armpit", "waist", "hip", "leftmost", "rightmost", "top"),
        "east": ("top", "neck front", "neck back", "upper back", "chest front", "waist front", "waist back", "belly front", "buttock back")}


STROKE = {}
SHIFT = {}
EDGE = "fabric"      # "outer" = the outer edge of his black (snapdraw.py)


def catmull(P, n=24):
    """centripetal Catmull-Rom through the points P (open curve), n samples per span"""
    P = np.asarray(P, float)
    if len(P) < 2:
        return P
    Q = np.r_[[2 * P[0] - P[1]], P, [2 * P[-1] - P[-2]]]
    out = []
    for i in range(1, len(Q) - 2):
        p0, p1, p2, p3 = Q[i - 1], Q[i], Q[i + 1], Q[i + 2]
        t0 = 0.0; t1 = t0 + max(np.linalg.norm(p1 - p0), 1e-3) ** 0.5
        t2 = t1 + max(np.linalg.norm(p2 - p1), 1e-3) ** 0.5; t3 = t2 + max(np.linalg.norm(p3 - p2), 1e-3) ** 0.5
        for t in np.linspace(t1, t2, n, endpoint=False):
            a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
            a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
            a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
            b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
            b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
            out.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    out.append(P[-1])
    return np.array(out)


def outer_contour(mask):
    cs = measure.find_contours(np.pad(mask.astype(float), 1), 0.5)
    c = max(cs, key=len) - 1.0
    return c[:, ::-1]                          # (x, y)


def arc_of(contour, keep):
    """the longest circular run of contour points where keep is True, as an ordered (x, y) array"""
    k = np.asarray(keep, bool)
    if k.all():
        return contour
    start = int(np.argmin(k))                   # rotate so the run does not wrap
    c = np.roll(contour, -start, axis=0); k = np.roll(k, -start)
    best, cur, bs = (0, 0), 0, 0
    for i, v in enumerate(k):
        if v:
            if cur == 0:
                bs = i
            cur += 1
            if cur > best[1]:
                best = (bs, cur)
        else:
            cur = 0
    return c[best[0]:best[0] + best[1]]


def fit(arc, seeds):
    """anchor indices on the arc: both ends, the snapped seeds, then insertions until the curve stays within TOL"""
    tree = cKDTree(arc)
    idx = {0, len(arc) - 1}
    seeded = set()
    for p in seeds:
        _, j = tree.query(p); idx.add(int(j)); seeded.add(int(j))
    added = []
    for _ in range(60):
        order = sorted(idx)
        curve = catmull(arc[order])
        d, _ = cKDTree(curve).query(arc)
        j = int(np.argmax(d))
        if d[j] <= TOL:
            break
        idx.add(j); added.append(j)
    order = sorted(idx)
    curve = catmull(arc[order])
    d, _ = cKDTree(curve).query(arc)
    return order, seeded, set(added), curve, float(d.max()), float(d.mean())


EASE = {"Thin_Female": 0, "Hulk_Female": 0, "Fat_Female": 6}   # px his ShirtBasic stands off the body (median, 2026-11-07)


def synth_art(body, facing, body_a):
    """A ShirtBasic for a body the WDI artist did not draw (Male, Female, Thin, Fat, Hulk; 2026-11-07, Virginie 'on y va').
    On the three he drew his shirt is the body silhouette itself (Thin_Female, Hulk_Female: IoU 0.98 front and back) or
    stands about 6 px off it (Fat_Female), so: the body silhouette grown by the donor's ease, minus what the donor's shirt
    leaves bare around the neck (neckline, bare neck in profile), carried over from the donor in the neck frame
    (neck.frame: origin between the neck bases, shoulder half width, depth to the cleavage)."""
    import neck
    donor = crack2.DONOR[body]
    # +2 px: with no ease the curves through the points (3 px tolerance) cut inside the body and it showed along the
    # sides (Virginie 2026-11-07, Male north and east: 'les points sont en dedans de WDI')
    sil = ndi.binary_dilation(body_a, iterations=EASE[donor] + 2)
    d = case(donor, facing)
    bare_d = d["body_a"] & ~(d["art"][..., 3] > 0.5)          # not filled: the neckline is a hole in his shirt
    oxd, oyd, xud, yud = neck.frame(donor, facing, 1, 4)
    bare_d[int(oyd + 2.2 * yud):, :] = False                   # only around the neck, as for the drawn bodies
    ox, oy, xu, yu = neck.frame(body, facing, 1, 4)
    yy, xx = np.mgrid[0:N, 0:N]
    xd = np.clip(np.round(oxd + (xx - ox) / xu * xud), 0, N - 1).astype(int)
    yd = np.clip(np.round(oyd + (yy - oy) / yu * yud), 0, N - 1).astype(int)
    bare = bare_d[yd, xd] & body_a
    lab, n = ndi.label(bare)          # only the opening itself: stray bare pixels of the donor made Hulk south ragged
    if n > 1:
        bare = lab == (1 + int(np.argmax(ndi.sum(bare, lab, range(1, n + 1)))))
    if bare.any():                    # the opening reaches the edge where the body is wider than the dilation
        bare = ndi.binary_dilation(bare, iterations=EASE[donor] + 2) & ~ndi.binary_erosion(body_a, iterations=1) | bare
    sil = sil & ~bare
    # thin strips left between the carried opening and the body edge go (Male east: a strip of fabric up the front of the
    # throat, the neckline went down and back up, its pairs crossed the vanilla ones; Virginie 2026-11-07: 'erreur au
    # niveau du tour de cou est'): what an opening of radius 5 removes, when it is a long piece (corners only lose a few px)
    # touching the carried opening; in profile only: front and back a thin strip by the opening is the collar band (north:
    # removing it dug a notch into the top of the back)
    if facing in ("east", "west"):
        yy5, xx5 = np.mgrid[-5:6, -5:6]
        thin = sil & ~ndi.binary_opening(sil, structure=(xx5 ** 2 + yy5 ** 2) <= 25)
        near = ndi.binary_dilation(bare, iterations=2)
        lab, n = ndi.label(thin)
        for k in range(1, n + 1):
            if (lab == k).sum() > 60 and (near & (lab == k)).any():
                sil &= ~(lab == k)
        # and nothing in front of the opening, row by row: the strip's thicker base was left as a hook above E18
        # (Virginie 2026-11-07, 'pourquoi le crochet en avant ?'). No ShirtBasic covers the throat front: vanilla 0 to 80
        # px over the 5 bodies, the WDI artist 0 to 4 (collar survey 2026-11-07)
        for y in np.where(bare.any(axis=1))[0]:
            xs = np.where(bare[y])[0]
            if facing == "east":
                sil[y, xs.max() + 1:] = False
            else:
                sil[y, :xs.min()] = False
    lab, n = ndi.label(sil)
    if n > 1:
        sil = lab == (1 + int(np.argmax(ndi.sum(sil, lab, range(1, n + 1)))))
    art = np.zeros((N, N, 4), np.float32); art[sil] = (1, 1, 1, 1)
    return art


def case(body, facing):
    _, _, _, body_a, _ = crack2.prep(body, facing, None if body in BODIES else crack2.DONOR[body])
    vb = c1.VANILLA_OF[body]; Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    if body in BODIES:
        art = c1.load(rf"{e5.WDI_TEX}\Things\Pawn\Humanlike\Apparel\{G}\{G}_{body}_{facing}.png", N)
    else:
        art = synth_art(body, facing, body_a)
    if EDGE == "outer":
        # everything moves UP when his shirt starts under the WDI silhouette top (Hulk_Female front and back: 5 px)
        dy = int(np.where(body_a.any(axis=1))[0].min()) - int(np.where((art[..., 3] > 0.5).any(axis=1))[0].min())
        if dy < 0:
            art = np.concatenate([art[-dy:], np.zeros((-dy, N, 4), art.dtype)], axis=0)
        SHIFT[f"{body}_{facing}"] = min(dy, 0)
    # Virginie 2026-11-07: the points sit on the fabric, never on the black stroke: the contour is the fabric's edge,
    # inside his outline (fabric = his pixels lighter than FABRIC_LUM, the largest piece)
    # his inner black lines (under the breast, the armpits) touch the outline, so colour alone cuts notches: the fabric
    # edge is his filled silhouette moved in by his outline thickness, measured as the depth of the black from the edge
    al = art[..., 3] > 0.5; filled = ndi.binary_fill_holes(al)
    dist = ndi.distance_transform_edt(filled)
    black = al & (c1.lum(art) < FABRIC_LUM)
    edge_black = black & (dist < 30)
    lab_b, nb = ndi.label(edge_black)
    outer_lab = np.unique(lab_b[(dist <= 1.5) & edge_black]); outer_lab = outer_lab[outer_lab > 0]
    ring = np.isin(lab_b, outer_lab)
    w = float(np.percentile(dist[ring], 90)) if ring.any() else 12.0
    w = min(w, 13.0)                      # his outline is 10 to 12 px; more means the neck ring was counted with it
    fab = (dist > w) & al
    STROKE[f"{body}_{facing}"] = round(w, 1)
    # "outer": the outer edge of his black (Virginie 2026-11-07), and never below the top of the WDI silhouette: on
    # Hulk_Female his shirt starts 5 px under the body top, the body must not show above ours (union with the body)
    # Virginie 2026-11-07 ('on remonte tout pour que le haut soit géré'): no union any more, the whole drawing is moved up
    # (done at load, see SHIFT below), so his top meets the WDI silhouette top
    A = ndi.binary_fill_holes(fab) if EDGE == "fabric" else filled
    lab, n = ndi.label(A)
    if n > 1:
        A = lab == (1 + int(np.argmax(ndi.sum(A, lab, range(1, n + 1)))))
    contour = outer_contour(A)
    on = [i for i, n in enumerate(names) if any(n.startswith(k) or (" / " + k) in n for k in SIDE[facing])]
    seeds = src[on]
    # step 1: target = his contour above the hips (the lowest contour seed row), the bottom left out
    cut = float(max(seeds[:, 1])) if len(seeds) else N
    arc1 = arc_of(contour, contour[:, 1] <= cut)
    s1 = fit(arc1, seeds)
    res = {"src": src, "names": names, "on": on, "art": art, "body_a": body_a, "arc1": arc1, "s1": s1}
    # front: the neckline on the opening his shirt leaves bare
    if facing == "south":
        ox, oy, xu, yu = __import__("neck").frame(body, facing, 1, 4)
        # the opening plus its black ring: what his shirt leaves bare, grown by the stroke thickness
        bare0 = body_a & ~al; bare0[int(oy + 2.2 * yu):, :] = False
        bare = ndi.binary_dilation(bare0, iterations=int(round(w))) & (dist > w) if EDGE == "fabric" else bare0.copy()
        bare[int(oy + 2.2 * yu):, :] = False
        lab, n = ndi.label(bare); k = lab[int(np.clip(oy + 0.4 * yu, 0, N - 1)), int(ox)]
        if k:
            oc = outer_contour(lab == k)
            top = int(np.argmin(oc[:, 1])); oc = np.roll(oc, -top, axis=0)      # start at the top of the opening
            # 1 / 7 untangled (Virginie 2026-11-07): 'top' (1) stays on the outer edge at the midline; the jugular notch (7)
            # belongs to the neckline: it is put on the top of the opening, at the midline
            jx = float(np.median(src[[i for i, nm in enumerate(names) if "neck base" in nm], 0])) if any("neck base" in nm for nm in names) else ox
            near_mid = np.abs(oc[:, 0] - jx) < 3
            jug = oc[near_mid][np.argmin(oc[near_mid][:, 1])] if near_mid.any() else oc[0]
            res["jugular"] = jug
            neck_seeds = [jug]
            res["arcN"] = oc; res["sN"] = fit(oc, neck_seeds)
    # step 2: the waistband on min(B,C) = the pink line
    pink = np.array([float(v) for v in open(rf"{e5.PROTO}\hemshift_{body}_{facing}.pink.txt").read().strip().split(";")])
    xi = np.clip(np.round(contour[:, 0]).astype(int), 0, N - 1)
    arc2 = arc_of(contour, contour[:, 1] <= pink[xi])
    a, b = arc2[-1], arc2[0]                    # the two ends where his sides meet the pink line
    xs = np.linspace(a[0], b[0], max(2, int(abs(b[0] - a[0]) // 2)))
    hem = np.c_[xs, pink[np.clip(np.round(xs).astype(int), 0, N - 1)]]
    s2 = fit(arc2, seeds[seeds[:, 1] <= cut])
    h2 = fit(hem, [])
    res.update(arc2=arc2, s2=s2, hem=hem, h2=h2, pink=pink)
    return res


def draw(res, step, font):
    art = res["art"]; body_a = res["body_a"]
    wb = np.zeros((N, N, 4), np.float32); wb[body_a] = (0.80, 0.80, 0.80, 1)
    im = e5.pil(wb)
    if step == 1:
        a = art.copy(); a[..., 3] *= 0.55; im.alpha_composite(e5.pil(a))
    im = e5.on_bg(im); dr = ImageDraw.Draw(im)
    if step == 2:
        poly = [tuple(p) for p in res["s2"][3]] + [tuple(p) for p in res["h2"][3]]
        sh = Image.new("RGBA", (N, N), (0, 0, 0, 0)); ImageDraw.Draw(sh).polygon(poly, fill=(255, 255, 255, 230))
        if "sN" in res:
            ImageDraw.Draw(sh).polygon([tuple(p) for p in res["sN"][3]], fill=(0, 0, 0, 0))
        im.alpha_composite(sh); dr = ImageDraw.Draw(im)
        dr.line([(x, float(res["pink"][x])) for x in range(N) if body_a[:, x].any()], fill=(255, 80, 200), width=2)
    # his contour in blue
    dr.line([tuple(p) for p in (res["arc1"] if step == 1 else res["arc2"])], fill=(30, 90, 255), width=2)
    for key, arc in (("s1" if step == 1 else "s2", "arc1" if step == 1 else "arc2"), ("sN", "arcN"), ("h2", "hem")):
        if key not in res or (key == "h2" and step == 1) or (key == "sN" and False):
            continue
        order, seeded, added, curve, dmax, dmean = res[key]
        dr.line([tuple(p) for p in curve], fill=(0, 0, 0), width=3)
        A = res[arc]
        for j in order:
            x, y = A[j]
            col = (255, 140, 0) if j in added else ((255, 80, 200) if key == "h2" else (255, 220, 0))
            r = 6 if j in added else 7
            dr.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=(0, 0, 0))
    for i in res["on"]:                         # her points before snapping (small cyan)
        x, y = res["src"][i]
        dr.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(0, 230, 255))
    return im


def main():
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 380; pad = 8; left = 120; top = 70; head = 34
    cols = [(b, s) for b in BODIES for s in (1, 2)]
    im = Image.new("RGB", (left + len(cols) * (T + pad), top + 3 * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), f"Step 1: your points snapped on the artist's {G} contour (blue), curve through them (black); yellow = your points, orange = added where the curve strayed over {TOL:.0f} px, cyan dot = your point before.", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Step 2: the waistband on min(B,C) (pink line): his sides down to it, then the hem along it (magenta points). White = the pseudo shirt.", fill=(0, 0, 0), font=fontb)
    for j, (b, s) in enumerate(cols):
        dr.text((left + j * (T + pad), top - 20), f"{b}  step {s}", fill=(0, 0, 0), font=fontb)
    dump = {}
    for r, f in enumerate(FACINGS):
        y = top + r * (T + head + pad); dr.text((8, y + head + 8), f, fill=(0, 0, 0), font=fontb)
        for j, (b, s) in enumerate(cols):
            try:
                res = case(b, f)
            except Exception as ex:
                print("FAIL", b, f, repr(ex)[:200]); continue
            t = draw(res, s, font)
            x = left + j * (T + pad)
            k = "s1" if s == 1 else "s2"
            order, seeded, added, curve, dmax, dmean = res[k]
            txt = f"{len(order)} points ({len(added)} added), gap max {dmax:.1f} mean {dmean:.1f} px"
            if s == 1 and "sN" in res:
                o2, _, a2, _, m2, _ = res["sN"]; txt += f"\nneckline: {len(o2)} points ({len(a2)} added), max {m2:.1f}"
            if s == 2:
                o3, _, a3, _, m3, _ = res["h2"]; txt += f"\nwaistband: {len(o3)} points, max {m3:.1f}"
            dr.text((x, y), txt, fill=(0, 0, 0), font=font)
            im.paste(t.resize((T, T), Image.LANCZOS).convert("RGB"), (x, y + head))
            dump[f"{b}_{f}_step{s}"] = {"outline": res[k][3][::4].round(1).tolist(), "anchors": [res["arc1" if s == 1 else "arc2"][i].round(1).tolist() for i in res[k][0]]}
            print("done", b, f, s, txt.replace("\n", " | "))
    with open(rf"{c1.OUT}\snap_points.json", "w") as fh:
        json.dump(dump, fh)
    print("stroke", STROKE)
    out = rf"{c1.CAPT}\2026-11-07_snap-shirt.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
