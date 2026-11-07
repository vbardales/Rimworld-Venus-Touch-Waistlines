# Garment fit process: vanilla garment to a WDI body

State on 2026-11-07, written from the prototype boards Virginie validated step by step that day. Nothing here is in the DLL yet:
the prototype is Python under `Art/work/transfer-proto/fable-crack/` (local, gitignored, see "Tools"). This page says, step by
step, what the process takes, what each step does and why, so it can be run on other inputs (other garments, bodies, mods) and,
one day, produce other outputs (other body families, the in-game C# version).

All sizes are at the 512 px working scale unless said otherwise (vanilla textures are 128 px, upscaled x4).

## Overview

| Part | Step | Done | Output |
|---|---|---|---|
| A, once per WDI body and facing | A1 points | recalibrate the landmark pairs | named WDI and vanilla points |
| | A2 lines | min(B,C) and max(B,C) from the underwear sprites | two waist lines per column |
| | A3 d_min | gap from min(B,C) to the boxers' leg line | one constant |
| | A4 outlines | the target outline of the top and of the trousers | reference contours, snapped points, added points |
| | A5 rules | where each garment stops, for each case | lower limit of the top, top of the trousers |
| B, per garment | B1 source | the vanilla garment, x4, its vanilla points | 512 px source |
| | B2 peel | its black outline removed by thickness | source without outline |
| | B3 pairs | every WDI point with its vanilla partner, pressed up for the legs | the warp pairs |
| | B4 warp | thin-plate spline driven by the pairs only | the garment on the WDI body |
| | B5 clip | cut to the target outline of the rule, gaps filled, shading | the garment, clipped |
| | B6 outline | 4 px stroke inward, layering with the trousers | the final image |

## Inputs

| Input | Where | Notes |
|---|---|---|
| Source garment | a worn texture drawn for the **vanilla** body types `Male`, `Female`, `Thin`, `Fat`, `Hulk`, facings `south`, `east`, `north` | Vanilla: 128 px (`Art/work/core17/`). Mods: AB's Pants at `workshop/294100/2986402536/Textures/Things/Pawn/Humanlike/Apparel/Pants` (128 px). Some mods ship 256 px. |
| Target body | the WDI body (`workshop/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_<Body>_<facing>.png`), eight adult bodies | Each WDI body is drawn over one vanilla body: `Thin_Female` over `Thin`, `Fat_Female` over `Fat`, `Hulk_Female` over `Hulk`, the others over their namesake (`crack.VANILLA_OF`). |
| Landmark pairs | `Art/work/captures/2026-11-03_points/delta-<facing>-points.txt` | Virginie's points study of 2026-11-03: each named point with its vanilla and WDI position, for all eight bodies. Front 25 to 27 points, side 12, back 15 to 17. `axis` rows are not used. |
| Ground truth | the WDI artist's garments: `Apparel/<Garment>/<Garment>_<Body>_<facing>.png` | Only on `Thin_Female`, `Fat_Female`, `Hulk_Female` (`ShirtBasic`, `ShirtButton`, `CorsetRoyal`, `TribalA`, `VestRoyal`, `BodyStrap`, `EltexShirt`, `UNA_Dress_sitagi`). He drew **no trousers**. |
| Underwear | `Textures/UWUnderwear/<boxers|panties|longjohns>/<kind>_<Body>_<facing>.png` | All eight bodies, three facings. Boxers (B) and panties (C) give the waist lines; the longjohns are the only WDI drawing of the legs. |
| Pants study | `Art/work/captures/2026-11-03_points/pants-<facing>-table.txt` | The same named points on AB, XND and catMonke pants, per vanilla body. |

## Part A: once per WDI body and facing (no garment involved)

### A1. Points

Every point of a side moves by the same amount so the highest one sits on the top of its own silhouette (vanilla points on the
vanilla body, WDI points on the WDI body). `explain5b.recal`.

### A2. The two waist lines, min(B,C) and max(B,C)

- **Per column**, from the top edge of the boxers (B) and of the panties (C): **min(B,C)** is the **lower** one on screen (larger y),
  **max(B,C)** the **higher** one. Taken column by column, not as one whole sprite line: where the two tops cross, the line moves
  from one to the other (`Thin_Female` north: boxers, then panties, then boxers). On `Thin_Female` east the artist drew both tops
  identical (0 px apart on all 98 shared columns), so min = max there.
- **Sprite walls dropped first.** The top edge of a sprite is not the waistband at its ends:
  1. a jump of 5 px or more in the 10 end columns (the rounded side pad of the panties: `Hulk_Female` 383 then 396 px south);
  2. then the columns that still step by more than 2 px;
  3. then a gentle wall up to a real corner within 35 % of the line from its end (the line rises to the corner, then turns back
     down by more than 2 px): `Thin_Female` east back, 8 columns; `Hulk_Female` east back, past the corner at column 164 the top
     edge is the buttock outline for 39 columns.
- Median of 3 on the span both sprites still cover, then **both lines extended past that span with their own slope** (linear fit on
  their last 12 columns); max is never under min. A line held flat, or following the sprite's silhouette, made the hems drop
  back at the sides (Virginie: "ça a utilisé certaines lignes sans extrapolation, d'où la redescente").
- `pantsnap.lines`; the trousers use the same lines (`pantsnap.waist_line`).

### A3. d_min

- **One constant per body type and facing.** The smallest gap between min(B,C) and the bottom of the boxers, over the shared span,
  **only in the columns where the boxers' bottom runs across** (slope 0.3 px per column or less: the leg line).
- Not the leg line: the side walls of the sprite (counted, they gave 11.2 on `Thin_Female` east and 65.6 north) and the slanted hip
  sides of the wide boxers (slope 0.7 to 1 on `Fat_Female`; counted, 42 south, 13 east, 44 north).
- The same d_min serves the top alone and the untucked top (a second d_min measured from max(B,C) was tried and dropped).
- `rules4.dmin_of`, values in `Art/work/transfer-proto/dmin.json`:

| Body | south | east | north |
|---|---|---|---|
| Thin_Female | 40 | 45 | 75 |
| Fat_Female | 56 | 38 | 91 |
| Hulk_Female | 45 | 34 | 81 |
| Male | 42 | 29 | 48 |
| Female | 31 | 34 | 72 |
| Thin | 50 | 43 | 52 |
| Fat | 56 | 27 | 91 |
| Hulk | 53 | 42 | 68 |

### A4. Target outlines

**Edge convention: outer edge.** Points sit on the outer edge of the black outline; a curve through them is stroked **inward**
(4 px in the tests). The other choice (fabric to fabric, outline drawn outward) is consistent too but needs the vanilla points
moved onto the vanilla fabric edge.

**Top (shirt).**

1. Reference: the artist's `ShirtBasic` where he drew one. If it starts below the WDI silhouette top, the **whole drawing moves up**
   until it meets it (no union, no local stretch): `Hulk_Female` front and back 5 px, `Thin_Female` front 2, `Fat_Female` back 1.
2. Bodies he did not draw (`Male`, `Female`, `Thin`, `Fat`, `Hulk`): the WDI body silhouette grown by the donor's ease + 2 px (donor
   `crack2.DONOR`; his shirt sits on the body for `Thin_Female` and `Hulk_Female`, IoU 0.98, about 6 px off it for `Fat_Female`),
   minus the opening the donor's shirt leaves bare around the neck, carried over in the neck frame (`snapshirt.synth_art`). The
   +2 px keeps the curves from cutting inside the body.
