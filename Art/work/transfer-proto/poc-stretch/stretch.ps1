# POC 2026-11-06: stretch a vanilla top garment onto the WDI body. Steps: 1 vanilla art, 2 cut out (outline peeled), 3 warp onto E
# with the hem on D, 4 TailorMade edge 4 px. Offline only. Usage: stretch.ps1 -Body Male -Facing south [-Shirt ShirtButton] [-Hem pink|bottom|<row>]
param([string]$Body = 'Male', [string]$Facing = 'south', [string]$Shirt = 'ShirtButton', [string]$Hem = 'table', [int]$SmoothRows = 8, [int]$BlendRows = 24, [double]$CollarScale = 0, [string]$Tag = '', [string]$Variant = '', [switch]$OwnHem)
$ErrorActionPreference = 'Stop'
$here = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
$poc = $here + 'poc-stretch\'
$caps = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\'
$ws = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$core = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17\'
$van = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\vanilla\'
Add-Type -AssemblyName System.Drawing, PresentationCore, WindowsBase, System.Xaml
Add-Type -ReferencedAssemblies System.Drawing, PresentationCore, WindowsBase, System.Xaml, System.Core -TypeDefinition (Get-Content ($poc + 'stretch.cs.txt') -Raw)

# vanilla body key: Thin_Female, Fat_Female, Hulk_Female share the vanilla Thin, Fat, Hulk art; Female keeps its own
$VBody = if ($Body -ne 'Female' -and $Body.EndsWith('_Female')) { $Body.Substring(0, $Body.Length - 7) } else { $Body }
# vertical landmarks, vanilla row -> WDI row at 512, below the collar block (the top and the collar block are automatic, the hem is D).
# Male from Virginie's landmark boards (2026-11-05 points era, 2026-11-06 band lines): south pecs 276->300, navel 360->356;
# north armpits 296->292, waist 332->332; east: vanilla waistband 364 -> WDI pink centre 376 (the only side landmark we have).
# Variant A (default): collar block = cloth top .. vanilla pecs row, translated with the top; then one linear band to the navel;
# then navel .. hem (D). The WDI pecs row is NOT a landmark (the pecs relief is left to the tension flats).
# Variant B (-Variant B): collar block ends at 247 (collar box of the 2026-11-05 bands) and the vanilla pecs row 276 lands on the
# WDI pecs row 300 (x1.97 under the collar, x0.67 to the navel).
$Tables = @{
  'Male_south'   = @{ v = @(360);      w = @(356);      collarEnd = 276; hem = 404 }
  'Male_south_B' = @{ v = @(276, 360); w = @(300, 356); collarEnd = 247; hem = 404 }
  'Male_north'   = @{ v = @(332);      w = @(332);      collarEnd = 296; hem = 408 }
  'Male_east'    = @{ v = @(364);      w = @(376);      collarEnd = 247; hem = 417 }
  'Female_south' = @{ v = @(340);      w = @(340);      collarEnd = 260; hem = 400 }
  'Female_north' = @{ v = @(352);      w = @(348);      collarEnd = 292; hem = 416 }
  'Female_east'  = @{ v = @(380);      w = @(367);      collarEnd = 247; hem = 410 }
}
$key = $Body + '_' + $Facing + $(if ($Variant) { '_' + $Variant } else { '' })
if (-not $Tables.ContainsKey($key)) { throw "no landmark table for $key" }
$lm = $Tables[$key]

$shirtPath = $core + $Shirt + '_' + $VBody + '_' + $Facing + '.png'
$vbodyPath = $van + 'vanilla-' + $VBody.ToLower() + '-' + $Facing + '.png'
$wbodyPath = $ws + 'Things\Pawn\Humanlike\Bodies\Naked_' + $Body + '_' + $Facing + '.png'
$boxPath = $ws + 'UWUnderwear\boxers\boxers_' + $Body + '_' + $Facing + '.png'
$panPath = $ws + 'UWUnderwear\panties\panties_' + $Body + '_' + $Facing + '.png'
$uwPath = if ($Body -like '*Female') { $panPath } else { $boxPath }
$ePath = $here + 'E_' + $Body + '_' + $Facing + '.png'
$dPath = $here + 'hemshift_' + $Body + '_' + $Facing + '.txt'
$pinkPath = $here + 'hemshift_' + $Body + '_' + $Facing + '.pink.txt'

