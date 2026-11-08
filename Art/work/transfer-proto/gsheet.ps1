param([string]$out = 'gsheet.png', [switch]$points, [string]$list = '', [switch]$core, [string]$facing = "south")
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
if ($points) { . ($tmp + 'lib.ps1'); Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing }
if ($points) { [Gl]::Facing = $facing }
Add-Type -AssemblyName System.Drawing
$v = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\1814987817\Textures\Things\Apparel\'
if ($list) { $gs = $list -split ',' } else { $gs = @('CasualTShirt','Blouse','TankTop','ShirtFleece','Tunic','SheriffShirt','ShirtandTie','Scrubs','ChefsUniform','Jumpsuit') }
$bs = @(@('male','Male'),@('thin','Thin'),@('fat','Fat'),@('hulk','Hulk'),@('female','Female'))
$cw = 220; $chh = 230; $lab = 16
$sheet = New-Object System.Drawing.Bitmap (120 + $bs.Count*$cw), ($gs.Count*$chh)
$g = [System.Drawing.Graphics]::FromImage($sheet); $g.Clear([System.Drawing.Color]::FromArgb(200,196,182)); $g.InterpolationMode = 'HighQualityBicubic'
$font = New-Object System.Drawing.Font 'Arial', 9, ([System.Drawing.FontStyle]::Bold)
$ri = 0
foreach ($gn in $gs) { $g.DrawString($gn, $font, [System.Drawing.Brushes]::Black, 4, $ri*$chh + 100); $ci = 0
  foreach ($b in $bs) {
    if ($core) { $gp = $tmp + "core17png\${gn}_$($b[1])_$facing.png"; if (-not (Test-Path $gp)) { $gp = $tmp + "core17png\${gn}_$($b[0])_$facing.png" }; $up = $tmp + "cg_${gn}_$($b[0])_$facing.png" } else { $gp = $v + "$gn\${gn}_$($b[1])_$facing.png"; $up = $tmp + "vg_${gn}_$($b[0])_$facing.png" }
    $s = New-Object System.Drawing.Bitmap $gp; $d = New-Object System.Drawing.Bitmap 512, 512; $gg = [System.Drawing.Graphics]::FromImage($d); $gg.InterpolationMode = $(if ($core) { 'NearestNeighbor' } else { 'HighQualityBicubic' }); $gg.PixelOffsetMode = 'Half'; $gg.DrawImage($s, 0, 0, 512, 512); $gg.Dispose(); $d.Save($up, [System.Drawing.Imaging.ImageFormat]::Png); $s.Dispose(); $d.Dispose()
    $dst = New-Object System.Drawing.Rectangle (120 + $ci*$cw), ($ri*$chh), $cw, $chh; $src = New-Object System.Drawing.Rectangle 56, 100, 400, 418
    $bb = [System.Drawing.Bitmap]::FromFile($tmp + "core17_512/Naked_$($b[1])_$facing.png"); $g.DrawImage($bb, $dst, $src, 'Pixel'); $bb.Dispose()
    $gb = [System.Drawing.Bitmap]::FromFile($up); $g.DrawImage($gb, $dst, $src, 'Pixel'); $gb.Dispose()
    if ($points) { $gpts = [Pts]::Garment($up, 15, ($tmp + "core17_512/Naked_$($b[1])_$facing.png")); $g.DrawString([Gl]::NeckKind, $font, [System.Drawing.Brushes]::DarkRed, (120 + $ci*$cw + 4), ($ri*$chh + 4)); foreach ($p in [Pts]::Garment($up, 15, ($tmp + "core17_512/Naked_$($b[1])_$facing.png"))) { $px = 120 + $ci*$cw + ($p.X - 56) * $cw / 400.0; $py = $ri*$chh + ($p.Y - 100) * $chh / 418.0; if ($p.X -lt 0) { continue }
        $br = if ($p.Name -like '*sleeve*') { [System.Drawing.Brushes]::Blue } elseif ($p.Name -like '*hem*') { [System.Drawing.Brushes]::OrangeRed } else { [System.Drawing.Brushes]::Red }
        $g.FillEllipse($br, [float]($px - 3), [float]($py - 3), 6, 6) } }
    $ci++ }
  $ri++ }
$sheet.Save($tmp + $out, [System.Drawing.Imaging.ImageFormat]::Png); $g.Dispose(); $sheet.Dispose(); 'ok'
