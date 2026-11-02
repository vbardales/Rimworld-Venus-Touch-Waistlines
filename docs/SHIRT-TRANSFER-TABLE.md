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

## What is anchored by landmarks, what by relation (for bodies with no drawn breasts or belly)

A vanilla body (and most third-party bodies) has no nipple, no breast edge and no navel stroke. Only the silhouette and the crotch can be read from it. So the map between two bodies rests on two kinds of anchors:

| Anchor | Exists on vanilla | Exists on WDI | Used for |
|---|---|---|---|
| Neck junctions (left, right), top of the torso | yes (silhouette) | yes | collar placement, upper layer |
| Shoulder tips, armpits | yes (silhouette) | yes | sleeves, upper layer sides |
| Waist narrowest points (left, right) | yes (silhouette) | yes | the line between layers when no breast edge exists |
| Hip widest points, crotch apex, bottom of the torso | yes (silhouette) | yes | lower layer, hem |
| Nipples, breast lower edge | no | yes | breast layer: WDI-side only |
| Navel | no | yes (stroke) | lower layer centre: WDI-side only |

Rule: a landmark absent on the source body is not matched; the corresponding WDI feature is placed by RELATION (its position as a share of the torso height and chest width, read from the WDI table), and the source garment carries nothing there. The breast layer on a vanilla-to-WDI transfer is therefore an invention on the WDI side: the garment's fill is stretched into it, its strokes are not. This is the case most likely to look wrong; it is tested first, on a loose-PNG apparel mod drawn for the vanilla body (front view), with the vanilla bodies dumped by ticket f38f.

Hip landmarks are read from the silhouette (widest points), no longer estimated at 0.55 of the half width.

## Acceptance of a transfer (Audit, 2026-11-02, fixed before any run; relational, no pixel IoU)

Input: a real Core shirt (front) on its vanilla body (both from the f38f dump). Measured on the source (garment over its own body), required on the result (WDI body):

- C1 outline: along the contour (16+ samples), garment offset to the body silhouette on the result = source offset scaled by the local body scale, +-2 px at 512.
- C2 neckline: width over shoulder width and depth over torso length kept within +-5 %.
- C3 hem at the same fraction of torso length (+-3 %); sleeve ends at the same fraction of arm length.
- C4 strokes: same components and loops as the source (no new strokes); width median within +-10 % of the source, IQR no wider; no stroke leaving the silhouette.
- C5 garment area over body area = source ratio +-5 %.
- C6 landmark residuals (shoulders, neck, waist, hip, crotch) <= 2 px.

Controls first: vanilla garment on its own vanilla body = identity (skeleton <= 0.5 px, width median within 5 %); the WDI identity on every body with a WDI shirt (Thin, Fat, Hulk, then the men). The breast layer is run as its own step: baseline without it, then with it, and the difference reported. The owner then looks at side-by-side pictures, the only subjective step. If the criterion fails, the method changes, not the criterion. Order of the study: (1) WDI identities, (2) vanilla to WDI, (3) Beautiful Bodies (texture folder listed first).

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
- Collar ring: the largest ink piece inside the collar box of the reference shirt, thinned to a skeleton, 16 points by angle, taken on the SKELETON at the ring's true extent (never on an ink bounding box: on the Thin shirt the ring top is 17 px above the box of its thicker lower part, and a box-derived point splits the ring); ink = dark pixels (mean RGB under 60) for black rings, more than 40 levels darker than the 15 px local mean for grey lines.
- Outline offset: per-contour offset of the reference shirt silhouette from the body silhouette, sampled at 16 angles (not only top, left, right, bottom), signed.
- Stroke width: median of 2 x Euclidean distance - 1 on the skeleton of the reference's interior ink.

## Pipeline constants validated by the identity test (step 1, accepted by Audit 2026-11-02)

- Stroke redraw radius bias: proportional to the stroke width, radius x (1 + 0.4 / 3.5) (the same +0.4 px at 7 px). A fixed +0.4 px over-thickened the Hulk's 3.5 px grey line by 34 %.
- Fill low-pass: box blur 6 px, three passes, garment pixels only, strokes redrawn after it.
- Step 1 results (WDI shirt onto its own body): Thin skeleton 0.2 / 0.5 px, width 7.2 / 7.0, 1 component 1 loop; Fat 0.2 / 0.2, 7.2 / 7.0, 3 and 1; Hulk 0.2 / 0.2, 3.5 / 3.5, 1 loop, 5 components against 6 (one small piece merged: documented deviation, accepted, not a failure).
- Bodies with no WDI shirt, so no identity test and fallback only: Female, and all four men (WDI ships Naked_Male/Thin/Fat/Hulk bodies but no ShirtBasic for them). Step 1b (men) is therefore not an identity test; the men can only be judged on the relation criterion C1-C6 against a vanilla garment.
