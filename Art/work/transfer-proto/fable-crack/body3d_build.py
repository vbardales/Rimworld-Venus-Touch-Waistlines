"""Rebuild the 3D viewer Art/work/captures/2026-11-08_body3d.html from body3d_template.html (the viewer code) and the DATA line
already inside the current viewer (shade / relief / simple height datasets). Run: uv run python body3d_build.py
To change the data, re-export with relief_export2.py (out/relief3d-shade5.json) and replace the "shade" key of DATA by hand."""
import pathlib
here = pathlib.Path(__file__).parent
out = here.parent.parent / "captures" / "2026-11-08_body3d.html"
cur = out.read_text(encoding="utf-8").split("\n")
data = [l for l in cur if l.startswith("const DATA=")][0][len("const DATA="):].rstrip(";")
tpl = (here / "body3d_template.html").read_text(encoding="utf-8")
out.write_text(tpl.replace("__DATA__", data), encoding="utf-8")
print("ok", out)
