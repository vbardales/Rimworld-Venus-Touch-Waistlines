$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
function LoadPx($path) { $bm = New-Object System.Drawing.Bitmap $path; $w = $bm.Width; $h = $bm.Height
  $d = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,$w,$h), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $px = New-Object byte[] ($w*$h*4); [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $px, 0, $px.Length); $bm.UnlockBits($d); $bm.Dispose(); return ,@($px, $w, $h) }
[Layers]::Redraw = $true; [Layers]::InkLuma = 60; [Layers]::FillDilate = 3; [Layers]::TargetWidth = 0.0; [Layers]::CopyLine = $false; [Layers]::StrokeGray = 15; [S3]::Bridge = $false; [S3]::RadiusBias = 0.4; [Layers]::FillBlur = 6; [S3]::SourceBand = 0; [S3]::RingTopY = 0; [Layers]::HoleBoxL = $null; [S3]::RelativeInk = $false; [Layers]::Extra = $null
$wdiShirt = @{ 'Thin_Female' = 1; 'Fat_Female' = 1; 'Hulk_Female' = 1 }; if ($null -eq $tightOff) { $tightOff = 1 }; if ($null -eq $biasOut) { $biasOut = 0 }; if ($null -eq $biasHem) { $biasHem = 0 }; if ($null -eq $biasSleeve) { $biasSleeve = 0 }
if (-not $pairsToRun) { $pairsToRun = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'), @('thin','Thin_Female'), @('fat','Fat_Female'), @('hulk','Hulk_Female')) }
$idx = @('neckL','neckR','shL','shR','armL','armR','waistL','waistR','hipL','hipR','crotch','top','bottom')
function LmOf($path) { $info = ''; $v = [Lm]::Detect($path, [ref]$info); return @{ v = $v; info = $info; ww = [Lm]::WeakWaist; wh = [Lm]::WeakHip; wa = [Lm]::WeakArm } }
function Interp($x, $xs, $ys) { for ($j = 0; $j -lt $xs.Count - 1; $j++) { if ($x -le $xs[$j+1] -or $j -eq $xs.Count - 2) { $f = ($x - $xs[$j]) / [Math]::Max(1e-6, $xs[$j+1] - $xs[$j]); return $ys[$j] + $f * ($ys[$j+1] - $ys[$j]) } } }
function Bbox($s) { if ($s -match 'bbox \((\d+),(\d+)\)-\((\d+),(\d+)\)') { return @([int]$Matches[1], [int]$Matches[2], [int]$Matches[3], [int]$Matches[4]) } return $null }
foreach ($pr in $pairsToRun) {
  $sk = $pr[0]; $tk = $pr[1]
  $sBodyP = $tmp + "vbody512_$sk.png"; $sGarP = $tmp + "imo512_$sk.png"; $tBodyP = $wdi + "Naked_${tk}_south.png"
  $Sg = LmOf $sBodyP; $Tg = LmOf $tBodyP
  $weakNeck = (($Tg.v[1] - $Tg.v[23]) -lt 6) -or (($Sg.v[1] - $Sg.v[23]) -lt 6)
  $use = New-Object System.Collections.Generic.List[int]; foreach ($i in 2,3,11,12) { $use.Add($i) }; if (-not $weakNeck) { $use.Add(0); $use.Add(1) }
  if (-not $Sg.wa -and -not $Tg.wa) { $use.Add(4); $use.Add(5) }
  if (-not $Sg.ww -and -not $Tg.ww) { $use.Add(6); $use.Add(7) }
  if (-not $Sg.wh -and -not $Tg.wh) { $use.Add(8); $use.Add(9) }
  $base = New-Object System.Collections.Generic.List[double]; $names = New-Object System.Collections.Generic.List[string]
  foreach ($i in ($use | Sort-Object)) { $base.Add($Tg.v[2*$i]); $base.Add($Tg.v[2*$i+1]); $base.Add($Sg.v[2*$i]); $base.Add($Sg.v[2*$i+1]); $names.Add($idx[$i]) }
  $nBody = $names.Count
  $rowsT = @($Tg.v[23], $Tg.v[1], $Tg.v[5]); $rowsS = @($Sg.v[23], $Sg.v[1], $Sg.v[5]); if ($weakNeck) { $rowsT = @($Tg.v[23], $Tg.v[5]); $rowsS = @($Sg.v[23], $Sg.v[5]) }
  if ($use.Contains(4)) { $rowsT += $Tg.v[9]; $rowsS += $Sg.v[9] }
  if ($use.Contains(6)) { $rowsT += $Tg.v[13]; $rowsS += $Sg.v[13] }
  if ($use.Contains(8)) { $rowsT += $Tg.v[17]; $rowsS += $Sg.v[17] }
  $rowsT += $Tg.v[25]; $rowsS += $Sg.v[25]
  $rp = New-Object System.Collections.Generic.List[double]
  for ($j = 0; $j -lt $rowsT.Count - 1; $j++) { for ($q = 0; $q -lt 4; $q++) { $f = $q / 4.0; $rp.Add($rowsT[$j] + $f * ($rowsT[$j+1] - $rowsT[$j])); $rp.Add($rowsS[$j] + $f * ($rowsS[$j+1] - $rowsS[$j])) } }
  $rp.Add($rowsT[$rowsT.Count-1] - 2); $rp.Add($rowsS[$rowsS.Count-1] - 2)
  $sB = LoadPx $sBodyP; $srcGar = LoadPx $sGarP
  $L = $null; $R = $null; $ot = 0; $ob = 0; $oo = 0; [S3]::Offsets($sB[0], $srcGar[0], 512, 512, [ref]$L, [ref]$R, [ref]$ot, [ref]$ob, [ref]$oo)
  $band = [Math]::Max(15, $oo + 1); [Layers]::OutlineW = $oo
  "== vanilla $sk garment (IMO) -> WDI $tk"
  "  vanilla: " + $Sg.info; "  WDI    : " + $Tg.info
  # garment features, placed on the target body by relation (row map between the landmark rows, x by the share of the half width at that row)
  $ft = [Gl]::Features($srcGar[0], 512, 512, $band); $fn = [Gl]::Names -split ' '
  $all = New-Object System.Collections.Generic.List[double]; $all.AddRange([double[]]$base.ToArray())
  $fdesc = @()
  for ($k = 0; $k -lt $ft.Count / 2; $k++) { $x = $ft[2*$k]; $y = $ft[2*$k+1]
    $yt = Interp $y $rowsS $rowsT; $eS = [Lm]::Ext($sBodyP, [int][Math]::Round($y)); $eT = [Lm]::Ext($tBodyP, [int][Math]::Round($yt))
    if ($eS[0] -lt 0 -or $eT[0] -lt 0) { continue }
    $cxS = ($eS[0] + $eS[1]) / 2; $cxT = ($eT[0] + $eT[1]) / 2; $hS = ($eS[1] - $eS[0]) / 2; $hT = ($eT[1] - $eT[0]) / 2
    $xt = $cxT + ($x - $cxS) * $hT / $hS
    # round 3 (Virginie 2026-11-03: the cloth must come over the skin): hem down, hem corners and sleeve ends outward
    if ($fn[$k] -like 'hem*') { $yt += $biasHem; $xt += [Math]::Sign($x - $cxS) * $biasOut }
    if ($fn[$k] -like 'sleeve*') { $xt += [Math]::Sign($x - $cxS) * $biasSleeve }
    $all.Add($xt); $all.Add($yt); $all.Add($x); $all.Add($y); $fdesc += ("{0}({1:0},{2:0})->({3:0},{4:0})" -f $fn[$k], $x, $y, $xt, $yt) }
  # round 3: garment contour anchors, 12 rows from 6 % to 88 % of the garment height, edge placed at the target body edge + source offset x local scale + biasOut (outward)
  $wL = $null; $wR = $null; if ($wdiShirt.ContainsKey($tk)) { $tbp = LoadPx $tBodyP; $wsp = LoadPx ($tmp + "wshirt512_$tk.png"); $wl = $null; $wr = $null; $w1 = 0; $w2 = 0; $w3 = 0; [S3]::Offsets($tbp[0], $wsp[0], 512, 512, [ref]$wl, [ref]$wr, [ref]$w1, [ref]$w2, [ref]$w3); $wL = $wl; $wR = $wr; "  outline: WDI offset profile of ShirtBasic_${tk} (width $w3, row 300 L$($wl[300]) R$($wr[300]))" } else { "  outline: tight (body outline + $tightOff px)" }
  $G = LmOf $sGarP; $gTop = $G.v[23]; $gBot = $G.v[25]; $nCont = 0
  for ($i = 0; $i -lt 24; $i++) { $u = 0.03 + 0.94 * $i / 23; $ys = [int][Math]::Round($gTop + $u * ($gBot - $gTop)); $yt = Interp $ys $rowsS $rowsT; $eS = [Lm]::Ext($sBodyP, $ys); $eT = [Lm]::Ext($tBodyP, [int][Math]::Round($yt)); if ($eS[0] -lt 0 -or $eT[0] -lt 0) { continue }; $all.Add($eT[0]); $all.Add($yt); $all.Add($eS[0]); $all.Add($ys); $all.Add($eT[1]); $all.Add($yt); $all.Add($eS[1]); $all.Add($ys); $nCont += 2 }
  # hem bottom middle, biased down
  $gb = [Lm]::Ext($sGarP, [int]$gBot); $mx = ($gb[0] + $gb[1]) / 2.0; $ytb = (Interp $gBot $rowsS $rowsT) + $biasHem; $eS = [Lm]::Ext($sBodyP, [int]$gBot); $eT = [Lm]::Ext($tBodyP, [int][Math]::Round($ytb - $biasHem))
  if ($eS[0] -ge 0 -and $eT[0] -ge 0) { $all.Add(($eT[0] + $eT[1]) / 2.0 + ($mx - ($eS[0] + $eS[1]) / 2.0) * ($eT[1] - $eT[0]) / ($eS[1] - $eS[0])); $all.Add($ytb); $all.Add($mx); $all.Add($gBot) }
  "  contour anchors: $nCont, bias out $biasOut, hem down $biasHem, sleeves out $biasSleeve"
  "  anchors (body): " + ($names -join ' ') + "; dropped as weak: " + ((0..9 | Where-Object { -not $use.Contains($_) } | ForEach-Object { $idx[$_] }) -join ' ')
  "  anchors (garment features by relation): " + ($fdesc -join ' ')
  # per-garment stroke radius calibration from the identity run (4x width estimator)
  [Layers]::TargetWidth = 0.0
  $srcMed = 0; [void][W4]::Measure($srcGar[0], 512, 512, $band, 'src'); $srcMed = [W4]::Med; $srcQ1 = [W4]::Q1; $srcQ3 = [W4]::Q3
  $top = 0; $bot = 0; for ($y = 0; $y -lt 512; $y++) { $any = $false; for ($x = 0; $x -lt 512; $x++) { if ($sB[0][($y*512+$x)*4+3] -gt 40) { $any = $true; break } }; if ($any) { if ($top -eq 0) { $top = $y }; $bot = $y } }
  $irp = New-Object System.Collections.Generic.List[double]; for ($y = $top + 2; $y -lt $bot - 1; $y += 12) { $irp.Add($y); $irp.Add($y) }
  $c = 1.0; $mw = 0; $bestC = 1.0; $bestErr = 1e9
  for ($it = 0; $it -lt 6; $it++) {
    if ($it -gt 0) { [Layers]::TargetWidth = $c * $mw }
    [void][Layers]::Single($sBodyP, $sGarP, $sBodyP, [double[]]@(), [double[]]$irp.ToArray(), ($tmp + 'cal.png'), 2.0, $band)
    if ($it -eq 0 -and [Layers]::Info -match 'median width ([\d\.,]+)') { $mw = [double]($Matches[1] -replace ',', '.') }
    $cal = LoadPx ($tmp + 'cal.png'); [void][W4]::Measure($cal[0], 512, 512, $band, 'id'); $idMed = [W4]::Med
    "  radius calibration pass ${it}: source width4 median $([Math]::Round($srcMed,2)), identity $([Math]::Round($idMed,2)), factor c $([Math]::Round($c,2))"
    if ($idMed -le 0) { break }
    $err = [Math]::Abs($idMed / $srcMed - 1); if ($err -lt $bestErr) { $bestErr = $err; $bestC = $c }
    if ($err -le 0.03) { break }
    $c = [Math]::Max(0.6, [Math]::Min(3.0, $c * [Math]::Pow($srcMed / $idMed, 0.6))) }
  $c = $bestC; "  radius factor kept: c $([Math]::Round($c,2)) (identity width error $([Math]::Round(100*$bestErr,1)) %)"
  if ($c -ne 1.0) { [Layers]::TargetWidth = $c * $mw } else { [Layers]::TargetWidth = 0.0 }
  $outP = $tmp + "s10${sfx}_${tk}.png"
  if ($breast -and $nipT.ContainsKey($tk)) {
    $nt = $nipT[$tk]; $neckT = $Tg.v[1]; $waistT = $Tg.v[13]; $neckS = $Sg.v[1]; $waistS = $Sg.v[13]
    if ($Tg.ww) { $waistT = $Tg.v[1] + 0.5 * ($Tg.v[25] - $Tg.v[1]) }; if ($Sg.ww) { $waistS = $Sg.v[1] + 0.5 * ($Sg.v[25] - $Sg.v[1]) }
    foreach ($pt in @(@($nt[0], $nt[2]), @($nt[1], $nt[2]), @(256, $nt[3]))) {
      $ty = $pt[1]; $fy = ($ty - $neckT) / ($waistT - $neckT); $sy = $neckS + $fy * ($waistS - $neckS)
      $eT = [Lm]::Ext($tBodyP, [int]$ty); $eS = [Lm]::Ext($sBodyP, [int][Math]::Round($sy))
      $fx = ($pt[0] - ($eT[0] + $eT[1]) / 2) / (($eT[1] - $eT[0]) / 2); $sx = ($eS[0] + $eS[1]) / 2 + $fx * (($eS[1] - $eS[0]) / 2)
      $all.Add($pt[0]); $all.Add($ty); $all.Add($sx); $all.Add($sy) }
    "  breast layer ON: nipples and navel anchors added by relation" }
  $res = [Layers]::Single($sBodyP, $sGarP, $tBodyP, [double[]]$all.ToArray(), [double[]]$rp.ToArray(), $outP, 2.0, $band)
  $out = LoadPx $outP
  # round 5: clip the result alpha to the target body edge + profile; keep the unclipped numbers
  $tb = LoadPx $tBodyP; $uP = $tmp + "s10u${sfx}_${tk}.png"; Copy-Item $outP $uP -Force
  # round 6 (Audit): per-row horizontal remap of the garment alone onto [body edge - profile, body edge + profile]; edge bands (8 px) copied 1:1, interior stretched
  $tb6 = LoadPx $tBodyP; $px0 = $out[0]; $px1 = New-Object byte[] $px0.Length; $W6 = 8
  $has6 = New-Object 'bool[]' 512; $slv = New-Object 'bool[]' 512; $gL6 = New-Object 'double[]' 512; $gR6 = New-Object 'double[]' 512; $tL6 = New-Object 'double[]' 512; $tR6 = New-Object 'double[]' 512
  for ($y = 0; $y -lt 512; $y++) { $gl = -1; $gr = -1; $bl = -1; $br = -1
    for ($x = 0; $x -lt 512; $x++) { if ($px0[($y*512+$x)*4+3] -gt 40) { if ($gl -lt 0) { $gl = $x }; $gr = $x }; if ($tb6[0][($y*512+$x)*4+3] -gt 40) { if ($bl -lt 0) { $bl = $x }; $br = $x } }
    if ($gl -lt 0 -or $bl -lt 0) { continue }
    if ($wL) { $eL = $wL[$y]; $eR = $wR[$y] } else { $eL = $tightOff; $eR = $tightOff }
    $has6[$y] = $true; $gL6[$y] = $gl; $gR6[$y] = $gr; $tL6[$y] = $bl - $eL; $tR6[$y] = $br + $eR; $slv[$y] = (($gl -lt $bl - 30) -or ($gr -gt $br + 30)) }
  function Sm6($a, $has) { $m = New-Object 'double[]' 512; for ($y = 0; $y -lt 512; $y++) { if (-not $has[$y]) { continue }; $v = New-Object System.Collections.Generic.List[double]; for ($k = -2; $k -le 2; $k++) { $yy = $y + $k; if ($yy -ge 0 -and $yy -lt 512 -and $has[$yy]) { $v.Add($a[$yy]) } }; $v.Sort(); $m[$y] = $v[[int][Math]::Floor($v.Count / 2)] }
    $g = New-Object 'double[]' 512; for ($y = 0; $y -lt 512; $y++) { if (-not $has[$y]) { continue }; $s = 0.0; $ws = 0.0; for ($k = -5; $k -le 5; $k++) { $yy = $y + $k; if ($yy -ge 0 -and $yy -lt 512 -and $has[$yy]) { $w = [Math]::Exp(-($k*$k)/8.0); $s += $w * $m[$yy]; $ws += $w } }; $g[$y] = $s / $ws }; return ,$g }
  $tL6 = Sm6 $tL6 $has6; $tR6 = Sm6 $tR6 $has6
  $facs = New-Object System.Collections.Generic.List[double]; $nSlv = 0
  for ($y = 0; $y -lt 512; $y++) { if (-not $has6[$y]) { continue }; $gl = $gL6[$y]; $gr = $gR6[$y]
    if ($slv[$y]) { $nSlv++; for ($x = 0; $x -lt 512; $x++) { $o = ($y*512+$x)*4; for ($c = 0; $c -lt 4; $c++) { $px1[$o+$c] = $px0[$o+$c] } }; continue }
    $tl = $tL6[$y]; $tr = $tR6[$y]; $fw = ($tr - $tl) / [Math]::Max(1.0, $gr - $gl); $facs.Add($fw)
    for ($x = [int][Math]::Floor($tl); $x -le [int][Math]::Ceiling($tr); $x++) { if ($x -lt 0 -or $x -gt 511) { continue }; $d = $x - $tl; $e = $tr - $x
      if ($d -lt $W6) { $sx = $gl + $d } elseif ($e -lt $W6) { $sx = $gr - $e } elseif (($tr - $tl) -gt 2 * $W6 + 2 -and ($gr - $gl) -gt 2 * $W6 + 2) { $u = ($d - $W6) / (($tr - $tl) - 2 * $W6); $sx = $gl + $W6 + $u * (($gr - $gl) - 2 * $W6) } else { $sx = $gl + ($d / [Math]::Max(1.0, $tr - $tl)) * ($gr - $gl) }
      $sxi = [Math]::Max(0, [Math]::Min(511, [int][Math]::Round($sx))); $so = ($y*512+$sxi)*4; $o = ($y*512+$x)*4; for ($c = 0; $c -lt 4; $c++) { $px1[$o+$c] = $px0[$so+$c] } } }
  $out[0] = $px1; $fs = $facs.ToArray() | Sort-Object; $over15 = ($fs | Where-Object { $_ -gt 1.5 }).Count
  "  [round 6 remap] rows remapped $($facs.Count), sleeve rows kept as is $nSlv; stretch factor min $([Math]::Round($fs[0],2)) median $([Math]::Round($fs[[int]($fs.Count/2)],2)) max $([Math]::Round($fs[$fs.Count-1],2)); rows over 1.5: $over15$(if ($over15 -gt 0) { ' FLAG' })"
  $px = $out[0]; $removed = 0; $area0 = 0; $outside = 0; $uOvN = 0; $uOvW = 0.0; $uShN = 0; $uShW = 0.0; $cutRows = New-Object 'bool[]' 512
  $loS = New-Object 'int[]' 512; $hiS = New-Object 'int[]' 512
  for ($y = 0; $y -lt 512; $y++) { $bl = -1; $br = -1; for ($x = 0; $x -lt 512; $x++) { if ($tb[0][($y*512+$x)*4+3] -gt 40) { if ($bl -lt 0) { $bl = $x }; $br = $x } }
    if ($bl -lt 0) { $loS[$y] = 512; $hiS[$y] = -1 } else { if ($wL) { $eL = $wL[$y]; $eR = $wR[$y] } else { $eL = $tightOff; $eR = $tightOff }; $loS[$y] = $bl - $eL; $hiS[$y] = $br + $eR }
    $gl = -1; $gr = -1
    for ($x = 0; $x -lt 512; $x++) { $o = ($y*512+$x)*4+3; if ($px[$o] -gt 40) { $area0++; if ($bl -ge 0 -and ($x -lt $bl -or $x -gt $br)) { $outside++ }; if ($gl -lt 0) { $gl = $x }; $gr = $x
        if ($x -lt $loS[$y] -or $x -gt $hiS[$y]) { $px[$o] = 0; $removed++; $cutRows[$y] = $true } } }
    if ($bl -ge 0 -and $gl -ge 0) { $dl = $loS[$y] - $gl; $dr = $gr - $hiS[$y]; foreach ($d in @($dl, $dr)) { if ($d -gt 0) { $uOvN++; if ($d -gt $uOvW) { $uOvW = $d } } } } }
  # strokes redrawn on the clipped edge: 3 px dark ink just inside the band edge on rows that were cut
  for ($y = 0; $y -lt 512; $y++) { if (-not $cutRows[$y]) { continue }; foreach ($xe in @($loS[$y], $hiS[$y])) { for ($k = 0; $k -lt 3; $k++) { $x = if ($xe -eq $loS[$y]) { $xe + $k } else { $xe - $k }; if ($x -ge 0 -and $x -lt 512) { $o = ($y*512+$x)*4; if ($px[$o+3] -gt 40) { $px[$o] = 15; $px[$o+1] = 15; $px[$o+2] = 15; $px[$o+3] = 255 } } } } }
  $bm = New-Object System.Drawing.Bitmap 512, 512, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb); $dd = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,512,512), [System.Drawing.Imaging.ImageLockMode]::WriteOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb); [System.Runtime.InteropServices.Marshal]::Copy($px, 0, $dd.Scan0, $px.Length); $bm.UnlockBits($dd); $bm.Save($outP); $bm.Dispose(); $out = LoadPx $outP
  "  [round 5 clip] unclipped: garment area $area0 px, outside the body edge $outside px, UNCLIPPED overshoot: $uOvN edge samples beyond body+profile, worst $uOvW px; clip removed $removed px ($([Math]::Round(100*$removed/[Math]::Max(1,$area0),1)) % of the garment, $([Math]::Round(100*$removed/[Math]::Max(1,$outside),1)) % of the part outside the body edge)$(if ($removed -gt 0.15 * [Math]::Max(1,$outside)) { ' FLAG: over 15 % of the sleeve/outside part' })"
  "  [round 3] $res"; "    " + [C1s]::Run($sBodyP, $sGarP, $tBodyP, $outP, "C1", 24)
  "    " + [Layers]::MapCheck($sBodyP, $tBodyP, [double[]]$all.ToArray(), [double[]]$rp.ToArray(), 2.0, [string[]]$names.ToArray(), $nBody)
  # C1 round 4: result garment outer edge against the TARGET body edge + the outline profile (WDI offsets, or tight +tightOff); shortfall limit 2, overshoot limit 8
  $tb = LoadPx $tBodyP; $gy0 = 512; $gy1 = 0; for ($y = 0; $y -lt 512; $y++) { for ($x = 0; $x -lt 512; $x++) { if ($out[0][($y*512+$x)*4+3] -gt 40) { if ($y -lt $gy0) { $gy0 = $y }; if ($y -gt $gy1) { $gy1 = $y }; break } } }
  $sf = New-Object System.Collections.Generic.List[double]; $ov = New-Object System.Collections.Generic.List[double]; $nS = 0; $nO = 0; $n = 0
  for ($i = 0; $i -lt 24; $i++) { $y = [int][Math]::Round($gy0 + (0.03 + 0.94 * $i / 23) * ($gy1 - $gy0)); $bl = -1; $br = -1; $gl = -1; $gr = -1
    for ($x = 0; $x -lt 512; $x++) { if ($tb[0][($y*512+$x)*4+3] -gt 40) { if ($bl -lt 0) { $bl = $x }; $br = $x }; if ($out[0][($y*512+$x)*4+3] -gt 40) { if ($gl -lt 0) { $gl = $x }; $gr = $x } }
    if ($bl -lt 0 -or $gl -lt 0) { continue }
    if ($wL) { $eL = $wL[$y]; $eR = $wR[$y] } else { $eL = $tightOff; $eR = $tightOff }
    foreach ($d in @((($bl - $gl) - $eL), (($gr - $br) - $eR))) { $n++; if ($d -lt -2) { $sf.Add(-$d); $nS++ } ; if ($d -gt 8) { $ov.Add($d); $nO++ } } }
  "    C1 round 4 (garment edge vs body edge + profile), $n samples: shortfall over 2: $nS (worst $(if ($sf.Count) { [Math]::Round(($sf | Measure-Object -Maximum).Maximum,1) } else { 0 })), overshoot over 8: $nO (worst $(if ($ov.Count) { [Math]::Round(($ov | Measure-Object -Maximum).Maximum,1) } else { 0 })) -> $(if ($nS -eq 0 -and $nO -eq 0) { 'PASS' } else { 'FAIL' })"
  $c1 = $false; $c2 = $false; $c3 = $false; $c5 = $false
  [Cm]::Compare($sBodyP, $sGarP, $tBodyP, $outP, [ref]$c1, [ref]$c2, [ref]$c3, [ref]$c5)
  $sw = [Cm]::Measure($sBodyP, $sGarP); $tw2 = [Cm]::Measure($tBodyP, $outP)
  $bs = Bbox ([S3]::RingBoxIn($srcGar[0], 512, 512, $band, 60, 150, 100, 360, 330)); $bt = Bbox ([S3]::RingBoxIn($out[0], 512, 512, $band, 60, 150, 100, 360, 330))
  if ($bs -and $bt) { $sNw = ($bs[2]-$bs[0]+1) / $sw.ShoulderW; $tNw = ($bt[2]-$bt[0]+1) / $tw2.ShoulderW; $sNd = ($bs[3]-$bs[1]+1) / ($sw.Bot-$sw.Top); $tNd = ($bt[3]-$bt[1]+1) / ($tw2.Bot-$tw2.Top)
    "    C2 (collar ring ink bbox): width/shoulders source $([Math]::Round($sNw,3)) result $([Math]::Round($tNw,3)) ($([Math]::Round(100*[Math]::Abs($tNw/$sNw-1),1)) %), height/torso source $([Math]::Round($sNd,3)) result $([Math]::Round($tNd,3)) ($([Math]::Round(100*[Math]::Abs($tNd/$sNd-1),1)) %), limit 5 %" }
  $ws = [S3]::Widths($srcGar[0], 512, 512, $band, 60, 'src'); $wr = [S3]::Widths($out[0], 512, 512, $band, 60, 'res')
  [void][W4]::Measure($out[0], 512, 512, $band, 'res'); $rMed = [W4]::Med; $rQ1 = [W4]::Q1; $rQ3 = [W4]::Q3
  "    C4 topology: " + (($ws -split "`n")[0] -replace '^\s*src: ', 'source ') + " | " + (($wr -split "`n")[0] -replace '^\s*res: ', 'result ')
  "    C4 width4: source median $([Math]::Round($srcMed,2)) IQR $([Math]::Round($srcQ1,2))-$([Math]::Round($srcQ3,2)); result median $([Math]::Round($rMed,2)) ($([Math]::Round(100*($rMed/$srcMed-1),1)) %) IQR $([Math]::Round($rQ1,2))-$([Math]::Round($rQ3,2)); limit 10 %"
}






