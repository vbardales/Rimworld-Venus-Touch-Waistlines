"""Measure how the WDI drawn garments relate to the WDI bodies (2026-11-06, Fable).
Run: uv run --with numpy --with pillow --with scipy python analyse.py
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

WS = r"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike"
CORE = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17"
VAN = r"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\vanilla"

def load(path, size=None):
    im = Image.open(path).convert("RGBA")
    if size and im.size != (size, size):
        print(f"   (native {im.size[0]} px: {path.split(chr(92))[-1]})")
        im = im.resize((size, size), Image.BILINEAR)
    return np.asarray(im).astype(np.float32) / 255.0

def bbox(m):
    ys, xs = np.where(m)
    return (xs.min(), ys.min(), xs.max(), ys.max()) if len(xs) else None

def iou(a, b):
    return (a & b).sum() / max(1, (a | b).sum())

def stroke_width(img, alpha, lum, row_frac=0.5):
    """dark run from the left alpha edge inward on a row at row_frac of the alpha bbox height"""
    b = bbox(alpha)
    y = int(b[1] + (b[3] - b[1]) * row_frac)
    row_a = alpha[y]; row_l = lum[y]
    xs = np.where(row_a)[0]
    if len(xs) == 0: return -1
    x = xs[0]; n = 0
    while x < img.shape[1] and row_a[x] and row_l[x] < 0.35:
        n += 1; x += 1
    return n

def thin_line_width(lum, alpha, outline):
    """median width of dark runs that are inside the garment but not in the outline"""
    inner = alpha & ~outline
    dark = inner & (lum < 0.5)
    runs = []
    for y in range(0, lum.shape[0], 2):
        r = dark[y]; x = 0
        while x < len(r):
            if r[x]:
                n = 0
                while x < len(r) and r[x]: n += 1; x += 1
                runs.append(n)
            else: x += 1
    runs = [r for r in runs if r <= 12]
    return (np.median(runs) if runs else -1), len(runs)

for body, vbody in [("Thin_Female", "thin"), ("Fat_Female", "fat"), ("Hulk_Female", "hulk")]:
    for facing in ["south", "east", "north"]:
        B = load(rf"{WS}\Bodies\Naked_{body}_{facing}.png")
        ba = B[..., 3] > 0.5
        bl = B[..., :3].mean(axis=2)
        print(f"== {body} {facing}: body bbox {bbox(ba)} area {ba.sum()}")
        for g in ["ShirtBasic", "ShirtButton"]:
            G = load(rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png", 512)
            ga = G[..., 3] > 0.5
            gl = G[..., :3].mean(axis=2)
            # outline = dark pixels within 14 px of the alpha edge
            edge_dist = ndi.distance_transform_edt(ga)
            outline = ga & (gl < 0.35) & (edge_dist <= 14)
            sw = stroke_width(G, ga, gl)
            tw, tn = thin_line_width(gl, ga, outline)
            # how much of the garment lies outside the body, and vice versa (body minus garment = neck hole + uncovered)
            out_body = (ga & ~ba).sum() / ga.sum()
            body_uncovered = (ba & ~ga).sum() / ba.sum()
            # body dilated by k so the garment fits inside
            fits = []
            for k in [0, 2, 4, 6, 8]:
                bd = ndi.binary_dilation(ba, iterations=k) if k else ba
                fits.append(f"{k}:{(ga & ~bd).sum() / ga.sum():.3f}")
            # luminance stats inside, away from edges
            inner = ga & (edge_dist > 16)
            # darkest/lightest colour of the outline
            oc = G[outline][..., :3].mean(axis=0) if outline.sum() else None
            # inner luminance relation to body luminance (where both present)
            both = inner & ba & (bl > 0.35)
            corr = np.corrcoef(gl[both], bl[both])[0, 1] if both.sum() > 100 else 0
            print(f"  {g}: bbox {bbox(ga)} area {ga.sum()} IoU(body) {iou(ga, ba):.3f} garment-outside-body {out_body:.3f} body-uncovered {body_uncovered:.3f} outside-dilated {' '.join(fits)}")
            print(f"     outline width {sw} px, outline colour {np.round(oc*255).astype(int) if oc is not None else None}, thin lines median {tw} px (n={tn}), inner lum mean {gl[inner].mean():.3f} min {np.percentile(gl[inner],1):.3f}, corr(garment lum, body lum) {corr:.3f}")
        # body outline width
        bedge = ndi.distance_transform_edt(ba)
        print(f"  body outline width {stroke_width(B, ba, bl)} px, body inner lum mean {bl[ba & (bedge > 16)].mean():.3f}")
    # vanilla
    for facing in ["south", "east", "north"]:
        V = load(rf"{VAN}\vanilla-{vbody}-{facing}.png")
        va = V[..., 3] > 0.5
        vl = V[..., :3].mean(axis=2)
        print(f"   vanilla {vbody} {facing}: body bbox {bbox(va)} outline {stroke_width(V, va, vl)} px")
        for g in ["ShirtBasic", "ShirtButton"]:
            G = load(rf"{CORE}\{g}_{vbody.capitalize()}_{facing}.png")
            ga = G[..., 3] > 0.5
            gl = G[..., :3].mean(axis=2)
            print(f"     {g}: bbox {bbox(ga)} IoU(body) {iou(ga, va):.3f} outside-body {(ga & ~va).sum()/ga.sum():.3f} body-uncovered {(va & ~ga).sum()/va.sum():.3f} outline {stroke_width(G, ga, gl)} px")
