# Changelog

## [Unreleased]

Targets 1.0.0, the first public version.

- **Renamed Venus Touch Waistlines**, `packageId` `nelim.venustouch.waistlines` (the
  private 0.1.0 item carried the old name).
- **New option: fit tops to the body's silhouette** (off by default). With a WDI body, every
  garment worn on the skin that covers the torso but not the legs is cut along the outline
  of the body, so a shirt drawn for another body no longer sticks out at the shoulders and
  the collar. Colours and hem are kept; garments TailorMade fits itself are left alone.
- **TailorMade is optional.** Every reach into it goes through one link; its bands and
  resizing are patched only when it is loaded, and the band sliders show only then.
- **Trousers start on WDI's underwear**, column by column, instead of a fixed band;
  female Thin, Fat and Hulk get their own copy of AB's shell; Fat trousers keep AB's full
  width; the gap between the legs is painted, not cut; the low-resolution silhouette is
  softened; children's trousers have their own drop.
- **Shirts end just under the trousers' top edge**, every facing, so no belly skin
  shows: cut on WDI's own art for Fat and Hulk, compressed into the band elsewhere;
  jackets and other shell-layer torso garments stay full length.
- **Dresses drawn for the body are left as they are** (setting, on by default), and the
  bodice of the royal dress is fitted to the breasts of WDI's bodies.
- **Experimental, off by default: outline of vanilla trousers on WDI's ten bodies.** The
  vanilla trousers are drawn as a blue outline, interior left empty, cut on the installed
  WDI art (no WDI texture is shipped), to show where vanilla garments stop fitting. The
  trousers line follows the panties or boxers line, chosen per body and per view (front,
  side, back), and the outline also surrounds the open triangle between the legs. The
  matching red hem outline of a top is drawn for a test garment only, never shipped.
  Skipped when Apparel Paper Pattern is active.

## [0.1.0] — 2026-09-23

Prepublished to the Workshop as item 3806769245 on 2026-09-23, private: Steam creates
every new item private, and RimWorld never calls SetItemVisibility. `Mod/About/PublishedFileId.txt`
carries that id and is committed - lost, the next upload would create a second item instead of
updating this one, and that is not recoverable.

The mod was rebuilt twice before it settled. Only the last shape is loaded; the
two earlier ones are kept locally under `Parked/` (not in this repository) with a README saying what each
answered and how to bring it back.

### The mod as it stands

- **Trousers that read as trousers, where AB's Visible Pants supplies them.** AB
  draws a plain shell. Two options, on by default and read at startup: use
  General Textures Collection's retexture of the same garment, read from
  General's own folder because its LoadFolders never loads it with AB active, and
  draw a waistband, a fly and seams onto the shells General has nothing for (the
  child, mainly). Registered in this mod's own content; nothing shipped, nothing
  copied. General's `_Female` files are registered too, for Female Apparel Variants.
  Two sliders lower what this supplies by a fraction of its height, one for adults (0.03) and one
  for children (0.067), chosen by eye on captures, because a child is drawn smaller.
  For each body type it supplied art for, TailorMade is told to leave the trousers alone (a
  pattern def made in code, so the condition is that this mod really supplied the art); with
  both options off, or without AB, TailorMade fits them and follows the pants slider as before.
  Only `Pants` is covered. `Tests/Check-Trousers.ps1` runs the generator
  without the game, on synthetic shells and on all eighteen of AB's.

- The settings window is fully translatable: 13 `Keyed` keys in English and
  French, no sentence left in the code. The mod's own name, in the settings
  category, is the one literal.
- A shortcut in the main button bar, hidden by default, opens the same settings
  for RIMMSQOL and other customisation mods. Nothing shows until one reveals it.
- Settings read back from the config file are clamped to their sliders' ranges;
  NaN and infinity fall back to the default. The window scrolls, and each slider
  has a tooltip.
- `Tests/Check-Localization.ps1` and `Tests/Check-Settings.ps1`, neither of which
  starts the game.

- The three bands TailorMade fits garments into — pants `(0, 0.58)`, boots
  `(0, 0.20)`, chest `(0.45, 1)` — become settings, through a postfix on
  `ApparelClassifier.BandFor`. This corrects every leg garment of every mod at
  once. The defaults are TailorMade's own values, so installing the mod changes
  nothing until a slider moves.
- A prefix on `TexBake.BakeFitted` does the same job where the band arrives, in
  case Mono inlines the small method above it. It only rewrites a band still
  holding its stock value. A self-test at startup reports in the log which of
  the two is active.
- An option, off by default, lifts `ConfirmChestArt` so that a shirt drawn over
  the whole body counts as a chest piece and can be shortened. The band scales
  the art rather than cropping it, so the shirt is compressed.
- Closing the settings window calls `TailorMadeCache.ClearAndRepaint()`.
- `Tests/Check-Mod.ps1`: 22 checks by reflection over TailorMade's assembly,
  none of which start the game. It catches the way these patches fail — in
  silence — if a method is renamed or a band constant retuned.

### Parked, and why

- **Generated pants.** 27 textures, nine body types by three facings, each cut
  to its body's silhouette by `_tools/make-garment.js --auto`: Kas's garment
  mapped row by row onto WDI's body, waistband at 0.32 of the body's height,
  outline 2px against the body's own 13. With a patch filling `wornGraphicPath`
  on `Apparel_Pants` and `Apparel_KidPants`, and a `TailorPatternDef` telling
  TailorMade to leave both alone. Set aside once the brief became *automatic,
  no retextures*: the fitting must be computed at render time, for every
  garment, not drawn in advance for one.
- **Hand-painted masks.** The first design of all: a mask per body type handed
  to TailorMade in place of the body silhouette, painted in GIMP over a project
  `_tools/gimp-project.scm` builds.

### Measurement tools, kept

`_tools/` holds what the two parked routes were built on, and what settled
several arguments: silhouette overlap between body retextures, where the navel
sits, where a waistband sits, how heavy a drawn outline is. No dependency
beyond Node — `png.js` reads and writes PNG by hand, including greyscale and
16-bit sources, which several body mods turn out to use.
