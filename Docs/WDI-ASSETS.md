# What WDI's Realistic Bodies provides

Workshop 3527486510, folder read on 2026-10-15. Every texture exists as `_south`, `_east` and `_north` PNG (a `.dds` beside each). WDI has no `Defs`: it only replaces textures by path, so a garment is redrawn only for the bodies listed.

## Bodies (`Things/Pawn/Humanlike/Bodies/`)

- Naked: `Male`, `Female`, `Thin`, `Thin_Female`, `Hulk`, `Hulk_Female`, `Fat`, `Fat_Female`, `Child`, `FurChild`.
- Skins, for the eight adult keys: `BarkSkin`, `FurCovered`, `Insectskin`, `InsectskinMineralized`.
- `Pawn/ScalySkin`, `Pawn/SyntheticSkin`, `Humanlike/PerfectBody` (`*_Female` keys).

## Underwear (`UWUnderwear/`, for Underwhere)

`boxers`, `panties`, `bra`, `chestwrap`, `tanktop`, `longjohns`: the eight adult keys. `loincloth`: the eight adult keys and `Child`. This is where the waist lines of the cut rule come from (boxers and panties for adults, loincloth for children).

## Apparel redrawn for WDI's female bodies

Only for `Thin_Female`, `Hulk_Female`, `Fat_Female` (and `Female` where said): the body types FemaleBodyVariants adds. The male and average bodies use the garment's own art.

| Path | Garment | Bodies |
|---|---|---|
| `Things/Pawn/Humanlike/Apparel/ShirtBasic` | vanilla T-shirt | Thin_Female, Hulk_Female, Fat_Female |
| `Things/Pawn/Humanlike/Apparel/ShirtButton` | vanilla button-down shirt | same |
| `Things/Pawn/Humanlike/Apparel/TribalA` | vanilla tribalwear | same |
| `Things/Pawn/Humanlike/Apparel/EltexShirt` | Royalty eltex shirt | same |
| `Things/Pawn/Humanlike/Apparel/VestRoyal` | Royalty formal vest | same |
| `Things/Pawn/Humanlike/Apparel/CorsetRoyal` | Royalty corset | same, and Female |
| `Things/Pawn/Humanlike/Apparel/BodyStrap` | Ideology slave body strap | Thin_Female, Hulk_Female, Female |
| `Things/Pawn/Humanlike/Apparel/UNA_Dress_sitagi` | UNAGI dress underlayer | Thin_Female, Hulk_Female, Fat_Female |
| `Things/Apparel/Blouse`, `CasualTShirt`, `ChefsUniform`, `Jumpsuit`, `MilitaryUniform`, `Scrubs`, `SheriffShirt`, `ShirtandTie`, `ShirtFleece`, `TankTop`, `Tunic` | modded shirts (another apparel mod's paths) | Thin_Female, Hulk_Female, Fat_Female |

`CorsetRoyal` also holds a misnamed `Fat_Femaleeast.png` (no underscore before the facing): the game will not find it under that name.

Not provided by WDI: trousers of any kind (vanilla trousers have no worn art; AB's Visible Pants or General Textures Collection supply it), jackets, coats, robes, armour, and any garment for the `Male`, `Thin`, `Hulk`, `Fat` or `Child` bodies.
