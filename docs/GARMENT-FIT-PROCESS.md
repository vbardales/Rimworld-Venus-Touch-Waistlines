# Garment fit process: vanilla garment to a WDI body

State on 2026-11-07, written from the prototype boards Virginie validated step by step that day. Nothing here is in the DLL yet: the
prototype is Python under `Art/work/transfer-proto/fable-crack/` (local, gitignored, see "Tools"). This page says what the process
takes, what it does and why, so it can be run on other inputs (other garments, other bodies, other mods) and, one day, produce other
outputs (other body families, the in-game C# version).

## 1. Inputs

| Input | Where | Notes |
|---|---|---|
| Source garment | a worn texture drawn for the **vanilla** body types `Male`, `Female`, `Thin`, `Fat`, `Hulk`, three facings `south`, `east`, `north` | Vanilla: 128 px (`Art/work/core17/`). Mods: AB's Pants at `workshop/294100/2986402536/Textures/Things/Pawn/Humanlike/Apparel/Pants` (128 px, PNG beside DDS). Some mods ship 256 px. |
| Target body | the WDI body (`workshop/294100/3527486510/Textures/Things/Pawn/Humanlike/Bodies/Naked_<Body>_<facing>.png`), eight adult bodies | Each WDI body is drawn over one vanilla body: `Thin_Female` over `Thin`, `Fat_Female` over `Fat`, `Hulk_Female` over `Hulk`, the others over their namesake (`crack.VANILLA_OF`). |
| Landmark pairs | `Art/work/captures/2026-11-03_points/delta-<facing>-points.txt` | Virginie's points study of 2026-11-03: for each WDI body, each named point with its vanilla and WDI position. Front has 25 points, side 12, back 17. `axis` rows are not used. |
| Ground truth | the WDI artist's own garments: `Apparel/<Garment>/<Garment>_<Body>_<facing>.png` | Only for `ShirtBasic`, `ShirtButton`, `CorsetRoyal`, `TribalA`, `VestRoyal`, `BodyStrap`, `EltexShirt`, `UNA_Dress_sitagi`, and only on `Thin_Female`, `Fat_Female`, `Hulk_Female`. He drew **no trousers**. |
| Underwear | `Textures/UWUnderwear/<boxers|panties|longjohns>/<kind>_<Body>_<facing>.png` | All eight bodies, three facings. The tops of boxers (B) and panties (C) give the waist lines; the longjohns are the only WDI drawing of the legs. |
| Pants study | `Art/work/captures/2026-11-03_points/pants-<facing>-table.txt` | The same named points placed on AB, XND and catMonke pants, per vanilla body. |

## 2. Reference lines (per WDI body and facing, per column of the 512 px image)

- **min(B,C)**, the pink line: per column the **lower** of the boxers and panties tops on screen (`Nav.SetPink`: `Math.Max` on y), only
  where both sprites are drawn, median of 3. **The shirt follows it.** Past the shared span it is **extended with its own slope**
  (`hemshift_<Body>_<facing>.pink.txt`, with the hook handling of `hemshift.ps1`): held flat, the back of the side view went wrong.
- **max(B,C)**: per column the **higher** of the two tops (smaller y), same span rule, **held flat** past the shared span. **The trousers
  follow it.** The shirt therefore overlaps the top of the trousers between the two lines.
- min and max are taken **column by column**, not as one whole sprite line (Virginie, 2026-11-07): where the boxers and panties
  tops cross, the line moves from one to the other. On `Thin_Female` north the lower one is the boxers, then the panties, then
  the boxers again. On `Thin_Female` east the WDI artist drew both tops identical (0 px apart on all 98 shared columns), so
  min(B,C) = max(B,C) there.
- **Untucked limit**: an untucked shirt never goes below the **bottom of the boxers** (her rule of 2026-11-05, confirmed 2026-11-07).

**The four rules** (Virginie, 2026-11-07; board `2026-11-07_four-rules.png`, script `rules4.py`):

| Case | Top | Trousers | Drawn on top |
|---|---|---|---|
| 1. top alone | down to **min(B,C) + d_min**, d_min = the smallest gap, over the columns where both sprites are drawn, between min(B,C) and the bottom of the boxers' legs (the hem keeps the shape of min(B,C) and never goes below the boxers) | none | top |
| 2. trousers with a top | | up to **max(B,C)** | see 3 and untucked |
| 3. tucked top | **cropped at min(B,C)** | up to max(B,C), so no gap opens between the two lines; **min(B,C) in the columns where the two lines are within one stroke (4 px)** | **top over the trousers** (two layers: trousers under, top over); where the lines are close, a **single stroke, the trousers' waistband** |
| 4. trousers alone | none | stop at **min(B,C)** | trousers |
| untucked top | as in rule 1 | up to min(B,C) (or max(B,C): hidden either way) | **top over the trousers** |

Layering corrected by Virginie on `Thin_Female` south the same day, and the concept validated by her on that body and facing (the
others not reviewed yet): in both tucked and untucked cases the trousers are the lower
layer and the top the upper one.

**Tucked, where the two lines are close** (Virginie, 2026-11-07, "garde bas"; validated on `Thin_Female` south, east and north):
when min(B,C) and max(B,C) are less than one stroke apart, the trousers' stroke and the top's hem stroke sit side by side as an
8 px black band (east, where the lines are identical). In those columns:

- the trousers go up to min(B,C), the lower line, so their waistband sits where it sits on trousers alone (rule 4);
- the top's hem stroke is turned back into fabric (a stroke pixel nearer the hem curve than the side curve, within the hem band);
- the top's crop goes down to the trousers' top plus 1.5 px, so no row of body shows between them;
- the trousers' waistband stroke is drawn again over the top.

On `Thin_Female` this applies to 0 of 106 columns south, 98 of 98 east, 69 of 106 north.

**d_min is one constant per body type and facing** (Virginie, 2026-11-07), computed once like D
(`Art/work/transfer-proto/dmin.json`). Measure: the smallest gap between min(B,C) and the bottom of the boxers, over the shared
span, **only in the columns where the boxers' bottom runs across** (slope of 1 px per column or less). The side walls of the sprite,
where its bottom climbs to meet its top, are not the leg line: counted, they gave 11.2 on `Thin_Female` east and 65.6 north,
both wrong (Virginie, same day). Values at the 512 scale (only `Thin_Female` reviewed; `Hulk_Female` east still looks wrong):

| Body | south | east | north |
|---|---|---|---|
| Thin_Female | 40.0 | 43.0 | 75.0 |
| Fat_Female | 42.0 | 13.2 | 43.9 |
| Hulk_Female | 45.0 | 2.1 | 72.0 |
| Male | 32.0 | 25.0 | 43.0 |
| Female | 31.0 | 27.0 | 70.0 |
| Thin | 42.0 | 22.0 | 51.0 |
| Fat | 34.0 | 9.1 | 43.9 |
| Hulk | 53.0 | 42.0 | 66.0 |

At the back the boxers cover the buttocks, so d_min is large: the top alone reaches the bottom of the boxers.
- **D**: per column, pink line minus the vanilla naked body bottom, **centred** (its value at the middle removed) and smoothed
  (`hemshift_<Body>_<facing>.txt`). It carries the shape of the line, not its height. Known faults: the slope extension climbs steeply
  at the sides on `Hulk` and `Hulk_Female` front and back, and leaves the body on several side views; to bound before use on trousers.

## 3. The target outline (what the garment must become on WDI)

1. **Recalibrate the points.** On each side, every point moves by the same amount so the highest one sits on the top of its own
   silhouette (vanilla points on the vanilla body, WDI points on the WDI body).
2. **Edge convention: outer edge.** Points sit on the **outer edge** of the black outline, not on the fabric. A curve drawn from them is
   then stroked **inward** (4 px in the tests). Rationale and alternative in section 5.
3. **Top.** If the reference garment starts below the WDI silhouette top, the **whole drawing moves up** until it meets it (no union,
   no local stretch). Seen: `Hulk_Female` front and back 5 px, `Thin_Female` front 2 px, `Fat_Female` back 1 px.
4. **Point 1 and point 7.** `1 top` = the topmost pixel of the outer edge on the midline. `7 jugular notch` = the top of the neckline
   opening on the midline. On `Hulk` and `Hulk_Female` the outer edge dips at the midline, so 1 lies under the neck bases.
5. **Snap and complete.** The contour points of the body (neck bases, shoulder tips, armpits, waist, hips; side view: neck, upper back,
   chest, waist, belly, buttock) are snapped onto the reference contour. A centripetal Catmull-Rom curve is drawn through them, and a
   point is **added** where the curve strays more than **3 px** (512 scale) from the reference, until none does. Typical result: 16 to
   27 points per shirt outline (4 to 16 added), mean gap 0.8 px.
6. **Neckline (front).** The opening the reference garment leaves bare, done the same way, starting from 7: 8 to 10 points.
7. **Waistband.** The sides stop where the reference contour meets the waist line of section 2; the hem follows that line, with points
   added the same way (3 to 7 points).
8. **Trousers bottom: a U, not a W.** The naked body ends in two lobes with a crotch notch; trousers do not. The bottom 40 % of the
   target is replaced by its convex hull, so the crotch points land at the bottom of the U.

Reference contour per garment class:

| Class | Reference | Waist line |
|---|---|---|
| Top (shirt) | the artist's `ShirtBasic` where he drew one | min(B,C), extended |
| Trousers | the artist's longjohns below the waist, bottom closed in a U | max(B,C), held flat |
| Bodies he did not draw (`Male`, `Female`, `Thin`, `Fat`, `Hulk`) | no ground truth: borrow from a donor body (`crack2.DONOR`) | same lines, which exist for all eight |

Check: redraw the outline (white fill, 4 px stroke inward) and compare with the reference. Shirt above the hips: shape IoU 0.971 to
0.992. Trousers: 0.943 to 0.984. Shirt and trousers meet on one line, the shirt over the trousers.

## 4. Preparing the source garment

1. **Upscale x4** (128 to 512) so the warp does not resample coarse pixels.
2. **Remove the black outline by thickness, not by colour.** Colour alone either leaves a dotted grey halo (anti-aliasing) or eats dark
   parts of the garment (FlakVest straps). Remove a band of the measured outline thickness (vanilla about 3 to 4 px at 128) plus 1 px
   for the halo. Inner strokes (collar, seams, buttons) are kept.
3. **Fill the freed band with fabric** up to the vanilla outer edge, by copying the nearest **light** fabric pixel (never a stroke), so
   the source again covers its full outer silhouette. Proposed by the Fable worker, retained by Virginie on 2026-11-07.
4. Nothing else is cut: no collar zone, no back band (her decision on step 4, 2026-11-07).

## 5. Why the outer edge, and the alternative

The source keeps no black. If its fabric (smaller than its silhouette by the outline) were stretched onto an outer-edge target, it
would be deformed by the outline width. Two consistent choices exist:

- **Outer to outer (retained):** fill the freed band (section 4.3), warp outer edge to outer edge, draw the WDI outline over the edge.
  The filled band is hidden by the new outline, or becomes legitimate fabric.
- **Fabric to fabric:** points on the fabric edge on both sides, the new outline drawn outward. Invents nothing, but the vanilla points
  must then also be moved onto the vanilla fabric edge.

## 6. The warp

- **Driven by the point pairs only.** Pulling every edge of the WDI silhouette onto the nearest garment edge (round 8, step 5 E) is what
  turned corsets, jackets and strap vests into full shirts; it is gone.
- **Thin-plate spline** from WDI to vanilla coordinates (backward map). Smoothing `lam = 2000` misses the points by 1.5 to 2 vanilla px
  on average (6.8 max, `Fat_Female` side, waist front); `lam = 1` hits every point but folds where close points move in opposite
  directions (crotch cluster, `Hulk_Female` top +16 px, side chest -9 / waist +16). Fix the contradictory pairs before going exact.
- **Room for the legs.** Below the navel (else the belly front, else the hips, always 24 px above the waist line), the WDI targets are
  compressed so the body bottom of each column lands on the garment's lower limit (section 2).
- **Added points need vanilla twins.** Points added in section 3.5 exist on the WDI side only; each needs a vanilla partner, e.g. at
  the same arc-length fraction between the same two named neighbours on the vanilla contour. Not done yet.

## 7. Finishing

- Clip the warped garment to the target outline (section 3), cut the neckline.
- Shading: the WDI body shading multiplied at 0.30 (round 7); to review.
- **No forced whitening.** Bringing the fabric to the artist's white is valid only for light garments; a dark garment (FlakVest,
  luminance 0.08) or a coloured modded one must keep its colour.
