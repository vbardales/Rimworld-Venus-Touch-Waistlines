"""Clean strokes from a warped detail mask (Fable, 2026-11-06, round 2).
skeleton -> traced branches -> Douglas-Peucker -> Catmull-Rom -> drawn 4x supersampled with round joints;
compact blobs (buttons) -> rings at their centres.
"""
import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
from skimage.morphology import skeletonize


def _nbrs(p, pts):
    y, x = p
    return [(y + dy, x + dx) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if (dy or dx) and (y + dy, x + dx) in pts]


def trace(sk):
    """ordered polylines (x, y) through the skeleton pixels, split at junctions"""
    pts = set(zip(*np.where(sk)))
    deg = {p: len(_nbrs(p, pts)) for p in pts}
    junction = {p for p in pts if deg[p] >= 3}
    endpoints = [p for p in pts if deg[p] == 1]
    visited = set(); polys = []

    def walk(start, first):
        poly = [start, first]; visited.add(first)
        prev, cur = start, first
        while cur not in junction:
            nx = [q for q in _nbrs(cur, pts) if q != prev and q not in visited]
            if not nx:
                break
            nx.sort(key=lambda q: abs(q[0] - cur[0]) + abs(q[1] - cur[1]))
            prev, cur = cur, nx[0]
            visited.add(cur); poly.append(cur)
        return poly

    for s in endpoints + sorted(junction):
        visited.add(s)
        for q in _nbrs(s, pts):
            if q not in visited:
                polys.append(walk(s, q))
    for p in sorted(pts):                       # closed loops
        if p not in visited:
            visited.add(p)
            q = [q for q in _nbrs(p, pts) if q not in visited]
            if q:
                poly = walk(p, q[0]); poly.append(p); polys.append(poly)
    return [np.array([(x + 0.5, y + 0.5) for y, x in poly], dtype=np.float64) for poly in polys]


def simplify(P, eps):
    if len(P) < 3:
        return P
    a, b = P[0], P[-1]; ab = b - a; n = np.hypot(*ab)
    d = np.hypot(*(P - a).T) if n < 1e-9 else np.abs(ab[0] * (P[:, 1] - a[1]) - ab[1] * (P[:, 0] - a[0])) / n
    i = int(np.argmax(d))
    if d[i] > eps:
        return np.vstack([simplify(P[:i + 1], eps)[:-1], simplify(P[i:], eps)])
    return np.array([a, b])


def catmull(P, step=1.0):
    if len(P) < 3:
        return P
    Pe = np.vstack([P[0], P, P[-1]]); out = []
    for i in range(1, len(Pe) - 2):
        p0, p1, p2, p3 = Pe[i - 1], Pe[i], Pe[i + 1], Pe[i + 2]
        n = max(2, int(np.hypot(*(p2 - p1)) / step) + 1)
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(P[-1])
    return np.array(out)


def render(det, width=2.5, eps=1.8, min_len=8, button_max=22, ring_r=5.0, ring_w=2.0, ss=4, keep=None):
    """det: binary detail mask at the output size. Returns (soft stroke mask in [0,1], list of button centres)."""
    H, W = det.shape
    lab, n = ndi.label(det, structure=np.ones((3, 3)))
    buttons = []; linemask = det.copy()
    for i in range(1, n + 1):
        comp = lab == i
        ys, xs = np.where(comp)
        h, w = int(np.ptp(ys)) + 1, int(np.ptp(xs)) + 1
        area = len(ys)
        if h <= button_max and w <= button_max and 0.5 <= w / h <= 2.0 and area >= 12 and area / (h * w) >= 0.25:
            buttons.append((xs.mean() + 0.5, ys.mean() + 0.5)); linemask &= ~comp
    sk = skeletonize(linemask)
    polys = [p for p in trace(sk) if len(p) >= min_len and (keep is None or keep(p))]
    canvas = Image.new("L", (W * ss, H * ss), 0); dr = ImageDraw.Draw(canvas)
    lw = max(1, int(round(width * ss)))
    for P in polys:
        Q = catmull(simplify(P, eps), step=0.5) * ss
        seq = [tuple(q) for q in Q]
        if len(seq) >= 2:
            dr.line(seq, fill=255, width=lw, joint="curve")
            for q in (seq[0], seq[-1]):
                dr.ellipse([q[0] - lw / 2, q[1] - lw / 2, q[0] + lw / 2, q[1] + lw / 2], fill=255)
    for (cx, cy) in buttons:
        r = ring_r * ss; rw = max(1, int(round(ring_w * ss)))
        dr.ellipse([cx * ss - r, cy * ss - r, cx * ss + r, cy * ss + r], outline=255, width=rw)
    soft = np.asarray(canvas.resize((W, H), Image.BOX)).astype(np.float32) / 255.0
    return soft, buttons, len(polys)
