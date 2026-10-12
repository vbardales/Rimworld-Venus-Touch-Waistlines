# TailorMade Waistlines — in-game test scenarios

`Tests/Run-Tests.ps1` runs beside this file and starts nothing:

```
powershell -ExecutionPolicy Bypass -File Tests\Run-Tests.ps1
```

It runs the six sets in turn — `Check-Mod.ps1`, that every method and constant
this mod reaches into still exists and still means what the code assumes;
`Check-Logic.ps1`, that our own patch bodies hand back the right band for each
slider and shorten the right garments; `Check-Settings.ps1`, the defaults, the
reset and the clamping; `Check-Trousers.ps1`, the trouser-detail drawing on
synthetic shells and on AB's real ones, as bytes; `Check-WdiAppPatterns.ps1`,
that the APP bridge keeps the ten WDI targets distinct and turns only the
installed body's alpha into a full top silhouette plus a waist-clipped pants mask; `Check-Localization.ps1`,
the keys and both languages. 359 checks, on the DLL in `Mod/Assemblies`. The
APP check also opens all thirty installed WDI naked-body sources, for every
target profile and facing, and requires their expected 512×512 dimensions.
The APP Pickle pass seeds its explicit opt-in setting; normal installations
leave the prototype disabled.

None of that is a single tick of play: the bands are compared as numbers, never
as pixels, and no texture is ever baked. This file is the list of what has to be
watched in a running colony, and what counts as a pass.

It is not shipped: it lives beside `Mod/`, never inside it.

## Before starting

- RimWorld 1.6, with Harmony and TailorMade active, and this mod after both.
- A mod that gives leg garments a worn graphic. Vanilla trousers carry none, so
  without one the game draws nothing and every scenario below fails for a
  reason that has nothing to do with this mod.
- A body retexture drawn without legs. The mod does nothing wrong on a vanilla
  body; it simply has nothing to correct.

### The trap that costs an evening

**AB's Visible Pants forgets its own categories.** Its `ExposeData` creates the
five defaults on load and then, two lines later, `Scribe_Collections.Look`
overwrites them with the empty list saved in its config. Its settings screen is
then blank, `AVPCache.pants` stays empty, and it assigns no texture at all — so
pawns are drawn bare and it looks as though this mod broke something.

Its **Reset** button, on the *Advanced Settings* tab, fills the list in memory.
It is applied in `AVPCache`'s static constructor, which runs at startup, so the
sequence is: press Reset, close, **restart**. Check
`Config/Mod_2986402536_ABsVisiblePantsMod.xml` afterwards — if `<datas />` is
still empty, it did not take.

**The same trap, worse, on a fresh profile**, found 2026-09-21 by decompiling
the installed 1.6 assembly. AB's category list is filled only when that config
file is *read* or when Reset is pressed. A profile that has no such file at all —
which is every headless run, and any clean install — therefore has AB present,
enabled, and assigning no texture whatsoever. Every capture taken in that state
shows a pawn drawn bare, and the run is green because nothing asserts.

So a pass with AB is only valid if AB was seeded.
`Tests/Pickle/config/wdi-ab/Mod_2986402536_ABsVisiblePantsMod.xml` holds AB's
five default categories, copied unchanged from the working configuration on this
machine, and the staging copies it into the profile for that pass only. The
scenario *AB has actually given the trousers a worn graphic* reads
`Apparel_Pants.apparel.wornGraphicPath` and is the net: **red there means the
pass is invalid, not that this mod is broken.**

## The passes

The scenarios below are played more than once, because what supplies the trousers changes what
there is to look at. Each pass is a different mod set, selected with
`Run-PickleWsl.ps1 -DepMap <file>`, and its name (the map's file name without `wsl-deps.` and
`.map`) is on the report and nowhere in an image.

