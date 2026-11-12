# How other mods fit a shirt to a legless body (read 2026-10-06)

Question: on WDI's Realistic Bodies (legless) the trousers are drawn from AB's shells, and a vanilla shirt, drawn over the whole body, hides them.
TailorMade bands a torso garment into a horizontal band, which squeezes the whole shirt, shoulders included. What do the other mods do?

Everything below was read in the Workshop folders on this machine (`steamapps/workshop/content/294100/<id>`), except where marked.

## The two families

| Family | Mods | What it does to a shirt |
|---|---|---|
| Cut with a mask | Apparel Paper Pattern (2480887589), THIGAPPE (2839518933), THIGAPPE Masking Patches (3344769721), UNAGI APP Extension (3379688555), THIGAPPE ABC Body 2 Patch (3611523059), Yuran Race THIGAPPE Addon (3573526343), Xeva Body Patch (2846970684), APP for Compatible Body 2 (2480905277) | The garment is cut with a prepared mask image, one set per body type. Nothing is resized. |
| Move or scale the whole garment | [UY] Apparel Race Renderer (3758410877), Layered Apparel (3632480044) | Offset, scale and rotation per facing, by hand. The shape is not changed. |

No mod read here squeezes only the lower half of a shirt.

## AbsCon Dynamically Cropped Apparel (gitgud.io/AbstractConcept/abscon-dynamically-cropped-apparel)

Closest to what is wanted, and simpler than what this mod does. Source cloned and read (`GraphicMaskingUtility.cs`, `ApparelTexture2DPack.cs`; 339 lines, 1.5, no licence file found).

- The top of the shirt is kept as drawn. Everything below a line is **erased**, by a mask named `Masks/apparel_shirt_mask_<BodyType>_<facing>`, one per body type and facing.
- Per pixel: mask white keeps the pixel; mask alpha 0 clears it; otherwise the darker of the two. The bottom is a clean cut with a proper edge.
- A patch on the visible-pants mods (`HarmonyPatch_VisiblePants`) applies it to garments that must end under the trousers.
- Consequence for this mod: no blur, no squeezed shoulders, and the cut line can differ per body (and per sex) without touching the width.

Licence: none stated. Take the idea (cut with a generated mask), not the code, and say so in ATTRIBUTION.md if it is used.

## What this mod does today, and its defects (runs 600b and 75fa)

- TailorMade's chest band squeezes the whole shirt into 0.25 to 1, shoulders included: Hulk's shoulders then show bare.
- `JacketArt` (commit after d12c2ac) redraws a shirt by compressing only its lower half. Better shoulders, but the compression has no interpolation: a blurred, toothed fringe at the hem on Fat, Female and Thin female.
- Jackets (shell layer) are stretched down to the trousers' hem; stretched rows are not smoothed either (stair-stepped edge).

## Other mods read

