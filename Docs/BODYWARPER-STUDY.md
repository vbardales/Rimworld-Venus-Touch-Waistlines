# BodyWarper study (2026-11-17)

Kaitorisenkou's BodyWarper framework (Workshop 3121766100, `kaitorisenkou.bodywarper.framework`, 1.4 and 1.5) and its
Boobs add-on (3121768399, `kaitorisenkou.bodywarper.breast`), read from the 1.5 DLLs decompiled with ilspycmd, against
the 1.6 game assembly (1.6.4871). Virginie found them and asked whether they could give Venus the expected result.

## How it works

- The body quad is rebuilt as a grid of 16 x 16 cells per facing (17 x 17 vertices). Each vertex gets an x/z offset,
  summed over every `BodyWarpDef` and weighted by `GetWarpDegreeOf(pawn, node)`.
- The offsets live only in the player's ModSettings, per def, body type and facing (stored x 1000). Neither mod ships
  any shape: the player sculpts the vertices by hand in a settings menu, on a headless male mannequin.
- A Harmony prefix on `HumanlikeMeshPoolUtility.GetHumanlikeBodySetForPawn` returns the warped mesh set for every
  humanlike pawn. Body apparel asks the same method (`PawnRenderNode_Apparel.MeshSetFor`, checked on 1.6), so the clothes
  drawn over the body follow the warp exactly. Head, hair, headgear and apparel with `overrideMeshSize` are not warped.
- The per-node apparel warp (`BWFramework_Apparel`) is commented out and would not work as written: the apparel node
  constructors reassign `meshSet` after the transpiled base call, and the per-node cache is static and keyed by type.
- Boobs: `BodyWarpDef_Breast` scales its def's offsets by a `CompBreastGrowth` (age curve, females, random factor),
  plus a body part, a capacity, cup labels A to J and health-card patches. The shape itself is again sculpted by hand.

## Porting to 1.6

The hooks still exist (`GetHumanlikeBodySetForPawn`, the `PawnRenderNode` constructor calling `MeshSetFor`,
`PortraitsCache.Get`, `GraphicMeshSet`). Two things break: `MeshPool.GetMetaData` is a plain dictionary indexer, so every
generated mesh needs `MeshPool.EnsureMetaDataCached`; and `FlipGraphic` swaps in a flat `GridPlaneFlip` mesh, which drops
the warp. A port is about 50 to 150 lines. The pawn cache is never pruned and is not refreshed on a body type or life
stage change.

## Licence

None stated (About.xml, files). Treat as all rights reserved: ask kaitorisenkou before reusing code.

## For Venus

The idea fits: one warped mesh per body type and facing, shared by the body and every body garment, makes clothes follow
a target silhouette without cutting textures, and the warp is a forward displacement field that Venus could compute from
its own data (WDI source silhouette to the M1 / M prototype silhouettes). Missing for that: shape data a mod can ship (a
def or data file, not player settings), more resolution where edges matter (16 cells is about 8 px per cell on 128 px
art, and the art stretches with the mesh), zero displacement toward the neck seam, cache refresh, the 1.6 fixes above.
A clean Venus implementation of the idea (about 300 lines) is safer than depending on an experimental mod with no licence.

## Intended use (Virginie, 2026-11-17)

Not an automatic reshape of every body: a way to retouch by hand the occasional garment that the automatic cut leaves
wrong. So a warp per apparel def (and body type, facing), sculpted in an in-game dev editor in the spirit of
BodyWarper's vertex grid, saved as data shipped with Venus (a Def or XML, not player settings), applied to that
garment's render node only. Breasts go to a separate mod (Venus Touch - Breasts).