| pass | map | what it establishes |
| --- | --- | --- |
| bare | `wsl-deps.tools.map` | the mod does nothing wrong with nothing to do: no error, no exception, pawns drawn as vanilla draws them. The trousers scenarios skip, by their `@requires` tags, rather than photograph a bare pawn |
| WDI + AB | `wsl-deps.wdi-ab.map`, seeded | AB supplies a plain shell and this mod draws a waistband, fly and seams onto it |
| WDI + AB + General | `wsl-deps.wdi-ab-general.map`, seeded | the pass in which this mod reads General Textures Collection's retexture, which General's own LoadFolders never loads with AB active |
| WDI + AB, band | `wsl-deps.wdi-ab-band.map`, seeded, **with `-Filter '<suite>,!@native-art'`** | both art options off: TailorMade fits AB's shell into the band and the pants slider applies. The only pass in which the band is what is drawn. The `@native-art` scenarios assert the opposite state and go red here by design |
| WDI + XND | `wsl-deps.wdi-xnd.map` | XeoNovaDan's Visible Pants instead of AB's. This mod does nothing on purpose, so this shows what the band does to art drawn for the vanilla footprint |
| WDI + XND + General | `wsl-deps.wdi-xnd-general.map` | with XND active General's retexture loads, so the art is General's, supplied by General; this mod's "leave it alone" branch runs |
| WDI + APP | `wsl-deps.app-wdi.map` | opt-in APP slice for BasicShirt/KidShirt and Pants/KidPants. `docs/runs/2026-10-09_app-wdi-full-top/` is the clean 2/2 `@facings` proof: blue trousers remain visible under the t-shirt, with no waist gap, in east and north for all ten WDI profiles. Middle/Shell are still outside the slice |

Written 2026-09-24. Before that only the first three existed. All six ran that day on the DLL with
the trouser art: no failure on the mod, and ten `03-silhouettes` scenarios red in every AB pass (and in
the band pass) on a step Pickle does not have. `03` was then rewritten, first with three scenarios on the released
Pickle, then with ten on a PickleTools step (`Tests/Pickle/README.md`), and has not run in either form. Results and images kept: `STATUS.md`, `docs/runs/`.

## Scenarios

### 1. The patch is live, and by the right route

Start the game and read `Player.log`. Exactly one of these appears:

- `[TailorMade Waistlines] band patch active on ApparelClassifier.BandFor.` — pass.
- `... looks inlined; falling back to TexBake.BakeFitted` — also works, but
  a slider change then needs a restart, because TailorMade's cache was keyed on
  the old value. Worth knowing before judging anything else.

### 2. Nothing changes until asked

With the settings untouched, a pawn looks exactly as it did before the mod was
installed. The defaults are TailorMade's own numbers. If anything moved, the
patch is returning something it should not.

### 3. The waistband follows the slider

One pawn, trousers, facing south. Lower **Pants reach up to** from 0.58 to 0.40
and close the window. The waistband drops, the hem does not move, and the pawns
already on the map repaint without a reload.

Measured reference points, on WDI's bodies at 512: the navel sits at 0.52 of
the body's height on Female, 0.48 on Male, 0.46 on Fat, 0.58 on Thin. A
waistband below all of them needs roughly 0.42 or lower.

### 4. Every body type

Character Editor gives one of each in two clicks. Ten silhouettes à regarder :
Male, Female, Male_Thin, Male_Hulk, Male_Fat, Female_Thin, Female_Hulk,
Female_Fat, Kid_Boy et Kid_Girl.

- Hulk and Hulk_Female are the tall ones — their art reaches row 495 where
  Female stops at 443. A height error shows there first.
- Child wears `Apparel_KidPants`, a separate def from `Apparel_Pants`. Whatever
  supplies the art has to cover it; AB's does, because its keyword is the
  substring `Pants`.

### 5. Four facings

West is mirrored from east by the game. Turn a pawn all the way round and watch
for a jump between the two.

### 6. Shirts, and the compression

Tick **Shorten full-body shirts** and lower **Chest pieces start at**. A
vanilla button-down shirt should stop short and let the trousers show.

Then put a duster on the same pawn. It must still reach the ankles: the option
is limited to on-skin garments for exactly this reason, and a shortened duster
is a bug, not a taste question.

The question this scenario exists to answer is not whether it works but whether
it *reads*: the band scales the art into itself rather than cropping, so the
collar and buttons are squeezed along with the hem. If that looks wrong, the
answer is to crop in our own bake, which is a real piece of work and has not
been written.

### 7. Boots

Lower **Boots reach up to** and check that footwear from any mod follows. This
is the band nobody has looked at yet.

### 8. Save, load, and settings

Change all three sliders, save, quit, restart, load. The values survive, and
the pawns are drawn with them from the first frame rather than after a repaint.

### 9. The settings, in English and in French

