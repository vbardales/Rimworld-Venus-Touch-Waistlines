$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
# WDI navel: the dark ink on the middle columns between the waist row and the crotch, away from the outline; reported as a share of waist-to-hip and of neck-to-crotch.
$fr = @{}
foreach ($k in 'Male', 'Thin', 'Fat', 'Hulk', 'Female', 'Thin_Female', 'Fat_Female', 'Hulk_Female') {
  $p = $wdi + 'Naked_' + $k + '_south.png'; $info = ''; $v = [Lm]::Detect($p, [ref]$info)
  $neck = $v[1]; $wai = $v[13]; $hip = $v[17]; $cr = $v[21]; $mid = [int]$v[20]
  $bm = New-Object System.Drawing.Bitmap $p; $ys = @()
  for ($y = $wai - 30; $y -lt $cr - 8; $y++) { for ($x = $mid - 6; $x -le $mid + 6; $x++) { $c = $bm.GetPixel($x, $y); if ($c.A -gt 200 -and ($c.R + $c.G + $c.B) / 3 -lt 120) { $ys += $y; break } } }
  $bm.Dispose()
  if ($ys.Count -eq 0) { "{0,-12} no navel ink found (waist {1} hip {2} crotch {3})" -f $k, $wai, $hip, $cr; continue }
  $ny = ($ys | Measure-Object -Average).Average
  $a = ($ny - $wai) / [Math]::Max(1, $hip - $wai); $b = ($ny - $neck) / ($cr - $neck); $fr[$k] = @($a, $b)
  "{0,-12} navel y {1,6:0.0} (ink rows {2}-{3}); waist {4} hip {5} crotch {6}; share waist-to-hip {7:0.00}, neck-to-crotch {8:0.00}" -f $k, $ny, $ys[0], $ys[-1], $wai, $hip, $cr, $a, $b }
'--- vanilla estimate (waist + share x (hip - waist)), share taken from the WDI body of the same build'
foreach ($k in 'male', 'thin', 'fat', 'hulk', 'female') { $K = (Get-Culture).TextInfo.ToTitleCase($k)
  $info = ''; $v = [Lm]::Detect($tmp + 'vbody512_' + $k + '.png', [ref]$info); $neck = $v[1]; $wai = $v[13]; $hip = $v[17]; $cr = $v[21]
  if (-not $fr.ContainsKey($K)) { "{0,-12} no WDI share" -f $K; continue }
  $e1 = $wai + $fr[$K][0] * ($hip - $wai); $e2 = $neck + $fr[$K][1] * ($cr - $neck)
  "{0,-12} waist {1} hip {2} crotch {3}{4}{5}; navel by waist/hip {6:0.0}, by neck/crotch {7:0.0}, gap {8:0.0} px" -f $K, $wai, $hip, $cr, $(if ([Lm]::WeakWaist) { ' weakWaist' } else { '' }), $(if ([Lm]::WeakHip) { ' weakHip' } else { '' }), $e1, $e2, ($e1 - $e2) }
