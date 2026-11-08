Add-Type -AssemblyName System.Drawing
# Buttons of ShirtButton, vanilla vs WDI, in 512 px rows: small closed blobs of grey ink near the middle (the placket line is
# tall and thin, so it is not a blob). Prints each blob's centre row and the garment's top and bottom at the middle.
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-'
$wa = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Apparel\'
function Load($p) { $b = New-Object System.Drawing.Bitmap $p; $s = 512 / $b.Width; $n = $b.Width; $a = New-Object 'int[,]' 512, 512
  for ($y = 0; $y -lt $n; $y++) { for ($x = 0; $x -lt $n; $x++) { $c = $b.GetPixel($x, $y); $v = if ($c.A -le 40) { -1 } else { [int](($c.R + $c.G + $c.B) / 3) }
    for ($dy = 0; $dy -lt $s; $dy++) { for ($dx = 0; $dx -lt $s; $dx++) { $a[($x * $s + $dx), ($y * $s + $dy)] = $v } } } }; $b.Dispose(); return ,$a }
function Blobs($a, $lum) { $seen = New-Object 'bool[,]' 512, 512; $res = @()
  for ($y = 0; $y -lt 512; $y++) { for ($x = 196; $x -lt 316; $x++) { if ($seen[$x, $y] -or $a[$x, $y] -lt 0 -or $a[$x, $y] -ge $lum) { continue }
    $q = New-Object System.Collections.Generic.Queue[int]; $q.Enqueue($y * 512 + $x); $seen[$x, $y] = $true; $x0 = $x; $x1 = $x; $y0 = $y; $y1 = $y; $n = 0
    while ($q.Count) { $i = $q.Dequeue(); $px = $i % 512; $py = [Math]::Floor($i / 512); $n++; if ($px -lt $x0) { $x0 = $px }; if ($px -gt $x1) { $x1 = $px }; if ($py -lt $y0) { $y0 = $py }; if ($py -gt $y1) { $y1 = $py }
      foreach ($d in @(@(1, 0), @(-1, 0), @(0, 1), @(0, -1))) { $nx = $px + $d[0]; $ny = $py + $d[1]; if ($nx -lt 196 -or $nx -ge 316 -or $ny -lt 0 -or $ny -ge 512) { continue }
        if (-not $seen[$nx, $ny] -and $a[$nx, $ny] -ge 0 -and $a[$nx, $ny] -lt $lum) { $seen[$nx, $ny] = $true; $q.Enqueue($ny * 512 + $nx) } } }
    $w = $x1 - $x0 + 1; $h = $y1 - $y0 + 1; if ($w -ge 6 -and $w -le 24 -and $h -ge 6 -and $h -le 24) { $res += "($([int](($x0 + $x1) / 2)),$([int](($y0 + $y1) / 2)) ${w}x$h)" } } }; return $res }
function Span($a) { $t = -1; $b = -1; for ($y = 0; $y -lt 512; $y++) { if ($a[256, $y] -ge 0) { if ($t -lt 0) { $t = $y }; $b = $y } }; "top $t bottom $b" }
foreach ($p in @(@('Thin_Female', 'thin'), @('Fat_Female', 'fat'), @('Hulk_Female', 'hulk'), @('Female', 'female'))) {
  $v = Load ($film + 'shirtbutton-' + $p[1] + '-south\0000.png'); "$($p[0]) vanilla($($p[1])) $(Span $v): $((Blobs $v 200) -join ' ')"
  $wp = $wa + 'ShirtButton\ShirtButton_' + $p[0] + '_south.png'; if (Test-Path $wp) { $w = Load $wp; "$($p[0]) WDI $(Span $w): $((Blobs $w 200) -join ' ')" } }
