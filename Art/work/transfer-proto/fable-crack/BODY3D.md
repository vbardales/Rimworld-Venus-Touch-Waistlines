# WDI body 3D study (2026-11-08)

Goal (Virginie): a 3D representation of the eight WDI bodies derived from the relief map, with a smooth surface, the black outline integrated, volumes read from the WDI shading, features (nipples, sex, navel), legs, and an inner skeleton used as a constraint and a diagnostic. Later aims: cloth as a low-pass of the volume, tucked and untucked rules, AB Pants. An "isoRim" variant was suggested by Virginie, not started.

All files live under `Art/work/` (gitignored, force-added on branch `cloud-work`).

## Files

| File | Role |
|---|---|
| `transfer-proto/fable-crack/shade3d.py` | Active height field: a smooth three-silhouette envelope plus signed, localized patches anchored to the 2026-11-03 landmarks (neck/collar, axillae, attached breast or pec, sternum, navel, abs, pubis/groin, glutes). The former column-luminance solve remains selectable as a fallback. |
| `transfer-proto/fable-crack/relief_export2.py` | Closed mesh export: 360 sub-pixel rings from the south and north height fields, a hard east-profile envelope, lower cut rings below the crotch (notch or landmark seam), landmark rows, and the rigid-rib-cage floor. Output `out/relief3d-shade5.json` (R=360, U=44). |
| `transfer-proto/fable-crack/body3d_compare.py` | Silhouette overlays and a source-versus-active-relief panel for every body/view. The latter plots the 2026-11-03 landmarks so a low contour error cannot conceal a lost neck, chest attachment, navel or groin. |
| `transfer-proto/fable-crack/body3d_template.html` | Viewer code (three.js r128): skin modes, the exported diagnostic skeleton, and organs. `__DATA__` is replaced by the datasets. |
| `transfer-proto/fable-crack/body3d_build.py` | Rebuilds `captures/2026-11-08_body3d.html`, automatically replacing the first dataset with the latest export (`wdi3d-mesh.json`; `legacy` argument for `relief3d-shade5.json`). |
| `transfer-proto/fable-crack/wdi3d.py`, `wdi3d_export.py` | The core + masses model fitted to the WDI drawing, and its export (mesh, crease maps, frame) for the viewer. |
| `captures/2026-11-08_body3d.html` | The viewer (open in a browser, `squelette` checkbox, `east` button). |

Run the active export: `uv run --with numpy --with pillow --with scipy --with scikit-image python relief_export2.py`; then `uv run --with numpy --with pillow --with scipy --with scikit-image python body3d_compare.py`; then `uv run python body3d_build.py`. Inspect both `out/body3d-compare/<body>-<view>.png` (source/mesh edge overlay) and `out/body3d-compare/<body>-<view>-surface.png` (source + anchors beside the active signed relief); neither may be replaced by the other.

`RELIEF_MODE=structured` is the default. It does not sample the broad light/grey paint as height. `RELIEF_MODE=legacy` retains the previous `SHADE_K`/`SHADE_MU` column solve for A/B diagnosis only; it must not be treated as the active anatomy result. The older named-detail knobs remain meaningful only in that fallback.

## Method

