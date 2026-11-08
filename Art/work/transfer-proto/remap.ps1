Add-Type -AssemblyName System.Drawing
# Vanilla to WDI, vertical only (2026-11-04): piecewise-linear row map through four anchors per body (top, shoulder tip,
# under-breast fold, crotch), vanilla rows to WDI rows in 512 px. Above the top and below the crotch the offset is kept (the
# legs move as one block). Anchors: 2026-11-03_points delta-south-points (x4); crotch: vanilla measured on the bodies, WDI
# = midline crotch (Thin_F 385 agrees with FrontApexRise). Test on ShirtButton, the only shaped top WDI draws for women.
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing;
public static class Remap {
  public static Bitmap Rows(string src, int[] v, int[] w) {
    Bitmap s = new Bitmap(src); Bitmap o = new Bitmap(512, 512); double k = s.Height / 512.0;
    for (int Y = 0; Y < 512; Y++) {
      double y;
      if (Y <= w[0]) y = Y - w[0] + v[0];
      else if (Y >= w[w.Length - 1]) y = Y - w[w.Length - 1] + v[v.Length - 1];
      else { int i = 0; while (Y > w[i + 1]) i++; y = v[i] + (Y - w[i]) * (double)(v[i + 1] - v[i]) / (w[i + 1] - w[i]); }
      int sy = (int)Math.Floor(y * k); if (sy < 0 || sy >= s.Height) continue;
      for (int X = 0; X < 512; X++) o.SetPixel(X, Y, s.GetPixel((int)(X * k), sy));
    }
    s.Dispose(); return o; } }
'@
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\'
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-04_shirtbutton-vertical-remap.png'
#                     top        shoulder   under-breast  crotch
$map = [ordered]@{
  Thin_Female = @('thin',   @(180, 232, 256, 402), @(176, 248, 272, 385))
  Fat_Female  = @('fat',    @(160, 240, 272, 422), @(164, 244, 308, 398))
  Hulk_Female = @('hulk',   @(136, 236, 320, 464), @(200, 276, 324, 445))
  Female      = @('female', @(160, 236, 276, 418), @(180, 252, 288, 400)) }
$cell = 300; $bmp = New-Object System.Drawing.Bitmap (3 * $cell), (4 * $cell + 24); $g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90)); $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $f = New-Object System.Drawing.Font 'Arial', 10
$heads = 'vanilla tel quel', 'vanilla remappe', 'ShirtButton WDI'
for ($c = 0; $c -lt 3; $c++) { $g.DrawString($heads[$c], $f, [System.Drawing.Brushes]::Yellow, $c * $cell + 6, 4) }
function Draw($im, $x, $y) { $g.DrawImage($im, $x, $y, $cell, $cell) }
$r = 0
foreach ($tk in $map.Keys) { $m = $map[$tk]; $y0 = 24 + $r * $cell
  $body = New-Object System.Drawing.Bitmap ($wb + 'Bodies\Naked_' + $tk + '_south.png'); $v = New-Object System.Drawing.Bitmap ($film + 'shirtbutton-' + $m[0] + '-south\0000.png')
  $o = [Remap]::Rows(($film + 'shirtbutton-' + $m[0] + '-south\0000.png'), $m[1], $m[2]); $o.Save($tmp + 'remap_' + $tk + '.png')
  Draw $body 0 $y0; Draw $v 0 $y0; Draw $body $cell $y0; Draw $o $cell $y0
  $wp = $wb + 'Apparel\ShirtButton\ShirtButton_' + $tk + '_south.png'; if (Test-Path $wp) { $w = New-Object System.Drawing.Bitmap $wp; Draw $body (2 * $cell) $y0; Draw $w (2 * $cell) $y0; $w.Dispose() }
  $g.DrawString($tk, $f, [System.Drawing.Brushes]::White, 6, $y0 + 4); $body.Dispose(); $v.Dispose(); $o.Dispose(); $r++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
