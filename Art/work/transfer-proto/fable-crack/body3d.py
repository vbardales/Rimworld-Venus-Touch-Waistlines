import json, numpy as np
from scipy.ndimage import gaussian_filter1d
from PIL import Image
D = 'C:/Users/nelim/Documents/rimworld/VenusTouchWaistlines/Art/work/transfer-proto/'
S = 'C:/Users/nelim/AppData/Local/Temp/claude/215bed336962f00b/c583379c-c3d9-40ec-95ff-cf63aa5c516c/scratchpad/'
bodies = ['Male', 'Female', 'Thin', 'Thin_Female', 'Fat', 'Fat_Female', 'Hulk', 'Hulk_Female']
R, A = 140, 56


def mask(b, f):
    return np.array(Image.open(f'{D}E_{b}_{f}.png'))[..., 3] > 127


def rows(m):
    ys = np.where(m.any(1))[0]
    return ys.min(), ys.max()


out = {}
for b in bodies:
    s, e = mask(b, 'south'), mask(b, 'east')
    s0, s1 = rows(s)
    e0, e1 = rows(e)
    cx = np.mean([np.where(s[y])[0].mean() for y in range(s0, s1 + 1)])
    prof = []
    for i in range(R):
        t = i / (R - 1)
        ys = int(round(s0 + t * (s1 - s0)))
        ye = int(round(e0 + t * (e1 - e0)))
        xs = np.where(s[ys])[0]
        xe = np.where(e[ye])[0]
        prof.append(None if len(xs) == 0 or len(xe) == 0 else (xs.min(), xs.max(), xe.min(), xe.max()))
    ref = [p for p in prof if p]
    ec = np.mean([(p[2] + p[3]) / 2 for p in ref])
    for i, p in enumerate(prof):
        if p is None:
            prof[i] = prof[i - 1] if i and prof[i - 1] is not None else ref[0]
    P = gaussian_filter1d(np.array(prof, float), 3.5, axis=0, mode="nearest")
    prof = [tuple(r) for r in P]
    pts = []
    for i, p in enumerate(prof):
        xl, xr, yb, yf = p
        x0 = (xl + xr) / 2 - cx
        hw = (xr - xl) / 2
        d = (yf - yb) / 2
        ym = (yb + yf) / 2 - ec
        row = []
        for k in range(A):
            a = 2 * np.pi * k / A
            c, sn = np.cos(a), np.sin(a)
            ex = x0 + hw * np.sign(c) * abs(c) ** (2 / 2.6)
            ey = ym + d * np.sign(sn) * abs(sn) ** (2 / 2.6)
            row += [round(float(ex), 1), round(float(-(s0 + (s1 - s0) * i / (R - 1))), 1), round(float(ey), 1)]
        pts.append(row)
    out[b] = pts
json.dump(out, open(S + 'body3d.json', 'w'), separators=(',', ':'))
print({b: len(v) for b, v in out.items()})
