<#
.SYNOPSIS
    Exercises the code that draws trouser details onto a plain shell,
    without starting RimWorld and without Unity.

.DESCRIPTION
    `TrouserDetail.Apply` is a pure function on RGBA bytes: no game type, no
    Unity type. That is deliberate, and it is what makes it testable here.

    What is checked is what must hold whatever the shell looks like, and it is
    stated as invariants rather than as expected images, because the shells
    are not one shape - a female or fat body gets a wide crescent, a thin one a
    small cup - and a check that compared pixels would pin the drawing rather
    than the rules:

      - the input array is never modified;
      - no pixel of the garment gets brighter, because every mark is a
        multiplication of the colour already there and the game tints these
        textures with the garment's own colour;
      - a pixel that was transparent stays exactly as it was;
      - alpha is never touched (the gap between the legs is painted black, not cut):
        at the bottom, in the middle, and never in the side view;
      - something is actually drawn, and the waistband follows the top edge of
        a crescent as well as of a bowl;
      - the result is the same every time.

    The same invariants are then run over AB's real textures, all eighteen, when
    AB's Visible Pants is installed. That is where a shape nobody thought of
    would show up. It is skipped, and says so, when they are not there.

    What is not here: how any of it looks. That is a judgement about an image,
    made from a contact sheet or from a capture, and no assertion states it.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File Tests\Check-Trousers.ps1
#>

