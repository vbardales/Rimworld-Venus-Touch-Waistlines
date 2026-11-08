# Where does the hem of the stretched shirt land, compared with the pink line and with D? (Male, three facings)
param([string]$Body = 'Male')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing, PresentationCore, WindowsBase, System.Xaml
Add-Type -ReferencedAssemblies System.Drawing, PresentationCore, WindowsBase, System.Xaml -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.Globalization;
using System.IO;
using System.Text;

public static class DCheck
{
    static byte[] Read(string path, out int w, out int h)
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
    static double[] Table(string path)
    {
        var p = File.ReadAllText(path).Trim().Split(';');
        var v = new double[p.Length];
        for (int i = 0; i < v.Length; i++) v[i] = double.Parse(p[i], CultureInfo.InvariantCulture);
        return v;
    }

    public static string Report(string step3, string e, string d, string pink, string bodyPng, string dest)
    {
        int w, h, ew, eh, bw, bh;
        var s = Read(step3, out w, out h); var em = Read(e, out ew, out eh); var body = Read(bodyPng, out bw, out bh);
        var D = Table(d); var P = Table(pink);
        int lo = 512, hi = -1;
        for (int x = 0; x < 512; x++) for (int y = 0; y < 512; y++) if (em[(y * 512 + x) * 4 + 3] >= 128) { if (x < lo) lo = x; if (x > hi) hi = x; break; }
        var hem = new double[512];
        for (int x = 0; x < 512; x++) { hem[x] = -1; for (int y = 511; y >= 0; y--) if (s[(y * 512 + x) * 4 + 3] >= 128) { hem[x] = y; break; } }
        var sb = new StringBuilder();
        sb.AppendLine("span " + lo + ".." + hi);
        int mid = 256;
        for (int k = 0; k <= 8; k++)
        {
            int x = lo + (hi - lo) * k / 8;
            sb.AppendLine("x=" + x + "  pink=" + P[x].ToString("0.#") + "  D=" + D[x].ToString("0.#") + "  hem=" + hem[x].ToString("0.#") + "  hem-pink=" + (hem[x] - P[x]).ToString("0.#") + "  (pink-pink[mid]=" + (P[x] - P[mid]).ToString("0.#") + ", hem-hem[mid]=" + (hem[x] - hem[mid]).ToString("0.#") + ")");
        }
        // overlay: crop the lower torso, x3
        int y0 = 280, y1 = 470, sc = 3;
        int cw = (hi - lo + 40), ch = y1 - y0;
        var bmp = new Bitmap(cw * sc, ch * sc, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(bmp))
        {
            g.Clear(Color.FromArgb(88, 105, 88));
            g.InterpolationMode = InterpolationMode.NearestNeighbor; g.PixelOffsetMode = PixelOffsetMode.Half;
            foreach (var layer in new[] { body, s })
            {
                var l = new byte[layer.Length];
                for (int i = 0; i < layer.Length; i += 4) { l[i] = layer[i + 2]; l[i + 1] = layer[i + 1]; l[i + 2] = layer[i]; l[i + 3] = layer[i + 3]; }
                using (var b = new Bitmap(512, 512, PixelFormat.Format32bppArgb))
                {
                    var dd = b.LockBits(new Rectangle(0, 0, 512, 512), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
                    System.Runtime.InteropServices.Marshal.Copy(l, 0, dd.Scan0, l.Length); b.UnlockBits(dd);
                    if (layer == s)
                    {
                        // tint the shirt blue
                        for (int y = 0; y < 512; y++) for (int x = 0; x < 512; x++) { var c = b.GetPixel(x, y); if (c.A > 0) b.SetPixel(x, y, Color.FromArgb(c.A, c.R * 120 / 255, c.G * 170 / 255, c.B * 235 / 255)); }
                    }
                    g.DrawImage(b, new Rectangle(0, 0, cw * sc, ch * sc), lo - 20, y0, cw, ch, GraphicsUnit.Pixel);
                }
            }
            using (var pPink = new Pen(Color.FromArgb(255, 60, 160), 2f))
            using (var pHem = new Pen(Color.FromArgb(255, 220, 0), 2f))
                for (int x = lo - 20; x < hi + 20 - 1; x++)
                {
                    int xa = Math.Max(0, Math.Min(511, x)), xb = Math.Max(0, Math.Min(511, x + 1));
                    g.DrawLine(pPink, (x - (lo - 20)) * sc, (float)(P[xa] - y0) * sc, (x + 1 - (lo - 20)) * sc, (float)(P[xb] - y0) * sc);
                    if (hem[xa] >= 0 && hem[xb] >= 0) g.DrawLine(pHem, (x - (lo - 20)) * sc, (float)(hem[xa] - y0) * sc, (x + 1 - (lo - 20)) * sc, (float)(hem[xb] - y0) * sc);
                }
        }
        bmp.Save(dest, ImageFormat.Png);
        return sb.ToString();
    }
}
'@
$proto = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto'
$WS = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100'
foreach ($f in 'south', 'east', 'north') {
    "== $Body $f"
    [DCheck]::Report("$proto\simple-stretch\${Body}_${f}_step3.png", "$proto\E_${Body}_$f.png", "$proto\hemshift_${Body}_$f.txt", "$proto\hemshift_${Body}_$f.pink.txt", "$WS\3527486510\Textures\Things\Pawn\Humanlike\Bodies\Naked_${Body}_$f.png", "$proto\simple-stretch\dcheck_${Body}_$f.png")
}
