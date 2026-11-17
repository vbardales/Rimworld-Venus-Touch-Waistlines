"""The trunk muscles of the stack taken from BodyParts3D (2026-11-17, Virginie: 'repars de ceux de la lib pour tous ceux
validés ici').

Each muscle of the stack that BodyParts3D 4.0 has is replaced by the BodyParts3D mesh (right side), laid on the Male frame
by the same fit as the reference bones (bp3d_import.frame and thorax_width), then made solid on the grid. The ones the
library does not have stay hand-made in stack3d.build_male: rectus abdominis, latissimus dorsi, thoracolumbar fascia and
multifidus (BodyParts3D 4.0 has no rectus abdominis, latissimus dorsi, multifidus, internal oblique, transversus abdominis
or quadratus lumborum).

    uv run --with numpy --with scipy python bp3d_torso.py      writes out/bp3d/torso_muscles.npz (meshes, Male frame)

stack3d.build_male reads that file through prim(); without it the hand-made shapes stay.
"""
import collections
import pathlib

import numpy as np
from scipy import ndimage as ndi

HERE = pathlib.Path(__file__).parent / "out" / "bp3d"
PATH = HERE / "torso_muscles.npz"

# stack part name -> BodyParts3D objects (right side)
GROUPS = {
    "trapezius (upper)": ["descending part of right trapezius"],
    "trapezius (middle, lower)": ["transverse part of right trapezius", "ascending part of right trapezius"],
    "serratus": ["right serratus anterior"],
    "pectoralis major": ["clavicular part of right pectoralis major", "sternocostal part of right pectoralis major",
                         "abdominal part of right pectoralis major"],
    "external oblique": ["right external oblique"],
    "erector spinae": ["right iliocostalis lumborum", "right iliocostalis thoracis", "right longissimus thoracis",
                       "right spinalis thoracis"],
    "infraspinatus, teres, rhomboid": ["right infraspinatus muscle", "right supraspinatus", "right teres major",
                                       "right teres minor", "right rhomboid major", "right rhomboid minor"],
    "gluteus minimus": ["right gluteus minimus"],
    "gluteus medius": ["right gluteus medius"],
    "gluteus maximus": ["right gluteus maximus"],
    "psoas major": ["right psoas major"],
    "iliacus": ["right iliacus"],
    "tensor fasciae latae": ["right tensor fasciae latae"],
    # Virginie 2026-11-17: every muscle whose belly lies in the pelvis and femur stump block, cut at the stump plane
    "piriformis": ["right piriformis"],
    "obturator internus": ["right obturator internus"],
    "obturator externus": ["right obturator externus"],
    "gemellus superior": ["right gemellus superior"],
    "gemellus inferior": ["right gemellus inferior"],
    "quadratus femoris": ["right quadratus femoris"],
    "thigh, rectus femoris": ["right rectus femoris"],
    "thigh, vastus intermedius": ["right vastus intermedius"],
    "thigh, vastus medialis": ["right vastus medialis"],
    "thigh, vastus lateralis": ["right vastus lateralis"],
    "thigh, sartorius": ["right sartorius"],
    "thigh, pectineus": ["right pectineus"],
    "thigh, adductor longus": ["right adductor longus"],
    "thigh, adductor brevis": ["right adductor brevis"],
    "thigh, adductor magnus": ["right adductor magnus"],
    "thigh, gracilis": ["right gracilis"],
    "thigh, biceps femoris (long head)": ["long head of right biceps femoris"],
    "thigh, semitendinosus": ["right semitendinosus"],
    "thigh, semimembranosus": ["right semimembranosus"],
}
# groups laid with the pelvis bones (bp3d_import.pelvis_width, like the hip bone and the sacrum)
ROTATORS = ("piriformis", "obturator internus", "obturator externus", "gemellus superior", "gemellus inferior", "quadratus femoris")
PELVIC = {k for k in GROUPS if k in ROTATORS or k.startswith("thigh, ")}


# bones of the trunk (2026-11-17, Virginie: 'pareil pour les os'): display groups -> name words of BodyParts3D bones
BONES = {
    "spine (BodyParts3D)": ("thoracic vertebra", "lumbar vertebra", "sacrum", "coccyx"),
    "rib cage (BodyParts3D)": (" rib", "costal cartilage", "body of sternum", "manubrium", "xiphoid process"),
    "clavicle (BodyParts3D)": ("clavicle",),
    "scapula (BodyParts3D)": ("scapula",),
    "hip bone (BodyParts3D)": ("hip bone",),
    "femur (BodyParts3D)": ("femur",),   # stack3d cuts it at the thigh stump plane
}


