using System;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Shorts drawn as two legs side by side, with a dark line down the whole middle and a gap in the hem between the legs:
    /// Swimwear's swimming trunks (kaitorisenkou.Swimwear). On a body drawn without legs they read as a garment cut in two
    /// (Virginie 2026-11-06, Soren's swim photo). The front and back art is mended with <see cref="TrouserDetail.MendSplitLegs"/>:
    /// the line is kept only below the crotch, as a seam, and the gap in the hem is closed. The side view has no middle line
    /// and is left alone.
    ///
    /// Registered in this mod's own content, as the trousers and the jackets are: removing the mod puts the original art back.
    /// </summary>
    public static class SplitLegArt
    {
        /// <summary>The garments mended, by the mod that draws them.</summary>
        private static readonly (string PackageId, string DefName)[] Garments =
        {
            ("kaitorisenkou.Swimwear", "Swimwear_SwimTrunks"),
        };

        private static readonly string[] Facings = { "south", "north" };

        public static int Mended { get; private set; }

        public static void Apply()
        {
            Mended = 0;
            var mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
            foreach (var (packageId, defName) in Garments)
            {
                if (TrouserArt.FindPackPublic(packageId) == null) continue;
                string worn = DefDatabase<ThingDef>.GetNamedSilentFail(defName)?.apparel?.wornGraphicPath;
                if (string.IsNullOrEmpty(worn)) continue;
                foreach (BodyTypeDef body in DefDatabase<BodyTypeDef>.AllDefsListForReading)
                    foreach (string facing in Facings)
                        Mend(worn + "_" + body.defName + "_" + facing, mine);
            }
            if (Mended > 0) Log.Message("[TailorMade Waistlines] split-leg shorts: " + Mended + " textures mended.");
        }

        private static void Mend(string path, ModContentHolder<Texture2D> mine)
        {
            if (mine.contentList.ContainsKey(path)) return;
            Texture2D tex = TrouserArt.TextureAt(path, mine);
            if (tex == null) return;
            try
            {
                byte[] px = TrouserArt.Read(tex, out int w, out int h);
                byte[] mended = TrouserDetail.MendSplitLegs(px, w, h);
                if (ReferenceEquals(mended, px)) return;
                mine.contentList[path] = TrouserArt.Build(mended, w, h, "TMW_SplitLeg_" + path.Replace('/', '_'));
                Mended++;
            }
            catch (Exception e)
            {
                Log.Warning("[TailorMade Waistlines] could not mend " + path + ": " + e.Message);
            }
        }
    }
}
