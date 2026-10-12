using System;
using System.Collections.Generic;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Lets a jacket reach down to the hem of the trousers. A vanilla jacket is drawn for a body with legs and ends at the
    /// waist; on WDI's bodies the trousers go on below it, so the jacket stops where the trousers begin. The jacket's art
    /// is stretched downwards, below the navel, until its hem lands on the lowest row of the trousers' shell for the same
    /// body and facing. Above the navel nothing moves, so the collar, the shoulders and the chest stay as drawn.
    ///
    /// Registered in this mod's own content, as the trousers are: the game takes the last loaded mod's texture for a path,
    /// so removing the mod puts the original jacket back.
    /// </summary>
    public static class JacketArt
    {
        private static readonly string[] FacingNames = { "south", "east", "north" };

        public static int Stretched { get; private set; }

        /// <summary>True once the art has been redrawn, so TailorMade must leave these garments unbanded.</summary>
        public static bool Active { get; private set; }

        public static void Apply()
        {
            Stretched = 0;
            Active = false;
            var settings = TailorMadeWaistlinesMod.Settings;
            if (settings == null || !(settings.keepJacketsLong || settings.shortenShirts)) return;
            // The trousers' shells are what the hem is measured on: without AB there are none.
            if (TrouserArt.FindPackPublic("AB.VPLRF") == null) return;
            Active = true;

            var mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();
            var done = new HashSet<string>();
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
            {
                // Shirts (kind 2) are cut by ShirtCut after TailorMade has resized them; only jackets are redrawn here.
                if (Kind(def) != 1) continue;
                int kind = 1;
                string worn = def.apparel.wornGraphicPath;
                if (string.IsNullOrEmpty(worn) || !done.Add(worn)) continue;

                foreach (BodyTypeDef body in DefDatabase<BodyTypeDef>.AllDefsListForReading)
                {
                    if (!TrouserArt.BelowNavel.TryGetValue(body.defName, out float navel)) continue;
                    for (int f = 0; f < FacingNames.Length; f++)
                        Register(worn + "_" + body.defName + "_" + FacingNames[f], body.defName, FacingNames[f], navel, mine, kind == 2);
                }
            }

            if (settings.shortenShirts) NativeShirts(mine);

            Log.Message("[TailorMade Waistlines] jackets and shirts: " + Stretched + " textures redrawn to the trousers, "
                + NativeCut + " shirt textures cut on the underwear without TailorMade's resizing.");
        }

        public static int NativeCut { get; private set; }

        /// <summary>
        /// A body retexture such as WDI's ships a shirt drawn for each body (<c>ShirtBasic_Fat_Female_south</c>). TailorMade
        /// resizes it again to the body, which is wrong on the widest and the broadest ones. Here the shirt art is cut on the
        /// underwear's top edge as it is, and TailorMade is told to leave those garments on those bodies alone.
        /// </summary>
        private static void NativeShirts(ModContentHolder<Texture2D> mine)
        {
            NativeCut = 0;
            // One BodyTypeDef can have two WDI targets (Thin/Fat/Hulk men and women).
            // The profile table is the sole authority for the corresponding texture keys.
            foreach (string bodyName in new[] { "Male", "Female", "Thin", "Hulk", "Fat", "Child" })
            {
                BodyTypeDef body = DefDatabase<BodyTypeDef>.GetNamedSilentFail(bodyName);
                if (body == null) continue;
                var targets = new List<string>();
                foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
                {
                    if (Kind(def) != 2) continue;
                    string worn = def.apparel.wornGraphicPath;
                    if (string.IsNullOrEmpty(worn)) continue;
                    int cut = 0;
                    foreach (WdiVisualProfile profile in WdiVisualProfiles.ForBodyType(bodyName))
                        for (int f = 0; f < FacingNames.Length; f++)
                            if (CutNative(worn + "_" + profile.TextureKey + "_" + FacingNames[f], profile.TextureKey, FacingNames[f], mine)) cut++;
                    // Only a garment the body retexture draws for this body is left alone; any other is still resized.
                    if (cut > 0 || mine.contentList.ContainsKey(worn + "_" + bodyName + "_south"))
                        targets.Add("^" + System.Text.RegularExpressions.Regex.Escape(def.defName) + "$");
                }
                if (targets.Count == 0) continue;
                string name = "TMW_NativeShirt_" + bodyName;
                if (TailorMadeLink.Loaded) TailorMadeLink.LeaveAlone(name, body, targets);
            }
        }

        private static bool CutNative(string path, string key, string facing, ModContentHolder<Texture2D> mine)
        {
            if (mine.contentList.ContainsKey(path)) return false;
            Texture2D tex = TrouserArt.TextureAt(path, mine);
            if (tex == null) return false;
            try
            {
                byte[] px = TrouserArt.Read(tex, out int w, out int h);
                byte[] cut = ShirtCut.CutBelowProfile(px, w, h, ShirtCut.CutRows(key, facing, w, h));
                if (ReferenceEquals(cut, px)) return false;
                mine.contentList[path] = TrouserArt.Build(cut, w, h, "TMW_NativeShirt_" + path.Replace('/', '_'));
                NativeCut++;
                return true;
            }
            catch (Exception e)
            {
                Log.Warning("[TailorMade Waistlines] could not cut " + path + ": " + e.Message);
                return false;
            }
        }

        /// <summary>Zero for anything else; 1 for a coat or a jacket (shell layer, torso and not the legs); 2 for a shirt (on-skin, same).</summary>
        public static int Kind(ThingDef def)
        {
            ApparelProperties a = def?.apparel;
            if (a == null) return 0;
            var settings = TailorMadeWaistlinesMod.Settings;
            int kind = a.LastLayer == ApparelLayerDefOf.Shell && settings.keepJacketsLong ? 1
                     : a.LastLayer == ApparelLayerDefOf.OnSkin && settings.shortenShirts ? 2 : 0;
            if (kind == 0) return 0;
            bool torso = false;
            foreach (BodyPartGroupDef g in a.bodyPartGroups ?? new List<BodyPartGroupDef>())
            {
                if (g.defName == "Legs" || g.defName == "Feet") return 0;
                if (g.defName == "Torso") torso = true;
            }
            return torso ? kind : 0;
        }

        private static void Register(string path, string body, string facing, float navel, ModContentHolder<Texture2D> mine, bool shirt)
        {
            if (mine.contentList.ContainsKey(path)) return;
            Texture2D jacket = TrouserArt.TextureAt(path, mine);
            Texture2D pants = shirt ? null : TrouserArt.TextureAt(TrouserArt.PantsTexturePath(body, facing), mine);
            if (jacket == null || (!shirt && pants == null)) return;
            try
            {
                byte[] px = TrouserArt.Read(jacket, out int w, out int h);
                int hem, pivot;
                if (shirt)
                {
                    // A shirt keeps its top (collar, shoulders, chest) and only its lower half is brought up, until its hem
                    // runs just under the top of the trousers.
                    int top = TrouserDetail.TopRow(px, w, h), bottom = TrouserDetail.BottomRow(px, w, h);
                    if (top < 0) return;
                    pivot = (top + bottom) / 2;
                    hem = (int)Math.Round((navel + 0.03f) * h, MidpointRounding.AwayFromZero);
                }
                else
                {
                    byte[] pantsPx = TrouserArt.Read(pants, out int pw, out int ph);
                    hem = TrouserDetail.BottomRow(pantsPx, pw, ph);
                    if (hem < 0 || h != ph) return;
                    pivot = (int)Math.Round(navel * h, MidpointRounding.AwayFromZero);
                }
                byte[] stretched = TrouserDetail.StretchBottom(px, w, h, pivot, hem);
                if (ReferenceEquals(stretched, px)) return;
                mine.contentList[path] = TrouserArt.Build(stretched, w, h, "TMW_Jacket_" + path.Replace('/', '_'));
                Stretched++;
            }
            catch (Exception e)
            {
                Log.Warning("[TailorMade Waistlines] could not lengthen " + path + ": " + e.Message);
            }
        }
    }
}
