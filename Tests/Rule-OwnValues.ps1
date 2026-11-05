<#
.SYNOPSIS
    The values and facts of this mod's own content that no shared script states: the slider labels
    that receive a value carry {0}, no hard-coded sentence is left in the settings code, and the
    hidden MainButtons shortcut is declared the way MOD_SETTINGS.md asks.

.DESCRIPTION
    One consumer, so nothing here is shareable; Tests/Test-Mod.ps1 (generated) runs it after the
    shared checks. Nothing here starts RimWorld. Checks, each a numbered line (lib/TestRunner.ps1):

      - the English and French texts, through the shared Check-Translations with this mod's
        values (identical French refused, except the settings button label, which is the mod's
        name), and the French DefInjected paths through the shared Check-DefInjected;
      - the slider labels that receive a value carry {0} in both languages;
      - no sentence-like string literal (a space and a letter) is left in the settings code outside
        the keys (the mod's own name, "Venus Touch Waistlines", is a proper noun and is the one
        allowed exception; spacing and brackets around a def label hold no letter to translate);
      - the MainButtonDef exists, is hidden by default (buttonVisible false), is valid without a
        map, and names a worker class that exists in the shipped assembly.

    Cut 2026-11-02 and 2026-11-05 (LOCAL-SCRIPTS-CUT, LOCAL-SCRIPTS-REVIEW-2026-11-04): key
    coverage, unused keys, duplicates, empty texts, placeholder parity and the DefInjected paths
    are the shared scripts named above. The worker class stays here: Check-XmlClasses needs type
    lists dumped from the game, which this mod does not keep.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Rule-OwnValues.ps1
#>

[CmdletBinding()]
param(
    # Given by Tests/Test-Mod.ps1 (generated); by hand both default to this checkout and the protocols' scripts/.
    [string]$ModRoot,
    [string]$SharedDir,
    # The game's assemblies, so the worker class's base type resolves when the assembly is inspected.
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed'
)

$ErrorActionPreference = 'Stop'
if (-not $ModRoot) { $ModRoot = Split-Path -Parent $PSScriptRoot }
$ModRoot = (Resolve-Path -LiteralPath $ModRoot).Path
if (-not $SharedDir) { $SharedDir = Join-Path $ModRoot '..\scripts' }
# Shared runner (lib/TestRunner.ps1): one numbered line per check, the detail of a failure under it, Complete-Tests exits 1 on any.
. (Join-Path $SharedDir 'lib\TestRunner.ps1')

$mod = Join-Path $ModRoot 'Mod'
$src = Join-Path $ModRoot 'Source\TailorMadeWaistlines'

# A shared script as one check: its exit code decides, the tail of its output is the detail of a failure.
function Invoke-Shared([string]$Script, [string[]]$Arguments) {
    $out = @(& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $SharedDir $Script) @Arguments 2>&1 | ForEach-Object { "$_" })
    if ($LASTEXITCODE -ne 0) { $out | Where-Object { $_ -match '\S' } | Select-Object -Last 15 }
}

It 'English and French texts: coverage, duplicates, placeholders, no identical French but the mod name (Check-Translations)' {
    Invoke-Shared 'Check-Translations.ps1' '-ModRoot', $ModRoot, '-RejectIdentical', '-AllowIdentical', 'MainButtonDef/TailorMadeWaistlines_Settings.label'
}
It 'every French DefInjected path resolves to a field (Check-DefInjected)' {
    Invoke-Shared 'Check-DefInjected.ps1' '-TransMod', $mod, '-Managed', $Managed
}

function Read-Keyed([string]$Path) {
    $keys = @{}
    [xml]$xml = Read-Text $Path
    foreach ($node in $xml.LanguageData.ChildNodes) { if ($node.NodeType -eq 'Element') { $keys[$node.Name] = $node.InnerText } }
    return $keys
}
$en = Read-Keyed (Join-Path $mod 'Languages\English\Keyed\TailorMadeWaistlines.xml')
$fr = Read-Keyed (Join-Path $mod 'Languages\French\Keyed\TailorMadeWaistlines.xml')

It 'the three slider labels receive their value ({0}) in English and French' {
    foreach ($key in 'PantsTop', 'BootsTop', 'ChestBottom') {
        $full = "TailorMadeWaistlines.Settings.$key"
        if ($en[$full] -notmatch '\{0\}') { "$full (English) has no {0}" }
        if ($fr[$full] -notmatch '\{0\}') { "$full (French) has no {0}" }
    }
}

It 'no string literal that reads as text in the settings code' {
    $allowed = @('Venus Touch Waistlines')
    foreach ($name in 'TailorMadeWaistlinesMod.cs', 'MainButtonWorker_TailorMadeWaistlines.cs') {
        $text = Read-Text (Join-Path $src $name)
        $text = [regex]::Replace($text, '(?m)^\s*//.*$', '')
        $text = [regex]::Replace($text, '/\*[\s\S]*?\*/', '')
        [regex]::Matches($text, '"([^"\\]*)"') | ForEach-Object { $_.Groups[1].Value } |
            Where-Object { $_ -match '\s' -and $_ -match '\p{L}' -and $allowed -notcontains $_ } | ForEach-Object { "${name}: ""$_""" }
    }
}

It 'the MainButtons shortcut: one def, hidden by default, valid without a map, worker class in the assembly' {
    $defPath = Join-Path $mod 'Defs\MainButtonDefs\MainButtons.xml'
    if (-not (Test-Path -LiteralPath $defPath)) { return 'Defs\MainButtonDefs\MainButtons.xml is missing' }
    [xml]$defs = Read-Text $defPath
    $def = @($defs.Defs.MainButtonDef)
    if ($def.Count -ne 1) { return "$($def.Count) MainButtonDef declared, 1 expected" }
    $def = $def[0]
    if ($def.buttonVisible -ne 'false') { 'buttonVisible is not false' }
    if ($def.validWithoutMap -ne 'true') { 'validWithoutMap is not true' }
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
    try {
        $asm = [System.Reflection.Assembly]::LoadFrom((Join-Path $mod 'Assemblies\TailorMadeWaistlines.dll'))
        if ($null -eq $asm.GetType($def.workerClass, $false)) { "worker class $($def.workerClass) not in the assembly" }
    }
    finally { [System.AppDomain]::CurrentDomain.remove_AssemblyResolve($resolver) }
}

Complete-Tests
