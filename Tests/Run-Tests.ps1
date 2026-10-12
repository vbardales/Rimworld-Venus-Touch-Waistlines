<#
.SYNOPSIS
    Runs every test set beside it and reports which of them failed.

.DESCRIPTION
    Six sets, each answering a different question, none of them starting the
    game:

      - `Check-Mod.ps1`          - does TailorMade still look the way the
                                   patches assume? Reflection over its
                                   assembly; no code of ours is run.
      - `Check-Logic.ps1`        - given the settings, does our own code hand
                                   back the right band and shorten the right
                                   garments? Our patch bodies are invoked.
      - `Check-Settings.ps1`     - defaults, reset, and the clamping applied to
                                   a config file that has been hand-edited.
      - `Check-Trousers.ps1`     - does the code that draws trouser details
                                   onto a plain shell keep to its rules, on
                                   synthetic shells and on AB's real ones?
                                   Pure bytes; no Unity, no game.
      - `Check-WdiAppPatterns.ps1` - does the APP bridge retain ten distinct
                                   WDI targets and turn only a body's alpha
                                   channel into an in-memory clipping mask?
      - `Check-Localization.ps1` - every player-facing key resolves in English
                                   and French, and the hidden shortcut is
                                   declared as asked.

    What still needs a running colony is in `TESTING.md`, and nothing here
    replaces it.

    The sets do not all take the same parameters - `Check-Localization.ps1`
    reads the tree rather than the assemblies, and `Check-Settings.ps1` wants
    Harmony as a folder where the others want the DLL. So each one is given
    only the parameters it declares, in the shape its own default shows it
    expects.

    Exit code is 0 when all pass, 1 when a check failed, 2 when a set could
    not run at all - a missing game or Workshop path, most likely.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Run-Tests.ps1

.EXAMPLE
    # After a build, against a DLL that is not the one in Mod/Assemblies.
    powershell -ExecutionPolicy Bypass -File Tests\Run-Tests.ps1 -ModAssembly C:\tmp\TailorMadeWaistlines.dll
#>

[CmdletBinding()]
param(
    [string]$Managed,
    [string]$TailorMade,
    # The Harmony assembly. A set that wants its folder is handed the folder.
    [string]$Harmony,
    [string]$ModAssembly,
    [string]$Root
)

$sets = @(
    @{ Name = 'compatibility with TailorMade'; Script = 'Check-Mod.ps1' }
    @{ Name = 'bands and the shirt option';    Script = 'Check-Logic.ps1' }
    @{ Name = 'settings, reset and clamping';  Script = 'Check-Settings.ps1' }
    @{ Name = 'trouser details';               Script = 'Check-Trousers.ps1' }
    @{ Name = 'WDI APP patterns';              Script = 'Check-WdiAppPatterns.ps1' }
    @{ Name = 'English, French, shortcut';     Script = 'Check-Localization.ps1' }
)

$given = $PSBoundParameters
$results = @()

foreach ($set in $sets) {
    $path = Join-Path $PSScriptRoot $set.Script
    Write-Host ""
    Write-Host ("=== " + $set.Script + " - " + $set.Name) -ForegroundColor Cyan

    if (-not (Test-Path $path)) {
        Write-Host ("cannot find " + $path) -ForegroundColor Yellow
        $results += @{ Name = $set.Script; Code = 2 }
        continue
    }

    $declared = (Get-Command -Name $path -CommandType ExternalScript).Parameters
    # A Harmony default with no .dll on the end is a set that probes a folder.
    $harmonyIsFolder = $declared.ContainsKey('Harmony') -and
        -not ((Get-Content $path -Raw) -match '\[string\]\$Harmony\s*=\s*''[^'']*\.dll''')

    $forward = @{}
    foreach ($name in @('Managed', 'TailorMade', 'Harmony', 'ModAssembly', 'Root')) {
        if (-not $given.ContainsKey($name)) { continue }
        if (-not $declared.ContainsKey($name)) { continue }
        $value = $given[$name]
        if ($name -eq 'Harmony' -and $harmonyIsFolder -and $value -like '*.dll') {
            $value = Split-Path -Parent $value
        }
        $forward[$name] = $value
    }

    & $path @forward
    $results += @{ Name = $set.Script; Code = $LASTEXITCODE }
}

Write-Host ""
Write-Host "=== summary" -ForegroundColor Cyan
foreach ($r in $results) {
    $label = switch ($r.Code) { 0 { 'passed' } 2 { 'could not run' } default { 'FAILED' } }
    $colour = switch ($r.Code) { 0 { 'Green' } 2 { 'Yellow' } default { 'Red' } }
    Write-Host ("  " + $r.Name.PadRight(24) + $label) -ForegroundColor $colour
}

if ($results | Where-Object { $_.Code -eq 2 }) { exit 2 }
if ($results | Where-Object { $_.Code -ne 0 }) { exit 1 }
exit 0