3. **Point 1 and point 7.** `1 top` = the topmost pixel of the outer edge on the midline. `7 jugular notch` = the top of the neckline
   opening on the midline (on `Hulk` and `Hulk_Female` the edge dips at the midline, so 1 lies under the neck bases).
4. **Snap and complete.** The contour points (neck bases, shoulder tips, armpits, waist, hips; side: neck, upper back, chest, waist,
   belly, buttock) are snapped onto the reference contour. A centripetal Catmull-Rom curve goes through them, and a point is
   **added** where the curve strays more than **3 px** from the reference, until none does: 16 to 27 points per outline (4 to 16
   added), mean gap 0.8 px.
5. **Neckline (front)**: the opening, done the same way from 7, 8 to 10 points.
6. **Hem**: the sides stop where the contour meets the rule's lower limit (A5); the hem follows that line, points added the same way.

Check: redrawn outline against the artist's shirt above the hips, IoU 0.971 to 0.992.

**Trousers.** The artist's longjohns below the waist line, united with the body there (on `Male` and `Female` his longjohns are
narrower than the body); the bottom 40 % of the target is replaced by its convex hull, so trousers end in a **U**, not the naked
body's W. The same snap and completion. Check: IoU 0.943 to 0.984.

### A5. The rules: where each garment stops

