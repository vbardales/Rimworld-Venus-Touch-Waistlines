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
                    byte[] rgba = BuildPantsOutline(profile, facing, cut, pixels, width, height);
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
        /// WdiAppPatterns.WaistLines, plus a line around the between-leg wedge (the triangle of DrawTriangle, which is a gap in the
        /// trousers) to show its position and size.  Opaque pixels, baked blue, drawn with a white material colour.
        /// </summary>
        private static byte[] BuildPantsOutline(WdiVisualProfile profile, string facing, byte[] cut, byte[] body, int width, int height)
        {
            byte[] outline = WdiAppPatterns.Ring(cut, width, height, WdiAppPatterns.RingPx);
            if (facing != "east" && WedgeEdges(body, width, height, out int tip, out int baseRow, out int[] left, out int[] right))
            {
                const int Stroke = 2;   // columns each side of the edge
                for (int y = tip; y <= baseRow; y++)
                {
                    // A step of the edge from one row to the next is drawn as a run, so the arc has no hole.
                    int next = Math.Min(y + 1, baseRow);
                    int l0 = Math.Min(left[y], left[next]), l1 = Math.Max(left[y], left[next]);
                    int r0 = Math.Min(right[y], right[next]), r1 = Math.Max(right[y], right[next]);
                    for (int x = l0 - Stroke; x <= l1 + Stroke; x++) Mark(outline, width, x, y, body);
                    for (int x = r0 - Stroke; x <= r1 + Stroke; x++) Mark(outline, width, x, y, body);
                }
            }
            for (int i = 0; i < outline.Length; i += TrouserDetail.Channels)
                if (outline[i + 3] != 0) { outline[i] = outline[i + 1] = 0; outline[i + 2] = 255; outline[i + 3] = 255; }
            return outline;
        }

        private static void Mark(byte[] image, int width, int x, int y, byte[] body)
        {
            if (x < 0 || x >= width) return;
            int i = (y * width + x) * TrouserDetail.Channels;
            if (body[i + 3] != 0) image[i + 3] = 255;
        }

        // The between-leg wedge as WDI draws it (Virginie, 2026-10-27): the black ink from the crotch down to where it meets the
        // round, black-edged lower part of the body.  Read in the body texture on the middle column: from the bottom up, past the
        // dark run wider than MaxWedge (the body's own outline), the first narrower dark run is the last row of the wedge; going on
        // up while the middle column stays dark gives the crotch.  No wedge is drawn when the body has none (M-Thin, M, which
        // have the genitals there instead).  Per row, the run's two ends are the arcs.  The pubic bar is wider
        // than the stem under it, so the edges only move inward going up: the wedge is a triangle with curved sides.
        private const int MaxWedge = 60, DarkLuma = 60, MinAlpha = 40;
        private static bool WedgeEdges(byte[] body, int width, int height, out int tip, out int baseRow, out int[] left, out int[] right)
        {
            tip = baseRow = -1;
            left = right = null;
            int mid = width / 2;
            Func<int, int, bool> dark = (x, y) =>
            {
                if (x < 0 || x >= width) return false;
                int i = (y * width + x) * TrouserDetail.Channels;
                return body[i + 3] >= MinAlpha && (body[i] + body[i + 1] + body[i + 2]) / 3 < DarkLuma;
            };
            Func<int, int[]> run = y =>
            {
                if (!dark(mid, y)) return null;
                int l = mid, r = mid;
                while (dark(l - 1, y)) l--;
                while (dark(r + 1, y)) r++;
                return r - l + 1 <= MaxWedge ? new[] { l, r } : null;
            };
            // Only the lower part of the body: above it the middle column crosses hair and the navel, not the wedge.
            int floor = height * 3 / 5;
            bool merged = false;
            for (int y = height - 1; y >= floor; y--)
            {
                if (!dark(mid, y)) continue;
                if (run(y) == null) merged = true;
                else if (merged) { baseRow = y; break; }
            }
            if (baseRow < 0) return false;
            tip = baseRow;
            while (tip > floor && dark(mid, tip - 1) && run(tip - 1) != null) tip--;
            if (baseRow - tip < 10) return false;
            left = new int[height];
            right = new int[height];
            for (int y = baseRow; y >= tip; y--)
            {
                int[] ends = run(y);
                left[y] = ends[0];
                right[y] = ends[1];
                if (y < baseRow) { left[y] = Math.Max(left[y], left[y + 1]); right[y] = Math.Min(right[y], right[y + 1]); }
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
