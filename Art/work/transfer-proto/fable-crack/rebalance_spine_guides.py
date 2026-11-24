"""Rebalance exported WDI spine guides while preserving their profile curves.

Each coloured zone receives a stable vertical share of the guide: cervical 23%,
thoracic 40%, lumbar 24%, sacrum/coccyx 13%.  X coordinates stay untouched;
each Bézier control's relative Y position within its own zone is retained.
"""
import json
from pathlib import Path

SHARES = (0.23, 0.40, 0.24, 0.13)
ANCHORS = ("green", "pink", "blueUpper", "blueLower", "deepBlue")
CONTROLS = ("inflectGreenPink", "inflectPinkBlue", "inflectBlueBlue", "inflectBlueDeep")
def main():
    root = Path(__file__).resolve().parents[2] / "landmark-editor-site" / "dist" / "assets"
    source = root / "reperes-anatomiquesColonne.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    for key, guide in payload["_spineGuide"].items():
        old = json.loads(json.dumps(guide))
        old_points = [old[name] for name in ANCHORS]
        top, bottom = old_points[0]["y"], old_points[-1]["y"]
        total = bottom - top
        if total <= 0:
            raise ValueError(f"{key}: spine guide must run downwards")
        new_y = [top]
        for share in SHARES:
            new_y.append(new_y[-1] + total * share)
        for index, name in enumerate(ANCHORS):
            guide[name]["y"] = new_y[index]
        for index, name in enumerate(CONTROLS):
            old_start, old_end = old_points[index]["y"], old_points[index + 1]["y"]
            ratio = (old[name]["y"] - old_start) / (old_end - old_start)
            guide[name]["y"] = new_y[index] + ratio * (new_y[index + 1] - new_y[index])
    source.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"rebalanced {len(payload['_spineGuide'])} guides in {source}")


if __name__ == "__main__":
    main()
