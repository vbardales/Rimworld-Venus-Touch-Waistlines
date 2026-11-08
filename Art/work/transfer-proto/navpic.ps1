Add-Type -AssemblyName System.Drawing
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_navel-transfer-anchors.png'
# columns: Core shirt untouched on the WDI body | WDI shirt | whole height (v2) | from the bust | from under the breasts; rows Thin, Fat, Hulk Female
# marks on the WDI body: magenta = bust, cyan = under the breasts, yellow = navel (only on the columns that use them)
$an = @{ thin = @(264, 287, 346); fat = @(278, 321, 339); hulk = @(299, 330, 394) }
$cell = 384; $sc = $cell / 512.0; $bmp = New-Object System.Drawing.Bitmap (5 * $cell), (3 * $cell + 24)
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90)); $g.InterpolationMode = 'HighQualityBicubic'
$f = New-Object System.Drawing.Font 'Arial', 11
$names = 'Core brut', 'chemise WDI', 'toute hauteur', 'du buste', 'sous les seins'
for ($c = 0; $c -lt 5; $c++) { $g.DrawString(($c + 1).ToString() + '. ' + $names[$c], $f, [System.Drawing.Brushes]::Yellow, $c * $cell + 6, 4) }
$row = 0
foreach ($k in 'thin', 'fat', 'hulk') { $tk = (Get-Culture).TextInfo.ToTitleCase($k) + '_Female'; $body = $wdi + 'Naked_' + $tk + '_south.png'
  $cols = @(($tmp + 'core512_' + $k + '.png'), ($tmp + 'wshirt512_' + $tk + '.png'), ($tmp + 'nav_none_' + $tk + '.png'), ($tmp + 'nav_bust_' + $tk + '.png'), ($tmp + 'nav_under_' + $tk + '.png'))
  for ($c = 0; $c -lt 5; $c++) { $x0 = $c * $cell; $y0 = 24 + $row * $cell
    foreach ($p in @($body, $cols[$c])) { $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $x0, $y0, $cell, $cell); $im.Dispose() }
    $marks = @(); if ($c -ge 2) { $marks += ,@($an[$k][2], [System.Drawing.Color]::Yellow) }; if ($c -eq 3) { $marks += ,@($an[$k][0], [System.Drawing.Color]::Magenta) }; if ($c -eq 4) { $marks += ,@($an[$k][1], [System.Drawing.Color]::Cyan) }
    foreach ($m in $marks) { $pen = New-Object System.Drawing.Pen $m[1], 2; $yy = $y0 + $m[0] * $sc; $g.DrawLine($pen, $x0 + 40, $yy, $x0 + $cell - 40, $yy); $pen.Dispose() } }
  $row++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
