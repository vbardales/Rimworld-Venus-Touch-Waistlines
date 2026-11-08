Add-Type -AssemblyName System.Drawing
# Vanilla to WDI on garments with a shape (Virginie, 2026-11-03: navel and chest, see how WDI stretches a drawn shape).
# Per row (WDI body): for ShirtButton then CorsetRoyal, the vanilla garment on its vanilla body | the same vanilla texture as the
# game draws it on the WDI body | WDI's own version on the WDI body (blank when WDI has none). Vanilla 128 px scaled x4, nearest.
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_shaped-tops-vanilla-vs-wdi.png'
$rows = @(@('Thin_Female', 'thin'), @('Fat_Female', 'fat'), @('Hulk_Female', 'hulk'), @('Female', 'female'))
$cell = 300; $bmp = New-Object System.Drawing.Bitmap (6 * $cell), (4 * $cell + 24); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90))
$g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $f = New-Object System.Drawing.Font 'Arial', 10
$heads = 'ShirtButton vanilla', 'vanilla sur WDI', 'ShirtButton WDI', 'CorsetRoyal vanilla', 'vanilla sur WDI', 'CorsetRoyal WDI'
for ($c = 0; $c -lt 6; $c++) { $g.DrawString($heads[$c], $f, [System.Drawing.Brushes]::Yellow, $c * $cell + 6, 4) }
function Draw($p, $x, $y) { if (-not (Test-Path $p)) { return }; $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $x, $y, $cell, $cell); $im.Dispose() }
$r = 0
foreach ($row in $rows) { $tk = $row[0]; $k = $row[1]; $y0 = 24 + $r * $cell; $wBody = $wb + 'Bodies\Naked_' + $tk + '_south.png'
  $c = 0
  foreach ($gar in 'ShirtButton', 'CorsetRoyal') { $v = $film + $gar.ToLower() + '-' + $k + '-south\0000.png'
    Draw ($tmp + 'vbody512_' + $k + '.png') ($c * $cell) $y0; Draw $v ($c * $cell) $y0; $c++
    Draw $wBody ($c * $cell) $y0; Draw $v ($c * $cell) $y0; $c++
    $wg = $wb + 'Apparel\' + $gar + '\' + $gar + '_' + $tk + '_south.png'; if (Test-Path $wg) { Draw $wBody ($c * $cell) $y0; Draw $wg ($c * $cell) $y0 }; $c++ }
  $g.DrawString($tk, $f, [System.Drawing.Brushes]::White, 6, $y0 + 4); $r++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
