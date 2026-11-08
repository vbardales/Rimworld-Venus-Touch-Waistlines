# Simple stretch of a vanilla top garment onto a WDI body, steps 1 to 4 (Virginie 2026-11-06), no handling of the flats.
#   1 take the vanilla garment (128 px, as Core draws it)
#   2 cut it out: the vanilla black outline removed (the alpha eroded by the measured stroke width), cloth kept
#   3 stretch onto E: vertical map linear from the cloth top to E's top and from the hem to the pink line (+ D on the tail),
#     horizontal map per row from the cloth edges to E's edges at that row
#   4 redraw the edge, 4 px, inside, in TailorMade's colour (0.06 0.06 0.07)
# Inputs per body and facing: Art\work\core17\ShirtBasic_<shirt key>_<facing>.png, Art\work\transfer-proto\E_<Body>_<facing>.png,
# hemshift_<Body>_<facing>.txt (D, 512 values, px) and hemshift_<Body>_<facing>.pink.txt (pink line, 512 values, rows).
# Output: Art\work\transfer-proto\simple-stretch\<Body>_<facing>_step{2,3,4}.png (512 px RGBA) and boards in Art\work\captures.
param([string[]]$Bodies = @('Male'), [string]$Garment = 'ShirtBasic', [string]$Tag = 'male', [switch]$Nearest, [switch]$Pubis, [switch]$Cap, [switch]$Flats, [double]$Sigma = 36)
$ErrorActionPreference = 'Stop'
$Bodies = @($Bodies | ForEach-Object { $_ -split ',' })   # -File passes 'A,B' as one string
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
    // Crisp mode (Virginie 2026-11-06: the result must not be blurry): the nearest source pixel, no mixing of colours.
    public static bool Nearest;

    static void Sample(byte[] px, int w, int h, double x, double y, out double r, out double g, out double b, out double a)
    {
        if (Nearest)
        {
            int nx = Math.Max(0, Math.Min(w - 1, (int)Math.Floor(x))), ny = Math.Max(0, Math.Min(h - 1, (int)Math.Floor(y)));
            int q = (ny * w + nx) * 4;
            r = px[q]; g = px[q + 1]; b = px[q + 2]; a = px[q + 3] / 255.0;
            return;
        }
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

    // hemRow > 0: the vanilla hem goes to that WDI row (the pubis) instead of the pink line. spread: D acts as a displacement that grows
    // linearly from 0 at the cloth top to its full value at the hem (no squash of a short tail, nothing cropped).
    // lm (complex stretch, -Flats): groups of 5 numbers per landmark, at 512: vanilla x, vanilla y, WDI x, WDI y, use-x (1/0). Null = simple stretch.
    // The simple map (silhouette + navel band + D) is the base; each landmark adds the residual that makes the vanilla landmark land on its WDI
    // one (Gaussian-weighted blend, sigma Sigma px, fading to zero far from every landmark, at the E edge for x, at the top and at the hem for y).
    public static double Sigma = 36, W0 = 0.02;
    static double Smooth(double t) { t = Math.Max(0, Math.Min(1, t)); return t * t * (3 - 2 * t); }

    public static string Process(string shirtPath, string ePath, string dPath, string pinkPath, string outPrefix, double hemRow, bool spread, bool cap, double navelV, double navelW, double[] lm, out string info)
    {
        int sw, sh;
        byte[] shirt = Read(shirtPath, out sw, out sh);
        int ew, eh;
        byte[] eMask = Read(ePath, out ew, out eh);
        double[] D = Table(dPath), pink = Table(pinkPath);
        // cap: the hem never goes lower than the pubis row (Virginie 2026-11-06): D may only raise the line, never lower it.
        if (cap) for (int i = 0; i < D.Length; i++) if (D[i] > 0) D[i] = 0;

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
        // The reference hem: the median of the per-column bottoms over the central half of the cloth, not the bottom at the middle
        // column, which sits in the notch of the vanilla hem (first version: hem landed 21 px under the pink line, Male south).
        var colBottoms = new List<int>();
        {
            int xl = N, xr = -1;
            for (int x = 0; x < N; x++) for (int y = 0; y < N; y++) if (cloth512[(y * N + x) * 4 + 3] >= 128) { if (x < xl) xl = x; if (x > xr) xr = x; break; }
            int q0 = xl + (xr - xl) / 4, q1 = xr - (xr - xl) / 4;
            for (int x = q0; x <= q1; x++) for (int y = N - 1; y >= 0; y--) if (cloth512[(y * N + x) * 4 + 3] >= 128) { colBottoms.Add(y); break; }
        }
        colBottoms.Sort();
        int cBotMid = colBottoms.Count > 0 ? colBottoms[colBottoms.Count / 2] : cBot;
        // cap (Virginie 2026-11-06: the shirt never goes lower than the pubis point): the LOWEST point of the vanilla hem lands on the
        // pubis row, so no column can end under it, and D only raises the line.
        if (cap) cBotMid = cBot;
        double cW = cBotMid - 0.22 * (cBotMid - cTop);   // start of the tail, where D begins to act
        int eTop = N; for (int y = 0; y < N; y++) { bool any = false; for (int x = 0; x < N; x++) if (eMask[(y * N + x) * 4 + 3] >= 128) { any = true; break; } if (any) { eTop = y; break; } }
        double yb = hemRow > 0 ? hemRow : pink[mid];      // the hem, at the middle, lands on the pink line (or on the pubis row)
        double[] cL, cR, eL, eR;
        RowEdges(cloth512, N, N, out cL, out cR);
        RowEdges(eMask, N, N, out eL, out eR);

        // With the navel landmark (navelV on the vanilla body, navelW on the WDI one): top to navel, then navel to hem, two linear bands.
        Func<double, double> vmap = y => navelV > 0
            ? (y <= navelV ? eTop + (y - cTop) * (navelW - eTop) / (navelV - cTop) : navelW + (y - navelV) * (yb - navelW) / (cBotMid - navelV))
            : eTop + (y - cTop) * (yb - eTop) / (double)(cBotMid - cTop);
        // spread: D acts from the vanilla NAVEL to the hem (Virginie 2026-11-06: 'nombril à ourlet'); the navel is taken at 0.77 of the
        // cloth height (Male south: row 360 of cloth rows 192..411), the same fraction for every facing, an estimate.
        double yNavel = navelV > 0 ? navelV : cTop + 0.77 * (cBotMid - cTop);
        Func<double, double> wt = y => spread ? Math.Max(0.0, Math.Min(1.0, (y - yNavel) / (cBotMid - yNavel))) : Math.Max(0.0, Math.Min(1.0, (y - cW) / (cBotMid - cW)));

        // base inverse map: WDI row Y at column X -> cloth row (Y = vmap(y) + D[X] * wt(y), inverted by bisection)
        Func<int, int, double> baseY = (X, Y) =>
        {
            double d = D[X];
            double lo = cTop - 40, hi = cBot + 160;
            for (int it = 0; it < 24; it++) { double m = 0.5 * (lo + hi); if (vmap(m) + d * wt(m) < Y) lo = m; else hi = m; }
            return 0.5 * (lo + hi);
        };
        // base x: WDI column X on row Y -> cloth column at cloth row y (cloth edges onto E edges), NaN when a row has no width
        Func<int, int, double, double> baseX = (X, Y, y) =>
        {
            int yr = Math.Max(0, Math.Min(N - 1, (int)Math.Round(y)));
            int Yr = Math.Max(0, Math.Min(N - 1, Y));
            double el = eL[Yr], er = eR[Yr], cl = cL[yr], cr = cR[yr];
            if (er - el < 2 || cr - cl < 2) return double.NaN;
            return cl + (X - el) * (cr - cl) / (er - el);
        };
        int nl = lm == null ? 0 : lm.Length / 5;
        var lX = new double[nl]; var lY = new double[nl]; var rX = new double[nl]; var rY = new double[nl]; var lOk = new bool[nl];
        for (int i = 0; i < nl; i++)
        {
            double vx = lm[5 * i], vy = lm[5 * i + 1], wx = lm[5 * i + 2], wy = lm[5 * i + 3];
            int wxi = (int)Math.Round(wx), wyi = (int)Math.Round(wy);
            if (wxi < 0 || wxi >= N || wyi < 0 || wyi >= N) continue;
            double by = baseY(wxi, wyi); double bx = baseX(wxi, wyi, vy);   // x read on the cloth row the landmark ends on
            lX[i] = wx; lY[i] = wy; rY[i] = vy - by;
            rX[i] = lm[5 * i + 4] > 0 && !double.IsNaN(bx) ? vx - bx : 0;
            lOk[i] = true;
        }
        var stretched = new byte[N * N * 4];
        for (int X = 0; X < N; X++)
        {
            double d = D[X];
            for (int Y = 0; Y < N; Y++)
            {
                double y = baseY(X, Y);
                double fx = 0, fy = 0;
                if (nl > 0)
                {
                    double wsum = 0, sx = 0, sy = 0;
                    for (int i = 0; i < nl; i++)
                    {
                        if (!lOk[i]) continue;
                        double dx = X - lX[i], dy = Y - lY[i];
                        double wi = Math.Exp(-(dx * dx + dy * dy) / (2 * Sigma * Sigma));
                        wsum += wi; sx += wi * rX[i]; sy += wi * rY[i];
                    }
                    // zero-residual anchors along the E top and the hem curve keep the cloth top and the tail where the simple map put them
                    double aTop = Y - eTop, aHem = Y - (yb + d);
                    double den = wsum + W0 + 1.5 * Math.Exp(-(aTop * aTop) / (2 * 24.0 * 24.0)) + 1.0 * Math.Exp(-(aHem * aHem) / (2 * 30.0 * 30.0));
                    int Yc = Math.Max(0, Math.Min(N - 1, Y));
                    double tX = Smooth(Math.Min(X - eL[Yc], eR[Yc] - X) / 18.0);
                    double tY = Smooth((Y - eTop) / 12.0) * Smooth((yb + d - Y) / 50.0);
                    fx = sx / den * tX * tY; fy = sy / den * tY;
                }
                y += fy;
                if (y < cTop - 1 || y > cBot + 1) continue;
                double x = baseX(X, Y, y);
                if (double.IsNaN(x)) continue;
                x += fx;
                if (X < eL[Math.Max(0, Math.Min(N - 1, Y))] - 0.5 || X > eR[Math.Max(0, Math.Min(N - 1, Y))] + 0.5) continue;
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

    // landmark marks (WDI positions at 512): cyan square = x and y used, yellow = y only
    public static Bitmap Dots(double[] lm)
    {
        var px = new byte[N * N * 4];
        for (int i = 0; i < lm.Length / 5; i++)
        {
            int cx = (int)Math.Round(lm[5 * i + 2]), cy = (int)Math.Round(lm[5 * i + 3]); bool ux = lm[5 * i + 4] > 0;
            for (int dy = -3; dy <= 3; dy++) for (int dx = -3; dx <= 3; dx++)
            {
                int xx = cx + dx, yy = cy + dy; if (xx < 0 || yy < 0 || xx >= N || yy >= N) continue;
                bool ring = Math.Abs(dx) == 3 || Math.Abs(dy) == 3; if (!ring) continue;
                int p = (yy * N + xx) * 4; px[p] = (byte)(ux ? 0 : 255); px[p + 1] = (byte)(ux ? 255 : 230); px[p + 2] = (byte)(ux ? 255 : 0); px[p + 3] = 255;
            }
        }
        return ToBitmap(px, N, N);
    }

    public static Bitmap Layer(string path) { int w, h; var px = Read(path, out w, out h); return ToBitmap(px, w, h); }
    public static Bitmap Tinted(string path) { int w, h; var px = Read(path, out w, out h); for (int i = 0; i < px.Length; i += 4) { px[i] = (byte)(px[i] * 120 / 255); px[i + 1] = (byte)(px[i + 1] * 170 / 255); px[i + 2] = (byte)(px[i + 2] * 235 / 255); } return ToBitmap(px, w, h); }
    public static Bitmap EdgeFromFile(string path) { int w, h; var px = Read(path, out w, out h); return EdgeOf(px, w, h); }
    public static Bitmap CellOf(int size, Bitmap a, Bitmap b, Bitmap c) { return Cell(size, a, b, c); }
}
'@

[Simple]::Nearest = [bool]$Nearest
[Simple]::Sigma = $Sigma
$sfx0 = $(if ($Nearest) { '_near' } else { '' }) + $(if ($Pubis) { '_pub' } else { '' }) + $(if ($Cap) { 'cap' } else { '' })
$sfx = $sfx0 + $(if ($Flats) { '_flats' } else { '' })
# Landmarks read from Virginie's point files (Art\work\captures\2026-11-03_points\delta-<facing>-points.txt, units of a 128 px picture,
# x4 here). The files say 'vanilla x,y' and 'WDI x,y' for every body (Thin_Female/Thin = the WDI body over the vanilla body).
#   navel  : south 'navel'; north 'waist L'; east 'waist front'          -> (vanilla row, WDI row)
#   pubis  : south 'sex' (WDI row); north 'crotch point' (WDI row); east has no such point: the WDI 'bottom' row minus the distance
#            between the south 'crotch point' and 'sex' of the same body (Male: 424 - 16 = 408)
$pointsDir = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points'
$pts = @{}; $pts4 = @{}
# Complex stretch (-Flats): landmarks that become displacement points. 'xy' = interior points, both coordinates used; 'y' = body outline
# points (shoulder tips, armpits, waist, hips, neck), only the row used, the silhouette already stretches the columns.
$lmNames = @{
    south = @{ xy = @('breast apex L', 'breast apex R', 'cleavage', 'under-breast fold L', 'under-breast fold R', 'jugular notch', 'navel'); y = @('shoulder tip L', 'shoulder tip R', 'armpit L', 'armpit R', 'waist L', 'waist R', 'hip L', 'hip R', 'neck base L', 'neck base R') }
    north = @{ xy = @(); y = @('shoulder tip L', 'shoulder tip R', 'armpit L', 'armpit R', 'waist L', 'waist R', 'hip L', 'hip R', 'neck base L', 'neck base R') }
    east  = @{ xy = @(); y = @('neck front', 'neck back', 'upper back (shoulder blade)', 'chest front', 'waist front', 'waist back (small of the back)', 'belly front') }
}
foreach ($fc in 'south', 'east', 'north') {
    foreach ($line in (Get-Content "$pointsDir\delta-$fc-points.txt" -Encoding UTF8)) {
        $p = $line.TrimStart([char]0xFEFF).Split('|')
        if ($p.Count -lt 5 -or $p[0] -ne $fc) { continue }
        if ($p[4] -notmatch 'vanilla (\d+),(\d+)') { continue }; $vx = [int]$Matches[1]; $vy = [int]$Matches[2]
        if ($p[5] -notmatch 'WDI (\d+),(\d+)') { continue }; $wx = [int]$Matches[1]; $wy = [int]$Matches[2]
        $bodyName = $p[1].Split('/')[0]
        $pts["$fc|$bodyName|$($p[3])"] = @(($vy * 4), ($wy * 4))
        $pts4["$fc|$bodyName|$($p[3])"] = @(($vx * 4), ($vy * 4), ($wx * 4), ($wy * 4))
    }
}
$pubisRow = @{}; $navelRows = @{}
foreach ($bn in 'Male', 'Female', 'Thin', 'Thin_Female', 'Fat', 'Fat_Female', 'Hulk', 'Hulk_Female') {
    $sSex = $pts["south|$bn|sex"]; $sCrotch = $pts["south|$bn|crotch point"]
    $pubisRow[$bn] = @{ south = $sSex[1]; north = $pts["north|$bn|crotch point"][1]; east = $pts["east|$bn|bottom"][1] - ($sCrotch[1] - $sSex[1]) }
    $navelRows[$bn] = @{ south = $pts["south|$bn|navel"]; north = $pts["north|$bn|waist L"]; east = $pts["east|$bn|waist front"] }
}
@{ pubis = $pubisRow; navel = $navelRows } | ConvertTo-Json -Depth 5 | Set-Content 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\simple-stretch\landmarks_used.json' -Encoding UTF8
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
        $gp = if ($Garment -ne 'ShirtBasic') { "${Garment}_" } else { '' }
        $prefix = "$out\$gp${b}_$f$sfx"
        $info = ''
        $hemRow = 0.0
        if ($Pubis -and $pubisRow.ContainsKey($b)) { $hemRow = [double]$pubisRow[$b][$f] }
        $nv = 0.0; $nw = 0.0
        if ($Pubis -and $navelRows.ContainsKey($b)) { $nv = [double]$navelRows[$b][$f][0]; $nw = [double]$navelRows[$b][$f][1] }
        $lmArr = $null
        if ($Flats) {
            $list = New-Object 'System.Collections.Generic.List[double]'
            foreach ($kind in 'xy', 'y') {
                foreach ($nm in $lmNames[$f][$kind]) {
                    $q = $pts4["$f|$b|$nm"]; if (-not $q) { continue }
                    foreach ($v in $q) { $list.Add([double]$v) }; $list.Add($(if ($kind -eq 'xy') { 1.0 } else { 0.0 }))
                }
            }
            $lmArr = [double[]]$list.ToArray()
        }
        $null = [Simple]::Process("$core\${Garment}_${key}_$f.png", "$proto\E_${b}_$f.png", "$proto\hemshift_${b}_$f.txt", "$proto\hemshift_${b}_$f.pink.txt", $prefix, $hemRow, [bool]$Pubis, [bool]$Cap, $nv, $nw, $lmArr, [ref]$info)
        "$b $f : $info" + $(if ($Flats) { " ; $($lmArr.Length / 5) landmarks" } else { '' })
        $body = [Simple]::Layer("$WS\3527486510\Textures\Things\Pawn\Humanlike\Bodies\Naked_${b}_$f.png")
        $c1 = [Simple]::CellOf($size, [Simple]::Tinted("$core\${Garment}_${key}_$f.png"), $null, $null)
        if ($Flats) {
            # second column: the simple stretch of the same run (without -Flats), over the body, for the comparison
            $c2 = [Simple]::CellOf($size, $body, [Simple]::Tinted("$out\$gp${b}_$f${sfx0}_step4.png"), $null)
            $c3 = [Simple]::CellOf($size, $body, [Simple]::Tinted("${prefix}_step3.png"), [Simple]::Dots($lmArr))
        } else {
            $c2 = [Simple]::CellOf($size, [Simple]::Tinted("${prefix}_step2.png"), $null, $null)
            $c3 = [Simple]::CellOf($size, $body, [Simple]::Tinted("${prefix}_step3.png"), [Simple]::EdgeFromFile("$proto\E_${b}_$f.png"))
        }
        $c4 = [Simple]::CellOf($size, $body, [Simple]::Tinted("${prefix}_step4.png"), $null)
        $rows.Add([System.Drawing.Bitmap[]]@($c1, $c2, $c3, $c4))
        $rowLabels += "$b $f"
    }
}
$heads = [string[]]@('1 vanilla garment (128 px)', '2 outline removed (cloth = alpha eroded by the measured stroke)', '3 stretched onto E (red = E edge), D on the tail, over the WDI body', '4 + 4 px edge inside, smoothed, over the WDI body')
if ($Flats) { $heads = [string[]]@('1 vanilla garment (128 px)', 'SIMPLE stretch, step 4, over the WDI body (same run, no flats)', ('COMPLEX step 3: simple map + landmark displacement (sigma ' + $Sigma + '); cyan = x and y used, yellow = y only'), 'COMPLEX step 4, edge 4 px, over the WDI body') }
[Simple]::Board("$capt\2026-11-06_simple-stretch-$Tag.png", $(if ($Flats) { "Complex stretch (landmark displacement), $Garment, $($Bodies -join ', ')" } else { "Simple stretch, $Garment, $($Bodies -join ', ')" }), $heads, [string[]]$rowLabels, $rows, $size)
"$capt\2026-11-06_simple-stretch-$Tag.png"