1. Silhouette: alpha mask with holes filled, black outline kept (it is the rim where the surface turns away from the eye, so it is integrated, not removed).
2. Volume: width from the south view, depth from the east view, mid-depth line from the east silhouette. The east outline is a hard envelope: relief is renormalised row by row inside it, and the cage floor is capped there too.
3. Surface: localized signed patches are placed from the measured landmark geometry, never from a full-column luminance integral. The neck/collar, clavicles, sternal hollow, armpits, attachment folds, navel, groin and intergluteal cleft therefore have finite endpoints rather than becoming screen-wide bands.
4. Body-specific anatomy: female breast patches are asymmetric teardrop supports bounded by each own attachment crease and a central cleavage return to the cage; their local maximum lies below the apex landmark and a medial gate preserves the sternal skin plane. Thin_Female receives only a slightly stronger local lift inside that same narrow support. Fat adds a mild bilateral suspended chest patch under each apex; Fat and Fat_Female add a soft low pubic apron and larger gluteal patches. Hulk receives three short bilateral abdominal pairs from the costal margin to the pubis; Male/Average receives two restrained pairs. Both retain a finite, gated linea alba and lower-abdomen structure; their pectorals run as finite sternum-to-humerus fans rather than horizontal ellipses. On the back, a broad upper spinal sulcus joins a capped lower sacral/intergluteal cleft rather than a neck-to-crotch zip; Hulk and Male/Average also receive small diagonal trapezius, scapular and latissimus planes bounded by neck, shoulder, armpit and waist landmarks. These are laid over the rigid cage/pelvic envelope, so bone-bearing volume stays the base and muscle is a local attachment. Attachment, inguinal and pec creases follow short rounded arcs rather than unbounded rows. East-view patches make a deliberately small signed correction to the front/back mesh sections before the hard profile cap. White/grey paint remains paint unless a landmark asks for a form.
5. Mesh: front ring from the south field, back ring from the north field, joined at the silhouette edge. The assets end just below the crotch; their lower rings are a cut edge, not a reconstructed leg. Where a sprite has a crotch notch, its two alpha runs define two cut rings; otherwise, the named crotch starts an internal medial seam with the outer source projection unchanged.
6. Skeleton (viewer): every bone is placed from the skin by a ray from the row axis and a margin under it.
   - Rib cage: rigid barrel of 12 ribs, from the neck base (20 % of the way from the body top to the under-breast fold) to just above the navel (85 % of the way from the nipples to the navel). Depth fitted per level on the centre-line skin (7 px margin in front, 12 px behind), smoothed over 5 levels. Width from the 40th percentile of the side margins.
   - Sternum: a straight line fitted by least squares on the centre-line skin, lifted to the 60th percentile of the residuals.
   - Clavicles under the neck skin (Virginie: the clavicles sit under the skin of the neck), from the notch to 10 px above the shoulder tip.
   - Spine at 30 % of the depth from the back skin (at least 14 px); scapulae and iliac wings as plates; sacrum, pubis, femurs.
7. Floor (export): where there is no muscle the skin rests on the cage. After the cage is built, any skin point in front of or behind the cage is pushed out to at least 5 px from the cage surface. The export records the number of displaced points in each body's `cage.moved`; the viewer is diagnostic and never changes its input mesh.

## Checkpoint (2026-11-09)

The active reconstruction is a landmark-led anatomical prototype, not yet a WDI-equivalent render. `shade3d.py` retains `RELIEF_MODE=legacy` as an A/B fallback, while the default structured mode has a smooth three-silhouette envelope and local signed forms: neck/collar and axillae, attached breasts or sternum-to-humerus pectoral fans, sternum, navel, groin/pubis, Hulk lower abdominal pairs, posterior spine/scapular/latissimus planes and gluteal cleft. The supporting cage, spine, pelvis and femur roots remain a diagnostic constraint beneath that skin.

The required export, comparison and viewer build were last run on all eight bodies. Silhouette p95 ranges from 0.70 px (Thin south) to 4.79 px (Fat south); `Fat_Female` east is 4.10 px. Those numbers are only a contour gate. The source-plus-landmark and active-relief panels still show overly pillow-like transitions for Fat, Fat_Female and Thin_Female, and the uniform 3D viewer material cannot reproduce the WDI white/grey/ink treatment by itself.

Two generic smoothing experiments were rejected after full South/North/East regeneration: final Z smoothing degraded profile agreement, and lateral/global smoothing of the envelope both degraded east agreement and introduced normal artefacts near the neck. The next change must instead construct the thorax–abdomen–pelvis base directly from profile landmarks, retain the existing signed local anatomy above it, and compare full three-view renders with WDI rather than accepting a contour-only result.

## Profile-led base envelope (2026-11-09, real WDI textures)

All numbers below use the real Workshop textures (`Naked_<Body>_<facing>.png`, Steam id 3527486510) on this workstation; the stand-in is not used. The older Checkpoint numbers came from the stand-in, so they are not comparable.

Method (new files `base3d.py`, `body3d_render.py`; edits in `shade3d.py`, `relief_export2.py`):

