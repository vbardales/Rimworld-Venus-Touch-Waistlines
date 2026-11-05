using System;
using HarmonyLib;
using TailorMade;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Cuts an on-skin shirt where the underwear starts, after TailorMade has resized it to the body.
    ///
    /// Out of the chest band, TailorMade fits the shirt to the whole silhouette: shoulders and width are the body's. A vanilla
    /// shirt is drawn over the whole body though, so its hem has to be brought up to the trousers. Resizing the lower half does
    /// it badly (blurred hem); this erases the pixels below a line instead, as the masks of Apparel Paper Pattern and AbsCon do.
    ///
    /// The line is the top of the underwear WDI draws for the same body and sex (UWUnderwear, boxers), as a fraction of the
    /// picture counted from the top, measured with scripts/measure-underwear.js. Trousers drawn over the shirt hide the rest.
    /// </summary>
    public static class ShirtCut
    {
        // Top row of WDI's boxers over the height of its 512 px body, south view. Female variants of Thin, Hulk and Fat have
        // their own line: the body is a different drawing.
        internal static readonly System.Collections.Generic.Dictionary<string, float> Line = new System.Collections.Generic.Dictionary<string, float>
        {
            { "Male", 0.711f }, { "Female", 0.686f }, { "Thin", 0.699f }, { "Thin_Female", 0.674f },
            { "Fat", 0.643f }, { "Fat_Female", 0.643f }, { "Hulk", 0.799f }, { "Hulk_Female", 0.783f },
        };

        [ThreadStatic] private static string bodyKey;

        private static readonly System.Collections.Generic.Dictionary<string, float[]> profiles = new System.Collections.Generic.Dictionary<string, float[]>();

        private const int FeatherRows = 3;

        /// <summary>
        /// Erases, column by column, everything from that column's cut row down, and fades the last rows above it so that the
        /// edge is not a ruler line. <paramref name="cutRows"/> holds one row per column.
        /// </summary>
        public static byte[] CutBelowProfile(byte[] rgba, int width, int height, int[] cutRows)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (cutRows == null || cutRows.Length != width) throw new ArgumentException("one cut row per column.");
            if (width <= 0 || height <= 0 || rgba.Length != width * height * TrouserDetail.Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var px = (byte[])rgba.Clone();
            for (int x = 0; x < width; x++)
            {
                int cut = Math.Max(0, Math.Min(height, cutRows[x]));
                for (int y = cut; y < height; y++) px[(y * width + x) * TrouserDetail.Channels + 3] = 0;
                for (int k = 1; k <= FeatherRows && cut - k >= 0; k++)
                {
                    int i = ((cut - k) * width + x) * TrouserDetail.Channels + 3;
                    px[i] = (byte)(px[i] * (k / (float)(FeatherRows + 1)));
                }
            }
            return px;
        }

        /// <summary>
        /// The top edge of WDI's underwear for this body, facing and sex, as a fraction of the picture height for each of its
        /// columns; columns the underwear does not reach take the nearest column's value. Null when the underwear is not there.
        /// </summary>
        // Two lines per column (Virginie 2026-11-05: "si la rose est en bas et la jaune en haut, le tshirt descend jusqu'à la
        // rose et le pantalon est coupé selon la jaune"): of the boxers' and the panties' top edges, the higher one (yellow)
        // is where the trousers start, the lower one (pink) is where a tucked shirt ends. The shirt is drawn over the
        // trousers, so the band between the two lines is the shirt's, and no skin shows at the join.
        internal static float[] ProfileFor(string key, string facing) => Combine(key, facing, true);

        /// <summary>The lower of the boxers' and the panties' top edges (the pink line): where a tucked shirt ends.</summary>
        internal static float[] LowerFor(string key, string facing) => Combine(key, facing, false);

        private static float[] Combine(string key, string facing, bool upper)
        {
            string cacheKey = (upper ? "up_" : "low_") + key + "_" + facing;
            if (profiles.TryGetValue(cacheKey, out float[] cached)) return cached;
            float[] a = Top("boxers", key, facing), b = Top("panties", key, facing), result = a ?? b;
            if (a != null && b != null && a.Length == b.Length)
            {
                result = new float[a.Length];
                for (int x = 0; x < a.Length; x++) result[x] = upper ? Math.Min(a[x], b[x]) : Math.Max(a[x], b[x]);
            }
            profiles[cacheKey] = result;
            return result;
        }

        private static float[] Top(string kind, string key, string facing)
        {
            string cacheKey = kind + "_" + key + "_" + facing;
            if (profiles.TryGetValue(cacheKey, out float[] cached)) return cached;
            float[] result = null;
            try
            {
                Texture2D tex = ContentFinder<Texture2D>.Get("UWUnderwear/" + kind + "/" + kind + "_" + key + "_" + facing, false);
                if (tex != null)
                {
                    byte[] px = TrouserArt.Read(tex, out int w, out int h);
                    var top = new float[w];
                    for (int x = 0; x < w; x++)
                    {
                        top[x] = -1f;
                        for (int y = 0; y < h; y++)
                            if (px[(y * w + x) * TrouserDetail.Channels + 3] >= 128) { top[x] = y / (float)h; break; }
                    }
                    int first = Array.FindIndex(top, v => v >= 0f), last = Array.FindLastIndex(top, v => v >= 0f);
                    if (first >= 0)
                    {
                        for (int x = 0; x < first; x++) top[x] = top[first];
                        for (int x = last + 1; x < w; x++) top[x] = top[last];
                        for (int x = first; x <= last; x++) if (top[x] < 0f) top[x] = top[x - 1];
                        result = top;
                    }
                }
            }
            catch (Exception e)
            {
                Log.WarningOnce("[TailorMade Waistlines] could not read the underwear for " + cacheKey + ": " + e.Message, cacheKey.GetHashCode());
            }
            profiles[cacheKey] = result;
            return result;
        }

        /// <summary>
        /// One cut row per column of a picture <paramref name="width"/> wide and <paramref name="height"/> high: the top edge of
        /// this pawn's underwear, or the top edge of the underwear the trousers of its body start on when that is lower, plus a
        /// hand under the trousers. The trousers are cut on the same curve, so the shirt always runs under them.
        /// </summary>
        internal static int[] CutRows(string key, string facing, int width, int height)
        {
            // A child has no underwear and no side or back waistband of her own: every face takes the front's line.
            if (key == "Child") facing = "south";
            // The shirt runs under the trousers as they are drawn: the top edge of the finished trousers texture, column by column,
            // so both have the same shape.
            // ...and reaches at least the pink line, the lower underwear edge: the trousers start on the yellow one above it.
            float[] drawn = TrouserTop(key, facing);
            if (drawn != null)
            {
                float[] pink = LowerFor(key, facing);
                var follow = new int[width];
                for (int x = 0; x < width; x++)
                {
                    float t = drawn[Math.Min(drawn.Length - 1, (int)(x * (long)drawn.Length / width))] + UnderTrousers;
                    if (pink != null) t = Math.Max(t, pink[Math.Min(pink.Length - 1, (int)(x * (long)pink.Length / width))]);
                    // + FeatherRows: the faded rows above the cut fall under the trousers, not on the skin (2026-11-05, bac7)
                    follow[x] = (int)Math.Round(t * height, MidpointRounding.AwayFromZero) + FeatherRows;
                }
                return follow;
            }
            float[] own = LowerFor(key, facing);
            // The trousers of a female Thin, Fat or Hulk are cut on her own underwear too: the same curve.
            float[] pants = own ?? LowerFor(key.EndsWith("_Female") ? key.Substring(0, key.Length - 7) : key, facing);
            var rows = new int[width];
            if (own == null && pants == null)
            {
                int row = (int)Math.Round((LineFor(key) + UnderTrousers) * height, MidpointRounding.AwayFromZero) + FeatherRows;
                for (int x = 0; x < width; x++) rows[x] = row;
                return rows;
            }
            float drop = TailorMadeWaistlinesMod.Settings.trouserDrop - TailorMadeWaistlinesSettings.DefaultTrouserDrop;
            for (int x = 0; x < width; x++)
            {
                float a = own == null ? 0f : own[Math.Min(own.Length - 1, (int)(x * (long)own.Length / width))];
                float p = pants == null ? 0f : pants[Math.Min(pants.Length - 1, (int)(x * (long)pants.Length / width))] + drop;
                rows[x] = (int)Math.Round((Math.Max(a, p) + UnderTrousers) * height, MidpointRounding.AwayFromZero) + FeatherRows;
            }
            return rows;
        }

        private static readonly System.Collections.Generic.Dictionary<string, float[]> trouserTops = new System.Collections.Generic.Dictionary<string, float[]>();

        /// <summary>
        /// The top edge of the trousers this mod drew for a body and facing, as a fraction of their height for each column
        /// (empty columns take the nearest one's), or null when this mod drew none for it.
        /// </summary>
        internal static float[] TrouserTop(string key, string facing)
        {
            string cacheKey = key + "_" + facing;
            if (trouserTops.TryGetValue(cacheKey, out float[] cached)) return cached;
            float[] result = null;
            try
            {
                var mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
                string path = TrouserArt.PantsTexturePath(key, facing);
                Texture2D tex = mine.contentList.ContainsKey(path) ? mine.contentList[path] : null;
                if (tex != null)
                {
                    byte[] px = TrouserArt.Read(tex, out int w, out int h);
                    var top = new float[w];
                    for (int x = 0; x < w; x++)
                    {
                        top[x] = -1f;
                        for (int y = 0; y < h; y++)
                            if (px[(y * w + x) * TrouserDetail.Channels + 3] >= 128) { top[x] = y / (float)h; break; }
                    }
                    int first = Array.FindIndex(top, v => v >= 0f), last = Array.FindLastIndex(top, v => v >= 0f);
                    if (first >= 0)
                    {
                        for (int x = 0; x < first; x++) top[x] = top[first];
                        for (int x = last + 1; x < w; x++) top[x] = top[last];
                        for (int x = first; x <= last; x++) if (top[x] < 0f) top[x] = top[x - 1];
                        result = top;
                    }
                }
            }
            catch (Exception e)
            {
                Log.WarningOnce("[TailorMade Waistlines] could not read the trousers' top edge for " + cacheKey + ": " + e.Message, cacheKey.GetHashCode());
            }
            trouserTops[cacheKey] = result;
            return result;
        }

        private static float childLine = -1f;

        /// <summary>
        /// The line a body's shirt is cut on when it has no underwear curve. WDI draws no underwear for children, so the line
        /// is the one the child's trousers were given: the top of their finished texture, already lowered by the slider.
        /// </summary>
        internal static float LineFor(string key)
        {
            if (key != "Child") return Line[key];
            if (childLine >= 0f) return childLine;
            try
            {
                var mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
                Texture2D pants = TrouserArt.TextureAt(TrouserArt.PantsTexturePath("Child", "south"), mine);
                if (pants != null)
                {
                    byte[] px = TrouserArt.Read(pants, out int w, out int h);
                    int top = TrouserDetail.TopRow(px, w, h);
                    if (top >= 0) return childLine = top / (float)h;
                }
            }
            catch (Exception e)
            {
                Log.WarningOnce("[TailorMade Waistlines] could not find the child's trouser line: " + e.Message, 9482114);
            }
            return 0.7f;
        }

        private static float PantsLine(string key)
        {
            string body = key.EndsWith("_Female") ? key.Substring(0, key.Length - 7) : key;
            return TrouserArt.BelowNavel.TryGetValue(body, out float pantsTop)
                ? pantsTop + (TailorMadeWaistlinesMod.Settings.trouserDrop - TailorMadeWaistlinesSettings.DefaultTrouserDrop) + UnderTrousers
                : 0f;
        }

        // The shirt runs this far under the top of the trousers (3 px of the 512 px picture), so that no belly shows between them.
        private const float UnderTrousers = 3f / 512f;

        /// <summary>
        /// Where the cut falls: the top of the underwear, or just under the top of the trousers when that is lower, so a
        /// shirt always reaches the trousers (AB's Fat shell starts well below WDI's boxers).
        /// </summary>
        internal static float CutFraction(string key)
        {
            float line = LineFor(key);
            string body = key.EndsWith("_Female") ? key.Substring(0, key.Length - 7) : key;
            if (TrouserArt.BelowNavel.TryGetValue(body, out float pantsTop))
                line = Math.Max(line, pantsTop + (TailorMadeWaistlinesMod.Settings.trouserDrop - TailorMadeWaistlinesSettings.DefaultTrouserDrop) + UnderTrousers);
            return line;
        }

        /// <summary>Erases every row from <paramref name="cutRow"/> down. Returns the input itself when there is nothing to erase.</summary>
        public static byte[] CutBelow(byte[] rgba, int width, int height, int cutRow)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * TrouserDetail.Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            if (cutRow < 0 || cutRow >= height) return rgba;
            var px = (byte[])rgba.Clone();
            Array.Clear(px, cutRow * width * TrouserDetail.Channels, (height - cutRow) * width * TrouserDetail.Channels);
            return px;
        }

        /// <summary>Notes the body and the garment while TailorMade builds one graphic, so the bake that follows can cut it.</summary>
        [HarmonyPatch(typeof(Graphic_TailorMade), nameof(Graphic_TailorMade.Init))]
        public static class Init_Patch
        {
            public static void Prefix(GraphicRequest req)
            {
                bodyKey = null;
                if (!JacketArt.Active) return;
                string[] parts = req.path.Split(default(char));
                if (parts.Length < 3) return;
                ThingDef def = DefDatabase<ThingDef>.GetNamedSilentFail(parts[2]);
                if (JacketArt.Kind(def) != 2) return;
                ResolvedPattern pattern = PatternRegistry.Get(parts[1]);
                if (pattern?.BodyType == null) return;
                string key = pattern.BodyType.defName + (pattern.FemaleBody && pattern.BodyType.defName != "Female" ? "_Female" : "");
                if (Line.ContainsKey(key) || key == "Child") bodyKey = key;
            }

            public static void Finalizer() => bodyKey = null;
        }

        [HarmonyPatch(typeof(TexBake), nameof(TexBake.BakeFitted))]
        public static class BakeFitted_Patch
        {
            public static void Postfix(ref Texture2D __result, Rot4 rot)
            {
                if (bodyKey == null || __result == null) return;
                try
                {
                    byte[] px = TrouserArt.Read(__result, out int w, out int h);
                    // Every face follows the top edge of the trousers drawn for it, 3 px under it. West is the east picture
                    // turned round: its columns run the other way.
                    string facing = rot == Rot4.North ? "north" : rot == Rot4.South ? "south" : "east";
                    int[] rows = CutRows(bodyKey, facing, w, h);
                    if (rot == Rot4.West) Array.Reverse(rows);
                    byte[] cut = CutBelowProfile(px, w, h, rows);
                    if (ReferenceEquals(cut, px)) return;
                    __result = TrouserArt.Build(cut, w, h, "TMW_ShirtCut_" + bodyKey);
                }
                catch (Exception e)
                {
                    Log.WarningOnce("[TailorMade Waistlines] could not cut a shirt: " + e.Message, 9482113);
                }
            }
        }
    }
}