- Draw the outline on the outer edge, inward. Tests use 4 px; the WDI artist's own outline is 10 to 12 px at 512.

## 8. Other inputs

- **Other garments.** The outline must come from the **garment's own shape** carried through the warp, clipped to the WDI silhouette
  only where the vanilla garment touched the vanilla body edge. A generic "body + margin" target turns every garment into a shirt
  (generalisation test of 2026-11-07: corset, one-shoulder TribalA, open Jacket, FlakVest all failed that way). The collar block of
  round 8 must not be pasted on garments without a collar.
- **Other mods' textures.** Same body keys; 256 px textures are scaled to the same 512 working grid.
- **Other bodies.** Each new body needs: its landmark pairs, its two waist lines (or underwear sprites to compute them), and a donor for
  the reference contour if no artist garment exists.

## 9. Outputs, now and later

- **Now:** one 512 px RGBA image per WDI body, facing and garment, for boards.
- **In game (C#):** compute once per garment, body and facing on first draw, then cache, as TailorMade does (`TexBake.BakeFitted`); the
  steps are plain image operations (upscale, distance transform, label, fill, thin-plate spline). Port only once the method holds on
  several garment classes.
- **Other targets:** a body family with its own legs and feet (for example Xeva's) is the same process with another target body and
  other reference lines; the cut line stays replaceable (expansion roadmap).

## 10. Open items

- Vanilla twins of the added points (section 6), then the real warp of the vanilla shirt and of AB's Pants into the outlines.
- Bound the slope extension of D and of the pink line to the body.
- Donor rule for the five bodies the artist did not draw.
- Contradictory point pairs (crotch cluster, `Hulk_Female` top, side chest and waist) before an exact warp.
- Outline width (4 px of the tests or the artist's 10 to 12 px).

## Tools (prototype, `Art/work/transfer-proto/fable-crack/`, gitignored)

| Script | Board in `Art/work/captures/` | What it shows |
|---|---|---|
| `crack8.py` + `steps.py` | `2026-11-07_round8-steps*.png` | round 8 step by step; switches `CUT_CLOTH`, `PEEL`, `EDGE_PULL` |
| `explain5b.py` | `2026-11-07_step5-detail*.png` | the warp in detail; options `exact`, `legs`, `untucked`, `recal` |
| `snapshirt.py`, `snapdraw.py` | `2026-11-07_snap-shirt.png`, `2026-11-07_snap-draw.png` | points on the artist's shirt, redraw and comparison |
| `shirt2.py` | `2026-11-07_shirt-step2.png` | shirt down to min(B,C), over the trousers |
| `pantsnap.py` | `2026-11-07_pants-snap-<facing>.png` | trousers on the longjohns, max(B,C), U bottom |
| `dline.py` | `2026-11-07_D-line.png` | the D line on all bodies |
| `rules4.py [Body]` | `2026-11-07_four-rules[-<Body>].png` | the four rules and untucked; d_min (`dmin_of`), tucked (`tucked`) |
| `tuckzoom.py [Body]` | `2026-11-07_tucked-zoom-<Body>.png` | waist zoom: trousers alone over tucked, three facings |
| `generalise.py` | `2026-11-07_generalise-<facing>.png` | round 8 on garments it was never tuned on |

Run any of them with `uv run --with numpy --with pillow --with scipy --with scikit-image python <script>` from that folder.
