# Vanilla to WDI button shirt for any adult body type, three facings (generalises tmfit.ps1, tmfit-east.ps1, tmfit-north.ps1,
# which were tuned by hand on Male). Same method: TailorMade's per-row fit with bands, C' shirt tail from hemshift_<Body>_<facing>.txt.
# Bands, vanilla row -> WDI row:
#   top of the body -> top of the body;
#   collar (vanilla top + 75) -> WDI top + 58 (south) / + 60 (north); no collar band on the side view, as on Male;
#   vanilla trousers waistband (top of AB's Pants_<Body>_<facing> at its middle column) -> WDI pink line at the body's middle
#   (south, north) or blue line (east), as on Male;
#   shirt bottom -> waistband target + 0.65 x (shirt bottom - vanilla waistband).
# Male's hand-picked pec band (323 -> 317, south) is not generalised: it has no measured counterpart on the other bodies.
param([string]$Body = 'Fat', [int]$BackTarget = 0, [int]$Outline = 4, [switch]$NoShift, [switch]$Strip, [double]$SmoothSigma = 0, [switch]$Cover, [string[]]$Facings = @('south', 'east', 'north'))  # NoShift: C' set to 0 (to compare, 2026-11-05); Strip: vanilla outline removed first, TailorMade's TRIM (Virginie 2026-11-05, women)  # Outline: final outline radius at 512 (TailorMade: 2 px at 256). 16 (the vanilla outline width) tried 2026-11-05: blocky, black neck and hem, dropped
# was:  # BackTarget > 0: waistband target of the back view forced to that row (alternative to its own pink line)
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition (Get-Content ($d + 'tmfit.cs.txt') -Raw)
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-shirtbutton-'
$vb = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$ab = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2986402536\Textures\Things\Pawn\Humanlike\Apparel\Pants\Pants_'
$core = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17\ShirtButton_'
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\215bed336962f00b\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\'
function Edge($p, $fromTop, $x) { [TmFit]::Edge($p, $fromTop, $x) }
foreach ($f in $Facings) {  # SmoothSigma > 0: silhouette smoothed after the fit (TmFit.SmoothEdge), files suffixed _smooth
  $gar = if ($f -eq 'south') { $film + $Body.ToLower() + '-south\0000.png' } else { $core + $Body + '_' + $f + '.png' }
  $vbody = if ($f -eq 'south') { $vb + $Body.ToLower() + '.png' } else { $vb + $Body + '_' + $f + '.png' }
  $nb = $wb + 'Things\Pawn\Humanlike\Bodies\Naked_' + $Body + '_' + $f + '.png'
  $bx = $wb + 'UWUnderwear\boxers\boxers_' + $Body + '_' + $f + '.png'; $pt = $wb + 'UWUnderwear\panties\panties_' + $Body + '_' + $f + '.png'
  $pants = $ab + $Body + '_' + $f + '.png'
  $mid = [TmFit]::Mid($nb); $vwb = Edge $pants $true ([TmFit]::Mid($pants))
  $bTop = Edge $bx $true $mid; $pTop = Edge $pt $true $mid
  $tgt = if ($f -eq 'east') { [Math]::Min($bTop, $pTop) } else { [Math]::Max($bTop, $pTop) }
  if ($f -eq 'north' -and $BackTarget -gt 0) { $tgt = $BackTarget }
  $vt = Edge $vbody $true (-1); $wt = Edge $nb $true (-1); $gb = Edge $gar $false (-1); $tail = $tgt + [int](0.65 * ($gb - $vwb))
  if ($f -eq 'east') { $v = @($vt, $vwb, $gb); $w = @($wt, $tgt, $tail) }
  else { $v = @($vt, ($vt + 75), $vwb, $gb); $w = @($wt, ($wt + $(if ($f -eq 'south') { 58 } else { 60 })), $tgt, $tail) }
  $hs = $d + 'hemshift_' + $Body + '_' + $f + '.txt'
  if (-not (Test-Path $hs)) { powershell.exe -NoProfile -ExecutionPolicy Bypass -File ($d + 'hemshift.ps1') -Body $Body -Facing $f }
  [Nav]::SetPink($bx, $pt, 512, 512); [TmFit]::TailPink = [Nav]::Pink; [TmFit]::TailLen = 38
  [TmFit]::Shift = [double[]]((Get-Content $hs) -split ';' | ForEach-Object { [double]::Parse($_, [cultureinfo]::InvariantCulture) })
  if ($NoShift) { [TmFit]::Shift = New-Object double[] 512 }
  $full = $tmp + 'tmb_' + $Body + '_' + $f + $(if ($NoShift) { '_noshift' } elseif ($Strip) { '_strip' } else { '' }) + $(if ($Cover) { '_cover' } else { '' }) + $(if ($SmoothSigma -gt 0) { '_smooth' } else { '' }) + '_full.png'
  # shirt bottom at most on the boxers bottom, never over the legs (Virginie 2026-11-05): bake, measure, shrink the tail where long, bake again
  [TmFit]::CoverStroke = [bool]$Cover; [TmFit]::FlatBottom = -not $Cover; [TmFit]::StripOutline = [bool]$Strip; [TmFit]::TailScale = $null; $first = [TmFit]::Bake($gar, $vbody, $nb, $v, $w)
  [TmFit]::Save($first, 4, ($tmp + 'tmb_' + $Body + '_' + $f + '_nostretch.png'))
  [TmFit]::TailScale = [TmFit]::Stretch($first, $bx, 8); "  tail scale " + [Math]::Round([TmFit]::LastScale, 2) + " (column " + [TmFit]::LastScaleCol + ")"
  # one factor for the whole tail, no crop (the hem keeps its shape)
  [TmFit]::StripOutline = [bool]$Strip; $baked = [TmFit]::Bake($gar, $vbody, $nb, $v, $w); if ($SmoothSigma -gt 0) { $baked = [TmFit]::SmoothEdge($baked, $SmoothSigma) }; [TmFit]::Save($baked, $Outline, $full); [TmFit]::Save($baked, 0, ($full -replace '_full.png$', '_nooutline.png')); if ($Cover) { [TmFit]::Save($baked, 13, ($full -replace '_full.png$', '_out13.png')) }; [TmFit]::TailScale = $null
  [TmFit]::Pants($nb, $bx, $pt, ($tmp + 'tmb_' + $Body + '_' + $f + '_pants.png'))
  "  inner stroke WDI L " + [TmFit]::InL + " R " + [TmFit]::InR + ", vanilla L " + [TmFit]::VInL + " R " + [TmFit]::VInR; "  cloth top " + [TmFit]::ClothTop + " (vanilla body top $vt)"
  "$Body $f  v=$($v -join ',')  w=$($w -join ',')  -> $full"
}
