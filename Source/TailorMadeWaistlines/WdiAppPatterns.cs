using System;
using System.Collections.Generic;
using System.Linq;
using ApparelPaperPattern;
using APPUtilities;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// The first APP-backed WDI slice. APP clips a garment through a texture
    /// mask, so storing a hand-traced copy of WDI's bodies would both go stale
    /// and redistribute another mod's art.  Instead, a mask is made in memory
    /// from the alpha channel of the WDI body the player has installed.
    ///
    /// APP identifies a pattern by BodyTypeDef; APP Utilities adds the gender
    /// predicate needed to keep Thin/Fat/Hulk female WDI profiles distinct.
    /// APP resolves the last matching pattern, so the category must be explicit:
    /// two OnSkin garments cannot safely share a full-height body mask. The
    /// initial pair targets only vanilla shirts and pants.  The shirt gets the
    /// whole WDI silhouette, so its own artwork decides its hem; only trousers
    /// are clipped at the measured waistline.  Cutting both independent vanilla
    /// graphics creates a visible body band. Middle and Shell require separate
    /// policies and must never fall through to these patterns.
    /// </summary>
    public static class WdiAppPatterns
    {
        private const string AppPackageId = "nalsnoir.ApparelPaperPattern";
        private const string UtilityPackageId = "WRK.APPBodyTypeOverrider";
        private const string WdiPackageId = "WDI.Realistic.Bodies";
        private const string Layer = "OnSkin";
        private static readonly WdiApparelCategory[] Categories =
        {
            WdiApparelCategory.Top,
            WdiApparelCategory.Pants,
            WdiApparelCategory.DiagnosticTop,
            WdiApparelCategory.DiagnosticPants
        };
        // Safety gate: the category masks have static proof only. Do not change
        // a player's visible clothing until a clean, exclusive in-game capture
        // proves that a shirt and trousers coexist for every target profile.
        private static bool ExperimentalPatternsEnabled => TailorMadeWaistlinesMod.Settings != null
            && TailorMadeWaistlinesMod.Settings.enableExperimentalAppPatterns;
        private static readonly string[] Facings = { "south", "east", "north" };

        public static bool Active { get; private set; }
        public static int RegisteredProfiles { get; private set; }

        public static void Apply()
        {
            Active = false;
            RegisteredProfiles = 0;
            if (!ExperimentalPatternsEnabled) return;
            if (!ModsConfig.IsActive(AppPackageId) || !ModsConfig.IsActive(UtilityPackageId) || !ModsConfig.IsActive(WdiPackageId))
                return;

            try
            {
                ModContentHolder<Texture2D> mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
                ModContentPack wdi = LoadedModManager.RunningMods.FirstOrDefault(mod =>
                    string.Equals(mod.PackageIdPlayerFacing, WdiPackageId, StringComparison.OrdinalIgnoreCase));
                if (wdi == null) return;
                foreach (WdiVisualProfile profile in WdiVisualProfiles.All)
                {
                    bool complete = true;
                    foreach (WdiApparelCategory category in Categories)
                    {
                        if (!RegisterMask(profile, category, mine, wdi) || !AddOnSkinPattern(profile, category))
                        {
                            complete = false;
                            break;
                        }
                    }
                    if (complete) RegisteredProfiles++;
                }

                Active = RegisteredProfiles == WdiVisualProfiles.All.Count;
                if (!Active)
                    Log.Warning("[Venus Touch Waistlines] APP WDI category patterns were not enabled: "
                        + RegisteredProfiles + "/" + WdiVisualProfiles.All.Count + " profile pairs could be generated.");
                else
                    Log.Message("[Venus Touch Waistlines] APP WDI shirt/pants patterns ready for all " + RegisteredProfiles + " visual profiles.");
            }
            catch (Exception e)
            {
                Active = false;
                Log.Warning("[Venus Touch Waistlines] APP WDI category setup failed: " + e.Message);
            }
        }

        private static bool RegisterMask(WdiVisualProfile profile, WdiApparelCategory category, ModContentHolder<Texture2D> mine, ModContentPack wdi)
        {
            string maskPath = MaskPath(profile, category);
            string burnPath = BurnPath(profile, category);
            bool found = false;
            foreach (string facing in Facings)
            {
                string sourcePath = "Things/Pawn/Humanlike/Bodies/Naked_" + profile.TextureKey + "_" + facing;
                Texture2D source = ContentFinder<Texture2D>.Get(sourcePath, false);
                if (source == null) return false;

                byte[] pixels = TrouserArt.Read(source, out int width, out int height);
                bool pants = category == WdiApparelCategory.Pants || category == WdiApparelCategory.DiagnosticPants;
                byte[] mask = pants
                    ? UnderwearCoverageMask(profile, facing, pixels, width, height, wdi)
                    : AlphaMask(pixels, width, height, new int[width], false);
                if (mask == null) return false;
                if (category == WdiApparelCategory.DiagnosticTop || category == WdiApparelCategory.DiagnosticPants)
                    mask = OpacityMask(mask, 77); // 30%: enough colour to locate cloth without hiding underwear.
                mine.contentList[maskPath + "_" + facing] = TrouserArt.Build(mask, width, height,
                    "Venus_APP_" + profile.Id + "_" + category + "_" + facing);
                if (category == WdiApparelCategory.Top)
                    mine.contentList[burnPath + "_" + facing] = TrouserArt.Build(ReliefMask(pixels, width, height), width, height,
                        "Venus_APP_Relief_" + profile.Id + "_" + facing);
                found = true;
            }
            return found;
        }

        // The supplied underwear gives us the waistband, not the trouser area.
        // Pants begin one pixel above that boundary and continue to the bottom
        // of the WDI silhouette.  Intersecting the two alpha images only drew
        // a second pair of briefs; it could never make the long blue control
        // garment the gallery is meant to inspect.
        private static byte[] UnderwearCoverageMask(WdiVisualProfile profile, string facing, byte[] bodyPixels, int width, int height, ModContentPack wdi)
        {
            string key = profile.TextureKey;
            string kind = key == "Child" ? "loincloth" :
                (profile.Id.StartsWith("Male", StringComparison.Ordinal) ? "boxers" : "panties");
            Texture2D underwear = wdi.GetContentHolder<Texture2D>().Get("UWUnderwear/" + kind + "/" + kind + "_" + key + "_" + facing);
            if (underwear == null) return null;
            byte[] pixels = TrouserArt.Read(underwear, out int sourceWidth, out int sourceHeight);
            if (sourceWidth <= 0 || sourceHeight <= 0) return null;
            int[] waist = new int[width];
            for (int x = 0; x < width; x++) waist[x] = -1;
            for (int x = 0; x < width; x++)
            {
                int sourceX = Math.Min(sourceWidth - 1, (int)(x * (long)sourceWidth / width));
                for (int y = 0; y < height; y++)
                {
                    int sourceY = Math.Min(sourceHeight - 1, (int)(y * (long)sourceHeight / height));
                    if (pixels[(sourceY * sourceWidth + sourceX) * TrouserDetail.Channels + 3] == 0) continue;
                    waist[x] = y;
                    break;
                }
            }
            FillMissingWaistColumns(waist);
            if (key == "Child") SmoothChildFundoshiLine(waist, facing);

            var mask = new byte[bodyPixels.Length];
            for (int y = 0; y < height; y++) for (int x = 0; x < width; x++)
            {
                // Adult waistband is one pixel above underwear.  The child
                // line has already been smoothed from the lower fundoshi edge.
                if (waist[x] < 0 || y < waist[x] - 1) continue;
                int i = (y * width + x) * TrouserDetail.Channels;
                byte alpha = bodyPixels[i + 3];
                if (alpha == 0) continue;
                mask[i] = mask[i + 1] = mask[i + 2] = 255;
                mask[i + 3] = alpha;
            }
            return mask.Any(value => value != 0) ? mask : null;
        }

        private static void FillMissingWaistColumns(int[] waist)
        {
            int last = -1;
            for (int x = 0; x < waist.Length; x++)
            {
                if (waist[x] >= 0) { last = waist[x]; continue; }
                if (last >= 0) waist[x] = last;
            }
            last = -1;
            for (int x = waist.Length - 1; x >= 0; x--)
            {
                if (waist[x] >= 0) { last = waist[x]; continue; }
                if (last >= 0) waist[x] = last;
            }
        }

        private static void SmoothChildFundoshiLine(int[] waist, string facing)
        {
            int[] values = waist.Where(value => value >= 0).OrderBy(value => value).ToArray();
            if (values.Length == 0) return;
            if (facing != "east")
            {
                // Face/back: a single horizontal pseudo-waist, taken from the
                // lower fundoshi line rather than its frayed upper pixels.
                int line = values[values.Length / 2] + 1;
                for (int x = 0; x < waist.Length; x++) if (waist[x] >= 0) waist[x] = line;
                return;
            }
            // Profile: retain the agreed inclined, back-perpendicular line.
            int first = Array.FindIndex(waist, value => value >= 0);
            int last = Array.FindLastIndex(waist, value => value >= 0);
            if (first < 0 || last <= first) return;
            int from = waist[first] + 1, to = waist[last] + 1;
            for (int x = first; x <= last; x++)
                waist[x] = from + (to - from) * (x - first) / (last - first);
        }

        private static byte[] AlphaMask(byte[] source, int width, int height, int[] cutRows, bool keepBelow)
        {
            if (source == null || width <= 0 || height <= 0 || source.Length != width * height * TrouserDetail.Channels)
                throw new ArgumentException("source must hold width * height * 4 bytes.");
            if (cutRows == null || cutRows.Length != width)
                throw new ArgumentException("cutRows must hold one row per column.");
            byte[] mask = new byte[source.Length];
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    // A top garment already has its intended lower hem in its
                    // own texture.  Let it run behind the pants; APP's draw
                    // order then hides the overlap.  Pants alone start at the
                    // profile waistline.
                    if (keepBelow && y < cutRows[x]) continue;
                    int i = (y * width + x) * TrouserDetail.Channels;
                    byte alpha = source[i + 3];
                    if (alpha == 0) continue;
                    mask[i] = 255;
                    mask[i + 1] = 255;
                    mask[i + 2] = 255;
                    mask[i + 3] = alpha;
                }
            }
            return mask;
        }

        // APP's burn pass reads a white alpha map.  The alpha here is the
        // darkness of WDI's installed body art: light skin stays transparent,
        // while its crease/contour pixels gently darken the garment rendered
        // above it.  This is deliberately separate from the garment cut mask.
        private static byte[] ReliefMask(byte[] source, int width, int height)
        {
            if (source == null || width <= 0 || height <= 0 || source.Length != width * height * TrouserDetail.Channels)
                throw new ArgumentException("source must hold width * height * 4 bytes.");
            byte[] relief = new byte[source.Length];
            for (int i = 0; i < source.Length; i += TrouserDetail.Channels)
            {
                byte alpha = source[i + 3];
                if (alpha == 0) continue;
                int luminance = (source[i] * 54 + source[i + 1] * 183 + source[i + 2] * 19) / 256;
                // A full black burn turns WDI's shading into a second opaque
                // silhouette.  Keep it deliberately subtle: body darks are
                // relief information, not a replacement garment colour.
                byte darkness = (byte)((255 - luminance) / 4);
                if (darkness == 0) continue;
                relief[i] = relief[i + 1] = relief[i + 2] = 255;
                relief[i + 3] = (byte)(darkness * alpha / 255);
            }
            return relief;
        }

        // Kept for the eventual post-render compositor. APP RenderVersion 2's
        // BurnPath alters the garment's tint as well as drawing black, so it
        // cannot safely be used as an outline channel for this alpha-mask path.
        private static byte[] EdgeMask(byte[] mask, int width, int height)
        {
            byte[] edge = new byte[mask.Length];
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    int i = (y * width + x) * TrouserDetail.Channels;
                    if (mask[i + 3] == 0) continue;
                    bool outside = x == 0 || x == width - 1 || y == 0 || y == height - 1;
                    if (!outside)
                    {
                        outside = mask[i - TrouserDetail.Channels + 3] == 0 ||
                            mask[i + TrouserDetail.Channels + 3] == 0 ||
                            mask[i - width * TrouserDetail.Channels + 3] == 0 ||
                            mask[i + width * TrouserDetail.Channels + 3] == 0;
                    }
                    if (!outside) continue;
                    edge[i] = edge[i + 1] = edge[i + 2] = edge[i + 3] = 255;
                }
            }
            return edge;
        }

        private static byte[] OpacityMask(byte[] mask, byte opacity)
        {
            if (mask == null) throw new ArgumentNullException(nameof(mask));
            byte[] translucent = (byte[])mask.Clone();
            for (int i = 3; i < translucent.Length; i += TrouserDetail.Channels)
                translucent[i] = (byte)(translucent[i] * opacity / 255);
            return translucent;
        }

        private static bool AddOnSkinPattern(WdiVisualProfile profile, WdiApparelCategory category)
        {
            string defName = "Venus_WDI_" + profile.Id + "_" + category;
            if (DefDatabase<ApparelPaperPatternDef>.GetNamedSilentFail(defName) != null) return true;

            BodyTypeDef body = DefDatabase<BodyTypeDef>.GetNamedSilentFail(profile.BodyTypeName);
            if (body == null) return false;

            var pattern = new ApparelPaperPatternDef
            {
                defName = defName,
                label = defName,
                RenderVersion = category == WdiApparelCategory.Top ? 2 : 1,
                RaceName = "Human",
                BodyType = body,
                ApparelLayer = Layer,
                MaskPath = MaskPath(profile, category),
                BurnPath = category == WdiApparelCategory.Top ? BurnPath(profile, category) : string.Empty,
                TargetApparelDefs = new List<string>(TargetDefs(category)),
                modExtensions = new List<DefModExtension>
                {
                    new DefModExtension_GenderRequirements
                    {
                        genderWhitelist = new List<Gender> { GenderFor(profile) }
                    }
                }
            };
            // Vanilla's trousers are a short lower-body sprite.  Scale them
            // before the WDI underwear coverage mask is applied, otherwise
            // their transparent upper half exposes the boxer/panty beneath.
            // The mask remains the final authority on the contour, so this
            // expansion cannot spill outside WDI's supplied underwear shape.
            if (category == WdiApparelCategory.Pants || category == WdiApparelCategory.DiagnosticPants)
            {
                pattern.ScaleNorth = 1.75f;
                pattern.ScaleEast = 1.75f;
                pattern.ScaleSouth = 1.75f;
                pattern.ScaleWest = 1.75f;
            }
            DefDatabase<ApparelPaperPatternDef>.Add(pattern);
            return true;
        }

        private static Gender GenderFor(WdiVisualProfile profile)
        {
            return profile.Id.StartsWith("Female", StringComparison.Ordinal) || profile.Id == "Kid_Girl"
                ? Gender.Female
                : Gender.Male;
        }

        private static IEnumerable<string> TargetDefs(WdiApparelCategory category)
        {
            switch (category)
            {
                case WdiApparelCategory.Top:
                    return new[] { "^Apparel_(BasicShirt|KidShirt)$" };
                case WdiApparelCategory.Pants:
                    return new[] { "^Apparel_(Pants|KidPants)$" };
                case WdiApparelCategory.DiagnosticTop:
                    return new[] { "^Apparel_(BasicShirt|KidShirt)$" };
                case WdiApparelCategory.DiagnosticPants:
                    return new[] { "^Apparel_(Pants|KidPants)$" };
                default:
                    return Enumerable.Empty<string>();
            }
        }

        private static string MaskPath(WdiVisualProfile profile, WdiApparelCategory category) =>
            "Venus/APP/WDI/" + profile.Id + "/" + category + "/mask";

        private static string BurnPath(WdiVisualProfile profile, WdiApparelCategory category) =>
            "Venus/APP/WDI/" + profile.Id + "/" + category + "/burn";
    }

    internal enum WdiApparelCategory
    {
        Top,
        Pants,
        DiagnosticTop,
        DiagnosticPants
    }
}
