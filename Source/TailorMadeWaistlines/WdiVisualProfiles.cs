using System;
using System.Collections.Generic;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// WDI's human apparel is not keyed by <see cref="BodyTypeDef"/> alone.
    /// Thin, Hulk and Fat have one texture for a man and another for a woman;
    /// children are two gameplay profiles even though WDI 1.6 currently draws
    /// both from its shared <c>Child</c> texture.  Keeping that distinction in
    /// one table prevents a later refitter from silently treating Fat and
    /// Fat_Female as the same target.
    /// </summary>
    public sealed class WdiVisualProfile
    {
        internal WdiVisualProfile(string id, string bodyTypeName, string textureKey)
        {
            Id = id;
            BodyTypeName = bodyTypeName;
            TextureKey = textureKey;
        }

        /// <summary>The stable target name used by Venus and its tests.</summary>
        public string Id { get; }

        /// <summary>The vanilla BodyTypeDef used by RimWorld's renderer.</summary>
        public string BodyTypeName { get; }

        /// <summary>The suffix WDI 1.6 uses in an apparel texture path.</summary>
        public string TextureKey { get; }
    }

    public static class WdiVisualProfiles
    {
        public static readonly WdiVisualProfile Male = new WdiVisualProfile("Male", "Male", "Male");
        public static readonly WdiVisualProfile Female = new WdiVisualProfile("Female", "Female", "Female");
        public static readonly WdiVisualProfile MaleThin = new WdiVisualProfile("Male_Thin", "Thin", "Thin");
        public static readonly WdiVisualProfile MaleHulk = new WdiVisualProfile("Male_Hulk", "Hulk", "Hulk");
        public static readonly WdiVisualProfile MaleFat = new WdiVisualProfile("Male_Fat", "Fat", "Fat");
        public static readonly WdiVisualProfile FemaleThin = new WdiVisualProfile("Female_Thin", "Thin", "Thin_Female");
        public static readonly WdiVisualProfile FemaleHulk = new WdiVisualProfile("Female_Hulk", "Hulk", "Hulk_Female");
        public static readonly WdiVisualProfile FemaleFat = new WdiVisualProfile("Female_Fat", "Fat", "Fat_Female");
        public static readonly WdiVisualProfile KidGirl = new WdiVisualProfile("Kid_Girl", "Child", "Child");
        public static readonly WdiVisualProfile KidBoy = new WdiVisualProfile("Kid_Boy", "Child", "Child");

        /// <summary>All ten WDI human silhouette targets, in the public naming order.</summary>
        public static readonly IReadOnlyList<WdiVisualProfile> All = new[]
        {
            Male, Female, MaleThin, MaleHulk, MaleFat, FemaleThin, FemaleHulk, FemaleFat, KidGirl, KidBoy
        };

        /// <summary>
        /// Resolves the visual target from the renderer's body type and the
        /// pawn's gender. Unknown bodies deliberately return null: Venus must
        /// never remap another race or a custom body to a WDI silhouette.
        /// </summary>
        public static WdiVisualProfile Resolve(string bodyTypeName, Gender gender)
        {
            switch (bodyTypeName)
            {
                case "Male": return Male;
                case "Female": return Female;
                case "Thin": return gender == Gender.Female ? FemaleThin : MaleThin;
                case "Hulk": return gender == Gender.Female ? FemaleHulk : MaleHulk;
                case "Fat": return gender == Gender.Female ? FemaleFat : MaleFat;
                case "Child": return gender == Gender.Female ? KidGirl : KidBoy;
                default: return null;
            }
        }

        /// <summary>The visual profiles whose WDI texture belongs to a body type.</summary>
        public static IEnumerable<WdiVisualProfile> ForBodyType(string bodyTypeName)
        {
            foreach (WdiVisualProfile profile in All)
                if (string.Equals(profile.BodyTypeName, bodyTypeName, StringComparison.Ordinal))
                    yield return profile;
        }
    }
}
