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
    /// initial pair targets only vanilla shirts and pants.  Both are cut on
    /// WDI's own underwear lines, trousers from the higher one, the shirt down
    /// to the lower one, so the two always overlap (see WaistLines).  Middle
    /// and Shell require separate policies and must never fall through to
    /// these patterns.
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
            WdiApparelCategory.Pants
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
                BodyColumns(pixels, width, height, out int bodyMin, out int bodyMax);
                if (!WaistLines(profile, facing, width, height, wdi, bodyMin, bodyMax, out int[] trouserTop, out int[] shirtHem)) return false;
                byte[] mask = category == WdiApparelCategory.Pants
                    ? AlphaMask(pixels, width, height, trouserTop, true)
                    : AlphaMask(pixels, width, height, shirtHem, false);
                int filled = OpaquePixels(mask);
                mask = Ring(mask, width, height, RingPx);
                Log.Message("[Venus Touch Waistlines] APP mask " + profile.Id + " " + category + " " + facing + " " + width + "x" + height
                    + ": opaque pixels " + filled + " before Ring, " + OpaquePixels(mask) + " after.");
                if (!mask.Any(value => value != 0)) return false;
                mine.contentList[maskPath + "_" + facing] = TrouserArt.Build(mask, width, height,
                    "Venus_APP_" + profile.Id + "_" + category + "_" + facing);
                if (category == WdiApparelCategory.Top)
                    mine.contentList[burnPath + "_" + facing] = TrouserArt.Build(ReliefMask(pixels, width, height), width, height,
                        "Venus_APP_Relief_" + profile.Id + "_" + facing);
                found = true;
            }
            return found;
        }

        // The cut rule (Virginie, 2026-10-15): WDI draws two adult underwear
        // lines, the top of its boxers and the top of its panties, and neither
        // is always the higher one.  Trousers start at the higher of the two,
        // the shirt stops at the lower, so the shirt always overlaps the
        // trousers and no band of skin shows between them.  Children have only
        // the fundoshi: trousers start at its smoothed line and the shirt keeps
        // its own drawn hem (shirtHem null).
        private static bool WaistLines(WdiVisualProfile profile, string facing, int width, int height, ModContentPack wdi,
            int bodyMin, int bodyMax, out int[] trouserTop, out int[] shirtHem)
        {
            trouserTop = null;
            shirtHem = null;
            string key = profile.TextureKey;
            if (key == "Child")
            {
                int[] fundoshi = UnderwearTopLine(wdi, "loincloth", key, facing, width, height, bodyMin, bodyMax);
                if (fundoshi == null) return false;
                // The two child lines are the fundoshi's edge (Virginie, 2026-10-18): the shirt ends on it, the trousers start
                // one row above it.  Front and back keep the flat smoothing; the profile follows the edge, extrapolated at the
                // back like the adults', instead of a straight slope between its two ends.
                if (facing != "east") SmoothChildFundoshiLine(fundoshi, facing); else SmoothRipple(fundoshi);
                trouserTop = fundoshi.Select(y => y < 0 ? y : y - 1).ToArray();
                shirtHem = (int[])fundoshi.Clone();
                return true;
            }
            int[] boxers = UnderwearTopLine(wdi, "boxers", key, facing, width, height, bodyMin, bodyMax);
            int[] panties = UnderwearTopLine(wdi, "panties", key, facing, width, height, bodyMin, bodyMax);
            if (boxers == null && panties == null) return false;
            // Each line follows its own sprite (Virginie, 2026-10-18): the slip gives the top of the trousers, the boxers the hem
            // of the shirt.  Either sprite stands in for a body that lacks the other.
            CombineUnderwearLines(boxers ?? panties, panties ?? boxers, out trouserTop, out shirtHem);
            return true;
        }

        // Per column, the waistband sits one pixel above the higher underwear
        // line; the shirt hem is the lower line.  -1 marks a column with no
        // underwear on either side.
        private static void CombineUnderwearLines(int[] boxers, int[] panties, out int[] trouserTop, out int[] shirtHem)
        {
            trouserTop = new int[boxers.Length];
            shirtHem = new int[boxers.Length];
            for (int x = 0; x < boxers.Length; x++)
            {
                int a = boxers[x], b = panties[x];
                if (a < 0 && b < 0) { trouserTop[x] = shirtHem[x] = -1; continue; }
                if (a < 0) a = b;
                if (b < 0) b = a;
                trouserTop[x] = b - 1;
                shirtHem[x] = a;
            }
            // Where the boxers' edge is higher than the slip's, bare skin is left between the two lines.  Both lines move apart by
            // half of the largest such gap of the body and facing (the hem down, the trousers up), so they meet there and
            // overlap elsewhere (Virginie, 2026-10-18).
            int gap = 0;
            for (int x = 0; x < boxers.Length; x++)
                if (shirtHem[x] >= 0) gap = Math.Max(gap, trouserTop[x] - shirtHem[x] - 1);
            int shift = (gap + 1) / 2;
            if (shift > 0)
                for (int x = 0; x < boxers.Length; x++)
                    if (shirtHem[x] >= 0) { shirtHem[x] += shift; trouserTop[x] -= shift; }
        }

        // First opaque row of a WDI underwear texture, per column, resampled to
        // the body's size and filled across the columns the sprite leaves empty.
        private static int[] UnderwearTopLine(ModContentPack wdi, string kind, string key, string facing, int width, int height, int bodyMin, int bodyMax)
        {
            Texture2D underwear = wdi.GetContentHolder<Texture2D>().Get("UWUnderwear/" + kind + "/" + kind + "_" + key + "_" + facing);
            if (underwear == null) return null;
            byte[] pixels = TrouserArt.Read(underwear, out int sourceWidth, out int sourceHeight);
            if (sourceWidth <= 0 || sourceHeight <= 0) return null;
            int[] line = new int[width];
            for (int x = 0; x < width; x++)
            {
                line[x] = -1;
                int sourceX = Math.Min(sourceWidth - 1, (int)(x * (long)sourceWidth / width));
                for (int y = 0; y < height; y++)
                {
                    int sourceY = Math.Min(sourceHeight - 1, (int)(y * (long)sourceHeight / height));
                    if (pixels[(sourceY * sourceWidth + sourceX) * TrouserDetail.Channels + 3] == 0) continue;
                    line[x] = y;
                    break;
                }
            }
            ExtrapolateToBody(line, bodyMin, bodyMax);
            FillMissingWaistColumns(line);
            return line;
        }

        private static void BodyColumns(byte[] pixels, int width, int height, out int min, out int max)
        {
            min = width; max = -1;
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                    if (pixels[(y * width + x) * TrouserDetail.Channels + 3] != 0) { if (x < min) min = x; if (x > max) max = x; }
        }

        // The rule (Virginie, 2026-10-18): follow the edge of the underwear as drawn and, at each side, where the sprite's
        // rounded corner begins, extrapolate the line out to the body's last column.  The corner is the stretch of outer
        // columns where the line moves against its dominant direction (the top of the buttock on a profile, the bottom of the
        // hook on the front and back) or steeply (more than CornerStep rows a column); from the first column past it, the slope
        // over SlopeWindow columns is carried outward, replacing the corner.  scripts/game-cut-preview.js draws the same rule.
        private const int CornerStep = 2, SlopeWindow = 10, MaxCorner = 90;   // a corner never takes more than a third of the sprite
        private static void ExtrapolateToBody(int[] line, int bodyMin, int bodyMax)
        {
            int first = Array.FindIndex(line, value => value >= 0);
            int last = Array.FindLastIndex(line, value => value >= 0);
            if (first < 0 || last - first < 60) return;
            int corner = Math.Min(MaxCorner, (last - first) / 3 - SlopeWindow);

            int lead = Math.Sign(line[first + corner + SlopeWindow] - line[first + corner]);
            int a = first;
            while (a < first + corner && ((lead != 0 && (line[a + 1] - line[a]) * lead < 0) || Math.Abs(line[a + 1] - line[a]) > CornerStep)) a++;
            for (int x = a - 1; x >= Math.Min(bodyMin, first) && x >= 0; x--)
                line[x] = Extend(line[a], line[a + SlopeWindow], line[a + 2 * SlopeWindow], a - x);

            int trail = Math.Sign(line[last - corner - SlopeWindow] - line[last - corner]);
            int b = last;
            while (b > last - corner && ((trail != 0 && (line[b - 1] - line[b]) * trail < 0) || Math.Abs(line[b - 1] - line[b]) > CornerStep)) b--;
            for (int x = b + 1; x <= Math.Max(bodyMax, last) && x < line.Length; x++)
                line[x] = Extend(line[b], line[b - SlopeWindow], line[b - 2 * SlopeWindow], x - b);
        }

        // A parabola through the interior points y0 (the first smooth column), y1 and y2 (SlopeWindow and 2 SlopeWindow columns
        // further in), followed outward for SmoothColumns, then straight on with the slope it reached: the line leaves the
        // corner with the curve it had inside, not at an angle.  s = columns outward from y0.
        private const int SmoothColumns = 16;
        private static int Extend(int y0, int y1, int y2, int s)
        {
            double d1 = y1 - y0, d2 = y2 - y0;
            double c = (d2 - 2 * d1) / (SlopeWindow * SlopeWindow);
            double b = d1 / SlopeWindow - 0.5 * c * SlopeWindow;
            int sc = Math.Min(s, SmoothColumns);
            double y = y0 - b * sc + 0.5 * c * sc * sc;
            if (s > SmoothColumns) y += (-b + c * SmoothColumns) * (s - SmoothColumns);
            return (int)Math.Round(y, MidpointRounding.AwayFromZero);
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

        // The child profile follows the fundoshi edge, which ripples by 1 to 3 rows: a moving average over 2 * RippleRadius + 1
        // columns takes it out and keeps the slope and the curve of the back (Virginie, 2026-10-18).
        private const int RippleRadius = 8;
        private static void SmoothRipple(int[] line)
        {
            int[] source = (int[])line.Clone();
            for (int x = 0; x < line.Length; x++)
            {
                if (source[x] < 0) continue;
                int sum = 0, count = 0;
                for (int k = Math.Max(0, x - RippleRadius); k <= Math.Min(line.Length - 1, x + RippleRadius); k++)
                    if (source[k] >= 0) { sum += source[k]; count++; }
                line[x] = (int)Math.Round(sum / (double)count, MidpointRounding.AwayFromZero);
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
            if (cutRows != null && cutRows.Length != width)
                throw new ArgumentException("cutRows must hold one row per column.");
            byte[] mask = new byte[source.Length];
            for (int y = 0; y < height; y++)
            {
                for (int x = 0; x < width; x++)
                {
                    // keepBelow: trousers, from the cut row down.  Otherwise a
                    // shirt, down to and including its hem row.  No rows, or a
                    // column at -1, keeps the whole silhouette (the child's
                    // shirt, which keeps its own drawn hem).
                    int cut = cutRows == null ? -1 : cutRows[x];
                    if (cut >= 0 && (keepBelow ? y < cut : y > cut)) continue;
                    if (cut < 0 && keepBelow) continue;
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

        // The garment drawn as an outline, interior left empty, to show the limits of a vanilla garment (Virginie, 2026-10-19).
        // A mask pixel stays when a pixel within radius of it (a disc) is outside the mask: transparent body, the picture's
        // edge, or a row cut away by the waist rule, so the cut line is part of the outline.  The stroke lies inside the
        // silhouette.  Same rule as scripts/game-cut-preview.js --ring.
        private const int RingPx = 5;
        private static int OpaquePixels(byte[] mask)
        {
            int count = 0;
            for (int i = 3; i < mask.Length; i += TrouserDetail.Channels)
                if (mask[i] != 0) count++;
            return count;
        }
        private static byte[] Ring(byte[] mask, int width, int height, int radius)
        {
            if (mask == null || width <= 0 || height <= 0 || mask.Length != width * height * TrouserDetail.Channels)
                throw new ArgumentException("mask must hold width * height * 4 bytes.");
            byte[] ring = new byte[mask.Length];
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int i = (y * width + x) * TrouserDetail.Channels;
                    if (mask[i + 3] == 0) continue;
                    bool edge = false;
                    for (int dy = -radius; dy <= radius && !edge; dy++)
                        for (int dx = -radius; dx <= radius; dx++)
                        {
                            if (dx * dx + dy * dy > radius * radius) continue;
                            int nx = x + dx, ny = y + dy;
                            if (nx < 0 || ny < 0 || nx >= width || ny >= height
                                || mask[(ny * width + nx) * TrouserDetail.Channels + 3] == 0) { edge = true; break; }
                        }
                    if (!edge) continue;
                    ring[i] = mask[i]; ring[i + 1] = mask[i + 1]; ring[i + 2] = mask[i + 2]; ring[i + 3] = mask[i + 3];
                }
            return ring;
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
            if (category == WdiApparelCategory.Pants)
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
        Pants
    }
}
