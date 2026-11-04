using HarmonyLib;
using RimWorld;
using TailorMade;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Lets a full-body shirt be treated as a chest piece, so the chest band
    /// applies to it.
    ///
    /// TailorMade will only band a torso garment once <c>ConfirmChestArt</c>
    /// has measured the art and found that it starts at least 40% of the way
    /// up the texture. Its author says plainly what that test is for, in the
    /// tooltip of the setting it guards:
    ///
    ///   "Only kicks in when the worn texture is actually torso-only; long
    ///    coats and capes that drape down the body are left full-body."
    ///
    /// Which is right, and is the reason this option cannot simply lift the
    /// test. A vanilla shirt is drawn over the whole body, so it fails the
    /// measurement and stays full length, hiding the trousers whatever the
    /// trousers do — but so is a duster, and a duster is *supposed* to reach
    /// the ankles.
    ///
    /// The layer separates them, and vanilla is consistent about it: shirts
    /// and tribalwear are OnSkin, while dusters, parkas, jackets and robes are
    /// Shell. So the test is lifted for on-skin garments only. A coat still
    /// drapes, and astryl's guard still does the job he wrote it for.
    /// </summary>
    public static class ChestArt
    {
        private static bool LiftsTest(ThingDef def) =>
            TailorMadeWaistlinesMod.Settings.Tucked(def)
            && def?.apparel != null
            && def.apparel.LastLayer == ApparelLayerDefOf.OnSkin;

        [HarmonyPatch(typeof(ApparelClassifier), nameof(ApparelClassifier.ConfirmChestArt))]
        public static class ConfirmChestArt_Patch
        {
            public static void Postfix(ThingDef def, ref bool __result)
            {
                if (__result) return;
                if (LiftsTest(def)) __result = true;
            }
        }

        /// <summary>
        /// <c>ConfirmChestArt</c> stores its answer, and TailorMade asks <c>ChestArtCached</c> first: once a garment has
        /// been measured, the stored "no" is read back and <c>ConfirmChestArt</c> is never called again. The patch above
        /// therefore lifts the test for the first pawn only; this one lifts it for every later one.
        /// </summary>
        [HarmonyPatch(typeof(ApparelClassifier), nameof(ApparelClassifier.ChestArtCached))]
        public static class ChestArtCached_Patch
        {
            public static void Postfix(ThingDef def, ref bool confirmed, ref bool __result)
            {
                if (!__result || confirmed) return;
                if (!LiftsTest(def)) return;
                confirmed = true;
            }
        }

        /// <summary>
        /// Keeps a jacket the length its art has. TailorMade bands any torso-only garment into the chest band, so a
        /// jacket whose art starts high enough is cut off at the waist; the same garment on a body drawn with trousers
        /// reaches the hips. Taking the Shell layer out of the chest class leaves it full band, as drawn.
        /// </summary>
        [HarmonyPatch(typeof(ApparelClassifier), nameof(ApparelClassifier.Info))]
        public static class Info_Patch
        {
            /// <summary>
            /// Jackets and shirts are redrawn by <see cref="JacketArt"/> to the trousers, so TailorMade must not band them as
            /// well: its band squeezes the whole garment, shoulders included, instead of moving only the lower half.
            /// </summary>
            public static void Postfix(ThingDef def, ref ApparelClassInfo __result)
            {
                if (__result.cls != ApparelClass.Chest || !JacketArt.Active) return;
                if (JacketArt.Kind(def) == 0) return;
                __result.cls = ApparelClass.None;
            }
        }
    }
}
