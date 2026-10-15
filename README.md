# Venus Touch Waistlines

Decides where garments stop on the body. An add-on to TailorMade, which is
MIT, and not affiliated with it.

Meant for release. Only `Mod/` is uploaded, and it holds nothing but this
project's own work — see [ATTRIBUTION.md](ATTRIBUTION.md). `Parked/` never leaves
the author's machine and is not in this repository: it carries textures derived
from art that grants no licence.

It began as a set of pants cut to one body's silhouette, under another name. It
ended as three numbers that fix every leg garment of every mod at once, which
is why both the name and the packageId changed before anyone had them.

## The problem

TailorMade sorts apparel into classes and fits each class into a horizontal
band of the body's alpha bounds — 0 at the hem, 1 at the top of the head:

| class | band | meaning |
| --- | --- | --- |
| Pants | `(0, 0.58)` | the bottom 58% |
| Boots | `(0, 0.20)` | the bottom fifth |
| Chest | `(0.45, 1)` | the top 55% |

In `TexBake.BakeFitted` the target rectangle is literally
`AlphaBoundsUVInBand(body, band.x, band.y)`, so a band's edges are where the
garment's edges land. Those numbers suit a body drawn with legs. On a body
retexture drawn as one legless shape, 58% of the way up from the hem is above
the navel, and trousers read as a high-waisted skirt.

Nothing in TailorMade exposes them: they are `static readonly Vector2`
constants, and its settings do not mention them.

## What this mod does

Two Harmony patches, a settings window, and a step at startup that gives AB's
trousers better art than the plain shell they ship with. No texture is shipped:
what that step uses is read at run time from what the player already has. The
one def is a hidden shortcut to that window (below). English and French text,
as `Keyed` files.

**The bands become settings.** A postfix on `ApparelClassifier.BandFor`
returns our values instead of the constants. That is the better of the two
places to patch, because TailorMade builds its texture cache key from the
band's value — so a band changed at the source invalidates the cache by itself
and no stale texture survives.

**A fallback, on purpose.** `BandFor` is a small static method returning a
switch over static fields, which Mono may inline into its caller; an inlined
method is one Harmony has nothing left to patch. So a prefix on
`TexBake.BakeFitted` corrects the band again where it arrives, in a method far
too large to be inlined. It only rewrites a band still holding its stock value,
so when the first patch worked this one does nothing. A self-test at startup
says in the log which of the two is doing the work:

```
[TailorMade Waistlines] band patch active on ApparelClassifier.BandFor.
```

**An option for shirts.** TailorMade only bands a torso garment once
`ConfirmChestArt` has seen that its art already starts 40% of the way up the
texture. The test is sound — it stops the mod squashing a garment never drawn
as a crop top — but it excludes exactly the garments that need it: a vanilla
shirt is drawn over the whole body, so it stays full length and hides the
trousers whatever the trousers do. Its author says in the tooltip of the setting it guards what the test is for:
"long coats and capes that drape down the body are left full-body" — which is
right, and is why the option cannot simply lift it. A postfix lifts it for
**on-skin garments only**: vanilla is consistent here, shirts and tribalwear
being OnSkin while dusters, parkas, jackets and robes are Shell. Off by
default, and note that the band **scales** the art into itself rather than
cropping, so the shirt is compressed, collar and buttons included.

**Trousers that read as trousers.** AB's Visible Pants draws its trousers as a
bowl: an outline and an even fill, with no waistband, no fly, no seam. On a body
drawn without legs that bowl is all there is, and it reads as a shell. Two
options, both on by default and both applied at startup, act only where AB is
the mod supplying a texture. First, General Textures Collection carries a
retexture of the same garment with the details, at `Mods/VisiblePants/`, but
its `LoadFolders` only loads it when XeoNovaDan's Visible Pants is active; with
AB active instead it never reaches a pawn. `TrouserArt` reads those PNGs from
General's installed folder and registers them in this mod's own content, which
the game consults after AB's because this mod loads later (`ContentFinder` walks
the running mods from the last back). It also registers General's `_Female` files
(`Pants_Fat_Female`): Female Apparel Variants adds no body type, it asks for the
same path with `_Female` on the end for a female pawn of a body type both genders
share, when a texture exists there. Second, where General has nothing - it has
no child, and no jeans, shorts, skirt or suit trousers - `TrouserDetail` draws a
waistband, a fly and seams onto AB's own shell and parts the legs at the bottom.
It is a pure function on RGBA bytes, so it is tested without the game. It draws
only by multiplying the colour already there, because the game tints these
textures with the garment's colour. Two more settings, `trouserDrop` and
`trouserDropChild`, move whatever this step registers down the body by a fraction of the
texture's height, never cutting the garment. There are two because a child is drawn smaller,
so the same fraction is fewer pixels on screen. The defaults, 0.03 and 0.067, are what a
player chose by looking at captures at 1080p and the closest zoom, women and a girl; nobody has
yet looked at a man. A measurement that tried to hit a number of pixels put the child at 0.20,
which the eye rejected. All are read at startup. Only `Pants` is covered; the other four
garment folders AB ships are untouched.

That art is already drawn for the body, and TailorMade would stretch it into its band, which
is how a plain shell became a bucket up to the chest. So for every body type this step
supplied art for, `TrouserArt` creates a `TailorPatternDef` with `ignore` set, and TailorMade
leaves those trousers alone. It is made in code and not shipped as XML because the condition
that matters is that this mod actually supplied the art, which a def in a file cannot know.
With both art options off, or without AB, no def is made, TailorMade fits the trousers as it
always did, and the pants slider applies. The registry is read once, at the first pawn
rendered, long after the def is added.

