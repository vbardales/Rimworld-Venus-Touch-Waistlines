using System.Reflection;
using HarmonyLib;
using UnityEngine;
using Verse;

namespace TailorMadeWaistlines
{
    public class TailorMadeWaistlinesSettings : ModSettings
    {
        // The three bands default to TailorMade's own values, so installing this
        // mod moves nothing until a slider is moved: where a garment should stop
        // is a matter of the body art and of taste, and neither is ours to guess.
        // The two art options below are different. They exist to fix trousers that
        // read as a plain shell, so they are on: they only ever act where AB's
        // Visible Pants is active, and they are read at startup.
        public const float DefaultPantsTop = 0.58f;
        public const float DefaultBootsTop = 0.20f;
        public const float DefaultChestBottom = 0.25f;

        // The slider ranges. A value read back from the config file is brought
        // into them too, so a hand-edited or damaged file cannot ask TailorMade
        // for a band outside the body.
        public const float PantsMin = 0.20f, PantsMax = 0.90f;
        public const float BootsMin = 0.05f, BootsMax = 0.60f;
        public const float ChestMin = 0.20f, ChestMax = 0.80f;

        // How far the trouser art this mod supplies is moved down the body, as a fraction of its own
        // height. Two values, because a child is drawn smaller: the same fraction is fewer pixels on
        // screen. Both defaults are what a player chose by looking at captures at 1080p and the
        // closest zoom: the first version moved the art 0.02, and the second, 0.05 and 0.10, was
        // judged a little too low, for women and for a girl, so they were 0.03 and 0.09; the girl was then raised 3 px (0.067). That is
        // what the eye said, and it is worth more than arithmetic: a measurement that tried to hit
        // "2 and 4 pixels more" put the child at 0.20, which was wrong. Measured, an adult moves
        // about 0.16 pixels per row of its 512-row texture and a child about 0.18 per row of its
        // 128-row one. Nobody has yet looked at a man: until then his value is the women's.
        public const float DefaultTrouserDrop = 0.03f;
        public const float DefaultChildTrouserDrop = 0.067f;
        public const float TrouserDropMin = 0f, TrouserDropMax = 0.30f;

        public float pantsTop = DefaultPantsTop;
        public float bootsTop = DefaultBootsTop;
        public float chestBottom = DefaultChestBottom;

        // Off by default: it changes how every on-skin torso garment is drawn,
        // and the shirt is compressed into the band rather than cut off at it.
        public bool shortenShirts = false;

        // Experimental APP patterns alter only the four vanilla control garments.
        // They are opt-in and read at startup, so a review pass can seed them
        // without changing a normal player's apparel.
        public bool enableExperimentalAppPatterns = false;

        // On by default: a jacket is drawn to its own length instead of being banded to the waist.
        public bool keepJacketsLong = true;

        // On by default: a dress, robe or long coat drawn for the body by its own mod is left as drawn. Read at startup.
        public bool keepDressesWhole = true;

        // Take General Textures Collection's trouser art where AB supplies a plain shell, and
        // draw details onto the shells that have no such art. Both read at startup.
        public bool useGeneralArt = true;
        public bool detailPlainShells = true;
        public float trouserDrop = DefaultTrouserDrop;
        public float trouserDropChild = DefaultChildTrouserDrop;

        public override void ExposeData()
        {
            base.ExposeData();
            Scribe_Values.Look(ref pantsTop, "pantsTop", DefaultPantsTop);
            Scribe_Values.Look(ref bootsTop, "bootsTop", DefaultBootsTop);
            Scribe_Values.Look(ref chestBottom, "chestBottom", DefaultChestBottom);
            Scribe_Values.Look(ref shortenShirts, "shortenShirts", false);
            Scribe_Values.Look(ref enableExperimentalAppPatterns, "enableExperimentalAppPatterns", false);
            Scribe_Values.Look(ref keepJacketsLong, "keepJacketsLong", true);
            Scribe_Values.Look(ref keepDressesWhole, "keepDressesWhole", true);
            Scribe_Values.Look(ref useGeneralArt, "useGeneralArt", true);
            Scribe_Values.Look(ref detailPlainShells, "detailPlainShells", true);
            Scribe_Values.Look(ref trouserDrop, "trouserDrop", DefaultTrouserDrop);
            Scribe_Values.Look(ref trouserDropChild, "trouserDropChild", DefaultChildTrouserDrop);

            if (Scribe.mode == LoadSaveMode.PostLoadInit)
                Sanitize();
        }

