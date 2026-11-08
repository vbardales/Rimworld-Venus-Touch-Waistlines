# Simple stretch of a vanilla top garment onto a WDI body, steps 1 to 4 (Virginie 2026-11-06), no handling of the flats.
#   1 take the vanilla garment (128 px, as Core draws it)
#   2 cut it out: the vanilla black outline removed (the alpha eroded by the measured stroke width), cloth kept
#   3 stretch onto E: vertical map linear from the cloth top to E's top and from the hem to the pink line (+ D on the tail),
#     horizontal map per row from the cloth edges to E's edges at that row
#   4 redraw the edge, 4 px, inside, in TailorMade's colour (0.06 0.06 0.07)
# Inputs per body and facing: Art\work\core17\ShirtBasic_<shirt key>_<facing>.png, Art\work\transfer-proto\E_<Body>_<facing>.png,
# hemshift_<Body>_<facing>.txt (D, 512 values, px) and hemshift_<Body>_<facing>.pink.txt (pink line, 512 values, rows).
# Output: Art\work\transfer-proto\simple-stretch\<Body>_<facing>_step{2,3,4}.png (512 px RGBA) and boards in Art\work\captures.
param([string[]]$Bodies = @('Male'), [string]$Garment = 'ShirtBasic', [string]$Tag = 'male')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing, PresentationCore, WindowsBase, System.Xaml
Add-Type -ReferencedAssemblies System.Drawing, PresentationCore, WindowsBase, System.Xaml -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;

public static class Simple
{
    public const int N = 512;

    public static byte[] Read(string path, out int w, out int h)
    {
        var dec = new System.Windows.Media.Imaging.PngBitmapDecoder(new Uri(path), System.Windows.Media.Imaging.BitmapCreateOptions.PreservePixelFormat, System.Windows.Media.Imaging.BitmapCacheOption.OnLoad);
        var src = new System.Windows.Media.Imaging.FormatConvertedBitmap(dec.Frames[0], System.Windows.Media.PixelFormats.Bgra32, null, 0);
        w = src.PixelWidth; h = src.PixelHeight;
        var bgra = new byte[w * h * 4];
        src.CopyPixels(bgra, w * 4, 0);
        var rgba = new byte[bgra.Length];
        for (int i = 0; i < bgra.Length; i += 4) { rgba[i] = bgra[i + 2]; rgba[i + 1] = bgra[i + 1]; rgba[i + 2] = bgra[i]; rgba[i + 3] = bgra[i + 3]; }
        return rgba;
    }

    public static Bitmap ToBitmap(byte[] rgba, int w, int h)
    {
        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var bgra = new byte[rgba.Length];
        for (int i = 0; i < rgba.Length; i += 4) { bgra[i] = rgba[i + 2]; bgra[i + 1] = rgba[i + 1]; bgra[i + 2] = rgba[i]; bgra[i + 3] = rgba[i + 3]; }
        var d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        System.Runtime.InteropServices.Marshal.Copy(bgra, 0, d.Scan0, bgra.Length);
        bmp.UnlockBits(d);
        return bmp;
    }

    public static void Save(byte[] rgba, int w, int h, string path) { using (var b = ToBitmap(rgba, w, h)) b.Save(path, ImageFormat.Png); }

    public static double[] Table(string path)
    {
        var parts = File.ReadAllText(path).Trim().Split(';');
        var v = new double[parts.Length];
        for (int i = 0; i < v.Length; i++) v[i] = double.Parse(parts[i], CultureInfo.InvariantCulture);
        return v;
    }

