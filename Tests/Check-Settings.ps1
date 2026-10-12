<#
.SYNOPSIS
    Exercises the settings object of this mod without starting RimWorld: defaults,
    reset, and the clamping applied to values read back from a config file.

.DESCRIPTION
    A hand-edited or damaged config file must never hand TailorMade a band outside
    the body. `TailorMadeWaistlinesSettings.Sanitize` is what runs after a load;
    it is a plain method, reached here by reflection on the shipped DLL with the
    game's Managed folder on the probe path.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Check-Settings.ps1
#>

[CmdletBinding()]
param(
    [string]$Managed = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\RimWorldWin64_Data\Managed',
    [string]$Harmony = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2009463077\Current\Assemblies',
    [string]$ModAssembly
)

$ErrorActionPreference = 'Stop'
if (-not $ModAssembly) {
    $ModAssembly = Join-Path (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)) 'Mod\Assemblies\TailorMadeWaistlines.dll'
}
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

$probeDirs = @($Managed, $Harmony, (Split-Path -Parent $ModAssembly))
$resolver = [System.ResolveEventHandler] {
    param($sender, $e)
    $n = (New-Object System.Reflection.AssemblyName($e.Name)).Name
    foreach ($dir in $probeDirs) {
        $c = Join-Path $dir ($n + '.dll')
        if (Test-Path $c) { return [System.Reflection.Assembly]::LoadFrom($c) }
    }
    return $null
}
[System.AppDomain]::CurrentDomain.add_AssemblyResolve($resolver)