        /// <summary>Brings every value into its slider's range; NaN and infinity fall back to the default.</summary>
        public void Sanitize()
        {
            pantsTop = Clean(pantsTop, PantsMin, PantsMax, DefaultPantsTop);
            bootsTop = Clean(bootsTop, BootsMin, BootsMax, DefaultBootsTop);
            chestBottom = Clean(chestBottom, ChestMin, ChestMax, DefaultChestBottom);
            trouserDrop = Clean(trouserDrop, TrouserDropMin, TrouserDropMax, DefaultTrouserDrop);
            trouserDropChild = Clean(trouserDropChild, TrouserDropMin, TrouserDropMax, DefaultChildTrouserDrop);
        }

        public void ResetToDefaults()
        {
            pantsTop = DefaultPantsTop;
            bootsTop = DefaultBootsTop;
            chestBottom = DefaultChestBottom;
            shortenShirts = false;
            enableExperimentalAppPatterns = false;
            keepJacketsLong = true;
            keepDressesWhole = true;
            useGeneralArt = true;
            detailPlainShells = true;
            trouserDrop = DefaultTrouserDrop;
            trouserDropChild = DefaultChildTrouserDrop;
        }

        private static float Clean(float value, float min, float max, float fallback)
        {
            if (float.IsNaN(value) || float.IsInfinity(value)) return fallback;
            return Mathf.Clamp(value, min, max);
        }
    }

    public class TailorMadeWaistlinesMod : Mod
    {
        public static TailorMadeWaistlinesMod Instance { get; private set; }
        public static TailorMadeWaistlinesSettings Settings;

        private Vector2 scrollPosition;
        private float viewHeight = 600f;

        public TailorMadeWaistlinesMod(ModContentPack content) : base(content)
        {
            Instance = this;
            Settings = GetSettings<TailorMadeWaistlinesSettings>();
            // Every Harmony patch of this mod targets a TailorMade type, and TailorMade is optional: without it the mod
            // still draws the trousers and cuts the shirts WDI ships for each body, but has nothing to patch.
            if (TailorMadeLink.Loaded)
            {
                new Harmony("nelim.venustouch.waistlines").PatchAll(Assembly.GetExecutingAssembly());
                LongEventHandler.ExecuteWhenFinished(TailorMadeLink.SelfTestBands);
            }
            else
                TailorMadeLink.SayAbsent();
            // The autonomous WDI diagnostic renderer is a Venus patch, not a
            // TailorMade one.  It must therefore be installed even in the
            // deliberately AB/APP/TailorMade-free evidence map.
            new Harmony("nelim.venustouch.waistlines.nativewdi").CreateClassProcessor(typeof(NativeWdiPants.NativeGraphicPatch)).Patch();
            // After the game has loaded every mod's textures, which is when there is something to replace.
            LongEventHandler.ExecuteWhenFinished(TrouserArt.Apply);
            // AB's APP bridge adds its own patterns from a late initializer.
            // A single ExecuteWhenFinished here ran before that bridge, so AB
            // won APP's last-pattern selection and Venus' masks were never
            // rendered. Queue one turn later: all first-wave late initializers
            // (including AB) finish first, then our WDI patterns become the
            // final, explicit match. This remains opt-in inside Apply().
            LongEventHandler.ExecuteWhenFinished(() =>
                LongEventHandler.ExecuteWhenFinished(() =>
                {
                    WdiAppPatterns.Apply();
                    NativeWdiPants.Apply();
                }));
            // After the trousers: the jackets are measured on their shells.
            LongEventHandler.ExecuteWhenFinished(JacketArt.Apply);
            // Dresses drawn for the body: TailorMade clips them, they need no fitting.
            LongEventHandler.ExecuteWhenFinished(DressArt.Apply);
            // The bust of the dresses whose lines have been read, fitted to the breasts of WDI's bodies.
            LongEventHandler.ExecuteWhenFinished(BustFit.Apply);
        }

        // The mod's own name, a proper noun: the one player-facing string that is not a key.
        public override string SettingsCategory() => "Venus Touch Waistlines";

