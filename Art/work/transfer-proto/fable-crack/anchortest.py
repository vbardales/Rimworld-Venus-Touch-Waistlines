"""Which height anchor makes the bands (reliefstudy.py, 2026-11-08): on seven bodies the weak zones are whole bands between
two consecutive height anchors, uniformly squeezed or stretched; a point added inside such a band changes nothing. This
test measures the weak share of the map (|log2 area ratio - median| > 0.58, over the body) for:
  base      : the anchors as they are (reliefmap.KEEP)
  -<name>   : one anchor dropped at a time
  soft 0.5  : the anchors' scale blended half with the uniform top-to-bottom scale (reliefmap.SOFT)
  soft 1.0  : top and bottom only
Output: out/anchortest.json and the table printed.
Run: uv run --with numpy --with pillow --with scipy --with scikit-image python run_linux.py anchortest.py [Body ...|all]
"""
import sys, json
import numpy as np
from scipy import ndimage as ndi
import crack as c1, reliefmap as rm, fullpass as fp
from reliefstudy import area_ratio, BODIES, WEAK

fp.GROIN = False
rm.MODES = {}; rm.SOFT_AUTO = False      # the modes under test are set here, not read from out/heightmode.json
DROPS = ["neck", "armpit", "navel", "sex"]


def weak_share(body, f):
    R = rm.build(body, f)
    r = area_ratio(R["Xs"], R["Ys"], R["mw"])
    inside = ndi.binary_erosion(R["mw"], iterations=2)
    med = float(np.nanmedian(r[inside]))
    return float(np.mean(np.abs(r[inside] - med) > WEAK)), float(2 ** med)


def main():
    args = [a for a in sys.argv[1:] if "=" not in a]
    bodies = BODIES if (not args or args == ["all"]) else args
    keep0 = set(rm.KEEP); shared0 = tuple(rm.SHARED)
    out = {}
    print("body        facing  base   " + "  ".join(f"-{d:6s}" for d in DROPS) + "  soft.5  soft1")
    for b in bodies:
        for f in ("south", "east", "north"):
            row = {}
            rm.KEEP = set(keep0); rm.SHARED = shared0; rm.SOFT = 0.0
            row["base"] = weak_share(b, f)
            for d in DROPS:
                rm.KEEP = {n for n in keep0 if d not in n}; rm.SHARED = tuple(n for n in shared0 if d not in n)
                row["-" + d] = weak_share(b, f)
            rm.KEEP = set(keep0); rm.SHARED = shared0
            rm.SOFT = 0.5; row["soft0.5"] = weak_share(b, f)
            rm.SOFT = 1.0; row["soft1"] = weak_share(b, f)
            rm.SOFT = 0.0
            out[f"{b}/{f}"] = row
            print(f"{b:11s} {f:7s} {100 * row['base'][0]:4.0f}%  " + "  ".join(f"{100 * row['-' + d][0]:5.0f}% " for d in DROPS)
                  + f"  {100 * row['soft0.5'][0]:4.0f}%  {100 * row['soft1'][0]:4.0f}%")
    with open(rf"{c1.OUT}\anchortest.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)


if __name__ == "__main__":
    main()
