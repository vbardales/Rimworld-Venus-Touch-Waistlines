# Annuaire Workshop — Venus / WDI

Registre cumulatif des liens transmis pour l'étude de la compatibilité de
Venus Touch Waistlines. Une entrée `inspecté localement` signifie que la copie
Workshop installée a été lue (About/Defs/patches pertinents) ; ce n'est pas une
validation en jeu. Les pages Steam peuvent être retirées ou afficher une
compatibilité obsolète : l'état courant reste à vérifier avant publication.

## Légende

| Statut | Sens |
| --- | --- |
| moteur | Mod qui rend, transforme ou sélectionne l'apparence des vêtements. |
| silhouettes | Mod qui fournit ou change des corps. |
| contenu | Bibliothèque de vêtements ou retextures : cas de test, pas moteur. |
| garde-fou | Mod qui filtre, superpose ou altère la sélection/le rendu. |
| inspecté localement | Copie installée analysée dans cette machine. |
| page seulement | Titre/résumé indexé, sources locales absentes. |

## Familles de géométrie corporelle

**Cible unique : WDI SA.** Les familles ci-dessous sont un corpus de comparaison
et de provenance des vêtements ; Venus ne génère pas de sortie destinée à ces
autres corps.

Taxonomie transmise par Virginie le 9 octobre 2026 depuis la fiche Workshop
`3792365853`. C'est une classification visuelle à vérifier dans les sources de
chaque mod, pas un synonyme des `BodyTypeDef` vanilla.

| Famille | Corps cités | Conséquence pour Venus |
| --- | --- | --- |
| Tronçons de jambes | WDI, Beautiful Bodies, FemaleBB, Malang Bodies, ScrubDaddy, Sin's Bodies, Just Bodies, Chanfana's Bodies, Chanfana x MaliBody, TREB's Body (chunk) | Famille WDI de référence : les patrons doivent respecter cette base de jambe raccourcie. |
| Sans jambes | Erin's Body, UNAGI et leurs Female Variants, RimNude, Chiseled Bodies, SA0 / Sized Apparel Zero | Corpus comparatif : ne pas générer de patron pour cette famille ; mesurer seulement les écarts de bas du corps et de jonction pantalon/robe. |
| Intermédiaire | Simple Bodies, ABC Body 2 | Corpus comparatif distinct à mesurer, sans le rattacher arbitrairement à une famille extrême. |
| Corps avec jambes | Compatible Body 2, [NL] Realistic Body, Hooman, Imozhou Body | Étalon de provenance des vêtements à jambes complètes ; la sortie reste un patron WDI SA. |

## Moteurs et silhouettes

