"""Garments through the relief map on the eight bodies (2026-11-08, 'puis ensuite, teste avec des vêtements'): the vanilla
garment, prepared as in B2 (black peeled by thickness), carried by the relief map (ease EASE px) in the body's height
mode (out/heightmode.json), onto the WDI body. No clip, no outline (B5, B6 are out). No point-warp comparison here (it
needs the underwear sprites and the artist's garments, absent from the cloud container).
One board per garment: row per body, the three facings; Art/work/captures/2026-11-08_garmentstudy-<Garment>.png
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python run_linux.py garmentstudy.py [garment=ShirtBasic,LabCoat] [Body ...]
"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import crack as c1, explain5b as e5, fullpass as fp, reliefmap as rm
from reliefstudy import BODIES

N = c1.N
fp.GROIN = False


def main():
    args = [a for a in sys.argv[1:] if "=" not in a]
    bodies = BODIES if (not args or args == ["all"]) else args
    garments = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("garment=")), "ShirtBasic,LabCoat").split(",")
    font = ImageFont.load_default(size=15)
    maps = {(b, f): rm.build(b, f, rm.EASE) for b in bodies for f in ("south", "east", "north")}
    for g in garments:
        rows = []
        for b in bodies:
            tiles = []
            for f in ("south", "east", "north"):
                Mp = maps[(b, f)]
                vb = c1.VANILLA_OF[b]
                Vg = c1.load(rf"{c1.CORE}\{g}_{vb.capitalize()}_{f}.png")
                Vb = c1.load(rf"{c1.VAN}\vanilla-{vb}-{f}.png")
                Gp = fp.prepared(Vg, Vb)
                t = e5.pil(Mp["imw"][f]); t.alpha_composite(e5.pil(e5.warp(Gp, Mp["U"], Mp["V"]))); t = e5.on_bg(t)
                ys, xs = np.nonzero(Mp["D"])
                box = (max(0, xs.min() - 12), max(0, ys.min() - 12), min(N, xs.max() + 12), min(N, ys.max() + 12))
                c = t.crop(box); c = c.resize((int(c.width * 1.5), int(c.height * 1.5)), Image.LANCZOS)
                ImageDraw.Draw(c).text((6, 4), f"{b} {f}", fill=(255, 255, 255), font=font)
                tiles.append(c)
            rows.append(tiles)
        W = max(sum(t.width + 8 for t in r_) for r_ in rows) + 20
        H = sum(max(t.height for t in r_) + 8 for r_ in rows) + 50
        im = Image.new("RGB", (W, H), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((10, 8), f"{g}: vanilla garment through the relief map (ease {rm.EASE} px, height mode per body), eight bodies; no clip, no outline. WDI bodies are stand-ins (wdi_from_study.py).",
                fill=(0, 0, 0), font=ImageFont.load_default(size=17))
        y = 40
        for r_ in rows:
            x = 10
            for t in r_:
                im.paste(t.convert("RGB"), (x, y)); x += t.width + 8
            y += max(t.height for t in r_) + 8
        out = rf"{c1.CAPT}\2026-11-08_garmentstudy-{g}.png"; im.save(out); print(out)


if __name__ == "__main__":
    main()