    static bool[] Erode(bool[] m, int w, int h, int d)
    {
        var e = new bool[w * h];
        for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                if (!m[y * w + x]) continue;
                bool ok = true;
                for (int dy = -d; dy <= d && ok; dy++)
                    for (int dx = -d; dx <= d; dx++)
                    {
                        if (dx * dx + dy * dy > d * d) continue;
                        int xx = x + dx, yy = y + dy;
                        if (xx < 0 || xx >= w || yy < 0 || yy >= h || !m[yy * w + xx]) { ok = false; break; }
                    }
                e[y * w + x] = ok;
            }
        return e;
    }

    static bool[] SmoothMask(bool[] m0, int w, int h, double sigma)
    {
        var f = new double[w * h];
        for (int i = 0; i < f.Length; i++) f[i] = m0[i] ? 1.0 : 0.0;
        int r = (int)Math.Ceiling(sigma * 3);
        var k = new double[2 * r + 1]; double sum = 0;
        for (int i = -r; i <= r; i++) { k[i + r] = Math.Exp(-i * i / (2 * sigma * sigma)); sum += k[i + r]; }
        for (int i = 0; i < k.Length; i++) k[i] /= sum;
        var t = new double[w * h]; var o = new double[w * h];
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { double s = 0; for (int i = -r; i <= r; i++) s += k[i + r] * f[y * w + Math.Max(0, Math.Min(w - 1, x + i))]; t[y * w + x] = s; }
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { double s = 0; for (int i = -r; i <= r; i++) s += k[i + r] * t[Math.Max(0, Math.Min(h - 1, y + i)) * w + x]; o[y * w + x] = s; }
        var m = new bool[w * h];
        for (int i = 0; i < m.Length; i++) m[i] = o[i] >= 0.5;
        return m;
    }

    // Median width, in px, of the dark outline met from the left edge of each row (alpha >= 128, luma < 80).
    static int StrokeWidth(byte[] px, int w, int h)
    {
        var runs = new List<int>();
        for (int y = 0; y < h; y++)
        {
            int x = 0; while (x < w && px[(y * w + x) * 4 + 3] < 128) x++;
            if (x >= w) continue;
            int n = 0;
            while (x < w)
            {
                int i = (y * w + x) * 4;
                if (px[i + 3] < 128 || (px[i] + px[i + 1] + px[i + 2]) / 3 >= 80) break;
                n++; x++;
            }
            if (n > 0) runs.Add(n);
        }
        if (runs.Count == 0) return 3;
        runs.Sort();
        return Math.Max(2, Math.Min(7, runs[runs.Count / 2]));
    }

    // Bilinear sample of premultiplied colour and alpha of a 512 px RGBA image at (x, y) in its own pixel centres.
    static void Sample(byte[] px, int w, int h, double x, double y, out double r, out double g, out double b, out double a)
    {
        double fx = x - 0.5, fy = y - 0.5;
        int x0 = (int)Math.Floor(fx), y0 = (int)Math.Floor(fy);
        double tx = fx - x0, ty = fy - y0;
        r = g = b = a = 0;
        for (int j = 0; j < 2; j++)
            for (int i = 0; i < 2; i++)
            {
                int xx = Math.Max(0, Math.Min(w - 1, x0 + i)), yy = Math.Max(0, Math.Min(h - 1, y0 + j));
                double wgt = (i == 0 ? 1 - tx : tx) * (j == 0 ? 1 - ty : ty);
                int p = (yy * w + xx) * 4;
                double al = px[p + 3] / 255.0;
                r += wgt * px[p] * al; g += wgt * px[p + 1] * al; b += wgt * px[p + 2] * al; a += wgt * al;
            }
        if (a > 1e-6) { r /= a; g /= a; b /= a; }
    }

    // Rows -> leftmost and rightmost solid column of a 512 mask (alpha >= 128), -1 when the row is empty; smoothed over +-2 rows.
    static void RowEdges(byte[] px, int w, int h, out double[] left, out double[] right)
    {
        var l = new double[h]; var r = new double[h];
        for (int y = 0; y < h; y++)
        {
            int a = -1, b = -1;
            for (int x = 0; x < w; x++) if (px[(y * w + x) * 4 + 3] >= 128) { if (a < 0) a = x; b = x; }
            l[y] = a; r[y] = b;
        }
        left = new double[h]; right = new double[h];
        for (int y = 0; y < h; y++)
        {
            double sl = 0, sr = 0; int n = 0;
            for (int j = -2; j <= 2; j++) { int q = Math.Max(0, Math.Min(h - 1, y + j)); if (l[q] >= 0) { sl += l[q]; sr += r[q]; n++; } }
            if (n > 0) { left[y] = sl / n; right[y] = sr / n; } else { left[y] = -1; right[y] = -1; }
        }
        // empty rows take the nearest row that has an edge
        for (int y = 0; y < h; y++) if (left[y] < 0) { int d = 1; while (d < h) { int q = y - d, p = y + d; if (q >= 0 && left[q] >= 0) { left[y] = left[q]; right[y] = right[q]; break; } if (p < h && left[p] >= 0) { left[y] = left[p]; right[y] = right[p]; break; } d++; } }
    }

    public static string Process(string shirtPath, string ePath, string dPath, string pinkPath, string outPrefix, out string info)
    {
        int sw, sh;
        byte[] shirt = Read(shirtPath, out sw, out sh);
        int ew, eh;
        byte[] eMask = Read(ePath, out ew, out eh);
        double[] D = Table(dPath), pink = Table(pinkPath);

        // step 2: cloth = shirt alpha eroded by the stroke width, then 512 px
        int stroke = StrokeWidth(shirt, sw, sh);
        var solid = new bool[sw * sh];
        for (int i = 0; i < solid.Length; i++) solid[i] = shirt[i * 4 + 3] >= 128;
        bool[] cloth = Erode(solid, sw, sh, stroke);
        var clothPx = new byte[sw * sh * 4];
        for (int i = 0; i < solid.Length; i++) { clothPx[i * 4] = shirt[i * 4]; clothPx[i * 4 + 1] = shirt[i * 4 + 1]; clothPx[i * 4 + 2] = shirt[i * 4 + 2]; clothPx[i * 4 + 3] = (byte)(cloth[i] ? 255 : 0); }
        var cloth512 = new byte[N * N * 4];
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                double r, g, b, a;
                Sample(clothPx, sw, sh, (x + 0.5) * sw / N, (y + 0.5) * sh / N, out r, out g, out b, out a);
                int p = (y * N + x) * 4;
                cloth512[p] = (byte)Math.Round(r); cloth512[p + 1] = (byte)Math.Round(g); cloth512[p + 2] = (byte)Math.Round(b); cloth512[p + 3] = (byte)Math.Round(a * 255);
            }
        Save(cloth512, N, N, outPrefix + "_step2.png");

        // landmarks of the cloth, at 512
        int cTop = N, cBot = -1;
        for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) if (cloth512[(y * N + x) * 4 + 3] >= 128) { if (y < cTop) cTop = y; if (y > cBot) cBot = y; }
        int mid = N / 2;
        int cBotMid = -1; for (int y = N - 1; y >= 0; y--) if (cloth512[(y * N + mid) * 4 + 3] >= 128) { cBotMid = y; break; }
        if (cBotMid < 0) cBotMid = cBot;
        double cW = cBotMid - 0.22 * (cBotMid - cTop);   // start of the tail, where D begins to act
        int eTop = N; for (int y = 0; y < N; y++) { bool any = false; for (int x = 0; x < N; x++) if (eMask[(y * N + x) * 4 + 3] >= 128) { any = true; break; } if (any) { eTop = y; break; } }
        double yb = pink[mid];                            // the hem, at the middle, lands on the pink line
        double[] cL, cR, eL, eR;
        RowEdges(cloth512, N, N, out cL, out cR);
        RowEdges(eMask, N, N, out eL, out eR);

        Func<double, double> vmap = y => eTop + (y - cTop) * (yb - eTop) / (double)(cBotMid - cTop);
        Func<double, double> wt = y => Math.Max(0.0, Math.Min(1.0, (y - cW) / (cBotMid - cW)));

        var stretched = new byte[N * N * 4];
        for (int X = 0; X < N; X++)
        {
            double d = D[X];
            for (int Y = 0; Y < N; Y++)
            {
                // invert Y = vmap(y) + D[X] * wt(y) by bisection on y
                double lo = cTop - 40, hi = cBot + 160;
                for (int it = 0; it < 24; it++) { double m = 0.5 * (lo + hi); if (vmap(m) + d * wt(m) < Y) lo = m; else hi = m; }
                double y = 0.5 * (lo + hi);
                if (y < cTop - 1 || y > cBot + 1) continue;
                int yr = Math.Max(0, Math.Min(N - 1, (int)Math.Round(y)));
                int Yr = Math.Max(0, Math.Min(N - 1, Y));
                double el = eL[Yr], er = eR[Yr], cl = cL[yr], cr = cR[yr];
                if (er - el < 2 || cr - cl < 2) continue;
                double x = cl + (X - el) * (cr - cl) / (er - el);
                if (X < el - 0.5 || X > er + 0.5) continue;
                double r, g, b, a;
                Sample(cloth512, N, N, x + 0.5, y + 0.5, out r, out g, out b, out a);
                int p = (Y * N + X) * 4;
                stretched[p] = (byte)Math.Round(r); stretched[p + 1] = (byte)Math.Round(g); stretched[p + 2] = (byte)Math.Round(b); stretched[p + 3] = (byte)Math.Round(a * 255);
            }
        }
        // clip to E
        for (int i = 0; i < N * N; i++) if (eMask[i * 4 + 3] < 128) stretched[i * 4 + 3] = 0;
        Save(stretched, N, N, outPrefix + "_step3.png");

        // step 4: smooth the alpha, then a 4 px edge inside, TailorMade's colour
        var m4 = new bool[N * N];
        for (int i = 0; i < m4.Length; i++) m4[i] = stretched[i * 4 + 3] >= 128;
        bool[] sm = SmoothMask(m4, N, N, 1.5);
        bool[] inner = Erode(sm, N, N, 4);
        var final = new byte[N * N * 4];
        for (int i = 0; i < N * N; i++)
        {
            if (!sm[i]) continue;
            if (!inner[i]) { final[i * 4] = 15; final[i * 4 + 1] = 15; final[i * 4 + 2] = 18; final[i * 4 + 3] = 255; }
            else
            {
                // colour from the stretched cloth, nearest solid one when this pixel was not solid there
                final[i * 4] = stretched[i * 4]; final[i * 4 + 1] = stretched[i * 4 + 1]; final[i * 4 + 2] = stretched[i * 4 + 2]; final[i * 4 + 3] = 255;
                if (stretched[i * 4 + 3] < 128) final[i * 4] = final[i * 4 + 1] = final[i * 4 + 2] = 200;
            }
        }
        Save(final, N, N, outPrefix + "_step4.png");
        info = "stroke " + stroke + " px (128), cloth rows " + cTop + ".." + cBotMid + " (512), E top " + eTop + ", hem to " + Math.Round(yb) + ", tail from " + Math.Round(cW);
        return outPrefix + "_step4.png";
    }

    // ------------------------------------------------------------------ boards
    static Bitmap Cell(int size, params Bitmap[] layers)
    {
        var cell = new Bitmap(size, size, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(cell))
        {
            g.Clear(Color.FromArgb(88, 105, 88));
            g.InterpolationMode = InterpolationMode.NearestNeighbor;
            g.PixelOffsetMode = PixelOffsetMode.Half;
            foreach (var l in layers) if (l != null) g.DrawImage(l, new Rectangle(0, 0, size, size), 0, 0, l.Width, l.Height, GraphicsUnit.Pixel);
        }
        return cell;
    }

    public static Bitmap EdgeOf(byte[] mask, int w, int h)
    {
        var m = new bool[w * h];
        for (int i = 0; i < m.Length; i++) m[i] = mask[i * 4 + 3] >= 128;
        bool[] e = Erode(m, w, h, 1);
        var px = new byte[w * h * 4];
        for (int i = 0; i < m.Length; i++) if (m[i] && !e[i]) { px[i * 4] = 255; px[i * 4 + 1] = 0; px[i * 4 + 2] = 0; px[i * 4 + 3] = 255; }
        return ToBitmap(px, w, h);
    }

    public static void Board(string dest, string title, string[] heads, string[] rowLabels, List<Bitmap[]> cells, int size)
    {
        int lw = 110, hh = 70, pad = 4;
        var bmp = new Bitmap(lw + heads.Length * (size + pad), 26 + hh + rowLabels.Length * (size + pad), PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(bmp))
        using (var big = new Font("Segoe UI", 12, FontStyle.Bold))
        using (var small = new Font("Segoe UI", 9))
        {
            g.Clear(Color.White);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;
            g.DrawString(title, big, Brushes.Black, 4, 2);
            for (int c = 0; c < heads.Length; c++) g.DrawString(heads[c], small, Brushes.Black, new RectangleF(lw + c * (size + pad), 26, size, hh));
            for (int r = 0; r < rowLabels.Length; r++)
            {
                g.DrawString(rowLabels[r], big, Brushes.Black, 4, 26 + hh + r * (size + pad) + size / 2 - 10);
                for (int c = 0; c < heads.Length; c++) if (cells[r][c] != null) g.DrawImage(cells[r][c], lw + c * (size + pad), 26 + hh + r * (size + pad), size, size);
            }
        }
        bmp.Save(dest, ImageFormat.Png);
    }

    public static Bitmap Layer(string path) { int w, h; var px = Read(path, out w, out h); return ToBitmap(px, w, h); }
    public static Bitmap EdgeFromFile(string path) { int w, h; var px = Read(path, out w, out h); return EdgeOf(px, w, h); }
    public static Bitmap CellOf(int size, Bitmap a, Bitmap b, Bitmap c) { return Cell(size, a, b, c); }
}
'@

