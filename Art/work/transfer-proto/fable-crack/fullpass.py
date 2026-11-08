"""First full pass (Virginie 2026-11-07, 'teste sur Male déjà'): the vanilla ShirtBasic fitted onto a WDI body, rule 1 (top alone),
steps 1 to 6 on one board, three facings.
  1 source  : vanilla ShirtBasic on the vanilla body, x4, her vanilla points (yellow) and the vanilla twins of the added points (orange)
  2 prep    : black outline peeled by thickness, the freed band filled from the nearest light fabric (doc 4.2, 4.3)
  3 target  : the WDI outline (snapshirt, outer edge; drawn or synthetic ShirtBasic), hem on min(B,C) + d_min, her WDI points
              snapped (yellow) and the added points (orange)
  4 warp    : thin-plate spline WDI -> vanilla driven by the point pairs only (named pairs, snapped contour pairs, added pairs)
  5 clip    : the warped garment clipped to the target outline, WDI body shading at 0.30, no whitening
  6 outline : 4 px stroke inward on the outer edge
Vanilla twin of an added point: same arc-length fraction between the same two snapped neighbours, on the vanilla garment's outer
contour, along its shorter way between them (doc 6).
Board: Art/work/captures/2026-11-07_fullpass-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python fullpass.py [Body]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.spatial import cKDTree
import crack as c1, crack2, crack8, explain5b as e5, snapshirt as ss, rules4 as r4

N = c1.N; SHADE = 0.30
# the vanilla garment, "garment=<core17 name>" (Virginie 2026-11-07: ShirtBasic has a torn collar and a torn hem, try the
# blouse = LabCoat)
G = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("garment=")), "ShirtBasic")
NOLEGS = "nolegs" in sys.argv[1:]
FULLLEN = "fulllen" in sys.argv[1:]
POINTWARP = "pointwarp" in sys.argv[1:]   # Virginie 2026-11-08 ("point warp est une cata par rapport à relief map", "oui, remplace"):
# B4 is the relief map (reliefmap.build, Part C); "pointwarp" brings the thin-plate spline on the pairs back, for comparison
B56 = "b56" in sys.argv[1:]     # Virginie 2026-11-07: steps 5 (clip, fill, shading) and 6 (outline) taken out; "b56" shows them again
GROIN = "nogroin" not in sys.argv[1:]     # validated by Virginie 2026-11-07: on by default
LAM = 20.0          # warp smoothing: 2000 missed the points by 3.5 px (median) to 16 px, the fabric fell short of the outline (Virginie 2026-11-07: flanks, belly, neck, shoulders)
SNAP_TOL = 12.0     # px at 512: a body contour point snaps onto the garment edge only when this close to it
GROIN_X = 0.72     # groin creases: share of the study's distance from the navel's x (her circles, Male south)
ss.EDGE = "outer"


def arclen(P):
    return np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]


def prepared(Vg, Vb=None):
    """step 2: peel the black by thickness, then fill the freed band from the nearest light fabric pixel"""
    Gp = crack8.upscale4(Vg, crack8.UPSCALE)
    full = Gp[..., 3] > 0.5
    # the crotch notch of the vanilla hem is closed first (convex hull of the bottom 30 %), the new part takes the fabric's
    # smoothed colour: peeled as it was, the bottom became a W (Virginie 2026-11-07, 'regarde le peeling déjà')
    from skimage.morphology import convex_hull_image
    ys = np.where(full.any(axis=1))[0]
    rows = np.arange(N)[:, None]
    low = rows >= ys.max() - int(0.40 * (ys.max() - ys.min()))
    add = convex_hull_image(full & low) & low & ~full
    # only a notch: an opening that runs up through the whole band (LabCoat's open front) is part of the garment
    ar = np.where(add.any(axis=1))[0]
    if len(ar) and ar.max() - ar.min() >= 0.9 * (ys.max() - (ys.max() - int(0.40 * (ys.max() - ys.min())))):
        add[:] = False
    added = add.copy()
    if add.any():
        fab = full & (c1.lum(Gp) > 0.5)
        w = fab.astype(np.float32); den = ndi.gaussian_filter(w, 8)
        sm = np.stack([ndi.gaussian_filter(Gp[..., k] * w, 8) for k in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
        _, idx = ndi.distance_transform_edt(~(den > 0.05), return_indices=True)
        sm = sm[idx[0], idx[1]]
        Gp = Gp.copy(); Gp[add, :3] = sm[add]; Gp[add, 3] = 1.0
        full = full | add
    # Peel LAYER BY LAYER, as in round 8 (Virginie 2026-11-07: 'fais comme avant, la suppression par couche, puis en
    # finalisant le fait d'enlever le petit pourtour'):
    # 1. each pass takes the outer rim (from the outside only: holes filled, the neck hole keeps its thin line) and drops its
    #    pure black pixels (under crack8.PEEL_LUM = 0.04); it stops at the first pass with none, and never goes deeper than
    #    the measured outline (4 px at 128) + 1 px. The closed notch counts as outline there, so the bottom stays straight.
    # 2. finishing: the little grey anti-aliased rim left (darker than 60 % of the fabric own lightness), 4 passes at most.
    va = Vg[..., 3] > 0.5
    s_out = int(c1.edge_run(va, c1.lum(Vg), ~va))
    depth = (min(4, max(1, s_out)) + 1) * 4
    L = c1.lum(Gp)
    keep = full.copy()

    def rim(a):
        return a & ~ndi.binary_erosion(ndi.binary_fill_holes(a))
    in_band = ndi.distance_transform_edt(ndi.binary_fill_holes(full)) <= depth
    # only the outline along the body's edge is peeled: the edges of an opening inside the body (LabCoat's open front)
    # keep their line, as the vanilla artist drew it (Virginie 2026-11-07, blouse)
    if Vb is not None:
        vb = e5.x4(Vb[..., 3] > 0.5)
        on_edge = (ndi.distance_transform_edt(vb) + ndi.distance_transform_edt(~vb)) <= depth + 8
    else:
        on_edge = np.ones_like(full)
    for _ in range(depth):
        rm = rim(keep) & ((L < crack8.PEEL_LUM) | (added & in_band)) & on_edge
        if not rm.any():
            break
        keep &= ~rm
    core = ndi.binary_erosion(keep, iterations=6)
    ref = float(np.median(L[core])) if core.any() else 1.0
    for _ in range(4):                               # 1 px at 128
        rm = rim(keep) & (L < 0.6 * ref) & on_edge
        if not rm.any():
            break
        keep &= ~rm
    lab, n = ndi.label(keep)                         # no stray specks left on the edge
    if n > 1:
        keep = lab == (1 + int(np.argmax(ndi.sum(keep, lab, range(1, n + 1)))))
    # the notch closed again on what is left: peeling its black sides reopened a slit in the middle of the hem
    if added.any():
        slit = convex_hull_image(keep & low) & low & ~keep
        Gp = Gp.copy(); Gp[slit, :3] = sm[slit]; Gp[slit, 3] = 1.0
        keep = keep | slit
    # no fill of the freed band any more (Virginie 2026-11-07: 'pas besoin de populer les bords'): step 5 already fills
    # every pixel of the target that the warped garment leaves empty, and the whole is shrunk to 256 at the end
    out = Gp.copy(); out[~keep, 3] = 0.0
    return out


def legs(S, D, names, src_n, dst_n, body, facing, body_a, van_a, hem):
    """Room for the legs (doc 6, Virginie 2026-11-07: 'ça ne prend pas en compte les points qu'on a bougé pour le pantalon',
    then 'bouge les points à l'intérieur du corps' and 'résous les points 7, 21 et 22 east').
    Start row: the navel, else the belly, else the hips, on both bodies (WDI y0, vanilla v0); WDI y0 always 24 px above the hem.
    Below it, a point keeps on the WDI side the share of height its VANILLA partner has between v0 and the vanilla body
    bottom of its column, laid between y0 and the garment's lower limit `hem` (rule 1: min(B,C) + d_min). Taking the
    proportion on the WDI side instead left the east front points (7, 21, 22: vanilla waist and belly) at the WDI hem,
    since the WDI front ends right on it."""
    pick = [i for i, n in enumerate(names) if "navel" in n] or [i for i, n in enumerate(names) if "belly" in n] \
        or [i for i, n in enumerate(names) if n.startswith("hip")]
    y0 = float(np.mean(src_n[pick, 1])) if pick else float(np.median(src_n[:, 1]))
    v0 = float(np.mean(dst_n[pick, 1])) * 4 if pick else float(np.median(dst_n[:, 1])) * 4
    cols = np.where(body_a.any(axis=0))[0]; vcols = np.where(van_a.any(axis=0))[0]
    y0 = min(y0, float(hem[cols].min()) - 24)
    rows = np.arange(N); out = S.copy()
    for i, ((x, y), (vx, vy)) in enumerate(zip(S, D * 4)):
        xi = int(cols[np.argmin(np.abs(cols - x))])          # outside the body's columns: the nearest one
        yh = float(hem[xi])
        vxi = int(vcols[np.argmin(np.abs(vcols - vx))])
        vcol = van_a[:, max(0, vxi - 2):vxi + 3].any(axis=1)
        vbot = float(rows[vcol].max())
        if vy > v0 and vbot > v0 + 1 and yh > y0:
            out[i, 1] = y0 + (vy - v0) / (vbot - v0) * (yh - y0)
        elif y > y0:
            out[i, 1] = min(y, y0 + 0.5 * (yh - y0))           # vanilla above its start row, WDI below ours: halfway
        out[i, 1] = min(out[i, 1], yh - 2)                     # every point ends inside the garment
        # it may move a point DOWN too: on Male the groin creases of the study sit on the belly (356, above the boxers' top
        # 372); by their vanilla share between navel and crotch they land at 379, inside the boxers (proposal 2026-11-07)
    return out, y0


def vanilla_contour(Vg, Vb=None):
    """the vanilla side of the contour pairs: the edge of the fabric LEFT after B2, not the original outer edge. With the
    original edge the peeled band (now transparent) was stretched up to the WDI outline and showed as a transparent rim in
    B4 (Virginie 2026-11-07: 'il faut retirer les bords transparents de ce qui est étiré')"""
    a = ndi.binary_fill_holes(prepared(Vg, Vb)[..., 3] > 0.5)
    return ss.outer_contour(a)


def vanilla_hole(Vg):
    """the vanilla neck hole's contour (512 units), or None"""
    hole = ndi.binary_fill_holes(e5.x4(Vg[..., 3] > 0.5)) & ~e5.x4(Vg[..., 3] > 0.5)
    lab, n = ndi.label(hole)
    if not n:
        return None
    hole = lab == (1 + int(np.argmax(ndi.sum(hole, lab, range(1, n + 1)))))
    # without the V slit under it (an opening of radius 8 removes it): paired by angle, the WDI hole's bottom went to the
    # slit's tip and the slit was stretched down the chest (lam 20, 2026-11-07)
    yy, xx = np.mgrid[-8:9, -8:9]
    op = ndi.binary_opening(hole, structure=(xx ** 2 + yy ** 2) <= 64)
    return ss.outer_contour(op if op.any() else hole)


def hole_span(c):
    """x span of the top third of a hole contour"""
    y0 = c[:, 1].min(); m = c[:, 1] <= y0 + (c[:, 1].max() - y0) / 3
    return float(c[m, 0].min()), float(c[m, 0].max())


def along(loop, k0, k1, t):
    """point at fraction t of the shorter way from index k0 to k1 on a closed contour"""
    n = len(loop)
    fw = np.r_[np.arange(k0, k0 + ((k1 - k0) % n) + 1)] % n
    bw = np.r_[np.arange(k0, k0 - ((k0 - k1) % n) - 1, -1)] % n
    path = loop[fw] if len(fw) <= len(bw) else loop[bw]
    L = arclen(path)
    if L[-1] <= 0:
        return path[0]
    s = t * L[-1]; i = int(np.searchsorted(L, s)); i = min(max(i, 1), len(path) - 1)
    u = (s - L[i - 1]) / max(L[i] - L[i - 1], 1e-6)
    return path[i - 1] + u * (path[i] - path[i - 1])


def pairs(body, facing, Vg):
    """the warp pairs: WDI (512) -> vanilla (128); returns src, dst, seeds_w, added_w, seeds_v, added_v"""
    res = ss.case(body, facing)
    body_a = res["body_a"]
    Vb = c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{facing}.png")
    src, dst, names = e5.named_pairs(body, facing)
    src, dst = e5.recal(src, dst, body_a, Vb[..., 3] > 0.5)
    # Groin creases (proposal 2026-11-07, Virginie: 'il y a une erreur dans le placement du pubis ... je maintiens'): in the
    # study they sit at the NAVEL's height on the WDI bodies (Male: both 356), above the pelvis lines the artist drew, while
    # on vanilla they are well under the navel. Each takes on WDI the share of height it has on vanilla between navel and
    # sex (Male 0.64: 356 -> 387), its x kept.
    if GROIN:
        ix = {n: i for i, n in enumerate(names)}
        nv, sx = ix.get("navel"), ix.get("sex")
        if nv is not None and sx is not None and dst[sx, 1] > dst[nv, 1]:
            # her placement on Male south (circles of 2026-11-07): ON the waistband line min(B,C), where the pelvis lines
            # start under the navel, about 0.72 of the study's distance from the midline
            mnl = __import__("pantsnap").lines(body, facing)[0]
            for k in ("groin crease L", "groin crease R"):
                g = ix.get(k)
                if g is not None:
                    src[g, 0] = src[nv, 0] + GROIN_X * (src[g, 0] - src[nv, 0])
                    src[g, 1] = float(mnl[int(round(src[g, 0]))])
    arc = res["arc1"]; order, seeded, added, _, _, _ = res["s1"]
    on = res["on"]
    vc = vanilla_contour(Vg, Vb); vtree = cKDTree(vc)
    # neck bases keep the vanilla order against the neck hole (Virginie 2026-11-07, 'un souci vers 5 face'; collar survey):
    # on vanilla Male the neck base lies 12 to 16 px outside the hole, on our WDI Male 4 px above it, so the warp folded the
    # fabric between them. Where the side flips (Male, Fat, Fat_Female), the WDI neck base goes on the top edge at the
    # vanilla share between the shoulder tip and the hole edge; the WDI hole (the artist's, wider) is kept
    hv = vanilla_hole(Vg)
    if hv is not None and "arcN" in res:
        ix = {n: i for i, n in enumerate(names)}
        (vl, vr), (wl, wr) = hole_span(hv), hole_span(res["arcN"])
        for side, hev, hew, sg in (("L", vl, wl, -1), ("R", vr, wr, 1)):
            i, j = ix.get(f"neck base {side}"), ix.get(f"shoulder tip {side}")
            if i is None or j is None or i not in on:
                continue
            nbv = vc[vtree.query(dst[i] * 4)[1]][0]
            if (sg * (nbv - hev) > 0) == (sg * (src[i, 0] - hew) > 0):
                continue                                           # same side on both: as it is
            f = (hev - nbv) / (hev - dst[j, 0] * 4)
            x = hew - f * (hew - src[j, 0])
            near = arc[np.abs(arc[:, 0] - x) < 1.5]
            if len(near):
                src[i] = near[np.argmin(near[:, 1])]
    # the jugular notch on the top of the opening on BOTH sides: on WDI it was put there (1 / 7 untangled), on vanilla it
    # stayed on the fabric's top edge, above the neck bases, and the triangle 7-5-6 turned over (fold check 2026-11-07)
    if hv is not None and "jugular" in res:
        g = {n: i for i, n in enumerate(names)}.get("jugular notch")
        if g is not None:
            mid = hv[np.abs(hv[:, 0] - dst[g, 0] * 4) < 3]
            if len(mid):
                src[g] = res["jugular"]; dst[g] = mid[np.argmin(mid[:, 1])] / 4
    tree = cKDTree(arc)
    jw = {i: int(tree.query(src[i])[1]) for i in on}               # each contour seed: its index on the WDI arc
    kv = {i: int(vtree.query(dst[i] * 4)[1]) for i in on}          # and on the vanilla contour
    # a body contour point goes onto the garment's edge only where the garment lies on the body's edge there (within
    # SNAP_TOL); elsewhere it stays a body point on both sides. LabCoat in profile (Virginie 2026-11-07, 'de côté, c'est
    # catastrophique'): its open front edge runs behind the chest, the chest points snapped onto it and dragged it to the
    # WDI chest front, the lapel crumpled
    snapped = {i: bool(np.linalg.norm(vc[kv[i]] - dst[i] * 4) <= SNAP_TOL) for i in on}
    S, D = [], []
    for i in range(len(src)):
        if i in on and snapped[i]:
            S.append(arc[jw[i]]); D.append(vc[kv[i]] / 4)          # contour seeds: snapped on both outlines
        else:
            S.append(src[i]); D.append(dst[i])                      # inner points (and unsnapped seeds) as they are
    seq = sorted((j, i) for i, j in jw.items())
    aw, av = [], []
    L = arclen(arc)
    for a in sorted(added):
        left = [(j, i) for j, i in seq if j < a]; right = [(j, i) for j, i in seq if j > a]
        if not left or not right:
            continue                                               # before the first or after the last seed: no twin
        (jl, il), (jr, ir) = left[-1], right[0]
        if not (snapped[il] and snapped[ir]):
            continue                                               # the garment leaves the body edge there: no twin
        t = (L[a] - L[jl]) / max(L[jr] - L[jl], 1e-6)
        v = along(vc, kv[il], kv[ir], t)
        S.append(arc[a]); D.append(v / 4); aw.append(arc[a]); av.append(v)
    # front neckline: the WDI opening's points (snapshirt sN, starting at the jugular notch on top) paired with the vanilla
    # neck hole at the same arc-length fraction from its top, same direction of travel; without them the vanilla hole landed
    # lower than the target's and the gap was filled in streaks (Male south, first pass)
    # by angle around each hole's centre, not by arc length: the V slit under the vanilla hole lengthens its contour and
    # the pairs slid and crossed (33-36, 38-40, 37 with the cleavage; fold check 2026-11-07)
    if "sN" in res:
        if hv is not None:
            oc = res["arcN"]; idxN = res["sN"][0]
            cw = oc.mean(axis=0); cv = hv.mean(axis=0)
            aw_ = np.arctan2(oc[:, 1] - cw[1], oc[:, 0] - cw[0])
            av_ = np.arctan2(hv[:, 1] - cv[1], hv[:, 0] - cv[0])
            for j in idxN:
                k = int(np.argmin(np.abs(np.angle(np.exp(1j * (av_ - aw_[j]))))))
                S.append(oc[j]); D.append(hv[k] / 4); aw.append(oc[j]); av.append(hv[k])
    return (np.array(S), np.array(D), np.array([arc[jw[i]] for i in on]), np.array(aw).reshape(-1, 2),
            np.array([vc[kv[i]] for i in on]), np.array(av).reshape(-1, 2), res, names, src)


def dots(img, P, col, r=6):
    d = ImageDraw.Draw(img)
    for x, y in P:
        d.ellipse((x - r, y - r, x + r, y + r), fill=col, outline=(0, 0, 0))


def facing_row(body, facing):
    vb = c1.VANILLA_OF[body]
    Vg = c1.load(rf"{c1.CORE}\{G}_{vb.capitalize()}_{facing}.png")
    Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{facing}.png")
    drawn = body in crack2.DRAWN
    _, _, shade, body_a, _ = crack2.prep(body, facing, None if drawn else crack2.DONOR[body])
    S, D, sw, aw, sv, av, res, names, src_n = pairs(body, facing, Vg)
    Gp = prepared(Vg, Vb)
    mn = r4.lines(body, facing)[0]; dmin = r4.dmin_of(body, facing, mn)[0]
    S0 = S.copy()
    _, dst_n, _ = e5.named_pairs(body, facing)
    _, dst_n = e5.recal(src_n, dst_n, body_a, Vb[..., 3] > 0.5)
    van_a = e5.x4(Vb[..., 3] > 0.5)
    if NOLEGS:      # Virginie 2026-11-07: 'pour l'instant, SANS les jambes': her WDI points as they are, no press
        y0 = float(N)
    else:
        S, y0 = legs(S, D, names, src_n, dst_n, body, facing, body_a, van_a, mn + dmin)
    if FULLLEN:
        # option 'fulllen': the target is the reference outline at full length, down to the WDI body bottom (a misreading
        # of 'sans jambe, il ne faut pas faire B4', which meant: no press up to the hem in B4; the B5 cut stays)
        res_f = ss.case(body, facing)
        Ff = ndi.binary_fill_holes(res_f["art"][..., 3] > 0.5)
        holes = res_f["sN"][3] if "sN" in res_f else None
        if holes is not None:
            hm = Image.new("L", (N, N), 0); ImageDraw.Draw(hm).polygon([tuple(p) for p in holes], fill=255)
            Ff &= ~(np.asarray(hm) > 127)
        ring = Image.new("L", (N, N), 0); dr_ = ImageDraw.Draw(ring)
        c_ = ss.outer_contour(ndi.binary_fill_holes(res_f["art"][..., 3] > 0.5))
        dr_.line([tuple(p) for p in c_] + [tuple(c_[0])], fill=255, width=9)
        if holes is not None:
            dr_.line([tuple(p) for p in holes] + [tuple(holes[0])], fill=255, width=9)
        F = Ff; St = (np.asarray(ring) > 127) & F
    else:
        (F, St), _ = r4.shirt_to(body, facing, mn + dmin)
    # a contour point the press moved goes back onto the target outline (nearest outline pixel): it kept its x and fell
    # outside where the outline narrows at the bottom (east front 7, 21, 22; Virginie 2026-11-07)
    edge = F & ~ndi.binary_erosion(F)
    ey, ex = np.nonzero(edge); etree = cKDTree(np.c_[ex, ey])
    on_set = set(res["on"]); n0 = len(src_n)
    for i in range(len(S)):
        if (i in on_set or i >= n0) and abs(S[i, 1] - S0[i, 1]) > 1:
            S[i] = np.r_[ex, ey].reshape(2, -1)[:, etree.query(S[i])[1]]
    # hips: the contour pairs stop at her lowest contour point (snapshirt arc1 is cut there), so nothing held the sides
    # between it and the hem (Virginie 2026-11-07: 'il manque des marques pour les hanches'). Every 16 px down each side of
    # the target, from that point to the hem: the WDI edge pixel, its vanilla twin = the nearest point of the peeled fabric
    # edge to where the warp WITHOUT them samples that pixel (the deformation of the other pairs is kept)
    U0, V0 = c1.warp_field(c1.TPS(S, D, lam=LAM))
    vc = vanilla_contour(Vg, Vb); vtree = cKDTree(vc)
    ylow = max(S[i, 1] for i in on_set)
    hem_ = mn + dmin
    hip_S, hip_D = [], []
    for y in np.arange(ylow + 16, N, 16):
        row = np.where(F[int(y)])[0]
        if not len(row):
            break
        for x in (row.min(), row.max()):
            if y > hem_[x] - 6:
                continue
            dj, j = vtree.query((U0[int(y), x] * 4, V0[int(y), x] * 4))
            if dj > SNAP_TOL:
                continue                                           # the garment is not on that edge (open front)
            hip_S.append((float(x), float(y))); hip_D.append(vc[j] / 4)
    if hip_S:
        S = np.r_[S, np.array(hip_S)]; D = np.r_[D, np.array(hip_D)]; S0 = np.r_[S0, np.array(hip_S)]
    # the whole vanilla hem onto the WDI hem: 9 pairs across the width, from the bottom edge of the prepared fabric (side to
    # side) to the rule's lower limit (side to side of the target). Only the middle points were pressed before, so the
    # bottom corners stayed pulled down to the WDI body bottom (Virginie 2026-11-07: 'ce n'est pas étiré en hauteur ...
    # regarde les points du bas')
    if not NOLEGS:      # without the legs the vanilla bottom stays on the WDI body bottom: no hem pairs
        fabm = ndi.binary_fill_holes(Gp[..., 3] > 0.5)
        vb = np.array([np.where(fabm[:, x])[0].max() if fabm[:, x].any() else -1 for x in range(N)], float)
        vcs = np.where(vb >= vb.max() - 16)[0]                       # the hem span of the vanilla fabric
        hem_ = mn + dmin
        wcs = np.where(F.any(axis=0) & (np.array([np.where(F[:, x])[0].max() if F[:, x].any() else -1 for x in range(N)]) >= hem_ - 6))[0]
        extra_S, extra_D = [], []
        # each hem pair keeps the deformation of the others (Virginie 2026-11-07: 'tes verts ne conservent pas la
        # déformation, écris tes verts comme s'il n'y avait pas déformation en bas'): its WDI x is where the warp WITHOUT the
        # hem pairs already sends that vanilla point (the WDI pixel whose sample is nearest to it); only its y goes on the hem
        U0, V0 = c1.warp_field(c1.TPS(S, D, lam=LAM))
        for t in np.linspace(0.05, 0.95, 9):
            vx = vcs.min() + t * (vcs.max() - vcs.min()); vy = vb[int(round(vx))]
            k = int(np.argmin((U0 - vx / 4) ** 2 + (V0 - vy / 4) ** 2)); _, wx = divmod(k, N)
            wx = float(np.clip(wx, wcs.min(), wcs.max()))
            extra_D.append((vx / 4, vy / 4)); extra_S.append((wx, hem_[int(round(wx))] - 2))
        S = np.r_[S, np.array(extra_S)]; D = np.r_[D, np.array(extra_D)]; S0 = np.r_[S0, np.array(extra_S)]
    # fold check (Virginie 2026-11-07, 'corrige-les'): a triangle of WDI points that turns over on vanilla folds the fabric.
    # While one does, its least reliable point leaves the warp (kept on the boards, grey): detected extremes first (top,
    # bottom, leftmost, rightmost), then the added contour and neckline twins, then the hip and hem pairs; her named points
    # stay, a fold among them only is reported
    from scipy.spatial import Delaunay
    nm_ = list(names) + [""] * (len(S) - len(names))
    n_add = len(S0) - len(hip_S) - (0 if NOLEGS else 9)
    rank = [0 if nm_[i] in ("top", "bottom", "leftmost", "rightmost") else 3 if i < n0 else 1 if i < n_add else 2
            for i in range(len(S))]
    keep = np.ones(len(S), bool); folds_left = []
    if NOLEGS:      # no legs: the crotch and leg points do not drive the fabric (the vanilla leg notch came up to the hem)
        for i, n_ in enumerate(nm_):
            if n_ in ("crotch point", "leg bottom L", "leg bottom R", "bottom"):
                keep[i] = False
    for _ in range(40):
        idx = np.where(keep)[0]; tri = Delaunay(S[idx]); worst = None
        for t in tri.simplices:
            a, b, c = idx[t]
            sa = (S[b, 0] - S[a, 0]) * (S[c, 1] - S[a, 1]) - (S[b, 1] - S[a, 1]) * (S[c, 0] - S[a, 0])
            va = (D[b, 0] - D[a, 0]) * (D[c, 1] - D[a, 1]) - (D[b, 1] - D[a, 1]) * (D[c, 0] - D[a, 0])
            if sa * va < 0 and abs(sa) > 20:
                low = min((a, b, c), key=lambda i: rank[i])
                if rank[low] < 3 and (worst is None or rank[low] < rank[worst]):
                    worst = low
                elif rank[low] == 3:
                    folds_left.append((a, b, c))
        if worst is None:
            break
        keep[worst] = False
        folds_left = []
    if POINTWARP:
        U, V = c1.warp_field(c1.TPS(S[keep], D[keep], lam=LAM))
    else:
        import reliefmap as rmap                     # imported here: it imports this module
        Rm = rmap.build(body, facing, rmap.EASE)
        U, V = Rm["U"], Rm["V"]
    W = e5.warp(Gp, U, V)
    wbody = np.zeros((N, N, 4), np.float32); wbody[body_a] = (0.80, 0.80, 0.80, 1)
    tiles = []
    # every pair applied, numbered the same on both sides: yellow = her contour point snapped, cyan = her inner point,
    # orange = added point / its vanilla twin; on 3 a hollow blue ring = where a point was before the legs press
    on = set(res["on"]); n0 = len(src_n)
    kind = [((255, 220, 0) if i in on else (0, 220, 255)) if i < n0 else (255, 140, 0) for i in range(len(S))]
    kind = [k if keep[i] else (150, 150, 150) for i, k in enumerate(kind)]       # grey = left out by the fold check
    nfont = ImageFont.load_default(size=15)

    def numbered(img, P, moved=None):
        d = ImageDraw.Draw(img)
        if moved is not None:
            for (ax, ay), (bx, by) in zip(moved, P):
                if abs(ay - by) > 1:
                    d.line((ax, ay, bx, by), fill=(30, 60, 220), width=2); d.ellipse((ax - 6, ay - 6, ax + 6, ay + 6), outline=(30, 60, 220), width=2)
        for i, (x, y) in enumerate(P):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=kind[i], outline=(0, 0, 0))
            d.text((x + 7, y - 9), str(i + 1), fill=(0, 0, 0), font=nfont, stroke_width=2, stroke_fill=(255, 255, 255))
    # 1 source
    vbody = e5.x4(Vb); vbody[..., :3] = vbody[..., :3] * 0.5 + 0.45
    t = e5.pil(vbody); t.alpha_composite(e5.pil(e5.x4(Vg))); t = e5.on_bg(t); numbered(t, D * 4)
    tiles.append(t)
    # 2 prep: the garment alone on the background (no body under it, which read as a grey ring), the removed band in red
    removed = (e5.x4(Vg[..., 3] > 0.5)) & ~(Gp[..., 3] > 0.5)
    red = np.zeros((N, N, 4), np.float32); red[removed] = (0.9, 0.1, 0.1, 0.75)
    t = e5.on_bg(e5.pil(Gp)); t.alpha_composite(e5.pil(red)); tiles.append(t)
    # 3 target, with the points as applied (after the legs press)
    tg = np.zeros((N, N, 4), np.float32); tg[F] = (1, 1, 1, 0.85); tg[St] = (0.02, 0.02, 0.03, 1)
    t = e5.pil(wbody); t.alpha_composite(e5.pil(tg)); t = e5.on_bg(t); numbered(t, S, S0)
    tiles.append(t)
    # 4 warp, with the points pressed up for the legs (blue: from where to where) and the start row y0 (grey)
    t = e5.pil(wbody); t.alpha_composite(e5.pil(W)); t = e5.on_bg(t); d4 = ImageDraw.Draw(t)
    d4.line((0, y0, N, y0), fill=(120, 120, 120), width=1)
    d4.line([(x, float(mn[x] + dmin)) for x in range(N) if body_a[:, x].any()], fill=(40, 200, 60), width=2)
    for (ax, ay), (bx, by) in zip(S0, S):
        if abs(ay - by) > 1:
            d4.line((ax, ay, bx, by), fill=(30, 60, 220), width=3); d4.ellipse((bx - 5, by - 5, bx + 5, by + 5), fill=(30, 60, 220))
    tiles.append(t)
    # 5 clip + shading
    # the body's shading blurred: its muscles (pecs, abs) are not folds of the cloth
    s = ndi.gaussian_filter(shade, 10) / max(float(np.percentile(shade[body_a], 95)), 1e-3)
    C = W.copy(); C[..., :3] *= ((1 - SHADE) + SHADE * np.clip(s, 0, 1.2))[..., None]
    C[..., 3] = np.where(F, np.maximum(C[..., 3], 0), 0)
    hole = F & (C[..., 3] < 0.5)                                    # inside the outline but no garment pixel: fill nearest
    if hole.any():
        # the fabric's colour smoothed (normalised blur over the garment pixels), carried to the farthest hole pixel:
        # copying the nearest pixel drew streaks fanning out from the edge (Male, first pass)
        okm = F & (C[..., 3] >= 0.5)
        w = okm.astype(np.float32); den = ndi.gaussian_filter(w, 10)
        sm = np.stack([ndi.gaussian_filter(C[..., k] * w, 10) for k in range(3)], -1) / np.maximum(den, 1e-6)[..., None]
        have = den > 0.05
        _, idx = ndi.distance_transform_edt(~have, return_indices=True)
        sm = sm[idx[0], idx[1]]
        C[hole, :3] = sm[hole]; C[hole, 3] = 1.0
    t = e5.pil(wbody); t.alpha_composite(e5.pil(np.clip(C, 0, 1))); tiles.append(e5.on_bg(t)) if B56 else None
    # 6 outline
    # Virginie 2026-11-07 ('le contour noir', step 6): the 4 px hard stroke was a third of the line both artists draw (WDI
    # ShirtBasic 11 to 13 px at 512, vanilla 14, black, soft edge). Now the WDI artist's thickness (his drawing, or the
    # donor's for an undrawn body), black, along every edge of the target (outside, neck hole, hem), its inner side
    # anti-aliased by the distance
    w = ss.STROKE.get(f"{body}_{facing}") if body in crack2.DRAWN else ss.STROKE.get(f"{crack2.DONOR[body]}_{facing}")
    w = float(w or 12.0)
    dist = ndi.distance_transform_edt(F)
    a_line = np.clip(w - dist + 0.5, 0, 1) * F
    O = np.clip(C, 0, 1).copy()
    O[..., :3] = O[..., :3] * (1 - a_line[..., None])
    O[..., 3] = np.where(F, np.maximum(O[..., 3], a_line), O[..., 3])
    t = e5.pil(wbody); t.alpha_composite(e5.pil(O)); tiles.append(e5.on_bg(t)) if B56 else None
    info = f"{len(sw)} contour pairs, {len(aw)} added pairs, {len(S) - len(sw) - len(aw)} inner pairs; d_min {dmin:.0f}; holes filled {int(hole.sum())} px; fold check: left out " + (", ".join(str(i + 1) for i in np.where(~keep)[0]) or "none") + "; folds among her points: " + (", ".join("-".join(str(i + 1) for i in t) for t in folds_left) or "none")
    LAST.update(S=S, S0=S0, D=D, kind=kind, F=F, St=St, Gp=Gp, Vg=Vg, Vb=Vb, body_a=body_a, n0=n0, names=names,
                hem=mn + dmin, y0=y0, nhem=0 if NOLEGS else 9)
    return tiles, info


