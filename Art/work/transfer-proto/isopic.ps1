Add-Type -AssemblyName System.Drawing
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_iso-wdi-core-vs-wdi-vs-mine.png'
$cell = 256; $bmp = New-Object System.Drawing.Bitmap (3 * $cell), (3 * $cell + 0)
$g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90))
$g.InterpolationMode = 'HighQualityBicubic'
$row = 0
foreach ($k in 'thin', 'fat', 'hulk') { $tk = (Get-Culture).TextInfo.ToTitleCase($k) + '_Female'
  $cols = @(@(($tmp + 'vbody512_' + $k + '.png'), ($tmp + 'core512_' + $k + '.png')), @(($wdi + 'Naked_' + $tk + '_south.png'), ($tmp + 'wshirt512_' + $tk + '.png')), @(($wdi + 'Naked_' + $tk + '_south.png'), ($tmp + 's16wdi_' + $tk + '.png')))
  for ($c = 0; $c -lt 3; $c++) { foreach ($p in $cols[$c]) { $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $c * $cell, $row * $cell, $cell, $cell); $im.Dispose() } }
  $row++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