        public override void DoSettingsWindowContents(Rect inRect)
        {
            var viewRect = new Rect(0f, 0f, inRect.width - 20f, viewHeight);
            Widgets.BeginScrollView(inRect, ref scrollPosition, viewRect);

            var list = new Listing_Standard();
            list.Begin(viewRect);

            list.Label("TailorMadeWaistlines.Settings.Intro".Translate());
            list.Label("TailorMadeWaistlines.Settings.Scope".Translate());
            list.Gap();

            // The three bands are TailorMade's: without it there is nothing for them to move.
            if (TailorMadeLink.Loaded)
            {
                Slider(list, "TailorMadeWaistlines.Settings.PantsTop", "TailorMadeWaistlines.Settings.PantsTopTip",
                    ref Settings.pantsTop, TailorMadeWaistlinesSettings.PantsMin, TailorMadeWaistlinesSettings.PantsMax);
                Slider(list, "TailorMadeWaistlines.Settings.BootsTop", "TailorMadeWaistlines.Settings.BootsTopTip",
                    ref Settings.bootsTop, TailorMadeWaistlinesSettings.BootsMin, TailorMadeWaistlinesSettings.BootsMax);
                Slider(list, "TailorMadeWaistlines.Settings.ChestBottom", "TailorMadeWaistlines.Settings.ChestBottomTip",
                    ref Settings.chestBottom, TailorMadeWaistlinesSettings.ChestMin, TailorMadeWaistlinesSettings.ChestMax);
                list.Gap();
            }
            else
            {
                list.Label("TailorMadeWaistlines.Settings.NoTailorMade".Translate());
                list.Gap();
            }

            list.CheckboxLabeled("TailorMadeWaistlines.Settings.ShortenShirts".Translate(),
                ref Settings.shortenShirts,
                "TailorMadeWaistlines.Settings.ShortenShirtsTip".Translate());
            list.CheckboxLabeled("TailorMadeWaistlines.Settings.ExperimentalAppPatterns".Translate(),
                ref Settings.enableExperimentalAppPatterns,
                "TailorMadeWaistlines.Settings.ExperimentalAppPatternsTip".Translate());
            list.CheckboxLabeled("TailorMadeWaistlines.Settings.KeepJacketsLong".Translate(),
                ref Settings.keepJacketsLong,
                "TailorMadeWaistlines.Settings.KeepJacketsLongTip".Translate());
            if (TailorMadeLink.Loaded)
                list.CheckboxLabeled("TailorMadeWaistlines.Settings.KeepDressesWhole".Translate(),
                    ref Settings.keepDressesWhole,
                    "TailorMadeWaistlines.Settings.KeepDressesWholeTip".Translate());

            list.Gap();
            list.CheckboxLabeled("TailorMadeWaistlines.Settings.UseGeneralArt".Translate(),
                ref Settings.useGeneralArt,
                "TailorMadeWaistlines.Settings.UseGeneralArtTip".Translate());
            list.CheckboxLabeled("TailorMadeWaistlines.Settings.DetailShells".Translate(),
                ref Settings.detailPlainShells,
                "TailorMadeWaistlines.Settings.DetailShellsTip".Translate());
            Slider(list, "TailorMadeWaistlines.Settings.TrouserDrop", "TailorMadeWaistlines.Settings.TrouserDropTip",
                ref Settings.trouserDrop, TailorMadeWaistlinesSettings.TrouserDropMin, TailorMadeWaistlinesSettings.TrouserDropMax);
            Slider(list, "TailorMadeWaistlines.Settings.TrouserDropChild", "TailorMadeWaistlines.Settings.TrouserDropChildTip",
                ref Settings.trouserDropChild, TailorMadeWaistlinesSettings.TrouserDropMin, TailorMadeWaistlinesSettings.TrouserDropMax);
            list.Label("TailorMadeWaistlines.Settings.ArtNeedsRestart".Translate());

            list.Gap();
            if (list.ButtonText("TailorMadeWaistlines.Settings.Reset".Translate()))
                Settings.ResetToDefaults();

            if (TailorMadeLink.Loaded)
            {
                list.Gap();
                list.Label(Bands.DirectPatchWorks
                    ? "TailorMadeWaistlines.Settings.PatchDirect".Translate()
                    : "TailorMadeWaistlines.Settings.PatchFallback".Translate());
            }

            viewHeight = list.CurHeight + 10f;
            list.End();
            Widgets.EndScrollView();
        }

        private static void Slider(Listing_Standard list, string labelKey, string tipKey, ref float value, float min, float max)
        {
            Rect label = list.Label(labelKey.Translate(value.ToString("0.00")));
            TooltipHandler.TipRegion(label, tipKey.Translate());
            value = Widgets.HorizontalSlider(list.GetRect(22f), value, min, max, false, null, null, null, 0.01f);
        }

        public override void WriteSettings()
        {
            base.WriteSettings();
            // Every fitted texture was baked against the old bands, so they all
            // have to go. TailorMade does the whole sweep itself and repaints
            // the pawns already on the map.
            if (TailorMadeLink.Loaded) TailorMadeLink.ClearAndRepaint();
        }
    }
}