[CmdletBinding()]
param(
    [string]$ModAssembly,
    [string]$AbPants = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2986402536\Textures\Things\Pawn\Humanlike\Apparel\Pants'
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

# The comparisons run over tens of thousands of bytes each, which PowerShell does slowly, so
# they are written in C#. It only reads arrays and builds synthetic shells; it knows nothing of
# the code under test.
Add-Type -TypeDefinition @'
using System;

public static class TmwCheck
{
    public const int Solid = 128;

    /// kind 0: a bowl with a flat top. kind 1: a crescent whose top edge dips in the middle.
    public static byte[] Shell(int w, int h, int kind)
    {
        var px = new byte[w * h * 4];
        var inside = new bool[w * h];
        int cx = w / 2;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                double dx = (x - cx) / 30.0;
                if (Math.Abs(dx) > 1) continue;
                double top, bottom;
                if (kind == 0) { top = 80; bottom = 80 + 26 * Math.Sqrt(1 - dx * dx); }
                else
                {
                    double dip = 1 - dx * dx;
                    top = 74 + 12 * dip;
                    bottom = 92 + 16 * dip;
                }
                inside[y * w + x] = y >= top && y <= bottom;
            }
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                if (!inside[y * w + x]) continue;
                bool edge = false;
                for (int d = 1; d <= 2 && !edge; d++)
                    edge = !Get(inside, w, h, x - d, y) || !Get(inside, w, h, x + d, y)
                        || !Get(inside, w, h, x, y - d) || !Get(inside, w, h, x, y + d);
                int i = (y * w + x) * 4;
                byte v = (byte)(edge ? 12 : 205);
                px[i] = v; px[i + 1] = v; px[i + 2] = v; px[i + 3] = 255;
            }
        return px;
    }

    private static bool Get(bool[] a, int w, int h, int x, int y)
    {
        return x >= 0 && x < w && y >= 0 && y < h && a[y * w + x];
    }

    /// [0] pixels of the garment that got brighter        (must be 0)
    /// [1] pixels whose alpha was raised                   (must be 0)
    /// [2] pixels of the gap: alpha lowered, or colour painted to pure black on a pixel that was not
    /// [3] pixels that were transparent and changed        (must be 0)
    /// [4] pixels of the garment that got darker
    /// [5..8] bounding box of the lowered alpha: minX, maxX, minY, maxY (-1 when none)
    public static int[] Audit(byte[] before, byte[] after, int w, int h)
    {
        var r = new int[9];
        r[5] = w; r[6] = -1; r[7] = h; r[8] = -1;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                int i = (y * w + x) * 4;
                bool wasSolid = before[i + 3] >= Solid;
                if (after[i + 3] > before[i + 3]) r[1]++;
                bool blackened = before[i + 3] >= Solid && after[i + 3] == before[i + 3]
                    && after[i] == 0 && after[i + 1] == 0 && after[i + 2] == 0
                    && (before[i] != 0 || before[i + 1] != 0 || before[i + 2] != 0);
                if (after[i + 3] < before[i + 3] || blackened)
                {
                    r[2]++;
                    if (x < r[5]) r[5] = x; if (x > r[6]) r[6] = x;
                    if (y < r[7]) r[7] = y; if (y > r[8]) r[8] = y;
                }
                if (!wasSolid)
                {
                    for (int c = 0; c < 4; c++) if (after[i + c] != before[i + c]) { r[3]++; break; }
                    continue;
                }
                if (after[i + 3] < Solid || blackened) continue;   // the gap; judged by [2]
                bool brighter = false, darker = false;
                for (int c = 0; c < 3; c++)
                {
                    if (after[i + c] > before[i + c]) brighter = true;
                    if (after[i + c] < before[i + c]) darker = true;
                }
                if (brighter) r[0]++;
                if (darker) r[4]++;
            }
        if (r[6] < 0) { r[5] = -1; r[7] = -1; }
        return r;
    }

    public static int SolidWidth(byte[] px, int w, int h)
    {
        int lo = w, hi = -1;
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
                if (px[(y * w + x) * 4 + 3] >= Solid) { if (x < lo) lo = x; if (x > hi) hi = x; }
        return hi < 0 ? 0 : hi - lo + 1;
    }

    public static int AlphaChanged(byte[] a, byte[] b)
    {
        int n = 0;
        for (int i = 3; i < a.Length; i += 4) if (a[i] != b[i]) n++;
        return n;
    }

    public static int TopRow(byte[] px, int w, int h)
    {
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
                if (px[(y * w + x) * 4 + 3] >= Solid) return y;
        return -1;
    }

    public static int BottomRow(byte[] px, int w, int h)
    {
        for (int y = h - 1; y >= 0; y--)
            for (int x = 0; x < w; x++)
                if (px[(y * w + x) * 4 + 3] >= Solid) return y;
        return -1;
    }

    public static bool Same(byte[] a, byte[] b)
    {
        if (a.Length != b.Length) return false;
        for (int i = 0; i < a.Length; i++) if (a[i] != b[i]) return false;
        return true;
    }

    /// First solid row of a column, or -1.
    public static int TopEdge(byte[] px, int w, int h, int x)
    {
        for (int y = 0; y < h; y++) if (px[(y * w + x) * 4 + 3] >= Solid) return y;
        return -1;
    }

    public static int Brightness(byte[] px, int w, int x, int y)
    {
        int i = (y * w + x) * 4;
        return px[i] + px[i + 1] + px[i + 2];
    }
}
'@

$asm = [Reflection.Assembly]::LoadFrom($ModAssembly)
$detail = $asm.GetType('TailorMadeWaistlines.TrouserDetail', $true)
$facingType = $asm.GetType('TailorMadeWaistlines.Facing', $true)
$apply = $detail.GetMethod('Apply')
$facings = @(
    @{ Name = 'south'; Value = [Enum]::ToObject($facingType, 0) },
    @{ Name = 'east';  Value = [Enum]::ToObject($facingType, 1) },
    @{ Name = 'north'; Value = [Enum]::ToObject($facingType, 2) }
)

function Invoke-Apply([byte[]]$px, [int]$w, [int]$h, $facing, [bool]$bare = $false) {
    return , $apply.Invoke($null, @($px, $w, $h, $facing, $bare))
}

