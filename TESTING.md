# TailorMade Waistlines — in-game test scenarios

`Tests/Run-Tests.ps1` runs beside this file and starts nothing:

```
powershell -ExecutionPolicy Bypass -File Tests\Run-Tests.ps1
```

Runs six sets in turn — `Check-Mod.ps1`: every method and constant mod reaches into still exists, still means what code assumes; `Check-Logic.ps1`: our patch bodies return right band per slider, shorten right garments; `Check-Settings.ps1`: defaults, reset, clamping; `Check-Trousers.ps1`: trouser-detail drawing on synthetic shells and AB's real ones, as bytes; `Check-WdiAppPatterns.ps1`: APP bridge keeps ten WDI targets distinct, turns only installed body's alpha into full top silhouette plus waist-clipped pants mask; `Check-Localization.ps1`: keys and both languages. 359 checks, on DLL in `Mod/Assemblies`. APP check also opens all thirty installed WDI naked-body sources, every target profile and facing, requires expected 512×512 dimensions. APP Pickle pass seeds explicit opt-in setting; normal installs leave prototype disabled.

None of that is one tick of play: bands compared as numbers, never pixels, no texture baked. This file = list of what must be watched in running colony, and what counts as pass.

Not shipped: lives beside `Mod/`, never inside.

## Before starting

- RimWorld 1.6, Harmony and TailorMade active, this mod after both.
- Mod giving leg garments worn graphic. Vanilla trousers carry none, so without one game draws nothing, every scenario below fails for reason unrelated to this mod.
- Body retexture drawn without legs. Mod does nothing wrong on vanilla body; nothing to correct.

### The trap that costs an evening

**AB's Visible Pants forgets its own categories.** Its `ExposeData` creates five defaults on load, then two lines later `Scribe_Collections.Look` overwrites them with empty list saved in config. Settings screen blank, `AVPCache.pants` empty, no texture assigned — pawns drawn bare, looks like this mod broke something.

Its **Reset** button, *Advanced Settings* tab, fills list in memory. Applied in `AVPCache` static constructor at startup, so sequence: press Reset, close, **restart**. Afterwards check `Config/Mod_2986402536_ABsVisiblePantsMod.xml` — if `<datas />` still empty, did not take.

**Same trap, worse, on fresh profile**, found 2026-09-21 by decompiling installed 1.6 assembly. AB's category list filled only when config file *read* or Reset pressed. Profile with no such file — every headless run, any clean install — has AB present, enabled, assigning no texture at all. Every capture in that state shows bare pawn, run green because nothing asserts.

So pass with AB valid only if AB seeded. `Tests/Pickle/config/wdi-ab/Mod_2986402536_ABsVisiblePantsMod.xml` holds AB's five default categories, copied unchanged from working config on this machine; staging copies it into profile for that pass only. Scenario *AB has actually given the trousers a worn graphic* reads `Apparel_Pants.apparel.wornGraphicPath`, is the net: **red there means pass invalid, not mod broken.**

## The passes

Scenarios below played more than once, because what supplies trousers changes what there is to look at. Each pass = different mod set, selected with `Run-PickleWsl.ps1 -DepMap <file>`; its name (map file name without `wsl-deps.` and `.map`) is on report, nowhere in image.

