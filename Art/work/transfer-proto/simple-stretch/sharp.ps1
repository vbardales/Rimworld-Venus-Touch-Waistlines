# Sharpness check: step 4 of the simple stretch, bilinear against nearest, 4x crops of the collar and of the hem (Male south).
param([string]$Body = 'Male', [string]$Facing = 'south')
Add-Type -AssemblyName System.Drawing
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\simple-stretch'
function Tint([System.Drawing.Bitmap]$b) {
    $o = New-Object System.Drawing.Bitmap $b.Width, $b.Height
    for ($y = 0; $y -lt $b.Height; $y++) { for ($x = 0; $x -lt $b.Width; $x++) {
        $c = $b.GetPixel($x, $y)
        if ($c.A -gt 0) { $o.SetPixel($x, $y, [System.Drawing.Color]::FromArgb($c.A, [int]($c.R * 120 / 255), [int]($c.G * 170 / 255), [int]($c.B * 235 / 255))) }
    } }
    $o
}
$a = Tint (New-Object System.Drawing.Bitmap "$d\${Body}_${Facing}_step4.png")
$n = Tint (New-Object System.Drawing.Bitmap "$d\${Body}_${Facing}_near_step4.png")
$sc = 4
$regions = @(@{ Name = 'collar'; X = 190; Y = 188; W = 132; H = 80 }, @{ Name = 'buttons and hem'; X = 190; Y = 300; W = 132; H = 90 })
$cw = 132 * $sc; $out = New-Object System.Drawing.Bitmap (2 * $cw + 30), (80 * $sc + 90 * $sc + 80)
$g = [System.Drawing.Graphics]::FromImage($out); $g.Clear([System.Drawing.Color]::White)
$g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'
$f = New-Object System.Drawing.Font 'Segoe UI', 12, ([System.Drawing.FontStyle]::Bold)
$g.DrawString('bilinear (before)', $f, [System.Drawing.Brushes]::Black, 4, 2); $g.DrawString('nearest (crisp)', $f, [System.Drawing.Brushes]::Black, $cw + 30, 2)
$y = 30
foreach ($r in $regions) {
    $bg = [System.Drawing.Color]::FromArgb(88, 105, 88)
    foreach ($k in 0, 1) {
        $x0 = $k * ($cw + 30)
        $g.FillRectangle((New-Object System.Drawing.SolidBrush $bg), $x0, $y, $cw, $r.H * $sc)
        $src = if ($k -eq 0) { $a } else { $n }
        $g.DrawImage($src, (New-Object System.Drawing.Rectangle $x0, $y, $cw, ($r.H * $sc)), $r.X, $r.Y, $r.W, $r.H, [System.Drawing.GraphicsUnit]::Pixel)
    }
    $y += $r.H * $sc + 10
}
$dest = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-06_sharpness-bilinear-vs-nearest.png'
$out.Save($dest, [System.Drawing.Imaging.ImageFormat]::Png); $dest
