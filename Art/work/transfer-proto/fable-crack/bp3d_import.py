"""Reference anatomy from BodyParts3D (DBCLS, CC BY-SA 2.1 JP), laid on the Male frame.

Work aid only (Virginie 2026-11-11): the bones help to place the anatomy, nothing of them goes into the mod, and the
data stays out of git (out/bp3d/). Download: https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
(isa_BP3D_4.0_obj_99.zip as out/bp3d/isa_obj.zip, isa_element_parts.txt beside it).

    uv run --with numpy python bp3d_import.py inspect     axes, extents, landmark bones
    uv run --with numpy python bp3d_import.py             out/bp3d/bones.npz and muscles.npz in the Male frame

The fit is one scale per axis (cage width, jugular notch to pubis, cage depth): a real body laid on the sprite torso,
which is wide and short. The arms are then opened about the head of the humerus to the angle of the ghost arms.
"""
import collections
import pathlib
import sys
import zipfile

import numpy as np

HERE = pathlib.Path(__file__).parent / "out" / "bp3d"
BONE_SETS = ("bone organ", "costal cartilage", "body of sternum", "manubrium", "xiphoid process")   # the sternum is listed by its zones only
TORSO = ("rib", "sternum", "manubrium", "xiphoid", "thoracic vertebra", "lumbar vertebra", "sacrum", "coccyx", "hip bone",
         "clavicle", "scapula", "costal cartilage")
ARM = ("humerus", "radius", "ulna", "carpal", "metacarpal", "phalanx of", "scaphoid", "lunate", "triquetr", "pisiform",
       "trapezium", "trapezoid", "capitate", "hamate", "hand", "finger", "thumb")
LEGWORDS = ("foot", "toe", "tarsal")
# Reference-only landmarks for the cervico-thoracic pass.  These stay separate from the procedural muscle stack:
# BodyParts3D supplies their real attachments, while the stack remains the editable, source-fitted skin underneath.
MUSCLE_SETS = (
    "right sternocleidomastoid",
    "ascending part of right trapezius", "transverse part of right trapezius", "descending part of right trapezius",
    "clavicular part of right pectoralis major", "sternocostal part of right pectoralis major",
    "abdominal part of right pectoralis major",
)
MUSCLE_TAGS = ("muscle organ", "zone of muscle organ")
MUSCLE_GENERIC = set(MUSCLE_TAGS + (
    "muscle of head", "muscle of neck", "muscle of thorax", "muscle of abdomen", "muscle of upper limb", "muscle of lower limb",
    "muscle of pelvis", "muscle of vertebral column", "superficial muscle of neck", "organ", "solid organ",
    "anatomical entity", "anatomical structure", "physical anatomical entity", "material anatomical entity",
))


def names(allowed=BONE_SETS):
    by = collections.defaultdict(list); count = collections.Counter()
    for ln in (HERE / "isa_element_parts.txt").read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        if len(c) >= 3:
            by[c[2]].append(c[1]); count[c[1]] += 1
    keep = {fj for fj, ns in by.items() if any(n in allowed for n in ns)}
    out = {}
    for fj in keep:
        # Bone objects are all also labelled "bone organ".  Prefer the named sternal zones, then the least-shared
        # anatomical name (right clavicle, seventh cervical vertebra, …) used by orient() and the diagnostics.
        if allowed == BONE_SETS:
            labels = by[fj]
            out[fj] = min(labels, key=lambda n: (n not in BONE_SETS[2:], count[n], -len(n)))
        else:
            labels = [n for n in by[fj] if n in allowed]
            out[fj] = min(labels, key=lambda n: (count[n], -len(n)))
    return out


def read_obj(txt):
    v, f = [], []
    for ln in txt.splitlines():
        if ln.startswith("v "):
            v.append([float(t) for t in ln.split()[1:4]])
        elif ln.startswith("f "):
            ix = [int(t.split("/")[0]) - 1 for t in ln.split()[1:]]
            for k in range(1, len(ix) - 1):
                f.append([ix[0], ix[k], ix[k + 1]])
    return np.asarray(v, np.float32), np.asarray(f, np.int32)


