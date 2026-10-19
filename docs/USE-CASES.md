# Use cases and backlog

What the mod has to look right on, per silhouette humaine WDI (Male, Female, Male_Thin, Male_Hulk, Male_Fat, Female_Thin, Female_Hulk, Female_Fat, Kid_Boy, Kid_Girl) and
per pass. A case is done when its captures were opened and read, not when the run is green.

## Covered by the gallery pass (`05-gallery.feature`, "ten bodies, four outfits")

| Case | State |
|---|---|
| T-shirt, no trousers | cut on the underwear's top edge; read |
| Bare torso, trousers | trousers start on the underwear's top edge; adult-content question open (PUBLICATION.md) |
| T-shirt and trousers | shirt runs 0.03 under the trousers' top edge; Female and Thin female were showing belly skin |
| Jacket on a bare torso | stretched to the trousers' hem; judged ugly (stair-stepped, artificially stretched); to replace by a THIGAPPE-style mask, no stretch |

## Covered by the legwear pass (`06-legwear.feature`)

Shorts (gap between the legs left open), skirt (nothing black under it). Not in the gallery yet.

## To add

- **Dress** (torso and legs in one garment): left alone by the cut; needs its own capture on every body.
- **Long coat and robe:** must keep draping; the mask must not shorten them.
- **Croptop** (Simple Pants and Shirts) and a short top: must never be lengthened, only cut.
- **Stockings and tights:** a layer on the legs, under trousers and skirts. Needs a mod that adds them; to find.
- **High heels:** change the foot and the leg line. Needs a heels mod (Workshop "high-heels" was seen on LoversLab, not checked); to find.
- **"Realistic" clothing:** garments drawn for a realistic body (WDI's own apparel folders: Blouse, CasualTShirt, ChefsUniform,
  Jumpsuit, MilitaryUniform, Scrubs, SheriffShirt, ShirtFleece, ShirtandTie, TankTop, Tunic, BodyStrap, CorsetRoyal, EltexShirt,
  ShirtBasic, ShirtButton, TribalA, dress, VestRoyal). Native art is now cut as it is for shirts; each of these needs a capture.
- **Other types found in the clothing libraries** (Smaller Shirt Textures, Simple Pants and Shirts, Useless clothes, Xeva Body Pants,
  retextures of visible pants, female variants for fat bodies): one capture each per body once the cut works for them.
- **Children:** no WDI underwear; the cut line is the one the child's trousers start on. Needs a child in a dress, a jacket and shorts.
- **Later (expansion):** pregnancy belly, breasts, penises, body hair; the cut line stays replaceable
  (`ShirtCut.CutFraction`, `ShirtCut.LineFor`).

## Mods the Sanctuary needs for these passes