| Mod | Id | Relevance |
|---|---|---|
| TailorMade Unlock Fix | 3769650943 | HAR race apparel restriction toggle only. None. |
| Smaller Shirt Textures | 3169180308 | Redraws vanilla shirts smaller (123 textures). The only one that touches shirt art. Hem measured 2026-10-06 (fraction of the picture from the top, south, against the top of AB's raw trouser shell): Male 0.73 vs 0.70, Female 0.66 vs 0.69, Thin 0.68 vs 0.69, Fat 0.82 vs 0.71, Hulk 0.85 vs 0.80. So it already reaches about the trousers on Male, Thin and Hulk, stops 0.03 short on Female and runs 0.11 below on Fat. The best base for a cut: a cut at the trouser line is then small. |
| Simple Pants and Shirts | 3795174803 | Adds a V-neck tee, a croptop, a logo shirt; better pants art. The croptop is a short top (hem 0.58 to 0.67 of the picture, well above the trousers at 0.69 to 0.80): a test case for any "bring every shirt down to the trousers" rule, which must not lengthen it. |
| Simple Skirt | 3029003553 | A skirt with its own art: a second skirt test case. Defs not read. |
| AB's Visible Pants | 2986402536 | The shell source. Picks art by a keyword in the def name (Pants, Skirt, Trousers, Jeans, Shorts_Pants). `VAE_Apparel_Shorts` matches none: no art unless added by hand as TargetApparel. |
| [XND] Visible Pants | 2264108215 | The other pants supplier; this mod leaves its textures alone. |
| Pumpkinlass Visible Pants Retexture | 3772689105 | Pants and jeans art for XND or AB, all bodies including Fat female. |
| Visible Pants Retexture (catMonke) | 3671309201 | 512 px pants art, VAE included. Loads after AB. Which wins on `Pants_<Body>_<facing>` not tested. |
| Pawn Visible Pants / VAE Patch | 2985986536, 3799793039 | Pants, flak pants, kid pants; trousers, skirt, shorts, jeans for VAE. |
| Medieval Visible Pants Addon | 3707481634 | Pants for Medieval Overhaul. |
| [PL] Female Variant Clothing: For Fat Bodies | 3771446780 | Female variants of apparel for Fat, plus a new Fat body. Brings its own waist height: the Fat female is not served by this mod's single table. |
| TY Slender Female Body (B18) | 1349843576 | Replaces the Thin body with a slender female one, and the basic apparel. Conflicts with WDI on Thin if active. |
| StylistMade, FaceMade | 3744238014, 3744805284 | Hair and faces for HAR races. None. |
| Dubs Apparel Tweaks, AB's Head Apparel Tweaker | 2296697286, 2990606008 | Hats. None. |

Installed on the second check, all read: Xeva Body Pants (3503852086, pants for the Xeva body, 587 textures), Better Button-down Shirt And Pants (3367585685, stats only), VFE Light Tribalwear is pants (3794730286, moves a garment from the torso slot to the legs slot, so TailorMade classes it as pants), Useless clothes (2683996253, apparel with art, 146 textures, not read in detail), PawnRenderExport (3644533685, a render export tool, no art), [IMO] Default Apparel Retexture (2660249018, apparel drawn for one custom body only: male, female and thin, does not fit vanilla or other bodies). None of them fits a shirt to a legless body. Page not readable then (Steam 429) and now installed: 2660249018.

## Navel and body findings (scripts/measure-navel.js, extended to the female variants)

Navel row as a fraction of the body, from the bottom:

| Body | Fraction |
|---|---|
| Female | 0.52 |
| Male | 0.48 |
| Thin | 0.58 (the detector lands on the pectorals: the male Thin has no clear navel on this drawing) |
| Fat | 0.46 |
| Fat female | 0.51 |
| Hulk | 0.48 (same caveat) |
| Thin female | 0.31 |
| Hulk female | 0.32 |

Thin and Hulk have a separate female body; AB has one pants shell for each, shared by both sexes. A per-sex trouser height therefore needs a second texture made for the female pawn (the `_Female` path suffix, which this mod already registers but only for non-shells). Male Thin and male Hulk navels have to be measured by hand.

## Proposed next step (not done)

Replace the lower-half compression of shirts and jackets with an AbsCon-style cut: a mask generated per body and facing from the top edge of AB's trouser shell for that body, white above it, transparent below. Hem ends under the trousers, top untouched, no resampling, so no blur. Needs the per-sex heights above to be right for Thin and Hulk.

## Update 2026-10-06 (second pass)

- All the mods listed as missing were downloaded later and read: none fits a shirt to a legless body; AbsCon's mask cut stays the only model.
- Smaller Shirt Textures draws shirts nearly to the trouser line already (hems above). With it active, a cut mask would remove little; without it, vanilla shirts run the whole body.
- Not read in detail: Useless clothes (2683996253, 146 textures), Xeva Body Pants (3503852086).
- Open decision: which shirt source the gallery uses (vanilla, or Smaller Shirt Textures).
