# Publication notes

What the Workshop page needs and the repository holds nowhere else (`PUBLISHING.md`, `AUDIT.md` step
`tested → prepublished`). It serves twice: at the first upload, and for whoever takes the mod over.

**State, 2026-10-07: incomplete, on purpose.** Since 2026-09-25 the mod ends shirts on WDI's underwear line (cut on WDI's own art where it exists, compressed into the band otherwise), redraws trousers per body and sex, and lets TailorMade out of the shirts WDI draws itself (`docs/USE-CASES.md`, `docs/SHIRT-FITTING-RESEARCH.md`). The `About.xml` description was updated for that; the live Steam description still has the 0.1.0 text. Older note: **State, 2026-09-25: incomplete, on purpose.** The item exists (`3806769245`, prepublished 0.1.0, private).
The sections below say what is decided and what is not. Nothing here is filled in to look finished.

## 1. Description

The live description is the one sent when the item was created (`SetItemDescription` is called once). It is
the text of `Mod/About/About.xml` at that commit and is corrected by hand on the Steam page. What still differs from
`AUDIT.md`'s required order (body, `IF I GO QUIET`, `AI-GENERATED`, `THANKS`, the line pointing to
`ATTRIBUTION.md` and the licence, then the source link), to fix on the page:

- the three closing paragraphs are titled `Thanks`, `Made with AI`, `Adoption`, not the required headings;
- there is no line pointing to `ATTRIBUTION.md` and the licence;
- the mods it names have no Workshop link on their names;
- the thanks miss the development tools (Pickle, RimLogging, PickleTools, development only, never a
  dependency) and XeoNovaDan's Visible Pants, which has a pass of its own.

**Coming standard, not adopted yet** (CI/CD setup, 2026-09-25, `Rimworld-Release-Admin` `f196148`, nothing forced): the
description is written once, in Markdown, in a fenced block under `## Steam description` of this file; the CI
converts it to BBCode and generates `About.xml`'s `<description>` from it, and every dry-run and publish stops if
the two differ. To adopt at the next publication or when Virginie asks, through the CI/CD session (this repository
has no publish workflow of its own to regenerate yet). Until then the text above is the working list.

The thanks sentence for the authors of WDI's Realistic Bodies, approved by Virginie on 2026-09-25, to put in
`THANKS`:

```
and to Windonsi and Starkz, whose [url=https://steamcommunity.com/sharedfiles/filedetails/?id=3527486510]WDI's Realistic Bodies[/url] draws bodies without legs, which is the reason this mod exists at all, and the bodies every test of it is played on.
```

## 2. Gallery, in upload order

**Not decided.** The order is arranged by what each image shows, and no capture of the trousers has been
looked at yet: the pawn is about 45 px tall in a 1080p frame in every capture so far, and the last one had
the hover tooltip over the legs. Steam shows the first image large; it must be the most demonstrative, not the
prettiest. To fill in once the framing is fixed and the images are opened.

### Plan written 2026-10-06; since then a "ten bodies, four outfits" scenario exists (`05-gallery.feature`, galleries 1 to 32, captures read one by one; the final pictures are not chosen)

Rule (PUBLISHING.md, 2026-10-02 and 2026-10-06): every capture is a staged photograph, except menus and windows; the place is chosen
from the empty photographs of every place of the Sanctuaire (`PickleTools/docs/GALERIE.md`, `SANCTUAIRE-LIEUX.md`), not from its name;
each played image is opened and read; an anomaly of the scene or of the shared tool goes to PickleTools (NPT), never worked around here.

Story: *the fitting*. Nelim (Virginie, the only colonist of the fixture) tries one pair of trousers on five bodies, then one body in
three waistlines. Subjects are dressed in plain strong colours so the waistband and the hem read, in a palette that suits the cream or
bare ground.

