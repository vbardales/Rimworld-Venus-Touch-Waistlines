# Vanilla to WDI, the whole chain (2026-11-04), ShirtButton south on the eight adult WDI bodies:
# 1. rows: piecewise-linear map through top, shoulder tip, under-breast fold, crotch (vanilla rows to WDI rows, 512 px);
#    top and crotch read on the bodies at the middle column, shoulder and under-breast from 2026-11-03_points (x4);
#    above the top and below the crotch the offset is kept (the legs move as one block);
# 2. width: on each row the garment keeps its margin over the vanilla body and is laid on the WDI body's silhouette;
# 3. Nav: cut at the pink line, navel..hem resized per column, hem stroke, taper (as navall.ps1).
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System; using System.Drawing;
public static class Remap3 {
  static byte[] A(string p, out Bitmap b512) { Bitmap s = new Bitmap(p); b512 = new Bitmap(512, 512); double k = s.Width / 512.0; byte[] a = new byte[512 * 512];
    for (int y = 0; y < 512; y++) for (int x = 0; x < 512; x++) { Color c = s.GetPixel((int)(x * k), (int)(y * k)); b512.SetPixel(x, y, c); a[y * 512 + x] = c.A; }
    s.Dispose(); return a; }
  static bool Ext(byte[] a, int y, out int l, out int r) { l = -1; r = -1; if (y < 0 || y > 511) return false;
    for (int x = 0; x < 512; x++) if (a[y * 512 + x] > 40) { if (l < 0) l = x; r = x; } return l >= 0; }
  static bool ExtNear(byte[] a, int y, out int l, out int r) { for (int dy = 0; dy < 512; dy++) { if (Ext(a, y - dy, out l, out r) || Ext(a, y + dy, out l, out r)) return true; } l = r = -1; return false; }
  public static int Bottom(string p) { Bitmap b; byte[] a = A(p, out b); b.Dispose(); int m = -1; for (int y = 0; y < 512; y++) for (int x = 0; x < 512; x++) if (a[y * 512 + x] > 40) m = y; return m; }
  public static int Top(string p) { Bitmap b; byte[] a = A(p, out b); b.Dispose(); for (int y = 0; y < 512; y++) if (a[y * 512 + 256] > 40) return y; return -1; }
  // crotch apex: up the middle columns from the bottom, through the gap or the dark seam between the legs, to the first light skin
  public static int Crotch(string p) { Bitmap b; byte[] a = A(p, out b); int best = 512;
    for (int x = 252; x <= 260; x++) { int y = 511; while (y >= 0 && a[y * 512 + x] <= 40) y--;
      while (y >= 0) { Color c = b.GetPixel(x, y); if (c.A > 40 && (c.R + c.G + c.B) / 3 > 110) break; y--; } if (y < best) best = y; }
    b.Dispose(); return best + 1; }
  public static string Run(string gar, string vBody, string wBody, int[] v, int[] w, string outP) {
    Bitmap gb, tmp, src = new Bitmap(gar); byte[] ga = A(gar, out gb), va = A(vBody, out tmp); tmp.Dispose(); byte[] wa = A(wBody, out tmp); tmp.Dispose();
    Bitmap o = new Bitmap(512, 512); int n = w.Length - 1;
    // per row: source row yf and the affine x map sx = sa * X + sb; then sa, sb and the target edges are smoothed over
    // nearby rows so that a garment edge jumping from one row to the next does not streak
    double[] YF = new double[512], TLs = new double[512], TRs = new double[512], SA = new double[512], SB = new double[512]; bool[] ok = new bool[512];
    for (int Y = 0; Y < 512; Y++) {
      double yf; if (Y <= w[0]) yf = Y - w[0] + v[0]; else if (Y >= w[n]) yf = Y - w[n] + v[n];
      else { int i = 0; while (Y > w[i + 1]) i++; yf = v[i] + (Y - w[i]) * (double)(v[i + 1] - v[i]) / (w[i + 1] - w[i]); }
      YF[Y] = yf; int y = (int)Math.Round(yf); int gL, gR, bL, bR, BL, BR; if (!Ext(ga, y, out gL, out gR)) continue;
      if (!ExtNear(va, y, out bL, out bR) || !ExtNear(wa, Y, out BL, out BR)) continue;
      double TL = BL - (bL - gL), TR = BR + (gR - bR); if (TR - TL < 2) continue;
      ok[Y] = true; TLs[Y] = TL; TRs[Y] = TR; SA[Y] = (gR - gL) / (TR - TL); SB[Y] = gL - TL * SA[Y]; }
    const int R = 6; double[] sa = new double[512], sb = new double[512], tl = new double[512], tr = new double[512];
    for (int Y = 0; Y < 512; Y++) { if (!ok[Y]) continue; double c = 0; for (int j = Math.Max(0, Y - R); j <= Math.Min(511, Y + R); j++) if (ok[j]) { c++; sa[Y] += SA[j]; sb[Y] += SB[j]; tl[Y] += TLs[j]; tr[Y] += TRs[j]; }
      sa[Y] /= c; sb[Y] /= c; tl[Y] /= c; tr[Y] /= c; }
    for (int Y = 0; Y < 512; Y++) { if (!ok[Y]) continue;
      for (int X = (int)Math.Ceiling(tl[Y]); X <= (int)Math.Floor(tr[Y]) && X < 512; X++) { if (X < 0) continue;
        o.SetPixel(X, Y, Bil(src, sa[Y] * X + sb[Y], YF[Y])); } }
    o.Save(outP); o.Dispose(); gb.Dispose(); src.Dispose(); return outP; }
  // bilinear sample of the source texture at a 512 px position, colours weighted by alpha
  static Color Bil(Bitmap s, double x512, double y512) { double k = s.Width / 512.0, fx = (x512 + 0.5) * k - 0.5, fy = (y512 + 0.5) * k - 0.5;
    int x0 = (int)Math.Floor(fx), y0 = (int)Math.Floor(fy); double tx = fx - x0, ty = fy - y0, a = 0, r = 0, g = 0, b = 0;
    for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++) { int xx = Math.Max(0, Math.Min(s.Width - 1, x0 + i)), yy = Math.Max(0, Math.Min(s.Height - 1, y0 + j));
      double wgt = (i == 0 ? 1 - tx : tx) * (j == 0 ? 1 - ty : ty); Color c = s.GetPixel(xx, yy); double wa = wgt * c.A; a += wa; r += wa * c.R; g += wa * c.G; b += wa * c.B; }
    if (a < 1) return Color.Transparent; return Color.FromArgb((int)Math.Min(255, a), (int)(r / a), (int)(g / a), (int)(b / a)); }
  // silhouette stroke redrawn along the new edge: every opaque pixel closer than S to the outside becomes the outline colour
  public static void Outline(string p, int S, int[] pink) { Bitmap b = new Bitmap(p); int[] d = new int[512 * 512]; var q = new System.Collections.Generic.Queue<int>();
    // outside = transparent pixels reached from the border (the neck hole is not outside: it keeps its own drawn line)
    bool[] tr = new bool[512 * 512]; for (int i = 0; i < tr.Length; i++) tr[i] = b.GetPixel(i % 512, i / 512).A <= 40;
    for (int i = 0; i < d.Length; i++) d[i] = int.MaxValue; var f = new System.Collections.Generic.Queue<int>();
    for (int i = 0; i < 512; i++) foreach (int s in new[] { i, 511 * 512 + i, i * 512, i * 512 + 511 }) if (tr[s] && d[s] != 0) { d[s] = 0; f.Enqueue(s); }
    while (f.Count > 0) { int i = f.Dequeue(); q.Enqueue(i); int x = i % 512, y = i / 512; foreach (int n in new[] { x > 0 ? i - 1 : -1, x < 511 ? i + 1 : -1, y > 0 ? i - 512 : -1, y < 511 ? i + 512 : -1 })
      if (n >= 0 && tr[n] && d[n] != 0) { d[n] = 0; f.Enqueue(n); } }
    while (q.Count > 0) { int i = q.Dequeue(), x = i % 512, y = i / 512; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx > 511 || ny > 511) continue; int n = ny * 512 + nx; if (d[n] > d[i] + 1) { d[n] = d[i] + 1; q.Enqueue(n); } } }
    for (int i = 0; i < d.Length; i++) if (!tr[i] && d[i] <= S && i / 512 < pink[i % 512] - 8) b.SetPixel(i % 512, i / 512, Color.FromArgb(255, 15, 15, 18));
    b.Save(p + ".tmp.png"); b.Dispose(); System.IO.File.Copy(p + ".tmp.png", p, true); System.IO.File.Delete(p + ".tmp.png"); } }
