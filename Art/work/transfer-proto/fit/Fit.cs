// Fit a vanilla top garment onto a WDI body with as little deformation as possible (Virginie 2026-11-06: the simple stretch is
// "totalement déformé"). Standalone C# (no PowerShell: the TM asked, hemmax.ps1 leaked handles).
//   step 2: cloth = garment alpha eroded by its measured outline width, 128 -> 512 bilinear
//   step 3: ONE uniform horizontal scale (sx) and ONE vertical scale (sy) for the whole garment, so the collar, the placket, the
//           buttons and the shading keep their shape; only a band along each side (about a fifth of the width) bends so the cloth
//           edge meets E's edge; vertical: cloth top -> E top, lowest cloth point -> pubis row, D raises the hem from the navel down
//   step 4: alpha smoothed (gaussian 1.5), 4 px edge inside in TailorMade's colour (15,15,18)
// Build: csc /r:System.Drawing.dll /r:<WPF>\PresentationCore.dll /r:<WPF>\WindowsBase.dll /r:System.Xaml.dll Fit.cs
// Run:   Fit.exe <Body,Body,...> <Garment> <tag>
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;

static class Fit
{
    const int N = 512;
    const string Mod = @"C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines";
    const string WS = @"C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies";
    static readonly string Proto = Mod + @"\Art\work\transfer-proto";
    static readonly string Core = Mod + @"\Art\work\core17";
    static readonly string Capt = Mod + @"\Art\work\captures";
    static readonly string Points = Capt + @"\2026-11-03_points";

    static byte[] Read(string path, out int w, out int h)
    {
        var dec = new System.Windows.Media.Imaging.PngBitmapDecoder(new Uri(path), System.Windows.Media.Imaging.BitmapCreateOptions.PreservePixelFormat, System.Windows.Media.Imaging.BitmapCacheOption.OnLoad);
        var src = new System.Windows.Media.Imaging.FormatConvertedBitmap(dec.Frames[0], System.Windows.Media.PixelFormats.Bgra32, null, 0);
        w = src.PixelWidth; h = src.PixelHeight;
        var bgra = new byte[w * h * 4]; src.CopyPixels(bgra, w * 4, 0);
        var rgba = new byte[bgra.Length];
        for (int i = 0; i < bgra.Length; i += 4) { rgba[i] = bgra[i + 2]; rgba[i + 1] = bgra[i + 1]; rgba[i + 2] = bgra[i]; rgba[i + 3] = bgra[i + 3]; }
        return rgba;
    }

    static Bitmap ToBitmap(byte[] rgba, int w, int h, bool tint = false)
    {
        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var bgra = new byte[rgba.Length];
        for (int i = 0; i < rgba.Length; i += 4)
        {
            int r = rgba[i], g = rgba[i + 1], b = rgba[i + 2];
            if (tint) { r = r * 120 / 255; g = g * 170 / 255; b = b * 235 / 255; }
            bgra[i] = (byte)b; bgra[i + 1] = (byte)g; bgra[i + 2] = (byte)r; bgra[i + 3] = rgba[i + 3];
        }
        var d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        System.Runtime.InteropServices.Marshal.Copy(bgra, 0, d.Scan0, bgra.Length);
        bmp.UnlockBits(d);
        return bmp;
    }

    static void Save(byte[] rgba, string path) { using (var b = ToBitmap(rgba, N, N)) b.Save(path, ImageFormat.Png); }

    static double[] Table(string path)
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