function Assert-Invariants([string]$label, [byte[]]$before, [byte[]]$after, [int]$w, [int]$h, [string]$facingName, [int]$cx, [int]$shellTop, [int]$shellBottom) {
    $a = [TmwCheck]::Audit($before, $after, $w, $h)
    Assert-That "$label - nothing gets brighter"            ($a[0] -eq 0) "$($a[0]) pixels did"
    Assert-That "$label - alpha is never raised"            ($a[1] -eq 0) "$($a[1]) pixels were"
    Assert-That "$label - a transparent pixel is untouched" ($a[3] -eq 0) "$($a[3]) changed"
    Assert-That "$label - something is drawn"               ($a[4] -ge 15) "only $($a[4]) pixels darkened"

    if ($facingName -eq 'east') {
        Assert-That "$label - the side view keeps its outline whole" ($a[2] -eq 0) "$($a[2]) pixels of alpha were removed"
    } else {
        $height = $shellBottom - $shellTop + 1
        Assert-That "$label - the legs are parted" ($a[2] -ge 3) "$($a[2]) pixels of alpha were removed"
        if ($a[2] -ge 3) {
            $middle = ($a[5] -ge $cx - 12) -and ($a[6] -le $cx + 12)
            $low = $a[7] -ge ($shellBottom - [Math]::Ceiling($height * 0.45))
            Assert-That "$label - the gap is at the bottom, in the middle" ($middle -and $low) "columns $($a[5])..$($a[6]), rows $($a[7])..$($a[8])"
        }
    }
}

Write-Host "synthetic shells"
foreach ($kind in 0, 1) {
    $kindName = @('a bowl', 'a crescent')[$kind]
    $w = 128; $h = 128; $cx = 64
    foreach ($f in $facings) {
        $shell = [TmwCheck]::Shell($w, $h, $kind)
        $keep = [byte[]]$shell.Clone()
        $out = (Invoke-Apply $shell $w $h $f.Value)
        $label = "$kindName, $($f.Name)"

        Assert-That "$label - the input is left alone" ([TmwCheck]::Same($shell, $keep))
        Assert-That "$label - the result is a copy of the same size" (($out.Length -eq $shell.Length) -and -not [object]::ReferenceEquals($out, $shell))
        $top = [TmwCheck]::TopEdge($shell, $w, $h, $cx)
        Assert-Invariants $label $shell $out $w $h $f.Name $cx $top 106

        $again = (Invoke-Apply $shell $w $h $f.Value)
        Assert-That "$label - the same input gives the same result" ([TmwCheck]::Same($out, $again))
    }

    # The waistband follows the top edge. Two rows under the outline at the middle column, where a
    # crescent's edge is lowest, must be darker; a band fixed at the top of the bounding box would
    # have missed the crescent's middle entirely.
    $shell = [TmwCheck]::Shell($w, $h, $kind)
    $out = (Invoke-Apply $shell $w $h $facings[0].Value)
    $top = [TmwCheck]::TopEdge($shell, $w, $h, 64)
    $probe = $top + 3
    $was = [TmwCheck]::Brightness($shell, $w, 64, $probe)
    $now = [TmwCheck]::Brightness($out, $w, 64, $probe)
    Assert-That "$kindName - the waistband sits under the top edge of the middle column" ($now -lt $was) "row $probe was $was, is $now"

    $south = (Invoke-Apply $shell $w $h $facings[0].Value)
    $east  = (Invoke-Apply $shell $w $h $facings[1].Value)
    $north = (Invoke-Apply $shell $w $h $facings[2].Value)
    Assert-That "$kindName - the three views are drawn differently" (-not [TmwCheck]::Same($south, $east) -and -not [TmwCheck]::Same($south, $north) -and -not [TmwCheck]::Same($east, $north))
}

Write-Host ""
Write-Host "inputs that must come back untouched, or be refused"
$empty = New-Object byte[] (128 * 128 * 4)
$out = (Invoke-Apply $empty 128 128 $facings[0].Value)
Assert-That 'a texture with nothing solid in it comes back unchanged' ([TmwCheck]::Same($empty, $out))