$shirtImg = [Img]::Read($shirtPath)
$vbody = [Img]::Read($vbodyPath)
$wbody = [Img]::Read($wbodyPath)
$uw = [Img]::Read($uwPath)
$E = [Poc]::Mask([Img]::Read($ePath), 128)
$D = [Poc]::ReadTable($dPath)
$pink = [Poc]::ReadTable($pinkPath)

# step 2
$cut = [Poc]::Strip($shirtImg, 5, 160)
$vHem = [Poc]::Hem($cut, 26)

# hem row at the centre column
$eBottom = 0; for ($x = 216; $x -le 296; $x++) { for ($y = 511; $y -ge 0; $y--) { if ($E[$y * 512 + $x]) { if ($y -gt $eBottom) { $eBottom = $y }; break } } }
$hemRow = switch ($Hem) { 'table' { [double]$lm.hem } 'pink' { $pink[256] } 'bottom' { $eBottom + 1 } default { [double]$Hem } }

# step 3
[Poc]::OwnHem = [bool]$OwnHem
# sharp: nearest-neighbour sampling of the 128 px source (no colour blending); soft: the old bilinear, for the before/after zoom
[Poc]::Nearest = $false
$warpSoft = [Poc]::Warp($cut, $E, [double[]]$lm.v, [double[]]$lm.w, $vHem, $D, $hemRow, [int]$lm.collarEnd, $CollarScale, $BlendRows, $SmoothRows, 1.0)
$edgedSoft = [Poc]::Edge([Poc]::Hard($warpSoft), 4)
[Poc]::Nearest = $true
$warpRaw = [Poc]::Warp($cut, $E, [double[]]$lm.v, [double[]]$lm.w, $vHem, $D, $hemRow, [int]$lm.collarEnd, $CollarScale, $BlendRows, $SmoothRows, 1.0)
$hemW = [double[]][Poc]::HemW
$bands = [Poc]::Bands
$topDelta = [Poc]::TopDelta
# step 3 shown with its contour rounded (mask gaussian sigma 2, threshold, clipped to E) and anti-aliased (alpha only, sigma 1), colours untouched
[Poc]::EClip = $E
$warp = [Poc]::Finish($warpRaw, 0, 1.0)
# step 4: crisp 4 px stroke (inner border one pixel ramp), contour anti-aliased (alpha only)
$edged = [Poc]::Finish($warpRaw, 4, 1.0)

# --- board
$shirtUp = $shirtImg.Up512(); $vbodyUp = $vbody.Up512(); $cutUp = $cut.Up512()
$eRing = [Poc]::Ring($E); [Poc]::Tint($eRing, 255, 60, 60)
$eRingCyan = [Poc]::Ring($E); [Poc]::Tint($eRingCyan, 0, 220, 255)
$SL = [double[]][Poc]::SL; $SR = [double[]][Poc]::SR
$vTop = [Poc]::Top($SL); $wTop = [Poc]::Top([double[]][Poc]::EL)

$c0 = [Img]::Over($vbodyUp, $shirtUp)
foreach ($r in @($vTop, $lm.collarEnd) + $lm.v) { [Poc]::HLine($c0, $r, 255, 230, 0, 0, 511, 4) }
$c1 = $cutUp.Clone(); [Poc]::EdgesCurve($c1, $SL, $SR, 255, 140, 0); $c1 = [Img]::Over($c1, $eRingCyan)
$c2 = [Img]::Over($warp, $eRing); [Poc]::Curve($c2, $hemW, 255, 80, 200, 0, 511)
foreach ($r in @($wTop, ($lm.collarEnd + $topDelta)) + $lm.w) { [Poc]::HLine($c2, $r, 255, 230, 0, 0, 511, 4) }
$c3 = [Img]::Over([Img]::Over($wbody, $uw), $edged)
$c4 = [Img]::Over($wbody, $uw); $c4 = [Img]::Over($c4, $eRing); [Poc]::Curve($c4, $hemW, 255, 80, 200, 0, 511)
$pinkC = New-Object double[] 512; for ($x = 0; $x -lt 512; $x++) { $pinkC[$x] = $pink[$x] }; [Poc]::Curve($c4, $pinkC, 255, 255, 255, 0, 511)