def load(allowed=BONE_SETS):
    return load_named(names(allowed))


def load_named(nm):
    out = {}
    with zipfile.ZipFile(HERE / "isa_obj.zip") as z:
        files = {pathlib.PurePosixPath(n).stem: n for n in z.namelist() if n.lower().endswith(".obj")}
        for fj, name in nm.items():
            if fj in files:
                out[fj] = (name, *read_obj(z.read(files[fj]).decode("utf-8", "replace")))
    return out


def all_muscle_names():
    """One representative of every BP3D skeletal-muscle object (right side only; the viewer mirrors it)."""
    by = collections.defaultdict(list); count = collections.Counter()
    for ln in (HERE / "isa_element_parts.txt").read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        if len(c) >= 3:
            by[c[2]].append(c[1]); count[c[1]] += 1
    out = {}
    for fj, labels in by.items():
        if not any(n in MUSCLE_TAGS for n in labels):
            continue
        specific = [n for n in labels if n not in MUSCLE_GENERIC]
        if not specific or any("left " in n or " of left " in n for n in specific):
            continue
        out[fj] = min(specific, key=lambda n: (count[n], -len(n)))
    return out


def find(B, word, side=None):
    r = [(n, v) for n, v, f in B.values() if word in n and (side is None or n.startswith(side))]
    return r


def inspect():
    B = load()
    allv = np.concatenate([v for _, v, _ in B.values()])
    print("bones", len(B), "min", allv.min(0).round(1), "max", allv.max(0).round(1))
    for w in ("right clavicle", "left clavicle", "manubrium", "body of sternum", "right scapula", "right humerus", "right femur", "right hip bone",
              "frontal bone", "mandible", "seventh cervical vertebra", "first thoracic vertebra", "fifth lumbar vertebra", "right seventh rib",
              "right radius", "right calcaneus", "right first rib", "occipital bone", "sacrum"):
        for n, v in find(B, w):
            if n == w:
                print(f"{n:28s} min {v.min(0).round(1)} max {v.max(0).round(1)}")
    print(sorted({n for n, _, _ in B.values()})[:400])


# Male frame landmarks the reference is laid on (stack3d.MALE and skeleton_detail)
ROW_NOTCH, ROW_PUBIS = 203.0, 404.0        # jugular notch, lower edge of the pubic symphysis
CAGE_HALF = 74.0                           # outer half width of the rib barrel
Z_FRONT, Z_BACK = 322.0, 196.0             # sternum line and rib angles
ARM_DEG = 38.0                             # abduction of the ghost arms (head of the humerus to the wrist)
CELL = 1.2                                 # vertex clustering, px of the Male frame
CHEST_WIDTH_GAIN = 0.08                    # local lateral room for the axillary cage; depth is deliberately unchanged
PELVIS_WIDTH_GAIN = 0.12                   # the imported pelvis must remain inside the fitted WDI skin
HEADWORDS = ("frontal", "parietal", "occipital", "temporal", "sphenoid", "ethmoid", "maxilla", "mandible",
             "nasal", "zygomatic", "lacrimal", "palatine", "vomer", "concha")


def orient(B):
    """BodyParts3D axes to (right, up, front), signs from the bones themselves."""
    c = lambda w: np.concatenate([v for n, v in find(B, w) if n == w]).mean(0)
    allv = np.concatenate([v for _, v, _ in B.values()])
    up = int(np.argmax(allv.max(0) - allv.min(0)))
    d = c("right clavicle") - c("left clavicle")
    lat = int(np.argmax(np.abs(d)))
    ap = 3 - up - lat
    su = 1.0 if c("frontal bone")[up] > c("right femur")[up] else -1.0
    sl = 1.0 if d[lat] > 0 else -1.0
    sa = 1.0 if c("body of sternum")[ap] > c("seventh thoracic vertebra")[ap] else -1.0
    return lambda v: np.stack([sl * v[:, lat], su * v[:, up], sa * v[:, ap]], 1)