def build_bones(O, T, out):
    import bp3d_import as bi
    B = bi.load()
    for key, words in BONES.items():
        V, F, off = [], [], 0
        for fj, (n, v, f) in B.items():
            if "left" in n.split() or not any(wd in n or n.endswith(wd.strip()) for wd in words):
                continue
            v = bi.thorax_width(T(O(v)))
            if any(wd in n for wd in ("hip bone", "sacrum", "coccyx", "femur")):
                v = bi.pelvis_width(v)
            V.append(v); F.append(f + off); off += len(v)
        if V:
            k = "bone_" + key.split(" (")[0].replace(" ", "_")
            out[f"v_{k}"] = np.concatenate(V); out[f"f_{k}"] = np.concatenate(F)
            v = out[f"v_{k}"]
            print(f"  {key:36s} {len(V)} bones  x {v[:, 0].min():.0f}..{v[:, 0].max():.0f}  rows {v[:, 1].min():.0f}..{v[:, 1].max():.0f}  z {v[:, 2].min():.0f}..{v[:, 2].max():.0f}")


def bone_prim(key):
    return prim("bone_" + key.split(" (")[0].replace(" ", "_"))


def build():
    import bp3d_import as bi
    O, T = bi.frame()
    by = collections.defaultdict(list)
    for ln in (HERE / "isa_element_parts.txt").read_text(encoding="utf-8").splitlines()[1:]:
        c = ln.split("\t")
        if len(c) >= 3:
            by[c[1]].append(c[2])
    want = {n: by[n][0] for g in GROUPS.values() for n in g if by.get(n)}
    missing = [n for g in GROUPS.values() for n in g if n not in want]
    if missing:
        print("not in BodyParts3D:", missing)
    M = bi.load_named({fj: n for n, fj in want.items()})
    mesh = {n: (v, f) for fj, (n, v, f) in M.items()}
    out = {}
    for key, names in GROUPS.items():
        V, F, off = [], [], 0
        for n in names:
            if n not in mesh:
                continue
            v, f = mesh[n]
            v = bi.thorax_width(T(O(v)))
            if key in PELVIC:
                v = bi.pelvis_width(v)
            V.append(v); F.append(f + off); off += len(v)
        if V:
            k = key.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
            out[f"v_{k}"] = np.concatenate(V); out[f"f_{k}"] = np.concatenate(F)
            v = out[f"v_{k}"]
            print(f"  {key:36s} {len(names)} parts  x {v[:, 0].min():.0f}..{v[:, 0].max():.0f}  rows {v[:, 1].min():.0f}..{v[:, 1].max():.0f}  z {v[:, 2].min():.0f}..{v[:, 2].max():.0f}")
    build_bones(O, T, out)
    np.savez_compressed(PATH, **out)
    print(PATH)


_CACHE = {}


def prim(key, h=1.0):
    """(fn, lo, hi) of the solid of a group, or None when the file or the group is absent. The solid: the triangles
    sampled every h/3, those voxels closed (fill holes), then a signed distance on a 1 px grid around it."""
    if not PATH.exists():
        return None
    k = key.replace(" ", "_").replace(",", "").replace("(", "").replace(")", "")
    if (k, h) not in _CACHE:
        D = np.load(PATH)
        if f"v_{k}" not in D:
            return None
        v, f = D[f"v_{k}"].astype(np.float64), D[f"f_{k}"]
        g = 1.0
        lo = v.min(0) - 6.0; hi = v.max(0) + 6.0
        shp = tuple(int(np.ceil((hi[i] - lo[i]) / g)) + 1 for i in range(3))
        occ = np.zeros(shp, bool)
        a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
        n = int(np.ceil(max(np.linalg.norm(b - a, axis=1).max(), np.linalg.norm(c - a, axis=1).max()) / (g / 3.0))) + 1
        for i in range(n + 1):
            for j in range(n + 1 - i):
                p = a + (b - a) * (i / n) + (c - a) * (j / n)
                q = np.round((p - lo) / g).astype(int)
                occ[q[:, 0], q[:, 1], q[:, 2]] = True
        occ = ndi.binary_closing(occ, iterations=1)
        occ = ndi.binary_fill_holes(occ)
        sd = (ndi.distance_transform_edt(~occ) - ndi.distance_transform_edt(occ)) * g
        _CACHE[(k, h)] = (sd.astype(np.float32), lo, g)
    sd, lo, g = _CACHE[(k, h)]

    def fn(X, R, Z):
        co = [(np.broadcast_to(X, np.broadcast_shapes(X.shape, R.shape, Z.shape)) - lo[0]) / g,
              (np.broadcast_to(R, np.broadcast_shapes(X.shape, R.shape, Z.shape)) - lo[1]) / g,
              (np.broadcast_to(Z, np.broadcast_shapes(X.shape, R.shape, Z.shape)) - lo[2]) / g]
        out = ndi.map_coordinates(sd, co, order=1, mode="constant", cval=50.0)
        return out.astype(np.float32)

    hi = lo + (np.array(sd.shape) - 1) * g
    return fn, lo + 6.0, hi - 6.0


if __name__ == "__main__":
    build()
