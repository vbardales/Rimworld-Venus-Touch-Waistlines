"""Rebuild the 3D viewer with the latest mesh export.

Run ``uv run python body3d_build.py`` after ``wdi3d_export.py`` (the wdi3d model:
mesh, crease maps, frame). ``body3d_build.py legacy`` puts the older
``relief_export2.py`` mesh (out/relief3d-shade5.json) back in the first mode.
The relief and simple comparison modes remain from the existing viewer.

When ``out/stack3d-mesh.json`` exists (stack3d_export.py: skeleton, muscles,
fat, skin), each of its bodies takes the place of the wdi3d body of the same
name; the wdi3d one stays in the list as ``<Body> (wdi3d)``. ``nostack`` skips it.
"""
import json
import pathlib
import sys
here = pathlib.Path(__file__).parent
out = here.parent.parent / "captures" / "2026-11-08_body3d.html"
cur = out.read_text(encoding="utf-8").splitlines()
data_line = next(line for line in cur if line.startswith("const DATA="))
data = json.loads(data_line[len("const DATA="):].rstrip(";"))
source = "relief3d-shade5.json" if "legacy" in sys.argv[1:] else "wdi3d-mesh.json"
shade = json.loads((here / "out" / source).read_text(encoding="utf-8"))
shade["A"] = 2 * shade.pop("U")
refs = {name: {"wdi": entry.get("wdi"), "frame": entry.get("frame")} for name, entry in shade["bodies"].items()}

# The simple and relief meshes use the same source coordinate system.  Give every one the original WDI pixels and its
# frame so the comparison overlay is available in all three model families, not only in the stack export.
for mode, collection in data.items():
    if mode == "shade" or not isinstance(collection, dict):
        continue
    bodies = collection.get("bodies")
    if not isinstance(bodies, dict):
        continue
    for name, entry in list(bodies.items()):
        ref = refs.get(name.split(" (")[0])
        if not ref or not ref["wdi"]:
            continue
        if isinstance(entry, list):
            bodies[name] = {"rows": entry, "legs": None, "lm": None, "frame": ref["frame"], "wdi": ref["wdi"]}
        elif isinstance(entry, dict):
            entry.setdefault("frame", ref["frame"])
            entry.setdefault("wdi", ref["wdi"])
stack_path = here / "out" / "stack3d-mesh.json"
if stack_path.exists() and "nostack" not in sys.argv[1:] and "legacy" not in sys.argv[1:]:
    stack = json.loads(stack_path.read_text(encoding="utf-8"))["bodies"]
    bodies = {}
    for name, entry in shade["bodies"].items():
        if name in stack:
            bodies[name] = stack[name]
            bodies[f"{name} (wdi3d)"] = entry
        else:
            bodies[name] = entry
    shade["bodies"] = bodies
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
