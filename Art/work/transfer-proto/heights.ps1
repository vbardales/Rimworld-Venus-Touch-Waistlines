# WDI vs vanilla 1.7 bodies, all at 512: top and bottom rows, height, and where AB's pants waistband (vanilla) falls on the WDI body. Overlay sheet: WDI body, vanilla silhouette outline in red, AB pants top in blue.
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points\'
Add-Type -AssemblyName System.Drawing
function Load512($p) { $s = New-Object System.Drawing.Bitmap $p; if ($s.Width -eq 512) { return $s }; $d = New-Object System.Drawing.Bitmap 512, 512; $g = [System.Drawing.Graphics]::FromImage($d); $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $g.DrawImage($s, 0, 0, 512, 512); $g.Dispose(); $s.Dispose(); $d }
function Mask($b) { $r = New-Object 'bool[,]' 512, 512; for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { $r[$x, $y] = $b.GetPixel($x, $y).A -gt 40 } }; , $r }
function Rows($a) { $t = -1; $bt = -1; for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { if ($a[$x, $y]) { if ($t -lt 0) { $t = $y }; $bt = $y; break } } }; @($t, $bt) }
$pairs = @(@('Male','Male'),@('Thin','Thin'),@('Fat','Fat'),@('Hulk','Hulk'),@('Female','Female'),@('Thin_Female','Thin'),@('Fat_Female','Fat'),@('Hulk_Female','Hulk'))
foreach ($f in 'south','east','north') {
  $cw = 300; $sh = New-Object System.Drawing.Bitmap ($cw * $pairs.Count), 340; $g = [System.Drawing.Graphics]::FromImage($sh); $g.Clear([System.Drawing.Color]::FromArgb(200,196,182))
  $font = New-Object System.Drawing.Font 'Arial', 9, ([System.Drawing.FontStyle]::Bold); $i = 0
  foreach ($p in $pairs) {
    $wb = Load512 ($wdi + "Naked_$($p[0])_$f.png"); $vb = Load512 ($tmp + "core17_512\Naked_$($p[1])_$f.png")
    $wm = Mask $wb; $vm = Mask $vb; $wr = Rows $wm; $vr = Rows $vm; $wh = $wr[1] - $wr[0]; $vh = $vr[1] - $vr[0]
    $pm = Mask (Load512 ($tmp + "pants512_AB_$($p[1])_$f.png")); $pt = (Rows $pm)[0]
    "{0,-6} WDI {1,-12} top {2,3} bottom {3,3} height {4,3} | vanilla {5,-7} top {6,3} bottom {7,3} height {8,3} | WDI/vanilla {9:0.00}, top {10:+0;-0;0}, bottom {11:+0;-0;0} | AB waistband row {12} = {13:0}% of vanilla, {14:0}% of WDI" -f $f, $p[0], $wr[0], $wr[1], $wh, $p[1], $vr[0], $vr[1], $vh, ($wh / $vh), ($wr[0] - $vr[0]), ($wr[1] - $vr[1]), $pt, (100.0 * ($pt - $vr[0]) / $vh), (100.0 * ($pt - $wr[0]) / $wh)
    # crop rows 90..508 to 340 px tall, columns 56..456
    $dst = New-Object System.Drawing.Rectangle ($i * $cw), 0, $cw, 340; $src = New-Object System.Drawing.Rectangle 56, 90, 400, 453
    $g.DrawImage($wb, $dst, $src, 'Pixel')
    $sx = $cw / 400.0; $sy = 340 / 453.0
    for ($y = 1; $y -lt 511; $y++) { for ($x = 1; $x -lt 511; $x++) { if ($vm[$x, $y] -and (-not $vm[($x-1), $y] -or -not $vm[($x+1), $y] -or -not $vm[$x, ($y-1)] -or -not $vm[$x, ($y+1)])) { $g.FillRectangle([System.Drawing.Brushes]::Red, [float]($i * $cw + ($x - 56) * $sx), [float](($y - 90) * $sy), 1.5, 1.5) } } }
    $g.DrawLine((New-Object System.Drawing.Pen ([System.Drawing.Color]::Blue), 1.5), [float]($i * $cw), [float](($pt - 90) * $sy), [float]($i * $cw + $cw), [float](($pt - 90) * $sy))
    $g.DrawString("WDI $($p[0]) / van. $($p[1])", $font, [System.Drawing.Brushes]::Black, ($i * $cw + 4), 4)
    $wb.Dispose(); $vb.Dispose(); $i++ }
  $g.Dispose(); $sh.Save($out + "heights-$f.png", [System.Drawing.Imaging.ImageFormat]::Png); $sh.Dispose() }
