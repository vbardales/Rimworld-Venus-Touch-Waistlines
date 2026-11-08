# Vanilla to WDI, TailorMade's method (TexBake.BakeFitted, decompiled 2026-11-05) with Virginie's bands instead of its single
# vertical scale. Male, ShirtButton south, 512 px.
# - rows: piecewise-linear WDI row -> vanilla row through the band edges (collar, pecs, under the pecs, the vanilla trousers
#   waistband onto the WDI blue line, the shirt tail under it);
# - columns, per row: the BODY edges (not the garment's), averaged over 3 rows, vanilla body at the source row and WDI body at
#   the target row, one linear map across the row;
# - bilinear sample, alpha times the WDI body alpha, then TailorMade's outline: every pixel with alpha >= 0.1 within 4 px
#   (2 px at 256, square neighbourhood) of a transparent pixel becomes 15/15/18 and keeps its alpha;
# - split: the body of the shirt is cut on the pink line (hem drawn by the same outline), the tail below it is kept apart and
#   goes under the trousers (tucked) or over them (untucked), a per-garment setting later.
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition (Get-Content ($d + 'tmfit.cs.txt') -Raw)
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-shirtbutton-'
$vb = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\215bed336962f00b\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-05_shirtbutton-tailormade-bands-male-r6.png'
# band edges, vanilla rows -> WDI rows (Male, 512): top, collar | pecs, pecs | under the pecs, waistband -> blue line, hem (tail x0.65)
$v = @(172, 247, 323, 372, 431); $w = @(184, 242, 317, 372, 410)  # waistband on the pink line (372; blue 365): the visible shirt ends there, the tail starts there
$tk = 'Male'; $body = $wb + 'Things\Pawn\Humanlike\Bodies\Naked_' + $tk + '_south.png'; $gar = $film + 'male-south\0000.png'
[Nav]::SetPink(($wb + 'UWUnderwear/boxers/boxers_' + $tk + '_south.png'), ($wb + 'UWUnderwear/panties/panties_' + $tk + '_south.png'), 512, 512); [TmFit]::TailPink = [Nav]::Pink; [TmFit]::TailLen = 38
$hs = $d + 'hemshift_' + $tk + '_south.txt'; if (-not (Test-Path $hs)) { powershell.exe -NoProfile -ExecutionPolicy Bypass -File ($d + 'hemshift.ps1') -Body $tk -Facing south | Out-Null }
[TmFit]::Shift = [double[]]((Get-Content $hs) -split ';' | ForEach-Object { [double]::Parse($_, [cultureinfo]::InvariantCulture) })
$full = [TmFit]::Bake($gar, ($vb + 'male.png'), $body, $v, $w)
[TmFit]::Save($full, 4, ($tmp + 'tm_full.png')); # tucked (option a, Virginie 2026-11-05): outline first, then cut, so the cut gets no line: the trousers waistband is the hem
[TmFit]::Save([TmFit]::Cut([TmFit]::Px($tmp + "tm_full.png"), [Nav]::Pink, $false), 0, ($tmp + "tm_main.png"))
# board: vanilla on its body | tucked (body, tail, trousers, shirt body) | untucked (body, trousers, whole shirt) | v4 for reference.
# The trousers are stood in for by WDI's boxers sprite (top edge = the line the trousers start on).
$boxers = $wb + 'UWUnderwear\boxers\boxers_' + $tk + '_south.png'
$cols = @(@(($vb + 'male.png'), $gar), @($body, ($tmp + 'tm_full.png'), $boxers, ($tmp + 'tm_main.png')), @($body, $boxers, ($tmp + 'tm_full.png')),
  @($body, 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\c3b_Male.png'))
$heads = 'vanilla', 'rentree (pan sous)', 'sortie (pan dessus)', 'v4 (avant)'
$cell = 400; $bmp = New-Object System.Drawing.Bitmap (4 * $cell), ($cell + 20); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90))
$g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $f = New-Object System.Drawing.Font 'Arial', 10
for ($c = 0; $c -lt 4; $c++) { foreach ($p in $cols[$c]) { $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $c * $cell, 20, $cell, $cell); $im.Dispose() }
  $g.DrawString($heads[$c], $f, [System.Drawing.Brushes]::Yellow, $c * $cell + 6, 2) }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out