TailorMade, WDI's Realistic Bodies, Female Body Variants Continued, Female Apparel Variants Continued, AB's Visible Pants, and this mod.
Female Body Variants must load before WDI (its own `Naked_*_Female` files are copies of the base bodies and would shadow WDI's),
TailorMade after the body mods (`last:astryl.tailormade` in the pass map).

## Clothing libraries to test (given by Virginie, read from the installed Workshop folders, not yet captured)

- **ZX's Apparel for [NL] Realistic Body**, Workshop 3604442772, `zx.apparel.realisticbody`, needs `Nals.RealisticBody` ([NL] Realistic Body)
  and Harmony. About 25 garments with art for Fat, Female, Hulk, Male and Thin in three facings (Gothicdress, Gowndress, Hoodie,
  Maiddress...). The art is drawn for [NL]'s bodies, not WDI's: to see what the cut does on them, and whether they belong in the
  WDI passes at all (to find).
- **UNAGI Royalty Apparel**, Workshop 3352990362, `UNAGI.Ap.Dress`: Royalty noble dresses and clothes (about 12 apparel defs plus
  headgear; folders `UNARoyalDress`, `UNA_Dress_sitagi`, `UNA_RoyalRobe`...). Given for Compatible Body 2, Erin's and Unagi's bodies.
  Dresses: to capture on every body, as in "Dress" above.
- **[IMO] Default Apparel Retexture** (Sato Imozou), Workshop 2660249018, `SatoImozou.IMOZOUapparel`: retextures vanilla apparel
  (258 images under `Things/Pawn/Humanlike/Apparel`). Given for Imozou's bodies. To capture on every body, with and without the cut.
- **Chibi Body**, Workshop 2187064189: given by Virginie, not installed here, not read yet.
- **Ratkin Apparel+ (unofficial)** (PPONN), Workshop 3247891238, `PPONN.RatkinApparel`, needs Humanoid Alien Races and Harmony: apparel
  for Ratkin, 70 images. A race of its own, so a body of its own: to find out whether the cut and the trousers mean anything there.
- **Not read, not installed here:** Chibi Body 2187064189 and "abc" 3459200778. Steam answered 429 to the page fetch.
- **UNAGI family** (Virginie: "à noter"). Installed here, read by name only: UNAGI Vanilla Apparel 3245977854 (`UNAGI.apparel.B.Zibunyou`),
  Mini MOD SimpleSuit 3253298952 (`UNAGI.suit.SET`), Winter clothing 3266399912 (`UNAGI.huyuhuku.SET`), Japanese Assortment 3297676809
  (`UNAGI.Wahuu.hako`), Battle Coat 3301577366 (`UNAGI.Battle.coat`), CAFE 3325530853 (`UNAGI.Cafe.gohan`), Royalty Apparel 3352990362,
  and Apparel APP Extension 3379688555 (`InternSeraph.UNAAPPExt`, by another author: it reads as a patch for the APP/THIGAPPE pattern
  system, to check). **"Unagi coat" 3253300748, given by Virginie, is not installed here: not read.** Coats are the cases where the
  cut must leave the garment long; each needs a capture.
- **ATH's Retexture Female Apparel** (Anthitei), Workshop 3145326932, `Anthitei.ATHsRetextureFemalApparel.Retexture`: retextures women's
  versions of vanilla apparel (Apron, Blouse, Cape, CasualTShirt, Hoodie, Overalls, PeltCoat, SheriffShirt, ShirtFleece, ShirtandTie,
  TankTop, TribalKilt, TribalPoncho, Tunic; 116 images). Given by Virginie for "compatible" bodies. To capture on the female bodies,
  with and without the cut.
- **[SS]Maid Project** (BJInternetSupervision), Workshop 1498756997, `BBIS.MaidProject`, 1.6 supported, 437 images, no body textures
  (apparel and buildings only). Given by Virginie as "female BB": maid outfits, dresses and aprons; to capture on the female bodies.

## Compatibility passes to run (Virginie, 2026-10-08)

- **Venus beside THIGAPPE and Apparel Paper Pattern** (`WRK.THIGAPPE` 2839518933, `nalsnoir.ApparelPaperPattern` 2480887589): pass map
  `Tests/Pickle/wsl-deps.thigappe.map`, same gallery feature. Declared incompatibility of THIGAPPE: `nalsnoir.APPCompatibleBody2` only.
  Question: who cuts the shirt, and does the same garment get cut twice. Also with the ABC Body 2 patch (3611523059) and
  APPBodyTypeOverrider, not prepared.

## Direction (Virginie, 2026-10-08)

The aim is not to load THIGAPPE but to do for WDI's bodies what THIGAPPE does for its own: fit every garment to the body automatically.
The THIGAPPE passes (6d97, a107) stay as a diagnostic only. What Venus does today: draws AB's trousers per sex, cuts the shirts WDI
draws for each body. What it leaves to TailorMade (lost without it): garments that have no art drawn for WDI's bodies, which
must be resized to the silhouette. That generic refit is the gap to close, and the retextures (ATH, IMO) and the plain vanilla
garments are the first cases to test it on.
- **Keep APP, drop THIGAPPE** (Virginie, 2026-10-08). `nalsnoir.ApparelPaperPattern` is the engine; THIGAPPE is a content pack for it
  (per-body mask textures, e.g. `Textures/Things/ApparelPaperPattern/Human/Female/Armor/Female_cmask_bottom_cover_south.png`, in its
  `1.6/Mods/RealisticBody/` for [NL]'s bodies, and pattern defs patched in by XML). Venus would be the same kind of pack for WDI's bodies:
  masks generated at runtime from the alpha silhouette of the player-installed WDI naked bodies and the pattern defs, so APP can clip every garment of any
  mod, and Venus keeps only AB's trousers. The first vertical slice registered runtime-only alpha masks for all ten WDI profiles and
  APP `OnSkin` patterns; APP Utilities supplied the gender predicate which distinguishes Thin/Fat/Hulk women. Its 2026-10-09 capture
  showed a full-height shirt hiding same-layer trousers. The corrected slice gives the shirt the whole WDI silhouette and clips only
  the trousers at the waist. the 2026-10-09 `@facings` run (green 2/2, evidence deleted 2026-10-19) showed in its east/north captures the four starter
  defs without a waist gap on all ten profiles. The setting remains opt-in because Middle/Shell, burns and dresses are not covered.

### Couches APP à traiter, après la preuve OnSkin

Le contenu THIGAPPE installé ne réduit pas les vêtements à une seule couche :
sa bibliothèque de patterns contient 346 entrées `OnSkin`, 222 `Shell`, 215
`Middle`, puis des couches de tête/accessoires (`Overhead`, `EyeCover`, `Belt`)
et de sous-vêtements (`UnderwearTop`, `Underwear`). Ces nombres décrivent son
corpus, pas un objectif de copier ses assets. Pour WDI, l'ordre est donc :

1. `OnSkin` — hauts proches du corps, validés par le premier rendu APP ;
2. `Middle` — gilets et robes courtes, à vérifier sur les bustes WDI avant de
   les masquer ;
3. `Shell` — manteaux, dusters et robes longues, qui exigent un masque/burn ou
   une exemption afin de préserver le drapé ;
4. sous-vêtements et couches ajoutées par d'autres mods — seulement après un
   cas de rendu dédié ; les couches inconnues restent ignorées.

## Findings of 2026-10-08 on the UNAGI dresses (wardrobe-3, zoomed on Fat, Female and Hulk women)

- The bust of the dresses does not follow WDI's chests. The dress is drawn for an ordinary chest: a flat corset line and a neckline at a fixed height,
  while WDI's women have large, low chests (Fat, Hulk) that the dress ignores; on the bare body the breasts show a different outline from the dress's.
- Fat woman: the skirt flares well beyond the body's outline and the bust line sits high; the dress reads as a separate shape put on top.
- What fits well: the hem and the shoulders on Thin and Female.
- To do: a refit of torso garments that have no WDI art, row by row on the body's silhouette (the technique TailorMade describes as "per row warp",
  MIT licence), with the chest outline taken from the naked body texture. The chest is also the first element of the expansion roadmap (breasts).
  Cases to keep: UNAGI Royalty, Battle Coat, Maid Project (Thin and Female), any dress.

## Backlog

- **Underwear covers.** A pawn wearing underwear shows less: the men's sex, the women's nipples. Look at the underwear layer of every wardrobe sheet (men: below the waist; women: chest) and compare it to the bare row. The underwear seen under coats in the refit run without TailorMade (refit-notm) has no known source yet; find it first.
