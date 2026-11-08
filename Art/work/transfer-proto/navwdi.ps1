$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$uw = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\UWUnderwear\'
# Step 1 ISO (Virginie): the WDI shirt itself, on its own body, turned towards the trousers: unchanged above the WDI navel, the band
# navel..WDI hem resized per column onto navel..pink line (hem shape kept).
$tNav = @{ Thin_Female = 346; Fat_Female = 339; Hulk_Female = 394 }
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_wdi-shirt-to-pink-line.png'
$cell = 384; $bmp = New-Object System.Drawing.Bitmap (2 * $cell), (3 * $cell); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90)); $g.InterpolationMode = 'HighQualityBicubic'
$row = 0
foreach ($tk in 'Thin_Female', 'Fat_Female', 'Hulk_Female') { $body = $wdi + 'Naked_' + $tk + '_south.png'; $shirt = $tmp + 'wshirt512_' + $tk + '.png'; $o = $tmp + 'wpink_' + $tk + '.png'
  [Nav]::SetPink(($uw + 'boxers\boxers_' + $tk + '_south.png'), ($uw + 'panties\panties_' + $tk + '_south.png'), 512, 512); [Nav]::TAnchor = -1; [Nav]::HemPx = 4; [Nav]::TaperPx = 24
  $r = [Nav]::Run($body, $shirt, $body, $shirt, $tNav[$tk], $tNav[$tk], $o); "$tk : $r"
  $c = 0; foreach ($p in $shirt, $o) { foreach ($q in $body, $p) { $im = New-Object System.Drawing.Bitmap $q; $g.DrawImage($im, $c * $cell, $row * $cell, $cell, $cell); $im.Dispose() }; $c++ }
  $row++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