$hemTxt = if ($Hem -eq 'table') { 'landmark row ' + $lm.hem } elseif ($Hem -eq 'pink') { 'pink centre' } elseif ($Hem -eq 'bottom') { 'E bottom' } else { 'row ' + $Hem }
$labels = @(
  ('1 vanilla ' + $Shirt + '_' + $VBody + ' on the vanilla body (x4 nearest); yellow = vanilla landmark rows'),
  '2 cut out: outline peeled (5 layers at 128, lum<160), largest piece; orange = cloth edges (+-6 rows), cyan = E edge',
  ('3 warped onto E: rows through the landmarks (yellow); hem (pink) = ' + $(if ($OwnHem) { 'own vanilla hem per column + D' } else { 'flat + D' }) + ', centre on ' + $hemTxt + '; red = E edge'),
  '4 + TailorMade edge 4 px, on the WDI body + underwear',
  'reference: WDI body + underwear, E edge (red), pink line (white), hem curve used (pink)'
)
$title = $Body + ' ' + $Facing + ' ' + $Shirt + ' : top ' + $vTop + '->' + $wTop + ' (collar block ' + ('{0:+0;-0;0}' -f $topDelta) + ', x: ' + $(if ($CollarScale -gt 0) { 'uniform x' + $CollarScale } else { 'edge map' }) + '); bands ' + $bands + ' hem centre ' + [Math]::Round($hemRow, 1) + '; row map smoothed +-' + $SmoothRows
$out = $caps + '2026-11-06_stretch-' + $Body.ToLower() + '-' + $Facing + $(if ($Tag) { '-' + $Tag } else { '' }) + '.png'
[Poc]::Board($out, $title, [string[]]$labels, [Img[]]@($c0, $c1, $c2, $c3, $c4), 380, 150, 460)
$warp.Save($poc + 'step3_' + $key + $(if ($Tag) { '-' + $Tag } else { '' }) + '.png')
$edged.Save($poc + 'step4_' + $key + $(if ($Tag) { '-' + $Tag } else { '' }) + '.png')
$cut.Save($poc + 'step2_' + $key + '.png')
# sharpness board: 4x zooms of the hem and the collar, bilinear (before) vs nearest + crisp edge (after), step 4 on the WDI body
$onBody = [Img]::Over($wbody, $uw)
$bSoft = [Img]::Over($onBody, $edgedSoft); $bSharp = [Img]::Over($onBody, $edged)
$hy = [int][Math]::Round($hemRow) - 44; $cy = $wTop - 6
$zooms = [Img[]]@(
  [Poc]::Zoom($bSoft, 196, $hy, 120, 64, 4), [Poc]::Zoom($bSharp, 196, $hy, 120, 64, 4),
  [Poc]::Zoom($bSoft, 186, $cy, 140, 80, 4), [Poc]::Zoom($bSharp, 186, $cy, 140, 80, 4),
  [Poc]::Zoom($bSoft, 150, 150, 212, 300, 2), [Poc]::Zoom($bSharp, 150, 150, 212, 300, 2)
)
$zl = [string[]]@('hem, BEFORE: bilinear sample of the 128 px source, square 4 px edge (x4)', 'hem, AFTER: nearest sample (no colour blend), contour rounded (mask sigma 2) and anti-aliased (alpha sigma 1), crisp 4 px edge (x4)',
  'collar, BEFORE (x4)', 'collar, AFTER (x4)', 'whole, BEFORE (x2)', 'whole, AFTER (x2)')
$outZ = $caps + '2026-11-06_stretch-' + $Body.ToLower() + '-' + $Facing + $(if ($Tag) { '-' + $Tag } else { '' }) + '-sharpness.png'
[Poc]::Sheet($outZ, ($Body + ' ' + $Facing + ' ' + $Shirt + ' : sharpness, before (bilinear) / after (nearest + crisp edge); step 4 on the WDI body + underwear'), $zl, $zooms, 2)
$outZ
[Poc]::Log
"top $vTop -> $wTop ; bands $bands ; hemRow $hemRow ; eBottom $eBottom"
"hemW at 160/192/224/256/288/320/352: " + ((160, 192, 224, 256, 288, 320, 352) | ForEach-Object { [Math]::Round($hemW[$_], 1) }) -join ' '
$out
