# Parked

Nothing under this folder is loaded by the game: RimWorld only reads `Defs`,
`Patches`, `Textures`, `Assemblies` and the rest of the known names at the mod
root.

The mod's brief, settled on 2026-09-20, is that the fitting must be **automatic**
— computed at render time from the body it is worn on, for every garment of
every mod — and not a set of textures drawn or generated in advance. Everything
here is an earlier answer that shipped art instead. It is kept because the
automatic route depends on somebody supplying art at all, and if that art turns
out to be unusable these are one move from being back.

## `Pants_WornGraphic.xml`, `Textures/Pants`, `TailorPatternDefs_Ignore.xml`

The three pieces of the art route, and they only work together: a patch writing
`wornGraphicPath` onto `Apparel_Pants` and `Apparel_KidPants`, 27 textures cut
to each body's silhouette by `scripts/make-garment.js --auto`, and a
`TailorPatternDef` telling TailorMade to leave both garments alone because they
are fitted already.

Measured at the point they were parked: waistband at 0.32 of the body's height,
outline 2px against the body's own 13px, nine body types by three facings.

Bring them back only together — the patch without the ignore def would have
TailorMade fit an already-fitted texture, and the ignore def without the patch
would switch off the fitting of whatever art is supplying the pants instead.

## `TailorPatternDefs_Masks.xml`

The first design of all: a hand-painted mask per body type, handed to TailorMade
in place of the body silhouette. The masks are still under
`Mod/Textures/Things/TailoredPants/<Body>/`, and `scripts/` still builds and
reads them.

## A note on the paths in here

These files still name `Things/TailoredPants/…`, the mod's first name. That is
a path inside the mod's own texture folder, not an identifier anything else
depends on, so it keeps working as written if the route ever comes back. It is
left alone so that the files stay exactly as they were measured and tested.