$tiny = New-Object byte[] (6 * 4 * 4)
for ($i = 0; $i -lt 6 * 4; $i++) { $tiny[$i * 4] = 200; $tiny[$i * 4 + 1] = 200; $tiny[$i * 4 + 2] = 200; $tiny[$i * 4 + 3] = 255 }
$out = (Invoke-Apply $tiny 6 4 $facings[0].Value)
Assert-That 'a shell too small to hold the marks comes back unchanged' ([TmwCheck]::Same($tiny, $out))

$refused = $false
try { $apply.Invoke($null, @([byte[]](New-Object byte[] 10), 128, 128, $facings[0].Value, $false)) | Out-Null }
catch { $refused = ($_.Exception.InnerException -is [ArgumentException]) -and ($_.Exception.InnerException.Message -like '*must hold*') }
Assert-That 'a buffer of the wrong length is refused' $refused

$refused = $false
try { $apply.Invoke($null, @($null, 128, 128, $facings[0].Value, $false)) | Out-Null }
catch { $refused = $_.Exception.InnerException -is [ArgumentNullException] }
Assert-That 'no buffer at all is refused' $refused

Write-Host ""
Write-Host "moving the picture down"
$w = 128; $h = 128
$shell = [TmwCheck]::Shell($w, $h, 0)
$keep = [byte[]]$shell.Clone()
$shiftBase = [TmwCheck]::Audit($shell, $shell, $w, $h)

function Solid-Count([byte[]]$px) { $n = 0; for ($i = 3; $i -lt $px.Length; $i += 4) { if ($px[$i] -ge 128) { $n++ } }; return $n }
function Lowest-Solid([byte[]]$px, [int]$w, [int]$h) {
    for ($y = $h - 1; $y -ge 0; $y--) { for ($x = 0; $x -lt $w; $x++) { if ($px[($y * $w + $x) * 4 + 3] -ge 128) { return $y } } }
    return -1
}
$shift = $detail.GetMethod('ShiftDown')
$before = Lowest-Solid $shell $w $h
$moved = $shift.Invoke($null, @($shell, $w, $h, 4))
Assert-That 'the input is left alone' ([TmwCheck]::Same($shell, $keep))
Assert-That 'the garment moves down by exactly the rows asked' ((Lowest-Solid $moved $w $h) -eq ($before + 4)) "lowest solid row was $before, is $(Lowest-Solid $moved $w $h)"
Assert-That 'no pixel of the garment is lost' ((Solid-Count $moved) -eq (Solid-Count $shell))
$topRowsClear = $true
for ($i = 3; $i -lt 4 * $w * 4; $i += 4) { if ($moved[$i] -ne 0) { $topRowsClear = $false } }
Assert-That 'the rows it leaves at the top are transparent' $topRowsClear
Assert-That 'zero rows changes nothing' ([TmwCheck]::Same($shift.Invoke($null, @($shell, $w, $h, 0)), $shell))
Assert-That 'a negative shift changes nothing' ([TmwCheck]::Same($shift.Invoke($null, @($shell, $w, $h, -3)), $shell))

$room = $h - 1 - $before
$greedy = $shift.Invoke($null, @($shell, $w, $h, 500))
Assert-That 'asking for too much moves it as far as it goes, and stops' ((Lowest-Solid $greedy $w $h) -eq ($h - 1)) "lowest solid row is $(Lowest-Solid $greedy $w $h), room was $room"
Assert-That 'and still loses no pixel of the garment' ((Solid-Count $greedy) -eq (Solid-Count $shell))

$empty = New-Object byte[] ($w * $h * 4)
Assert-That 'a texture with nothing solid in it is left as it is' ([TmwCheck]::Same($shift.Invoke($null, @([byte[]]$empty, $w, $h, 6)), $empty))

$refused = $false
try { $shift.Invoke($null, @([byte[]](New-Object byte[] 10), $w, $h, 3)) | Out-Null }
catch { $refused = ($_.Exception.InnerException -is [ArgumentException]) -and ($_.Exception.InnerException.Message -like '*must hold*') }
Assert-That 'a buffer of the wrong length is refused' $refused

