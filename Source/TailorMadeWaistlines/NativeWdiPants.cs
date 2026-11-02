using System;
using System.Collections.Generic;
using System.Linq;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// A deliberately narrow AB-free control garment.  It supplies the worn
    /// graphic vanilla trousers lack, using WDI's installed alpha only.  APP
    /// is not involved: this is the reference path for a true translucent
    /// garment and for the black between-leg wedge.
    /// </summary>
    internal static class NativeWdiPants
    {
        private const string WdiPackageId = "WDI.Realistic.Bodies";
        private const string Path = "Venus/NativePants/Pants";
        private const string TopPath = "Venus/NativePants/Top";
        private static readonly string[] Facings = { "south", "east", "north" };
        private static readonly Dictionary<string, Texture2D> PantsTextures = new Dictionary<string, Texture2D>();
        private static readonly Dictionary<string, Texture2D> TopTextures = new Dictionary<string, Texture2D>();
        private static readonly Dictionary<string, Graphic> Graphics = new Dictionary<string, Graphic>();
        // The outline top is baked red and ignores the apparel's dye (Virginie, 2026-10-23).
        private const string OutlineTopDef = "Venus_TestOutlineTop";
        private static readonly Dictionary<string, Texture2D> OutlineTextures = new Dictionary<string, Texture2D>();
        private const string ShirtTexturePath = "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_";
        // True when the trousers are the baked blue outline (ApplyOutlineShirt): drawn white, the dye does not touch them.
        private static bool outlinePants;

        public static void Apply()
        {
            if (TailorMadeWaistlinesMod.Settings == null || !TailorMadeWaistlinesMod.Settings.enableExperimentalAppPatterns)
                return;
            if (!ModsConfig.IsActive(WdiPackageId)) return;

            ThingDef pants = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_Pants");
            ThingDef kidPants = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_KidPants");
            ThingDef shirt = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_BasicShirt");
            ThingDef kidShirt = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_KidShirt");
            if (pants?.apparel == null || kidPants?.apparel == null || shirt?.apparel == null || kidShirt?.apparel == null) return;

            ModContentHolder<Texture2D> mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
            PantsTextures.Clear();
            TopTextures.Clear();
            Graphics.Clear();
            outlinePants = false;
            foreach (WdiVisualProfile profile in WdiVisualProfiles.All)
                foreach (string facing in Facings)
                {
                    Texture2D body = ContentFinder<Texture2D>.Get("Things/Pawn/Humanlike/Bodies/Naked_" + profile.TextureKey + "_" + facing, false);
                    if (body == null) continue;
                    Texture2D underwear = ContentFinder<Texture2D>.Get(UnderwearPath(profile, facing), false);
                    if (underwear == null) continue;
                    byte[] rgba = BuildPants(profile, facing, body, underwear, out int width, out int height);
                    if (rgba == null) continue;
                    Texture2D pantsTexture = TrouserArt.Build(rgba, width, height, "Venus_NativePants_" + profile.TextureKey + "_" + facing);
                    mine.contentList[Path + "_" + profile.TextureKey + "_" + facing] = pantsTexture;
                    PantsTextures[profile.TextureKey + "_" + facing] = pantsTexture;
                    byte[] top = BuildTop(body, underwear, width, height);
                    Texture2D topTexture = TrouserArt.Build(top, width, height, "Venus_NativeTop_" + profile.TextureKey + "_" + facing);
                    mine.contentList[TopPath + "_" + profile.TextureKey + "_" + facing] = topTexture;
                    TopTextures[profile.TextureKey + "_" + facing] = topTexture;
                }

            // Female Apparel Variants asks these body types for a trailing
            // _Female texture.  The WDI keys already carry that distinction.
            Alias(mine, "Thin_Female", "Thin_Female");
            Alias(mine, "Hulk_Female", "Hulk_Female");
            Alias(mine, "Fat_Female", "Fat_Female");
            Alias(mine, "Child_Female", "Child");
            AliasTop(mine, "Thin_Female", "Thin_Female");
            AliasTop(mine, "Hulk_Female", "Hulk_Female");
            AliasTop(mine, "Fat_Female", "Fat_Female");
            AliasTop(mine, "Child_Female", "Child");
            // RimWorld creates the later PawnRenderNode only when this value
            // is non-empty.  NativeGraphicPatch replaces its usual
            // ContentFinder lookup, so these are sentinels, not asset paths.
            pants.apparel.wornGraphicPath = Path;
            kidPants.apparel.wornGraphicPath = Path;
            shirt.apparel.wornGraphicPath = TopPath;
            kidShirt.apparel.wornGraphicPath = TopPath;
            Log.Message("[Venus Touch Waistlines] native WDI diagnostic top and pants are ready for the direct apparel renderer.");
        }

        /// <summary>
        /// The garments drawn by this mod alone, no APP (Virginie, 2026-10-23).  The outline top is its own garment, the def
        /// Venus_TestOutlineTop of the Pickle test mod (Middle layer, so it is worn over a shirt): the WDI body cut on its waist line
        /// and reduced to a red outline, interior empty.  Opaque pixels, so the Cutout shader keeps every stroke.  The vanilla
        /// shirts are left alone.  The two vanilla trousers get the translucent WDI trousers of Apply.
        /// </summary>
        public static void ApplyOutlineShirt()
        {
            if (TailorMadeWaistlinesMod.Settings == null || !TailorMadeWaistlinesMod.Settings.enableExperimentalAppPatterns)
                return;
            if (!ModsConfig.IsActive(WdiPackageId)) return;
            if (ModsConfig.IsActive("nalsnoir.ApparelPaperPattern")) return;   // APP draws the shirts then

            ThingDef outlineTop = DefDatabase<ThingDef>.GetNamedSilentFail(OutlineTopDef);
            ThingDef pants = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_Pants");
            ThingDef kidPants = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_KidPants");
            if (outlineTop?.apparel == null || pants?.apparel == null || kidPants?.apparel == null) return;
            ModContentPack wdi = LoadedModManager.RunningMods.FirstOrDefault(mod =>
                string.Equals(mod.PackageIdPlayerFacing, WdiPackageId, StringComparison.OrdinalIgnoreCase));
            if (wdi == null) return;

            ModContentHolder<Texture2D> mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
            PantsTextures.Clear();
            OutlineTextures.Clear();
            Graphics.Clear();
            foreach (WdiVisualProfile profile in WdiVisualProfiles.All)
                foreach (string facing in Facings)
                {
                    Texture2D body = ContentFinder<Texture2D>.Get("Things/Pawn/Humanlike/Bodies/Naked_" + profile.TextureKey + "_" + facing, false);
                    if (body == null) continue;
                    byte[] pixels = TrouserArt.Read(body, out int width, out int height);
                    byte[] mask = WdiAppPatterns.OutlineMask(profile, WdiApparelCategory.Top, facing, pixels, width, height, wdi);
                    if (mask != null)
                    {
                        for (int i = 0; i < mask.Length; i += TrouserDetail.Channels)
                            if (mask[i + 3] != 0) { mask[i] = 255; mask[i + 1] = mask[i + 2] = 0; }
                        Texture2D texture = TrouserArt.Build(mask, width, height, "Venus_OutlineTop_" + profile.TextureKey + "_" + facing);
                        mine.contentList[TopPath + "_" + profile.TextureKey + "_" + facing] = texture;
                        OutlineTextures[profile.TextureKey + "_" + facing] = texture;
                    }
                    Texture2D underwear = ContentFinder<Texture2D>.Get(UnderwearPath(profile, facing), false);
                    if (underwear == null) continue;
                    byte[] cut = WdiAppPatterns.CutMask(profile, WdiApparelCategory.Pants, facing, pixels, width, height, wdi);
                    if (cut == null) continue;
                    byte[] rgba = BuildPantsOutline(profile, facing,
                        WdiAppPatterns.IsFrontWoman(profile, facing) ? cut : WithShirtBelowBelt(cut, profile, facing, width, height, wdi),
                        pixels, width, height);
                    Texture2D pantsTexture = TrouserArt.Build(rgba, width, height, "Venus_OutlinePants_" + profile.TextureKey + "_" + facing);
                    mine.contentList[Path + "_" + profile.TextureKey + "_" + facing] = pantsTexture;
                    PantsTextures[profile.TextureKey + "_" + facing] = pantsTexture;
                }
            outlinePants = true;
            Alias(mine, "Thin_Female", "Thin_Female");
            Alias(mine, "Hulk_Female", "Hulk_Female");
            Alias(mine, "Fat_Female", "Fat_Female");
            Alias(mine, "Child_Female", "Child");
            AliasTop(mine, "Thin_Female", "Thin_Female");
            AliasTop(mine, "Hulk_Female", "Hulk_Female");
            AliasTop(mine, "Fat_Female", "Fat_Female");
            AliasTop(mine, "Child_Female", "Child");
            outlineTop.apparel.wornGraphicPath = TopPath;
            pants.apparel.wornGraphicPath = Path;
            kidPants.apparel.wornGraphicPath = Path;
            Log.Message("[Venus Touch Waistlines] outline top ready: " + OutlineTextures.Count + " textures, trousers " + PantsTextures.Count + ".");
        }

        // The trousers' silhouette is the larger of the body cut on the trouser line and the basic shirt below that line
        // (Virginie, 2026-10-29: "le max entre le vert et la ligne bleue pour le pantalon, pas pour le haut"; the shirt sticks out
        // at the collar, so only the rows under the belt count).  The trouser line itself does not move.  Children keep the cut.
        // The shirt is never the vanilla basic one: its hem has a notch at the crotch that made the blue ragged (captures of 060f,
        // Virginie 2026-10-30: the shirt was asked for "pour ne pas avoir la partie cassée en bas").  The three female Thin, Fat
        // and Hulk bodies take the basic shirt WDI itself ships (256 px, closed flat hem); the other adults take Vanilla Apparel
        // Expanded's blouse (Virginie: its Thin, Fat and Hulk are the names of the male versions).  A child, or a body whose
        // shirt is not installed, keeps its own cut.
        private const string VaePackageId = "VanillaExpanded.VAPPE";
        private const string BlousePath = "Things/Apparel/Blouse/Blouse_";

        internal static Texture2D MaxShirt(WdiVisualProfile profile, string facing, ModContentPack wdi)
        {
            if (profile.TextureKey == "Child") return null;
            Texture2D shirt = wdi.GetContentHolder<Texture2D>().Get(ShirtTexturePath + profile.TextureKey + "_" + facing);
            if (shirt != null || profile.TextureKey.EndsWith("_Female", StringComparison.Ordinal)) return shirt;
            ModContentPack vae = LoadedModManager.RunningMods.FirstOrDefault(mod =>
                string.Equals(mod.PackageIdPlayerFacing, VaePackageId, StringComparison.OrdinalIgnoreCase));
            return vae?.GetContentHolder<Texture2D>().Get(BlousePath + profile.BodyTypeName + "_" + facing);
        }

        private static byte[] WithShirtBelowBelt(byte[] cut, WdiVisualProfile profile, string facing, int width, int height, ModContentPack wdi)
        {
            Texture2D shirt = MaxShirt(profile, facing, wdi);
            if (shirt == null) return cut;
            byte[] shirtPixels = TrouserArt.Read(shirt, out int sw, out int sh);
            int[] belt = Enumerable.Repeat(-1, width).ToArray();
            for (int x = 0; x < width; x++)
                for (int y = 0; y < height; y++)
                    if (cut[(y * width + x) * TrouserDetail.Channels + 3] != 0) { belt[x] = y; break; }
            Fill(belt);
            // The shirt's alpha at the body's resolution, then fitted to the body (setting outlineShirtFit).
            bool[] shirt1 = new bool[width * height];
            for (int y = 0; y < height; y++)
            {
                int sy = Math.Min(sh - 1, (int)(y * (long)sh / height));
                for (int x = 0; x < width; x++)
                {
                    int sx = Math.Min(sw - 1, (int)(x * (long)sw / width));
                    shirt1[y * width + x] = shirtPixels[(sy * sw + sx) * TrouserDetail.Channels + 3] >= TopFit.MinAlpha;
                }
            }
            WdiAppPatterns.RowExtents(cut, width, height, out int[] rowLeft, out int[] rowRight);
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                    if (x < rowLeft[y] || x > rowRight[y]) shirt1[y * width + x] = false;
            int fit = TailorMadeWaistlinesMod.Settings?.outlineShirtFit ?? 0;
            if (fit == 1 || fit == 2) shirt1 = FitShirt(shirt1, cut, belt, width, height, fit == 2);
            byte[] merged = (byte[])cut.Clone();
            for (int x = 0; x < width; x++)
            {
                if (belt[x] < 0) continue;
                for (int y = belt[x]; y < height; y++)
                {
                    if (!shirt1[y * width + x]) continue;
                    int i = (y * width + x) * TrouserDetail.Channels;
                    merged[i] = merged[i + 1] = merged[i + 2] = merged[i + 3] = 255;
                }
            }
            return merged;
        }

        // The shirt is wider than the body at the belt on the heavy bodies, and the max then keeps a ledge there (captures 060f).
        // Two ways to fit it (Virginie 2026-10-30, to compare): one horizontal scale from the belt row (everything below keeps the
        // shirt's own shape, hem included), or a scale of each row on the body's width at that row (like TailorMade's bands).
        // Both stretch about the middle of the body; a row with no body (below its bottom) takes the last row's width.
        private static bool[] FitShirt(bool[] shirt, byte[] cut, int[] belt, int width, int height, bool perRow)
        {
            Func<int, int, int, bool> opaque = (x, y, pass) => pass == 0 ? cut[(y * width + x) * TrouserDetail.Channels + 3] != 0 : shirt[y * width + x];
            Func<int, int, int> left = (y, pass) => { for (int x = 0; x < width; x++) if (opaque(x, y, pass)) return x; return -1; };
            Func<int, int, int> right = (y, pass) => { for (int x = width - 1; x >= 0; x--) if (opaque(x, y, pass)) return x; return -1; };
            bool[] fitted = new bool[shirt.Length];
            int beltRow = belt[width / 2];
            if (beltRow < 0) return shirt;
            int refRow = Math.Min(height - 1, beltRow + 4);
            double once = 1.0;
            if (!perRow)
            {
                int bl0 = left(refRow, 0), br0 = right(refRow, 0), sl0 = left(refRow, 1), sr0 = right(refRow, 1);
                if (bl0 < 0 || sl0 < 0 || sr0 - sl0 <= br0 - bl0) return shirt;
                once = (br0 - bl0 + 1.0) / (sr0 - sl0 + 1.0);
            }
            int lastBl = -1, lastBr = -1;
            for (int y = beltRow; y < height; y++)
            {
                int bl = left(y, 0), br = right(y, 0), sl = left(y, 1), sr = right(y, 1);
                if (bl >= 0) { lastBl = bl; lastBr = br; } else { bl = lastBl; br = lastBr; }
                if (sl < 0 || bl < 0) continue;
                double bc = (bl + br) / 2.0, sc = (sl + sr) / 2.0;
                double scale = perRow ? (br - bl + 1.0) / (sr - sl + 1.0) : once;
                for (int x = 0; x < width; x++)
                {
                    int sx = (int)Math.Round(sc + (x - bc) / scale);
                    fitted[y * width + x] = sx >= 0 && sx < width && shirt[y * width + sx];
                }
            }
            for (int y = 0; y < beltRow; y++) Array.Copy(shirt, y * width, fitted, y * width, width);
            return fitted;
        }

        [HarmonyPatch(typeof(ApparelGraphicRecordGetter), nameof(ApparelGraphicRecordGetter.TryGetGraphicApparel))]
        internal static class NativeGraphicPatch
        {
            private static int traceCount;
            // This is the actual RimWorld 1.6 apparel resolution point.  A
            // generated Texture2D has no pre-load asset path, so we supply
            // complete materials here instead of asking GraphicDatabase to
            // discover it through ContentFinder.
            private static bool Prefix(Apparel apparel, BodyTypeDef bodyType, bool forStatue,
                ref ApparelGraphicRecord rec, ref bool __result)
            {
                if (forStatue || TailorMadeWaistlinesMod.Settings == null || !TailorMadeWaistlinesMod.Settings.enableExperimentalAppPatterns)
                    return true;
                Dictionary<string, Texture2D> source = SourceFor(apparel?.def?.defName);
                if (source == null || apparel.Wearer == null) return true;
                WdiVisualProfile profile = WdiVisualProfiles.Resolve(bodyType?.defName, apparel.Wearer.gender);
                if (profile == null || !source.ContainsKey(profile.TextureKey + "_south")) return true;
                if (traceCount++ < 12)
                    Log.Message("[Venus Touch Waistlines] direct apparel match " + apparel.def.defName + " " + profile.TextureKey + ".");
                Color color = source == OutlineTextures || (source == PantsTextures && outlinePants) ? Color.white : apparel.DrawColor;
                string cacheKey = apparel.def.defName + "|" + profile.TextureKey + "|" + color;
                if (!Graphics.TryGetValue(cacheKey, out Graphic graphic))
                {
                    graphic = BuildGraphic(source, profile.TextureKey, color, apparel.def.graphicData.drawSize);
                    Graphics[cacheKey] = graphic;
                }
                rec = new ApparelGraphicRecord(graphic, apparel);
                __result = true;
                return false;
            }

            private static Dictionary<string, Texture2D> SourceFor(string defName)
            {
                switch (defName)
                {
                    case "Apparel_Pants":
                    case "Apparel_KidPants": return PantsTextures;
                    case "Apparel_BasicShirt":
                    case "Apparel_KidShirt": return TopTextures;
                    case OutlineTopDef: return OutlineTextures;
                    default: return null;
                }
            }

            private static Graphic BuildGraphic(Dictionary<string, Texture2D> source, string key, Color color, Vector2 drawSize)
            {
                var graphic = new DirectGraphic();
                var mats = new Material[4];
                mats[0] = Material(source[key + "_north"], color);
                mats[1] = Material(source[key + "_east"], color);
                mats[2] = Material(source[key + "_south"], color);
                mats[3] = mats[1];
                AccessTools.Field(typeof(Graphic_Multi), "mats").SetValue(graphic, mats);
                AccessTools.Field(typeof(Graphic), "drawSize").SetValue(graphic, drawSize);
                return graphic;
            }

            // PawnRenderNode may ask an apparel graphic for a recoloured
            // version just before drawing it. Graphic_Multi normally rebuilds
            // that version through GraphicDatabase and its string path; these
            // images are generated at runtime and deliberately have none.
            // Their material already contains the apparel dye, so retaining
            // this direct graphic is the correct recoloured version.
            internal sealed class DirectGraphic : Graphic_Multi
            {
                public override Graphic GetColoredVersion(Shader newShader, Color newColor, Color newColorTwo) => this;
            }

            private static Material Material(Texture2D texture, Color color)
            {
                MaterialRequest request = default(MaterialRequest);
                request.mainTex = texture;
                request.shader = ShaderDatabase.Cutout;
                request.color = color;
                return MaterialPool.MatFrom(request);
            }
        }

        private static void Alias(ModContentHolder<Texture2D> mine, string requested, string source)
        {
            foreach (string facing in Facings)
            {
                Texture2D texture;
                if (mine.contentList.TryGetValue(Path + "_" + source + "_" + facing, out texture))
                    mine.contentList[Path + "_" + requested + "_" + facing] = texture;
            }
        }

        private static void AliasTop(ModContentHolder<Texture2D> mine, string requested, string source)
        {
            foreach (string facing in Facings)
            {
                Texture2D texture;
                if (mine.contentList.TryGetValue(TopPath + "_" + source + "_" + facing, out texture))
                    mine.contentList[TopPath + "_" + requested + "_" + facing] = texture;
            }
        }

        private static string UnderwearPath(WdiVisualProfile profile, string facing)
        {
            string kind = profile.TextureKey == "Child" ? "loincloth" :
                (profile.Id.StartsWith("Male", StringComparison.Ordinal) ? "boxers" : "panties");
            return "UWUnderwear/" + kind + "/" + kind + "_" + profile.TextureKey + "_" + facing;
        }

        private static byte[] BuildPants(WdiVisualProfile profile, string facing, Texture2D body, Texture2D underwear, out int width, out int height)
        {
            byte[] bodyPixels = TrouserArt.Read(body, out width, out height);
            if (!UnderwearRows(profile, facing, underwear, width, height, out int[] top, out int[] bottom)) return null;

            byte[] output = new byte[bodyPixels.Length];
            for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
            {
                if (top[x] < 0 || y < top[x] - 1) continue;
                int i = (y * width + x) * TrouserDetail.Channels;
                if (bodyPixels[i + 3] == 0) continue;
                output[i] = output[i + 1] = output[i + 2] = 255;
                output[i + 3] = 77; // Dye supplies blue; garment, not mask, owns transparency.
            }
            if (facing != "east") DrawTriangle(output, width, height, top, bottom, profile.TextureKey == "Child");
            return output;
        }

        // Per column, the first and last row of the underwear sprite, resampled to the body and filled across empty columns.
        private static bool UnderwearRows(WdiVisualProfile profile, string facing, Texture2D underwear, int width, int height,
            out int[] top, out int[] bottom)
        {
            byte[] underwearPixels = TrouserArt.Read(underwear, out int uw, out int uh);
            top = Enumerable.Repeat(-1, width).ToArray();
            bottom = Enumerable.Repeat(-1, width).ToArray();
            for (int x = 0; x < width; x++)
            {
                int ux = Math.Min(uw - 1, (int)(x * (long)uw / width));
                for (int y = 0; y < height; y++)
                {
                    int uy = Math.Min(uh - 1, (int)(y * (long)uh / height));
                    if (underwearPixels[(uy * uw + ux) * TrouserDetail.Channels + 3] == 0) continue;
                    if (top[x] < 0) top[x] = y;
                    bottom[x] = y;
                }
            }
            Fill(top); Fill(bottom);
            if (top.All(v => v < 0)) return false;
            if (profile.TextureKey == "Child") SmoothChild(top, facing);
            return true;
        }

        /// <summary>
        /// The trousers as a blue outline, interior empty (Virginie, 2026-10-26): the WDI body cut on the trouser line of
        /// WdiAppPatterns.WaistLines, plus the triangle between the legs, drawn as the shape the trousers will leave open to show
        /// its position and size.  Opaque pixels, baked blue, drawn with a white material colour.
        /// </summary>
        private static byte[] BuildPantsOutline(WdiVisualProfile profile, string facing, byte[] cut, byte[] body, int width, int height)
        {
            byte[] outline = WdiAppPatterns.Ring(cut, width, height, WdiAppPatterns.RingPx);
            if (facing != "east" && !DrawBlackTriangle(outline, body, profile, width, height, facing))
                DrawOpenTriangle(outline, body, profile, width, height, facing);
            for (int i = 0; i < outline.Length; i += TrouserDetail.Channels)
                if (outline[i + 3] != 0) { outline[i] = outline[i + 1] = 0; outline[i + 2] = 255; outline[i + 3] = 255; }
            return outline;
        }

        private static void Mark(byte[] image, int width, int height, int x, int y, byte[] body)
        {
            if (x < 0 || x >= width || y < 0 || y >= height) return;
            int i = (y * width + x) * TrouserDetail.Channels;
            if (body[i + 3] != 0) image[i + 3] = 255;
        }

        private static void MarkLine(byte[] image, byte[] body, int width, int height, double x0, double y0, double x1, double y1)
        {
            int steps = (int)Math.Max(Math.Abs(x1 - x0), Math.Abs(y1 - y0)) * 2 + 1;
            for (int s = 0; s <= steps; s++)
            {
                double f = s / (double)steps;
                int x = (int)Math.Round(x0 + (x1 - x0) * f), y = (int)Math.Round(y0 + (y1 - y0) * f);
                Mark(image, width, height, x, y, body);
                Mark(image, width, height, x + 1, y, body);
                Mark(image, width, height, x, y + 1, body);
            }
        }

        // The triangle between the legs (Virginie, 2026-10-27), read in the WDI body texture where its ink is black:
        //  - apex: the crotch, which is the top of the dark stem on the middle column above the body's bottom outline (women,
        //    children); the top of the dark cluster of the genitals for the men;
        //  - base: two points on the inner edge of the bottom outline, HalfBase columns either side of the middle (a measure per
        //    male profile, 6.5 % of the body width otherwise), joined by a curve that follows the rounded bottom of the body
        //    like the basic shirt's hem and ignores the small notch the body outline has between the legs.
        // Nothing is drawn when the texture shows no crotch there.
        private const int DarkLuma = 60, MinAlpha = 40;
        // Seen from behind the apex is the bottom of the buttocks, the small mark where the two curves meet the middle crease
        // (Virginie, 2026-10-29, red dots on the WDI north textures).  Rows above the inner edge of the bottom outline, at the middle
        // column, read off her dots (512 px textures, about 2 px of error).  Every body is listed (the second four adults and the child from her dots of the same day).
        private static readonly Dictionary<string, int> BackApexRise = new Dictionary<string, int>
        {
            { "Male", 10 }, { "Female", 32 }, { "Fat", 4 }, { "Hulk_Female", 26 },
            { "Thin", 25 }, { "Hulk", 9 }, { "Thin_Female", 37 }, { "Fat_Female", 16 },
            { "Child", -5 }   // her dot is the centre of the black star, 5 rows below the top of the dark stem the old rule took
        };
        // Seen from the front the apex is the crotch, where the thigh gap we removed would start (Virginie, 2026-10-31, red rings on
        // the Naked_<body>_south textures, ten rows read off them, about 1 row of error).  Rows ABOVE the body's lowest solid pixel
        // on the middle column (width / 2), the notch between the buttocks.  The old rules (top of the dark stem, top of the genital
        // cluster) put the apex too high.
        private static readonly Dictionary<string, int> FrontApexRise = new Dictionary<string, int>
        {
            { "Male", 31 }, { "Thin", 34 }, { "Fat", 40 }, { "Hulk", 52 },
            { "Female", 31 }, { "Thin_Female", 44 }, { "Fat_Female", 42 }, { "Hulk_Female", 54 },
            { "Child", 36 }
        };
        // The open triangle as Virginie redrew it, 2026-11-02 (her yellow lines on the nude zooms): it starts between the bulbs for
        // the men and at the lowest point of the vulva for the women and the child (from the front, her tables from the back), the
        // sides follow the black the body draws there (a narrow V between the arms for the men, the edges of the black stem for the
        // others), then open in a rounded flare to the two corners on the bottom edge of the body, and the base follows that edge.
        // False when the body shows no such crotch; the older triangle is then drawn.
        private static bool DrawBlackTriangle(byte[] outline, byte[] body, WdiVisualProfile profile, int width, int height, string facing)
        {
            int mid = width / 2, floor = height * 3 / 5;
            Func<int, int, bool> solid = (x, y) => x >= 0 && x < width && y >= 0 && y < height && body[(y * width + x) * TrouserDetail.Channels + 3] >= MinAlpha;
            Func<int, int, bool> dark = (x, y) =>
            {
                if (!solid(x, y)) return false;
                int i = (y * width + x) * TrouserDetail.Channels;
                return (body[i] + body[i + 1] + body[i + 2]) / 3 < DarkLuma;
            };
            Func<int, int> bottom = x =>
            {
                for (int y = height - 1; y >= 0; y--) if (solid(x, y)) return y;
                return -1;
            };
            Func<int, int, int[]> run = (x, y) =>
            {
                if (!dark(x, y)) return new[] { 0, 0 };
                int l = x, r = x;
                while (dark(l - 1, y) && x - l < 60) l--;
                while (dark(r + 1, y) && r - x < 60) r++;
                return new[] { l, r };
            };
            int bm = bottom(mid);
            if (bm < 0) return false;
            int rowY = bm - 20, left = 0, right = width - 1;
            while (left < width && !solid(left, rowY)) left++;
            while (right > 0 && !solid(right, rowY)) right--;
            int cx = (left + right) / 2;
            bool men = profile.TextureKey != "Child" && profile.Id.StartsWith("Male", StringComparison.Ordinal);

            int topCol = bm - 30;
            while (topCol > floor && dark(cx, topCol - 1)) topCol--;
            int apex;
            if (facing == "north")
            {
                if (!BackApexRise.TryGetValue(profile.TextureKey, out int rise)) return false;
                apex = Math.Max(floor, bm - 30 - rise);
            }
            else if (men) apex = topCol;
            else
            {
                int minWidth = int.MaxValue, wingRow = topCol, wingWidth = 0;
                for (int y = topCol; y <= topCol + 40; y++)
                {
                    int[] rn = run(cx, y);
                    if (rn[1] > 0) minWidth = Math.Min(minWidth, rn[1] - rn[0] + 1);
                    if (y <= topCol + 25 && rn[1] > 0 && rn[1] - rn[0] + 1 > wingWidth) { wingWidth = rn[1] - rn[0] + 1; wingRow = y; }
                }
                apex = topCol;
                for (int y = wingRow; y <= bm - 30; y++)
                {
                    int[] rn = run(cx, y);
                    if (rn[1] - rn[0] + 1 <= Math.Max(minWidth + 2, (int)(wingWidth * 0.6))) { apex = y; break; }
                }
            }
            if (apex < floor || apex >= bm - 6) return false;

            // The black's own edges, row by row, until the dark run flares into the bottom outline.
            var edgeL = new List<double[]>();
            var edgeR = new List<double[]>();
            int yF = apex;
            for (int y = apex; y <= bm - 6; y++)
            {
                int[] rn = run(cx, y);
                if (rn[1] == 0) rn = new[] { cx, cx };
                if (rn[1] - rn[0] + 1 > 34) break;
                edgeL.Add(new double[] { rn[0], y });
                edgeR.Add(new double[] { rn[1], y });
                yF = y;
            }
            if (edgeL.Count == 0) { edgeL.Add(new double[] { cx, apex }); edgeR.Add(new double[] { cx, apex }); }
            // The top tapers to a point at the apex (her yellow on the child: a drop, not a flat-topped stem).
            for (int i = 0; i < Math.Min(12, edgeL.Count); i++)
            {
                double k = (i + 1) / 13.0;
                edgeL[i][0] = cx + (edgeL[i][0] - cx) * k;
                edgeR[i][0] = cx + (edgeR[i][0] - cx) * k;
            }
            edgeL.Insert(0, new double[] { cx, apex });
            edgeR.Insert(0, new double[] { cx, apex });
            if (men && facing == "south")
            {
                // A narrow V between the arms of the fork, to the top of the flare.
                int eL = 12, eR = 12;
                for (int d = 1; d <= 40; d++) if (dark(cx - d, yF - 3)) { eL = d; break; }
                for (int d = 1; d <= 40; d++) if (dark(cx + d, yF - 3)) { eR = d; break; }
                eL = Math.Max(eL, 8); eR = Math.Max(eR, 8);
                edgeL = Curve(cx, apex, cx - 0.3 * eL, apex + 0.7 * (yF - apex), cx - eL, yF);
                edgeR = Curve(cx, apex, cx + 0.3 * eR, apex + 0.7 * (yF - apex), cx + eR, yF);
            }

            int half;
            if (men && facing == "south" && FrontBaseHalf.TryGetValue(profile.TextureKey, out int tabled)) half = tabled;
            // Virginie, 2026-11-02: the Hulk woman is very like the average one, her yellow sides run on to corners about 34 px
            // either side of the middle on both.
            else if (facing == "south" && (profile.TextureKey == "Female" || profile.TextureKey == "Hulk_Female")) half = 34;
            else
            {
                int bmax = 0;
                for (int x = cx - 70; x <= cx + 70; x++) bmax = Math.Max(bmax, bottom(x));
                half = 0;
                for (int d = 6; d <= 45 && half == 0; d++)
                    if (bottom(cx + d) >= bmax - 3 && bottom(cx - d) >= bmax - 3) half = d;
                if (half == 0) half = (int)Math.Round((right - left) * 0.065) + 8;
            }
            int cl = cx - half, cr = cx + half, yl = bottom(cl) - 2, yr = bottom(cr) - 2;
            if (yl < 0 || yr < 0) return false;
            Action<List<double[]>, int, int> side = (edge, corner, cornerY) =>
            {
                for (int i = 0; i + 1 < edge.Count; i++)
                    MarkLine(outline, body, width, height, edge[i][0], edge[i][1], edge[i + 1][0], edge[i + 1][1]);
                double[] end = edge[edge.Count - 1];
                List<double[]> flare = Curve(end[0], end[1], end[0] + 0.25 * (corner - end[0]), cornerY, corner, cornerY);
                for (int i = 0; i + 1 < flare.Count; i++)
                    MarkLine(outline, body, width, height, flare[i][0], flare[i][1], flare[i + 1][0], flare[i + 1][1]);
            };
            side(edgeL, cl, yl);
            side(edgeR, cr, yr);
            for (int x = cl; x <= cr; x++)
            {
                int yb = bottom(x) - 2;
                Mark(outline, width, height, x, yb, body);
                Mark(outline, width, height, x, yb + 1, body);
            }
            return true;
        }

        // A quadratic curve through three points, 16 steps.
        private static List<double[]> Curve(double x0, double y0, double x1, double y1, double x2, double y2)
        {
            var points = new List<double[]>();
            for (int i = 0; i <= 16; i++)
            {
                double t = i / 16.0, u = 1 - t;
                points.Add(new[] { u * u * x0 + 2 * u * t * x1 + t * t * x2, u * u * y0 + 2 * u * t * y1 + t * t * y2 });
            }
            return points;
        }

        // Half width of the open triangle's base at the bottom edge of the men from the front, from her blue drawing of 2026-11-02 on
        // the Naked_<body>_south zooms (about 2 screen px per texture px in those zooms).
        private static readonly Dictionary<string, int> FrontBaseHalf = new Dictionary<string, int>
        {
            { "Male", 10 }, { "Thin", 22 }, { "Fat", 29 }, { "Hulk", 16 }
        };
        private static void DrawOpenTriangle(byte[] outline, byte[] body, WdiVisualProfile profile, int width, int height, string facing)
        {
            int mid = width / 2, floor = height * 3 / 5;
            Func<int, int, bool> solid = (x, y) => x >= 0 && x < width && body[(y * width + x) * TrouserDetail.Channels + 3] >= MinAlpha;
            Func<int, int, bool> dark = (x, y) =>
            {
                if (!solid(x, y)) return false;
                int i = (y * width + x) * TrouserDetail.Channels;
                return (body[i] + body[i + 1] + body[i + 2]) / 3 < DarkLuma;
            };
            Func<int, int> bottom = x =>
            {
                for (int y = height - 1; y >= 0; y--) if (solid(x, y)) return y;
                return -1;
            };
            Func<int, int> inner = x =>
            {
                int y = bottom(x);
                while (y > floor && dark(x, y - 1)) y--;
                return y;
            };
            if (bottom(mid) < 0) return;

            bool male = profile.TextureKey != "Child" && profile.Id.StartsWith("Male", StringComparison.Ordinal);
            int rowY = bottom(mid) - 20, left = 0, right = width - 1;
            while (left < width && !solid(left, rowY)) left++;
            while (right > 0 && !solid(right, rowY)) right--;
            int cx = (left + right) / 2;   // the body's own middle at that row: 255 or 256 on a 512 px texture, 258 for the female back; width / 2 sat half a pixel to the right
            int half;
            switch (profile.TextureKey)
            {
                case "Thin" when male: half = 11; break;
                case "Fat" when male: half = 17; break;
                case "Hulk" when male: half = 17; break;
                default: half = male ? 15 : (int)Math.Round((right - left) * 0.065); break;
            }
            int thick = bottom(mid + 32) - inner(mid + 32);   // the bottom outline's thickness, away from the crotch
            int apex = -1;
            if (facing == "north" && BackApexRise.TryGetValue(profile.TextureKey, out int rise))
                apex = Math.Max(floor, inner(cx) - rise);
            else if (facing == "south" && FrontApexRise.TryGetValue(profile.TextureKey, out int up))
                apex = Math.Max(floor, bottom(mid) - up);
            else if (male)
            {
                int seedX = -1, seedY = -1;
                for (int y = bottom(mid) - thick - 1; y > bottom(mid) - thick - 50 && seedX < 0; y--)
                    for (int d = 0; d <= 12 && seedX < 0; d++)
                    {
                        if (dark(cx + d, y)) { seedX = cx + d; seedY = y; }
                        else if (dark(cx - d, y)) { seedX = cx - d; seedY = y; }
                    }
                if (seedX >= 0)
                {
                    var seen = new HashSet<int>();
                    var stack = new Stack<int[]>();
                    stack.Push(new[] { seedX, seedY });
                    int top = int.MaxValue;
                    while (stack.Count > 0)
                    {
                        int[] p = stack.Pop();
                        int x = p[0], y = p[1];
                        if (x < cx - 40 || x > cx + 40 || y < floor || y >= bottom(x) - thick || !dark(x, y) || !seen.Add(y * width + x)) continue;
                        top = Math.Min(top, y);
                        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) if (dx != 0 || dy != 0) stack.Push(new[] { x + dx, y + dy });
                    }
                    if (top != int.MaxValue) apex = top;
                }
            }
            else if (bottom(mid) - inner(cx) > thick + 4) apex = inner(cx);
            if (apex < 0) return;

            int xl = cx - half, xr = cx + half;
            // The men from the front (Virginie, 2026-11-02, her blue drawing on the four nude zooms: the triangle "fait bien plus que
            // suivre le noir"): from the apex a thin stem along the black the body draws there, then it opens in a triangle whose
            // sides run to the bottom outline and whose base follows the bottom edge of the body, notch included.  The half width
            // of the base is read off her drawing (512 px textures, about 3 px of error).
            if (male && facing == "south" && FrontBaseHalf.TryGetValue(profile.TextureKey, out int baseHalf)
                && TraceBlack(dark, bottom, cx, apex, floor, thick, width, out int[] lineL, out int[] lineR, out int yTop, out int yEnd))
            {
                MarkLine(outline, body, width, height, cx, apex, lineL[yTop], yTop);
                MarkLine(outline, body, width, height, cx, apex, lineR[yTop], yTop);
                for (int y = yTop; y < yEnd; y++)
                {
                    MarkLine(outline, body, width, height, lineL[y], y, lineL[y + 1], y + 1);
                    MarkLine(outline, body, width, height, lineR[y], y, lineR[y + 1], y + 1);
                }
                int cl = cx - baseHalf, cr = cx + baseHalf, yl = bottom(cl) - 2, yr = bottom(cr) - 2;
                if (yl < 0 || yr < 0) return;
                MarkLine(outline, body, width, height, lineL[yEnd], yEnd, cl, yl);
                MarkLine(outline, body, width, height, lineR[yEnd], yEnd, cr, yr);
                for (int x = cl; x <= cr; x++)
                {
                    int yBase = bottom(x) - 2;
                    Mark(outline, width, height, x, yBase, body);
                    Mark(outline, width, height, x, yBase + 1, body);
                }
                return;
            }
            MarkLine(outline, body, width, height, cx, apex, xl, inner(xl));
            MarkLine(outline, body, width, height, cx, apex, xr, inner(xr));
            // The rounded base: a parabola through the bottom outline 8 columns outside each corner and a point a little below the
            // higher of the two (the body's notch is not followed).
            int xa = xl - 8, xb = xr + 8, ya = bottom(xa), yb = bottom(xb);
            if (ya < 0 || yb < 0) return;
            double ym = Math.Max(ya, yb) + 3, lift = thick / 2.0;
            for (int x = xa; x <= xb; x++)
            {
                double t = (x - xa) / (double)(xb - xa);
                // quadratic Bezier-like: weights chosen so that the curve passes through ya, ym (at the middle) and yb
                double y = ya * (1 - t) * (1 - t) + (4 * ym - ya - yb) / 2.0 * 2 * t * (1 - t) + yb * t * t;
                Mark(outline, width, height, x, (int)Math.Round(y - lift), body);
                Mark(outline, width, height, x, (int)Math.Round(y - lift) + 1, body);
            }
        }

        // The black connected to the first dark pixel found within 14 columns of the middle in the 60 rows under the apex, kept
        // between 4 rows above the apex and the bottom outline (its thickness excluded) and 40 columns of the middle.  Returns, for
        // each of its rows from yTop to yEnd, its first and last column; false when there is no such black.
        private static bool TraceBlack(Func<int, int, bool> dark, Func<int, int> bottom, int cx, int apex, int floor, int thick, int width,
            out int[] lineL, out int[] lineR, out int yTop, out int yEnd)
        {
            lineL = lineR = null;
            yTop = yEnd = -1;
            int seedX = -1, seedY = -1;
            for (int y = apex - 4; y < apex + 60 && seedX < 0; y++)
                for (int d = 0; d <= 14 && seedX < 0; d++)
                {
                    if (y < floor || y >= bottom(cx) - thick) continue;
                    if (dark(cx + d, y)) { seedX = cx + d; seedY = y; }
                    else if (dark(cx - d, y)) { seedX = cx - d; seedY = y; }
                }
            if (seedX < 0) return false;
            var minX = new Dictionary<int, int>();
            var maxX = new Dictionary<int, int>();
            var seen = new HashSet<int>();
            var stack = new Stack<int[]>();
            stack.Push(new[] { seedX, seedY });
            while (stack.Count > 0)
            {
                int[] p = stack.Pop();
                int x = p[0], y = p[1];
                if (x < cx - 40 || x > cx + 40 || y < apex - 4 || y < floor || y >= bottom(x) - thick || !dark(x, y) || !seen.Add(y * width + x)) continue;
                minX[y] = minX.TryGetValue(y, out int lo) ? Math.Min(lo, x) : x;
                maxX[y] = maxX.TryGetValue(y, out int hi) ? Math.Max(hi, x) : x;
                for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) if (dx != 0 || dy != 0) stack.Push(new[] { x + dx, y + dy });
            }
            if (minX.Count == 0) return false;
            yTop = minX.Keys.Min();
            yEnd = minX.Keys.Max();
            int size = yEnd + 2;
            lineL = new int[size];
            lineR = new int[size];
            for (int y = yTop; y <= yEnd; y++)
            {
                if (!minX.ContainsKey(y)) { lineL[y] = lineL[y - 1]; lineR[y] = lineR[y - 1]; continue; }
                lineL[y] = minX[y];
                lineR[y] = maxX[y];
            }
            return true;
        }

        // The shirt ends two pixels below the underwear's upper edge.  That is
        // deliberate: it puts the shirt over the waistband without letting the
        // vanilla full-body shirt conceal the independently rendered trousers.
        private static byte[] BuildTop(Texture2D body, Texture2D underwear, int width, int height)
        {
            byte[] bodyPixels = TrouserArt.Read(body, out int bodyWidth, out int bodyHeight);
            byte[] underwearPixels = TrouserArt.Read(underwear, out int uw, out int uh);
            byte[] output = new byte[bodyPixels.Length];
            int[] top = Enumerable.Repeat(-1, width).ToArray();
            for (int x = 0; x < width; x++)
            {
                int ux = Math.Min(uw - 1, (int)(x * (long)uw / width));
                for (int y = 0; y < height; y++)
                {
                    int uy = Math.Min(uh - 1, (int)(y * (long)uh / height));
                    if (underwearPixels[(uy * uw + ux) * TrouserDetail.Channels + 3] > 0) { top[x] = y; break; }
                }
            }
            Fill(top);
            for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
            {
                if (top[x] < 0 || y > top[x] + 2) continue;
                int i = (y * width + x) * TrouserDetail.Channels;
                if (bodyPixels[i + 3] == 0) continue;
                output[i] = output[i + 1] = output[i + 2] = 255;
                output[i + 3] = 77;
            }
            return output;
        }

        private static void Fill(int[] rows)
        {
            int last = -1;
            for (int x = 0; x < rows.Length; x++) { if (rows[x] >= 0) last = rows[x]; else if (last >= 0) rows[x] = last; }
            last = -1;
            for (int x = rows.Length - 1; x >= 0; x--) { if (rows[x] >= 0) last = rows[x]; else if (last >= 0) rows[x] = last; }
        }

        private static void SmoothChild(int[] rows, string facing)
        {
            int[] values = rows.Where(v => v >= 0).OrderBy(v => v).ToArray();
            if (values.Length == 0) return;
            if (facing != "east") { int line = values[values.Length / 2] + 1; for (int x = 0; x < rows.Length; x++) if (rows[x] >= 0) rows[x] = line; return; }
            int left = Array.FindIndex(rows, v => v >= 0), right = Array.FindLastIndex(rows, v => v >= 0);
            if (left < 0 || right <= left) return;
            int from = rows[left] + 1, to = rows[right] + 1;
            for (int x = left; x <= right; x++) rows[x] = from + (to - from) * (x - left) / (right - left);
        }

        // The between-leg wedge: its apex on the underwear's lower edge at the middle column (the middle of the loincloth for a
        // child), its base on the lowest opaque row of the garment at that column.
        private static bool TriangleBounds(byte[] garment, int width, int height, int[] top, int[] bottom, bool child,
            out int mid, out int apex, out int lowest)
        {
            mid = width / 2;
            apex = child ? (top[mid] + bottom[mid]) / 2 : bottom[mid];
            lowest = -1;
            if (apex < 0) return false;
            for (int y = height - 1; y >= apex; y--) if (garment[(y * width + mid) * TrouserDetail.Channels + 3] > 0) { lowest = y; break; }
            return lowest > apex;
        }

        private static void DrawTriangle(byte[] output, int width, int height, int[] top, int[] bottom, bool child)
        {
            if (!TriangleBounds(output, width, height, top, bottom, child, out int mid, out int apex, out int lowest)) return;
            for (int y = apex; y <= lowest; y++)
            {
                int half = Math.Max(0, (y - apex) * 7 / Math.Max(1, lowest - apex));
                for (int x = mid - half; x <= mid + half; x++)
                {
                    if (x < 0 || x >= width) continue;
                    int i = (y * width + x) * TrouserDetail.Channels;
                    if (output[i + 3] == 0) continue;
                    output[i] = output[i + 1] = output[i + 2] = 0;
                    output[i + 3] = 255;
                }
            }
        }
    }
}