**WDI APP prototype, opt-in.** Venus generates in-memory category masks for
each of WDI's ten human visual profiles without shipping WDI art, and APP
Utilities keeps female Thin, Fat and Hulk distinct from the male targets. The
first pair is deliberately narrow: an upper mask for `Apparel_BasicShirt` and
`Apparel_KidShirt`, and a lower mask for `Apparel_Pants` and
`Apparel_KidPants`. The shirt uses the whole WDI silhouette and the trousers
start at the measured waistline: this preserves the shirt's own hem while its
overlap stays behind the trousers. The dedicated 2026-10-09 Pickle capture is
green in east and north for all ten profiles, but it also exposed the missing
ink contour at the WDI silhouette edge; the option therefore remains opt-in.
This proof covers only those four starter defs, not Middle or Shell.

**Where the settings are.** Mod options, then Venus Touch Waistlines. The same
window also has a `MainButtonDef`, hidden by default (`buttonVisible` false: not
shown, not greyed out), which a customisation mod such as RIMMSQOL can reveal.
It opens the same settings, with the same values. Values read back from the
config file are clamped to the sliders' ranges, and NaN or infinity fall back to
the default.

Closing the settings window calls `TailorMade.TailorMadeCache.ClearAndRepaint()`,
which sweeps every cached fit and repaints the pawns already on the map.

## What it does not do

It ships no texture. Vanilla trousers carry no `wornGraphicPath` at all - the
game draws nothing on the pawn - so a mod that fills that field is still
required. AB's Visible Pants does it, from its own 90 textures, once its
categories exist. They do not exist on a profile with no AB settings file: AB's
category list starts empty and is only filled when that file is read or Reset is
pressed in its options window, so a fresh install draws nothing until then.
Everything the trouser step does is in memory and needs AB, and does nothing
without it.

## Layout

```
Mod/                    everything that ships, and nothing else
  About/About.xml       nelim.venustouch.waistlines; needs Harmony; TailorMade,
                        APP, APP Utilities and WDI are optional integrations
  Assemblies/TailorMadeWaistlines.dll
  Defs/MainButtonDefs/  the hidden settings shortcut
  Languages/            English and French Keyed text, French DefInjected
Parked/                 earlier routes: art derived from other mods. Local only, not in this repository
Source/TailorMadeWaistlines/      Bands.cs, ChestArt.cs, TailorMadeWaistlinesMod.cs,
                        MainButtonWorker_TailorMadeWaistlines.cs,
                        TrouserArt.cs (the step at startup), TrouserDetail.cs (pure),
                        WdiVisualProfiles.cs and WdiAppPatterns.cs (runtime APP masks)
Tests/Run-Tests.ps1     runs the six sets below, no game started
Tests/Check-Mod.ps1     reflection over TailorMade: 30 checks, no game started
Tests/Check-Logic.ps1   our own patch bodies: the band per slider, which garments are shortened
Tests/Check-Localization.ps1   keys, French coverage, placeholders, hidden shortcut
Tests/Check-Settings.ps1       defaults, reset and clamping of the settings object
Tests/Check-Trousers.ps1       the trouser detail generator: invariants, on synthetic shells and AB's own
Tests/Check-WdiAppPatterns.ps1 WDI top/pants target paths and APP-mask generation
Tests/Pickle/           in-game scenarios, run by Pickle — see Tests/Pickle/README.md
scripts/*.js             measurement and generation, for the parked route
Art/                    Preview and ModIcon sources, the Preview renderer config and the generated .ico files
```

## The tools

They belong to the route that shipped textures, which is parked but not dead.
They need no dependency beyond Node: `png.js` reads and writes PNG by hand.

| tool | what it answers |
| --- | --- |
| `compare-bodies.js` | how close two body retextures are, as silhouette overlap |
| `measure-navel.js` | where the navel sits, as a fraction of the body |
| `measure-waist.js` | where a garment's waistband sits against the body |
| `measure-outline.js` | how heavy the drawn black edge is, theirs against ours |
| `make-garment.js` | builds a garment fitted to one body, from another's art |
| `make-gimp-bodies.js` | a GIMP project stacking every body retexture on disk |
| `waist-sheet.js` | a contact sheet of one body at several waist heights |

## Credits, and how this was made

**Thanks.** To astryl, whose [TailorMade: Unified Apparel & Body Refitting](https://steamcommunity.com/sharedfiles/filedetails/?id=3756915448)
does all the work this mod merely aims: three of its constants become three
sliders here, and its MIT licence is what makes that possible. To brrainz for
Harmony, without which no mod reaches another's internals. To aedbia, whose
AB's Visible Pants supplies the trousers vanilla never draws, and whose
assembly was read to learn how it assigns them. To Windonsi and Starkz, whose [WDI's Realistic Bodies](https://steamcommunity.com/sharedfiles/filedetails/?id=3527486510)
draws bodies without legs, which is the reason this mod exists at all, and the bodies every test of it is played on.
To NALS for Apparel Paper Pattern and WRelicK for APP Utilities: Venus references
their public runtime contracts only and ships neither assembly nor their assets.

**Made with AI.** The `About/Preview.png` and `About/ModIcon.png` were
generated by an image model and recomposed here; their untouched sources are
kept out of this repository under `Art/`. The assembly, the tests and this
documentation were written with [Claude Code](https://claude.com/claude-code),
which the commit history records as a co-author. What is measured in `STATUS.md`
was measured, not assumed; what has not been checked in a running game says so.

**Adoption.** If I do not answer within a reasonable time after being contacted,
anyone may freely update this or any other of my mods, including publishing a
continuation of it. All credit must be preserved.
