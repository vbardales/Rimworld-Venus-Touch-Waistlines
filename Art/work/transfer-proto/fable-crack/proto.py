"""Body prototypes M, W, T, H, F, C (2026-11-17, Virginie): all start equal to the Male average (the Male stack on
the Male sprite, with its fat), then each gets its own targets: fat, muscle and bone share of the mass, and the widths of
shoulders, upper chest, waist and pelvis relative to the shoulders.

This first part measures the Male average: the composition of the torso stack (volumes of bone, viscera, muscle, fat
pads, fat and the rest under the skin, masses with tissue densities) and the half-width profile of the skin.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python proto.py [h]
"""
import sys

import numpy as np
from scipy import ndimage as ndi

import stack3d as s

DENS = {"bone": 1.85, "viscera": 1.04, "viscera (thorax)": 0.45, "muscle": 1.06, "fat pads": 0.92, "fat": 0.92, "rest": 1.10}   # g/cm3
# the thoracic cavity holds the lungs (about 0.3 g/cm3, mostly air) and the heart: 0.45 on average, above the diaphragm
DIAPHRAGM = 300.0
DENS_MARROW = 1.0


def carry(K, a):
    out = K["steps"][0].warp(K["G0"], a, 1, K["G"])
    for f in K["steps"][1:]:
        out = f.warp(K["G"], out, 1)
    return out


def layer_fields(K):
    """Signed fields on the body grid: bone (display bones), muscle, fat pads, lean (whole stack), fat solid."""
    G, S, G0 = K["G"], K["S"], K["G0"]
    un = {"bone": G0.full(), "muscle": G0.full(), "fat": G0.full()}
    for name, layer, colour, sl, a in S.parts:
        if a is not None and layer in un:
            un[layer][sl] = np.minimum(un[layer][sl], a)
    fat = K["fat"]
    for f in K["steps"][1:]:
        fat = f.warp(G, fat, 1)
    return {"bone": carry(K, un["bone"]), "muscle": carry(K, un["muscle"]), "pads": carry(K, un["fat"]),
            "lean": carry(K, S.d), "fat": fat}


def composition(F, d, h):
    """Mass shares (%) inside the skin d: every layer less the ones under it; the fat outside the lean counts as fat."""
    skin = d < 0
    bone = F["bone_vox"] if "bone_vox" in F else F["bone"] < 0
    musc = (F["muscle_vox"] if "muscle_vox" in F else F["muscle"] < 0) & ~bone
    pads = (F["pads"] < 0) & ~bone & ~musc
    lean = F["lean"] < 0
    fat = (F["fat"] < 0) | F.get("grown", np.zeros_like(skin))   # the skin grown outward (prototype fat) is fat too
    under = bone | musc | pads
    fat = fat & ~lean & ~under
    vox = {"bone": bone, "muscle": musc, "fat pads": pads, "viscera": lean & ~under, "fat": fat,
           "rest": ~fat & ~lean & ~under}
    if "thorax" in F:
        vox["viscera (thorax)"] = vox["viscera"] & F["thorax"]
        vox["viscera"] = vox["viscera"] & ~F["thorax"]
    mass = {k: float((m & skin).sum()) * h ** 3 * DENS[k] for k, m in vox.items()}
    q = F.get("bone_frac", 1.0)                                  # share of a bone's volume that is bone tissue; the rest is marrow
    if q < 1.0:
        vb = mass["bone"] / DENS["bone"]
        mass["bone"] = q * vb * DENS["bone"]; mass["rest"] += (1.0 - q) * vb * DENS_MARROW
    tot = sum(mass.values())
    return {k: 100.0 * v / tot for k, v in mass.items()}


# Prototype targets: widths relative to the shoulders (Virginie 2026-11-17). Rows of the Male frame where each is read:
# shoulders = widest row (deltoid stump, 268), upper chest = under the armpits (298), waist = navel (358), pelvis = hips (382).
WROWS = {"shoulders": 268.0, "upper chest": 298.0, "waist": 358.0, "pelvis": 382.0}
# The three bodies (Virginie 2026-11-17):
#   WDI source = the stylised starting silhouette; no biological composition is attributed to it.
#   M1 lean / athletic = a chosen target: about 12 % fat, superficial muscles at about 100 %.
#   M average = about 20 to 23 % fat, superficial muscles at about 80 to 90 % of M1, envelope and pads thicker and softer.
# M of 2026-11-17 (second sheet): fat 23 %, muscle 42 %, bone 4 %; shoulders 43 cm, upper chest 34, waist 31, pelvis 33
PROTO = {"M": {"shoulders": 1.0, "upper chest": 0.79, "waist": 0.72, "pelvis": 0.77},
         "M1": None}   # M1 keeps the widths of the WDI source silhouette (no target of its own yet)
