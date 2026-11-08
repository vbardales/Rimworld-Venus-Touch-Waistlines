"""Step-by-step board of round 8 (2026-11-07, Virginie: 'une version avec les captures étape par étape').
One row per case, one column per stage of crack8.rebuild6 (captured through crack8.STEPS), then the WDI artist's
drawing when he made one. Board: Art/work/captures/2026-11-07_round8-steps.png

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python steps.py
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont
import crack as c1, neck, crack2, crack4, crack5, crack8

N = c1.N; CAPT = c1.CAPT; WS = c1.WS
CASES = [("Fat_Female", "south", "ShirtButton"), ("Fat_Female", "east", "ShirtButton"), ("Female", "north", "ShirtButton"),
         ("Fat_Female", "south", "CorsetRoyal"), ("Hulk_Female", "south", "Jacket"), ("Fat_Female", "south", "FlakVest")]


def main():
    nocut = "nocut" in sys.argv[1:]
    crack8.CUT_CLOTH = not nocut
    peel = "peel" in sys.argv[1:]
    crack8.PEEL = peel
    nopull = "nopull" in sys.argv[1:]
    crack8.EDGE_PULL = not nopull
    pv, pw = crack2.measure_profiles()
    A, B, ALLP, maps = crack2.neck_models(pv, pw)
    loops = crack4.drawn_loops(); table, _ = crack4.load_table(loops)
    rows = []
    for body, facing, g in CASES:
        drawn = body in crack2.DRAWN; donor = None if drawn else crack2.DONOR[body]
        tp = crack4.type_params(loops, exclude=body if drawn else None)
        kind = crack5.classify_vanilla(body, g)
        U, V, shade, body_a, cal = crack2.prep(body, facing, donor)
        fw = neck.frame(body, facing, 1, 4)
        th = crack8.target_opening(body, facing, g, kind, table, tp, B, ALLP, fw, body_a, drawn)
        crack8.STEPS = []
        crack8.rebuild6(body, facing, g, cal, shade, body_a, th, ref_body=body if drawn else donor)
        steps = crack8.STEPS; crack8.STEPS = None
        p = rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png"
        steps.append(("WDI artist's drawing" if os.path.exists(p) else "no drawing by the artist", c1.load(p, N) if os.path.exists(p) else None))
        rows.append((f"{g}\n{body}\n{facing}", steps))
        print("case", body, facing, g, len(steps))
    ncol = max(len(s) for _, s in rows)
    T = 250; pad = 6; left = 150; top = 50; head = 34
    font = ImageFont.load_default(size=13); fontb = ImageFont.load_default(size=18)
    im = Image.new("RGB", (left + ncol * (T + pad), top + len(rows) * (T + head + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
    dr.text((8, 8), "Round 8, step by step" + (", step 4 peels only the black edges" if peel else (", step 4 cuts NOTHING (whole garment kept)" if nocut else "")) + (", step 5 = your points only (no edge pulls)" if nopull else "") + ". Green = transparent. Read each row left to right; the last cell is the target.", fill=(0, 0, 0), font=fontb)
    for r, (label, steps) in enumerate(rows):
        y = top + r * (T + head + pad)
        dr.text((8, y + head), label, fill=(0, 0, 0), font=fontb)
        for j, (title, img) in enumerate(steps):
            x = left + j * (T + pad)
            words, line, lines = title.split(), "", []
            for w in words:
                if len(line) + len(w) > 34:
                    lines.append(line); line = w
                else:
                    line = (line + " " + w).strip()
            lines.append(line)
            dr.text((x, y), "\n".join(lines[:2]), fill=(0, 0, 0), font=font)
            if img is None:
                continue
            back = Image.new("RGBA", (N, N), (78, 98, 78, 255)); back.alpha_composite(c1.to_pil(img))
            im.paste(back.resize((T, T), Image.LANCZOS).convert("RGB"), (x, y + head))
    out = rf"{CAPT}\2026-11-07_round8-steps{'-peel' if peel else ('-nocut' if nocut else '')}{'-nopull' if nopull else ''}.png"; im.save(out); print("board", out)


if __name__ == "__main__":
    main()