1. `base3d.profile_base` replaces `relief3d.base_height` for south and north (east delegates to the old base; `BASE_MODE=ellipse` restores the old one). Depth per row still comes from the east silhouette (front and back half-depth about its centre, smoothed along rows with sigma 2). The per-row section is no longer an ellipse but a superellipse `(1-|t|^p)^(1/p)`, with p set per body class and interpolated between east landmark rows (top, chest front, waist front, buttock back, bottom): chest plate p 2.7 to 3.2 (Hulk highest, Fat 2.3), waist 2.0 to 2.6, hip 2.2 to 2.6, back halves flatter at the shoulder blades and rounder at the buttock. The signed anatomy patches of `shade3d.py` are laid over it unchanged.
2. `relief_export2.py`: the hard east cap now reads row-smoothed profile extents (`PROFILE_SIGMA=2`, rows only). The sprite is a 4 px upscale, so raw extents stepped and cut horizontal bands in the lit mesh. `CAGE_FADE=14`: the rib-cage floor holds its last level and fades its push over 14 px past both ends, so it leaves no step at the cage edge.
3. `body3d_render.py`: South/North/East shaded mesh (z-buffer, light upper left) beside the WDI texture and a mesh-edge overlay, one board per body in `Art/work/captures/2026-11-09_body3d-render-<Body>.png`. Legs share the body's vertical registration. This is the check that must be read, not the contour number.

Silhouette p95 (px), before (old ellipse base, real textures) then after:

| Body | south | north | east |
|---|---|---|---|
| Male | 2.10 / 2.10 | 1.15 / 0.96 | 2.87 / 2.42 |
| Female | 3.54 / 3.65 | 1.45 / 1.55 | 2.45 / 2.30 |
| Thin | 0.90 / 0.72 | 0.80 / 0.72 | 2.40 / 2.25 |
| Thin_Female | 1.21 / 1.30 | 1.91 / 2.10 | 2.25 / 2.23 |
| Fat | 4.68 / 4.79 | 2.60 / 2.70 | 2.85 / 2.55 |
| Fat_Female | 2.69 / 2.60 | 2.70 / 2.60 | 4.00 / 3.35 |
| Hulk | 1.40 / 1.30 | 2.38 / 2.20 | 2.65 / 2.67 |
| Hulk_Female | 2.30 / 2.30 | 2.19 / 2.40 | 3.00 / 3.05 |

East improves on 6 of 8 bodies (Fat_Female 4.00 to 3.35). South and north barely move: the base change is in the section, not in the outline. Fat south (4.79) is the worst; it is the bulging belly/breast outline, not touched here.

Read from the full renders (two render-and-fix cycles used):
- Better: the profile is smoother, no horizontal banding from the sprite steps, the chest reads as a plate and the torso as a block rather than a barrel (Hulk, Male, Thin_Female).
- Still wrong: Fat, Fat_Female, Thin_Female are still soft and uniform. The WDI breast lobes, the under-breast shelf and the belly folds are drawn lines and gradients, not silhouette, so a profile-only base cannot make them. Fat_Female south has a dark band at the fold but no lobes. Hulk has a hard shelf at the chest-to-abdomen row (a real step in the Hulk east profile, not a smoothing fault) and a bright pelvic plate on the north view. Residual faint banding remains on the north views. Legs are still the flat cut.
- The Hulk shelf was first suspected to be the cage floor; the fade did not change it, so it comes from the east profile.

Rejected, do not retry: final-Z smoothing; lateral or global envelope smoothing (both degraded east agreement and made normal artefacts near the neck). 

Recommendation for the step after: add per-body soft-tissue masses from the drawn shading that are not silhouette (breast lobes with the under-breast shelf, abdominal apron and fold, gluteal lobes), placed from the south/north landmarks as signed finite volumes with their own cross-section exponent, and score them by the lit render against the WDI texture's grey bands. Then rerun garment fitting on Male and Hulk first, whose base is good enough.

## Core + masses model with WDI-style capture (2026-11-09, `wdi3d.py`)

Requirement restated by Virginie: one 3D model per body type; captured from front, back and side it must give an image very close to the WDI sprite, and it must respect bone, muscle and fat. Anatomy references and the layer architecture are in `ANATOMY-LAYERS.md`. `wdi3d.py` is a new, self-contained pipeline; it does not replace the mesh export yet.

