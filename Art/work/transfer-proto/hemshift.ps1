# Hem shift table, one per body type and facing (Virginie 2026-11-05): C = WDI pink line - vanilla naked body bottom, per column
# (sign flipped 2026-11-05 on her word: the hem must follow the panties line, high at the back and low at the front in the side view;
# the first version, vanilla bottom - pink, bent it the other way; copy hemshift.before-flip.ps1),
# minus its value at the centre (no offset: only the column to column shift), smoothed. The vanilla shirt bottom (rows below the
# vanilla trousers waistband) is moved down by C in each column. Constant between WDI and vanilla: computed once, then read.
param([string]$Body = 'Male', [string]$Facing = 'south', [int]$Smooth = 8, [int]$SlopeFit = 12, [switch]$NoExtend)
# Pink line for the subtraction only (Virginie 2026-11-05: 'au lieu de remonter ou redescendre sur les bords, prolonger'): past the
# end of the underwear sprites the pink line used to stay flat at its last value; it now goes on with its own slope, fitted on the
# last SlopeFit columns before each end. The cut of the shirt and the DLL keep the plain pink line. -NoExtend: the flat ends.
# Vanilla has one Thin, Fat and Hulk body for both sexes: WDI's Thin_Female, Fat_Female and Hulk_Female are drawn over the vanilla
# Thin, Fat and Hulk (2026-11-06). Female keeps its own vanilla body.
$VanillaBody = if ($Body -ne 'Female' -and $Body.EndsWith('_Female')) { $Body.Substring(0, $Body.Length - 7) } else { $Body }
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$vbp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_' + $(if ($Facing -eq 'south') { $VanillaBody.ToLower() } else { $VanillaBody + '_' + $Facing }) + '.png'
[Nav]::SetPink(($wb + 'UWUnderwear/boxers/boxers_' + $Body + '_' + $Facing + '.png'), ($wb + 'UWUnderwear/panties/panties_' + $Body + '_' + $Facing + '.png'), 512, 512); $pink = [double[]][Nav]::Pink
if (-not $NoExtend) {
  $a = 0; while ($a -lt 511 -and $pink[$a + 1] -eq $pink[0]) { $a++ }; $b = 511; while ($b -gt 0 -and $pink[$b - 1] -eq $pink[511]) { $b-- }
  # least-squares slope over the SlopeFit columns just inside each flat end
  function Slope($x0, $x1) { $n = 0; $sx = 0; $sy = 0; $sxx = 0; $sxy = 0; for ($x = $x0; $x -le $x1; $x++) { $n++; $sx += $x; $sy += $pink[$x]; $sxx += $x * $x; $sxy += $x * $pink[$x] }; ($n * $sxy - $sx * $sy) / ($n * $sxx - $sx * $sx) }
  # hook at an end (Virginie 2026-11-05, side view: 'ce n'est pas prolongé'): near its end the top line can turn back along the
  # sprite's side edge (Female east, back: up to a peak at 186, then down to 179). The end is the turning point itself: in the
  # HookWin columns at each end, the extremum of the line in its own direction (the highest row when it rises towards that end,
  # the lowest when it falls); the slope is then fitted just inside it, from the turning point, so the extension has no kink
  # (first fix, 2026-11-05: the end was the first column where the local slope turned, 179, and the fit took in the hook: kink).
  $HookWin = 40
  if ($a -gt 0 -and $a + $HookWin -lt $b) { $sin = Slope ($a + $HookWin - $SlopeFit) ($a + $HookWin); $t = $a
    for ($x = $a; $x -le $a + $HookWin; $x++) { if (($sin -gt 0 -and $pink[$x] -lt $pink[$t]) -or ($sin -lt 0 -and $pink[$x] -gt $pink[$t])) { $t = $x } }; $a = $t }
  if ($b -lt 511 -and $b - $HookWin -gt $a) { $sin = Slope ($b - $HookWin) ($b - $HookWin + $SlopeFit); $t = $b
    for ($x = $b; $x -ge $b - $HookWin; $x--) { if (($sin -gt 0 -and $pink[$x] -gt $pink[$t]) -or ($sin -lt 0 -and $pink[$x] -lt $pink[$t])) { $t = $x } }; $b = $t }
  if ($a -gt 0 -and $a + $SlopeFit -lt $b) { $k = Slope $a ($a + $SlopeFit); for ($x = 0; $x -lt $a; $x++) { $pink[$x] = $pink[$a] + $k * ($x - $a) } }
  if ($b -lt 511 -and $b - $SlopeFit -gt $a) { $k = Slope ($b - $SlopeFit) $b; for ($x = $b + 1; $x -lt 512; $x++) { $pink[$x] = $pink[$b] + $k * ($x - $b) } }
  $script:PinkEnds = "pink ends $a..$b" }
# the pink line used for the subtraction, for the boards
(($pink | ForEach-Object { $_.ToString("0.##", [cultureinfo]::InvariantCulture) }) -join ";") | Set-Content ($d + "hemshift_" + $Body + "_" + $Facing + ".pink.txt")
$src = New-Object System.Drawing.Bitmap $vbp; $vb = New-Object System.Drawing.Bitmap 512, 512; $gg = [System.Drawing.Graphics]::FromImage($vb); $gg.InterpolationMode = 'NearestNeighbor'; $gg.PixelOffsetMode = 'Half'; $gg.DrawImage($src, 0, 0, 512, 512); $gg.Dispose(); $src.Dispose()
$raw = New-Object double[] 512; $ok = New-Object bool[] 512
for ($x = 0; $x -lt 512; $x++) { for ($y = 511; $y -ge 0; $y--) { if ($vb.GetPixel($x, $y).A -ge 25) { if ($y -gt $pink[$x]) { $raw[$x] = $y - $pink[$x]; $ok[$x] = $true }; break } } }
$vb.Dispose()
# valid span: the run of columns around the centre where the vanilla bottom is below the pink line; outside it, hold the end value
$st = 256; if (-not $ok[$st]) { for ($q = 0; $q -lt 512; $q++) { if ($ok[$q]) { $st = $q; break } } }; $lo = $st; while ($lo -gt 0 -and $ok[$lo - 1]) { $lo-- }; $hi = $st; while ($hi -lt 511 -and $ok[$hi + 1]) { $hi++ }
for ($x = 0; $x -lt $lo; $x++) { $raw[$x] = $raw[$lo] }; for ($x = $hi + 1; $x -lt 512; $x++) { $raw[$x] = $raw[$hi] }
$c = New-Object double[] 512; for ($x = 0; $x -lt 512; $x++) { $s = 0; $n = 0; for ($j = -$Smooth; $j -le $Smooth; $j++) { $q = [Math]::Max(0, [Math]::Min(511, $x + $j)); $s += $raw[$q]; $n++ }; $c[$x] = $s / $n }
$cx = [int](($lo + $hi) / 2); $c0 = $c[$cx]; $out = $d + 'hemshift_' + $Body + '_' + $Facing + '.txt'
(($c | ForEach-Object { ($c0 - $_).ToString('0.##', [cultureinfo]::InvariantCulture) }) -join ';') | Set-Content $out
"$out  $script:PinkEnds  span $lo..$hi centre $cx  " + (($lo, ($lo + 16), ($lo + 32), $cx, ($hi - 32), ($hi - 16), $hi) | ForEach-Object { "$_=" + [Math]::Round($c0 - $c[$_], 1) }) -join ' '