# Solved together by solve_comp: fat by the slider, bone by the shell counted, muscle by the thickening of the muscles.
COMP = {"M": {"fat": 23.0, "muscle": 42.0, "bone": 4.0},
        "M1": {"fat": 12.0, "muscle": 42.0, "bone": 4.0}}
# body type of each prototype. M (average): the superficial muscles at 80 to 90 % of the relief of M1, the upper trapezius
# toned down most (80 %), the rectus abdominis not reinforced; bones and deep muscles unchanged (Virginie 2026-11-17)
TY = {"M": dict(s.TYPES["Male"], abs=1.0, relief={"pectoralis major": 0.85, "latissimus dorsi": 0.85, "trapezius (upper)": 0.8,
                                                   "trapezius (middle, lower)": 0.9, "gluteus maximus": 0.9, "external oblique": 0.9}),
      "M1": s.TYPES["Male"]}


def width_scale(G, d, target):
    """Row-wise width scale that brings the skin half widths at WROWS to target x shoulder width (1 above the
    shoulders, held below the pelvis)."""
    xm = np.nanmax(s.last_cross(d, 1, G.x), axis=1)
    hw = lambda r: float(np.interp(r, G.r, np.nan_to_num(xm)))
    sh = hw(WROWS["shoulders"])
    rows = [WROWS[k] for k in WROWS]
    k = [target[n] * sh / hw(WROWS[n]) for n in WROWS]
    return rows, k


# Shape edits on top of the widths (Virginie 2026-11-17 on M: 'étire la cage thoracique, remonte les pectoraux,
# retravaille les fesses'), all as smooth displacements of the finished stack (skin, muscles, bones move together):
#   cage: rows of the thorax stretched down: the costal margin (334) goes to 334 + cage, the crotch (422) stays;
#   pecs: the front of the chest (rows 250..345, x < 85) lifted by pecs px, most at the under-chest fold;
#   glutes: the back of the buttocks pushed back by glutes px and up by a third of it, round, centred on each cheek.
SHAPE = {"M": dict(cage=12.0, pecs=12.0, glutes=7.0), "M1": dict(cage=0.0, pecs=0.0, glutes=0.0)}
SHAPE_SMOOTH = 24.0   # px along the rows: the width and cage profiles are smoothed over this, no crease at their nodes


def sstep(v):
    v = np.clip(v, 0, 1)
    return v * v * (3 - 2 * v)


def bump(v, c, wd):
    """1 at c, 0 at c +/- wd, smooth."""
    return sstep(1.0 - np.abs(v - c) / wd)


def shaped(G, Gs, fields, rows, k, zc, sh):
    """Fields of the Male stack, scaled in width (rows, k), then edited by SHAPE: inverse map from each output voxel."""
    X, R, Z = (np.broadcast_to(a, G.shape).astype(np.float32) for a in G.coords((slice(None),) * 3))
    zm = np.interp(R, *zc).astype(np.float32)
    front = sstep((Z - zm) / 12.0); back = sstep((zm - Z) / 12.0)
    # glutes (undone first: they are the last edit)
    g = sh["glutes"] * bump(R, 402.0, 28.0) * bump(X, 30.0, 34.0) * back
    Z = Z + g; R = R + g / 3.0
    # pecs: output at R shows what was lower
    p = sh["pecs"] * bump(R, 315.0, 55.0) * sstep((85.0 - X) / 20.0) * front
    R = R + p
    # cage and widths: the piecewise linear profiles creased the skin at every node (hard horizontal steps on M), so both
    # are smoothed along the rows over SHAPE_SMOOTH px before use
    rt = np.arange(100.0, 520.0, 0.5)
    sg = SHAPE_SMOOTH / 0.5
    cage = ndi.gaussian_filter1d(np.interp(rt, [0.0, 232.0, 334.0 + sh["cage"], 422.0, 1000.0], [0.0, 232.0, 334.0, 422.0, 1000.0]),
                                 sg, mode="nearest")
    R = np.interp(R, rt, cage).astype(np.float32)
    kk = ndi.gaussian_filter1d(np.interp(rt, rows, k), sg, mode="nearest")
    X = X / np.interp(R, rt, kk).astype(np.float32)
    co = np.stack([(R - Gs.r[0]) / Gs.h, X / Gs.h, (Z - Gs.z[0]) / Gs.h])
    out = []
    for a, order in fields:
        out.append(ndi.map_coordinates(a.astype(np.float32), co, order=order, mode="nearest"))
    return out


