<#
.SYNOPSIS
    Exercises this mod's own decisions - the bands it hands back and the
    garments it agrees to shorten - without starting RimWorld.

.DESCRIPTION
    `Check-Mod.ps1` answers "does TailorMade still look the way the patches
    assume". It says nothing about whether our own code decides the right
    thing, because it never runs a line of it.

    This does. Every decision the mod makes is a pure function of the settings,
    and there are three of them:

      - `Bands.For(cls)` turns three sliders into a band per apparel class;
      - `Bands.BakeFitted_Patch.Prefix` rewrites a band it recognises as
        TailorMade's untouched stock value, and must leave anything else -
        including a band another mod tuned - exactly as it found it;
      - `ChestArt.ConfirmChestArt_Patch.Postfix` lifts astryl's torso-art test
        for on-skin garments only, so shirts shorten and dusters drape.

    All three are reached by reflection on the shipped DLL with the game's
    Managed folder on the probe path. The patch bodies are plain static methods,
    so Harmony is never needed to invoke them: a `ref` parameter is an element
    of the argument array, read back after the call.

    What is not here: the defaults, the reset and the clamping of a hand-edited
    config are `Check-Settings.ps1`, and a band is only ever compared as a
    number - no texture is baked, so how a shortened shirt *reads* stays a
    question for scenario 6 of TESTING.md.

    Two things the game normally builds are faked here:

      - `ThingDef` and `ApparelProperties` are allocated without their
        constructors (`GetUninitializedObject`). Constructing a ThingDef runs
        `Verse.BaseContent`'s static initialiser, which wants Unity and is not
        there.
      - `ApparelLayerDefOf.OnSkin` is a def the loader fills at startup. Here
        it is assigned a bare `ApparelLayerDef` instance, which is all the
        postfix compares against - it tests identity, not content.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Check-Logic.ps1
#>

[CmdletBinding()]
param(
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed',
    [string]$TailorMade = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3756915448\Assemblies\TailorMadeUnifiedApparelBodyRefitting.dll',
    [string]$Harmony = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2009463077\1.6\Assemblies\0Harmony.dll',
    [string]$ModAssembly
)

$ErrorActionPreference = 'Stop'
if (-not $ModAssembly) {
    $ModAssembly = Join-Path (Split-Path -Parent $PSScriptRoot) 'Mod\Assemblies\TailorMadeWaistlines.dll'
}

$script:failures = @()
$script:checks = 0

function Assert-That {
    param([string]$What, [bool]$Ok, [string]$Detail)
    $script:checks++
    if ($Ok) {
        Write-Host ("  ok    " + $What)
    } else {
        $script:failures += $What + $(if ($Detail) { " - " + $Detail } else { "" })
        Write-Host ("  FAIL  " + $What + $(if ($Detail) { " - " + $Detail } else { "" }))
    }
}

function Assert-Band {
    param([string]$What, $Band, [double]$X, [double]$Y)
    $ok = ([Math]::Abs($Band.x - $X) -lt 0.0005) -and ([Math]::Abs($Band.y - $Y) -lt 0.0005)
    Assert-That $What $ok ("got (" + $Band.x + ", " + $Band.y + "), wanted (" + $X + ", " + $Y + ")")
}

# PowerShell refuses to touch a member of a type that has two names differing
# only in case, and ThingDef has `size` and `Size`. Every field on a game type
# therefore goes through reflection.
function Get-Field { param([type]$Type, [string]$Name, $Instance) $Type.GetField($Name).GetValue($Instance) }
function Set-Field { param([type]$Type, [string]$Name, $Instance, $Value) $Type.GetField($Name).SetValue($Instance, $Value) }

function New-Blank { param([type]$Type) [System.Runtime.Serialization.FormatterServices]::GetUninitializedObject($Type) }

# --- loading -----------------------------------------------------------------
$probeDirs = @($Managed, (Split-Path -Parent $TailorMade), (Split-Path -Parent $Harmony), (Split-Path -Parent $ModAssembly)) |
    Select-Object -Unique

$script:resolver = [System.ResolveEventHandler] {
    param($sender, $e)
    $name = (New-Object System.Reflection.AssemblyName($e.Name)).Name
    foreach ($dir in $probeDirs) {
        $candidate = Join-Path $dir ($name + '.dll')
        if (Test-Path $candidate) { return [System.Reflection.Assembly]::LoadFrom($candidate) }
    }
    return $null
}
[System.AppDomain]::CurrentDomain.add_AssemblyResolve($script:resolver)

