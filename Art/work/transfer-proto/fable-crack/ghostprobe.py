"""Probe of the ghost carriage per body (2026-11-17): width scale the chain gives the head row and the arm row, the
armpit landmark, and the widest trunk half width below the armpit. Read only; prints one line per body.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python ghostprobe.py [h] [Body ...]
"""
import sys

import numpy as np

import stack3d as s
import stack3d_export as e
import wdi3d as w


def main():
    args = sys.argv[1:]
    h = float(args[0]) if args and args[0] not in s.TYPES else 2.0
    names = [a for a in args if a in s.TYPES] or list(w.BODIES)
    lm_m = s.MALE["lm"]
    lo, hi = lm_m[0] + 31.0, lm_m[4] - 27.0
    for b in names:
        K = s.make(b, h)
        T, steps = K["T"], K["steps"]
        P = T.P["south"]
        one = lambda r: float(s.chain_forward(steps, np.array([10.0]), np.array([float(r)]), np.array([240.0]), (lo, hi))[0][0] / 10.0)
        ax, ar = P["armpit L"]
        apx = abs(ax - T.cxs)
        rows = (T.rows >= ar) & (T.rows <= P["crotch point"][1])
        hwmax = float(T.hw[rows].max()); rmax = float(T.rows[rows][np.argmax(T.hw[rows])])
        print(f"{b:12s} sx head(215) {one(215):.3f} arm({e.ARM_ROW:.0f}) {one(e.ARM_ROW):.3f} | armpit x {apx:.1f} row {ar:.1f} | "
              f"trunk hw max {hwmax:.1f} at {rmax:.0f} | top {T.s0} neck hw {float(T.hw[2]):.1f}", flush=True)
        J = [float(a[0]) for a in s.chain_forward(steps, *(np.array([c]) for c in e.JOINT), (lo, hi))]
        print(f"{'':12s} joint x {J[0]:.1f} row {J[1]:.1f} | abduction {e.arm_theta(J, T):.1f} deg", flush=True)


if __name__ == "__main__":
    main()
