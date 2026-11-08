Add-Type -AssemblyName System.Drawing
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$rows = @(@('male','Male'),@('thin','Thin'),@('fat','Fat'),@('hulk','Hulk'),@('female','Female'),@('thin','Thin_Female'),@('fat','Fat_Female'),@('hulk','Hulk_Female'))
$cw = 300; $chh = 400; $lab = 22; $cols = 4; $s = 1
$sheet = New-Object System.Drawing.Bitmap ($cols*$cw), ($rows.Count*($chh+$lab))
$g = [System.Drawing.Graphics]::FromImage($sheet); $g.Clear([System.Drawing.Color]::FromArgb(176,172,156)); $g.InterpolationMode='NearestNeighbor'
$font = New-Object System.Drawing.Font 'Arial', 10, ([System.Drawing.FontStyle]::Bold)
$ri = 0
foreach ($r in $rows) {
  $sk = $r[0]; $tk = $r[1]; $y0 = $ri * ($chh + $lab)
  $items = @(@(($tmp + "vbody512_$sk.png"), ($tmp + "imo512_$sk.png"), "vanilla $sk + IMO shirt"), @(($wdi + "Naked_${tk}_south.png"), ($tmp + "s3_${tk}.png"), "WDI $tk, round 2"))
  $items += ,@(($wdi + "Naked_${tk}_south.png"), ($tmp + "s4_${tk}.png"), "WDI $tk, round 3")
  $items += ,@(($wdi + "Naked_${tk}_south.png"), $null, "WDI body alone")
  $c = 0
  foreach ($it in $items) {
    $px = $c * $cw; $g.DrawString($it[2], $font, [System.Drawing.Brushes]::Black, $px + 4, $y0 + 3)
    $b = [System.Drawing.Bitmap]::FromFile($it[0]); $dst = New-Object System.Drawing.Rectangle $px, ($y0 + $lab), $cw, $chh; $src = New-Object System.Drawing.Rectangle 106, 112, 300, 400
    $g.DrawImage($b, $dst, $src, 'Pixel'); $b.Dispose()
    if ($it[1]) { $m = [System.Drawing.Bitmap]::FromFile($it[1]); $g.DrawImage($m, $dst, $src, 'Pixel'); $m.Dispose() }
    $c++ }
  $ri++ }
$sheet.Save($tmp + 'step4-sheet.png', [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $sheet.Dispose(); 'ok'