try {
    $asm = [System.Reflection.Assembly]::LoadFrom($ModAssembly)
    $type = $asm.GetType('TailorMadeWaistlines.TailorMadeWaistlinesSettings', $true)

    function New-Settings { [Activator]::CreateInstance($type) }
    function Get-F($o, $n) { $type.GetField($n).GetValue($o) }
    function Set-F($o, $n, $v) { $type.GetField($n).SetValue($o, $v) }
    function Near([double]$a, [double]$b) { [Math]::Abs($a - $b) -lt 0.0005 }

    Write-Host ""
    Write-Host "defaults"
    $s = New-Settings
    Assert-That 'pantsTop starts at TailorMade''s 0.58' (Near (Get-F $s 'pantsTop') 0.58)
    Assert-That 'bootsTop starts at TailorMade''s 0.20' (Near (Get-F $s 'bootsTop') 0.20)
    Assert-That 'chestBottom starts at this mod''s 0.25' (Near (Get-F $s 'chestBottom') 0.25)
      Assert-That 'shortenShirts starts off' ((Get-F $s 'shortenShirts') -eq $false)
      Assert-That 'experimental APP patterns start off' ((Get-F $s 'enableExperimentalAppPatterns') -eq $false)
    Assert-That 'useGeneralArt starts on: it only acts where AB is active' ((Get-F $s 'useGeneralArt') -eq $true)
    Assert-That 'detailPlainShells starts on' ((Get-F $s 'detailPlainShells') -eq $true)
    Assert-That 'trouserDrop starts at 0.03' (Near (Get-F $s 'trouserDrop') 0.03)
    Assert-That 'trouserDropChild starts at 0.067, more than an adult because a child is drawn smaller' (Near (Get-F $s 'trouserDropChild') 0.067)

    Write-Host ""
    Write-Host "Sanitize: what a damaged config file can hold"
    $cases = @(
        @{ n = 'pantsTop';    v = 5.0;                      want = 0.90; why = 'above the slider' },
        @{ n = 'pantsTop';    v = -3.0;                     want = 0.20; why = 'below the slider' },
        @{ n = 'pantsTop';    v = [float]::NaN;             want = 0.58; why = 'NaN falls back to the default' },
        @{ n = 'pantsTop';    v = [float]::PositiveInfinity; want = 0.58; why = 'infinity falls back to the default' },
        @{ n = 'bootsTop';    v = 2.0;                      want = 0.60; why = 'above the slider' },
        @{ n = 'bootsTop';    v = 0.0;                      want = 0.05; why = 'below the slider' },
        @{ n = 'bootsTop';    v = [float]::NaN;             want = 0.20; why = 'NaN falls back to the default' },
        @{ n = 'chestBottom'; v = 1.0;                      want = 0.80; why = 'above the slider' },
        @{ n = 'chestBottom'; v = 0.0;                      want = 0.20; why = 'below the slider' },
        @{ n = 'chestBottom'; v = [float]::NegativeInfinity; want = 0.25; why = 'infinity falls back to the default' },
        @{ n = 'pantsTop';    v = 0.42;                     want = 0.42; why = 'a value inside the range is left alone' },
        @{ n = 'trouserDrop'; v = 0.5;                      want = 0.30; why = 'above the slider' },
        @{ n = 'trouserDrop'; v = -1.0;                     want = 0.0;  why = 'below the slider' },
        @{ n = 'trouserDrop'; v = [float]::NaN;             want = 0.03; why = 'NaN falls back to the default' },
        @{ n = 'trouserDropChild'; v = 9.0;                 want = 0.30; why = 'above the slider' },
        @{ n = 'trouserDropChild'; v = -2.0;                want = 0.0;  why = 'below the slider' },
        @{ n = 'trouserDropChild'; v = [float]::NaN;        want = 0.067; why = 'NaN falls back to the default' },
        @{ n = 'trouserDrop'; v = 0.05;                     want = 0.05; why = 'a value inside the range is left alone' }
    )
    foreach ($c in $cases) {
        $s = New-Settings
        Set-F $s $c.n ([float]$c.v)
        $type.GetMethod('Sanitize').Invoke($s, @()) | Out-Null
        $got = Get-F $s $c.n
        Assert-That ("{0} = {1}: {2} -> {3}" -f $c.n, $c.v, $c.why, $c.want) (Near $got $c.want) "got $got"
    }

    Write-Host ""
    Write-Host "ResetToDefaults"
    $s = New-Settings
      Set-F $s 'pantsTop' ([float]0.3); Set-F $s 'bootsTop' ([float]0.5); Set-F $s 'chestBottom' ([float]0.7); Set-F $s 'shortenShirts' $true
      Set-F $s 'enableExperimentalAppPatterns' $true
    Set-F $s 'useGeneralArt' $false; Set-F $s 'detailPlainShells' $false; Set-F $s 'trouserDrop' ([float]0.07); Set-F $s 'trouserDropChild' ([float]0.03)
    $type.GetMethod('ResetToDefaults').Invoke($s, @()) | Out-Null
    Assert-That 'the three bands return to their defaults' ((Near (Get-F $s 'pantsTop') 0.58) -and (Near (Get-F $s 'bootsTop') 0.20) -and (Near (Get-F $s 'chestBottom') 0.25))
      Assert-That 'the shirt option returns to off' ((Get-F $s 'shortenShirts') -eq $false)
      Assert-That 'experimental APP patterns return to off' ((Get-F $s 'enableExperimentalAppPatterns') -eq $false)
    Assert-That 'both trouser art options return to on' (((Get-F $s 'useGeneralArt') -eq $true) -and ((Get-F $s 'detailPlainShells') -eq $true))
    Assert-That 'both trouser drops return to their defaults' ((Near (Get-F $s 'trouserDrop') 0.03) -and (Near (Get-F $s 'trouserDropChild') 0.067))
}
finally {
    [System.AppDomain]::CurrentDomain.remove_AssemblyResolve($resolver)
}

Write-Host ""
if ($script:failures.Count -eq 0) {
    Write-Host ("$($script:checks) checks, all passed.") -ForegroundColor Green
    exit 0
}
Write-Host ("$($script:checks) checks, $($script:failures.Count) failed:") -ForegroundColor Red
$script:failures | ForEach-Object { Write-Host ("  - " + $_) -ForegroundColor Red }
exit 1
