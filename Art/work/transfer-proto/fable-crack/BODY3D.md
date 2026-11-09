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
4. Body-specific anatomy: female breast patches are asymmetric teardrop supports bounded by each own attachment crease and a central cleavage return to the cage; their local maximum lies below the apex landmark and a medial gate preserves the sternal skin plane. Fat and Fat_Female add a soft low pubic apron, a lower soft chest and larger gluteal patches; Hulk and Male/Average receive paired upper and lower abdominal pads with a finite linea alba. On the back, a broad upper spinal sulcus joins a capped lower sacral/intergluteal cleft rather than a neck-to-crotch zip. Attachment, inguinal and pec creases follow short rounded arcs rather than unbounded rows. East-view patches make a deliberately small signed correction to the front/back mesh sections before the hard profile cap. White/grey paint remains paint unless a landmark asks for a form.
5. Mesh: front ring from the south field, back ring from the north field, joined at the silhouette edge. The assets end just below the crotch; their lower rings are a cut edge, not a reconstructed leg. Where a sprite has a crotch notch, its two alpha runs define two cut rings; otherwise, the named crotch starts an internal medial seam with the outer source projection unchanged.
6. Skeleton (viewer): every bone is placed from the skin by a ray from the row axis and a margin under it.
   - Rib cage: rigid barrel of 12 ribs, from the neck base (20 % of the way from the body top to the under-breast fold) to just above the navel (85 % of the way from the nipples to the navel). Depth fitted per level on the centre-line skin (7 px margin in front, 12 px behind), smoothed over 5 levels. Width from the 40th percentile of the side margins.
   - Sternum: a straight line fitted by least squares on the centre-line skin, lifted to the 60th percentile of the residuals.
   - Clavicles under the neck skin (Virginie: the clavicles sit under the skin of the neck), from the notch to 10 px above the shoulder tip.
   - Spine at 30 % of the depth from the back skin (at least 14 px); scapulae and iliac wings as plates; sacrum, pubis, femurs.
7. Floor (export): where there is no muscle the skin rests on the cage. After the cage is built, any skin point in front of or behind the cage is pushed out to at least 5 px from the cage surface. The export records the number of displaced points in each body's `cage.moved`; the viewer is diagnostic and never changes its input mesh.

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
- The cloud checkout has no Steam Workshop tree. For repeatable validation, `relief3d.views()` uses the real WDI texture when available and otherwise rebuilds a local stand-in from `captures/2026-11-03_points` and the committed `E_<Body>_<facing>.png` masks. This is adequate for silhouette/landmark validation but not a substitute for rerunning on the original Workshop PNGs.
- Real-texture rerun of the cloud scripts (`heightmode.py all`, `garmentstudy.py all`).
- Cloth surface as a low-pass of the volume; tucked and untucked rules; AB Pants; isoRim variant.
- Docs of section C3 (`docs/GARMENT-FIT-PROCESS.md`) exist only on remote branch `nelim/lucid-davinci-jsbif5`, not merged.
