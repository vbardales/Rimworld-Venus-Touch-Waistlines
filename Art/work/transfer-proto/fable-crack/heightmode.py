"""Height mode per body (2026-11-08): from anchortest.py, the least weak of {anchors as they are, navel dropped, sex
dropped, anchors softened by half} over the three facings, never 'top and bottom only' (her landmarks would be gone).
Written to out/heightmode.json, read by reliefmap.mode_of. Board per body, row per facing: grid through the map as it was
| its weak map | grid through the chosen mode | its weak map.
Board: Art/work/captures/2026-11-08_heightmode-<Body>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python run_linux.py heightmode.py [Body ...|all]
"""
import sys, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
import crack as c1, explain5b as e5, reliefmap as rm, fullpass as fp
from gridboard import grid_garment
from reliefstudy import area_ratio, BODIES, WEAK, heat

N = c1.N
fp.GROIN = False
CHOICES = {"base": {"drop": "", "soft": 0.0}, "-navel": {"drop": "navel", "soft": 0.0}, "-sex": {"drop": "sex", "soft": 0.0},
           "soft0.5": {"drop": "", "soft": 0.5}}


def choose():
    with open(rf"{c1.OUT}\anchortest.json", encoding="utf-8") as fh:
        T = json.load(fh)
    modes = {}
    for b in BODIES:
        tot = {k: sum(T[f"{b}/{f}"][k][0] for f in ("south", "east", "north")) for k in CHOICES}
        best = min(tot, key=tot.get)
        # the anchors as they are win ties and anything within 3 points per facing of them
        if tot["base"] - tot[best] < 0.09:
            best = "base"
        modes[b] = dict(CHOICES[best], name=best, weak={k: round(v / 3, 3) for k, v in tot.items()})
    with open(rf"{c1.OUT}\heightmode.json", "w", encoding="utf-8") as fh:
        json.dump(modes, fh, indent=1)
    return modes


def run(body, f, mode):
    rm.MODES = {body: mode}; rm.SOFT = 0.0
    R = rm.build(body, f)
    r = area_ratio(R["Xs"], R["Ys"], R["mw"])
    inside = ndi.binary_erosion(R["mw"], iterations=2)
    med = float(np.nanmedian(r[inside]))
    return R, r, med, float(np.mean(np.abs(r[inside] - med) > WEAK))


def board(body, modes, font):
    rows = []
    for f in ("south", "east", "north"):
        Vb = c1.load(rf"{c1.VAN}\vanilla-{c1.VANILLA_OF[body]}-{f}.png"); G = grid_garment(Vb)
        tiles = []
        for name, mode in (("base", CHOICES["base"]), (modes[body]["name"], modes[body])):
            R, r, med, wk = run(body, f, mode)
            t = e5.pil(R["imw"][f]); t.alpha_composite(e5.pil(e5.warp(G, R["U"], R["V"]))); t = e5.on_bg(t)
            h = heat(r, R["mw"], med)
            ImageDraw.Draw(h).text((6, 6), f"{name}: weak {100 * wk:.0f}%, median x{2 ** med:.2f}", fill=(0, 0, 0), font=font)
            tiles += [t, h]
        ys, xs = np.nonzero(R["mw"])
        box = (max(0, xs.min() - 16), max(0, ys.min() - 16), min(N, xs.max() + 16), min(N, ys.max() + 16))
        rows.append((f, [t.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2), Image.LANCZOS) for t in tiles]))
    W = max(sum(t.width + 10 for t in ts) for _, ts in rows) + 100
    H = sum(ts[0].height + 30 for _, ts in rows) + 50
    im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
    m = modes[body]
    dr.text((10, 8), f"{body}: height mode '{m['name']}' (drop '{m['drop']}', soft {m['soft']}); weak share per mode, mean of the facings: "
            + ", ".join(f"{k} {100 * v:.0f}%" for k, v in m["weak"].items()) + ". Grid and weak map: as it was | chosen mode",
            fill=(0, 0, 0), font=ImageFont.load_default(size=17))
    y = 40
    for f, ts in rows:
        dr.text((10, y + 4), f, fill=(0, 0, 0), font=font); x = 90
        for t in ts:
            im.paste(t.convert("RGB"), (x, y)); x += t.width + 10
        y += ts[0].height + 30
    out = rf"{c1.CAPT}\2026-11-08_heightmode-{body}.png"; im.save(out); print(out)


def main():
    args = [a for a in sys.argv[1:] if "=" not in a]
    bodies = BODIES if (not args or args == ["all"]) else args
    modes = choose()
    for b in BODIES:
        print(f"{b:11s} -> {modes[b]['name']:8s}", {k: f"{100 * v:.0f}%" for k, v in modes[b]["weak"].items()})
    font = ImageFont.load_default(size=15)
    for b in bodies:
        board(b, modes, font)
    rm.MODES = None


if __name__ == "__main__":
    main()
