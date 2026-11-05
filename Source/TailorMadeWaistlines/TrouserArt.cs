using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection;
using System.Text.RegularExpressions;
using RimWorld;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    /// <summary>
    /// Gives AB's trousers something better than the plain shell it draws.
    ///
    /// AB's Visible Pants gives each pair of trousers a worn graphic and ships the textures for it,
    /// but those textures are a bowl: an outline and an even fill. Two better sources exist and
    /// this uses them in order.
    ///
    /// General Textures Collection carries a retexture of the same garment, with a waistband, belt
    /// loops, a fly and pockets, at Mods/VisiblePants/. Its LoadFolders only loads that folder when
    /// XeoNovaDan's Visible Pants is active, so with AB active instead none of it ever reaches a
    /// pawn. Where General has the matching file and no other mod supplies that path, the file is
    /// read from General's installed folder and registered here. That includes a body type AB ships
    /// no texture for: AB still gives the garment that path, so without a texture there the pawn
    /// would have nothing to draw, and supplying one fills the gap rather than adding a garment. A
    /// path somebody else supplies, XeoNovaDan's Visible Pants or General itself, is never touched.
    /// Nothing is copied and nothing is shipped: what is read is what the player already owns.
    ///
    /// Where General has nothing - it has no child, for one - <see cref="TrouserDetail"/> draws
    /// the marks onto AB's own shell.
    ///
    /// Either way the picture can then be moved down the body by a fraction of its height, because
    /// where a garment sits on a body is a matter of the body art and of taste.
    ///
    /// TailorMade would then fit these trousers into a band, stretching art that is already drawn
    /// for the body, which is how a plain shell became a bucket up to the chest. So for every body
    /// type this step supplied art for, TailorMade is told to leave the trousers alone. That is
    /// decided here, in code, and not by shipping a def: the condition that matters is that this
    /// mod actually supplied the art, and a def in XML cannot know that. With both options off, or
    /// without AB, nothing is registered, no def is made, and TailorMade fits the trousers, and
    /// answers the pants slider, exactly as it did before.
    ///
    /// Both are registered in this mod's own content, never in AB's or General's. The game asks
    /// for a texture path from the last loaded mod back, so this mod's entry wins over AB's as long
    /// as it loads after AB, which its About.xml asks for. Removing the mod removes the change.
    /// </summary>
    public static class TrouserArt
    {
        // Each mod's packageId as its own About.xml spells it.
        private const string AbPackageId = "AB.VPLRF";
        private const string GeneralPackageId = "Kas.GeneralCollection";

        // The path AB gives trousers by default, its Normal_Pants category. The game appends the
        // body type and the facing: <path>_<body type>_<facing>.
        private const string PantsPath = "Things/Pawn/Humanlike/Apparel/Pants/Pants";

        // Where General keeps its retexture of that garment, under its own folder.
        private static readonly string[] GeneralPantsFolder =
            { "Mods", "VisiblePants", "Textures", "Core", "Things", "Pawn", "Humanlike", "Apparel", "Pants" };

        // AB's Shorts category. Its shell is the trousers' shell, drawn the same way except that the gap between the legs is
        // left open, because shorts leave the legs bare.
        private const string ShortsPath = "Things/Pawn/Humanlike/Apparel/Shorts/Shorts";

        private static readonly string[] FacingNames = { "south", "east", "north" };

        // AB's Normal_Pants category matches on this keyword, as a plain substring of the def name.
        private const string PantsKeyword = "Pants";

        // The garments that are certain to be there: the adult trousers and the Biotech child's.
        private static readonly string[] BaseTrouserDefNames = { "Apparel_Pants", "Apparel_KidPants" };

        // Where the first row of skin below the navel sits on WDI's bodies, as a fraction of the picture counted from the top,
        // measured with scripts/measure-navel.js (the navel's darkest rows, plus a margin). The trousers start there.
        internal static readonly Dictionary<string, float> BelowNavel = new Dictionary<string, float>
        {
            { "Female", 0.637f }, { "Male", 0.658f }, { "Thin", 0.598f }, { "Fat", 0.658f }, { "Hulk", 0.707f },
        };

        private const string PatternDefPrefix = "TMW_Pants_Native_";

        /// <summary>What the last <see cref="Apply"/> did, for the log and for tests.</summary>
        public static int FromGeneral { get; private set; }
        public static int Drawn { get; private set; }
        public static int LeftAlone { get; private set; }

        public static void Apply()
        {
            FromGeneral = Drawn = LeftAlone = 0;

            var settings = TailorMadeWaistlinesMod.Settings;
            if (settings == null || (!settings.useGeneralArt && !settings.detailPlainShells)) return;

            // No AB, no shells: vanilla trousers have no worn graphic and there is nothing here to improve.
            ModContentPack ab = FindPack(AbPackageId);
            if (ab == null) return;

            string generalDir = settings.useGeneralArt ? GeneralPantsDirectory() : null;
            var mine = TailorMadeWaistlinesMod.Instance.Content.GetContentHolder<Texture2D>();

            var supplied = new List<BodyTypeDef>();
            foreach (BodyTypeDef body in DefDatabase<BodyTypeDef>.AllDefsListForReading)
            {
                // A child is drawn smaller, so the same fraction of the texture is fewer pixels on screen.
                float drop = body.defName == "Child" ? settings.trouserDropChild : settings.trouserDrop;
                int plain = 0;
                for (int f = 0; f < FacingNames.Length; f++)
                {
                    // The body type itself, then its female variant. Female Apparel Variants does not
                    // add body types: for a female pawn of a body type both genders share, it asks for
                    // the same path with _Female on the end when a texture exists there, and General
                    // ships Pants_Fat_Female for exactly that. Only the first can be a shell to draw on.
                    if (Register(body.defName, f, true, generalDir, drop, mine, settings)) plain++;
                    Register(body.defName, f, true, null, drop, mine, settings, ShortsPath, true);
                    Register(body.defName + "_Female", f, false, generalDir, drop, mine, settings);
                    RegisterFemaleShell(body.defName, f, drop, mine, settings, PantsPath, false);
                    RegisterFemaleShell(body.defName, f, drop, mine, settings, ShortsPath, true);
                }

                // TailorMade's ignore is per body type, not per facing or gender: it would leave every
                // facing of this body alone. So the body counts as supplied only when the plain variant
                // was supplied in all three facings. A body with some facings only would otherwise be
                // left with AB's raw shell in the facing that was not replaced, drawn unfitted.
                if (plain == FacingNames.Length) supplied.Add(body);
                else if (plain > 0)
                    Log.Warning("[TailorMade Waistlines] " + body.defName + " trousers were supplied in " + plain + " of "
                        + FacingNames.Length + " facings, so TailorMade keeps fitting them and the art this mod supplied is stretched into the band.");
            }

            LeaveToTailorMade(supplied);

            // A silent failure here looks exactly like success from outside: the trousers are simply
            // drawn as the shell they always were. So the one case that can be recognised as wrong is
            // said out loud, where a test can find it.
            if (generalDir != null && FromGeneral == 0 && LeftAlone == 0)
                Log.Warning("[TailorMade Waistlines] General Textures Collection has trouser textures at " + generalDir
                    + " but none was used: no body type matched a file, or none of AB's textures was there to replace.");

            Log.Message("[TailorMade Waistlines] trousers: " + FromGeneral + " textures read from General Textures Collection, "
                + Drawn + " drawn onto AB's plain shells, " + LeftAlone + " left to whichever mod supplies them, lowered by "
                + settings.trouserDrop.ToString("0.00") + " of their height, children " + settings.trouserDropChild.ToString("0.00") + ".");
        }

        /// <summary>
        /// One texture path: leave it alone if somebody else draws it, otherwise give it General's art
        /// when General has that file, otherwise (for a real body type) draw details onto AB's shell.
        /// </summary>
        private static bool Register(string variant, int facing, bool mayDrawOnShell, string generalDir, float drop,
            ModContentHolder<Texture2D> mine, TailorMadeWaistlinesSettings settings, string basePath = PantsPath, bool bareLegs = false)
        {
            string path = basePath + "_" + variant + "_" + FacingNames[facing];
            if (mine.contentList.ContainsKey(path)) return false;

            ModContentPack supplier = SupplierOf(path);
            if (supplier != null && !IsPack(supplier, AbPackageId))
            {
                // Somebody else draws it - General itself, when XeoNovaDan's is active. It is not ours to touch.
                LeftAlone++;
                return false;
            }

            Texture2D texture = FromGeneralFolder(generalDir, variant, FacingNames[facing], drop);
            if (texture != null)
            {
                mine.contentList[path] = texture;
                FromGeneral++;
                return true;
            }

            if (!mayDrawOnShell || !settings.detailPlainShells || supplier == null) return false;
            Texture2D shell = supplier.GetContentHolder<Texture2D>().Get(path);
            Texture2D detailed = shell == null ? null : Detail(shell, (Facing)facing, path, drop, bareLegs);
            if (detailed == null) return false;
            mine.contentList[path] = detailed;
            Drawn++;
            return true;
        }

        /// <summary>
        /// AB has one shell per body type for both sexes. WDI draws a separate female body for Thin, Fat and Hulk, with its
        /// own underwear, so a female pawn of those body types gets her own copy of the shell, cut on her own underwear.
        /// Female Apparel Variants asks for the path with _Female on the end when a texture exists there.
        /// </summary>
        private static void RegisterFemaleShell(string body, int facing, float drop, ModContentHolder<Texture2D> mine,
            TailorMadeWaistlinesSettings settings, string basePath, bool bareLegs)
        {
            string key = body + "_Female";
            string femalePath = basePath + "_" + key + "_" + FacingNames[facing];
            string path = basePath + "_" + body + "_" + FacingNames[facing];
            bool noCurve = ShirtCut.ProfileFor(key, FacingNames[facing]) == null;
            if (noCurve || !settings.detailPlainShells) return;
            if (mine.contentList.ContainsKey(femalePath) || SupplierOf(femalePath) != null) return;
            // AB's own shell: by now this mod's content already holds the detailed copy of the male one under the same path.
            ModContentPack ab = FindPack(AbPackageId);
            Texture2D shell = ab?.GetContentHolder<Texture2D>().Get(path);
            Texture2D detailed = shell == null ? null : Detail(shell, (Facing)facing, path, drop, bareLegs, key);
            if (detailed == null) return;
            mine.contentList[femalePath] = detailed;
            Drawn++;
        }

        /// <summary>
        /// Tells TailorMade to leave the trousers alone for each body type this step supplied art for.
        /// One pattern def per body type, so a body type whose art belongs to somebody else keeps being
        /// fitted as before. TailorMade reads its defs once, at the first pawn it renders, which is long
        /// after this runs; if that ever stops being true the trousers are still fitted, and it says so.
        /// </summary>
        private static void LeaveToTailorMade(List<BodyTypeDef> bodies)
        {
            if (bodies.Count == 0 || !TailorMadeLink.Loaded) return;

            if (TailorMadeLink.HasReadItsDefs())
                Log.Warning("[TailorMade Waistlines] TailorMade had already read its pattern defs before this ran, so it will keep"
                    + " fitting the trousers this mod supplies until the game is restarted.");

            List<string> targets = SelectTrouserTargets(ApparelDefs());
            if (targets.Count > BaseTrouserDefNames.Length)
                Log.Message("[TailorMade Waistlines] " + (targets.Count - BaseTrouserDefNames.Length)
                    + " more garment(s) share the trouser art and are left alone by TailorMade too.");

            foreach (BodyTypeDef body in bodies)
            {
                TailorMadeLink.LeaveAlone(PatternDefPrefix + body.defName, body, targets);
            }
        }

        /// <summary>
        /// The def names TailorMade must leave alone: every garment AB's Normal_Pants category gives
        /// this art to, and not only the two vanilla ones. AB matches a category by a plain substring of
        /// the def name and only writes a path where the def has none, so a def is ours when its worn
        /// graphic is already this path (any name: the player may add keywords to AB's category), or
        /// when it is still empty and its name holds AB's default keyword. Read from the defs
        /// rather than assumed, because a modded <c>...Pants</c> shares the path with the vanilla ones
        /// and would otherwise be fitted a second time into a band, on art that is already drawn for
        /// the body. A def with a graphic of its own is another mod's art and is left to TailorMade.
        ///
        /// Pure over (defName, wornGraphicPath) pairs, so it is checked outside the game.
        /// </summary>
        public static List<string> SelectTrouserTargets(IEnumerable<KeyValuePair<string, string>> apparel)
        {
            var names = new List<string>(BaseTrouserDefNames);
            if (apparel != null)
            {
                foreach (KeyValuePair<string, string> a in apparel)
                {
                    if (string.IsNullOrEmpty(a.Key) || names.Contains(a.Key)) continue;
                    // Already on AB's trousers or shorts path, whatever its name: AB's keywords are the
                    // player's to edit (a lowercase 'pants' catches LTS_Sweatpants).
                    if (a.Value == ShortsPath || a.Value == PantsPath) { names.Add(a.Key); continue; }
                    if (!string.IsNullOrEmpty(a.Value)) continue;
                    if (a.Key.IndexOf(PantsKeyword, StringComparison.Ordinal) < 0) continue;
                    names.Add(a.Key);
                }
            }

            // TailorMade reads these as regular expressions on the def name.
            return names.ConvertAll(n => "^" + Regex.Escape(n) + "$");
        }

        private static IEnumerable<KeyValuePair<string, string>> ApparelDefs()
        {
            foreach (ThingDef def in DefDatabase<ThingDef>.AllDefsListForReading)
                if (def.apparel != null)
                    yield return new KeyValuePair<string, string>(def.defName, def.apparel.wornGraphicPath);
        }

        // ------------------------------------------------------------------ the sources

        /// <summary>General's folder of trouser textures, or null when General is not active or has moved it.</summary>
        private static string GeneralPantsDirectory()
        {
            ModContentPack general = FindPack(GeneralPackageId);
            if (general == null) return null;

            string dir = general.RootDir;
            foreach (string part in GeneralPantsFolder) dir = Path.Combine(dir, part);
            if (Directory.Exists(dir)) return dir;

            Log.Warning("[TailorMade Waistlines] General Textures Collection is active but has no trouser textures at "
                + dir + ": it has been reorganised, and its art is not being used.");
            return null;
        }

        private static Texture2D FromGeneralFolder(string dir, string bodyType, string facing, float drop)
        {
            if (dir == null) return null;
            string file = Path.Combine(dir, "Pants_" + bodyType + "_" + facing + ".png");
            if (!File.Exists(file)) return null;

            // Decoded into a texture that is still readable, which is not how the game keeps a mod's
            // textures, so the pixels can be moved before it is built the way the game builds one.
            var decoded = new Texture2D(2, 2, TextureFormat.RGBA32, false);
            try
            {
                if (!decoded.LoadImage(File.ReadAllBytes(file))) return null;
                byte[] rgba = ToTopDown(decoded.GetPixels32(), decoded.width, decoded.height);
                rgba = Lower(rgba, decoded.width, decoded.height, drop);
                return FromTopDown(rgba, decoded.width, decoded.height, "TMW_General_Pants_" + bodyType + "_" + facing);
            }
            catch (Exception e)
            {
                Log.Warning("[TailorMade Waistlines] could not read " + file + ": " + e.Message);
                return null;
            }
            finally
            {
                UnityEngine.Object.Destroy(decoded);
            }
        }

        private static Texture2D Detail(Texture2D shell, Facing facing, string path, float drop, bool bareLegs, string curveBody = null)
        {
            try
            {
                byte[] rgba = ReadTopDown(shell, out int width, out int height);
                byte[] detailed;
                float[] curve = UnderwearCurve(path, curveBody, out string facingName);
                if (curve != null)
                {
                    // The underwear is the mask: the trousers start on its top edge, column by column. A shell that begins lower
                    // is first stretched up to the curve's highest point, one that begins higher is cut down to the curve.
                    float shift = drop - TailorMadeWaistlinesSettings.DefaultTrouserDrop;
                    float highest = float.MaxValue;
                    foreach (float v in curve) if (v < highest) highest = v;
                    rgba = TrouserDetail.StretchTop(rgba, width, height, (int)Math.Round((highest + shift) * height, MidpointRounding.AwayFromZero));
                    var rows = new int[width];
                    for (int x = 0; x < width; x++)
                        rows[x] = (int)Math.Round((curve[Math.Min(curve.Length - 1, (int)(x * (long)curve.Length / width))] + shift) * height, MidpointRounding.AwayFromZero);
                    rgba = TrouserDetail.CutAbove(rgba, width, height, rows);
                    detailed = TrouserDetail.Apply(rgba, width, height, facing, bareLegs);
                }
                else if (TryBelowNavel(path, out float target))
                {
                    // The slider is an offset from the navel: its default puts the top right under it.
                    float top = target + (drop - TailorMadeWaistlinesSettings.DefaultTrouserDrop);
                    rgba = TrouserDetail.StretchTop(rgba, width, height, (int)Math.Round(top * height, MidpointRounding.AwayFromZero));
                    detailed = TrouserDetail.Apply(rgba, width, height, facing, bareLegs);
                }
                else
                {
                    detailed = TrouserDetail.Apply(rgba, width, height, facing, bareLegs);
                    detailed = Lower(detailed, width, height, drop);
                }
                detailed = TrouserDetail.SmoothAlpha(detailed, width, height);
                return FromTopDown(detailed, width, height, "TMW_Detail_" + path.Replace('/', '_'));
            }
            catch (Exception e)
            {
                Log.Warning("[TailorMade Waistlines] could not draw details onto " + path + ": " + e.Message);
                return null;
            }
        }

        /// <summary>Moves the picture down by a fraction of the texture's height, without cutting it.</summary>
        /// <summary>The top edge of WDI's underwear for the body and facing of a trouser path, or null (no WDI, a body without underwear).</summary>
        private static float[] UnderwearCurve(string path, string curveBody, out string facing)
        {
            facing = null;
            Match m = Regex.Match(path, @"(?:Pants|Shorts)_([A-Za-z]+)_(south|east|north)$");
            if (!m.Success) return null;
            facing = m.Groups[2].Value;
            return ShirtCut.ProfileFor(curveBody ?? m.Groups[1].Value, facing);
        }

        private static bool TryBelowNavel(string path, out float target)
        {
            target = 0f;
            Match m = Regex.Match(path, @"(?:Pants|Shorts)_([A-Za-z]+)_(south|east|north)$");
            return m.Success && BelowNavel.TryGetValue(m.Groups[1].Value, out target);
        }

        private static byte[] Lower(byte[] rgba, int width, int height, float drop)
        {
            int rows = (int)Math.Round(drop * height, MidpointRounding.AwayFromZero);
            return rows <= 0 ? rgba : TrouserDetail.CompressTop(rgba, width, height, rows);
        }

        // ----------------------------------------------------- what the jackets are measured on

        internal static ModContentPack FindPackPublic(string packageId) => FindPack(packageId);

        internal static string PantsTexturePath(string body, string facing) => PantsPath + "_" + body + "_" + facing;

        /// <summary>This mod's own texture for the path if it has one, otherwise the one the game would use.</summary>
        internal static Texture2D TextureAt(string path, ModContentHolder<Texture2D> mine)
        {
            if (mine.contentList.TryGetValue(path, out Texture2D own)) return own;
            ModContentPack supplier = SupplierOf(path);
            if (supplier != null) return supplier.GetContentHolder<Texture2D>().Get(path);
            // The game's own textures are not in any mod's content: ContentFinder reaches them.
            return ContentFinder<Texture2D>.Get(path, false);
        }

        internal static byte[] Read(Texture texture, out int width, out int height) => ReadTopDown(texture, out width, out height);

        internal static Texture2D Build(byte[] rgba, int width, int height, string name) => FromTopDown(rgba, width, height, name);

        // ---------------------------------------------------------------- who supplies

        private static ModContentPack FindPack(string packageId)
        {
            foreach (ModContentPack pack in LoadedModManager.RunningModsListForReading)
                if (IsPack(pack, packageId)) return pack;
            return null;
        }

        private static bool IsPack(ModContentPack pack, string packageId) =>
            string.Equals(pack.PackageIdPlayerFacing, packageId, StringComparison.OrdinalIgnoreCase);

        /// <summary>The mod the game would take this texture from: the last loaded one that has it.</summary>
        private static ModContentPack SupplierOf(string path)
        {
            var mods = LoadedModManager.RunningModsListForReading;
            for (int i = mods.Count - 1; i >= 0; i--)
                if (mods[i].GetContentHolder<Texture2D>().Get(path) != null) return mods[i];
            return null;
        }

        // -------------------------------------------------------------------- pixels

        /// <summary>
        /// The texture's pixels as RGBA bytes, top row first. The game's textures are compressed and
        /// not readable, so it goes through a render texture, as TailorMade does.
        /// </summary>
        private static byte[] ReadTopDown(Texture source, out int width, out int height)
        {
            width = source.width;
            height = source.height;
            RenderTexture temp = RenderTexture.GetTemporary(width, height, 0, RenderTextureFormat.ARGB32, RenderTextureReadWrite.Default);
            RenderTexture active = RenderTexture.active;
            Texture2D copy = null;
            try
            {
                Graphics.Blit(source, temp);
                RenderTexture.active = temp;
                copy = new Texture2D(width, height, TextureFormat.RGBA32, false);
                copy.ReadPixels(new Rect(0f, 0f, width, height), 0, 0);
                copy.Apply(false, false);
                return ToTopDown(copy.GetPixels32(), width, height);
            }
            finally
            {
                RenderTexture.active = active;
                RenderTexture.ReleaseTemporary(temp);
                if (copy != null) UnityEngine.Object.Destroy(copy);
            }
        }

        /// <summary>Unity keeps the bottom row first; the generator and the shift work top row first.</summary>
        private static byte[] ToTopDown(Color32[] bottomUp, int width, int height)
        {
            var rgba = new byte[width * height * TrouserDetail.Channels];
            for (int y = 0; y < height; y++)
            {
                int from = (height - 1 - y) * width;
                for (int x = 0; x < width; x++)
                {
                    Color32 c = bottomUp[from + x];
                    int i = (y * width + x) * TrouserDetail.Channels;
                    rgba[i] = c.r; rgba[i + 1] = c.g; rgba[i + 2] = c.b; rgba[i + 3] = c.a;
                }
            }
            return rgba;
        }

        /// <summary>
        /// A texture built the way the game builds one from a PNG in a mod: trilinear, mipmapped,
        /// and compressed when the player has texture compression on and the size allows it.
        /// </summary>
        private static Texture2D FromTopDown(byte[] rgba, int width, int height, string name)
        {
            var colors = new Color32[width * height];
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int i = (y * width + x) * TrouserDetail.Channels;
                    colors[(height - 1 - y) * width + x] = new Color32(rgba[i], rgba[i + 1], rgba[i + 2], rgba[i + 3]);
                }

            var texture = new Texture2D(width, height, TextureFormat.RGBA32, true);
            texture.SetPixels32(colors);
            texture.name = name;
            texture.wrapMode = TextureWrapMode.Clamp;
            texture.filterMode = FilterMode.Trilinear;
            texture.anisoLevel = 2;

            if (Prefs.TextureCompression && width % 4 == 0 && height % 4 == 0)
            {
                texture.Apply(true, false);   // build the mip chain while the pixels are still readable
                texture.Compress(true);
                texture.Apply(false, true);
            }
            else
            {
                texture.Apply(true, true);
            }
            return texture;
        }
    }
}
