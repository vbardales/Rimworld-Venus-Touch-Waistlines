"""Rebuild the 3D viewer with the latest shaded mesh export.

Run ``uv run python body3d_build.py`` after ``relief_export2.py``. The relief
and simple comparison modes remain from the existing viewer; the shade mode is
replaced automatically so the browser cannot silently show stale data.
"""
import json
import pathlib
here = pathlib.Path(__file__).parent
out = here.parent.parent / "captures" / "2026-11-08_body3d.html"
cur = out.read_text(encoding="utf-8").splitlines()
data_line = next(line for line in cur if line.startswith("const DATA="))
data = json.loads(data_line[len("const DATA="):].rstrip(";"))
shade = json.loads((here / "out" / "relief3d-shade5.json").read_text(encoding="utf-8"))
shade["A"] = 2 * shade.pop("U")
data["shade"] = shade
tpl = (here / "body3d_template.html").read_text(encoding="utf-8")
marker = "const DATA=globalThis.__DATA__;"
if marker not in tpl:
    raise ValueError(f"viewer template marker missing: {marker}")
out.write_text(
    tpl.replace(marker, f"const DATA={json.dumps(data, separators=(',', ':'))};", 1),
    encoding="utf-8",
)
print("ok", out)
