# Shirt transfer: per-body data table (format v1, draft)

Interface between the runtime transfer (A, in the DLL) and the offline measurement tool (B, run by hand, under `Tests/` or `Art/work`, declared in `scripts/LOCAL_SCRIPTS.md`). B reads WDI's textures and writes this table; the table is committed; A reads it and never measures a WDI texture itself. Agreed with Audit on 2026-11-02 (A+B). Draft: nothing reads it yet.

## File

`Mod/Common/Data/ShirtTransfer.xml` (one file, one `<Body>` per WDI body key and facing). The root carries `version="1"`; a reader that does not know the version ignores the file and uses the fallback.

```xml
<ShirtTransfer version="1" texSize="512" measuredFrom="wdi.realistic.bodies 3527486510" measuredOn="2026-11-02">
  <Body key="Fat_Female" facing="south">
    <Reference shirt="ShirtBasic_Fat_Female_south" />            <!-- absent = no WDI shirt for this body: fallback rules -->
    <BodyTop>157</BodyTop> <BodyBottom>448</BodyBottom> <ChestWidth>266</ChestWidth>   <!-- px, body alpha above 40; chest width at 0.35 of the body height -->
    <Landmarks>                                                    <!-- px, in the body texture -->
      <NipL x="154" y="278"/> <NipR x="358" y="278"/> <Navel x="256" y="350"/>
      <HipL x="179" y="372"/> <HipR x="333" y="372"/> <Apex x="256" y="394"/>
    </Landmarks>
    <BreastEdge>                                                   <!-- lower edge of each breast, outer end (armpit) to sternum -->
      <Left>x,y x,y ...</Left> <Right>x,y x,y ...</Right>
    </BreastEdge>
    <Collar style="black|grey" grey="115" strokeWidth="7.0">       <!-- style and width of the collar line on the reference shirt -->
      <Ring>x,y x,y ... (16 points by angle, 0 = right, counter-clockwise on screen, on the stroke centre line)</Ring>
    </Collar>
    <Outline thickness="14">                                       <!-- outward offset of the reference shirt outline over the body outline -->
      <Offset angle="0" px="7"/> <Offset angle="22.5" px="6"/> ... (16 samples along the body contour by angle, signed: negative = inside the body outline)
    </Outline>
  </Body>
</ShirtTransfer>
```

All coordinates are in the 512 px body texture; WDI's shirt textures are 256 px and are scaled by 2 before any measure.

## Fallback (body with no `Reference`)

Tight outline (the body's own outline, thickness from the nearest measured body), collar ring from the Thin ring scaled by the chest width ratio, stroke width and grey of the Thin shirt. Every fallback use is logged once per body and flagged in the picture caption for the owner.

## Runtime notes (A)

- Cache key: hash of the garment texture pixels + body key + facing + table version.
- First draw: the transfer runs once per garment texture and body; later draws read the cache; the cost is paid per garment, never per frame.
- Hook: where the mod already patches TailorMade's `BakeFitted`.
- The DLL reproduces the prototype's numbers on the same inputs before any new feature: identity test (WDI Fat shirt onto itself): mean skeleton distance <= 0.5 px both ways, stroke width median within 5 %, same components and loops.
- `Check-HarmonyContract` on the DLL before it ships.

## Measure (B)

- Landmarks: nipples, navel and crotch apex from the body pixels; hips estimated (0.55 of the half width at half way navel to apex) until the owner confirms them.
- Breast edge: best path under each nipple maximising the white-to-darker step going down (1 px per column, nipple + 12 to + 110 rows).
- Collar ring: the largest ink piece inside the collar box of the reference shirt, thinned to a skeleton, 16 points by angle; ink = dark pixels (mean RGB under 60) for black rings, more than 40 levels darker than the 15 px local mean for grey lines.
- Outline offset: per-contour offset of the reference shirt silhouette from the body silhouette, sampled at 16 angles (not only top, left, right, bottom), signed.
- Stroke width: median of 2 x Euclidean distance - 1 on the skeleton of the reference's interior ink.
