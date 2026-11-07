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
| | B4 warp | thin-plate spline driven by the pairs only (`lam` 20), fold check | the garment on the WDI body: **the result for now** |
| | B5 clip | cut to the target outline of the rule, gaps filled, shading | taken out on 2026-11-07 (option `b56`) |
| | B6 outline | the artist's stroke width inward, layering with the trousers | taken out on 2026-11-07 (option `b56`) |
| C, per body (in progress) | C1 relief | each body imagined in volume from its three views | a height map per facing |
| | C2 relief map | vanilla, laid flat on its surface, laid again on the WDI relief | a dense map, no point pairs |

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
- **Only along the body's edge**: a stroke is peeled only within the outline depth + 8 px of the vanilla body's edge. The edges of an
  opening inside the body keep their line, as the vanilla artist drew it (`LabCoat`'s open front). On `ShirtBasic` it changes 0
  to 110 px.
- The crotch notch of the hem is closed (convex hull of the bottom 40 %) only when it is a notch: an opening that runs up through
  that whole band (`LabCoat`) is part of the garment.

### B3. Pairs

1. **Named pairs**: her points from A1. The contour points are snapped onto both outlines: the WDI target (A4) and, on the vanilla
   side, the edge of the fabric **left after B2** (not the original outer edge: the peeled band, now transparent, was stretched up to
   the WDI outline). The inner points stay as they are, except the **groin creases**: in the study they sit at the navel's height on
   the WDI bodies (`Male`: 356, above the pelvis lines), while on vanilla they are well under the navel. They go **on the waistband
   line min(B,C)**, where the pelvis lines start under the navel, at 0.72 of the study's distance from the navel's x (Virginie's
   placement on `Male` south, validated 2026-11-07; to check on the other bodies).
   A contour point snaps onto the garment's edge **only when the garment lies on the body's edge there** (within 12 px,
   `SNAP_TOL`); elsewhere it stays a body point on both sides. `LabCoat` in profile: its open front runs behind the chest, the chest
   points snapped onto it and dragged it to the WDI chest front (Virginie: "de côté, c'est catastrophique").
   **Neck bases keep the vanilla order against the neck hole**: where the neck base is outside the hole on one body and above it on
   the other (collar survey, `2026-11-07_collar-survey.txt`: `Male`, `Fat`, `Fat_Female`), the WDI neck base goes on the top edge at
   the vanilla share between the shoulder tip and the hole edge. The WDI hole (the artist's, often wider) is kept.
   **The jugular notch** sits on the top of the opening on both sides.
2. **Added points get vanilla twins**: the same arc-length fraction between the same two snapped neighbours, along the shorter way of
   the vanilla contour; none where a neighbour did not snap.
3. **Front neckline**: the WDI opening's points paired with the vanilla neck hole **by angle around each hole's centre**, the vanilla
   hole taken without its V slit (opening of radius 8). By arc length, the slit lengthened the vanilla contour and the pairs crossed.
4. **Hips**: her contour points stop at the lowest of them; every 16 px down each side to the hem, the target's edge pixel is paired
   with the nearest point of the vanilla fabric edge to where the warp without them samples it (Virginie: "il manque des marques pour
   les hanches"). In profile, no fabric may cover the throat front (no ShirtBasic does: vanilla 0 to 80 px, the artist 0 to 4).
5. **Fold check**: a triangle of WDI points (Delaunay) that turns over on vanilla folds the fabric. While one does, its least reliable
   point leaves the warp (grey on the boards): detected extremes (top, bottom, leftmost, rightmost) first, then added twins, then
   hip and hem pairs; her named points stay, a fold among them only is reported. Without legs (`nolegs`), the crotch, leg bottom and
   bottom points do not drive the fabric.
6. **Room for the legs** (left out for now, Virginie: "pour l'instant, SANS les jambes"; option without `nolegs`). Start row y0: the navel, else the belly, else the hips, on both bodies; always 24 px above the lower limit.
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
- **Thin-plate spline** from WDI to vanilla coordinates (backward map), `lam = 20` (`LAM`). With 2000 it missed the points by
  3.5 px (median) to 16 px at 512, and the fabric fell short of the outline on the flanks, the belly, the neck and the shoulders.
  With 20: 0.2 px (median), 1.3 px at most, no fold left in the target once the fold check (B3, 5) has run.
- Computed in chunks (the whole 512 x 512 grid at once ran out of memory).
- **B4 is the result for now**: B5 and B6 are taken out (Virginie 2026-11-07, "enlève aussi l'étape 5"); `b56` shows them again.

### Diagnostics: the grid

A grid garment (lines every 16 px, every 4th red) drawn on the vanilla body and carried by the warp shows how it behaves where there
is no point (`gridboard.py`, area change in colour). On `Male` with `ShirtBasic` pairs: the chest stretched x2 under the collar then
squeezed under the pecs (her chest points sit just under the vanilla collar, much lower on WDI), the right flank pinched, the profile
front and the back's shoulder corners not reached. With the contour pairs only, the chest is regular: the stretch comes from the
inner points. Points alone do not settle the inside: hence Part C.

### B5. Clip

- Cut to the target outline of the rule (A4, A5), neckline included.
- Pixels of the target the warped garment leaves empty get the **fabric's colour smoothed** (normalised blur over the garment
  pixels, carried outward); copying the nearest pixel drew streaks.
- Shading: the WDI body's shading at 0.30, **blurred** (sigma 10) so the body's muscles do not print on the cloth.
- **No forced whitening**: a dark or coloured garment keeps its colour.

### B6. Outline and layers

- The outline on every edge of the target (outside, neck hole, hem), inward, black, its inner side anti-aliased, at the WDI
  artist's own width: 11 to 13 px at 512 (vanilla 14); his drawing, or the donor's for an undrawn body. The 4 px hard stroke of the
  first tests was a third of it. Taken out with B5 for now.
- Layers as in A5: trousers under, top over.

`Male` validated by Virginie for the points and the warp (three facings), before the changes of the afternoon of 2026-11-07.

## Part C: the relief map (in progress, `Male`)

Virginie 2026-11-07: "partir d'une grille orthogonale SUR VANILLA, la passer en plate et la repasser sur le relief WDI".

### C1. Relief (`relief3d.py`)

- **Volume from the three views**: each row is a cross-section whose **width** comes from the front view and whose **depth** from the
  profile (back edge to front edge, so the chest, the belly and the buttocks are in it). Rows of the views are matched by the
  silhouette's top and bottom. Front: the front half of the section; back: the back half; profile: the side, its height the front
  view's half width. Rows smoothed (the 128 px vanilla steps striped it).
- **Chest lobes** (front): two lobes on her points (breast apex L/R, the cleavage between them lower, the under-breast fold as their
  lower edge).
- **Drawn volumes**: each zone the artist separates with his lines (pecs, abs blocks, shoulder blades) bulges on its own; the lines
  are where two volumes meet. The shading as height made hollows of the shadows (Virginie: "les ombres font des dépressions plutôt
  que de mettre en avant des différences de volume").
- The body's black outline is removed, the drawn folds bridged (closing of radius 6).

### C2. Relief map (`reliefmap.py`)

- Surface coordinates on each body: **across**, the surface length from the row's middle divided by the row's half surface width on
  that side (-1 at the left edge, +1 at the right); **down**, the surface length down each column.
- **Down made comparable** between the two bodies by her landmarks common to both (same names): piecewise linear between their
  surface heights (the row's median), top and bottom included.
- Every WDI pixel takes the vanilla pixel with the same (across, down) (nearest in a k-d tree), smoothed (sigma 3): a dense map,
  no point pairs, the whole WDI body covered.
- On `Male`: front regular; back clean but a band of close lines at the waist; profile a band under the pecs.
- **Why the bands** (2026-11-07): landmarks whose meaning differs on the two bodies. Profile "chest front" (detected, the most
  forward point) is high on the flat vanilla chest (y 226) and at the pec apex on WDI (278): segment ratio x6.3 then x0.29. Back
  "shoulder tip" (detected) at 226/234 on vanilla, 258 on WDI (sloped shoulders): x0.56. Front: the study's groin creases at the
  navel's height on WDI (the fix of B3 is not applied here): navel to sex x2.5. And the profile mixes front and back landmarks in
  one scale.
- **Corrections applied** (Virginie: "oui, applique"):
  1. Only the landmarks she placed in the study (delta tables: "both placed", "one placed"), plus the armpits and the neck front
     and back (detected, but on a real corner of the silhouette). Out: top, bottom, leftmost, rightmost, shoulder tip, chest front,
     shoulder blade, buttock, hips, leg bottoms.
  2. Heights shared between the views: pec apex, under-breast fold, navel and sex, taken from the front view's rows and mapped onto
     the side and back views (rows matched by the silhouette's top and bottom).
  3. Profile: the front landmarks drive the front half, the back ones the back half, the shared rows both; blended across the
     middle.
  4. The groin creases are left out of the heights: raised onto the waistband (B3) they stretched the grid x2 down to the sex,
     a dark band on the front. They stay in the B3 pairs.
  5. The **whole silhouette**, its black outline included, on both bodies: the vanilla garment covers the vanilla body's outline,
     so the map reaches the WDI body's outline too (Virginie: "on voit encore des zones noires ... il n'en faut justement pas").
  Result on `Male`: no dark zone left, the grid covers the whole WDI body in the three views.
- **Weak zones** (Virginie: "c'est les zones de faiblesse"): the board shows the map's local area change (blue squeezed, red
  stretched). Two causes found and treated on `Male` (2026-11-08):
  1. **The cloth, not the skin**: the relief has its hollows bridged (grey closing of radius 14) and falls from a bump no faster
     than 0.6 px per row going down (it hangs from the pec apex), so the cloth does not follow the fold under the pecs, the small of
     the back or the buttocks' cleft (`reliefmap.cloth`).
  2. **Landmarks the cloth hides or that sit differently on a muscled body** are out of the heights: the under-breast fold, the
     waist, the profile's belly front (right under the big WDI pecs, far below the apex on vanilla) and the pec apex (above the
     armpits on vanilla, below on WDI; in profile it squeezed the apex-to-navel stretch x0.61 into a band). Heights now come from
     the neck (bases, jugular notch, neck front and back), the armpits, the navel and the sex; the armpit, navel and sex rows are
     shared with the side and back views.
  Left: a mild general squeeze (the WDI torso is shorter on the surface than the vanilla one), the upper back in profile, the low
  front and the stretched rim along the outline.
- **The garment's ease**: past the body edge (up to `EASE` = 28 px) each pixel takes the coordinates of the nearest body pixel
  plus its screen offset (across divided by the body's half width, down in px), on both bodies, so what the vanilla garment has
  outside the vanilla body keeps its distance on WDI (`reliefmap.extend`, `reliefmap.build`).
- **First garments through the map** (`garmentmap.py`, board `2026-11-08_garmentmap-Male.png`, `ShirtBasic` and `LabCoat`,
  B2 prep, no clip, no outline): the garment stays on the WDI body in the three views, where the point warp spills past it
  (shoulders, flanks, back); the blouse keeps its lapels and its open front in profile. The fabric edge stops where the vanilla
  fabric stopped against the vanilla body (inside, the stroke peeled), so the WDI body's own outline shows around it; thin slivers of
  bare body remain at the shoulders (the stretched rim).
- Still to do: decide the garment's edge (the body's outline as its stroke, or a stroke of its own), the slivers, the other bodies,
  then the map in B4 instead of the point warp.

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

- Part C: the four landmark corrections, the garment's ease, then the map in B4; then the seven other bodies.
- Part B on the seven other bodies, then the other rules (tucked, untucked), then AB's Pants.
- `Male` south: the vanilla V slit stretched down the chest (her cleavage point is far lower on WDI): shorten or remove it.
- The vanilla collar ring stays dark and thick after the warp.
- Garments with an open front (`LabCoat`): the target is still a T-shirt's silhouette.
- Whether B5 and B6 come back, and how.
- Bound the slope extension of D (`hemshift_<Body>_<facing>.txt`, pink line minus the vanilla body bottom, centred) before using it
  on trousers.

## Tools (prototype, `Art/work/transfer-proto/fable-crack/`, gitignored)

| Script | Board in `Art/work/captures/` | What it shows |
|---|---|---|
| `fullpass.py [Body]` | `2026-11-07_fullpass-<Body>.png` | Part B, three facings. Options: `nolegs`, `garment=<core17 name>`, `b56`, `fulllen`, `nogroin` |
| `stepboard.py [Body] nolegs [garment=X]` | `2026-11-07_steps-<Body>-<facing>[-<garment>].png` | Part A and Part B step by step, one board per facing |
| `pointsboard.py [Body] nolegs [garment=X]` | `2026-11-07_points-<Body>-nolegs-groin[-<garment>].png` | the warp pairs, large, vanilla and WDI side by side |
| `gridboard.py [Body] nolegs` | `2026-11-07_grid-<Body>.png` | the grid through the point warp, area change |
| `reliefgrid.py [Body] nolegs` | `2026-11-07_relief-grid-<Body>.png` | contour-only warp against all pairs (first relief model, superseded) |
| `relief3d.py [Body]` | `2026-11-07_relief3d-<Body>.png` | C1: the relief, lit, and a grid draped on it |
| `reliefmap.py [Body] nolegs` | `2026-11-07_reliefmap-<Body>.png` | C2: vanilla grid, laid flat, on the WDI relief, weak zones, against the point warp |
| `garmentmap.py [Body] nolegs` | `2026-11-08_garmentmap-<Body>.png` | C2: `ShirtBasic` and `LabCoat` through the relief map against the point warp |
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