def cluster(v, f, cell):
    q = np.round(v / cell).astype(np.int64)
    _, first, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    f2 = inv.reshape(-1)[f]
    ok = (f2[:, 0] != f2[:, 1]) & (f2[:, 1] != f2[:, 2]) & (f2[:, 0] != f2[:, 2])
    return v[first], f2[ok]


def smooth01(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def thorax_width(v):
    """Give the cage room below the arms without changing its depth, neck root or pelvis."""
    out = v.copy(); r = out[:, 1]
    band = smooth01((r - 214.0) / 28.0) * (1.0 - smooth01((r - 326.0) / 32.0))
    out[:, 0] *= 1.0 + CHEST_WIDTH_GAIN * band
    return out


def pelvis_width(v):
    """Taper only pelvis bones back inside the source silhouette; do not alter the ghost legs."""
    out = v.copy(); r = out[:, 1]
    out[:, 0] *= 1.0 - PELVIS_WIDTH_GAIN * smooth01((r - 326.0) / 30.0)
    return out


def head_fit(v):
    """Contain the reference skull within the ghost head envelope without flattening the face."""
    out = v.copy()
    out[:, 0] *= 0.90
    out[:, 1] = 128.0 + (out[:, 1] - 128.0) * 0.90
    # The WDI ghost head is shallow at the occiput.  Compress only its rear strongly; keep enough face projection.
    dz = out[:, 2] - 250.0
    out[:, 2] = 254.0 + np.where(dz < 0.0, dz * 0.55, dz * 0.72)
    return out


def frame():
    """(O, T): BodyParts3D axes to (right, up, front), then mm to the Male frame (one scale per axis), from the bones."""
    B = load(); O = orient(B)
    P = {fj: (n, O(v), f) for fj, (n, v, f) in B.items()}
    get = lambda w: np.concatenate([v for n, v, _ in P.values() if n == w])
    ribs = np.concatenate([v for n, v, _ in P.values() if n.endswith(" rib")])
    x0 = float(get("body of sternum")[:, 0].mean())
    notch = float(get("manubrium")[np.abs(get("manubrium")[:, 0] - x0) < 6.0][:, 1].max())
    hip = get("right hip bone"); pubis = float(hip[np.abs(hip[:, 0] - x0) < 12.0][:, 1].min())
    half = float(np.abs(ribs[:, 0] - x0).max())
    mid = ribs[np.abs(ribs[:, 1] - (notch + pubis) / 2 - (notch - pubis) * 0.2) < (notch - pubis) * 0.15]
    f1, f0 = float(get("body of sternum")[:, 2].max()), float(mid[:, 2].min())
    sx = CAGE_HALF / half; sy = (ROW_PUBIS - ROW_NOTCH) / (notch - pubis); sz = (Z_FRONT - Z_BACK) / (f1 - f0)
    T = lambda v: np.stack([(v[:, 0] - x0) * sx, ROW_NOTCH + (notch - v[:, 1]) * sy, Z_BACK + (v[:, 2] - f0) * sz], 1).astype(np.float32)
    return O, T


def build():
    B = load(); O = orient(B)
    P = {fj: (n, O(v), f) for fj, (n, v, f) in B.items()}
    get = lambda w: np.concatenate([v for n, v, _ in P.values() if n == w])
    ribs = np.concatenate([v for n, v, _ in P.values() if n.endswith(" rib")])
    x0 = float(get("body of sternum")[:, 0].mean())
    notch = float(get("manubrium")[np.abs(get("manubrium")[:, 0] - x0) < 6.0][:, 1].max()) if True else 0.0
    hip = get("right hip bone"); pubis = float(hip[np.abs(hip[:, 0] - x0) < 12.0][:, 1].min())
    half = float(np.abs(ribs[:, 0] - x0).max())
    mid = ribs[np.abs(ribs[:, 1] - (notch + pubis) / 2 - (notch - pubis) * 0.2) < (notch - pubis) * 0.15]
    f1, f0 = float(get("body of sternum")[:, 2].max()), float(mid[:, 2].min())
    sx = CAGE_HALF / half; sy = (ROW_PUBIS - ROW_NOTCH) / (notch - pubis); sz = (Z_FRONT - Z_BACK) / (f1 - f0)
    print(f"mm to px: width {sx:.3f} height {sy:.3f} depth {sz:.3f} (width / height {sx / sy:.2f})")
    T = lambda v: np.stack([(v[:, 0] - x0) * sx, ROW_NOTCH + (notch - v[:, 1]) * sy, Z_BACK + (v[:, 2] - f0) * sz], 1).astype(np.float32)
    hum = T(get("right humerus")); top = hum[hum[:, 1] < hum[:, 1].min() + 0.12 * np.ptp(hum[:, 1])]
    head = top.mean(0)
    wrist = T(get("right radius")); wrist = wrist[wrist[:, 1] > wrist[:, 1].max() - 6.0].mean(0)
    cur = np.degrees(np.arctan2(wrist[0] - head[0], wrist[1] - head[1]))
    a = np.radians(ARM_DEG - cur); ca, sa = np.cos(a), np.sin(a)
    print(f"head of the humerus {head.round(1)}, arm {cur:.1f} deg, opened by {np.degrees(a):.1f} deg")
    out = {"t": ([], [], 0), "g": ([], [], 0)}
    kept = collections.Counter()
    for n, v, f in P.values():
        if "left" in n.split():
            continue
        v = T(v); bare = n.replace("right ", "")
        if any(w in bare for w in TORSO):
            v = thorax_width(v)
        if any(w in bare for w in ("hip bone", "sacrum", "coccyx")):
            v = pelvis_width(v)
        if any(w in bare for w in HEADWORDS):
            v = head_fit(v)
        if any(w in bare for w in ARM) and not any(w in bare for w in LEGWORDS) and v[:, 0].mean() > head[0] - 30:
            dx, dr = v[:, 0] - head[0], v[:, 1] - head[1]
            v = np.stack([head[0] + ca * dx + sa * dr, head[1] - sa * dx + ca * dr, v[:, 2]], 1)
            k = "g"
        else:
            k = "t" if any(w in bare for w in TORSO) else "g"
        v, f = cluster(v, f, CELL)
        V, F, off = out[k]; V.append(v); F.append(f + off); out[k] = (V, F, off + len(v)); kept[k] += 1
    np.savez_compressed(HERE / "bones.npz", tv=np.concatenate(out["t"][0]), tf=np.concatenate(out["t"][1]),
                        gv=np.concatenate(out["g"][0]), gf=np.concatenate(out["g"][1]))
    print("torso bones", kept["t"], "vertices", out["t"][2], "| limb and head bones", kept["g"], "vertices", out["g"][2])
    for w in ("right clavicle", "right scapula", "right humerus", "frontal bone", "mandible", "right femur", "right calcaneus", "right hip bone"):
        v = T(get(w))
        if any(k in w for k in TORSO):
            v = thorax_width(v)
        if any(k in w for k in ("hip bone", "sacrum", "coccyx")):
            v = pelvis_width(v)
        print(f"  {w:16s} x {v[:, 0].min():.0f}..{v[:, 0].max():.0f}  rows {v[:, 1].min():.0f}..{v[:, 1].max():.0f}  z {v[:, 2].min():.0f}..{v[:, 2].max():.0f}")

    # Full optional atlas: each object stays separate so the viewer can expose the actual gaps and attachments.  The
    # right half only is stored; the viewer mirrors it.  These are comparison meshes, never substituted for fitted skin.
    M = load_named(all_muscle_names())
    payload = {"names": np.asarray([n for n, _, _ in M.values()])}
    for i, (n, v, f) in enumerate(M.values()):
        v, f = cluster(thorax_width(T(O(v))), f, CELL)
        payload[f"v{i}"] = v; payload[f"f{i}"] = f
        print(f"  {n:38s} vertices {len(v)}")
    np.savez_compressed(HERE / "muscles.npz", **payload)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "inspect":
        inspect()
    else:
        build()
