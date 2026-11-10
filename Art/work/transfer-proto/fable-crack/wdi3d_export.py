"""Mesh and maps of the wdi3d model for the 3D viewer (2026-11-10).

Reads the fitted fields of wdi3d.py (out/wdi3d-<Body>.npz) and writes out/wdi3d-mesh.json in the
format of relief_export2.py (same rings, legs, landmark rows, cage), plus per body:
  - the mesh is built from the crease-free volumes closed(field) of the south and north views;
  - "tex": three 512 px maps (south, north, east), colour = areola albedo x (1 - ink), ink being the
    crease depth under the rim of the fitted field (the same quantity the wdi3d shader inks);
  - "frame": what the viewer needs to project a mesh point back into each sprite frame.
The creases are 2 to 14 px wide and the mesh has one vertex every 4 px across, so they are carried
as maps, not as geometry.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python wdi3d_export.py [Body ...]
then: uv run python body3d_build.py
"""
import base64
import io
import json
import os
import pathlib
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

import relief_export2 as rx
import wdi3d as w

HERE = pathlib.Path(__file__).parent
N = w.N


def data_uri(rgb):
    buf = io.BytesIO()
    Image.fromarray(np.clip(255 * rgb + 0.5, 0, 255).astype(np.uint8)).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def ink_map(h, img, m):
    """Albedo x (1 - ink) of one view; white outside the creases and the areolae."""
    ink = np.clip((w.closed(h) - h) * m / w.GROOVE, 0, 1)
    albedo = np.ones((N, N, 3))
    yy, xx = np.mgrid[0:N, 0:N]
    for (x, y, r, col) in w.areolae(img, m):
        a = np.clip(r + 0.5 - np.hypot(xx - x, yy - y), 0, 1)[..., None]
        albedo = albedo * (1 - a) + col * a
    return albedo * (1 - ink[..., None])


GATE_LUM = 0.93   # sprite luminance under which the artist painted a grey (or ink)


def grey_gate(img, m):
    """0..1 where the sprite has grey or ink, soft edge: the viewer lets the mesh light grey the skin only there.

    The mesh keeps the profile steps (under-breast shelf, buttock fold) as full-width facets; the drawing
    greys only a wedge of them. Extent comes from the drawing, tone and slope from the mesh.
    """
    g = ((w.c1.lum(img) < GATE_LUM) & (m > 0)).astype(float)
    g = ndi.maximum_filter(g, size=9)
    return np.clip(1.6 * ndi.gaussian_filter(g, 4.0), 0, 1)


BAKE_MAX = 0.6     # loss range of the baked tone map (the shader caps the loss there too)


def baked_loss(h, m):
    """Tone lost by the capture of wdi3d.py (top light on the crease-free volumes), 0..1 = 0..BAKE_MAX.

    At the three sprite views the viewer shows exactly this tone, so it equals the 2D capture; turned away from
    a view, it falls back to the lit mesh.
    """
    return np.clip((1.0 - w.tone_of_slope(w.closed(h))) * m / BAKE_MAX, 0, 1)


def gray_uri(g):
    buf = io.BytesIO()
    Image.fromarray(np.clip(255 * g + 0.5, 0, 255).astype(np.uint8)).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


HOLLOW = float(os.environ.get("HOLLOW", 18.0))        # px of depth of the broad hollows (0 = none)
GLUTE = float(os.environ.get("GLUTE", 22.0))         # px of extra cleft depth between the buttocks
GLUTE_CURL = float(os.environ.get("GLUTE_CURL", 24.0))   # px the lower edge of the lobes curls under
MID_SIGMA = float(os.environ.get("MID_SIGMA", 0.10))   # median valley half-width, fraction of the row width
MIDLINE = float(os.environ.get("MIDLINE", 36.0))     # px of depth of the median valley
HOLLOW_SIGMA = float(os.environ.get("HOLLOW_SIGMA", 9.0))


def hollowed(h, img, m, width, back=False):
    """Crease-free volume with broad soft hollows along the artist's creases (sternum, ab grooves, spine, scapulae).

    The creases are thin strokes; the hollow is their blur, scaled by the local height so it dies at the silhouette.
    The 3/4 views then have a valley where the drawing has a line; the three sprite views keep the baked tone.
    """
    L = w.wdi_lines(img, m, width)
    b = ndi.gaussian_filter(L, HOLLOW_SIGMA)
    b = np.clip(b / max(float(np.percentile(b[m > 0], 99)), 1e-6), 0, 1)
    hc = w.closed(h)
    rel = np.clip(hc / max(float(hc.max()), 1e-6) * 2.0, 0, 1)
    ys, xs = np.nonzero(m)
    y0, y1 = ys.min(), ys.max()
    yy, xx = np.mgrid[0:N, 0:N]
    mid = np.zeros((N, N))
    for y in range(y0, y1 + 1):                       # median valley: sternum and abdomen (south), spine (north)
        r = np.nonzero(m[y])[0]
        if len(r) < 8:
            continue
        cx, s = 0.5 * (r[0] + r[-1]), max(MID_SIGMA * (r[-1] - r[0]), 3.0)
        mid[y] = np.exp(-0.5 * ((np.arange(N) - cx) / s) ** 2)
    t = (yy - y0) / max(y1 - y0, 1)                   # 0 top .. 1 bottom of the sprite: taper in at the shoulders, out at the pelvis
    mid *= np.clip((t - 0.10) / 0.12, 0, 1) * (np.clip((0.80 - t) / 0.12, 0, 1) if not back else 1.0)
    glute = np.zeros((N, N))
    if back:                                            # buttocks: deeper cleft in the lower rows, lower edge of each lobe curls under (sub-gluteal fold)
        glute = GLUTE * mid * np.clip((t - 0.62) / 0.12, 0, 1) + GLUTE_CURL * np.clip((t - 0.90) / 0.10, 0, 1) ** 2
    return np.maximum(hc - HOLLOW * b * rel - MIDLINE * mid * rel - glute * rel, 0.0) * m


def one(body):
    z = np.load(HERE / "out" / f"wdi3d-{body}.npz")
    imgs, M, _ = w.load(body)
    wd = {f: w.outline_width(imgs[f], M[f]) for f in imgs}
    fields = {"south": hollowed(z["south"], imgs["south"], M["south"], wd["south"]), "north": hollowed(z["north"], imgs["north"], M["north"], wd["north"], back=True), "zc": z["zc"]}
    e = rx.one(body, fields)
    e["tex"] = {f[0]: data_uri(ink_map(z[f], imgs[f], M[f])) for f in ("south", "north", "east")}
    e["bake"] = {f[0]: gray_uri(baked_loss(z[f], M[f])) for f in ("south", "north", "east")}
    e["gate"] = {f[0]: gray_uri(grey_gate(imgs[f], M[f])) for f in ("south", "north", "east")}
    e["outline"] = round(float(np.mean([w.outline_width(imgs[f], M[f]) for f in imgs])), 1)
    return e


def main():
    names = [a for a in sys.argv[1:] if a in w.BODIES] or w.BODIES
    out = {}
    for b in names:
        out[b] = one(b)
        print(b, "legs", None if out[b]["legs"] is None else len(out[b]["legs"]["L"]), "frame", out[b]["frame"], flush=True)
    (HERE / "out" / "wdi3d-mesh.json").write_text(json.dumps({"R": rx.R, "U": rx.U, "bodies": out}, separators=(",", ":")), encoding="utf-8")
    print("ok")


if __name__ == "__main__":
    main()
