<#
.SYNOPSIS
    Checks the pure, publishable boundary of Venus' first APP slice.

.DESCRIPTION
    APP receives a texture mask. Venus must not ship a tracing of WDI's body
    textures, so it turns the installed body's alpha channel into a white mask
    in memory.  These checks prove that transparent pixels stay transparent,
    solid pixels stay at their original alpha, a top retains its own hem while
    pants start at their waistline, and each of the ten WDI visual profiles
    has distinct APP paths and the intended gender predicate.

    This is not a game-render proof: APP's RenderTexture pipeline and its
    Harmony ordering still require the dedicated Pickle scenario.
#>

[CmdletBinding()]
param(
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed',
    [string]$App = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2480887589\1.6\Assemblies\ApparelPaperPattern.dll',
    [string]$Utilities = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2839443438\1.6\Assemblies\APPUtilities.dll',
    [string]$WdiRoot = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510',
    [string]$ModAssembly
)

$ErrorActionPreference = 'Stop'
if (-not $ModAssembly) { $ModAssembly = Join-Path (Split-Path -Parent $PSScriptRoot) 'Mod\Assemblies\TailorMadeWaistlines.dll' }
$script:checks = 0
$script:failures = @()

function Assert-That {
    param([string]$What, [bool]$Ok, [string]$Detail)
    $script:checks++
    if ($Ok) { Write-Host ('  ok    ' + $What) }
    else {
        $script:failures += $What + $(if ($Detail) { ' - ' + $Detail } else { '' })
        Write-Host ('  FAIL  ' + $What + $(if ($Detail) { ' - ' + $Detail } else { '' }))
    }
}

foreach ($path in @($Managed, $App, $Utilities, $ModAssembly)) {
    if (-not (Test-Path -LiteralPath $path)) { Write-Host ('cannot find ' + $path) -ForegroundColor Red; exit 2 }
}

$probeDirs = @($Managed, (Split-Path -Parent $App), (Split-Path -Parent $Utilities), (Split-Path -Parent $ModAssembly)) | Select-Object -Unique
$script:resolver = [System.ResolveEventHandler] {
    param($sender, $e)
    $name = (New-Object System.Reflection.AssemblyName($e.Name)).Name
    foreach ($dir in $probeDirs) {
        $candidate = Join-Path $dir ($name + '.dll')
        if (Test-Path -LiteralPath $candidate) { return [System.Reflection.Assembly]::LoadFrom($candidate) }
    }
    return $null
}
[AppDomain]::CurrentDomain.add_AssemblyResolve($script:resolver)