Model, per body (real WDI textures):
1. Profile: front and back edges of the east silhouette per row.
2. Core: polyline through the profile landmark rows neck, waist, leg bottom (front and back). This is the bone-bearing trunk.
3. Masses: what the profile shows beyond the core (chest or breasts, belly, upper back, buttocks). Thickness per row comes from the profile; the lateral footprint is a left/right lobe pair with a midline notch (sternum, linea alba, groin, spine, cleft), breasts as teardrop lobes from the apex and fold landmarks. Each row is rescaled so the model profile is exactly the east silhouette.
4. Zones: barrier diffusion, the thin dark strokes of the sprite are barriers, so a profile step (pec shelf, under-breast fold) sits on the drawn crease and not on a horizontal row.
5. Local signed patches of `shade3d.py` on top.
6. Fit to the drawing: a screened Poisson fit corrects the vertical slope until the top-lit capture has the sprite broad shading (a shadow becomes a change of volume across it, never a hollow; pull back to the volumes MU=0.001), then the depth of each drawn crease is adjusted until the captured ink has the painted tone.
7. East view: the side of the same solid (half-width visible at each depth from the front and back fields), then the same fit with the east sprite. The model is the intersection of the three height-field solids.

Capture shader (same for all bodies): white skin, light from the top of the sprite (tone = 1 - 0.5 x downward slope beyond 0.15), ink where the skin lies below its surroundings (cavity), constant black outline of the measured width, nipples painted.

Score: mean absolute luminance difference with the WDI texture inside the outline after a 2 px blur, then the same for a blank white body. Lower is better.

| Body | south | north | east | moved mean / p95 px (south) |
|---|---|---|---|---|
| Male | 0.021 / 0.085 | 0.028 / 0.057 | 0.026 / 0.070 | 3.71 / 6.92 |
| Female | 0.027 / 0.098 | 0.040 / 0.057 | 0.031 / 0.085 | 3.56 / 9.45 |
| Thin | 0.024 / 0.107 | 0.023 / 0.048 | 0.025 / 0.080 | 2.43 / 7.63 |
| Thin_Female | 0.018 / 0.106 | 0.040 / 0.080 | 0.021 / 0.082 | 3.72 / 7.48 |
| Fat | 0.025 / 0.114 | 0.034 / 0.052 | 0.026 / 0.082 | 5.88 / 14.96 |
| Fat_Female | 0.027 / 0.102 | 0.042 / 0.071 | 0.029 / 0.064 | 5.64 / 12.97 |
| Hulk | 0.023 / 0.082 | 0.027 / 0.055 | 0.033 / 0.076 | 5.37 / 10.65 |
| Hulk_Female | 0.043 / 0.097 | 0.040 / 0.081 | 0.035 / 0.084 | 8.08 / 18.05 |

The capture removes 60 to 80 % of the difference to WDI on south and east, 40 to 60 % on north. Boards: `Art/work/captures/2026-11-09_wdi3d-<Body>.png` and `2026-11-09_wdi3d-overview.png` (WDI | capture, three views).

Read from the boards: the captures are recognisably the WDI drawings (pec and breast folds, abdominal lines, navel, groin, scapula crescents, gluteal cleft, fat folds). Still wrong: grey wedges are lighter and softer than WDI; drawn strokes are thinner and sometimes broken; black blobs on the spine and cleft of several north views; faint horizontal row bands in some east views (Fat, Fat_Female); nipples are only a pink disc; Hulk_Female south is the worst (0.043).

Limits to state plainly: the creases and the shading are read from each sprite, so likeness is partly by construction; the three views are fitted separately and only tied by the shared profile and silhouettes; the fit moved the surface by the amounts in the last column. The mesh export and the viewer (`relief_export2.py`, `body3d.html`) still use the older fields; the fitted fields are saved as `out/wdi3d-<Body>.npz`.

Next: feed these fields to the mesh export and viewer; cure the north over-inking (joint fit of slope and crease, lower crease gain on the midline); sharpen the strokes (crease profile with a flat floor of the stroke width); then replace the generic lobes by the muscle and fat-pad volumes of `ANATOMY-LAYERS.md`, body by body.

### Likeness pass (2026-11-10, `wdi3d.py`)