| ID | Mod | Catégorie | Lecture utile pour Venus | Statut |
| --- | --- | --- | --- | --- |
| [2480887589](https://steamcommunity.com/sharedfiles/filedetails/?id=2480887589) | Apparel Paper Pattern (APP) | moteur | Applique masque, burn, offset et échelle selon race, `BodyType` et couche. Ne porte pas de clé de genre. | source lue le 9 octobre 2026 |
| [2839443438](https://steamcommunity.com/workshop/filedetails/?id=2839443438) | WRelicK's APP Utilities / APP Body Type Overrider | moteur | Extension APP : ses `GenderRequirements` filtrent les patrons après `BodyType`. C'est la clé de patrons WDI séparés pour Thin/Fat/Hulk hommes et femmes ; le Body Type Overrider seul ne résout pas le sexe. | source lue le 9 octobre 2026 |
| [2839518933](https://steamcommunity.com/sharedfiles/filedetails/?id=2839518933) | THIGAPPE | moteur | Collection de patrons APP humains par corps et famille de vêtement ; référence de structure, pas dépendance Venus. | inspecté localement |
| [3344769721](https://steamcommunity.com/sharedfiles/filedetails/?id=3344769721) | THIGAPPE Masking Patches | moteur | Exceptions de classement de masque, notamment pour robes. Modèle de registre d'exceptions. | inspecté localement |
| [3611523059](https://steamcommunity.com/sharedfiles/filedetails/?id=3611523059) | THIGAPPE ABC Body 2 Patch | moteur | Patches d'offset, d'échelle et d'exclusion par corps : les masques seuls ne suffisent pas. | inspecté localement |
| [2846970684](https://steamcommunity.com/sharedfiles/filedetails/?id=2846970684) | THIGAPPE Xeva Body Patch | moteur | Remplace les masques APP de THIGAPPE pour Xeva ; précédent direct d'un pack de patrons par silhouette. | inspecté localement |
| [3756915448](https://steamcommunity.com/sharedfiles/filedetails/?id=3756915448) | TailorMade | moteur | Refit générique par bornes alpha de silhouette. Bon secours pour l'art absent, insuffisant pour différencier les variantes féminines WDI. | inspecté localement |
| [3758410877](https://steamcommunity.com/sharedfiles/filedetails/?id=3758410877) | Apparel Race Renderer | garde-fou | Retire le refit THIGAPPE et permet des réglages de rendu. Configuration concurrente à exclure d'un test APP/Venus. | inspecté localement |
| [3632480044](https://steamcommunity.com/sharedfiles/filedetails/?id=3632480044) | Layered Apparel | garde-fou | Change l'apparence par superposition de vêtements ; doit figurer dans une matrice de conflit de couches. | inspecté localement |
| [3629753146](https://steamcommunity.com/sharedfiles/filedetails/?id=3629753146) | Restrict Undrawn Apparel | garde-fou | Empêche l'équipement sans texture disponible pour le type de corps. Test de non-régression essentiel pour les patrons WDI. | inspecté localement |
| [3527486510](https://steamcommunity.com/sharedfiles/filedetails/?id=3527486510) | WDI's Realistic Bodies | silhouettes | Dix silhouettes humaines de référence : Male, Female, Male_Thin, Male_Hulk, Male_Fat, Female_Thin, Female_Hulk, Female_Fat, Kid_Boy, Kid_Girl. | inspecté localement |
| [2480905277](https://steamcommunity.com/sharedfiles/filedetails/?id=2480905277) | APP for Compatible Body 2 | silhouettes | Pack APP pour corps compatible ; précédent de masques et burn dédiés, mais couverture limitée à ses silhouettes. Son contrat APP est `RaceName + BodyType + ApparelLayer`, avec filtres par package et def. | inspecté localement |
| [3366699008](https://steamcommunity.com/sharedfiles/filedetails/?id=3366699008) | Hooman Cute Reborn | silhouettes | Retexture visant surtout Female ; utile pour mesurer les limites d'un support mono-silhouette. | inspecté localement |
| [3811425282](https://steamcommunity.com/sharedfiles/filedetails/?id=3811425282) | NL Female + Hooman Male \| Transmog & Wardrobe | silhouettes | Patch de compatibilité récent autour d'art NL/Hooman ; mécanisme non vérifié faute de copie locale. | page seulement |
| [3809028157](https://steamcommunity.com/sharedfiles/filedetails/?id=3809028157) | HumanBodyRefit | silhouettes | Corps humains originaux annoncés sans redistribution de NL Realistic Body ; source et interactions non vérifiées. | page seulement |

## Bibliothèques et cas de test

| ID | Mod | Catégorie | Lecture utile pour Venus | Statut |
| --- | --- | --- | --- | --- |
| [3352990362](https://steamcommunity.com/sharedfiles/filedetails/?id=3352990362) | UNAGI Royalty Apparel | contenu | Robes et tenues nobles : cas principal pour robe, bustier et drapé. | inspecté localement |
| [3379688555](https://steamcommunity.com/sharedfiles/filedetails/?id=3379688555) | UNAGI Apparel APP Extension | contenu | Définitions APP ciblées pour UNAGI ; exemple d'exceptions par bibliothèque. | inspecté localement |
| [3145326932](https://steamcommunity.com/sharedfiles/filedetails/?id=3145326932) | ATH's Retexture Female Apparel | contenu | Retextures Female transformant souvent les habits en robes ; cas important de veste/robe. | inspecté localement |
| [3604442772](https://steamcommunity.com/sharedfiles/filedetails/?id=3604442772) | ZX's Apparel for NL Realistic Body | contenu | Art déjà dessiné pour NL ; Venus doit le laisser intact plutôt que le refitter aveuglément. | inspecté localement |
| [3697882587](https://steamcommunity.com/sharedfiles/filedetails/?id=3697882587) | ZX's Tattered Apparel Framework | contenu | Framework/vêtements usés ZX ; à classer après lecture de ses sources. | page seulement |
| [3036547755](https://steamcommunity.com/sharedfiles/filedetails/?id=3036547755) | Remodeled Armors for NL Realistic Body | contenu | Armures vanilla et DLC redessinées pour NL, annoncées Female-only. | page seulement |
| [3038534472](https://steamcommunity.com/sharedfiles/filedetails/?id=3038534472) | Medieval Overhaul Remodeled Armors for NL Realistic Body | contenu | Armures Medieval Overhaul redessinées pour NL, annoncées Female-only. | page seulement |
| [3300430241](https://steamcommunity.com/sharedfiles/filedetails/?id=3300430241) | Compatible Armor | contenu | Armures Recon, Marine, Cataphract et Phoenix pour corps compatibles/THIGAPPE. | page seulement |
| [3464873413](https://steamcommunity.com/sharedfiles/filedetails/?id=3464873413) | Socks and Stockings for NL Realistic Body | contenu | Test indispensable de couche jambes sous pantalon/jupe. | page seulement |
| [2585928816](https://steamcommunity.com/sharedfiles/filedetails/?id=2585928816) | Eccentric Tech - Angel Apparel | contenu | Tenues multi-couches et couvre-chefs d'une race ; test d'exclusion/race, pas cible WDI directe. | inspecté localement |
| [3295274246](https://steamcommunity.com/sharedfiles/filedetails/?id=3295274246) | Bread Mo's Valentine's Day apparel | contenu | Robes, couvre-chefs et tenues fantaisie ; test de couches et de silhouettes. | inspecté localement |
| [3247891238](https://steamcommunity.com/sharedfiles/filedetails/?id=3247891238) | Ratkin Apparel+ (unofficial) | contenu | Vêtements d'une race HAR propre : doit rester hors du refit humain WDI sauf support explicite. | inspecté localement |
| [3635005747](https://steamcommunity.com/sharedfiles/filedetails/?id=3635005747) | Faction Weapons and Apparel Set | contenu | Configure des pools d'équipement de faction ; pas un refit, mais source de combinaisons de vêtements à tester. | page seulement |
| [2986402536](https://steamcommunity.com/sharedfiles/filedetails/?id=2986402536) | AB's Visible Pants | contenu | Fournit les pantalons visibles que Venus améliore déjà ; conserver comme intégration dédiée. | inspecté localement |
| [2264108215](https://steamcommunity.com/sharedfiles/filedetails/?id=2264108215) | XND Visible Pants | contenu | Fournisseur historique de pantalons, jeans, shorts et jupes visibles. Cas de test distinct d'AB, avec ses propres chemins de texture. | inspecté localement |
| [926698084](https://steamcommunity.com/sharedfiles/filedetails/?id=926698084) | XND Visible Pants (ancienne fiche) | contenu | Ancienne publication du même objectif ; ne pas charger en même temps que XND actuel sans vérifier les package IDs et chemins. | page seulement |
| [2985986536](https://steamcommunity.com/sharedfiles/filedetails/?id=2985986536) | Pawn Visible Pants | contenu | Graphismes pour pantalon, flak pants et kid pants vanilla ; n'impose pas le rendu au-dessus des autres couches. | inspecté localement |
| [3671309201](https://steamcommunity.com/sharedfiles/filedetails/?id=3671309201) | Visible Pants Retexture | contenu | Retextures 512×512 pour XND ou AB, y compris Vanilla Apparel Expanded. Test de compatibilité de fournisseur et de résolution. | inspecté localement |
| [3707481634](https://steamcommunity.com/sharedfiles/filedetails/?id=3707481634) | Medieval Visible Pants Addon | contenu | Textures de dessous de taille pour Medieval Overhaul/Tailor, avec couches de sous-pantalon. Test de pantalon historique et de superposition. | inspecté localement |
| [3772689105](https://steamcommunity.com/sharedfiles/filedetails/?id=3772689105) | Pumpkinlass Visible Pants Retexture | contenu | Retexture pensée pour des hauts moulants de forme vanilla. Test négatif pour les hauts longs ou les silhouettes WDI divergentes. | inspecté localement |
| [3799793039](https://steamcommunity.com/sharedfiles/filedetails/?id=3799793039) | Pawn Visible Pants — VAE Patch | contenu | Ajoute jeans, shorts, trousers et jupe de Vanilla Apparel Expanded ; couvre les catégories de bas à séparer dans Venus. | inspecté localement |
| [3795174803](https://steamcommunity.com/sharedfiles/filedetails/?id=3795174803) | Simple Pants and Shirts | contenu | Fournit notamment crop tops, chemises et pantalons. Cas de référence : un haut court ne doit jamais être allongé. | inspecté localement |
| [3169180308](https://steamcommunity.com/sharedfiles/filedetails/?id=3169180308) | Smaller Shirt Textures | contenu | Retexture les chemises vanilla afin qu'elles couvrent visuellement seulement le haut du torse. Cas de découpe de chemise. | inspecté localement |
| [3771446780](https://steamcommunity.com/sharedfiles/filedetails/?id=3771446780) | Female Variant Clothing: For Fat Bodies | contenu | Variantes féminines pour corps Fat, avec intégrations Visible Pants. Cas central pour la clé graphique `Fat_Female`. | inspecté localement |
| [3789119336](https://steamcommunity.com/sharedfiles/filedetails/?id=3789119336) | General Textures Collection | contenu | Collection dont les textures Visible Pants sont conditionnées à XND ; Venus les lit déjà comme complément d'AB. | inspecté localement |
| [1349843576](https://steamcommunity.com/sharedfiles/filedetails/?id=1349843576) | TY Slender Female Body and BasicApparel | contenu | Ancien corps Female mince avec vêtements de base ; référence historique, non cible WDI actuelle. | inspecté localement |
| [3687417406](https://steamcommunity.com/sharedfiles/filedetails/?id=3687417406) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [2037354634](https://steamcommunity.com/sharedfiles/filedetails/?id=2037354634) | Apparel BodyType Resolver | garde-fou | Remplace manuellement ou par XML un type de corps d'alternative quand l'art manque. Ne doit pas servir de solution automatique Venus, mais constitue un conflit/fallback à tester. | inspecté localement |
| [3363310625](https://steamcommunity.com/sharedfiles/filedetails/?id=3363310625) | Apparel Restriction based on Bodytype | garde-fou | Refuse des vêtements selon `restrictedBodyTypes`. À tester : Venus ne doit pas contourner une restriction choisie par le contenu. | page seulement |
| [3247897248](https://steamcommunity.com/sharedfiles/filedetails/?id=3247897248) | Mutie's Wicked Wardrobe | contenu | Bodystocking, leggings, hot pants, ceinture et étole : bon corpus pour sous-vêtements, jambes et accessoires. | inspecté localement |
| [2840348927](https://steamcommunity.com/sharedfiles/filedetails/?id=2840348927) | Swimwear | contenu | Bikini, haut de bikini et maillot masculin ; cas de vêtements courts, genrés et de couche underwear. | inspecté localement |
| [3798082132](https://steamcommunity.com/sharedfiles/filedetails/?id=3798082132) | Female Body Variants Continued | silhouettes | Sélectionne dynamiquement les corps `Thin_Female`, `Fat_Female` et `Hulk_Female`. Dépendance WDI fondamentale. | inspecté localement |
| [3799726535](https://steamcommunity.com/sharedfiles/filedetails/?id=3799726535) | Female Apparel Variants Continued | moteur | Sélectionne dynamiquement les textures vestimentaires `_Female` pour Thin/Fat/Hulk lorsqu'elles existent. Source de la clé graphique manquante dans APP. | inspecté localement |
| [2881748658](https://steamcommunity.com/sharedfiles/filedetails/?id=2881748658) | Female Apparel for Beautiful Bodies | contenu | Remplacements de vêtements pour corps féminins Beautiful Bodies. Cas d'art déjà spécialisé à préserver. | inspecté localement |
| [3029508162](https://steamcommunity.com/sharedfiles/filedetails/?id=3029508162) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [2999825572](https://steamcommunity.com/sharedfiles/filedetails/?id=2999825572) | Standard Body Type Only | garde-fou | Contraint certaines races au type de corps standard. Incompatible par intention avec une généralisation non filtrée des corps WDI. | inspecté localement |
| [3688530033](https://steamcommunity.com/sharedfiles/filedetails/?id=3688530033) | Children Wear Anything | garde-fou | Permet aux enfants de porter l'équipement normalement exclu. Dépendance de test importante pour valider les patrons Child. | inspecté localement |
| [3237739433](https://steamcommunity.com/sharedfiles/filedetails/?id=3237739433) | Ponpeco Kids' Clothes | contenu | Garde-robe Biotech dédiée aux enfants : test Child pour hauts, manteaux, cape, accessoires et chemins graphiques multiples. Licence CC BY-NC-ND : ne pas réutiliser ses assets. | inspecté localement |
| [3769650943](https://steamcommunity.com/sharedfiles/filedetails/?id=3769650943) | TailorMade Unlock Fix | garde-fou | Empêche TailorMade de supprimer les restrictions HAR durant le chargement XML. À charger après TailorMade ; obligatoire dans les tests HAR avec ce moteur. | inspecté localement |
| [3710288053](https://steamcommunity.com/sharedfiles/filedetails/?id=3710288053) | Body Hair Tattoos | contenu | Tatouages corporels, pensés pour un corps HD. Élément de backlog « pilosité » : à vérifier sous hauts courts et vêtements transparents, sans le traiter comme vêtement. | inspecté localement |
| [2068281501](https://steamcommunity.com/sharedfiles/filedetails/?id=2068281501) | Beautiful Bodies | silhouettes | Corps féminin historique ; référence pour l'art spécialisé féminin, non cible directe de WDI. | page seulement |
| [3749685861](https://steamcommunity.com/sharedfiles/filedetails/?id=3749685861) | Physical Hair | garde-fou | Anime les cheveux par maillage dynamique. N'affecte pas le patron de corps, mais peut révéler des conflits d'ordre avec coiffures/couvre-chefs. | page seulement |
| [3792365853](https://steamcommunity.com/sharedfiles/filedetails/?id=3792365853) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [2833465153](https://steamcommunity.com/sharedfiles/filedetails/?id=2833465153) | TY Female Body — Upscaled | silhouettes | Corps Female et vêtements de base à plus haute résolution ; précédent de résolution, pas une base d'assets à réutiliser. | page seulement |
| [3804244566](https://steamcommunity.com/sharedfiles/filedetails/?id=3804244566) | Pawn Size Editor Body Offsets Stuff | garde-fou | Échelle et offsets par pawn et par facing ; le corps et l'apparel suivent, tête/cheveux/chapeaux non. Test de compatibilité transformée indispensable. | inspecté localement |
| [3371718920](https://steamcommunity.com/sharedfiles/filedetails/?id=3371718920) | Bunny Armour From Hooman Cute | contenu | Armures, oreilles-casques et bodysuit ; cas de superposition armure/casque et de contenu chargeant après THIGAPPE. | inspecté localement |
| [3686645385](https://steamcommunity.com/sharedfiles/filedetails/?id=3686645385) | NSFW Female Body Texture for Nal | silhouettes | Patch qui remplace seulement Female pour NL Realistic Body. Cas de corps spécialisé à isoler : pas une texture ni une dépendance WDI. | inspecté localement |
| [3198510534](https://steamcommunity.com/sharedfiles/filedetails/?id=3198510534) | More Nal Clothes | contenu | Sous-vêtements, bas et petits vêtements pour NL Realistic Body. Cas de test de couches près du corps ; support déclaré seulement jusqu'à 1.5. | inspecté localement |
| [1870010563](https://steamcommunity.com/sharedfiles/filedetails/?id=1870010563) | UnderWhere | contenu | Quatre ensembles de sous-vêtements (masculin, féminin, tribal, froid) susceptibles d'être visibles sous les vêtements. Cas de couverture et de priorité de couche. | inspecté localement |
| [High Heels of Rim](https://www.loverslab.com/files/file/40832-high-heels-of-rim/) | High Heels of Rim | contenu | Talons avec effets de jeu : test de ligne pied/jambe et de bottes, pas de dépendance WDI. | page seulement |
| [Kilo's High Heels Vanilla-style Retexture](https://www.loverslab.com/files/file/46533-16-kilos-high-heels-of-rim-vanilla-style-retexture/) | High Heels Vanilla-style Retexture | contenu | Retexture du précédent : doit préserver la géométrie du pied, sans imposer d'asset Venus. | page seulement |
| [High Heels of Rim: Extreme](https://www.loverslab.com/files/file/48162-high-heels-of-rim-extreme/) | High Heels of Rim: Extreme | contenu | Variantes de talons de ballet ; cas de contrainte maximale sur la ligne du pied. | page seulement |
| [3337758778](https://steamcommunity.com/sharedfiles/filedetails/?id=3337758778) | UnderWhere Medieval | contenu | Sous-vêtements médiévaux avec tags Sanguophage/Ancient ; extension directe d'UnderWhere à tester sous armures et robes. | inspecté localement |
| [3664319933](https://steamcommunity.com/sharedfiles/filedetails/?id=3664319933) | UnderWhere — Greece and Japan Add-on | contenu | Sous-vêtements de style grec/japonais ; cas de vêtements courts et de couverture partielle. | inspecté localement |
| [2879594171](https://steamcommunity.com/sharedfiles/filedetails/?id=2879594171) | UnderWhereAddon v2 | contenu | Extension de contenu pour UnderWhere ; à traiter comme fournisseur supplémentaire de sous-vêtements. | inspecté localement |
| [3354891128](https://steamcommunity.com/sharedfiles/filedetails/?id=3354891128) | UnderWhere Patches | garde-fou | Change la couverture torse/jambes de certains sous-vêtements et classe un corset Royalty comme UnderWhere. Test de priorités de couches. | inspecté localement |
| [3506624860](https://steamcommunity.com/sharedfiles/filedetails/?id=3506624860) | Cloud's Extra Apparel Layers | garde-fou | Ajoute des emplacements de couches. Venus doit ignorer par défaut les couches inconnues et ne pas réordonner leur rendu. | inspecté localement |
| [3465257079](https://steamcommunity.com/sharedfiles/filedetails/?id=3465257079) | Imperial Attires | contenu | Tenues annoncées pour Female et Thin seulement. Cas de contenu explicitement incomplet selon silhouette. | inspecté localement |
| [3409778571](https://steamcommunity.com/sharedfiles/filedetails/?id=3409778571) | NewRatkinPanties (Unofficial) | contenu | Sous-vêtements Ratkin : garder hors de la règle humaine WDI, sauf support de race explicite. | page seulement |
| [3567611752](https://steamcommunity.com/sharedfiles/filedetails/?id=3567611752) | XevaFactionAddUnderwearRecipes | contenu | Ajoute des recettes de sous-vêtements à Xeva Faction. Cas de race distincte, pas cible WDI directe. | inspecté localement |
| [2014331572](https://steamcommunity.com/sharedfiles/filedetails/?id=2014331572) | Star Wars Slave Bikini Outfit | contenu | Tenue bikini à haut et bas séparés ; test de couverture minimale, sans réemploi d'assets. | inspecté localement |
| [2348051639](https://steamcommunity.com/sharedfiles/filedetails/?id=2348051639) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [3223256443](https://steamcommunity.com/sharedfiles/filedetails/?id=3223256443) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [3789231443](https://steamcommunity.com/sharedfiles/filedetails/?id=3789231443) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [3771598091](https://steamcommunity.com/sharedfiles/filedetails/?id=3771598091) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [2382617090](https://steamcommunity.com/sharedfiles/filedetails/?id=2382617090) | À identifier | contenu | Lien enregistré ; fiche Workshop et sources locales non disponibles au moment de l'indexation. | page seulement |
| [3148162289](https://steamcommunity.com/sharedfiles/filedetails/?id=3148162289) | RicoFox ACG Styles | contenu | Pack de styles d'apparence ; corpus de rendu, non moteur de refit. | inspecté localement |
| [1511204938](https://steamcommunity.com/sharedfiles/filedetails/?id=1511204938) | Hentai Fundoshi | contenu | Vêtement minimaliste : test de couverture basse et de priorité sous d'autres couches. | inspecté localement |

## Pistes liées : anatomie dynamique et couverture

Le relevé RJW transmis avec les liens ne correspond pas à une pile à charger pour
Venus. Il sert à cadrer les incompatibilités et les tests futurs :

- **RimNudeWorld et Sized Apparel Zero (SA0)** sont des bases alternatives de
  textures de corps ; le relevé déconseille de les combiner avec d'autres
  retextures de corps. Venus/WDI doit donc les traiter comme des configurations
  séparées, jamais comme dépendances ordinaires.
- **SA0 Auto Refit** et les add-ons `SizedApparel-Realistic Body` sont les
  précédents techniques les plus proches d'un refit automatique lorsque l'art
  n'a pas été dessiné à la main. Leur mécanisme, leurs caches et leur clé de
  sélection doivent être étudiés avant d'en tirer une architecture Venus.
- Les anatomies RJW sont des composants/hediffs à taille relative au corps. Le
  critère Venus est seulement la cohérence du recouvrement par les vêtements ;
  les données de gameplay et les assets de ces mods restent hors périmètre.
- Ajouter aux cas de rendu : ventre de grossesse, sous-vêtements à couverture
  réduite, bas/collants, talons et hauts dynamiquement raccourcis. Ce sont des
  catégories visuelles, pas une autorisation de reprendre leurs textures.

### Collection RimNude locale (lue le 9 octobre 2026)

Source : `C:\Users\nelim\Downloads\rimnude collection\rimnude collection`.
La collection comprend `RimNudeWorld` (package
`shauaputa.rimnudeworld`), son module Chiseled Bodies, un adaptateur SAO pour
races HAR et un module de graphismes animaux. Le noyau fournit ses propres
textures `Naked_Male`, `Naked_Female`, `Naked_Thin`, `Naked_Fat` et
`Naked_Hulk`, ainsi qu'un rendu dynamique de parties corporelles ; les modules
chargent ensuite des textures par race selon les mods présents.

**Conséquence :** RimNude appartient à la famille **sans jambes**, tout en
restant une pile de rendu dynamique à traiter comme un cas de compatibilité
séparé. Venus ne doit ni reprendre ses assets ni s'activer sur ses races ou sur
une anatomie dynamique sans une compatibilité explicite. Chiseled Bodies est
également classé sans jambes.

## Candidats à étudier avant d'étendre le périmètre

| Référence | Pourquoi elle manque encore | Statut |
| --- | --- | --- |
| [Sized Apparel Auto Refit](https://github.com/DanZinagri/SizedApparelAutoRefit) | Précédent direct de génération de textures pour vêtements sans art dédié. Sa clé est `wornPath + BodyType + genre + stade`, il annonce les chemins puis génère paresseusement au chargement de `Graphic_Multi`, injecte dans son propre `ContentHolder` et expire les caches. Son périmètre actuel est la poitrine et les vêtements couvrant le torse : reprendre l'architecture, pas l'algorithme ni le périmètre. | source lue le 9 octobre 2026 |
| [SizedApparel-Realistic Body (SARB)](https://gitgud.io/Talos/sizedapparel-realistic-body) | Add-on SA0/SAR 1.6 pour NL Realistic Body et Compatible Body 2 : remplace la silhouette humaine et les positions anatomiques, et fournit des retouches d'habits ciblées. Étalon le plus concret pour la famille avec jambes, mais pas un moteur de refit automatique à copier. | source lue le 9 octobre 2026 |
| [Sized Apparel-Realistic Body-More Apparels](https://rjw.miraheze.org/wiki/Sized_Apparel-Realistic_Body-More_Apparels) | Extensions de vêtements pour le même système, utile pour comprendre les exceptions de contenu. | source à lire |
| [Dynamically Cropped Apparel](https://rjw.miraheze.org/wiki/Dynamically_Cropped_Apparel) | Précédent de découpe du bas des chemises avec pantalons visibles. À confronter au comportement de `ShirtCut`. | source à lire |
| [Visible Pregnancy Belly Textures](https://rjw.miraheze.org/wiki/Visible_Pregnancy_Belly_Textures) | Cas de silhouette qui varie dans le temps ; définit le test de non-régression grossesse. | source à lire |
| [[NL] Realistic Body](https://steamcommunity.com/workshop/filedetails/?id=2820615654) | Dépendance de nombreuses bibliothèques déjà reçues. À garder comme corpus comparatif, distinct de WDI. | page repérée |

## Références externes transmises avec le relevé RJW

Ces liens sont conservés comme documentation de compatibilité, non comme
dépendances ou contenu Venus :

- [RJW Infotab](https://rjw.miraheze.org/wiki/RimJobWorld#RJW_Infotab)
- [Apparel Settings for RJW](https://gitgud.io/AbstractConcept/abscon-apparel-settings-for-rjw)
  et sa [fiche](https://rjw.miraheze.org/wiki/Apparel_Settings_For_RJW)
- [Apparel Tweaks for RJW](https://gitgud.io/ESeeker/abscon-apparel-settings-for-rjw)
  et sa [fiche](https://rjw.miraheze.org/wiki/Apparel_Tweaks_For_RJW)
- [RJW-Tidbits](https://gitgud.io/Ryufais/rjw-tidbits) et sa
  [fiche](https://rjw.miraheze.org/wiki/RJW-Tidbits)
- [RJW Additions](https://www.loverslab.com/files/file/44209-eseeker-rjw-forks-additions/)
  et sa [fiche](https://rjw.miraheze.org/wiki/RJW_Additions)
- [RJW Plastic Surgeries](https://gitgud.io/sssk/rjw-plastic-surgeries), sa
  [publication historique](https://loverslab.com/files/file/20433-rjw-plastic-surgeries)
  et sa [fiche](https://rjw.miraheze.org/wiki/RJW_Plastic_Surgeries)
- [RJW Balls and Ovaries](https://gitgud.io/Yhenna/rjw-now-with-balls-and-ovaries-i-guess/)
  et sa [fiche](https://rjw.miraheze.org/wiki/RJW_Balls_and_Ovaries)

## Audit de couverture — 9 octobre 2026

- **79 IDs Workshop uniques transmis : 79 catalogués.** Les deux IDs
  supplémentaires de l'annuaire sont APP et NL Realistic Body, ajoutés comme
  références d'architecture.
- **8 liens restent à identifier**, mais aucun n'est perdu : `3687417406`,
  `3029508162`, `3792365853`, `2348051639`, `3223256443`, `3789231443`,
  `3771598091` et `2382617090`.
- Une mention `page seulement` signifie que l'URL est bien conservée, mais que
  son titre ou son mécanisme n'est pas encore attesté par une copie locale.

## Règles de lecture pour les prochains liens

1. Ajouter l'ID, le titre et le lien ici dès réception.
2. Marquer `page seulement` tant qu'aucune copie locale ou source n'a été lue.
3. Ne jamais déduire qu'un mod est compatible parce qu'il est installé ou qu'une page Steam le dit.
4. Pour un mod de contenu, consigner les classes visuelles qu'il apporte : haut, haut long, pantalon, short, robe, armure, bottes, sous-vêtement, chapeau ou accessoire.
5. Pour un mod moteur, consigner sa clé de sélection (`race`, `BodyType`, genre, chemin de texture, couche, def) et ses conflits connus.
