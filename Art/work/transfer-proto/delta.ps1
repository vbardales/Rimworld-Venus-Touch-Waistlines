param([string]$facing = 'south')
# Delta vanilla 1.7 -> WDI per point of attention, same detector on both (Pts.Body), all at 512, reported in px of the 128 px texture (/4).
# Per zone: mean vertical shift, width ratio (L/R pairs, about the midline) or front/back shift (side view), spread inside the zone, and the move that absorbs it.
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
[Gl]::Facing = $facing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points\'
$pairs = @(@('Male','Male'),@('Thin','Thin'),@('Fat','Fat'),@('Hulk','Hulk'),@('Female','Female'),@('Thin_Female','Thin'),@('Fat_Female','Fat'),@('Hulk_Female','Hulk'))
$L = New-Object System.Collections.Generic.List[string]; $Z = New-Object System.Collections.Generic.List[string]
$cw = 300; $sh = New-Object System.Drawing.Bitmap ($cw * $pairs.Count), 360; $g = [System.Drawing.Graphics]::FromImage($sh); $g.Clear([System.Drawing.Color]::FromArgb(200,196,182)); $g.SmoothingMode = 'AntiAlias'
$font = New-Object System.Drawing.Font 'Arial', 9, ([System.Drawing.FontStyle]::Bold); $i = 0
$pen = New-Object System.Drawing.Pen ([System.Drawing.Color]::Red), 1.5; $pen.CustomEndCap = New-Object System.Drawing.Drawing2D.AdjustableArrowCap 3, 3
foreach ($p in $pairs) {
  $wp = $wdi + "Naked_$($p[0])_$facing.png"; $vp = $tmp + "core17_512\Naked_$($p[1])_$facing.png"
  [Pts]::MaleBody = ($p[0] -match '^(Male|Thin|Fat|Hulk)$'); $W = [Pts]::Body($wp)
  [Pts]::MaleBody = $false; $V = [Pts]::Body($vp)
  $vb = @{}; foreach ($q in $V) { $vb[$q.Name] = $q }
  $wb = New-Object System.Drawing.Bitmap $wp; $dst = New-Object System.Drawing.Rectangle ($i * $cw), 0, $cw, 360; $srcR = New-Object System.Drawing.Rectangle 56, 90, 400, 480; $g.DrawImage($wb, $dst, $srcR, 'Pixel'); $wb.Dispose()
  $g.DrawString("WDI $($p[0]) / van. $($p[1])", $font, [System.Drawing.Brushes]::Black, ($i * $cw + 4), 4)
  $sx = $cw / 400.0; $sy = 360 / 480.0
  $zones = @{}
  foreach ($q in $W) {
    $v = $vb[$q.Name]; if (-not $v -or $q.X -lt 0 -or $v.X -lt 0) { continue }
    $dx = ($q.X - $v.X) / 4.0; $dy = ($q.Y - $v.Y) / 4.0
    $sure = if ($q.Status -eq 'detected' -and $v.Status -eq 'detected') { 'both detected' } elseif ($q.Status -eq 'detected' -or $v.Status -eq 'detected') { 'one placed' } else { 'both placed' }
    $L.Add(('{0}|{1}|{2}|{3}|vanilla {4:0},{5:0}|WDI {6:0},{7:0}|dx {8:+0.0;-0.0;0.0}|dy {9:+0.0;-0.0;0.0}|{10}' -f $facing, "$($p[0])/$($p[1])", $q.Zone, $q.Name, ($v.X/4), ($v.Y/4), ($q.X/4), ($q.Y/4), $dx, $dy, $sure))
    # zone moves from points detected on both bodies only: a vanilla point 'to place' is a share of the height, not a mark of the art
    if ($q.Zone -ne 'extremes' -and $q.Zone -ne 'axis' -and $sure -eq 'both detected') { if (-not $zones[$q.Zone]) { $zones[$q.Zone] = New-Object System.Collections.Generic.List[object] }; $zones[$q.Zone].Add(@($q, $v, $dx, $dy, $sure)) }
    $x0 = $i * $cw + ($v.X - 56) * $sx; $y0 = ($v.Y - 90) * $sy; $x1 = $i * $cw + ($q.X - 56) * $sx; $y1 = ($q.Y - 90) * $sy
    $g.FillEllipse([System.Drawing.Brushes]::Blue, [float]($x0 - 2), [float]($y0 - 2), 4, 4)
    if ([Math]::Abs($x1 - $x0) + [Math]::Abs($y1 - $y0) -gt 1.5) { $g.DrawLine($pen, [float]$x0, [float]$y0, [float]$x1, [float]$y1) }
  }
  foreach ($zn in $zones.Keys) {
    $e = $zones[$zn]; $dys = $e | % { $_[3] }; $mdy = ($dys | Measure-Object -Average).Average; $spread = ($dys | Measure-Object -Maximum).Maximum - ($dys | Measure-Object -Minimum).Minimum
    $n = $e.Count; $sure = ($e | ? { $_[4] -eq 'both detected' }).Count
    if ($facing -eq 'east') {
      # side view: front points move with dx>0 = further forward, back points dx<0 = further back
      $fr = @(); $bk = @(); foreach ($a in $e) { if ($a[0].Name -match 'front|apex') { $fr += $a[2] } elseif ($a[0].Name -match 'back') { $bk += $a[2] } }
      $fdx = if ($fr.Count) { ($fr | Measure-Object -Average).Average } else { 0 }; $bdx = if ($bk.Count) { ($bk | Measure-Object -Average).Average } else { 0 }
      $act = @(); if ([Math]::Abs($mdy) -gt 1) { $act += ('move {0} {1:0.#} px' -f $(if ($mdy -gt 0) { 'down' } else { 'up' }), [Math]::Abs($mdy)) }
      if ([Math]::Abs($fdx) -gt 1) { $act += ('front {0} {1:0.#} px' -f $(if ($fdx -gt 0) { 'out' } else { 'in' }), [Math]::Abs($fdx)) }
      if ([Math]::Abs($bdx) -gt 1) { $act += ('back {0} {1:0.#} px' -f $(if ($bdx -lt 0) { 'out' } else { 'in' }), [Math]::Abs($bdx)) }
      if ($spread -gt 2) { $act += "stretch (zone spread $spread px)" }
      $Z.Add(('{0}|{1}|{2}|dy {3:+0.0;-0.0;0.0}|front dx {4:+0.0;-0.0;0.0}|back dx {5:+0.0;-0.0;0.0}|spread {6:0.0}|{7}/{8} both detected|{9}' -f $facing, "$($p[0])/$($p[1])", $zn, $mdy, $fdx, $bdx, $spread, $sure, $n, $(if ($act) { $act -join ', ' } else { 'nothing (within 1 px)' })))
    } else {
      # front and back views: width ratio from the L/R pairs, half-widths about x=256
      $rs = @(); foreach ($a in $e) { if ($a[0].Name -match ' L$') { $hv = [Math]::Abs($a[1].X - 256); $hw = [Math]::Abs($a[0].X - 256); $r = $e | ? { $_[0].Name -eq ($a[0].Name -replace ' L$', ' R') }; if ($r) { $hv = ($hv + [Math]::Abs($r[1].X - 256)) / 2; $hw = ($hw + [Math]::Abs($r[0].X - 256)) / 2 }; if ($hv -gt 8) { $rs += $hw / $hv } } }
      $wr = if ($rs) { ($rs | Measure-Object -Average).Average } else { 1 }
      $act = @(); if ([Math]::Abs($mdy) -gt 1) { $act += ('move {0} {1:0.#} px' -f $(if ($mdy -gt 0) { 'down' } else { 'up' }), [Math]::Abs($mdy)) }
      if ([Math]::Abs($wr - 1) -gt 0.04) { $act += ('{0} {1:0} %' -f $(if ($wr -lt 1) { 'narrow' } else { 'widen' }), [Math]::Abs(100 * ($wr - 1))) }
      if ($spread -gt 2) { $act += "stretch (zone spread $spread px)" }
      $Z.Add(('{0}|{1}|{2}|dy {3:+0.0;-0.0;0.0}|width x{4:0.00}|spread {5:0.0}|{6}/{7} both detected|{8}' -f $facing, "$($p[0])/$($p[1])", $zn, $mdy, $wr, $spread, $sure, $n, $(if ($act) { $act -join ', ' } else { 'nothing (within 1 px / 4 %)' })))
    }
  }
  $i++ }
$g.DrawString('blue = vanilla point, red arrow = to the WDI point', $font, [System.Drawing.Brushes]::Black, 4, 340)
$g.Dispose(); $sh.Save($out + "delta-$facing.png", [System.Drawing.Imaging.ImageFormat]::Png); $sh.Dispose()
$L | Set-Content -Encoding UTF8 ($out + "delta-$facing-points.txt"); $Z | Set-Content -Encoding UTF8 ($out + "delta-$facing-zones.txt")
$Z