Write-Host ""
Write-Host "the gap is painted, not cut; a fat shell can be narrowed"
$gw = 128; $gh = 128
$gshell = [TmwCheck]::Shell($gw, $gh, 0)
$gout = (Invoke-Apply $gshell $gw $gh $facings[0].Value)
Assert-That 'painting the gap leaves every alpha as it was' ([TmwCheck]::AlphaChanged($gshell, $gout) -eq 0) "$([TmwCheck]::AlphaChanged($gshell, $gout)) alpha values changed"
$narrow = $detail.GetMethod('Narrow')
$n09 = $narrow.Invoke($null, @($gshell, $gw, $gh, [single]0.9))
$w0 = [TmwCheck]::SolidWidth($gshell, $gw, $gh); $w9 = [TmwCheck]::SolidWidth($n09, $gw, $gh)
Assert-That 'narrowing by 0.9 makes the shell narrower' ($w9 -lt $w0 -and $w9 -ge [int]($w0 * 0.85)) "$w0 -> $w9"
$n10 = $narrow.Invoke($null, @($gshell, $gw, $gh, [single]1.0))
Assert-That 'narrowing by 1 changes nothing' ([TmwCheck]::Same($gshell, $n10))

$stretch = $detail.GetMethod('StretchTop')
$st0 = [TmwCheck]::TopRow($gshell, $gw, $gh); $sb0 = [TmwCheck]::BottomRow($gshell, $gw, $gh)
$stOut = $stretch.Invoke($null, @($gshell, $gw, $gh, [int]($st0 - 12)))
Assert-That 'stretching up lands the top on the asked row' ([TmwCheck]::TopRow($stOut, $gw, $gh) -eq ($st0 - 12)) "top $([TmwCheck]::TopRow($stOut, $gw, $gh)), asked $($st0 - 12)"
Assert-That 'stretching up leaves the bottom where it was' ([TmwCheck]::BottomRow($stOut, $gw, $gh) -eq $sb0) "bottom $([TmwCheck]::BottomRow($stOut, $gw, $gh)), was $sb0"
$stDown = $stretch.Invoke($null, @($gshell, $gw, $gh, [int]($st0 + 5)))
Assert-That 'a row below the top changes nothing' ([TmwCheck]::Same($gshell, $stDown))

$bareOut = (Invoke-Apply $gshell $gw $gh $facings[0].Value $true)
$nAlphaBare = [TmwCheck]::AlphaChanged($gshell, $bareOut)
Assert-That 'shorts: the gap between the legs is left open (alpha removed), not painted' ($nAlphaBare -gt 0) "$nAlphaBare alpha values changed"
Assert-That 'trousers: the gap is painted, no alpha removed' ([TmwCheck]::AlphaChanged($gshell, $gout) -eq 0)

$jb = $detail.GetMethod('StretchBottom')
$jbot = [TmwCheck]::BottomRow($gshell, $gw, $gh); $jtop = [TmwCheck]::TopRow($gshell, $gw, $gh)
$pivot = $jtop + [int](($jbot - $jtop) / 2)
$jOut = $jb.Invoke($null, @($gshell, $gw, $gh, $pivot, [int]($jbot + 10)))
Assert-That 'a jacket stretched down lands its hem on the asked row' ([TmwCheck]::BottomRow($jOut, $gw, $gh) -eq ($jbot + 10)) "hem $([TmwCheck]::BottomRow($jOut, $gw, $gh)), asked $($jbot + 10)"
Assert-That 'stretching down leaves the top where it was' ([TmwCheck]::TopRow($jOut, $gw, $gh) -eq $jtop)
$sameAbove = $true
for ($y = 0; $y -le $pivot; $y++) { for ($x = 0; $x -lt $gw; $x++) { $i = ($y * $gw + $x) * 4; if ($jOut[$i + 3] -ne $gshell[$i + 3]) { $sameAbove = $false } } }
Assert-That 'everything above the pivot is untouched' $sameAbove
$jNo = $jb.Invoke($null, @($gshell, $gw, $gh, $pivot, [int]$jbot))
Assert-That 'a garment already reaching the row is returned as it is' ([TmwCheck]::Same($gshell, $jNo))
$jUp = $jb.Invoke($null, @($gshell, $gw, $gh, $pivot, [int]($jbot - 6)))
Assert-That 'compressing brings the hem up to the asked row' ([TmwCheck]::BottomRow($jUp, $gw, $gh) -eq ($jbot - 6)) "hem $([TmwCheck]::BottomRow($jUp, $gw, $gh))"