PAD_GAIN = 1.5        # a pad adds 1.5 times the global layer where it lies (2.5 made bubbles once the envelope was smooth)
PAD_REACH = 40.0      # px from a pad over which its extra fat fades (broad: a pad melts into the layer, not a lump)


def fat_fields(G, F, d00, zc_rows):
    """near (pad weight) and dd (signed distance of the smooth envelope) for the fat slider."""
    pad = F["pads"] < 0
    front = G.z[None, None, :] >= np.asarray(zc_rows, np.float32)[:, None, None]
    sg = PAD_REACH / 2.0 / G.h
    wF = ndi.gaussian_filter((pad & front).any(axis=2).astype(np.float32), sg)
    wB = ndi.gaussian_filter((pad & ~front).any(axis=2).astype(np.float32), sg)
    near = np.where(front, np.clip(wF / 0.5, 0, 1)[:, :, None], np.clip(wB / 0.5, 0, 1)[:, :, None]).astype(np.float32)
    return near, envelope(G, d00 < 0)


def bisect(f, target, lo, hi, n=14):
    """x in [lo, hi] where the increasing f(x) meets target."""
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if f(mid) < target else (lo, mid)
    return 0.5 * (lo + hi)


def solve_comp(G, F, d00, zc_rows, target):
    """Fat, muscle and bone shares solved together (Virginie 2026-11-17: 'solve them'), the silhouette kept.
    fat: the global slider t over the smooth envelope, with the pads (as in solve_fat).
    bone: only a share c of a bone's volume is bone tissue (cortical shell and trabeculae); the rest is marrow, counted
          as internal tissue (BodyParts3D bones are solid, which counted them all at the density of compact bone).
    muscle: every muscle thickened by m px into the room under the skin that is not bone (the gaps between pieces, the
          inside of the envelope): the muscles fill the body instead of floating in unmodelled tissue.
    The three are solved in turn, four rounds. Returns grow, t, near, composition, ref, m, c."""
    near, dd = fat_fields(G, F, d00, zc_rows)
    ins = d00 < 0; envin = dd < 0
    bone0 = F["bone"] < 0
    mus0 = (F["muscle"] < 0) & ~bone0
    mdist = ndi.distance_transform_edt(~mus0) * G.h
    room = ins & ~bone0
    thorax = np.broadcast_to((G.r < DIAPHRAGM)[:, None, None], ins.shape)
    grow = lambda t, gain=PAD_GAIN: dd - t * (1.0 + gain * near)

    def comp(m, c, t):
        dt = grow(t)
        F2 = dict(F); F2["bone_frac"] = c; F2["muscle_vox"] = mus0 | (room & (mdist <= m))
        F2["grown"] = (dt < 0) & ~envin; F2["thorax"] = thorax
        return composition(F2, dt, G.h)
    m, c, t = 0.0, 1.0, 0.0
    for _ in range(4):
        t = bisect(lambda x: (lambda q: q["fat"] + q["fat pads"])(comp(m, c, x)), target["fat"], 0.0, 25.0)
        c = bisect(lambda x: comp(m, x, t)["bone"], target["bone"], 0.0, 1.0)
        m = bisect(lambda x: comp(x, c, t)["muscle"], target["muscle"], 0.0, 40.0)
    t = bisect(lambda x: (lambda q: q["fat"] + q["fat pads"])(comp(m, c, x)), target["fat"], 0.0, 25.0)
    xm = np.nan_to_num(np.nanmax(s.last_cross(d00, 1, G.x), axis=1))
    ref = float(np.interp(WROWS["shoulders"], G.r, xm))
    print(f"solved: fat layer {t:.2f} px ({100 * t / ref:.1f} % of the shoulder half width), bone tissue {100 * c:.0f} % of the bone volume, "
          f"muscles thickened {m:.2f} px")
    return grow, t, near, comp(m, c, t), ref, m, c