| Case | Top | Trousers | Layers |
|---|---|---|---|
| 1. top alone | down to **min(B,C) + d_min** | none | top |
| 4. trousers alone | none | up to **min(B,C)** | trousers |
| 3. tucked top | **cropped at min(B,C)** | up to **max(B,C)**; **min(B,C)** where the two lines are within one stroke (4 px) | trousers under, top over; where the lines are close, a single stroke: the trousers' waistband |
| untucked top | down to **max(B,C) + d_min** (same d_min): the hem sits higher by the gap between the lines, a little more of the trousers shows | up to min(B,C) | trousers under, top over |

- **Vertical offset.** d_min moves the line straight down, column by column (Virginie: "on garde"). On a steep line the gap seen
  across it is smaller (`Hulk_Female` east back, slope 2.5: 13 px across for 34 down); a perpendicular offset of the same size
  would go 91 px down there, under the boxers, and the cut stays per column like the game's.
- On east the top alone and the untucked top follow the diagonal waistband, so they are short at the back (accepted).
- **Tucked, close lines** ("garde bas"): the trousers take min(B,C); the top's hem stroke is turned back into fabric; the crop goes
  down to the trousers' top + 1.5 px so no body shows; the trousers' waistband is drawn again over the top. The min/max switch and
  the crop switch are smoothed weights, the trousers' line is smoothed again (sigma 8), and the crop never sits above the trousers'
  top (Virginie: "il manque un lissage"). `Thin_Female`: 0 of 106 columns south, 98 of 98 east, 69 of 106 north.
- The top stays as loose as the artist drew it, even tucked (tightening at the waist: optional backlog in `STATUS.md`).
- `rules4.py`: `untucked_hem`, `tucked`.

Validated by Virginie on the three bodies the artist drew, three facings; the five others reviewed, corrections made.

## Part B: per garment (first pass: vanilla `ShirtBasic`, rule 1, `fullpass.py`)

### B1. Source

The vanilla garment upscaled x4 (128 to 512) so the warp does not resample coarse pixels, on the vanilla body, with the vanilla
points (A1).

### B2. Peel

- The black outline is removed **by thickness, not by colour**: the outer band of the measured outline width (vanilla about 3 to 4 px
  at 128) + 1 px of halo, around the outer edge and around the neck hole. Colour alone left a dotted grey halo (anti-aliasing) or
  ate dark garments (FlakVest straps). Inner strokes are kept.
- **No fill** of the freed band (Virginie: "pas besoin de populer les bords"): B5 fills whatever the target lacks, and the whole is
  shrunk to 256 at the end. Nothing else is cut (no collar zone, no back band).

### B3. Pairs

1. **Named pairs**: her points from A1. The contour points are snapped onto both outlines (the WDI target, A4; the vanilla garment's
   outer contour); the inner points stay as they are.
2. **Added points get vanilla twins**: the same arc-length fraction between the same two snapped neighbours, along the shorter way of
   the vanilla contour.
3. **Front neckline**: the WDI opening's points paired with the vanilla neck hole, by arc-length fraction from its top, same
   direction of travel. Without them the vanilla hole landed lower than the target's.
4. **Room for the legs.** Start row y0: the navel, else the belly, else the hips, on both bodies; always 24 px above the lower limit.
   Below it, each WDI point takes the share of height its **vanilla** partner has between that landmark and the vanilla body bottom
   of its column, laid between y0 and the **rule's lower limit** (A5: top alone min(B,C) + d_min, untucked max(B,C) + d_min).
   So the vanilla crotch and body bottom land on that limit (Virginie: "on suit ce qu'on a dit à la pré-étude avec d_min"; `Male`
   top alone: about the bottom of the boxers at the centre). A contour point it moves goes back onto the target outline; no point
   stays under the limit. Taking the share on the WDI side left the east front points of `Male` (7, 21, 22: vanilla waist and
   belly) on the hem.

The board numbers every pair the same on steps 1 and 3: yellow her contour points, cyan her inner points, orange the added points
and their twins, a blue ring where a point was before the press.

### B4. Warp

- **Driven by the point pairs only.** Pulling every edge of the WDI silhouette onto the nearest garment edge (round 8, step 5 E)
  turned corsets, jackets and strap vests into full shirts; it is gone.