try {
    foreach ($path in @($TailorMade, $Harmony, $ModAssembly)) {
        if (-not (Test-Path $path)) {
            Write-Host ("cannot find " + $path) -ForegroundColor Red
            exit 2
        }
    }

    $tm = [System.Reflection.Assembly]::LoadFrom($TailorMade)
    [System.Reflection.Assembly]::LoadFrom($Harmony) | Out-Null
    $ours = [System.Reflection.Assembly]::LoadFrom($ModAssembly)
    Write-Host ""
    Write-Host ("TailorMade  " + $tm.GetName().Version)
    Write-Host ("this mod    " + $ours.GetName().Version)

    $bands = $ours.GetType('TailorMadeWaistlines.Bands', $true)
    $modType = $ours.GetType('TailorMadeWaistlines.TailorMadeWaistlinesMod', $true)
    $settingsType = $ours.GetType('TailorMadeWaistlines.TailorMadeWaistlinesSettings', $true)
    $apparelClass = $tm.GetType('TailorMade.ApparelClass', $true)
    $classifier = $tm.GetType('TailorMade.ApparelClassifier', $true)
    $wdiProfiles = $ours.GetType('TailorMadeWaistlines.WdiVisualProfiles', $true)

    # A fresh settings object, planted where the mod looks for it. Nothing in
    # the decisions reads anything else, so this is the whole world they need.
    $settings = [System.Activator]::CreateInstance($settingsType)
    $modType.GetField('Settings', [System.Reflection.BindingFlags]'Public,Static').SetValue($null, $settings)

    $For = $bands.GetMethod('For')
    $ClassOf = { param([string]$n) [Enum]::Parse($apparelClass, $n) }

    # --- WDI's target silhouettes --------------------------------------------
    Write-Host ""
    Write-Host "WDI visual targets stay distinct"
    $allProfiles = $wdiProfiles.GetField('All', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    Assert-That 'WDI declares all ten human silhouette targets' ($allProfiles.Count -eq 10)
    $resolveProfile = $wdiProfiles.GetMethod('Resolve')
    function Resolve-WdiProfile {
        param([string]$Body, [Verse.Gender]$Gender)
        return $resolveProfile.Invoke($null, @($Body, $Gender))
    }
    function Assert-WdiProfile {
        param([string]$What, [string]$Body, [Verse.Gender]$Gender, [string]$Id, [string]$TextureKey)
        $profile = Resolve-WdiProfile $Body $Gender
        $ok = $profile -and $profile.Id -eq $Id -and $profile.TextureKey -eq $TextureKey
        Assert-That $What $ok $(if ($profile) { "got $($profile.Id)/$($profile.TextureKey)" } else { 'got null' })
    }
    Assert-WdiProfile 'Thin man maps to Male_Thin'       'Thin'  ([Verse.Gender]::Male)   'Male_Thin'   'Thin'
    Assert-WdiProfile 'Thin woman maps to Female_Thin'   'Thin'  ([Verse.Gender]::Female) 'Female_Thin' 'Thin_Female'
    Assert-WdiProfile 'Hulk woman maps to Female_Hulk'   'Hulk'  ([Verse.Gender]::Female) 'Female_Hulk' 'Hulk_Female'
    Assert-WdiProfile 'Fat woman maps to Female_Fat'     'Fat'   ([Verse.Gender]::Female) 'Female_Fat'  'Fat_Female'
    Assert-WdiProfile 'girl maps to Kid_Girl'            'Child' ([Verse.Gender]::Female) 'Kid_Girl'    'Child'
    Assert-WdiProfile 'boy maps to Kid_Boy'              'Child' ([Verse.Gender]::Male)   'Kid_Boy'     'Child'
    Assert-That 'an unknown body is never remapped to WDI' ((Resolve-WdiProfile 'AlienCustom' ([Verse.Gender]::Male)) -eq $null)

    # --- the sliders start where TailorMade left them -------------------------
    Write-Host ""
    Write-Host "a fresh install changes nothing"

    Assert-That 'settings default pantsTop 0.58'   ([Math]::Abs((Get-Field $settingsType 'pantsTop' $settings) - 0.58) -lt 0.0005)
    Assert-That 'settings default bootsTop 0.20'   ([Math]::Abs((Get-Field $settingsType 'bootsTop' $settings) - 0.20) -lt 0.0005)
    Assert-That 'settings default chestBottom 0.25'([Math]::Abs((Get-Field $settingsType 'chestBottom' $settings) - 0.25) -lt 0.0005)
      Assert-That 'settings default shortenShirts off' ((Get-Field $settingsType 'shortenShirts' $settings) -eq $false)
      Assert-That 'settings default experimental APP patterns off' ((Get-Field $settingsType 'enableExperimentalAppPatterns' $settings) -eq $false)

    # Our copies of the stock values, against TailorMade's live fields. The
    # fallback prefix only rewrites a band it recognises, so a drift here is a
    # fallback that silently stops correcting anything.
    foreach ($pair in @(@('StockBoots', 'BootsBand'), @('StockPants', 'PantsBand'), @('StockChest', 'ChestBand'))) {
        $mine = $bands.GetField($pair[0], [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
        $field = $classifier.GetField($pair[1], [System.Reflection.BindingFlags]'Public,Static')
        if (-not $field) { Assert-That ("Bands." + $pair[0] + " matches ApparelClassifier." + $pair[1]) $false 'field not found'; continue }
        $theirs = $field.GetValue($null)
        Assert-Band ("Bands." + $pair[0] + " matches ApparelClassifier." + $pair[1]) $mine $theirs.x $theirs.y
    }

    Assert-Band 'Bands.For(Pants) on defaults' ($For.Invoke($null, @((& $ClassOf 'Pants')))) 0.0 0.58
    Assert-Band 'Bands.For(Boots) on defaults' ($For.Invoke($null, @((& $ClassOf 'Boots')))) 0.0 0.20
    Assert-Band 'Bands.For(Chest) on defaults' ($For.Invoke($null, @((& $ClassOf 'Chest')))) 0.25 1.0

    # --- each band follows its own slider, and only its own -------------------
    Write-Host ""
    Write-Host "each band follows its own slider"

    Set-Field $settingsType 'pantsTop' $settings ([float]0.40)
    Assert-Band 'pants band drops with the slider'  ($For.Invoke($null, @((& $ClassOf 'Pants')))) 0.0 0.40
    Assert-Band 'the boots band did not move'       ($For.Invoke($null, @((& $ClassOf 'Boots')))) 0.0 0.20
    Assert-Band 'the chest band did not move'       ($For.Invoke($null, @((& $ClassOf 'Chest')))) 0.25 1.0

    Set-Field $settingsType 'bootsTop' $settings ([float]0.35)
    Assert-Band 'boots band follows its slider'     ($For.Invoke($null, @((& $ClassOf 'Boots')))) 0.0 0.35

    Set-Field $settingsType 'chestBottom' $settings ([float]0.30)
    Assert-Band 'chest band lowers its floor'       ($For.Invoke($null, @((& $ClassOf 'Chest')))) 0.30 1.0
    Assert-That 'chest band keeps its top at 1'     ([Math]::Abs($For.Invoke($null, @((& $ClassOf 'Chest'))).y - 1.0) -lt 0.0005)

    # Every class TailorMade defines, so a new one added upstream shows up here
    # as a band we hand back unbanded rather than as a silent miss. Hands,
    # Head and whatever else is to be left whole: (0, 1).
    Write-Host ""
    Write-Host "classes we do not band are left whole"
    foreach ($name in [Enum]::GetNames($apparelClass)) {
        if ($name -in @('Boots', 'Pants', 'Chest')) { continue }
        Assert-Band ("Bands.For(" + $name + ") is the whole body") ($For.Invoke($null, @((& $ClassOf $name)))) 0.0 1.0
    }

    # --- the postfix on BandFor -----------------------------------------------
    # The direct patch's whole body: whatever TailorMade computed is discarded.
    Write-Host ""
    Write-Host "the BandFor postfix overwrites TailorMade's answer"

    $bandForPostfix = $ours.GetType('TailorMadeWaistlines.Bands+BandFor_Patch', $true).GetMethod('Postfix')
    $args = [object[]]@((& $ClassOf 'Pants'), [UnityEngine.Vector2]::new(0, 0.58))
    [void]$bandForPostfix.Invoke($null, $args)
    Assert-Band 'postfix replaces the stock band' $args[1] 0.0 0.40

    $args = [object[]]@((& $ClassOf 'Pants'), [UnityEngine.Vector2]::new(0.11, 0.22))
    [void]$bandForPostfix.Invoke($null, $args)
    Assert-Band 'postfix replaces a band it has never seen' $args[1] 0.0 0.40

    # --- the fallback prefix on BakeFitted ------------------------------------
    Write-Host ""
    Write-Host "the fallback prefix, while the direct patch is not known to work"

    $directWorks = $bands.GetField('DirectPatchWorks', [System.Reflection.BindingFlags]'Public,Static')
    $prefix = $ours.GetType('TailorMadeWaistlines.Bands+BakeFitted_Patch', $true).GetMethod('Prefix')
    $directWorks.SetValue($null, $false)

    function Invoke-Prefix { param([double]$X, [double]$Y) $a = [object[]]@([UnityEngine.Vector2]::new($X, $Y)); [void]$prefix.Invoke($null, $a); return $a[0] }

    Assert-Band 'stock pants band is corrected' (Invoke-Prefix 0.0 0.58) 0.0 0.40
    Assert-Band 'stock boots band is corrected' (Invoke-Prefix 0.0 0.20) 0.0 0.35
    Assert-Band 'stock chest band is corrected' (Invoke-Prefix 0.45 1.0) 0.30 1.0

    # Inside the tolerance the code itself uses, and just outside it.
    Assert-Band 'a stock pants band off by 0.0004 is still recognised' (Invoke-Prefix 0.0 0.5804) 0.0 0.40
    Assert-Band 'a band off by 0.002 is left alone'                    (Invoke-Prefix 0.0 0.582) 0.0 0.582

    # The bands another mod, or a future TailorMade, might hand us. Rewriting
    # one of these would be us breaking something that was already right.
    Assert-Band 'an unrecognised band is left alone'      (Invoke-Prefix 0.1 0.9) 0.1 0.9
    Assert-Band 'a full-body band is left alone'          (Invoke-Prefix 0.0 1.0) 0.0 1.0
    Assert-Band 'a band equal to our own target is kept'  (Invoke-Prefix 0.0 0.40) 0.0 0.40

    Write-Host ""
    Write-Host "and once the direct patch is known to work, it does nothing"
    $directWorks.SetValue($null, $true)
    Assert-Band 'stock pants band is left to the postfix' (Invoke-Prefix 0.0 0.58) 0.0 0.58
    Assert-Band 'stock boots band is left to the postfix' (Invoke-Prefix 0.0 0.20) 0.0 0.20
    Assert-Band 'stock chest band is left to the postfix' (Invoke-Prefix 0.45 1.0) 0.45 1.0
    $directWorks.SetValue($null, $false)

    # --- which torso garments get shortened -----------------------------------
    Write-Host ""
    Write-Host "the shirt option, garment by garment"

    $thingDefType = [Verse.ThingDef]
    $apparelPropsType = [RimWorld.ApparelProperties]
    $layerType = [Verse.ApparelLayerDef]

    $onSkin = New-Blank $layerType
    $shell  = New-Blank $layerType
    $middle = New-Blank $layerType

    # Touching any DefOf runs its static constructor, which is a single call to
    # `DefOfHelper.EnsureInitializedInCtor` - a guard that warns when a def is
    # read before the loader has bound them. Outside the game that warning goes
    # through Scribe and Unity's logger and dies on an internal call. Telling
    # the guard that binding is in progress skips it, and the field is then an
    # ordinary static we can fill ourselves.
    [RimWorld.DefOfHelper].GetField('bindingNow', [System.Reflection.BindingFlags]'NonPublic,Static').SetValue($null, $true)
    [RimWorld.ApparelLayerDefOf].GetField('OnSkin').SetValue($null, $onSkin)

    function New-Garment {
        param($Layer)
        $def = New-Blank $thingDefType
        if ($Layer) {
            $props = New-Blank $apparelPropsType
            $layers = [System.Collections.Generic.List[Verse.ApparelLayerDef]]::new()
            $layers.Add($Layer)
            Set-Field $apparelPropsType 'layers' $props $layers
            Set-Field $thingDefType 'apparel' $def $props
        }
        return $def
    }

    $shirt  = New-Garment $onSkin   # Apparel_Shirt*, tribalwear
    $duster = New-Garment $shell    # dusters, parkas, jackets, robes
    $vest   = New-Garment $middle   # flak vest and the like
    $wall   = New-Garment $null     # anything that is not apparel at all

    $postfix = $ours.GetType('TailorMadeWaistlines.ChestArt+ConfirmChestArt_Patch', $true).GetMethod('Postfix')
    function Invoke-Confirm { param($Def, [bool]$Result) $a = [object[]]@($Def, $Result); [void]$postfix.Invoke($null, $a); return [bool]$a[1] }

    Set-Field $settingsType 'shortenShirts' $settings $true
    Assert-That 'an on-skin shirt is confirmed as chest art'   ((Invoke-Confirm $shirt  $false) -eq $true)
    Assert-That 'a shell duster still drapes'                  ((Invoke-Confirm $duster $false) -eq $false)
    Assert-That 'a middle-layer vest is left to TailorMade'    ((Invoke-Confirm $vest   $false) -eq $false)
    Assert-That 'a def with no apparel block is left alone'    ((Invoke-Confirm $wall   $false) -eq $false)
    Assert-That 'a null def does not throw'                    ((Invoke-Confirm $null   $false) -eq $false)
    Assert-That "TailorMade's own yes is never reversed"        ((Invoke-Confirm $duster $true)  -eq $true)

    Set-Field $settingsType 'shortenShirts' $settings $false
    Write-Host ""
    Write-Host "and with the option off, nothing is lifted"
    Assert-That 'an on-skin shirt stays full-body'             ((Invoke-Confirm $shirt  $false) -eq $false)
    Assert-That "TailorMade's own yes still stands"            ((Invoke-Confirm $shirt  $true)  -eq $true)

    # --- which garments TailorMade is told to leave alone ---------------------
    # AB matches a category by a plain substring of the def name and only writes a path where the
    # def has none. The trouser art sits on that one shared path, so every def AB gave it to has to
    # be left alone, not just the two vanilla ones - and no def carrying another mod's own art.
    Write-Host ""
    Write-Host "the garments TailorMade is told to leave alone"

    $trouserArt = $ours.GetType('TailorMadeWaistlines.TrouserArt', $true)
    $select = $trouserArt.GetMethod('SelectTrouserTargets')
    $path = 'Things/Pawn/Humanlike/Apparel/Pants/Pants'
    function New-Pair { param([string]$Name, [string]$Worn) [System.Collections.Generic.KeyValuePair[string, string]]::new($Name, $Worn) }
    function Get-Targets {
        param($Pairs)
        $list = [System.Collections.Generic.List[System.Collections.Generic.KeyValuePair[string, string]]]::new()
        foreach ($p in $Pairs) { $list.Add($p) }
        return @($select.Invoke($null, @(, $list)))
    }

    $none = @(Get-Targets @())
    Assert-That 'with no defs at all, the two vanilla garments are still named' (($none -contains '^Apparel_Pants$') -and ($none -contains '^Apparel_KidPants$') -and $none.Count -eq 2)

    $mixed = @(Get-Targets @(
        (New-Pair 'Apparel_Pants' ''),
        (New-Pair 'Apparel_FlakPants' ''),
        (New-Pair 'Apparel_SuitPantsX' $null),
        (New-Pair 'Apparel_ModdedPants' $path),
        (New-Pair 'Apparel_OwnArtPants' 'Things/Pawn/Humanlike/Apparel/Other/Own'),
        (New-Pair 'Apparel_Jeans' ''),
        (New-Pair 'Apparel_Shirt' ''),
        (New-Pair 'Apparel_pants_lower' '')))
    Assert-That 'a modded ...Pants with no graphic of its own is left alone too'   ($mixed -contains '^Apparel_FlakPants$')
    Assert-That 'a def already on the trouser path is left alone'                  ($mixed -contains '^Apparel_ModdedPants$')
    Assert-That 'a def with art of its own is left to TailorMade'                  ($mixed -notcontains '^Apparel_OwnArtPants$')
    Assert-That 'a def without the keyword is not swept in'                        (($mixed -notcontains '^Apparel_Jeans$') -and ($mixed -notcontains '^Apparel_Shirt$'))
    Assert-That 'the keyword is matched as AB matches it: case-sensitively'       ($mixed -notcontains '^Apparel_pants_lower$')
    Assert-That 'the two vanilla garments are never listed twice'                  (@($mixed | Where-Object { $_ -eq '^Apparel_Pants$' }).Count -eq 1)
    $dots = @(Get-Targets @((New-Pair 'Apparel.Pants+X' '')))
    Assert-That 'a def name is escaped, never read as a pattern'                   ($dots -contains '^Apparel\.Pants\+X$')
}
finally {
    [System.AppDomain]::CurrentDomain.remove_AssemblyResolve($script:resolver)
}

Write-Host ""
if ($script:failures.Count -eq 0) {
    Write-Host ("$($script:checks) checks, all passed.") -ForegroundColor Green
    exit 0
}
Write-Host ("$($script:checks) checks, $($script:failures.Count) failed:") -ForegroundColor Red
$script:failures | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red }
exit 1
