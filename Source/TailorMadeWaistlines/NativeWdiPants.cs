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
        /// The shirt drawn by this mod alone, no APP: the WDI body cut on its waist line and reduced to an outline, interior empty
        /// (Virginie, 2026-10-23).  Opaque pixels, so the Cutout shader keeps every stroke.  Only the two vanilla shirts are
        /// taken over; trousers are left to whatever else supplies them.
        /// </summary>
        public static void ApplyOutlineShirt()
        {
            if (TailorMadeWaistlinesMod.Settings == null || !TailorMadeWaistlinesMod.Settings.enableExperimentalAppPatterns)
                return;
            if (!ModsConfig.IsActive(WdiPackageId)) return;
            if (ModsConfig.IsActive("nalsnoir.ApparelPaperPattern")) return;   // APP draws the shirts then

            ThingDef shirt = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_BasicShirt");
            ThingDef kidShirt = DefDatabase<ThingDef>.GetNamedSilentFail("Apparel_KidShirt");
            if (shirt?.apparel == null || kidShirt?.apparel == null) return;
            ModContentPack wdi = LoadedModManager.RunningMods.FirstOrDefault(mod =>
                string.Equals(mod.PackageIdPlayerFacing, WdiPackageId, StringComparison.OrdinalIgnoreCase));
            if (wdi == null) return;

            ModContentHolder<Texture2D> mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
            TopTextures.Clear();
            Graphics.Clear();
            foreach (WdiVisualProfile profile in WdiVisualProfiles.All)
                foreach (string facing in Facings)
                {
                    Texture2D body = ContentFinder<Texture2D>.Get("Things/Pawn/Humanlike/Bodies/Naked_" + profile.TextureKey + "_" + facing, false);
                    if (body == null) continue;
                    byte[] pixels = TrouserArt.Read(body, out int width, out int height);
                    byte[] mask = WdiAppPatterns.OutlineMask(profile, WdiApparelCategory.Top, facing, pixels, width, height, wdi);
                    if (mask == null) continue;
                    Texture2D texture = TrouserArt.Build(mask, width, height, "Venus_OutlineShirt_" + profile.TextureKey + "_" + facing);
                    mine.contentList[TopPath + "_" + profile.TextureKey + "_" + facing] = texture;
                    TopTextures[profile.TextureKey + "_" + facing] = texture;
                }
            AliasTop(mine, "Thin_Female", "Thin_Female");
            AliasTop(mine, "Hulk_Female", "Hulk_Female");
            AliasTop(mine, "Fat_Female", "Fat_Female");
            AliasTop(mine, "Child_Female", "Child");
            shirt.apparel.wornGraphicPath = TopPath;
            kidShirt.apparel.wornGraphicPath = TopPath;
            Log.Message("[Venus Touch Waistlines] outline shirt ready: " + TopTextures.Count + " textures.");
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
                string cacheKey = apparel.def.defName + "|" + profile.TextureKey + "|" + apparel.DrawColor;
                if (!Graphics.TryGetValue(cacheKey, out Graphic graphic))
                {
                    graphic = BuildGraphic(source, profile.TextureKey, apparel.DrawColor, apparel.def.graphicData.drawSize);
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
            private sealed class DirectGraphic : Graphic_Multi
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
            byte[] underwearPixels = TrouserArt.Read(underwear, out int uw, out int uh);
            int[] top = Enumerable.Repeat(-1, width).ToArray();
            int[] bottom = Enumerable.Repeat(-1, width).ToArray();
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
            if (top.All(v => v < 0)) return null;
            if (profile.TextureKey == "Child") SmoothChild(top, facing);

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

        private static void DrawTriangle(byte[] output, int width, int height, int[] top, int[] bottom, bool child)
        {
            int mid = width / 2;
            int apex = child ? (top[mid] + bottom[mid]) / 2 : bottom[mid];
            if (apex < 0) return;
            int lowest = -1;
            for (int y = height - 1; y >= apex; y--) if (output[(y * width + mid) * TrouserDetail.Channels + 3] > 0) { lowest = y; break; }
            if (lowest <= apex) return;
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
