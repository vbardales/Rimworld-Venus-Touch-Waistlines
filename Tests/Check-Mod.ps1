<#
.SYNOPSIS
    Checks that everything this mod reaches into TailorMade still exists, and
    still means what the code assumes.

.DESCRIPTION
    This mod is nothing but Harmony patches on another mod's internals. Every
    one of them fails the same way: silently. A renamed method is a patch that
    never applies, a moved constant is a fallback that never recognises the
    value it is meant to correct, and in both cases the game starts, logs
    nothing, and simply does not do what the settings say.

    So the test is reflection over TailorMade's own assembly:

      - the three types we patch or call are still there;
      - the methods still have the names and the shapes we patch;
      - TexBake.BakeFitted still takes its band as a `fitBand` parameter, which
        is what the fallback prefix binds to by name;
      - the stock band constants still hold the values the fallback compares
        against, since it only rewrites a band it recognises as untouched.

    Nothing here starts RimWorld. Assemblies are loaded for inspection with the
    game's Managed folder on the probe path.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Check-Mod.ps1
#>

[CmdletBinding()]
param(
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed',
    [string]$TailorMade = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3756915448\Assemblies\TailorMadeUnifiedApparelBodyRefitting.dll',
    # Reading our own [HarmonyPatch] attributes means resolving the attribute
    # type, so Harmony's own assembly has to be findable too.
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

# --- loading -----------------------------------------------------------------
# TailorMade references the game's assemblies, so the resolver has to find them
# or every type read fails on a dependency rather than on anything real.
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
    $ours = [System.Reflection.Assembly]::LoadFrom($ModAssembly)
    Write-Host ""
    Write-Host ("TailorMade  " + $tm.GetName().Version)
    Write-Host ("this mod    " + $ours.GetName().Version)

    # --- the types we reach into ---------------------------------------------
    Write-Host ""
    Write-Host "TailorMade's surface"

    $classifier = $tm.GetType('TailorMade.ApparelClassifier', $false)
    Assert-That 'type TailorMade.ApparelClassifier' ($null -ne $classifier)

    $texBake = $tm.GetType('TailorMade.TexBake', $false)
    Assert-That 'type TailorMade.TexBake' ($null -ne $texBake)

    $cache = $tm.GetType('TailorMade.TailorMadeCache', $false)
    Assert-That 'type TailorMade.TailorMadeCache' ($null -ne $cache)

    $apparelClass = $tm.GetType('TailorMade.ApparelClass', $false)
    Assert-That 'enum TailorMade.ApparelClass' ($null -ne $apparelClass)

    if ($apparelClass) {
        foreach ($name in @('Boots', 'Pants', 'Chest')) {
            Assert-That ("  ApparelClass." + $name) ([Enum]::IsDefined($apparelClass, $name))
        }
    }

    # --- what the trouser step reaches into ----------------------------------
    # TrouserArt makes TailorPatternDefs in code. A rename or a removal here would not stop
    # the game: the def would simply not be understood, and TailorMade would go on fitting
    # the trousers as if this mod were not there.
    Write-Host ""
    Write-Host "what the trouser step reaches into"

    $patternDef = $tm.GetType('TailorMade.TailorPatternDef', $false)
    Assert-That 'type TailorMade.TailorPatternDef' ($null -ne $patternDef)
    if ($patternDef) {
        Assert-That '  it is a Def' ($patternDef.BaseType.Name -eq 'Def') $patternDef.BaseType.Name
        $flags = [Reflection.BindingFlags]'Public,Instance'
        $ignore = $patternDef.GetField('ignore', $flags)
        Assert-That '  field ignore, a bool' (($null -ne $ignore) -and $ignore.FieldType -eq [bool])
        $body = $patternDef.GetField('bodyType', $flags)
        Assert-That '  field bodyType, a BodyTypeDef' (($null -ne $body) -and $body.FieldType.Name -eq 'BodyTypeDef')
        $targets = $patternDef.GetField('targetApparelDefs', $flags)
        Assert-That '  field targetApparelDefs, a list of strings' (($null -ne $targets) -and $targets.FieldType.IsGenericType -and ($targets.FieldType.GetGenericTypeDefinition().Name -eq 'List`1') -and ($targets.FieldType.GetGenericArguments()[0] -eq [string])) $(if ($targets) { $targets.FieldType.FullName })
        Assert-That '  it can be built without arguments' ($null -ne $patternDef.GetConstructor([Type[]]@()))
    }

    $registry = $tm.GetType('TailorMade.PatternRegistry', $false)
    Assert-That 'type TailorMade.PatternRegistry' ($null -ne $registry)
    if ($registry) {
        $defs = $registry.GetField('defs', [Reflection.BindingFlags]'NonPublic,Static')
        Assert-That '  a private static field defs, the list it reads once' (($null -ne $defs) -and $defs.FieldType.Name -like 'List*') $(if ($defs) { $defs.FieldType.Name })
    }

    # --- the methods we patch ------------------------------------------------
    Write-Host ""
    Write-Host "the methods we patch"

    if ($classifier) {
        $bandFor = $classifier.GetMethod('BandFor')
        Assert-That 'ApparelClassifier.BandFor exists' ($null -ne $bandFor)
        if ($bandFor) {
            Assert-That '  returns Vector2' ($bandFor.ReturnType.FullName -eq 'UnityEngine.Vector2') $bandFor.ReturnType.FullName
            $p = $bandFor.GetParameters()
            Assert-That '  takes one ApparelClass' ($p.Count -eq 1 -and $p[0].ParameterType -eq $apparelClass)
        }

        $confirm = $classifier.GetMethod('ConfirmChestArt')
        Assert-That 'ApparelClassifier.ConfirmChestArt exists' ($null -ne $confirm)
        if ($confirm) {
            Assert-That '  returns bool' ($confirm.ReturnType.FullName -eq 'System.Boolean') $confirm.ReturnType.FullName
        }
    }

    if ($texBake) {
        $bake = $texBake.GetMethod('BakeFitted')
        Assert-That 'TexBake.BakeFitted exists' ($null -ne $bake)
        if ($bake) {
            # The fallback prefix binds this parameter by name. A rename would
            # make Harmony pass nothing and the patch would quietly do nothing.
            $band = $bake.GetParameters() | Where-Object { $_.Name -eq 'fitBand' }
            Assert-That '  has a parameter named fitBand' ($null -ne $band)
            if ($band) {
                Assert-That '  and it is a Vector2' ($band.ParameterType.FullName -eq 'UnityEngine.Vector2') $band.ParameterType.FullName
            }
        }
    }

    if ($cache) {
        $clear = $cache.GetMethod('ClearAndRepaint')
        Assert-That 'TailorMadeCache.ClearAndRepaint exists' ($null -ne $clear)
    }

    # --- the constants the fallback recognises -------------------------------
    # Bands.StockPants and friends are copied into our own source. If TailorMade
    # ever retunes them, the fallback prefix stops recognising an untouched band
    # and silently stops correcting it.
    Write-Host ""
    Write-Host "the stock band values our fallback compares against"

    $expected = @{ 'BootsBand' = @(0.0, 0.2); 'PantsBand' = @(0.0, 0.58); 'ChestBand' = @(0.45, 1.0) }
    if ($classifier) {
        foreach ($name in $expected.Keys | Sort-Object) {
            $field = $classifier.GetField($name, [System.Reflection.BindingFlags]::Public -bor [System.Reflection.BindingFlags]::Static)
            if (-not $field) {
                Assert-That ("ApparelClassifier." + $name) $false 'field not found'
                continue
            }
            $value = $field.GetValue($null)
            $want = $expected[$name]
            $ok = ([Math]::Abs($value.x - $want[0]) -lt 0.0005) -and ([Math]::Abs($value.y - $want[1]) -lt 0.0005)
            Assert-That ("ApparelClassifier." + $name + " is (" + $want[0] + ", " + $want[1] + ")") $ok ("found (" + $value.x + ", " + $value.y + ")")
        }
    }

    # --- our own patches -----------------------------------------------------
    Write-Host ""
    Write-Host "our patches declare those targets"

    $harmonyAttr = 'HarmonyLib.HarmonyPatch'
    $patched = @{}
    foreach ($type in $ours.GetTypes()) {
        foreach ($attr in $type.GetCustomAttributesData()) {
            if ($attr.AttributeType.FullName -ne $harmonyAttr) { continue }
            $args = @($attr.ConstructorArguments | ForEach-Object { $_.Value })
            if ($args.Count -ge 2) { $patched[[string]$args[1]] = [string]$args[0] }
        }
    }
    foreach ($name in @('BandFor', 'BakeFitted', 'ConfirmChestArt')) {
        Assert-That ("a [HarmonyPatch] on " + $name) ($patched.ContainsKey($name)) ('found: ' + ($patched.Keys -join ', '))
    }
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
