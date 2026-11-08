# Per mod/body/facing: pants top and bottom as % of the vanilla body height (0 = body top), pants pixels outside the body silhouette, and whether AB and XND are the same pixels.
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
Add-Type -AssemblyName System.Drawing
function Alpha($p) { $b = New-Object System.Drawing.Bitmap $p; $r = New-Object 'bool[,]' 512, 512; for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { $r[$x, $y] = $b.GetPixel($x, $y).A -gt 40 } }; $b.Dispose(); , $r }
function Rows($a) { $t = -1; $bt = -1; for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { if ($a[$x, $y]) { if ($t -lt 0) { $t = $y }; $bt = $y; break } } }; @($t, $bt) }
foreach ($f in 'south', 'east', 'north') { foreach ($b in 'Male', 'Thin', 'Fat', 'Hulk', 'Female') {
  $ba = Alpha ($tmp + "core17_512\Naked_${b}_$f.png"); $br = Rows $ba; $H = $br[1] - $br[0]
  $line = "$f $b body rows $($br[0])-$($br[1])"
  foreach ($m in 'AB', 'XND', 'catMonke') { $pa = Alpha ($tmp + "pants512_${m}_${b}_$f.png"); $pr = Rows $pa; $out = 0; $n = 0
    for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { if ($pa[$x, $y]) { $n++; if (-not $ba[$x, $y]) { $out++ } } } }
    $line += " | $m top {0:0}% bottom {1:0}% outside {2} px" -f (100.0 * ($pr[0] - $br[0]) / $H), (100.0 * ($pr[1] - $br[0]) / $H), $out }
  $h1 = (Get-FileHash ($tmp + "pants512_AB_${b}_$f.png")).Hash; $h2 = (Get-FileHash ($tmp + "pants512_XND_${b}_$f.png")).Hash
  $line + $(if ($h1 -eq $h2) { ' | AB=XND' } else { ' | AB<>XND' }) } }
