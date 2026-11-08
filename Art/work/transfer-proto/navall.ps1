$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$uw = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\UWUnderwear\'
# Step 1 on the ten WDI bodies, south: the shirt the game draws on each (WDI's ShirtBasic for the three X_Female bodies, the
# vanilla one, 128 px scaled x4, for the other adults, Biotech's KidShirt for the two children: they cannot wear ShirtBasic)
# cut at the pink line, navel..hem resized per column onto navel..pink line. Children: the line is the fundoshi's, flat at the
# front (median of its top + 1, as the DLL does); navel read by eye at 310, the fundoshi line (296) was above it; now a flat hem under the navel, $childHem).
$childHem = 324  # Virginie: under the navel (dot rows 303-317), not on the fundoshi (296, too high)
$nav = @{ Male = 365; Thin = 360; Fat = 345; Hulk = 400; Female = 347; Thin_Female = 346; Fat_Female = 339; Hulk_Female = 394; Child = 310; FurChild = 310 }
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_shirt-to-pink-line-all-bodies.png'
$cell = 240; $bmp = New-Object System.Drawing.Bitmap (10 * $cell), (2 * $cell); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90)); $g.InterpolationMode = 'HighQualityBicubic'
$f = New-Object System.Drawing.Font 'Arial', 10
$i = 0
foreach ($tk in 'Male', 'Thin', 'Fat', 'Hulk', 'Female', 'Thin_Female', 'Fat_Female', 'Hulk_Female', 'Child', 'FurChild') {
  $body = $wdi + 'Naked_' + $tk + '_south.png'; $o = $tmp + 'wpink_' + $tk + '.png'
  if ($tk -like '*Child') { $shirt = $tmp + 'kid512_child.png'; $src = 'KidShirt'; [Nav]::SetPinkRow($childHem, 512) }
  else { [Nav]::SetPink(($uw + 'boxers\boxers_' + $tk + '_south.png'), ($uw + 'panties\panties_' + $tk + '_south.png'), 512, 512)
    if ($tk -like '*_Female') { $shirt = $tmp + 'wshirt512_' + $tk + '.png'; $src = 'WDI' } else { $shirt = $tmp + 'core512_' + $tk.ToLower() + '.png'; $src = 'vanilla' } }
  [Nav]::TAnchor = -1; [Nav]::HemPx = 4; [Nav]::TaperPx = 24
  $r = [Nav]::Run($body, $shirt, $body, $shirt, $nav[$tk], $nav[$tk], $o); "$tk : $r"
  $x0 = ($i % 5) * 2 * $cell; $y0 = [Math]::Floor($i / 5) * $cell
  $c = 0; foreach ($p in $shirt, $o) { foreach ($q in $body, $p) { $im = New-Object System.Drawing.Bitmap $q; $g.DrawImage($im, $x0 + $c * $cell, $y0, $cell, $cell); $im.Dispose() }; $c++ }
  $g.DrawString("$tk ($src) : avant | apres", $f, [System.Drawing.Brushes]::Yellow, $x0 + 6, $y0 + 4)
  $i++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
