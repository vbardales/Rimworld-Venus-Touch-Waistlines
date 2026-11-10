"""Headless capture of the 3D viewer: south, east, north for every body.

uv run --with playwright --with pillow python viewcap.py [tag] [Body ...]
Writes captures/2026-11-10_viewer-<tag>-<Body>.png (three views side by side) and
an overview. Needs `playwright install chromium` once.
"""
import pathlib
import sys
from PIL import Image
from playwright.sync_api import sync_playwright

here = pathlib.Path(__file__).parent
caps = here.parent.parent / "captures"
html = caps / "2026-11-08_body3d.html"
args = sys.argv[1:]
tag = args[0] if args else "t"
only = args[1:]
BODIES = ["Male", "Female", "Thin", "Thin_Female", "Fat", "Fat_Female", "Hulk", "Hulk_Female"]
W, H = 560, 760
rows = []
with sync_playwright() as p:
    br = p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
    pg = br.new_page(viewport={"width": W, "height": H})
    msgs = []
    pg.on("console", lambda m: msgs.append(m.text) if m.type in ("error", "warning") else None)
    pg.goto(html.as_uri())
    pg.wait_for_function("document.getElementById('b') && document.getElementById('b').options.length>0", timeout=60000)
    pg.add_style_tag(content="#ui,#note{display:none!important}")
    for b in (only or BODIES):
        pg.evaluate(f"(()=>{{const s=document.getElementById('b');s.value='{b}';s.onchange();}})()")
        pg.wait_for_timeout(1500)
        ims = []
        for v in range(3):
            pg.evaluate(f"document.querySelector('button[data-v=\"{v}\"]').click()")
            pg.wait_for_timeout(700)
            f = caps / f"_tmp_{b}_{v}.png"
            pg.screenshot(path=str(f))
            ims.append(Image.open(f).convert("RGB"))
            f.unlink()
        row = Image.new("RGB", (W * 3, H), (244, 242, 238))
        for i, im in enumerate(ims):
            row.paste(im, (i * W, 0))
        row.save(caps / f"2026-11-10_viewer-{tag}-{b}.png")
        rows.append(row)
        print("done", b)
    print("console:", msgs[:10])
    br.close()
if len(rows) > 1:
    s = 0.5
    ov = Image.new("RGB", (int(W * 3 * s) * 2, int(H * s) * 4), (244, 242, 238))
    for i, r in enumerate(rows):
        r = r.resize((int(W * 3 * s), int(H * s)))
        ov.paste(r, ((i % 2) * r.width, (i // 2) * r.height))
    ov.save(caps / f"2026-11-10_viewer-{tag}-overview.png")
