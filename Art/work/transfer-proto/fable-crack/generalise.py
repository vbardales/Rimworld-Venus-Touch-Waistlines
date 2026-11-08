"""Generalisation test of round 8 (2026-11-07): the round 8 pipeline run UNCHANGED on garments it was never tuned on.
No parameter is adjusted per garment. Outputs out/g8_<garment>_<body>_<facing>.png, out/scores_g8.json and one board per
facing, Art/work/captures/2026-11-07_generalise-<facing>.png: vanilla x4 | round 8 | the WDI artist's drawing when he made one.

Run: uv run --with numpy --with pillow --with scipy --with scikit-image python generalise.py CorsetRoyal,TribalA,Jacket,FlakVest
"""
import os, sys, json
from PIL import Image, ImageDraw, ImageFont
import crack as c1, neck, crack2, crack4, crack5, crack8

N = c1.N; OUT = c1.OUT; CAPT = c1.CAPT; WS = c1.WS; CORE = c1.CORE
GARMENTS = sys.argv[1].split(",")
BODIES = crack5.ALL_BODIES; DRAWN = crack2.DRAWN; FACINGS = crack2.FACINGS


def artist(g, body, facing):
    p = rf"{WS}\Apparel\{g}\{g}_{body}_{facing}.png"
    return c1.load(p, N) if os.path.exists(p) else None


def main():
    pv, pw = crack2.measure_profiles()
    A, B, ALLP, maps = crack2.neck_models(pv, pw)
    loops = crack4.drawn_loops(); table, _ = crack4.load_table(loops)
    results, tiles, errors = {}, {}, {}
    for body in BODIES:
        drawn = body in DRAWN; donor = None if drawn else crack2.DONOR[body]
        tp = crack4.type_params(loops, exclude=body if drawn else None)
        kinds = {}
        for g in GARMENTS:
            try:
                kinds[g] = crack5.classify_vanilla(body, g)
            except Exception as e:
                kinds[g] = None; errors[f"{body}_{g}_classify"] = repr(e)[:200]
        for facing in FACINGS:
            U, V, shade, body_a, cal = crack2.prep(body, facing, donor)
            fw = neck.frame(body, facing, 1, 4)
            for g in GARMENTS:
                key = f"{body}_{facing}_{g}"
                try:
                    th = crack8.target_opening(body, facing, g, kinds[g], table, tp, B, ALLP, fw, body_a, drawn)
                    out, info = crack8.rebuild6(body, facing, g, cal, shade, body_a, th, ref_body=body if drawn else donor)
                except Exception as e:
                    errors[key] = repr(e)[:200]; print("FAIL", key, errors[key]); continue
                c1.to_pil(out).save(rf"{OUT}\g8_{g}_{body}_{facing}.png")
                tiles[(body, facing, g)] = out
                ref = artist(g, body, facing)
                rec = {"kind": kinds[g], **{k: v for k, v in info.items() if isinstance(v, (int, float, str, bool))}}
                if ref is not None:
                    tiles[(body, facing, g, "wdi")] = ref
                    iou, edge, mae = c1.score(out, ref)
                    rec.update(iou=round(float(iou), 3), edge_px=round(float(edge), 2), lum_mae=round(float(mae), 3))
                results[key] = rec
        print("done", body)
    with open(rf"{OUT}\scores_g8.json", "w") as f:
        json.dump({"results": results, "errors": errors}, f, indent=1)
    font = ImageFont.load_default(size=15); fontb = ImageFont.load_default(size=22)
    S = 230; pad = 6; left = 150; top = 70
    for facing in FACINGS:
        cols = []
        for g in GARMENTS:
            cols += [(f"vanilla {g}", lambda b, g=g: c1.nearest4(c1.load(rf"{CORE}\{g}_{c1.VANILLA_OF[b].capitalize()}_{facing}.png"))),
                     (f"ROUND 8 {g}", lambda b, g=g: tiles.get((b, facing, g))),
                     (f"artist {g}", lambda b, g=g: tiles.get((b, facing, g, "wdi")))]
        im = Image.new("RGB", (left + len(cols) * (S + pad), top + len(BODIES) * (S + pad)), (235, 235, 230)); dr = ImageDraw.Draw(im)
        dr.text((8, 8), f"Generalisation test, round 8 unchanged, {facing}: garments never tuned on. Empty artist cell = he drew none; grey cell = failure.", fill=(0, 0, 0), font=fontb)
        for j, (name, _) in enumerate(cols):
            dr.text((left + j * (S + pad), 44), name, fill=(0, 0, 0), font=font)
        for r, b in enumerate(BODIES):
            y = top + r * (S + pad)
            dr.text((8, y + 8), f"{b}\n{facing}", fill=(0, 0, 0), font=fontb)
            for j, (_, get) in enumerate(cols):
                t = get(b)
                if t is None:
                    continue
                back = Image.new("RGBA", (N, N), (78, 98, 78, 255)); back.alpha_composite(c1.to_pil(t))
                im.paste(back.resize((S, S), Image.LANCZOS).convert("RGB"), (left + j * (S + pad), y))
        p = rf"{CAPT}\2026-11-07_generalise-{facing}.png"; im.save(p); print("board", p)


if __name__ == "__main__":
    main()
