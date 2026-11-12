# Using TailorMade Waistlines in another mod's gallery pass

For a mod session that wants its pawns dressed correctly on WDI's Realistic Bodies (trousers, shirts, jackets that fit every body type
and sex). Written 2026-10-07, for commit `59a1bd5`. The work is not published: this is the development build, loaded by path.

## What to load, in this order

| Order | packageId | Workshop id | Why |
|---|---|---|---|
| 1 | `brrainz.harmony` | 2009463077 | patches |
| 2 | `tiagocc0.FemaleBodyVariants` | 3798082132 | Female Body Variants Continued: must load BEFORE WDI, its `Naked_*_Female` files are copies of the base bodies and would shadow WDI's |
| 3 | `tiagocc0.FemaleApparelVariants` | 3799726535 | Female Apparel Variants Continued |
| 4 | `WDI.Realistic.Bodies` | 3527486510 | the bodies and their own shirts and underwear |
| 5 | `AB.VPLRF` | 2986402536 | AB's Visible Pants: the trouser shells |
| 6 | `astryl.tailormade` | 3756915448 | TailorMade, AFTER the body mods (`last:astryl.tailormade` in the pass map) |
| 7 | `nelim.venustouch.waistlines` | none (private) | this mod: `VenusTouchWaistlines/Mod/` (assembly `Mod/Assemblies/TailorMadeWaistlines.dll`, 40.5 KB) |

Pass map lines (the Pickle staging understands `last:`):

```
tiagocc0.FemaleBodyVariants    3798082132
tiagocc0.FemaleApparelVariants 3799726535
wdi.realistic.bodies   3527486510
ab.vplrf               2986402536
last:astryl.tailormade
```

Plus the Sanctuaire mods of the gallery pass (`screenshotstudio`, `colonistrace`, `camerazoom`, `stagedecor`, `clearscreen`, `clickdiagnostics`):
see `Tests/Pickle/wsl-deps.gallery.map`, the model. To load this mod itself the pass map needs its `Mod/` folder; the staging takes the
mod under test from its repo, so a foreign pass needs a line `nelim.venustouch.waistlines   path:VenusTouchWaistlines/Mod`.

## The settings that matter (config seed `Mod_local-nelim.venustouch.waistlines_TailorMadeWaistlinesMod.xml` when this mod is a `path:` dependency of your pass; `Mod_TailorMadeWaistlines_...` only in this repo)

Copy `Tests/Pickle/for-acs/config/galerie-tmw/` into the pass's `config/`; when this mod is staged by `path:` its seed is named `Mod_local-<packageId>_TailorMadeWaistlinesMod.xml` (staging script, folder `local-<packageId>`), not by the repo name. In particular: `shortenShirts` True (cuts shirts on WDI's underwear and
leaves TailorMade out of it for those bodies), `keepJacketsLong` False (jackets are drawn as they are), `detailPlainShells` True,
`trouserDrop` 0.03, `trouserDropChild` 0.067. AB needs its own seed (`Mod_2986402536_ABsVisiblePantsMod.xml`, same folder).

## Known limits

Children have no WDI underwear, so their line is the one the trousers start on. Dresses, long coats, croptops and stockings and heels
are not covered yet (`docs/USE-CASES.md`). Hulk female shirt has a neckline hole drawn by WDI on purpose.