def solve_fat(G, F, d00, zc_rows, target):
    """Fat (Virginie 2026-11-17): one global slider t thickens the subcutaneous layer of the whole torso by t px; the four
    pads (flanks, lower belly, suprapubic cushion, lower medial gluteal) add PAD_GAIN x t more where they lie. t is solved
    so fat is target % of the mass. Returns grow(t, gain=PAD_GAIN) -> skin field, t, near (pad weight), composition."""
    # where a pad lies, seen from the front and from the back: its outline on the surface, softened over PAD_REACH px,
    # applied through the whole depth of that side (the pads lie under the skin, the slider thickens the skin over them)
    pad = F["pads"] < 0
    front = G.z[None, None, :] >= np.asarray(zc_rows, np.float32)[:, None, None]
    sg = PAD_REACH / 2.0 / G.h
    wF = ndi.gaussian_filter((pad & front).any(axis=2).astype(np.float32), sg)
    wB = ndi.gaussian_filter((pad & ~front).any(axis=2).astype(np.float32), sg)
    near = np.where(front, np.clip(wF / 0.5, 0, 1)[:, :, None], np.clip(wB / 0.5, 0, 1)[:, :, None]).astype(np.float32)
    # Virginie 2026-11-17: the fat is not an offset of the stacked pieces (it would copy every edge, junction and cut
    # end of the muscles). It grows from one smooth envelope of the whole body: the pieces as one closed volume
    # (envelope), the global layer and the pads thickening that envelope, the skin over it.
    ins = d00 < 0
    dd = envelope(G, ins)
    grow = lambda t, gain=PAD_GAIN: dd - t * (1.0 + gain * near)

    def share(t):
        dt = grow(t)
        # the subcutaneous fat is what the slider grows over the envelope; the gaps the envelope closes between the
        # pieces count as the rest (internal tissue not modelled: junctions, organs, water, skin), not as fat
        Ft = dict(F); Ft["grown"] = (dt < 0) & ~(dd < 0)
        return composition(Ft, dt, G.h)
    lo, hi = 0.0, 25.0
    for _ in range(14):
        mid = 0.5 * (lo + hi)
        c = share(mid)
        lo, hi = (mid, hi) if c["fat"] + c["fat pads"] < target else (lo, mid)
    t = 0.5 * (lo + hi)
    # the slider as an anatomical thickness: a share of the half width of the shoulders, the same over the whole torso
    xm = np.nan_to_num(np.nanmax(s.last_cross(d00, 1, G.x), axis=1))
    ref = float(np.interp(WROWS["shoulders"], G.r, xm))
    pierce = int(((F["lean"] < -0.5) & (grow(t, 0.0) > 0)).sum())
    print(f"fat: global layer {t:.2f} px = {100 * t / ref:.1f} % of the shoulder half width; "
          f"lean voxels outside the fat: {pierce}")
    return grow, t, near, share(t), ref


ENV_CLOSE = 14.0      # px: gaps and hollows narrower than twice this between pieces are filled before the fat
ENV_SMOOTH = 12.0     # px: large-scale smoothing of the envelope (keeps the silhouette, drops the muscle edges)
# envelope and pads of each body: M thicker and softer than M1 (a broader closing and smoothing, broader stronger pads)
ENV = {"M1": dict(ENV_CLOSE=6.0, ENV_SMOOTH=5.0, PAD_GAIN=1.0, PAD_REACH=28.0),
       "M": dict(ENV_CLOSE=14.0, ENV_SMOOTH=12.0, PAD_GAIN=1.5, PAD_REACH=40.0)}


def use_env(name):
    """Set the envelope and pad constants of a body (ENV) for the solves that follow."""
    globals().update(ENV[name])


ENV_COVER = 0.8       # px: the least fat over any piece, before the global layer


def envelope(G, ins):
    """Signed distance (px) of one smooth closed envelope of the solid ins: closed (dilated then eroded by ENV_CLOSE,
    holes filled), redistanced, smoothed over ENV_SMOOTH, then never inside the solid (no piece pierces it)."""
    out = ndi.distance_transform_edt(~ins) * G.h
    closed = ndi.distance_transform_edt(out <= ENV_CLOSE) * G.h > ENV_CLOSE
    closed = ndi.binary_fill_holes(closed | ins)
    sd = ((ndi.distance_transform_edt(~closed) - ndi.distance_transform_edt(closed)) * G.h).astype(np.float32)
    sd = ndi.gaussian_filter(sd, ENV_SMOOTH / G.h)
    # the smoothing shrinks ridges and tips (muscle edges, thigh cut ends) under the envelope. Where a piece would come
    # within ENV_COVER of it, push the envelope out by a broad smooth amount (a max over the neighbourhood, then the
    # same smoothing): the envelope swells gently there, it does not copy the edge.
    lean = ((ndi.distance_transform_edt(~ins) - ndi.distance_transform_edt(ins)) * G.h).astype(np.float32)
    sg = ENV_SMOOTH / G.h; n = 2 * int(np.ceil(2.0 * sg)) + 1
    for _ in range(8):
        need = np.clip(sd - (lean - ENV_COVER), 0.0, None) * (lean < 3.0)
        if need.max() < 0.05:
            break
        sd = sd - ndi.gaussian_filter(ndi.maximum_filter(need, size=n), sg)
    return np.minimum(sd, lean - ENV_COVER).astype(np.float32)   # safety: what is left is below 0.05 px