| pass | map | what it establishes |
| --- | --- | --- |
| bare | `wsl-deps.tools.map` | mod does nothing wrong with nothing to do: no error, no exception, pawns drawn as vanilla draws them. Trousers scenarios skip, by `@requires` tags, rather than photograph bare pawn |
| WDI + AB | `wsl-deps.wdi-ab.map`, seeded | AB supplies plain shell, this mod draws waistband, fly, seams onto it |
| WDI + AB + General | `wsl-deps.wdi-ab-general.map`, seeded | pass where this mod reads General Textures Collection's retexture, which General's own LoadFolders never loads with AB active |
| WDI + AB, band | `wsl-deps.wdi-ab-band.map`, seeded, **with `-Filter '<suite>,!@native-art'`** | both art options off: TailorMade fits AB's shell into band, pants slider applies. Only pass where band is what is drawn. `@native-art` scenarios assert opposite state, go red here by design |
| WDI + XND | `wsl-deps.wdi-xnd.map` | XeoNovaDan's Visible Pants instead of AB's. Mod does nothing on purpose, so shows what band does to art drawn for vanilla footprint |
| WDI + XND + General | `wsl-deps.wdi-xnd-general.map` | with XND active General's retexture loads, art is General's, supplied by General; mod's "leave it alone" branch runs |
| WDI + APP | `wsl-deps.app-wdi.map` | opt-in APP slice for BasicShirt/KidShirt and Pants/KidPants. the 2026-10-09 `@facings` run (2/2 green, evidence deleted 2026-10-19: it predates the redrawn cut lines) showed: blue trousers remain visible under t-shirt, no waist gap, east and north, all ten WDI profiles. Middle/Shell still outside slice |

Written 2026-09-24. Before that only first three existed. All six ran that day on DLL with trouser art: no failure on mod, ten `03-silhouettes` scenarios red in every AB pass (and band pass) on step Pickle does not have. `03` then rewritten, first three scenarios on released Pickle, then ten on PickleTools step (`Tests/Pickle/README.md`), not run in either form. Results and images kept: `STATUS.md`, `docs/runs/`.

## Scenarios

### 1. The patch is live, and by the right route

Start game, read `Player.log`. Exactly one appears:

- `[TailorMade Waistlines] band patch active on ApparelClassifier.BandFor.` — pass.
- `... looks inlined; falling back to TexBake.BakeFitted` — also works, but slider change then needs restart, because TailorMade's cache keyed on old value. Worth knowing before judging anything else.

### 2. Nothing changes until asked

Settings untouched, pawn looks exactly as before mod installed. Defaults = TailorMade's own numbers. If anything moved, patch returning something it should not.

### 3. The waistband follows the slider

One pawn, trousers, facing south. Lower **Pants reach up to** 0.58 to 0.40, close window. Waistband drops, hem does not move, pawns already on map repaint without reload.

Measured reference points, WDI's bodies at 512: navel at 0.52 of body height on Female, 0.48 Male, 0.46 Fat, 0.58 Thin. Waistband below all needs roughly 0.42 or lower.

### 4. Every body type

Character Editor gives one of each in two clicks. Ten silhouettes à regarder :
Male, Female, Male_Thin, Male_Hulk, Male_Fat, Female_Thin, Female_Hulk,
Female_Fat, Kid_Boy et Kid_Girl.

- Hulk and Hulk_Female tall — art reaches row 495 where Female stops at 443. Height error shows there first.
- Child wears `Apparel_KidPants`, separate def from `Apparel_Pants`. Whatever supplies art must cover it; AB's does, keyword is substring `Pants`.

### 5. Four facings

West mirrored from east by game. Turn pawn all way round, watch for jump between the two.

### 6. Shirts, and the compression

Tick **Shorten full-body shirts**, lower **Chest pieces start at**. Vanilla button-down shirt should stop short, let trousers show.

Then put duster on same pawn. Must still reach ankles: option limited to on-skin garments for exactly this reason; shortened duster is bug, not taste question.

Question this scenario answers is not whether it works but whether it *reads*: band scales art into itself rather than cropping, so collar and buttons squeezed along with hem. If looks wrong, answer is crop in our own bake — real piece of work, not written.

### 7. Boots

Lower **Boots reach up to**, check footwear from any mod follows. Band nobody has looked at yet.

### 8. Save, load, and settings

Change all three sliders, save, quit, restart, load. Values survive, pawns drawn with them from first frame, not after repaint.

### 9. The settings, in English and in French