try {
    [System.Reflection.Assembly]::LoadFrom($App) | Out-Null
    [System.Reflection.Assembly]::LoadFrom($Utilities) | Out-Null
    $ours = [System.Reflection.Assembly]::LoadFrom($ModAssembly)
    $flags = [System.Reflection.BindingFlags]'NonPublic,Public,Static'
    $bridge = $ours.GetType('TailorMadeWaistlines.WdiAppPatterns', $true)
    $profiles = $ours.GetType('TailorMadeWaistlines.WdiVisualProfiles', $true)

    Write-Host ''
    $enabled = $bridge.GetProperty('ExperimentalPatternsEnabled', $flags)
    Assert-That 'the unvalidated APP category prototype is safety-disabled by default' (-not $enabled.GetValue($null))
    $settingsType = $ours.GetType('TailorMadeWaistlines.TailorMadeWaistlinesSettings', $true)
    $settingsHost = $ours.GetType('TailorMadeWaistlines.TailorMadeWaistlinesMod', $true)
    $settingsField = $settingsHost.GetField('Settings', $flags)
    $seededSettings = [Activator]::CreateInstance($settingsType)
    $settingsType.GetField('enableExperimentalAppPatterns').SetValue($seededSettings, $true)
    $settingsField.SetValue($null, $seededSettings)
    Assert-That 'the explicit experimental setting enables the APP category prototype' $enabled.GetValue($null)
    $settingsField.SetValue($null, $null)

    $seed = Join-Path (Split-Path -Parent $PSScriptRoot) 'Tests\Pickle\config\app-wdi\Mod_VenusTouchWaistlines_TailorMadeWaistlinesMod.xml'
    Assert-That 'the APP Pickle pass has an explicit experimental-settings seed' (Test-Path -LiteralPath $seed) $seed
    if (Test-Path -LiteralPath $seed) {
        [xml]$seedXml = Get-Content -LiteralPath $seed
        Assert-That 'the APP Pickle seed opts into the category prototype' ($seedXml.SettingsBlock.ModSettings.enableExperimentalAppPatterns -eq 'True')
    }
    $abSeed = Join-Path (Split-Path -Parent $PSScriptRoot) 'Tests\Pickle\config\app-wdi\Mod_2986402536_ABsVisiblePantsMod.xml'
    Assert-That 'the APP Pickle pass seeds AB worn-graphic categories' (Test-Path -LiteralPath $abSeed) $abSeed
    if (Test-Path -LiteralPath $abSeed) {
        [xml]$abSeedXml = Get-Content -LiteralPath $abSeed
        $normalPants = @($abSeedXml.SettingsBlock.ModSettings.datas.li | Where-Object { $_.category -eq 'Normal_Pants' })
        Assert-That 'the AB seed gives Apparel_Pants its Pants texture path' (($normalPants.Count -eq 1) -and ($normalPants[0].path -eq 'Things/Pawn/Humanlike/Apparel/Pants/Pants'))
    }

    Write-Host ''
    Write-Host 'APP keeps WDI visual targets distinct'
    $all = $profiles.GetField('All', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    $categoryType = $ours.GetType('TailorMadeWaistlines.WdiApparelCategory', $true)
    $top = [Enum]::Parse($categoryType, 'Top')
    $pants = [Enum]::Parse($categoryType, 'Pants')
    $maskPath = $bridge.GetMethod('MaskPath', $flags)
    $paths = @(
        foreach ($profile in $all) {
            foreach ($category in @($top, $pants)) {
                $maskPath.Invoke($null, [object[]]@($profile.psobject.BaseObject, $category))
            }
        }
    )
    Assert-That 'all ten profiles receive a top and pants APP mask path' ($paths.Count -eq 20)
    Assert-That 'no two WDI profile/category pairs share an APP mask path' (($paths | Select-Object -Unique).Count -eq 20)
    Assert-That 'mask paths are Venus-owned runtime paths' (($paths | Where-Object { $_ -notmatch '^Venus/APP/WDI/.+/(Top|Pants)/mask$' }).Count -eq 0)
    $targetDefs = $bridge.GetMethod('TargetDefs', $flags)
    $topTargets = @($targetDefs.Invoke($null, [object[]]@($top)))
    $pantsTargets = @($targetDefs.Invoke($null, [object[]]@($pants)))
    Assert-That 'the top pattern can match only the two vanilla shirt defs' (($topTargets -join ',') -eq '^Apparel_(BasicShirt|KidShirt)$')
    Assert-That 'the pants pattern can match only the two vanilla pants defs' (($pantsTargets -join ',') -eq '^Apparel_(Pants|KidPants)$')
    $names = [Enum]::GetNames($categoryType)
    Assert-That 'only Top and Pants register a pattern: APP keeps the last match, so a second category on the same defs replaces the real one (2026-10-12, undyed shirts and pants vanished)' (($names -join ',') -eq 'Top,Pants')

    $genderFor = $bridge.GetMethod('GenderFor', $flags)
    $femaleFat = $profiles.GetField('FemaleFat', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    $maleFat = $profiles.GetField('MaleFat', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    $girl = $profiles.GetField('KidGirl', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    $boy = $profiles.GetField('KidBoy', [System.Reflection.BindingFlags]'Public,Static').GetValue($null)
    Assert-That "Female_Fat selects APP's female predicate" ($genderFor.Invoke($null, [object[]]@($femaleFat.psobject.BaseObject)).ToString() -eq 'Female')
    Assert-That "Male_Fat selects APP's male predicate" ($genderFor.Invoke($null, [object[]]@($maleFat.psobject.BaseObject)).ToString() -eq 'Male')
    Assert-That 'Kid_Girl and Kid_Boy stay separate semantic targets' (($genderFor.Invoke($null, [object[]]@($girl.psobject.BaseObject)).ToString() -eq 'Female') -and ($genderFor.Invoke($null, [object[]]@($boy.psobject.BaseObject)).ToString() -eq 'Male'))
    $badGender = @(
        foreach ($profile in $all) {
            $expected = if ($profile.Id -like 'Female*' -or $profile.Id -eq 'Kid_Girl') { 'Female' } else { 'Male' }
            if ($genderFor.Invoke($null, [object[]]@($profile.psobject.BaseObject)).ToString() -ne $expected) { $profile.Id }
        }
    )
    Assert-That 'every WDI target has the right APP gender predicate' ($badGender.Count -eq 0) ($badGender -join ', ')

    Write-Host ''
    Write-Host 'the WDI alpha becomes a mask, not copied colour art'
    $alphaMask = $bridge.GetMethod('AlphaMask', $flags)
    $reliefMask = $bridge.GetMethod('ReliefMask', $flags)
    [byte[]]$source = New-Object byte[] 108
    for ($pixel = 0; $pixel -lt 27; $pixel++) {
        $offset = $pixel * 4
        $source[$offset] = [byte](12 + $pixel)
        $source[$offset + 1] = [byte](34 + $pixel)
        $source[$offset + 2] = [byte](56 + $pixel)
        $source[$offset + 3] = 255
    }
    $source[3] = 0
    $source[7] = 127
    [int[]]$cutRows = @(1)
    [byte[]]$topMask = $alphaMask.Invoke($null, [object[]]@($source, 1, 27, $cutRows, $false))
    [byte[]]$pantsMask = $alphaMask.Invoke($null, [object[]]@($source, 1, 27, $cutRows, $true))
    Assert-That 'the source buffer is unchanged' (($source[0] -eq 12) -and ($source[7] -eq 127) -and ($source[11] -eq 255) -and ($source[107] -eq 255))
    Assert-That 'transparent input stays fully transparent' (($topMask[0] -eq 0) -and ($topMask[1] -eq 0) -and ($topMask[2] -eq 0) -and ($topMask[3] -eq 0))
    Assert-That 'top keeps its full silhouette so its own graphic sets the hem' (($topMask[4] -eq 255) -and ($topMask[7] -eq 127) -and ($topMask[103] -eq 255))
    Assert-That 'pants retain only pixels from the waistline down' (($pantsMask[3] -eq 0) -and ($pantsMask[7] -eq 127) -and ($pantsMask[11] -eq 255) -and ($pantsMask[15] -eq 255))
    Assert-That 'both masks keep the body alpha where they overlap' (($topMask[7] -eq 127) -and ($pantsMask[7] -eq 127))
    [byte[]]$reliefSource = @(255,255,255,255, 0,0,0,255, 100,100,100,128, 255,255,255,0)
    [byte[]]$relief = $reliefMask.Invoke($null, [object[]]@($reliefSource, 4, 1))
    Assert-That 'the relief burn leaves bright body pixels transparent' ($relief[3] -eq 0)
    Assert-That 'the relief burn turns dark body details into subtle white burn input' (($relief[4] -eq 255) -and ($relief[5] -eq 255) -and ($relief[6] -eq 255) -and ($relief[7] -eq 63))
    Assert-That 'the relief burn preserves source alpha in its shading strength' ($relief[11] -eq 19)
    Assert-That 'the relief burn keeps transparent body pixels transparent' ($relief[15] -eq 0)

    Write-Host ''
    Write-Host 'the installed WDI body sources cover every runtime profile'
    Add-Type -AssemblyName System.Drawing
    foreach ($profile in $all) {
        foreach ($facing in @('south', 'east', 'north')) {
            $path = Join-Path $WdiRoot ('Textures\Things\Pawn\Humanlike\Bodies\Naked_' + $profile.TextureKey + '_' + $facing + '.png')
            $exists = Test-Path -LiteralPath $path
            Assert-That ($profile.Id + ' has a ' + $facing + ' naked source') $exists $path
            if (-not $exists) { continue }
            $bitmap = [System.Drawing.Bitmap]::new($path)
            try {
                Assert-That ($profile.Id + ' ' + $facing + ' source is a 512 px body texture') (($bitmap.Width -eq 512) -and ($bitmap.Height -eq 512)) ("$($bitmap.Width)x$($bitmap.Height)")
            }
            finally {
                $bitmap.Dispose()
            }
        }
    }
}
finally {
    [AppDomain]::CurrentDomain.remove_AssemblyResolve($script:resolver)
}

Write-Host ''
if ($script:failures.Count -eq 0) {
    Write-Host ("$($script:checks) checks, all passed.") -ForegroundColor Green
    exit 0
}
Write-Host ("$($script:checks) checks, $($script:failures.Count) failed:") -ForegroundColor Red
$script:failures | ForEach-Object { Write-Host ('  - ' + $_) -ForegroundColor Red }
exit 1