def fat_map(G, d_before, d_after, near, lean, name):
    """Board: thickness of the fat over the lean stack, front and back (rows down, x mirrored), before and after the
    slider, and where the four pads act. Colour scale 0 (white) to 16 px (dark orange)."""
    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for lab, d in (("avant le curseur", d_before), ("après le curseur", d_after)):
        for side, out in (("face", True), ("dos", False)):
            zs = s.last_cross(d, 2, G.z, out); zl = s.last_cross(lean, 2, G.z, out)
            th = np.abs(zs - zl); th = np.where(np.isfinite(th), th, np.nan)
            k = np.clip(np.nan_to_num(th) / 16.0, 0, 1)
            img = np.stack([255 - 40 * k, 255 - 150 * k, 255 - 230 * k], -1).astype(np.uint8)
            img[~np.isfinite(zs)] = (244, 242, 238)
            full = np.concatenate([img[:, :0:-1], img], axis=1)
            tiles.append((f"{lab}, {side}", Image.fromarray(full).resize((full.shape[1] * 2, full.shape[0] * 2), Image.NEAREST)))
    for side, out in (("face", True), ("dos", False)):
        zs = s.last_cross(d_after, 2, G.z, out)
        iz = np.clip(np.round((np.nan_to_num(zs) - G.z[0]) / G.h).astype(int) - (0 if out else -1), 0, len(G.z) - 1)
        w = np.take_along_axis(near, iz[..., None], 2)[..., 0]
        img = np.stack([255 - 60 * w, 255 - 200 * w, 255 - 60 * w], -1).astype(np.uint8)
        img[~np.isfinite(zs)] = (244, 242, 238)
        full = np.concatenate([img[:, :0:-1], img], axis=1)
        tiles.append((f"pads, {side}", Image.fromarray(full).resize((full.shape[1] * 2, full.shape[0] * 2), Image.NEAREST)))
    W = sum(t[1].width + 8 for t in tiles); H = max(t[1].height for t in tiles) + 40
    out = Image.new("RGB", (W, H), (244, 242, 238)); dr = ImageDraw.Draw(out)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 13)
    dr.text((4, 4), f"Prototype {name} : épaisseur de graisse sur les muscles (blanc 0, orange foncé 16 px) ; en violet, où agissent les 4 pads", fill=(0, 0, 0), font=font)
    x = 0
    for lab, im in tiles:
        dr.text((x + 4, 22), lab, fill=(0, 0, 0), font=font); out.paste(im, (x, 38)); x += im.width + 8
    path = s.CAPT / f"2026-11-17_proto{name}-fat.png"
    out.save(path); print(path)


