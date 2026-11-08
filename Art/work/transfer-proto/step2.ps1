$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
function LoadPx($path) { $bm = New-Object System.Drawing.Bitmap $path; $w = $bm.Width; $h = $bm.Height
  $d = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,$w,$h), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $px = New-Object byte[] ($w*$h*4); [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $px, 0, $px.Length); $bm.UnlockBits($d); $bm.Dispose(); return ,@($px, $w, $h) }
[Layers]::Redraw = $true; [Layers]::InkLuma = 60; [Layers]::FillDilate = 3; [Layers]::TargetWidth = 0.0; [Layers]::CopyLine = $false; [Layers]::StrokeGray = 15; [S3]::Bridge = $false; [S3]::RadiusBias = 0.4; [Layers]::FillBlur = 6; [S3]::SourceBand = 0; [S3]::RingTopY = 0; [Layers]::HoleBoxL = $null; [S3]::RelativeInk = $false; [Layers]::Extra = $null
if (-not $pairsToRun) { $pairsToRun = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'), @('thin','Thin_Female'), @('fat','Fat_Female'), @('hulk','Hulk_Female')) }
# WDI women's nipple and navel (texture px, south), measured 2026-11-02 in the previous round
$nip = @{ 'Thin_Female' = @(222,290,264,350); 'Female' = @(216,296,277,345); 'Fat_Female' = @(154,358,278,350); 'Hulk_Female' = @(169,342,298,398) }
$idx = @('neckL','neckR','shL','shR','armL','armR','waistL','waistR','hipL','hipR','crotch','top','bottom')
function LmOf($path) { $info = ''; $v = [Lm]::Detect($path, [ref]$info); return @{ v = $v; info = $info; ww = [Lm]::WeakWaist; wh = [Lm]::WeakHip; wa = [Lm]::WeakArm } }
foreach ($pr in $pairsToRun) {
  $sk = $pr[0]; $tk = $pr[1]
  $sBodyP = $tmp + "vbody512_$sk.png"; $sGarP = $tmp + "imo512_$sk.png"; $tBodyP = $wdi + "Naked_${tk}_south.png"
  $Sg = LmOf $sBodyP; $Tg = LmOf $tBodyP
  # landmark pairs: (target x, y, source x, y); a landmark that hit the edge of its search range on either body is dropped (weak)
  $weakNeck = (($Tg.v[1] - $Tg.v[23]) -lt 6) -or (($Sg.v[1] - $Sg.v[23]) -lt 6); $use = New-Object System.Collections.Generic.List[int]; foreach ($i in 2,3,11,12) { $use.Add($i) }; if (-not $weakNeck) { $use.Add(0); $use.Add(1) }
  if (-not $Sg.wa -and -not $Tg.wa) { $use.Add(4); $use.Add(5) }
  if (-not $Sg.ww -and -not $Tg.ww) { $use.Add(6); $use.Add(7) }
  if (-not $Sg.wh -and -not $Tg.wh) { $use.Add(8); $use.Add(9) }
  $base = New-Object System.Collections.Generic.List[double]; $names = New-Object System.Collections.Generic.List[string]
  foreach ($i in ($use | Sort-Object)) { $base.Add($Tg.v[2*$i]); $base.Add($Tg.v[2*$i+1]); $base.Add($Sg.v[2*$i]); $base.Add($Sg.v[2*$i+1]); $names.Add($idx[$i]) }
  # rows between consecutive landmark rows (top, neck, shoulders, armpits if used, waist if used, hips if used, bottom), four per span
  $rowsT = @($Tg.v[23], $Tg.v[1], $Tg.v[5]); $rowsS = @($Sg.v[23], $Sg.v[1], $Sg.v[5]); if ($weakNeck) { $rowsT = @($Tg.v[23], $Tg.v[5]); $rowsS = @($Sg.v[23], $Sg.v[5]) }
  if ($use.Contains(4)) { $rowsT += $Tg.v[9]; $rowsS += $Sg.v[9] }
  if ($use.Contains(6)) { $rowsT += $Tg.v[13]; $rowsS += $Sg.v[13] }
  if ($use.Contains(8)) { $rowsT += $Tg.v[17]; $rowsS += $Sg.v[17] }
  $rowsT += $Tg.v[25]; $rowsS += $Sg.v[25]
  $rp = New-Object System.Collections.Generic.List[double]
  for ($j = 0; $j -lt $rowsT.Count - 1; $j++) { for ($q = 0; $q -lt 4; $q++) { $f = $q / 4.0; $rp.Add($rowsT[$j] + $f * ($rowsT[$j+1] - $rowsT[$j])); $rp.Add($rowsS[$j] + $f * ($rowsS[$j+1] - $rowsS[$j])) } }
  $rp.Add($rowsT[$rowsT.Count-1] - 2); $rp.Add($rowsS[$rowsS.Count-1] - 2)
  # offsets of the source garment over its own body, carried to the target rows by the row map and scaled by the body width ratio
  $sB = LoadPx $sBodyP; $srcGar = LoadPx $sGarP; $tB = LoadPx $tBodyP
  $L = $null; $R = $null; $t = 0; $b = 0; $o = 0; [S3]::Offsets($sB[0], $srcGar[0], 512, 512, [ref]$L, [ref]$R, [ref]$t, [ref]$b, [ref]$o)
  $band = [Math]::Max(15, $o + 1)
  $offL = New-Object 'int[]' 512; $offR = New-Object 'int[]' 512
  for ($y = 0; $y -lt 512; $y++) { $ys = $y; for ($j = 0; $j -lt $rowsT.Count - 1; $j++) { if ($y -ge $rowsT[$j] -and $y -le $rowsT[$j+1]) { $f = ($y - $rowsT[$j]) / [Math]::Max(1, $rowsT[$j+1] - $rowsT[$j]); $ys = [int][Math]::Round($rowsS[$j] + $f * ($rowsS[$j+1] - $rowsS[$j])); break } }
    $ys = [Math]::Max(0, [Math]::Min(511, $ys)); $offL[$y] = $L[$ys]; $offR[$y] = $R[$ys] }
  [Layers]::OffL = $offL; [Layers]::OffR = $offR; [Layers]::OffTop = $t; [Layers]::OffBot = $b; [Layers]::OutlineW = $o
  "== vanilla $sk garment (IMO) -> WDI $tk"
  "  vanilla: " + $Sg.info; "  WDI    : " + $Tg.info
  "  control pairs: " + ($names -join ' ') + "; dropped as weak: " + ((0..9 | Where-Object { -not $use.Contains($_) } | ForEach-Object { $idx[$_] }) -join ' ')
  $variants = @(,@('off', $base.ToArray()))
  if ($nip.ContainsKey($tk)) {
    # breast layer ON: nipples and navel on the WDI side placed on the source by relation (share of torso height neck-to-waist, share of half width at that row)
    $nt = $nip[$tk]; $ex = New-Object System.Collections.Generic.List[double]; $ex.AddRange([double[]]$base.ToArray())
    $neckT = $Tg.v[1]; $waistT = $Tg.v[13]; $neckS = $Sg.v[1]; $waistS = $Sg.v[13]
    if ($Tg.ww) { $waistT = $Tg.v[25] * 0 + $Tg.v[1] + 0.5 * ($Tg.v[25] - $Tg.v[1]) }; if ($Sg.ww) { $waistS = $Sg.v[1] + 0.5 * ($Sg.v[25] - $Sg.v[1]) }
    $cxT = ($Tg.v[0] + $Tg.v[2]) / 2; $cxS = ($Sg.v[0] + $Sg.v[2]) / 2
    foreach ($pt in @(@($nt[0], $nt[2]), @($nt[1], $nt[2]), @(256, $nt[3]))) {
      $ty = $pt[1]; $fy = ($ty - $neckT) / ($waistT - $neckT); $sy = $neckS + $fy * ($waistS - $neckS)
      $eT = [Lm]::Ext($tBodyP, [int]$ty); $eS = [Lm]::Ext($sBodyP, [int][Math]::Round($sy))
      $fx = ($pt[0] - ($eT[0] + $eT[1]) / 2) / (($eT[1] - $eT[0]) / 2); $sx = ($eS[0] + $eS[1]) / 2 + $fx * (($eS[1] - $eS[0]) / 2)
      $ex.Add($pt[0]); $ex.Add($ty); $ex.Add($sx); $ex.Add($sy) }
    $variants += ,@('on', $ex.ToArray())
  }
  foreach ($vr in $variants) {
    $outP = $tmp + "s2_${tk}_$($vr[0]).png"
    $res = [Layers]::Single($sBodyP, $sGarP, $tBodyP, [double[]]$vr[1], [double[]]$rp.ToArray(), $outP, 2.0, $band)
    $out = LoadPx $outP
    "  [breast layer $($vr[0])] $res"
    $nm = $names.ToArray(); if ($vr[0] -eq 'on') { $nm += @('nipL','nipR','navel') }
    "    " + [Layers]::MapCheck($sBodyP, $tBodyP, [double[]]$vr[1], [double[]]$rp.ToArray(), 2.0, [string[]]$nm)
    $c1 = $false; $c2 = $false; $c3 = $false; $c5 = $false
    [Cm]::Compare($sBodyP, $sGarP, $tBodyP, $outP, [ref]$c1, [ref]$c2, [ref]$c3, [ref]$c5)
    "    C4 source: " + ([S3]::Widths($srcGar[0], 512, 512, $band, 60, 'src') -split "`n")[0..1] -join " | "
    "    C4 result: " + ([S3]::Widths($out[0], 512, 512, $band, 60, 'res') -split "`n")[0..1] -join " | "
  }
}
