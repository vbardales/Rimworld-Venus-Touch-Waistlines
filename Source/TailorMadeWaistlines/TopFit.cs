using System;
using System.Collections.Generic;
using HarmonyLib;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Fits the on-skin tops of any mod to the silhouette of a WDI body (Virginie, 2026-10-29: the clothes are clearly larger at the
    /// top than the silhouette).  A vanilla or modded shirt is drawn for another body, so its shoulders and collar stick out of
    /// WDI's.  The picture the game resolved is kept, colours and hem included, and every pixel outside the body's own alpha is
    /// erased, the way Apparel Paper Pattern masks a garment.  Behind the option fitTopsToSilhouette, off by default.
    /// TailorMade's own graphics are left alone: it already fits them to the body.
    /// </summary>
    internal static class TopFit
    {
        private const string WdiPackageId = "WDI.Realistic.Bodies";
        // The alpha a body pixel needs to count as part of the silhouette; the soft edge of its ink stays out.
        internal const int MinAlpha = 40;
        // The order of the four materials of a Graphic_Multi: north, east, south (west reuses east).
        private static readonly string[] Facings = { "north", "east", "south" };
        private static readonly System.Reflection.FieldInfo MatsField = AccessTools.Field(typeof(Graphic_Multi), "mats");
        private static readonly Dictionary<string, Graphic> Fitted = new Dictionary<string, Graphic>();
        private static readonly Dictionary<string, BodyPicture> Bodies = new Dictionary<string, BodyPicture>();

        private sealed class BodyPicture
        {
            public byte[] Rgba;
            public int Width, Height;
        }

        /// <summary>
        /// The garment with every pixel outside the body erased: a garment pixel is kept when the body's alpha at the same place
        /// (the two pictures cover the same square, whatever their resolution) is at least <see cref="MinAlpha"/>.  Both are
        /// RGBA, top row first.
        /// </summary>
        internal static byte[] ClipToBody(byte[] garment, int garmentWidth, int garmentHeight, byte[] body, int bodyWidth, int bodyHeight)
        {
            if (garment == null) throw new ArgumentNullException(nameof(garment));
            if (body == null) throw new ArgumentNullException(nameof(body));
            if (garmentWidth <= 0 || garmentHeight <= 0 || garment.Length != garmentWidth * garmentHeight * TrouserDetail.Channels)
                throw new ArgumentException("garment must hold width * height * 4 bytes.");
            if (bodyWidth <= 0 || bodyHeight <= 0 || body.Length != bodyWidth * bodyHeight * TrouserDetail.Channels)
                throw new ArgumentException("body must hold width * height * 4 bytes.");
            byte[] clipped = (byte[])garment.Clone();
            for (int y = 0; y < garmentHeight; y++)
            {
                int by = Math.Min(bodyHeight - 1, (int)(y * (long)bodyHeight / garmentHeight));
                for (int x = 0; x < garmentWidth; x++)
                {
                    int bx = Math.Min(bodyWidth - 1, (int)(x * (long)bodyWidth / garmentWidth));
                    if (body[(by * bodyWidth + bx) * TrouserDetail.Channels + 3] < MinAlpha)
                        clipped[(y * garmentWidth + x) * TrouserDetail.Channels + 3] = 0;
                }
            }
            return clipped;
        }

        /// <summary>A top: worn on the skin, covers the torso, does not reach the legs (dresses and jumpsuits are DressArt's).</summary>
        internal static bool IsTop(ThingDef def)
        {
            ApparelProperties apparel = def?.apparel;
            if (apparel?.layers == null || apparel.bodyPartGroups == null) return false;
            return apparel.layers.Contains(ApparelLayerDefOf.OnSkin)
                && apparel.bodyPartGroups.Contains(BodyPartGroupDefOf.Torso)
                && !apparel.bodyPartGroups.Contains(BodyPartGroupDefOf.Legs);
        }

        private static BodyPicture BodyFor(WdiVisualProfile profile, string facing)
        {
            string key = profile.TextureKey + "_" + facing;
            if (Bodies.TryGetValue(key, out BodyPicture cached)) return cached;
            BodyPicture picture = null;
            Texture2D body = ContentFinder<Texture2D>.Get("Things/Pawn/Humanlike/Bodies/Naked_" + key, false);
            if (body != null)
            {
                picture = new BodyPicture();
                picture.Rgba = TrouserArt.Read(body, out picture.Width, out picture.Height);
            }
            Bodies[key] = picture;
            return picture;
        }

        private static Graphic Fit(Graphic source, Material[] mats, WdiVisualProfile profile, string name)
        {
            var fitted = new Material[4];
            for (int i = 0; i < Facings.Length; i++)
            {
                Texture2D texture = mats[i]?.mainTexture as Texture2D;
                BodyPicture body = BodyFor(profile, Facings[i]);
                if (texture == null || body == null) return null;
                byte[] pixels = TrouserArt.Read(texture, out int width, out int height);
                byte[] clipped = ClipToBody(pixels, width, height, body.Rgba, body.Width, body.Height);
                var copy = new Material(mats[i]);
                copy.mainTexture = TrouserArt.Build(clipped, width, height, "TMW_TopFit_" + name + "_" + Facings[i]);
                fitted[i] = copy;
            }
            fitted[3] = fitted[1];
            var graphic = new NativeWdiPants.NativeGraphicPatch.DirectGraphic();
            // Same fields as the graphic the game built (path, colours, draw size, mask path ...), then the clipped materials.
            for (Type type = typeof(Graphic_Multi); type != null && type != typeof(object); type = type.BaseType)
                foreach (System.Reflection.FieldInfo field in type.GetFields(
                    System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.Public | System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.DeclaredOnly))
                    field.SetValue(graphic, field.GetValue(source));
            MatsField.SetValue(graphic, fitted);
            return graphic;
        }

        [HarmonyPatch(typeof(ApparelGraphicRecordGetter), nameof(ApparelGraphicRecordGetter.TryGetGraphicApparel))]
        internal static class Patch
        {
            private static void Postfix(Apparel apparel, BodyTypeDef bodyType, bool forStatue, ref ApparelGraphicRecord rec, ref bool __result)
            {
                if (!__result || forStatue || apparel?.Wearer == null) return;
                if (TailorMadeWaistlinesMod.Settings == null || !TailorMadeWaistlinesMod.Settings.fitTopsToSilhouette) return;
                if (!ModsConfig.IsActive(WdiPackageId) || !IsTop(apparel.def)) return;
                Graphic source = rec.graphic;
                // Ours are drawn from the body already; TailorMade's graphics are fitted by TailorMade.
                if (!(source is Graphic_Multi) || source is NativeWdiPants.NativeGraphicPatch.DirectGraphic
                    || source.GetType().Name == "Graphic_TailorMade") return;
                WdiVisualProfile profile = WdiVisualProfiles.Resolve(bodyType?.defName, apparel.Wearer.gender);
                if (profile == null) return;
                try
                {
                    var mats = MatsField.GetValue(source) as Material[];
                    if (mats == null || mats.Length < 3 || mats[2] == null) return;
                    string key = apparel.def.defName + "|" + profile.TextureKey + "|" + mats[2].mainTexture?.GetInstanceID() + "|" + source.Color;
                    if (!Fitted.TryGetValue(key, out Graphic fitted))
                    {
                        fitted = Fit(source, mats, profile, apparel.def.defName + "_" + profile.TextureKey);
                        Fitted[key] = fitted;
                    }
                    if (fitted != null) rec = new ApparelGraphicRecord(fitted, apparel);
                }
                catch (Exception e)
                {
                    Log.WarningOnce("[Venus Touch Waistlines] could not fit " + apparel.def.defName + " to the silhouette: " + e.Message,
                        apparel.def.defName.GetHashCode() ^ 0x4b17);
                }
            }
        }
    }
}
