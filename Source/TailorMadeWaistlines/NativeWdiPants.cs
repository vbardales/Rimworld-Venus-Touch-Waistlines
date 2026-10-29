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
        // The rim of the vanilla basic shirt as a green outline, a reference to read the red hem and the blue line against
        // (Virginie, 2026-10-29).  Test def of the Pickle mod, never shipped.
        private const string RimDef = "Venus_TestShirtRim";
        private const string ShirtTexturePath = "Things/Pawn/Humanlike/Apparel/ShirtBasic/ShirtBasic_";
        private static readonly Dictionary<string, Texture2D> RimTextures = new Dictionary<string, Texture2D>();
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
            RimTextures.Clear();
            Graphics.Clear();
            ThingDef rimShirt = DefDatabase<ThingDef>.GetNamedSilentFail(RimDef);
            foreach (WdiVisualProfile profile in WdiVisualProfiles.All)
                foreach (string facing in Facings)
                {
                    if (rimShirt?.apparel != null && profile.TextureKey != "Child") BuildShirtRim(mine, profile, facing);
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
            if (rimShirt?.apparel != null) rimShirt.apparel.wornGraphicPath = TopPath;
            pants.apparel.wornGraphicPath = Path;
            kidPants.apparel.wornGraphicPath = Path;
            Log.Message("[Venus Touch Waistlines] outline top ready: " + OutlineTextures.Count + " textures, trousers " + PantsTextures.Count
                + ", shirt rim " + RimTextures.Count + ".");
        }

        // The green rim: the alpha of the basic shirt texture the game resolves for this body (WDI's own where it ships one, the
        // vanilla one otherwise), reduced to a 5 px outline at the body's 512 px scale.  Children are left out: their shirt is
        // another def.
        private static void BuildShirtRim(ModContentHolder<Texture2D> mine, WdiVisualProfile profile, string facing)
        {
            Texture2D shirt = ContentFinder<Texture2D>.Get(ShirtTexturePath + profile.TextureKey + "_" + facing, false)
                ?? ContentFinder<Texture2D>.Get(ShirtTexturePath + profile.BodyTypeName + "_" + facing, false);
            if (shirt == null) return;
            byte[] pixels = TrouserArt.Read(shirt, out int width, out int height);
            byte[] mask = new byte[pixels.Length];
            for (int i = 0; i < pixels.Length; i += TrouserDetail.Channels)
                if (pixels[i + 3] != 0) { mask[i] = mask[i + 1] = mask[i + 2] = 255; mask[i + 3] = 255; }
            byte[] ring = WdiAppPatterns.Ring(mask, width, height, Math.Max(1, (int)Math.Round(WdiAppPatterns.RingPx * width / 512.0)));
            for (int i = 0; i < ring.Length; i += TrouserDetail.Channels)
                if (ring[i + 3] != 0) { ring[i] = 0; ring[i + 1] = 200; ring[i + 2] = 0; ring[i + 3] = 255; }
            Texture2D texture = TrouserArt.Build(ring, width, height, "Venus_ShirtRim_" + profile.TextureKey + "_" + facing);
            mine.contentList[TopPath + "_" + profile.TextureKey + "_" + facing + "_rim"] = texture;
            RimTextures[profile.TextureKey + "_" + facing] = texture;
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
                Color color = source == OutlineTextures || source == RimTextures || (source == PantsTextures && outlinePants) ? Color.white : apparel.DrawColor;
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
                    case RimDef: return RimTextures;
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
        /// WdiAppPatterns.WaistLines, plus the triangle between the legs, drawn as the shape the trousers will leave open to show
        /// its position and size.  Opaque pixels, baked blue, drawn with a white material colour.
        /// </summary>
        private static byte[] BuildPantsOutline(WdiVisualProfile profile, string facing, byte[] cut, byte[] body, int width, int height)
        {
            byte[] outline = WdiAppPatterns.Ring(cut, width, height, WdiAppPatterns.RingPx);
            if (facing != "east") DrawOpenTriangle(outline, body, profile, width, height);
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
        private static void DrawOpenTriangle(byte[] outline, byte[] body, WdiVisualProfile profile, int width, int height)
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
            if (male)
            {
                int seedX = -1, seedY = -1;
                for (int y = bottom(mid) - thick - 1; y > bottom(mid) - thick - 50 && seedX < 0; y--)
                    for (int d = 0; d <= 12 && seedX < 0; d++)
                    {
                        if (dark(mid + d, y)) { seedX = mid + d; seedY = y; }
                        else if (dark(mid - d, y)) { seedX = mid - d; seedY = y; }
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
                        if (x < mid - 40 || x > mid + 40 || y < floor || y >= bottom(x) - thick || !dark(x, y) || !seen.Add(y * width + x)) continue;
                        top = Math.Min(top, y);
                        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) if (dx != 0 || dy != 0) stack.Push(new[] { x + dx, y + dy });
                    }
                    if (top != int.MaxValue) apex = top;
                }
            }
            else if (bottom(mid) - inner(mid) > thick + 4) apex = inner(mid);
            if (apex < 0) return;

            int xl = mid - half, xr = mid + half;
            MarkLine(outline, body, width, height, mid, apex, xl, inner(xl));
            MarkLine(outline, body, width, height, mid, apex, xr, inner(xr));
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