$proto = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto'
$out = "$proto\simple-stretch"
$core = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17'
$capt = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures'
$WS = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100'
$facings = @('south', 'east', 'north')
$size = 256
$rows = New-Object 'System.Collections.Generic.List[System.Drawing.Bitmap[]]'
$rowLabels = @()
foreach ($b in $Bodies) {
    $key = if ($b -ne 'Female' -and $b.EndsWith('_Female')) { $b.Substring(0, $b.Length - 7) } else { $b }
    foreach ($f in $facings) {
        $prefix = "$out\${b}_$f"
        $info = ''
        $null = [Simple]::Process("$core\${Garment}_${key}_$f.png", "$proto\E_${b}_$f.png", "$proto\hemshift_${b}_$f.txt", "$proto\hemshift_${b}_$f.pink.txt", $prefix, [ref]$info)
        "$b $f : $info"
        $body = [Simple]::Layer("$WS\3527486510\Textures\Things\Pawn\Humanlike\Bodies\Naked_${b}_$f.png")
        $c1 = [Simple]::CellOf($size, [Simple]::Layer("$core\${Garment}_${key}_$f.png"), $null, $null)
        $c2 = [Simple]::CellOf($size, [Simple]::Layer("${prefix}_step2.png"), $null, $null)
        $c3 = [Simple]::CellOf($size, $body, [Simple]::Layer("${prefix}_step3.png"), [Simple]::EdgeFromFile("$proto\E_${b}_$f.png"))
        $c4 = [Simple]::CellOf($size, $body, [Simple]::Layer("${prefix}_step4.png"), $null)
        $rows.Add([System.Drawing.Bitmap[]]@($c1, $c2, $c3, $c4))
        $rowLabels += "$b $f"
    }
}
$heads = [string[]]@('1 vanilla garment (128 px)', '2 outline removed (cloth = alpha eroded by the measured stroke)', '3 stretched onto E (red = E edge), D on the tail, over the WDI body', '4 + 4 px edge inside, smoothed, over the WDI body')
[Simple]::Board("$capt\2026-11-06_simple-stretch-$Tag.png", "Simple stretch, $Garment, $($Bodies -join ', ')", $heads, [string[]]$rowLabels, $rows, $size)
"$capt\2026-11-06_simple-stretch-$Tag.png"
