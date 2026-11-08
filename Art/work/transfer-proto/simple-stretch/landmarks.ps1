# Landmark rows used by the simple stretch, Male, three facings: vanilla body (left) and WDI body (right), to validate the matching.
# cyan = top, yellow = navel (vanilla row -> WDI row), magenta = bottom of the garment / pubis. 512 px rows, drawn on 2x images.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing, PresentationCore, WindowsBase, System.Xaml
Add-Type -ReferencedAssemblies System.Drawing, PresentationCore, WindowsBase, System.Xaml -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
public static class Lm
{
    public static Bitmap Load(string path)
    {
        var dec = new System.Windows.Media.Imaging.PngBitmapDecoder(new Uri(path), System.Windows.Media.Imaging.BitmapCreateOptions.PreservePixelFormat, System.Windows.Media.Imaging.BitmapCacheOption.OnLoad);
        var src = new System.Windows.Media.Imaging.FormatConvertedBitmap(dec.Frames[0], System.Windows.Media.PixelFormats.Bgra32, null, 0);
        int w = src.PixelWidth, h = src.PixelHeight;
        var bgra = new byte[w * h * 4]; src.CopyPixels(bgra, w * 4, 0);
        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        System.Runtime.InteropServices.Marshal.Copy(bgra, 0, d.Scan0, bgra.Length); bmp.UnlockBits(d);
        return bmp;
    }
    public static Bitmap Panel(Bitmap body, double[] rows, string[] names, string title)
    {
        int size = 300; var cell = new Bitmap(size, size + 22, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(cell))
        using (var f = new Font("Segoe UI", 9, FontStyle.Bold))
        {
            g.Clear(Color.FromArgb(88, 105, 88));
            g.InterpolationMode = InterpolationMode.NearestNeighbor; g.PixelOffsetMode = PixelOffsetMode.Half;
            // crop rows 150..470 of the 512 square so the useful part fills the cell
            float y0 = 150, hh = 320;
            g.DrawImage(body, new Rectangle(0, 22, size, size), 0, y0 * body.Height / 512f, body.Width, hh * body.Height / 512f, GraphicsUnit.Pixel);
            Color[] cols = { Color.Cyan, Color.Yellow, Color.Magenta };
            for (int i = 0; i < rows.Length; i++)
            {
                float y = 22 + (float)((rows[i] - y0) / hh * size);
                using (var p = new Pen(cols[i], 1.5f)) g.DrawLine(p, 0, y, size, y);
                g.DrawString(names[i] + " " + Math.Round(rows[i]), f, new SolidBrush(cols[i]), 2, y - 14);
            }
            g.DrawString(title, f, Brushes.White, 2, 2);
        }
        return cell;
    }
    public static void Sheet(string dest, Bitmap[][] cells)
    {
        int w = cells[0][0].Width, h = cells[0][0].Height;
        var bmp = new Bitmap(2 * w + 4, 3 * h + 8, PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(bmp)) { g.Clear(Color.White); for (int r = 0; r < 3; r++) for (int c = 0; c < 2; c++) g.DrawImage(cells[r][c], c * (w + 4), r * (h + 4)); }
        bmp.Save(dest, ImageFormat.Png);
    }
}
'@
$WS = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100'
$mod = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines'
# vanilla top / navel / bottom of the garment (cloth rows of the stretch run), WDI top (E top) / navel / pubis
$data = @{
    south = @{ V = @(192, 360, 415); W = @(188, 356, 404) }
    east  = @{ V = @(188, 336, 411); W = @(188, 340, 408) }
    north = @{ V = @(188, 332, 415); W = @(186, 332, 408) }
}
$names = @('top', 'navel', 'bottom')
$cells = @()
foreach ($f in 'south', 'east', 'north') {
    $van = [Lm]::Load("$mod\Art\work\vanilla\vanilla-male-$f.png")
    $wdi = [Lm]::Load("$WS\3527486510\Textures\Things\Pawn\Humanlike\Bodies\Naked_Male_$f.png")
    $cells += , @([Lm]::Panel($van, [double[]]$data[$f].V, [string[]]$names, "vanilla Male $f"), [Lm]::Panel($wdi, [double[]]$data[$f].W, [string[]]@('top', 'navel', 'pubis'), "WDI Male $f"))
}
$dest = "$mod\Art\work\captures\2026-11-06_landmarks-male.png"
[Lm]::Sheet($dest, [System.Drawing.Bitmap[][]]$cells)
$dest