The table and the "still wrong" list above describe commit `31198ca`. This pass changed the shader and the two fits; the core + masses base is untouched. One shader and one parameter set for the eight bodies.

What changed:
1. Creases and volumes are separated by scale. `closed(h)` fills every hollow narrower than `CLOSE` = 19 px to its rim (grey closing with a disc; hollows shallower than about 1 px are left alone, otherwise the closing lays square plateaus on smooth saddles). Ink = depth under that rim, black at `GROOVE` = 4 px. The slope tone is computed on the closed surface, so a crease wall never shades and a broad tilt never inks. The former cavity term (surface below its 6 px Gaussian mean) inked the base midline notches (spine, gluteal cleft) as wide blobs and left wide strokes grey.
2. Joint fit: `fit_shading` returns the closed surface, so a narrow hollow of the base (the bottom of the spine and cleft notches) that the artist did not draw is filled, and only the drawn strokes are carved back by `fit_grooves`. The broad part of each notch stays.
3. Strokes: the crease is carved on the stroke's own pixels (no blur), depth started at `GROOVE` x darkness and iterated per pixel against the raw sprite luminance (depth cap 16 px, needed where a stroke sits on a volume step). Flat floor of the stroke's width, black where the sprite is black. Thin pale strokes (luminance about 0.8: spine, cleft) are now selected too.
4. Grey: toon transfer. Measured on the sprites, the grey mode is luminance 0.85 (median of the greys 0.81 to 0.86) with a tail down to 0.55. Tone lost = 0.15 reached over 0.10 of downward slope beyond 0.15, then 0.5 per unit of slope, capped at 0.6. The fit steps in slope units through the inverse transfer, 24 rounds, target blur 0.5 px (was 1.0).
5. East: rows of the side field smoothed (sigma 2 px, rows only) and 256 lateral samples (was 96).
6. Areola: read from the sprite's pink patches (centroid, equivalent radius, median colour) and applied as albedo under the ink, in every view, so the drawn dark crescent shows.
7. `overview()` writes `2026-11-09_wdi3d-overview.png` at the end of every run.

Score (mean absolute luminance difference, lower is better), before then after:

| Body | south | north | east | moved mean / p95 px after (south, north, east) |
|---|---|---|---|---|
| Male | 0.021 / 0.012 | 0.028 / 0.013 | 0.026 / 0.013 | 5.39 / 9.21, 1.42 / 4.62, 4.18 / 9.62 |
| Female | 0.027 / 0.018 | 0.040 / 0.011 | 0.031 / 0.021 | 3.29 / 7.93, 5.10 / 10.27, 5.09 / 12.62 |
| Thin | 0.024 / 0.019 | 0.023 / 0.009 | 0.025 / 0.017 | 1.17 / 2.67, 1.38 / 3.80, 3.20 / 9.58 |
| Thin_Female | 0.018 / 0.011 | 0.040 / 0.015 | 0.021 / 0.015 | 4.21 / 8.14, 2.59 / 5.34, 2.40 / 7.80 |
| Fat | 0.025 / 0.022 | 0.034 / 0.009 | 0.026 / 0.015 | 6.94 / 17.28, 7.03 / 15.74, 8.42 / 17.98 |
| Fat_Female | 0.027 / 0.011 | 0.042 / 0.013 | 0.029 / 0.014 | 5.69 / 12.42, 8.12 / 22.56, 9.06 / 21.30 |
| Hulk | 0.023 / 0.012 | 0.027 / 0.013 | 0.033 / 0.014 | 8.50 / 14.82, 3.14 / 10.10, 7.57 / 15.98 |
| Hulk_Female | 0.043 / 0.013 | 0.040 / 0.016 | 0.035 / 0.016 | 7.93 / 16.34, 3.26 / 11.40, 8.96 / 19.43 |

"Moved" is the distance between the profile-built volumes and the fitted surface before the creases are carved (it now includes the filling of narrow base hollows). It is large on Fat, Fat_Female and both Hulks (p95 15 to 23 px on a 512 px sprite): there the lobes are too far from the drawn volumes and the fit does the work. That is the measure of how much anatomy is still missing from the base, not a success.

