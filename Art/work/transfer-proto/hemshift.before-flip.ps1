# Hem shift table, one per body type and facing (Virginie 2026-11-05): C = vanilla naked body bottom - WDI pink line, per column,
# minus its value at the centre (no offset: only the column to column shift), smoothed. The vanilla shirt bottom (rows below the
# vanilla trousers waistband) is moved down by C in each column. Constant between WDI and vanilla: computed once, then read.
param([string]$Body = 'Male', [string]$Facing = 'south', [int]$Smooth = 8)
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$vbp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_' + $(if ($Facing -eq 'south') { $Body.ToLower() } else { $Body + '_' + $Facing }) + '.png'
[Nav]::SetPink(($wb + 'UWUnderwear/boxers/boxers_' + $Body + '_' + $Facing + '.png'), ($wb + 'UWUnderwear/panties/panties_' + $Body + '_' + $Facing + '.png'), 512, 512); $pink = [Nav]::Pink
$src = New-Object System.Drawing.Bitmap $vbp; $vb = New-Object System.Drawing.Bitmap 512, 512; $gg = [System.Drawing.Graphics]::FromImage($vb); $gg.InterpolationMode = 'NearestNeighbor'; $gg.PixelOffsetMode = 'Half'; $gg.DrawImage($src, 0, 0, 512, 512); $gg.Dispose(); $src.Dispose()
$raw = New-Object double[] 512; $ok = New-Object bool[] 512
for ($x = 0; $x -lt 512; $x++) { for ($y = 511; $y -ge 0; $y--) { if ($vb.GetPixel($x, $y).A -ge 25) { if ($y -gt $pink[$x]) { $raw[$x] = $y - $pink[$x]; $ok[$x] = $true }; break } } }
$vb.Dispose()
# valid span: the run of columns around the centre where the vanilla bottom is below the pink line; outside it, hold the end value
$st = 256; if (-not $ok[$st]) { for ($q = 0; $q -lt 512; $q++) { if ($ok[$q]) { $st = $q; break } } }; $lo = $st; while ($lo -gt 0 -and $ok[$lo - 1]) { $lo-- }; $hi = $st; while ($hi -lt 511 -and $ok[$hi + 1]) { $hi++ }
for ($x = 0; $x -lt $lo; $x++) { $raw[$x] = $raw[$lo] }; for ($x = $hi + 1; $x -lt 512; $x++) { $raw[$x] = $raw[$hi] }
$c = New-Object double[] 512; for ($x = 0; $x -lt 512; $x++) { $s = 0; $n = 0; for ($j = -$Smooth; $j -le $Smooth; $j++) { $q = [Math]::Max(0, [Math]::Min(511, $x + $j)); $s += $raw[$q]; $n++ }; $c[$x] = $s / $n }
$cx = [int](($lo + $hi) / 2); $c0 = $c[$cx]; $out = $d + 'hemshift_' + $Body + '_' + $Facing + '.txt'
(($c | ForEach-Object { ($_ - $c0).ToString('0.##', [cultureinfo]::InvariantCulture) }) -join ';') | Set-Content $out
"$out  span $lo..$hi centre $cx  " + (($lo, ($lo + 16), ($lo + 32), $cx, ($hi - 32), ($hi - 16), $hi) | ForEach-Object { "$_=" + [Math]::Round($c[$_] - $c0, 1) }) -join ' '