LAST = {}          # what the last facing_row computed, for the boards (pointsboard.py)


def main():
    body = sys.argv[1] if len(sys.argv) > 1 else "Male"
    font = ImageFont.load_default(size=12); fontb = ImageFont.load_default(size=16)
    T = 420; pad = 6; left = 90; top = 74; head = 18
    cols = ["1 source + vanilla points", "2 black peeled by thickness, no fill", "3 WDI target, points applied", "4 warp, points pressed up for the legs",
            "5 clipped, shaded 0.30", "6 outline 4 px inward"]
    im = Image.new("RGB", (left + 6 * (T + pad), top + 3 * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), f"First full pass, {body}, vanilla {G}, rule 1 (top alone: min(B,C) + d_min).", fill=(0, 0, 0), font=fontb)
    dr.text((8, 30), "Yellow = her points snapped on the outlines, orange = added points (WDI) and their vanilla twins.", fill=(0, 0, 0), font=fontb)
    for j, c in enumerate(cols):
        dr.text((left + j * (T + pad), top - 18), c, fill=(0, 0, 0), font=font)
    for r_, f in enumerate(["south", "east", "north"]):
        y = top + r_ * (T + head + pad)
        try:
            tiles, info = facing_row(body, f)
        except Exception as ex:
            import traceback; traceback.print_exc(); print("FAIL", body, f, repr(ex)[:200]); continue
        dr.text((8, y + head + 6), f, fill=(0, 0, 0), font=fontb)
        dr.text((left, y + 2), info, fill=(0, 0, 0), font=font)
        for j, p in enumerate(tiles):
            im.paste(p.resize((T, T), Image.LANCZOS).convert("RGB"), (left + j * (T + pad), y + head))
        print(body, f, info)
    out = rf"{c1.CAPT}\2026-11-07_fullpass-{body}.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