- **Thin-plate spline** from WDI to vanilla coordinates (backward map), `lam = 2000`: misses the points by 1.5 to 2 vanilla px on
  average; `lam = 1` hits every point but folds where close points move in opposite directions (crotch cluster, `Hulk_Female` top,
  side chest and waist). Fix the contradictory pairs before going exact.

### B5. Clip

- Cut to the target outline of the rule (A4, A5), neckline included.
- Pixels of the target the warped garment leaves empty get the **fabric's colour smoothed** (normalised blur over the garment
  pixels, carried outward); copying the nearest pixel drew streaks.
- Shading: the WDI body's shading at 0.30, **blurred** (sigma 10) so the body's muscles do not print on the cloth.
- **No forced whitening**: a dark or coloured garment keeps its colour.

### B6. Outline and layers

- The outline on the outer edge, inward, 4 px in the tests (the artist's own is 10 to 12 px at 512).
- Layers as in A5: trousers under, top over.

`Male` validated by Virginie for the points and the warp (three facings).

## Other inputs

- **Other garments.** The outline must come from the **garment's own shape** carried through the warp, clipped to the WDI
  silhouette only where the vanilla garment touched the vanilla body edge. A generic "body + margin" target turns every garment into
  a shirt (generalisation test: corset, one-shoulder TribalA, open Jacket, FlakVest all failed that way). No collar pasted on
  garments without one.
- **Other mods' textures.** Same body keys; 256 px textures are scaled to the same 512 grid.
- **Other bodies.** Each new body needs its landmark pairs, its underwear sprites (for A2 and A3), and a donor for A4 if no artist
  garment exists.

## Outputs, now and later

- **Now:** one 512 px RGBA image per WDI body, facing and garment, on boards.
- **In game (C#):** compute once per garment, body and facing on first draw, then cache, as TailorMade does (`TexBake.BakeFitted`);
  every step is a plain image operation (upscale, distance transform, label, blur, thin-plate spline). Port once the method holds
  on several garment classes. Part A is per body only and can be baked as constants (24 sets: 8 bodies, 3 facings).
- **Other targets:** a body family with its own legs and feet (for example Xeva's) is the same process with another target body and
  other reference lines; the cut line stays replaceable (expansion roadmap).

## Open items

- Part B on the seven other bodies, then the other rules (tucked, untucked), then AB's Pants.
- `Male` east: the neck front, where the warp leaves gaps; the vanilla inner collar stroke is kept on south.
- Contradictory point pairs before an exact warp.
- Outline width (4 px or the artist's 10 to 12 px).
- Bound the slope extension of D (`hemshift_<Body>_<facing>.txt`, pink line minus the vanilla body bottom, centred) before using it
  on trousers.

## Tools (prototype, `Art/work/transfer-proto/fable-crack/`, gitignored)

| Script | Board in `Art/work/captures/` | What it shows |
|---|---|---|
| `fullpass.py [Body]` | `2026-11-07_fullpass-<Body>.png` | Part B, steps 1 to 6, three facings |
| `rules4.py [Body]` | `2026-11-07_four-rules[-<Body>].png` | A3 and A5: d_min (`dmin_of`), the four rules, untucked (`untucked_hem`), tucked (`tucked`) |
| `pantsnap.py` | `2026-11-07_pants-snap-<facing>.png` | A2 lines (`lines`, `waist_line`), trousers outline |
| `snapshirt.py`, `snapdraw.py` | `2026-11-07_snap-shirt.png`, `2026-11-07_snap-draw.png` | A4 top outline, points on the artist's shirt (`synth_art` for undrawn bodies) |
| `tuckzoom.py [Body]` | `2026-11-07_tucked-zoom-<Body>.png` | waist zoom: trousers alone over tucked |
| `untuck2.py` | `2026-11-07_untucked-AB.png` | untucked variants set aside |
| `shirt2.py` | `2026-11-07_shirt-step2.png` | earlier shirt outline over the trousers |
| `dline.py` | `2026-11-07_D-line.png` | the D line |
| `explain5b.py`, `crack8.py` + `steps.py` | `2026-11-07_step5-detail*.png`, `2026-11-07_round8-steps*.png` | round 8 and its warp, superseded by `fullpass.py` |
| `generalise.py` | `2026-11-07_generalise-<facing>.png` | round 8 on garments it was never tuned on |

Run any of them with `uv run --with numpy --with pillow --with scipy --with scikit-image python <script>` from that folder.