**Turn developer mode on first, keep on for this one.** Without it scenario proves nothing about keys: key missing from active language falls back to clean English, which is exactly what correct English run looks like. In developer mode game marks fallback by accenting letter by letter — a→à, c→ç, e→è, g→ğ, l→ſ, n→ƞ, k→к in Cyrillic. So, reading French window:

- accented gibberish — key missing from French. Braces survive transformation, so `{0}` left raw or parameter missing still reads normally in middle of it;
- accented gibberish spelling out key itself — key missing from every language;
- **clean English in middle of French** — string never went through `Translate`: literal hardcoded in C# or XML. Mod's own name in category header is the one allowed to look like this.

Open Mod options, then TailorMade Waistlines, each language. Every line text, never raw key such as `TailorMadeWaistlines.Settings.Intro`; French shows comma decimal (0,58); nothing clipped, window scrolls to last line. Hover each slider: tooltip appears.

### 10. The hidden shortcut

Clean configuration: main button bar shows nothing new, no button, no greyed-out one. In RIMMSQOL, reveal *TailorMade Waistlines*: opens same window, edits show in Mod options, hiding again survives restart. Record which customisation mods actually tried.

### 11. A damaged config file

Game closed, set `pantsTop` to `5` and `bootsTop` to `NaN` in `Config/Mod_VenusTouchWaistlines_TailorMadeWaistlinesMod.xml`. On load, sliders show 0,90 and 0,20 (0.90 and 0.20 in English), log has no error.

## What a Pickle suite would cover here, and what it must not

Pickle does not replace four test sets, completes them, costs incomparably more: run takes machine — real clicks, real pointer, screen occupied — tens of minutes where sets take seconds. So anything provable outside game proved outside it; scenario repeating what `Check-Logic.ps1` or `Check-Settings.ps1` already proves confiscates machine every run, adds nothing. Delete it, not keep in case.

What is left is what only running game can show, short list:

- scenario 9, window in both languages, developer mode — layout, clipping, accented fallback no unit test can see;
- scenario 10, shortcut revealed in RIMMSQOL: real click must reach right window through whatever another mod laid over that point;
- scenarios 3 and 7, slider moved and pawns already on map repainting, which is `ClearAndRepaint` doing its work rather than value changing;
- scenario 8, values surviving save, restart, load;
- scenario 6, compressed shirt, as `@review` scenario: attaches screenshots for person to judge, asserts nothing. Green says journey ran, never image right.

Bands themselves, clamping of damaged config, defaults, which garments shirt option lifts all settled by sets in `Tests/`, belong in no scenario.

## What is not covered

- Alien races. TailorMade has own HAR handling, this mod does not touch it; bands apply to whatever it classifies.
- Parked texture route under `Parked/`. Own conditions; bringing back means bringing back all three files together.

## What the suite covers of the eleven, and what stays by hand

Written 2026-09-21, before first run of three features, so next session sees at glance what green suite would and would not buy. Twenty-two scenarios over three files against eleven here: counts don't line up because suite splits one into one scenario per body, answers some only in part.

| Scenario above | In the suite? |
| --- | --- |
| 1. The patch is live, and by the right route | **No.** Route is static flag and startup line; reading either needs step of our own, the one that did was removed. Log line by eye |
| 2. Nothing changes until asked | **Partly.** `the mod is quiet on a body drawn the ordinary way` covers bare pass. Defaults untouched on legless body not asserted anywhere |
| 3. The waistband follows the slider | **No.** Moving slider and watching map repaint needs settings window and step reading TailorMade's cache. By hand |
| 4. Every body type | **Yes, once it has run**: `03-silhouettes` dresses ten pawns with body type set by PickleTools' step and read back, checks no trouser texture failed to load. **Drawn texture path not asserted** (needs Pickle PR #32); capture is for a person. Two children open point (Child is age, not gene) |
| 5. Four facings | **No.** Nothing rotates pawn. By hand |
| 6. Shirts, and the compression | **No.** Suite never puts shirt on. Open question of mod, still entirely by eye |
| 7. Boots | **No.** Nothing wears boots |
| 8. Save, load, and settings | **No.** By hand; off-game sets cover file round trip, not real restart |
| 9. The settings, in English and in French | **No**, and only counts in developer mode |
| 10. The hidden shortcut | **No.** RIMMSQOL in no pass |
| 11. A damaged config file | **Covered off-game** by `Check-Settings.ps1`, deliberately not repeated here |