def proto_board(name, h):
    """Prototype vs WDI: the Male stack (skin, fat, lean) scaled row by row in width to the prototype's ratios, drawn
    by stack3d.board next to the WDI Male (WDI | stack in WDI style | outlines)."""
    import average as av
    use_env(name)
    K = s.make("Male", h, ty=TY[name])
    G, T = K["G"], K["T"]
    if PROTO[name] is None:                                    # the prototype keeps the widths of the WDI body
        rows, k = list(WROWS.values()), [1.0] * len(WROWS)
    else:
        rows, k = width_scale(G, K["d"], PROTO[name])
    print(f"{name}: width scale at {rows}: {[round(x, 3) for x in k]}")
    Go = s.Grid(G.h, x1=float(G.x[-1]) * max(max(k), 1.0) + 4.0, r0=float(G.r[0]), r1=float(G.r[-1]) + 8.0,
                z0=float(G.z[0]) - 8.0, z1=float(G.z[-1]))
    tgt = PROTO[name]
    # fat (Virginie 2026-11-17): one global slider t. It thickens the subcutaneous layer of the whole torso by t px, and the
    # four pads (flanks, lower belly, suprapubic cushion, lower medial gluteal) add PAD_GAIN x t more where they lie, so
    # the male distribution (lower belly and flanks first) grows with it. The slider is solved for the target fat share.
    F = layer_fields(K)
    d00 = K["d"]
    grow, tf, near, comp, ref, mm, bc = solve_comp(G, F, d00, np.interp(G.r, T.rows, T.zc), COMP[name])
    print(f"{name}: fat grown {tf:.2f} px; composition " + ", ".join(f"{k} {v:.1f} %" for k, v in comp.items()))
    K = dict(K); K["d"] = grow(tf)
    _xm = np.nan_to_num(np.nanmax(s.last_cross(K["d"], 1, G.x), axis=1))
    print("half widths after the fat:", {n: round(float(np.interp(r, G.r, _xm)), 1) for n, r in WROWS.items()}, "grid x max", float(G.x[-1]))
    fat_map(G, d00, K["d"], near, F["lean"], name)
    for it in range(10 if tgt is not None else 0):             # the shape edits and the smoothing move the widths: re-solve them on the result
        d, o = shaped(Go, G, [(K["d"], 1), (K["owner"], 0)], rows, k, (T.rows, T.zc), SHAPE[name])
        xm = np.nan_to_num(np.nanmax(s.last_cross(d, 1, Go.x), axis=1))
        hw = lambda r: float(np.interp(r, Go.r, xm))
        sh = hw(WROWS["shoulders"])
        k = [kk * tgt[n] * sh / hw(WROWS[n]) for kk, n in zip(k, WROWS)]
    d, o = shaped(Go, G, [(K["d"], 1), (K["owner"], 0)], rows, k, (T.rows, T.zc), SHAPE[name])
    o = np.round(o).astype(np.int16)
    rep, path = s.board(K["S"], Go, d, T, f"proto{name}", o, extra=f"prototype {name}, fat {100 * tf / ref:.1f} % of the shoulder half width")
    for f, r in rep.items():
        print(f"{f:6s} sil p95 {r['p95']:.2f} | lum {r['mae']:.4f}")
    xm = np.nanmax(s.last_cross(d, 1, Go.x), axis=1)
    sh = float(np.interp(WROWS["shoulders"], Go.r, np.nan_to_num(xm)))
    print("ratios now:", {n: round(float(np.interp(r, Go.r, np.nan_to_num(xm))) / sh, 3) for n, r in WROWS.items()})
    print(path)


def main():
    h = float(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1][0].isdigit() else 1.5
    if len(sys.argv) > 2 and sys.argv[2] in PROTO:
        return proto_board(sys.argv[2], h)
    K = s.make("Male", h)
    G, S, d = K["G"], K["S"], K["d"]
    # the stack's own bone layer is a filled barrel (the rib cage as one solid): the bones are the display parts
    G0 = K["G0"]
    un = {"bone": G0.full(), "muscle": G0.full(), "fat": G0.full()}
    for name, layer, colour, sl, a in S.parts:
        if a is not None and layer in un:
            un[layer][sl] = np.minimum(un[layer][sl], a)
    bone = carry(K, un["bone"]) < 0
    musc = (carry(K, un["muscle"]) < 0) & ~bone
    pads = (carry(K, un["fat"]) < 0) & ~bone & ~musc
    lean = carry(K, S.d) < 0
    fat = K["fat"]
    for f in K["steps"][1:]:
        fat = f.warp(G, fat, 1)
    fat = fat < 0
    skin = d < 0
    vox = {"bone": bone, "muscle": musc, "fat pads": pads, "viscera": lean & ~bone & ~musc & ~pads,
           "fat": fat & ~lean & ~bone & ~musc & ~pads, "rest": skin & ~fat & ~lean & ~bone & ~musc & ~pads}
    v = {k: float((m & skin).sum()) * G.h ** 3 for k, m in vox.items()}
    mass = {k: v[k] * DENS[k] for k in v}
    tot = sum(mass.values())
    print("composition of the torso (share of mass; volume share in brackets):")
    vt = sum(v.values())
    for k in v:
        print(f"  {k:9s} {100 * mass[k] / tot:5.1f} %  ({100 * v[k] / vt:5.1f} % of volume)")
    xm = s.last_cross(d, 1, G.x)                                # half width of the skin per row
    print("half width of the skin per row (Male frame rows):")
    for r in range(190, 432, 6):
        i = int(round((r - G.r[0]) / G.h))
        print(f"  row {r}: {np.nanmax(xm[i]):6.1f}")


if __name__ == "__main__":
    main()