    static bool[] SmoothMask(bool[] m0, double sigma)
    {
        var f = new double[N * N];
        for (int i = 0; i < f.Length; i++) f[i] = m0[i] ? 1 : 0;
        int r = (int)Math.Ceiling(sigma * 3);
        var k = new double[2 * r + 1]; double sum = 0;
        for (int i = -r; i <= r; i++) { k[i + r] = Math.Exp(-i * i / (2 * sigma * sigma)); sum += k[i + r]; }
        for (int i = 0; i < k.Length; i++) k[i] /= sum;
        var t = new double[N * N]; var o = new double[N * N];
        for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) { double s = 0; for (int i = -r; i <= r; i++) s += k[i + r] * f[y * N + Math.Max(0, Math.Min(N - 1, x + i))]; t[y * N + x] = s; }
        for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) { double s = 0; for (int i = -r; i <= r; i++) s += k[i + r] * t[Math.Max(0, Math.Min(N - 1, y + i)) * N + x]; o[y * N + x] = s; }
        var m = new bool[N * N];
        for (int i = 0; i < m.Length; i++) m[i] = o[i] >= 0.5;
        return m;
    }

    static int StrokeWidth(byte[] px, int w, int h)
    {
        var runs = new List<int>();
        for (int y = 0; y < h; y++)
        {
            int x = 0; while (x < w && px[(y * w + x) * 4 + 3] < 128) x++;
            if (x >= w) continue;
            int n = 0;
            while (x < w) { int i = (y * w + x) * 4; if (px[i + 3] < 128 || (px[i] + px[i + 1] + px[i + 2]) / 3 >= 80) break; n++; x++; }
            if (n > 0) runs.Add(n);
        }
        if (runs.Count == 0) return 3;
        runs.Sort();
        return Math.Max(2, Math.Min(7, runs[runs.Count / 2]));
    }

    // bilinear sample (alpha-weighted colour) of a 512 RGBA image at pixel-centre coordinates
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
                int p = (yy * w + xx) * 4; double al = px[p + 3] / 255.0;
                r += wgt * px[p] * al; g += wgt * px[p + 1] * al; b += wgt * px[p + 2] * al; a += wgt * al;
            }
        if (a > 1e-6) { r /= a; g /= a; b /= a; }
    }

    // leftmost / rightmost solid column per row (alpha >= 128), smoothed over +-2 rows, -1 when empty
    static void RowEdges(byte[] px, out double[] left, out double[] right) { RowEdges(px, 2, out left, out right); }
    static void RowEdges(byte[] px, int R, out double[] left, out double[] right)
    {
        var l = new double[N]; var r = new double[N];
        for (int y = 0; y < N; y++)
        {
            int a = -1, b = -1;
            for (int x = 0; x < N; x++) if (px[(y * N + x) * 4 + 3] >= 128) { if (a < 0) a = x; b = x; }
            l[y] = a; r[y] = b;
        }
        left = new double[N]; right = new double[N];
        for (int y = 0; y < N; y++)
        {
            double sl = 0, sr = 0; int n = 0;
            for (int j = -R; j <= R; j++) { int q = Math.Max(0, Math.Min(N - 1, y + j)); if (l[q] >= 0) { sl += l[q]; sr += r[q]; n++; } }
            if (n > 0) { left[y] = sl / n; right[y] = sr / n; } else { left[y] = -1; right[y] = -1; }
        }
    }

    static double Median(List<double> v) { if (v.Count == 0) return double.NaN; v.Sort(); return v[v.Count / 2]; }

    // her point files, units of 128 px, x4: "facing|Body/VanillaBody|group|name|vanilla x,y|WDI x,y|..."
    static Dictionary<string, double[]> pts = new Dictionary<string, double[]>();
    static void LoadPoints()
    {
        foreach (var fc in new[] { "south", "east", "north" })
            foreach (var raw in File.ReadAllLines(Points + @"\delta-" + fc + "-points.txt"))
            {
                var p = raw.TrimStart('\uFEFF').Split('|');
                if (p.Length < 6 || p[0] != fc) continue;
                var v = p[4].Replace("vanilla ", "").Split(','); var w = p[5].Replace("WDI ", "").Split(',');
                if (v.Length != 2 || w.Length != 2) continue;
                int vx, vy, wx, wy;
                if (!int.TryParse(v[0], out vx) || !int.TryParse(v[1], out vy) || !int.TryParse(w[0], out wx) || !int.TryParse(w[1], out wy)) continue;
                pts[fc + "|" + p[1].Split('/')[0] + "|" + p[3]] = new double[] { vx * 4, vy * 4, wx * 4, wy * 4 };
            }
    }

    static double PubisRow(string b, string f)
    {
        if (f == "south") return pts["south|" + b + "|sex"][3];
        if (f == "north") return pts["north|" + b + "|crotch point"][3];
        return pts["east|" + b + "|bottom"][3] - (pts["south|" + b + "|crotch point"][3] - pts["south|" + b + "|sex"][3]);
    }

    static double NavelV(string b, string f)
    {
        string k = f == "south" ? "navel" : f == "north" ? "waist L" : "waist front";
        return pts[f + "|" + b + "|" + k][1];
    }

    public static string Info;
    public static double BandH = 0;
    public static bool Zone;
    public static double RadialK = 0;
    public static string Knots = "";

    static string Process(string garmentPath, string b, string f, string outPrefix)
    {
        int sw, sh;
        byte[] shirt = Read(garmentPath, out sw, out sh);
        int ew, eh;
        byte[] eMask = Read(Proto + @"\E_" + b + "_" + f + ".png", out ew, out eh);
        double[] D = Table(Proto + @"\hemshift_" + b + "_" + f + ".txt");
        for (int i = 0; i < D.Length; i++) if (D[i] > 0) D[i] = 0;    // the hem never goes under the pubis

        // step 2
        int stroke = StrokeWidth(shirt, sw, sh);
        var solid = new bool[sw * sh];
        for (int i = 0; i < solid.Length; i++) solid[i] = shirt[i * 4 + 3] >= 128;
        bool[] cl0 = Erode(solid, sw, sh, stroke);
        var clothPx = new byte[sw * sh * 4];
        for (int i = 0; i < solid.Length; i++) { clothPx[i * 4] = shirt[i * 4]; clothPx[i * 4 + 1] = shirt[i * 4 + 1]; clothPx[i * 4 + 2] = shirt[i * 4 + 2]; clothPx[i * 4 + 3] = (byte)(cl0[i] ? 255 : 0); }
        var cloth = new byte[N * N * 4];
        for (int y = 0; y < N; y++)
            for (int x = 0; x < N; x++)
            {
                double r, g, bb, a;
                Sample(clothPx, sw, sh, (x + 0.5) * sw / N, (y + 0.5) * sh / N, out r, out g, out bb, out a);
                int p = (y * N + x) * 4;
                cloth[p] = (byte)Math.Round(r); cloth[p + 1] = (byte)Math.Round(g); cloth[p + 2] = (byte)Math.Round(bb); cloth[p + 3] = (byte)Math.Round(a * 255);
            }
        int cTop = N, cBot = -1;
        for (int y = 0; y < N; y++) for (int x = 0; x < N; x++) if (cloth[(y * N + x) * 4 + 3] >= 128) { if (y < cTop) cTop = y; if (y > cBot) cBot = y; }
        double pubis = PubisRow(b, f), navelV = NavelV(b, f);
        // flat hem (the vanilla bottom is one line, it lands on the pubis then D bends it): under the navel each row keeps at least the
        // span of the row above, so the bias flap, its notch and the rounded corners are filled down to the lowest cloth row; a filled
        // pixel takes the colour of the pixel above it in its column
        int filled = 0, p0 = -1, p1 = -1;
        for (int y = (int)navelV; y <= cBot; y++)
        {
            int a0 = -1, a1 = -1;
            for (int x = 0; x < N; x++) if (cloth[(y * N + x) * 4 + 3] >= 128) { if (a0 < 0) a0 = x; a1 = x; }
            if (p0 >= 0 && (a0 < 0 || p0 < a0)) a0 = p0;
            if (p1 >= 0 && p1 > a1) a1 = p1;
            p0 = a0; p1 = a1;
            for (int x = a0; a0 >= 0 && x <= a1; x++)
            {
                int p = (y * N + x) * 4; if (cloth[p + 3] >= 128) continue;
                int q = p - N * 4; if (q < 0 || cloth[q + 3] < 128) continue;
                cloth[p] = cloth[q]; cloth[p + 1] = cloth[q + 1]; cloth[p + 2] = cloth[q + 2]; cloth[p + 3] = 255; filled++;
            }
        }
        // side view: no neck hole to keep, so every gap inside a row (the notch at the front under the collar tip, left by the outline
        // removal) is filled from the nearest solid pixel on its left (the back side)
        if (f == "east")
            for (int y = cTop; y <= cBot; y++)
            {
                int a0 = -1, a1 = -1;
                for (int x = 0; x < N; x++) if (cloth[(y * N + x) * 4 + 3] >= 128) { if (a0 < 0) a0 = x; a1 = x; }
                for (int x = a0 + 1; a0 >= 0 && x < a1; x++)
                {
                    int p = (y * N + x) * 4; if (cloth[p + 3] >= 128) continue;
                    int q = p - 4;
                    cloth[p] = cloth[q]; cloth[p + 1] = cloth[q + 1]; cloth[p + 2] = cloth[q + 2]; cloth[p + 3] = 255; filled++;
                }
            }
        Save(cloth, outPrefix + "_step2.png");
        int eTop = N;
        for (int y = 0; y < N && eTop == N; y++) for (int x = 0; x < N; x++) if (eMask[(y * N + x) * 4 + 3] >= 128) { eTop = y; break; }
        double[] cL, cR, eL, eR;
        RowEdges(cloth, 6, out cL, out cR);     // cloth edges smoothed over +-6 rows: the collar tips and the 128 px steps make them jagged
        RowEdges(eMask, 2, out eL, out eR);

        // one vertical scale: cloth top -> E top, lowest cloth point -> pubis row
        double sy = (pubis - eTop) / (double)(cBot - cTop);
        Func<double, double> vmap = y => eTop + (y - cTop) * sy;
        Func<double, double> wt = y => Math.Max(0.0, Math.Min(1.0, (y - navelV) / (cBot - navelV)));

        // one horizontal scale and one centre line, from the torso core (25 to 75 percent of the cloth height)
        var ratios = new List<double>(); var eMid = new List<double>(); var cMid = new List<double>();
        for (int y = cTop + (cBot - cTop) / 4; y <= cTop + 3 * (cBot - cTop) / 4; y++)
        {
            int Y = (int)Math.Round(vmap(y));
            if (Y < 0 || Y >= N || cL[y] < 0 || eL[Y] < 0) continue;
            double cw = cR[y] - cL[y], ewid = eR[Y] - eL[Y];
            if (cw < 4 || ewid < 4) continue;
            ratios.Add(ewid / cw); eMid.Add((eL[Y] + eR[Y]) / 2); cMid.Add((cL[y] + cR[y]) / 2);
        }
        double sxG = Median(ratios), EcG = Median(eMid), ccG = Median(cMid);
        // bands (Virginie 2026-11-06: 'limiter par bande ou par zone ?'): with BandH > 0 the scale and the two centre lines are no longer
        // one value for the whole garment but a per-row value averaged over a band of rows (gaussian, sigma BandH). BandH = 0: one value
        // (the global fit); BandH -> 1: every row its own (the simple stretch).
        var sxY = new double[N]; var EcY = new double[N]; var ccY = new double[N];
        for (int Y = 0; Y < N; Y++) { sxY[Y] = sxG; EcY[Y] = EcG; ccY[Y] = ccG; }
        if (BandH > 0)
        {
            var rS = new double[N]; var rE = new double[N]; var rC = new double[N]; var ok = new bool[N];
            for (int Y = 0; Y < N; Y++)
            {
                int y = (int)Math.Round(cTop + (Y - eTop) / sy);
                if (y < cTop || y > cBot || eL[Y] < 0 || cL[y] < 0) continue;
                double cw = cR[y] - cL[y], ewid = eR[Y] - eL[Y];
                if (cw < 4 || ewid < 4) continue;
                rS[Y] = ewid / cw; rE[Y] = (eL[Y] + eR[Y]) / 2; rC[Y] = (cL[y] + cR[y]) / 2; ok[Y] = true;
            }
            int R = (int)Math.Ceiling(3 * BandH);
            for (int Y = 0; Y < N; Y++)
            {
                double ws = 0, s = 0, e = 0, c = 0;
                for (int k = -R; k <= R; k++)
                {
                    int q = Y + k; if (q < 0 || q >= N || !ok[q]) continue;
                    double w = Math.Exp(-k * k / (2 * BandH * BandH));
                    ws += w; s += w * rS[q]; e += w * rE[q]; c += w * rC[q];
                }
                if (ws > 1e-6) { sxY[Y] = s / ws; EcY[Y] = e / ws; ccY[Y] = c / ws; }
            }
        }

        // ZONE mode (Virginie 2026-11-06, from her studies in captures/2026-11-03_points): the VANILLA BODY is mapped onto the WDI BODY
        // zone by zone and the garment follows. Vertical: piecewise linear through her landmark rows (delta-<facing>-points.txt, vanilla
        // row -> WDI row), each band between two landmarks with its own scale, the lowest cloth row landing on the pubis. Horizontal: in
        // each zone (between two landmark rows) the vanilla body's two edges (left/right, or back/front in the side view) averaged over
        // the zone go onto the WDI body's two averaged edges: one scale and one offset per zone, interpolated between zone centres.
        if (Zone)
        {
            string[] names = f == "south" ? new[] { "top", "jugular notch", "shoulder tip L", "breast apex L", "under-breast fold L", "waist L", "hip L", "navel" }
                : f == "north" ? new[] { "top", "neck base L", "shoulder tip L", "armpit L", "waist L", "hip L" }
                : new[] { "top", "upper back (shoulder blade)", "chest front", "belly front", "waist back (small of the back)", "waist front", "buttock back" };
            var cand = new List<double[]>();
            foreach (var nm in names) { double[] q; if (pts.TryGetValue(f + "|" + b + "|" + nm, out q)) cand.Add(new[] { q[1], q[3] }); }
            cand.Sort((u, v) => u[0].CompareTo(v[0]));
            var kv = new List<double>(); var kw = new List<double>();
            foreach (var c in cand)
            {
                if (c[0] >= cBot - 4 || c[1] >= pubis - 4) continue;
                if (kv.Count > 0 && (c[0] <= kv[kv.Count - 1] + 3 || c[1] <= kw[kw.Count - 1] + 3)) continue;   // keep both rows increasing
                // a band squashed or stretched more than x2 (side view: a front point next to a back point) drops the landmark
                if (kv.Count > 0) { double sl = (c[1] - kw[kw.Count - 1]) / (c[0] - kv[kv.Count - 1]); if (sl < 0.5 || sl > 2.0) continue; }
                kv.Add(c[0]); kw.Add(c[1]);
            }
            kv.Add(cBot); kw.Add(pubis);
            Knots = "";
            for (int k = 0; k < kv.Count; k++) Knots += kv[k] + "->" + kw[k] + (k + 1 < kv.Count ? string.Format(CultureInfo.InvariantCulture, " x{0:0.00} ", (kw[k + 1] - kw[k]) / (kv[k + 1] - kv[k])) : "");
            Func<List<double>, List<double>, double, double> pw = (ks, kt, t) =>
            {
                if (t <= ks[0]) return kt[0] + (t - ks[0]);
                int last = ks.Count - 1;
                if (t >= ks[last]) return kt[last] + (t - ks[last]) * (last > 0 ? (kt[last] - kt[last - 1]) / (ks[last] - ks[last - 1]) : 1);
                int i = 1; while (ks[i] < t) i++;
                return kt[i - 1] + (t - ks[i - 1]) * (kt[i] - kt[i - 1]) / (ks[i] - ks[i - 1]);
            };
            vmap = y => pw(kv, kw, y);
            Func<double, double> vinv = Y => pw(kw, kv, Y);

            // body edges: vanilla body (128 px, x4) and WDI body (512 px)
            string vb = b != "Female" && b.EndsWith("_Female") ? b.Substring(0, b.Length - 7) : b;
            int vw, vh;
            byte[] vBody = Read(Mod + @"\Art\work\vanilla\vanilla-" + vb.ToLowerInvariant() + "-" + f + ".png", out vw, out vh);
            var vL = new double[N]; var vR = new double[N];
            for (int y = 0; y < N; y++)
            {
                int sy0 = y * vh / N; int a0 = -1, a1 = -1;
                for (int x = 0; x < vw; x++) if (vBody[(sy0 * vw + x) * 4 + 3] >= 128) { if (a0 < 0) a0 = x; a1 = x; }
                vL[y] = a0 < 0 ? -1 : a0 * (double)N / vw; vR[y] = a1 < 0 ? -1 : (a1 + 1) * (double)N / vw;
            }
            int bw, bh;
            byte[] wBody = Read(WS + @"\Naked_" + b + "_" + f + ".png", out bw, out bh);
            double[] wL, wR; RowEdges(wBody, 2, out wL, out wR);
            int nz = kw.Count - 1;
            var zS = new double[nz]; var zO = new double[nz]; var zC = new double[nz]; var zOk = new bool[nz];
            for (int k = 0; k < nz; k++)
            {
                double a = 0, bR = 0, c = 0, dd = 0; int n = 0;
                for (int Y = (int)Math.Ceiling(kw[k]); Y < kw[k + 1]; Y++)
                {
                    int y = (int)Math.Round(vinv(Y));
                    if (Y < 0 || Y >= N || y < 0 || y >= N || vL[y] < 0 || wL[Y] < 0) continue;
                    a += vL[y]; bR += vR[y]; c += wL[Y]; dd += wR[Y]; n++;
                }
                zC[k] = (kw[k] + kw[k + 1]) / 2;
                if (n == 0 || bR - a < 4 * n) continue;
                a /= n; bR /= n; c /= n; dd /= n;
                zS[k] = (dd - c) / (bR - a); zO[k] = c - zS[k] * a; zOk[k] = true;
                Knots += string.Format(CultureInfo.InvariantCulture, " | zone {0}: x{1:0.00}", k, zS[k]);
            }
            var zi = new List<int>(); for (int k = 0; k < nz; k++) if (zOk[k]) zi.Add(k);
            for (int Y = 0; Y < N && zi.Count > 0; Y++)
            {
                double s, o;
                if (Y <= zC[zi[0]]) { s = zS[zi[0]]; o = zO[zi[0]]; }
                else if (Y >= zC[zi[zi.Count - 1]]) { s = zS[zi[zi.Count - 1]]; o = zO[zi[zi.Count - 1]]; }
                else
                {
                    int j = 1; while (zC[zi[j]] < Y) j++;
                    int k0 = zi[j - 1], k1 = zi[j]; double t = (Y - zC[k0]) / (zC[k1] - zC[k0]);
                    s = zS[k0] + t * (zS[k1] - zS[k0]); o = zO[k0] + t * (zO[k1] - zO[k0]);
                }
                sxY[Y] = s; EcY[Y] = o; ccY[Y] = 0;     // X = o + s * x
            }
        }

        // RADIAL (Virginie 2026-11-06, 'du radial ?'): around each volume of the WDI body (breasts or pecs, chest front, belly, buttocks)
        // the garment is pushed outward from a centre, a magnifying lens: inside radius R the sampling point is pulled towards the centre
        // by k (1 - r^2)^2, so the cloth there is enlarged and its edges move out; nothing changes at r >= R. Centres from her point files
        // (WDI positions); side-view edge points are moved inside the body by half a radius. k = RadialK for every volume (to tune).
        var bulges = new List<double[]>();
        if (RadialK > 0)
        {
            Func<string, double[]> P = nm => { double[] q; return pts.TryGetValue(f + "|" + b + "|" + nm, out q) ? q : null; };
            Func<double, double> widthAt = yy => { int r0 = Math.Max(0, Math.Min(N - 1, (int)yy)); return eL[r0] < 0 ? 100 : eR[r0] - eL[r0]; };
            if (f == "south")
            {
                foreach (var nm in new[] { "breast apex L", "breast apex R" }) { var q = P(nm); if (q != null) bulges.Add(new[] { q[2], q[3], 0.2 * widthAt(q[3]) }); }
                var nv = P("navel"); if (nv != null) bulges.Add(new[] { nv[2], nv[3] - 0.1 * widthAt(nv[3]), 0.3 * widthAt(nv[3]) });
            }
            else if (f == "east")
            {
                foreach (var nm in new[] { "chest front", "belly front" }) { var q = P(nm); if (q != null) { double R = 0.35 * widthAt(q[3]); bulges.Add(new[] { q[2] - 0.5 * R, q[3], R }); } }
                var bb0 = P("buttock back"); if (bb0 != null) { double R = 0.35 * widthAt(bb0[3]); bulges.Add(new[] { bb0[2] + 0.5 * R, bb0[3], R }); }
            }
            Knots += " | bulges " + bulges.Count;
        }

        var outPx = new byte[N * N * 4];
        for (int X0 = 0; X0 < N; X0++)
        {
            for (int Y0 = 0; Y0 < N; Y0++)
            {
                if (eMask[(Y0 * N + X0) * 4 + 3] < 128) continue;
                double Xf = X0, Yf = Y0;
                foreach (var bg in bulges)
                {
                    double dx = Xf - bg[0], dy = Yf - bg[1], r2 = (dx * dx + dy * dy) / (bg[2] * bg[2]);
                    if (r2 >= 1) continue;
                    double fct = 1 - RadialK * (1 - r2) * (1 - r2);
                    Xf = bg[0] + dx * fct; Yf = bg[1] + dy * fct;
                }
                int X = Math.Max(0, Math.Min(N - 1, (int)Math.Round(Xf))), Y = Math.Max(0, Math.Min(N - 1, (int)Math.Round(Yf)));
                double d = D[X];
                // invert Y = vmap(y) + d * wt(y)
                double lo = cTop - 60, hi = cBot + 60;
                for (int it = 0; it < 30; it++) { double m = 0.5 * (lo + hi); if (vmap(m) + d * wt(m) < Yf) lo = m; else hi = m; }
                double y = 0.5 * (lo + hi);
                if (y < cTop - 0.5 || y > cBot + 0.5) continue;
                int yr = Math.Max(0, Math.Min(N - 1, (int)Math.Round(y)));
                double el = eL[Y], er = eR[Y], cl = cL[yr], cr = cR[yr];
                if (el < 0 || cl < 0 || cr - cl < 2) continue;
                // the scaled cloth edges, in WDI columns
                double sx = sxY[Y], Ec = EcY[Y], cc = ccY[Y];
                double Lp = Ec + (cl - cc) * sx, Rp = Ec + (cr - cc) * sx;
                double B = Math.Max(12, Math.Min(48, 0.2 * (er - el)));
                double KL = Math.Max(el + B, Lp + 0.5 * B), KR = Math.Min(er - B, Rp - 0.5 * B);
                double Xp;
                if (KL >= KR)
                    Xp = Lp + (Xf - el) * (Rp - Lp) / Math.Max(1, er - el);       // too narrow for a core: plain edge map
                else if (Xf < KL)
                    Xp = Lp + (Xf - el) / (KL - el) * (KL - Lp);                    // left band bends
                else if (Xf > KR)
                    Xp = KR + (Xf - KR) / (er - KR) * (Rp - KR);                    // right band bends
                else
                    Xp = Xf;                                                        // core: uniform scale only
                double x = cc + (Xp - Ec) / sx;
                x = Math.Max(cl + 0.5, Math.Min(cr - 0.5, x));
                double r, g, bb, a;
                Sample(cloth, N, N, x + 0.5, y + 0.5, out r, out g, out bb, out a);
                int p = (Y0 * N + X0) * 4;
                outPx[p] = (byte)Math.Round(r); outPx[p + 1] = (byte)Math.Round(g); outPx[p + 2] = (byte)Math.Round(bb); outPx[p + 3] = (byte)Math.Round(a * 255);
            }
        }
        Save(outPx, outPrefix + "_step3.png");

        // step 4
        var m4 = new bool[N * N];
        for (int i = 0; i < m4.Length; i++) m4[i] = outPx[i * 4 + 3] >= 128;
        bool[] sm = SmoothMask(m4, 1.5);
        bool[] inner = Erode(sm, N, N, 4);
        var fin = new byte[N * N * 4];
        int grey = 0;
        for (int Y = 0; Y < N; Y++)
            for (int X = 0; X < N; X++)
            {
                int i = Y * N + X;
                if (!sm[i]) continue;
                if (!inner[i]) { fin[i * 4] = 15; fin[i * 4 + 1] = 15; fin[i * 4 + 2] = 18; fin[i * 4 + 3] = 255; continue; }
                int src = i;
                if (outPx[i * 4 + 3] < 128)
                {
                    src = -1;
                    for (int k = 1; k <= 8 && src < 0; k++)
                    {
                        if (X - k >= 0 && outPx[(i - k) * 4 + 3] >= 128) src = i - k;
                        else if (X + k < N && outPx[(i + k) * 4 + 3] >= 128) src = i + k;
                    }
                }
                if (src < 0) { fin[i * 4] = fin[i * 4 + 1] = fin[i * 4 + 2] = 200; grey++; }
                else { fin[i * 4] = outPx[src * 4]; fin[i * 4 + 1] = outPx[src * 4 + 1]; fin[i * 4 + 2] = outPx[src * 4 + 2]; }
                fin[i * 4 + 3] = 255;
            }
        Save(fin, outPrefix + "_step4.png");
        Info = string.Format(CultureInfo.InvariantCulture, "stroke {0}, cloth rows {1}..{2}, E top {3}, pubis {4}, sy {5:0.000}, sx {6:0.000}, centres {7:0.0} -> {8:0.0}, grey px {9}, notch px filled {10}",
            stroke, cTop, cBot, eTop, pubis, sy, sxG, ccG, EcG, grey, filled);
        return outPrefix + "_step4.png";
    }

    static Bitmap Cell(int size, params Bitmap[] layers)
    {
        var cell = new Bitmap(size, size, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(cell))
        {
            g.Clear(Color.FromArgb(88, 105, 88));
            g.InterpolationMode = InterpolationMode.NearestNeighbor; g.PixelOffsetMode = PixelOffsetMode.Half;
            // crop rows 140..460 and columns 96..416 of the 512 square so the torso fills the cell
            foreach (var l in layers) if (l != null) g.DrawImage(l, new Rectangle(0, 0, size, size), 96 * l.Width / 512f, 140 * l.Height / 512f, 320 * l.Width / 512f, 320 * l.Height / 512f, GraphicsUnit.Pixel);
        }
        return cell;
    }

    static Bitmap Load(string path, bool tint = false) { int w, h; var px = Read(path, out w, out h); return ToBitmap(px, w, h, tint); }

    static int Main(string[] args)
    {
        var bodies = (args.Length > 0 ? args[0] : "Male").Split(',');
        string garment = args.Length > 1 ? args[1] : "ShirtButton";
        string tag = args.Length > 2 ? args[2] : "male";
        var bands = (args.Length > 3 ? args[3] : "0").Split(',');
        var facings = (args.Length > 4 ? args[4] : "south,east,north").Split(',');
        LoadPoints();
        string outDir = Proto + @"\fit";
        string simpleDir = Proto + @"\simple-stretch";
        string gp = garment == "ShirtBasic" ? "" : garment + "_";
        int size = 300;
        var rows = new List<Bitmap[]>(); var labels = new List<string>();
        foreach (var b in bodies)
        {
            string vb = b != "Female" && b.EndsWith("_Female") ? b.Substring(0, b.Length - 7) : b;
            foreach (var f in facings)
            {
                string garmentPath = Core + @"\" + garment + "_" + vb + "_" + f + ".png";
                var body = Load(WS + @"\Naked_" + b + "_" + f + ".png");
                string simple = simpleDir + @"\" + gp + b + "_" + f + "_pubcap_step4.png";
                var cells = new List<Bitmap> { Cell(size, Load(garmentPath, true)), Cell(size, body, File.Exists(simple) ? Load(simple, true) : null) };
                foreach (var h in bands)
                {
                    // token: zone | 0 | <sigma>, optionally followed by R<k> (radial bulges of strength k); "wdi" = WDI's own drawing
                    if (h == "wdi")
                    {
                        string wdiPath = WS.Replace(@"\Bodies", @"\Apparel\" + garment + @"\" + garment + "_" + b + "_" + f + ".png");
                        cells.Add(File.Exists(wdiPath) ? Cell(size, body, Load(wdiPath, true)) : Cell(size));
                        continue;
                    }
                    string baseTok = h, rTok = "";
                    int ri = h.IndexOf('R'); if (ri >= 0) { baseTok = h.Substring(0, ri); rTok = h.Substring(ri + 1); }
                    Zone = baseTok == "zone"; Knots = "";
                    BandH = Zone ? 0 : double.Parse(baseTok, CultureInfo.InvariantCulture);
                    RadialK = rTok == "" ? 0 : double.Parse(rTok, CultureInfo.InvariantCulture);
                    string prefix = outDir + @"\" + gp + b + "_" + f + (Zone ? "_zone" : BandH > 0 ? "_band" + baseTok : "") + (RadialK > 0 ? "_r" + rTok : "");
                    Process(garmentPath, b, f, prefix);
                    Console.WriteLine(b + " " + f + " " + h + " : " + Info + " ; " + Knots);
                    cells.Add(Cell(size, body, Load(prefix + "_step4.png", true)));
                }
                rows.Add(cells.ToArray());
                labels.Add(b + " " + f);
            }
        }
        var headList = new List<string> { "1 vanilla " + garment + " (128 px)", "SIMPLE stretch (each row its own scale)" };
        foreach (var h in bands)
        {
            if (h == "wdi") { headList.Add("WDI's own " + garment + " drawn by its artist (only Thin_Female, Fat_Female, Hulk_Female)"); continue; }
            string bt = h, rk = ""; int ri = h.IndexOf('R'); if (ri >= 0) { bt = h.Substring(0, ri); rk = h.Substring(ri + 1); }
            string head = bt == "zone" ? "ZONE (one scale per zone between her landmark rows)" : bt == "0" ? "FIT (one scale for the whole garment)" : "FIT bands sigma " + bt;
            if (rk != "") head += " + RADIAL bulges k " + rk + " (breasts/pecs, belly; side: chest, belly, buttocks)";
            headList.Add(head);
        }
        var heads = headList.ToArray();
        int lw = 120, hh = 50, pad = 4;
        using (var bmp = new Bitmap(lw + heads.Length * (size + pad), 30 + hh + labels.Count * (size + pad), PixelFormat.Format32bppArgb))
        using (var g = Graphics.FromImage(bmp))
        using (var big = new Font("Segoe UI", 12, FontStyle.Bold))
        using (var small = new Font("Segoe UI", 9))
        {
            g.Clear(Color.White); g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;
            g.DrawString("Fit with little deformation, " + garment + ", " + string.Join(", ", bodies) + " (crop 320 px of 512)", big, Brushes.Black, 4, 4);
            for (int c = 0; c < heads.Length; c++) g.DrawString(heads[c], small, Brushes.Black, new RectangleF(lw + c * (size + pad), 30, size, hh));
            for (int r = 0; r < labels.Count; r++)
            {
                g.DrawString(labels[r], big, Brushes.Black, 4, 30 + hh + r * (size + pad) + size / 2 - 10);
                for (int c = 0; c < heads.Length; c++) g.DrawImage(rows[r][c], lw + c * (size + pad), 30 + hh + r * (size + pad), size, size);
            }
            string dest = Capt + @"\2026-11-06_fit-" + tag + ".png";
            bmp.Save(dest, ImageFormat.Png);
            Console.WriteLine(dest);
        }
        return 0;
    }
}