$cutT = $asm.GetType('TailorMadeWaistlines.ShirtCut')
$cut = $cutT.GetMethod('CutBelow')
$cOut = $cut.Invoke($null, @($gshell, $gw, $gh, [int]($jtop + 8)))
Assert-That 'a shirt cut at a row has nothing solid from that row down' ([TmwCheck]::BottomRow($cOut, $gw, $gh) -lt ($jtop + 8)) "bottom $([TmwCheck]::BottomRow($cOut, $gw, $gh))"
Assert-That 'a shirt cut at a row keeps its top' ([TmwCheck]::TopRow($cOut, $gw, $gh) -eq $jtop)
$cNo = $cut.Invoke($null, @($gshell, $gw, $gh, [int]$gh))
Assert-That 'a cut row past the picture changes nothing' ([TmwCheck]::Same($gshell, $cNo))

$cutP = $cutT.GetMethod('CutBelowProfile')
$rowsP = [int[]](New-Object int[] $gw)
for ($x = 0; $x -lt $gw; $x++) { $rowsP[$x] = $jtop + 10 + [int]([Math]::Abs($x - 64) / 8) }
$pOut = $cutP.Invoke($null, @($gshell, $gw, $gh, $rowsP))
$pOk = $true
for ($x = 0; $x -lt $gw; $x++) { for ($y = $rowsP[$x]; $y -lt $gh; $y++) { if ($pOut[($y * $gw + $x) * 4 + 3] -ne 0) { $pOk = $false } } }
Assert-That 'a shirt cut along a curve has nothing left below the curve in any column' $pOk
Assert-That 'a shirt cut along a curve keeps its top' ([TmwCheck]::TopRow($pOut, $gw, $gh) -eq $jtop)

$cutA = $detail.GetMethod('CutAbove')
$rowsA = [int[]](New-Object int[] $gw)
for ($x = 0; $x -lt $gw; $x++) { $rowsA[$x] = $gtop2 = ($jtop + 6 + [int]([Math]::Abs($x - 64) / 10)) }
$aOut = $cutA.Invoke($null, @($gshell, $gw, $gh, $rowsA))
$aOk = $true
for ($x = 0; $x -lt $gw; $x++) { for ($y = 0; $y -lt $rowsA[$x]; $y++) { if ($aOut[($y * $gw + $x) * 4 + 3] -ne 0) { $aOk = $false } } }
Assert-That 'trousers cut along a curve have nothing left above the curve in any column' $aOk
Assert-That 'trousers cut along a curve keep their bottom' ([TmwCheck]::BottomRow($aOut, $gw, $gh) -eq $jbot)