**Turn developer mode on first, and keep it on for this one.** Without it this
scenario proves nothing about the keys: a key missing from the active language
falls back to clean English, and clean English is exactly what a correct
English run looks like. In developer mode the game marks that fallback instead,
by accenting it letter by letter — a→à, c→ç, e→è, g→ğ, l→ſ, n→ƞ, k→к in
Cyrillic. So, reading a French window:

- accented gibberish — the key is missing from French. The braces survive the
  transformation, so a `{0}` left raw or a parameter gone missing still reads
  normally in the middle of it;
- accented gibberish that spells out the key itself — the key is missing from
  every language;
- **clean English in the middle of the French** — the string never went through
  `Translate` at all: a literal hardcoded in the C# or the XML. The mod's own
  name in the category header is the one that is allowed to look like this.

Open Mod options, then TailorMade Waistlines, in each language. Every line is
text, never a raw key such as `TailorMadeWaistlines.Settings.Intro`; French
shows a comma decimal (0,58); nothing is clipped, and the window scrolls to the
last line. Hover each slider: a tooltip appears.

### 10. The hidden shortcut

On a clean configuration the main button bar shows nothing new, neither a
button nor a greyed-out one. In RIMMSQOL, reveal *TailorMade Waistlines*: it
opens the same window, edits show in Mod options, and hiding it again survives
a restart. Record which customisation mods were actually tried.

### 11. A damaged config file

With the game closed, set `pantsTop` to `5` and `bootsTop` to `NaN` in
`Config/Mod_VenusTouchWaistlines_TailorMadeWaistlinesMod.xml`. On load, the
sliders show 0,90 and 0,20 (0.90 and 0.20 in English), and the log has no
error.

## What a Pickle suite would cover here, and what it must not

Pickle does not replace the four test sets, it completes them, and it costs
incomparably more: a run takes the machine — real clicks, real pointer, the
screen occupied — for tens of minutes where the sets take seconds. So anything
that can be proved outside the game is proved outside it, and a scenario that
repeats what `Check-Logic.ps1` or `Check-Settings.ps1` already proves confiscates
the machine at every run without adding anything. It is to be deleted, not kept
in case.

What is left is what only a running game can show, and it is the short list:

- scenario 9, the window in both languages, in developer mode — layout,
  clipping, and the accented fallback that no unit test can see;
- scenario 10, the shortcut revealed in RIMMSQOL: a real click that has to
  reach the right window through whatever another mod has laid over that point;
- scenarios 3 and 7, a slider moved and the pawns already on the map repainting,
  which is `ClearAndRepaint` doing its work rather than a value changing;
- scenario 8, values that survive a save, a restart and a load;
- scenario 6, the compressed shirt, as a `@review` scenario: it attaches
  screenshots for a person to judge and asserts nothing. Its green says the
  journey ran, never that the image is right.

The bands themselves, the clamping of a damaged config, the defaults and which
garments the shirt option lifts are all settled by the sets in `Tests/`, and
belong in no scenario.

## What is not covered

- Alien races. TailorMade has its own HAR handling and this mod does not touch
  it; the bands apply to whatever it classifies.
- The parked texture route under `Parked/`. It has its own conditions, and
  bringing it back means bringing back all three of its files together.

## What the suite covers of the eleven, and what stays by hand

Written 2026-09-21, before the first run of the three features, so that the next session can see
at a glance what a green suite would and would not buy. Twenty-two scenarios over three files
against eleven written here: the counts do not line up because the suite splits one of these into
one scenario per body, and answers some of them only in part.

| Scenario above | In the suite? |
| --- | --- |
| 1. The patch is live, and by the right route | **No.** The route is a static flag and the startup line; reading either needs a step of our own, and the one that did was removed. Log line by eye |
| 2. Nothing changes until asked | **Partly.** `the mod is quiet on a body drawn the ordinary way` covers the bare pass. Defaults untouched on a legless body is not asserted anywhere |
| 3. The waistband follows the slider | **No.** Moving a slider and watching the map repaint needs the settings window and a step that reads TailorMade's cache. By hand |
| 4. Every body type | **Yes, once it has run**: `03-silhouettes` dresses ten pawns with the body type set by PickleTools' step and read back, and checks that no trouser texture failed to load. The **drawn texture path is not asserted** (that needs Pickle PR #32); the capture is for a person. The two children are the open point (Child is an age, not a gene) |
| 5. Four facings | **No.** Nothing rotates a pawn. By hand |
| 6. Shirts, and the compression | **No.** The suite never puts a shirt on. This is the open question of the mod and it is still entirely by eye |
| 7. Boots | **No.** Nothing wears boots |
| 8. Save, load, and settings | **No.** By hand; the off-game sets cover the file round trip, not a real restart |
| 9. The settings, in English and in French | **No**, and remember it only counts in developer mode |
| 10. The hidden shortcut | **No.** RIMMSQOL is not in any pass |
| 11. A damaged config file | **Covered off-game** by `Check-Settings.ps1`, and deliberately not repeated here |

