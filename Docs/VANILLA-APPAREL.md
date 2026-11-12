# Vanilla body garments (Core and the five DLC)

Every apparel ThingDef of RimWorld's own Data (Core, Royalty, Ideology, Biotech, Anomaly, Odyssey) worn on the body (OnSkin, Middle or Shell) with a worn graphic, read from the Defs on 2026-10-15 by a throwaway parser (layers and body parts inherited from the abstract parents). Headgear, eye covers, belts, packs and utility items are left out. Vanilla trousers (`Apparel_Pants`, `Apparel_KidPants`) carry no worn graphic: a mod such as AB's Visible Pants supplies it, so they are not in the list but are part of any pass.

| DLC | defName | Label | Layers | Body parts |
|---|---|---|---|---|
| Anomaly | `Apparel_LabCoat` | lab coat | Shell | Torso+Neck+Shoulders+Arms |
| Biotech | `Apparel_Sash` | sash | Middle | Torso |
| Biotech | `Apparel_MechlordSuit` | mechlord suit | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Biotech | `Apparel_KidParka` | kid parka | OnSkin | Torso+Neck+Shoulders+Arms |
| Biotech | `Apparel_KidRomper` | kid romper | OnSkin | Torso+Neck+Shoulders+Arms+Legs |
| Biotech | `Apparel_KidShirt` | kid shirt | OnSkin | Torso+Shoulders |
| Biotech | `Apparel_KidTribal` | kid tribalwear | OnSkin | Torso+Legs |
| Biotech | `Apparel_Bandolier` | heavy bandolier | Shell | Torso |
| Core | `Apparel_FlakVest` | flak vest | Middle | Torso+Neck |
| Core | `Apparel_ArmorRecon` | recon armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Core | `Apparel_PlateArmor` | plate armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Core | `Apparel_PowerArmor` | marine armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Core | `Apparel_BasicShirt` | T-shirt | OnSkin | Torso+Shoulders |
| Core | `Apparel_CollarShirt` | button-down shirt | OnSkin | Torso+Neck+Shoulders+Arms |
| Core | `Apparel_TribalA` | tribalwear | OnSkin | Torso+Legs |
| Core | `Apparel_Cape` | cape | Shell | Torso+Neck+Shoulders+Arms+Legs |
| Core | `Apparel_Duster` | duster | Shell | Torso+Neck+Shoulders+Arms+Legs |
| Core | `Apparel_FlakJacket` | flak jacket | Shell | Torso+Neck+Shoulders+Arms |
| Core | `Apparel_Jacket` | jacket | Shell | Torso+Neck+Shoulders+Arms |
| Core | `Apparel_Parka` | parka | Shell | Torso+Neck+Shoulders+Arms |
| Core | `Apparel_Robe` | robe | Shell | Torso+Shoulders+Arms+Legs |
| Ideology | `Apparel_BodyStrap` | slave body strap | Shell | Torso |
| Ideology | `Apparel_Burka` | burka | Shell | FullHead+UpperHead+Neck+Shoulders+Torso+Legs+Arms |
| Odyssey | `Apparel_Vacsuit` | vacsuit | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Odyssey | `Apparel_VacsuitChildren` | kid vacsuit | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_Corset` | corset | Middle | Torso |
| Royalty | `Apparel_PsyfocusVest` | eltex vest | Middle | Torso+Neck+Shoulders |
| Royalty | `Apparel_VestRoyal` | formal vest | Middle | Torso |
| Royalty | `Apparel_ArmorCataphract` | cataphract armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorCataphractPhoenix` | phoenix armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorCataphractPrestige` | prestige cataphract armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorLocust` | locust armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorMarineGrenadier` | grenadier armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorMarinePrestige` | prestige marine armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_ArmorReconPrestige` | prestige recon armor | Middle+Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_PsyfocusShirt` | eltex shirt | OnSkin | Torso+Shoulders |
| Royalty | `Apparel_ShirtRuffle` | formal shirt | OnSkin | Arms+Neck |
| Royalty | `Apparel_PsyfocusRobe` | eltex robe | Shell | Torso+Neck+Shoulders+Arms+Legs |
| Royalty | `Apparel_RobeRoyal` | prestige robe | Shell | Torso+Neck+Shoulders+Arms+Legs |

## Categories, by what Venus Touch Waistlines does to them

Read from the code on 2026-10-15 (`JacketArt.Kind`: Shell on the torso without legs is a jacket, OnSkin on the torso without legs is a shirt, anything on the legs is left alone; `DressArt.IsFullLength`: torso and legs; `WdiAppPatterns`: the APP masks, experimental, off by default).

| # | Category | Garments | What the mod does |
|---|---|---|---|
| 1 | Trousers | `Apparel_Pants`, `Apparel_KidPants` (art from AB's Visible Pants) | start on WDI's underwear line; APP mask when the experimental setting is on |
| 2 | Shirts (OnSkin, torso, no legs) | `Apparel_BasicShirt`, `Apparel_KidShirt`, `Apparel_CollarShirt`, `Apparel_PsyfocusShirt`, `Apparel_KidParka` | hem cut just under the trousers (`shortenShirts`); BasicShirt and KidShirt also get the APP mask when on |
| 3 | Shirt without torso | `Apparel_ShirtRuffle` (arms and neck only) | nothing |
| 4 | Full-length OnSkin (torso and legs) | `Apparel_TribalA`, `Apparel_KidTribal`, `Apparel_KidRomper` | left whole |
| 5 | Middle vests (torso, no legs) | `Apparel_FlakVest`, `Apparel_Corset`, `Apparel_PsyfocusVest`, `Apparel_VestRoyal`, `Apparel_Sash` | nothing |
| 6 | Jackets and coats (Shell, torso, no legs) | `Apparel_Jacket`, `Apparel_Parka`, `Apparel_FlakJacket`, `Apparel_LabCoat`, `Apparel_BodyStrap`, `Apparel_Bandolier` | kept full length, stretched to the trousers' hem (`keepJacketsLong`) |
| 7 | Long shell (Shell with legs) | `Apparel_Duster`, `Apparel_Cape`, `Apparel_Robe`, `Apparel_PsyfocusRobe`, `Apparel_RobeRoyal`, `Apparel_Burka` | left whole |
| 8 | Armour and suits (Middle and Shell, with legs) | `Apparel_ArmorRecon`, `Apparel_PlateArmor`, `Apparel_PowerArmor`, `Apparel_ArmorCataphract`, `Apparel_ArmorCataphractPhoenix`, `Apparel_ArmorCataphractPrestige`, `Apparel_ArmorLocust`, `Apparel_ArmorMarineGrenadier`, `Apparel_ArmorMarinePrestige`, `Apparel_ArmorReconPrestige`, `Apparel_Vacsuit`, `Apparel_VacsuitChildren`, `Apparel_MechlordSuit` | left whole |

Kid garments (`Kid*`, `Apparel_VacsuitChildren`) are worn by the two child profiles only.

## Planned captures

1. **One capture per garment**, alone over the underwear, on the ten WDI profiles, three facings.
2. **Then the crossings** that put two categories in contact at the waist or over each other:
   shirts (2) x trousers (1); shirts and trousers x middle vests (5); shirts and trousers x jackets (6);
   shirts and trousers x long shells (7); full-length OnSkin (4) x jackets (6). Categories 3 and 8 alone only.
