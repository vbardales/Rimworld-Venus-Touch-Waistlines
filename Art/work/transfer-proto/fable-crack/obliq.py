"""Oblique (3/4) captures of one body: front-left, front-right, back-left, back-right.

uv run --with playwright --with pillow python obliq.py <tag> <Body> [query]
query: viewer shader/mesh params, e.g. "?sn=0". Writes captures/2026-11-10_obliq-<tag>-<Body>.png.
"""
import math
import pathlib
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
caps = here.parent.parent / "captures"
tag, body = sys.argv[1], sys.argv[2]
query = sys.argv[3] if len(sys.argv) > 3 else ""
W, H = 560, 760
ANG = [35, -35, 145, -145]   # degrees around the vertical axis, 0 = south camera, 180 = north
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": W, "height": H})
    pg.goto((caps / "2026-11-08_body3d.html").as_uri() + query)
    pg.wait_for_function("document.getElementById('b') && document.getElementById('b').options.length>0", timeout=60000)
    pg.add_style_tag(content="#ui,#note{display:none!important}")
    pg.evaluate(f"(()=>{{const s=document.getElementById('b');s.value='{body}';s.onchange();}})()")
    pg.wait_for_timeout(1500)
    pg.evaluate("document.querySelector('button[data-v=\"0\"]').click()")
    ims = []
    for a in ANG:
        r = math.radians(a)
        pg.evaluate(f"(()=>{{const d=__fit||1000;__cam.position.set(d*Math.sin({r}),0,d*Math.cos({r}));__ctl.target.set(0,0,0);__ctl.update()}})()")
        pg.wait_for_timeout(700)
        f = caps / "_tmp_obl.png"
        pg.screenshot(path=str(f))
        ims.append(Image.open(f).convert("RGB"))
        f.unlink()
    br.close()
row = Image.new("RGB", (W * 4, H), (244, 242, 238))
for i, im in enumerate(ims):
    row.paste(im, (i * W, 0))
row.save(caps / f"2026-11-10_obliq-{tag}-{body}.png")
print("ok")
