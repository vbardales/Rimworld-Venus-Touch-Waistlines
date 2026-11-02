<#
.SYNOPSIS
    The parts of the localization check that no shared script does: the slider labels that
    receive a value carry {0}, no hard-coded sentence is left in the settings code, and the hidden
    MainButtons shortcut is declared the way MOD_SETTINGS.md asks.
    Cut 2026-11-02 (LOCAL-SCRIPTS-CUT): key coverage, unused keys, duplicates, empty texts, placeholder parity and
    identical French texts are scripts\Check-Translations.ps1 (run it with -RejectIdentical).

.DESCRIPTION
    Nothing here starts RimWorld. The checks read the source and the shipped XML:

      - every "TailorMadeWaistlines.*" key the source translates exists in
        Languages/English/Keyed and Languages/French/Keyed, non-empty;
      - neither language holds a key the source never uses, or a duplicate;
      - both languages carry the same {0} placeholders, and the slider labels
        that receive a value do carry {0};
      - no sentence-like string literal is left in the settings code outside
        the keys (the mod's own name, "Venus Touch Waistlines", is a proper
        noun and is the one allowed exception);
      - the MainButtonDef exists, is hidden by default (buttonVisible false),
        names a worker class that exists in the shipped assembly, and every
        French DefInjected key resolves to a field of that def.

    The DefInjected path check itself is scripts\Check-DefInjected.ps1, run
    beside this one.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Check-Localization.ps1
#>

[CmdletBinding()]
param(
    [string]$Root,
    # The game's assemblies, so the worker class's base type resolves when the assembly is inspected.
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed'
)

$ErrorActionPreference = 'Stop'
if (-not $Root) { $Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) }
$script:failures = @()
$script:checks = 0

function Assert-That {
    param([string]$What, [bool]$Ok, [string]$Detail)
    $script:checks++
    if ($Ok) { Write-Host ("  ok    " + $What) }
    else {
        $script:failures += $What + $(if ($Detail) { " - " + $Detail } else { "" })
        Write-Host ("  FAIL  " + $What + $(if ($Detail) { " - " + $Detail } else { "" }))
    }
}

function Read-Keyed {
    param([string]$Path)
    $keys = [ordered]@{}
    $dupes = @()
    [xml]$xml = Get-Content -Raw -Encoding UTF8 $Path
    foreach ($node in $xml.LanguageData.ChildNodes) {
        if ($node.NodeType -ne 'Element') { continue }
        if ($keys.Contains($node.Name)) { $dupes += $node.Name }
        $keys[$node.Name] = $node.InnerText
    }
    return @{ Keys = $keys; Dupes = $dupes }
}

$mod = Join-Path $Root 'Mod'
$src = Join-Path $Root 'Source\TailorMadeWaistlines'

$en = Read-Keyed (Join-Path $mod 'Languages\English\Keyed\TailorMadeWaistlines.xml')
$fr = Read-Keyed (Join-Path $mod 'Languages\French\Keyed\TailorMadeWaistlines.xml')

foreach ($key in @('PantsTop', 'BootsTop', 'ChestBottom')) {
    $full = "TailorMadeWaistlines.Settings.$key"
    Assert-That ("$full receives the slider value ({0})") ($en.Keys[$full] -match '\{0\}' -and $fr.Keys[$full] -match '\{0\}')
}

# --- no sentence left in code -------------------------------------------------
Write-Host ""
Write-Host "no hardcoded sentence in the settings code"
$allowed = @('Venus Touch Waistlines')
foreach ($name in @('TailorMadeWaistlinesMod.cs', 'MainButtonWorker_TailorMadeWaistlines.cs')) {
    $text = Get-Content -Raw -Encoding UTF8 (Join-Path $src $name)
    $text = [regex]::Replace($text, '(?m)^\s*//.*$', '')
    $text = [regex]::Replace($text, '/\*[\s\S]*?\*/', '')
    $sentences = @([regex]::Matches($text, '"([^"\\]*)"') | ForEach-Object { $_.Groups[1].Value } |
        Where-Object { $_ -match '\s' -and $allowed -notcontains $_ })
    Assert-That ("$name holds no string literal that reads as text") ($sentences.Count -eq 0) ($sentences -join ' | ')
}

# --- the hidden shortcut ------------------------------------------------------
Write-Host ""
Write-Host "the MainButtons shortcut"
$defPath = Join-Path $mod 'Defs\MainButtonDefs\MainButtons.xml'
Assert-That 'the MainButtonDef file exists' (Test-Path $defPath)
if (Test-Path $defPath) {
    [xml]$defs = Get-Content -Raw -Encoding UTF8 $defPath
    $def = $defs.Defs.MainButtonDef
    Assert-That 'one MainButtonDef is declared' (@($def).Count -eq 1)
    Assert-That '  it is hidden by default (buttonVisible false)' ($def.buttonVisible -eq 'false')
    Assert-That '  it is valid without a map' ($def.validWithoutMap -eq 'true')
    $resolver = [System.ResolveEventHandler] {
        param($sender, $e)
        $n = (New-Object System.Reflection.AssemblyName($e.Name)).Name
        foreach ($dir in @($Managed, (Join-Path $mod 'Assemblies'))) {
            $c = Join-Path $dir ($n + '.dll')
            if (Test-Path $c) { return [System.Reflection.Assembly]::LoadFrom($c) }
        }
        return $null
    }
    [System.AppDomain]::CurrentDomain.add_AssemblyResolve($resolver)
    $asm = [System.Reflection.Assembly]::LoadFrom((Join-Path $mod 'Assemblies\TailorMadeWaistlines.dll'))
    $worker = $asm.GetType($def.workerClass, $false)
    Assert-That ('  its worker class exists in the assembly: ' + $def.workerClass) ($null -ne $worker)
    [System.AppDomain]::CurrentDomain.remove_AssemblyResolve($resolver)

    $inj = Join-Path $mod 'Languages\French\DefInjected\MainButtonDef\MainButtons.xml'
    Assert-That 'the French DefInjected file exists' (Test-Path $inj)
    if (Test-Path $inj) {
        [xml]$fx = Get-Content -Raw -Encoding UTF8 $inj
        foreach ($node in $fx.LanguageData.ChildNodes) {
            if ($node.NodeType -ne 'Element') { continue }
            $parts = $node.Name.Split('.', 2)
            $ok = ($parts[0] -eq $def.defName) -and ($parts[1] -in @('label', 'description')) -and -not [string]::IsNullOrWhiteSpace($node.InnerText)
            Assert-That ("French key " + $node.Name + " targets the def") $ok
        }
    }
}

Write-Host ""
if ($script:failures.Count -eq 0) {
    Write-Host ("$($script:checks) checks, all passed.") -ForegroundColor Green
    exit 0
}
Write-Host ("$($script:checks) checks, $($script:failures.Count) failed:") -ForegroundColor Red
$script:failures | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red }
exit 1