Read from the overview:
- Cured: the black blobs on the spine and cleft (all north views); strokes have the drawn width and reach black (under the pecs and breasts, east chest crease, fat folds); the nipple crescent shows.
- Better, not equal: grey wedges have the WDI tone and a harder edge, but are smaller than drawn in places (Fat east lower back, Hulk_Female south under the breasts) and their inner edge is still a short gradient.
- Still wrong: faint vertical streaks and small blocks in white areas whose base slope sits near the toon threshold (lower buttocks on Male, Thin_Female, Fat and Fat_Female north; lower half of Fat, Fat_Female and Hulk east; Hulk and Hulk_Female south chest). Thin south (0.019), Fat south (0.022) and Female east (0.021) are the weakest. A faint light line doubles some heavy strokes on Fat south (the lit lower wall of a step under the stroke).

Tried and rejected in this pass (do not retry as such):
- Closing with a square footprint and no depth gate: block-shaped plateaus everywhere.
- Toon step over 0.06 of slope: too sensitive, speckled whites; 0.10 kept.
- Fit stepping on the measured slope with a margin on each side of the toon step (white pushed 0.05 under the threshold, grey 0.03 over): diverges unclipped (Fat north 0.009 to 0.041); clipped to 0.15 per round it lowers some scores (Fat south 0.017) but bands the whites horizontally and loses wedges (Fat east, Male north). The score did not see it; the board did.

The fitted fields were not yet fed to the viewer at this point; see the next section.

### wdi3d model in the 3D viewer (2026-11-10)

Run: `wdi3d.py`, then `wdi3d_export.py` (writes `out/wdi3d-mesh.json`, not committed, about 5 MB, it is embedded in the viewer), then `uv run python body3d_build.py`. `body3d_build.py legacy` puts the older `relief3d-shade5.json` mesh back.

- Mesh: `relief_export2.one(body, fields)` now accepts the wdi3d fields. Rings, legs, landmark rows and the east-profile cap are unchanged; the south and north fields are the crease-free volumes `closed(field)`, measured from the wdi3d centre plane; the rib cage is computed for the skeleton but no longer pushes the skin; rings smoothed over 3 rows (was 6); vertices at 0.01 px (at 0.1 px the ring-to-ring slope noise equals the toon step).
- Creases and areolae: three 512 px maps per body (south, north, east), colour = areola albedo x (1 - ink), ink = crease depth under the rim of the fitted field. They are maps because the mesh has one vertex every 4 px across and the creases are 2 to 14 px wide.
- Material (`body3d_template.html`, three.js r128 `ShaderMaterial`): white skin; toon top light with the wdi3d transfer, computed from the view-space normal, light = top of the screen, taken relative to the body's centre plane (per-vertex `tilt` attribute; without it the leaning trunk shaded the whole lower belly grey); maps projected from the three sprite frames and chosen by the object normal (south or north by its sign, east where the normal is sideways); black rim from the normal and its screen derivative, sized to the sprite outline at the current zoom. The first mode of the viewer is now "modèle WDI (wdi3d)"; `relief` and `simple` are unchanged; organs are off by default.

Read in the browser (Male south, Fat_Female east and north; one render-and-fix cycle, used for the tilt and the vertex precision):
- South and north are recognisably the wdi3d captures: white skin, grey under the pecs and buttocks, drawn creases, navel, cleft.
- Still wrong: fine horizontal banding of the greys on the lower trunk (ring-to-ring normal noise against the toon threshold); the rim is ragged and uneven, thin or missing on flat flanks, never the constant 12 to 15 px sprite outline; the east view is poor (ragged silhouette, smeared crease map on the breast, greys that come from the south/north volumes because the east fit has no field in the mesh).
- Cannot be reproduced by this viewer as built: a constant-width outline inside the silhouette (needs a screen-space edge pass, not a material); the east fit (the mesh has two fields, the model three); creases as real geometry at this mesh density.

Housekeeping: `out/relief3d-shade5.json` and `out/body3d-compare/*.png` were modified in the worktree by earlier export runs of the old pipeline; they were restored with `git checkout`, not committed.

Next: the streaks and the large "moved" values have the same cause, the generic lobes. Replace them by the muscle and fat-pad volumes of `ANATOMY-LAYERS.md` for Fat and Hulk first (belly apron, gluteal lobes, pec and latissimus planes), so that the base already has white flats and down-facing facets where the sprite has them and the fit only trims. Then feed the fields to the mesh export.