'@
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-shirtbutton-'
$vb = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\'
$uw = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\UWUnderwear\'
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-04_shirtbutton-chain-v4.png'
$nav = @{ Male = 365; Thin = 360; Fat = 345; Hulk = 400; Female = 347; Thin_Female = 346; Fat_Female = 339; Hulk_Female = 394 }
#            vanilla body, shoulder v/w, under-breast v/w (points file, 128 px)
$pts = [ordered]@{
  Male = @('male', 58, 63, 74, 80); Thin = @('thin', 58, 51, 64, 71); Fat = @('fat', 60, 60, 68, 81); Hulk = @('hulk', 59, 64, 80, 86)
  Female = @('female', 59, 63, 69, 72); Thin_Female = @('thin', 58, 62, 64, 68); Fat_Female = @('fat', 60, 61, 68, 77); Hulk_Female = @('hulk', 59, 69, 80, 81) }
$cell = 220; $bmp = New-Object System.Drawing.Bitmap (6 * $cell), (4 * $cell); $g = [System.Drawing.Graphics]::FromImage($bmp)
$g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90)); $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $f = New-Object System.Drawing.Font 'Arial', 9
function Draw($p, $x, $y) { $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $x, $y, $cell, $cell); $im.Dispose() }
$i = 0
foreach ($tk in $pts.Keys) { $p = $pts[$tk]; $k = $p[0]; $vbody = $vb + $k + '.png'; $body = $wb + 'Bodies\Naked_' + $tk + '_south.png'; $gar = $film + $k + '-south\0000.png'
  # v3 (Virginie 2026-11-05): whole garment moved as a block so its top meets the WDI top (collar and pecs kept 1:1);
  # then Nav squeezes only the band under the pecs (vanilla under-breast row, moved) down to the garment's own hem onto the pink line
  # v4 (Virginie: WDI pecs sit lower): collar band top..vanilla shoulder row kept 1:1 under the WDI top, collar..pecs stretched so the
  # under-breast lands on the WDI under-breast, then the band under it squeezed onto the pink line by Nav
  $vt = [Remap3]::Top($vbody); $wt = [Remap3]::Top($body); $ub = 4 * $p[4]; $off = $ub - 4 * $p[3]; $gb = [Remap3]::Bottom($gar)
  $v = @($vt, (4 * $p[1]), (4 * $p[3]), $gb); $w = @($wt, ($wt + 4 * $p[1] - $vt), $ub, [Math]::Min($gb + $off, 505))  # below the pecs, squeezed only if the move pushes the hem off the canvas
  $r1 = [Remap3]::Run($gar, $vbody, $body, $v, $w, ($tmp + 'c3a_' + $tk + '.png'))
  [Nav]::SetPink(($uw + 'boxers\boxers_' + $tk + '_south.png'), ($uw + 'panties\panties_' + $tk + '_south.png'), 512, 512)
  [Nav]::TAnchor = -1; [Nav]::HemPx = 4; [Nav]::TaperPx = 24; $o = $tmp + 'c3b_' + $tk + '.png'
  $r = [Nav]::Run($body, $r1, $body, $r1, $ub, $ub, $o); [Remap3]::Outline($o, 10, [Nav]::Pink); "$tk off=$off ub=$ub : $r"
  $x0 = ($i % 2) * 3 * $cell; $y0 = [Math]::Floor($i / 2) * $cell
  Draw $body $x0 $y0; Draw $gar $x0 $y0; Draw $body ($x0 + $cell) $y0; Draw $o ($x0 + $cell) $y0
  $wp = $wb + 'Apparel\ShirtButton\ShirtButton_' + $tk + '_south.png'; if (Test-Path $wp) { Draw $body ($x0 + 2 * $cell) $y0; Draw $wp ($x0 + 2 * $cell) $y0 }
  $g.DrawString("$tk : vanilla | chaine | WDI", $f, [System.Drawing.Brushes]::Yellow, $x0 + 4, $y0 + 2); $i++ }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out