So a suite entirely green answers **4** (without the drawn path), part of **2**, and adds three things the eleven
never asked for: that AB is the supplier in that pass, that AB actually filled `wornGraphicPath`,
and that the mod told TailorMade to leave its own art alone. Everything about the sliders, the
shirt, the boots, the facings, the languages and the shortcut is still a person in front of the
game.

## Evidence: what to keep, and how small

Reports and screenshots weigh megabytes each, a Pickle run overwrites its own folder, and the disk
is finite. So evidence lives **on disk and never in git** (`.gitignore` covers `evidence/`,
`Tests/Pickle/Evidence/`, `PickleReports*/` and `*.dds`), in `docs/runs/<date>_<hour>/evidence/`,
and the history is **one text line per run** in `docs/runs/README.md`.

What proves something, and is worth keeping while it is the latest for the shipped DLL:

- **`summary.json`, and `exitReason` read first.** A few hundred bytes. It says whether the run
  reached its end, how many scenarios played and how many features were discovered. Always keep.
- **One capture per silhouette that a person actually judged**, cropped to the pawn and its
  inspector, not the 1080p frame: `03-silhouettes` is ten, `01-trousers-review` is three. The
  inspector line (`Carrying`, `Wearing`) is what shows the garment was worn, so the crop keeps it.
- **The Gear-tab capture of `02`**, once, per body: it is the witness that does not depend on how
  anything is drawn.
- **The `Player.log` lines from this mod**, not the whole log: the trouser summary line and any
  warning.

Everything else goes: the full frames, `report.html` (tens of MB), `messages.ndjson`, `junit.xml`
and captures of scenarios that only assert. A capture of a garment that was not worn, or of a bare
pawn, proves nothing and is not kept as a curiosity: its finding goes into the text line.

**A report of a superseded build is deleted when a newer one replaces it.** Compare the DLL hash on
the line with the one in `Mod/Assemblies` before citing any of it, and never delete a report that a
`STATUS.md` field still names - repoint the field first.

### What to keep, restated 2026-10-06

- Evidence folders are `docs/runs/<date>_<pass>/evidence*/` (`evidence`, `evidence-1`, `evidence-2`, ...). All are ignored by
  git; none is committed. What goes in git is the text line in `docs/runs/README.md`.
- Per scenario, keep **the latest report for the DLL now in `Mod/`**, minimised to `summary.json` (read `exitReason` first), the mod's
  log lines, and the one capture a person actually judged, cropped. Keep an older report only if it is the sole proof of a scenario the
  latest run did not repeat; delete it once a newer one replaces it. `report.html`, `messages.ndjson`, `junit.xml`, the full
  `Player.log` and uncropped 1080p frames are never kept.
- A failed or superseded run keeps one line in `docs/runs/README.md` and no files.
- Never delete a report a `STATUS.md` field still names; repoint the field first.
- A throwaway exploration feature (`99-explore-*`) is deleted after it has been read once, with its reports.

### Conditions of `tested` (AUDIT.md, `done -> tested`)

1. No scenario tagged `@wip` (repair and replay, or delete with the reason).
2. Every `@requires:<id>` scenario has run in the pass that mounts that mod, and its report was read (`setName`, suite and scenario
   names, `exitReason`, played against discovered).
3. No manual scenario left to validate: each of the 11 above is automated and green, or listed here as not applicable with its reason.
4. `@review` captures opened and looked at, not only counted green.
5. FR and EN display and the settings checked in game, in developer mode.
6. Gallery photographs staged by a scenario (PUBLISHING.md), read one by one; an anomaly of the scene or of the shared tool goes to
   PickleTools (NPT), through the Ticket Manager session when NPT cannot be reached.