So fully green suite answers **4** (without drawn path), part of **2**, adds three things the eleven never asked for: AB is supplier in that pass, AB actually filled `wornGraphicPath`, mod told TailorMade to leave own art alone. Everything about sliders, shirt, boots, facings, languages, shortcut still person in front of game.

## Evidence: what to keep, and how small

Reports and screenshots weigh megabytes each, Pickle run overwrites own folder, disk finite. So evidence lives **on disk, never in git** (`.gitignore` covers `evidence/`, `Tests/Pickle/Evidence/`, `PickleReports*/` and `*.dds`), in `Tests/Pickle/Inbox/` then `Evidence/` (since 2026-10-19), history is **one text line per run** in `docs/runs/README.md`.

What proves something, worth keeping while latest for shipped DLL:

- **`summary.json`, `exitReason` read first.** Few hundred bytes. Says whether run reached end, how many scenarios played, how many features discovered. Always keep.
- **One capture per silhouette a person actually judged**, cropped to pawn and inspector, not 1080p frame: `03-silhouettes` is ten, `01-trousers-review` is three. Inspector line (`Carrying`, `Wearing`) shows garment worn, so crop keeps it.
- **Gear-tab capture of `02`**, once, per body: witness not depending on how anything drawn.
- **`Player.log` lines from this mod**, not whole log: trouser summary line and any warning.

Everything else goes: full frames, `report.html` (tens of MB), `messages.ndjson`, `junit.xml`, captures of scenarios that only assert. Capture of garment not worn, or bare pawn, proves nothing, not kept as curiosity: finding goes into text line.

**Report of superseded build deleted when newer one replaces it.** Compare DLL hash on line with one in `Mod/Assemblies` before citing any of it; never delete report a `STATUS.md` field still names - repoint field first.

### What to keep, restated 2026-10-06

- Evidence: `Tests/Pickle/Inbox/<run>` (reception), `Tests/Pickle/Evidence/` (minified proofs, each with a RELEASE.md), `Tests/Pickle/Parked/`. All git-ignored; none committed. Git gets text line in `docs/runs/README.md`.
- Per scenario, keep **latest report for DLL now in `Mod/`**, minimised to `summary.json` (read `exitReason` first), mod's log lines, one capture a person actually judged, cropped. Keep older report only if sole proof of scenario latest run did not repeat; delete once newer replaces it. `report.html`, `messages.ndjson`, `junit.xml`, full `Player.log`, uncropped 1080p frames never kept.
- Failed or superseded run keeps one line in `docs/runs/README.md`, no files.
- Never delete report a `STATUS.md` field still names; repoint field first.
- Throwaway exploration feature (`99-explore-*`) deleted after read once, with reports.

### Conditions of `tested` (AUDIT.md, `done -> tested`)

1. No scenario tagged `@wip` (repair and replay, or delete with reason).
2. Every `@requires:<id>` scenario ran in pass mounting that mod, report read (`setName`, suite and scenario names, `exitReason`, played against discovered).
3. No manual scenario left to validate: each of 11 above automated and green, or listed here as not applicable with reason.
4. `@review` captures opened and looked at, not only counted green.
5. FR and EN display and settings checked in game, developer mode.
6. Gallery photographs staged by scenario (PUBLISHING.md) read one by one; anomaly of scene or shared tool goes to PickleTools (NPT), through Ticket Manager session when NPT cannot be reached.