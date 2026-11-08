Add-Type -AssemblyName System.Drawing
# Buttons of ShirtButton, vanilla vs WDI, in 512 px rows: small closed blobs of grey ink near the middle (the placket line is
# tall and thin, so it is not a blob). Prints each blob's centre row and the garment's top and bottom at the middle.
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-'
$wa = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Apparel\'
function Load($p) { $b = New-Object System.Drawing.Bitmap $p; $s = 512 / $b.Width; $n = $b.Width; $a = New-Object 'int[,]' 512, 512
  for ($y = 0; $y -lt $n; $y++) { for ($x = 0; $x -lt $n; $x++) { $c = $b.GetPixel($x, $y); $v = if ($c.A -le 40) { -1 } else { [int](($c.R + $c.G + $c.B) / 3) }
    for ($dy = 0; $dy -lt $s; $dy++) { for ($dx = 0; $dx -lt $s; $dx++) { $a[($x * $s + $dx), ($y * $s + $dy)] = $v } } } }; $b.Dispose(); return ,$a }
# Corset: per column (middle, and 40 px either side) the dark lines crossed from the top down (runs of ink < 140), as row ranges.
function Lines($a, $x) { $r = @(); $in = $false; $s = 0; for ($y = 0; $y -lt 512; $y++) { $d = $a[$x, $y] -ge 0 -and $a[$x, $y] -lt 140
  if ($d -and -not $in) { $s = $y; $in = $true } elseif (-not $d -and $in) { $r += "$s-$($y - 1)"; $in = $false } }; return ($r -join ',') }
foreach ($p in @(@('Thin_Female', 'thin'), @('Fat_Female', 'fat'), @('Hulk_Female', 'hulk'), @('Female', 'female'))) {
  $v = Load ($film + 'corsetroyal-' + $p[1] + '-south\0000.png'); "$($p[0]) vanilla mid [$(Lines $v 256)] side [$(Lines $v 216)]"
  $wp = $wa + 'CorsetRoyal\CorsetRoyal_' + $p[0] + '_south.png'; if (Test-Path $wp) { $w = Load $wp; "$($p[0]) WDI     mid [$(Lines $w 256)] side [$(Lines $w 216)]" } }