| # | Shot | Place | Why this place |
|---|---|---|---|
| 0 | the Preview, byte for byte (`Art/Gallery/0-preview.png`) | n/a | rule of 2026-09-29 |
| 1 | five pawns in a row, one per WDI body type (Thin, Male, Female, Fat, Hulk), the same trousers, the same waistline | `calm-zone-close` (cream square, a row of nine cells) or `bare-clearing` | flat bare ground at midday, nothing to read but the garments; the choice between the two waits for NPT's answer on the overlays |
| 2 | one body, three values of the pants slider (0.45, 0.58, 0.70) | same place, one pawn moved between takes | shows what the setting does, which is the whole mod |
| 3 | a child beside an adult, same trousers | same place | the open child defect: not gallery material until it is fixed |
| 4 | the settings window in Mod options | `exhibition-zone` (Virginie's advice for windows) | a window is a screenshot, not a staged photo |

Rejected after reading the empty photographs: `terrace` (a mannequin and a piano, but stack counters and "no power" bolts over the
furniture), `hut` (red X marks on the animals, a dark interior), `statue-garden` and `gravel-yard` (busy ground that swallows a pawn
45 px tall), `exhibition-zone` for pawns (painted orange markers over the whole floor).

Waiting on NPT, asked through the Ticket Manager session on 2026-10-06: the step that sets a created pawn's body type and keeps it
through the capture, how to dye a worn garment, and the overlays seen on `exhibition-zone` and `calm-zone`. Needs `-DepMap` with the
Sanctuaire mods (`wsl-deps.sanctuary.map` as a model), plus WDI, AB and General.

## 3. Thank-you comments

One main comment per recipient page for the whole collection: `WORKSHOP_COMMENTS.md` (monorepo) decides
whether one is still to post. To post after the item is public, since a link to a private item opens for
nobody.

| Workshop ID | Recipient | State here | Registry row |
| --- | --- | --- | --- |
| `3527486510` | Windonsi and Starkz, WDI's Realistic Bodies | **drafted** (approved 2026-09-25) | none yet: a `drafted` row is to add to the register, which is Virginie's file |
| `3756915448` | astryl, TailorMade | **drafted** 2026-09-27 | none yet |
| `2986402536` | aedbia, AB's Visible Pants | **drafted** 2026-09-27 | none yet |
| `3789119336` | Kas, General Textures Collection | **drafted** 2026-09-27 | none yet |
| `2264108215` | XeoNovaDan, Visible Pants (has a pass of its own) | **drafted** 2026-09-27 | none yet |

None of the five drafts is approved by Virginie except the first (WDI, 2026-09-25). Nothing here is posted: `AGENTS.md` and this file's own rule are that nothing goes to Pickle or Steam upstream without her word, and a link to a private item opens for nobody besides.

Draft for `3527486510`, 628 characters (limit 1000), BBCode-safe, the bare link at the end makes a thumbnail:

```
Hi Windonsi and Starkz! 😊 Thank you for WDI's Realistic Bodies. It is the reason a small mod of mine exists: your bodies are drawn as one smooth shape with no legs, and looking at them closely showed me that TailorMade puts trousers a little too high on that kind of body. So I wrote TailorMade Waistlines, a few sliders that decide where trousers, boots and shirts stop. I built it and tested it on your bodies, and nothing of yours is copied or redistributed. ✨ It works with any body art, but yours is what it grew up on. Thank you for the beautiful work! 💛
https://steamcommunity.com/sharedfiles/filedetails/?id=3806769245
```

Draft for `3756915448` (astryl, TailorMade), not yet approved:

```
Hi astryl! 😊 Thank you for TailorMade, and for making it MIT. This mod is three of your own constants (the pants, boots and chest bands) turned into sliders, nothing more: your code does all the fitting work, mine only asks it for different numbers. Your licence is the only reason a mod like this can exist at all — without it I'd have had nothing to patch into. Thank you for the generous terms and the well-built mod behind them! 💛
https://steamcommunity.com/sharedfiles/filedetails/?id=3806769245
```

Draft for `2986402536` (aedbia, AB's Visible Pants), not yet approved:

```
Hi aedbia! 😊 Thank you for AB's Visible Pants — it's the mod that actually draws trousers on bodies vanilla leaves bare. Reading your assembly taught me how your settings file fills in the categories, and that knowledge is the only thing I took from it: nothing of your code or art is copied. My small mod, TailorMade Waistlines, gives your trousers a waistband and a fly where the body art has none, and moves them down a little on bodies drawn without legs. Thank you for supplying what nothing else does! 💛
https://steamcommunity.com/sharedfiles/filedetails/?id=3806769245
```

Draft for `3789119336` (Kas, General Textures Collection), not yet approved:

```
Hi Kas! 😊 Thank you for General Textures Collection. Your retexture of AB's trousers has the details — a waistband, a fly, a seam — that the base art doesn't, and my mod reads those PNGs straight from your installed folder at startup so a pawn wears your art instead of a plain shell, whenever General is active alongside AB. Nothing of yours is copied into mine: it's read at run time, exactly as the game would have loaded it itself. Thank you for the detail work! 💛
https://steamcommunity.com/sharedfiles/filedetails/?id=3806769245
```

Draft for `2264108215` (XeoNovaDan, Visible Pants), not yet approved:

```
Hi XeoNovaDan! 😊 Thank you for Visible Pants — the reason bodies without legs need trousers of their own at all is that yours drew the question first. TailorMade Waistlines gets its own capture pass against your mod, the same way it does against AB's, so your trousers get the same waistline correction on a legless body. Thank you for the original work this whole space is built on! 💛
https://steamcommunity.com/sharedfiles/filedetails/?id=3806769245
```

## 4. Dependencies and DLC

Read from `Mod/About/About.xml` on 2026-09-25; the sources were checked in the 2026-09-21 audit and not reopened for this note:

- **Hard:** Harmony, and TailorMade (`astryl.tailormade`): the mod is Harmony patches on its internals.
- **`loadAfter`, not dependencies:** AB's Visible Pants and General Textures Collection. The trouser step acts
  only where AB is active; without AB, nothing is drawn or registered; without General, its retexture is unavailable
  and the details are drawn onto AB's shell instead.
- **DLC:** none declared. The child garment (`Apparel_KidPants`) is Biotech's; the mod does not require Biotech.
  Not re-verified against the `LoadFolders`/`IfModActive` branches of the dependencies.

## 5. Content warnings

The adult-content boxes: **not answered.** The mod ships no image of a person beyond its own preview and icon,
and neither has been reopened for this question. To answer with the images open.

## 6. Steam change note

**Not written.** It is written at the moment of upload, in a tab nothing asks for until the form is open. The
0.1.0 upload only created the item. The `1.0.0` note will say what the mod does now: the three band sliders, the
shirt option (shirts cut on WDI's underwear, trousers on the same line), General Textures Collection's trouser retexture and the drawn
details, the two drop sliders, per-sex trousers for Thin, Fat and Hulk, children on their trousers' line, and that every trouser
texture is read at run time and none is shipped.

## 7. Before any `publish`

Fail fast applies (`AUDIT.md`, 2026-09-25), and none of it is skipped: no red scenario without a green replay
(today `03-silhouettes` has two red children, waiting on a PickleTools step), the gallery, Virginie's manual
validations, a dry-run of the exact commit, `publish` with the full SHA, and Virginie's approval of
`steam-production`. The rollback target is chosen before, not after.
