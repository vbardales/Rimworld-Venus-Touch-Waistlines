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
| `transfer-proto/fable-crack/body3d_build.py` | Rebuilds `captures/2026-11-08_body3d.html`, automatically replacing the shaded dataset with the latest export. |
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