# TopFit.ClipToBody: a garment clipped to a body picture of another resolution.
$fitT = $asm.GetType('TailorMadeWaistlines.TopFit')
$clip = $fitT.GetMethod('ClipToBody', [System.Reflection.BindingFlags]'NonPublic,Static')
$tg = New-Object byte[] (8 * 8 * 4)
for ($i = 0; $i -lt 64; $i++) { $tg[$i * 4] = 200; $tg[$i * 4 + 1] = 100; $tg[$i * 4 + 2] = 50; $tg[$i * 4 + 3] = 255 }
$tb = New-Object byte[] (4 * 4 * 4)
for ($by = 1; $by -le 2; $by++) { for ($bx = 1; $bx -le 2; $bx++) { $tb[($by * 4 + $bx) * 4 + 3] = 255 } }
$tb[(0 * 4 + 0) * 4 + 3] = 39   # below the threshold: still outside
$tkeep = [byte[]]$tg.Clone()
$tc = $clip.Invoke($null, @($tg, 8, 8, $tb, 4, 4))
$tIn = 0; $tOutOk = $true; $tRgbOk = $true
for ($y = 0; $y -lt 8; $y++) { for ($x = 0; $x -lt 8; $x++) {
    $a = $tc[($y * 8 + $x) * 4 + 3]
    $inside = ($x -ge 2 -and $x -le 5 -and $y -ge 2 -and $y -le 5)
    if ($inside) { $tIn += [int]($a -eq 255) } elseif ($a -ne 0) { $tOutOk = $false }
    if ($tc[($y * 8 + $x) * 4] -ne 200 -or $tc[($y * 8 + $x) * 4 + 1] -ne 100 -or $tc[($y * 8 + $x) * 4 + 2] -ne 50) { $tRgbOk = $false }
} }
Assert-That 'a garment clipped to a body keeps exactly the pixels over the body, across resolutions' (($tIn -eq 16) -and $tOutOk) "inside kept $tIn of 16"
Assert-That 'clipping a garment leaves its colours alone' $tRgbOk
Assert-That 'clipping a garment does not change the input' ([TmwCheck]::Same($tg, $tkeep))

Write-Host ""
Write-Host "AB's real textures"
if (-not (Test-Path $AbPants)) {
    Write-Host "  skipped: AB's Visible Pants is not installed at $AbPants"
} else {
    Add-Type -AssemblyName System.Drawing
    $bodies = 'Male', 'Female', 'Thin', 'Fat', 'Hulk', 'Child'
    foreach ($body in $bodies) {
        for ($d = 0; $d -lt 3; $d++) {
            $name = "Pants_${body}_$($facings[$d].Name).png"
            $file = Join-Path $AbPants $name
            if (-not (Test-Path $file)) { Assert-That "$name exists" $false "not in $AbPants"; continue }

            $bmp = New-Object System.Drawing.Bitmap $file
            $w = $bmp.Width; $h = $bmp.Height
            $data = $bmp.LockBits((New-Object System.Drawing.Rectangle 0, 0, $w, $h), 'ReadOnly', 'Format32bppArgb')
            $raw = New-Object byte[] ($w * $h * 4)
            [Runtime.InteropServices.Marshal]::Copy($data.Scan0, $raw, 0, $raw.Length)
            $bmp.UnlockBits($data); $bmp.Dispose()
            $px = New-Object byte[] ($w * $h * 4)
            for ($i = 0; $i -lt $w * $h; $i++) {
                $px[$i * 4] = $raw[$i * 4 + 2]; $px[$i * 4 + 1] = $raw[$i * 4 + 1]; $px[$i * 4 + 2] = $raw[$i * 4]; $px[$i * 4 + 3] = $raw[$i * 4 + 3]
            }

            $keep = [byte[]]$px.Clone()
            $out = (Invoke-Apply $px $w $h $facings[$d].Value)
            $a = [TmwCheck]::Audit($px, $out, $w, $h)
            $ok = ($a[0] -eq 0) -and ($a[1] -eq 0) -and ($a[3] -eq 0) -and ($a[4] -ge 10) -and [TmwCheck]::Same($px, $keep)
            $gapOk = if ($facings[$d].Name -eq 'east') { $a[2] -eq 0 } else { $a[2] -ge 3 }
            Assert-That "$name - the invariants hold and something is drawn" ($ok -and $gapOk) "brighter=$($a[0]) raised=$($a[1]) transparentChanged=$($a[3]) darkened=$($a[4]) gap=$($a[2])"
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
