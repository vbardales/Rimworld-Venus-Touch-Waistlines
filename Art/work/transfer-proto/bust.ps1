Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
# Bust row = mean row of the pink nipple pixels; under-breast row = first dark ink row below the nipple at its column, after leaving the nipple.
function Bust($tk) { $bm = New-Object System.Drawing.Bitmap ($wdi + 'Naked_' + $tk + '_south.png'); $ys = @(); $xs = @()
  for ($y = 100; $y -lt 420; $y++) { for ($x = 100; $x -lt 256; $x++) { $c = $bm.GetPixel($x, $y); if ($c.A -gt 200 -and $c.R -gt 200 -and $c.R - $c.B -gt 15 -and $c.G -lt 235) { $ys += $y; $xs += $x } } }
  $ny = [int](($ys | Measure-Object -Average).Average); $nx = [int](($xs | Measure-Object -Average).Average)
  $u = -1; $y = $ny; while ($y -lt 500 -and ($bm.GetPixel($nx, $y).R -gt 200 -or $bm.GetPixel($nx, $y).R - $bm.GetPixel($nx, $y).B -gt 15)) { $y++ }
  for (; $y -lt 500; $y++) { $c = $bm.GetPixel($nx, $y); if ($c.A -gt 200 -and ($c.R + $c.G + $c.B) / 3 -lt 90) { $u = $y; break } }
  $bm.Dispose(); return @($ny, $u, $nx) }
foreach ($tk in 'Thin_Female', 'Fat_Female', 'Hulk_Female') { $b = Bust $tk; "$tk nipple row $($b[0]) (x $($b[2])), under-breast row $($b[1])" }