## Research: soft tissue over the thorax (2026-11-08)

Question: how thick is the layer between skin and rib cage where there is no muscle, to set the depth of the skin on the cage. No source gives a direct skin-to-bone table for the thorax. What was found:

- Sternum, skin to bone, measured 1.5 cm under the sternal notch (intraosseous access site): 25 mm or less in 78 % of men and 90 % of women; men have more overlying soft tissue. [Wayne State digital commons](https://digitalcommons.wayne.edu/som_srs/70), summary in [core.ac.uk](https://core.ac.uk/works/40508558).
- Sternal bone thickness: manubrium 12.1 mm (men) and 10.4 mm (women); body 10.2 mm and 8.3 mm. [ajol.info](https://ajol.info/index.php/aja/article/view/129591/119166).
- Rib cortex about 0.9 mm (0.7 to 1.9 mm): the ribs are thin, the skin sits almost on the bone where no muscle covers it. [Holcombe and Derstine, J Anat 2022](https://deepblue.lib.umich.edu/handle/2027.42/175225).
- Lateral chest wall is thinner than the front: the 5th intercostal space at the anterior axillary line is 1.3 cm thinner on average than the 2nd space at the midclavicular line; high BMI predicts a thicker wall. [CT study of needle decompression sites](https://read.qxmd.com/read/22987168/radiologic-evaluation-of-alternative-sites-for-needle-decompression-of-tension-pneumothorax).
- Transverse thorax width: about 29.6 cm (men, 20 to 39) and 26.3 cm (women) on radiographs of Nigerian adults, smaller than Caucasian values per the authors. [study](https://search.bvsalud.org/gim/resource/en/biblio-1273428).
- Flaccid penis dimensions used earlier: Veale et al., BJU Int 2015;115:978 (9.16 cm length, 9.31 cm circumference, flaccid).

Not found: an adult anteroposterior-to-width ratio by sex; skin thickness over bare lateral and lower ribs; a rib-cage-to-skin table for the torso in forensic reconstruction (those tables are facial).

Consequences taken (estimates, not published measurements):
- Skin plus fat over a bare cage: 6 to 15 mm, set to 5 px minimum in the floor, at an assumed 5 px per cm (the torso is 190 px wide, about 36 to 40 cm: not verified).
- Testis size and the pec amplitudes (11 px male, 5 px female) are set by eye.

## Findings on the WDI data

- The WDI Male chest is deep: 165 px of depth for 190 px of width (0.87), against about 0.7 for a real thorax. Under the pecs the depth drops to 135 px.
- The WDI body top sits 70 px above the shoulder tip (stylised trapezius mass), so the sternal notch and clavicles are near the top, not at the shoulder tip (Virginie's correction).
- The first rib cage was too short (to nipple level) and followed the skin bumps. The 30th-percentile depth fit made it small. Both fixed.
- The floor moves 0 skin points on Male, a few hundred on some other bodies (console log, not mapped to bodies yet).

## Open

- Table of the gap cage to skin per rib level, for all eight bodies.
- These are torso–pelvis crops, not full figures: the source gives only 6 to 33 px below the crotch. Only the leg roots can be inferred faithfully. A complete leg model needs a procedural extension or full-body source views. Thin, Thin_Female, Hulk and Hulk_Female use a landmark-defined medial seam because their sprites have no crotch notch. The lower cut is closed by a flat mesh cap, not modelled as a leg or foot.
- Local runs use the real Workshop textures. The cloud checkout has no Steam Workshop tree, so there `relief3d.views()` falls back to a stand-in rebuilt from `captures/2026-11-03_points`; that is only for silhouette and landmark validation.
- Real-texture rerun: the mesh export, compare and render ran on the real textures on 2026-11-09. `heightmode.py all` and `garmentstudy.py all` are not rerun yet.
- Cloth surface as a low-pass of the volume; tucked and untucked rules; AB Pants; isoRim variant.
- Docs of section C3 (`docs/GARMENT-FIT-PROCESS.md`) exist only on remote branch `nelim/lucid-davinci-jsbif5`, not merged.
