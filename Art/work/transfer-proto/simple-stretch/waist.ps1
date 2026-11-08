# How the trousers of each source end at the waist, Male, three facings (Virginie 2026-11-06).
# Each raw texture is drawn over the whole 512 square of the WDI Male body, as the game does, tinted orange; yellow and pink are
# WDI's underwear top lines (higher / lower of boxers and panties). The last row is what VTW makes of AB's Pants shell.
param([string]$Body = 'Male')
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing, PresentationCore, WindowsBase, System.Xaml
Add-Type -ReferencedAssemblies System.Drawing, PresentationCore, WindowsBase, System.Xaml -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Drawing.Imaging;
using System.IO;

public static class Waist
{
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

    public static Bitmap ToBitmap(byte[] rgba, int w, int h, bool tint)
    {
        var bmp = new Bitmap(w, h, PixelFormat.Format32bppArgb);
        var bgra = new byte[rgba.Length];
        for (int i = 0; i < rgba.Length; i += 4)
        {
            int r = rgba[i], g = rgba[i + 1], b = rgba[i + 2];
            if (tint) { r = r * 235 / 255; g = g * 140 / 255; b = b * 60 / 255; }
            bgra[i] = (byte)b; bgra[i + 1] = (byte)g; bgra[i + 2] = (byte)r; bgra[i + 3] = rgba[i + 3];
        }
        var d = bmp.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
        System.Runtime.InteropServices.Marshal.Copy(bgra, 0, d.Scan0, bgra.Length);
        bmp.UnlockBits(d);
        return bmp;
    }

    public static float[] Top(byte[] px, int w, int h)
    {
        var top = new float[w];
        for (int x = 0; x < w; x++)
        {
            top[x] = -1f;
            for (int y = 0; y < h; y++) if (px[(y * w + x) * 4 + 3] >= 128) { top[x] = y / (float)h; break; }
        }
        int first = Array.FindIndex(top, v => v >= 0f), last = Array.FindLastIndex(top, v => v >= 0f);
        if (first < 0) return null;
        for (int x = 0; x < first; x++) top[x] = top[first];
        for (int x = last + 1; x < w; x++) top[x] = top[last];
        for (int x = first; x <= last; x++) if (top[x] < 0f) top[x] = top[x - 1];
        return top;
    }

    public static float[] Combine(float[] a, float[] b, bool upper)
    {
        var r = new float[a.Length];
        for (int x = 0; x < a.Length; x++) r[x] = upper ? Math.Min(a[x], b[x]) : Math.Max(a[x], b[x]);
        return r;
    }

    // One cell: the lower torso of the body (x 150..362, y 290..470 of 512) at 1.5x, the garment over it, the two lines.
    public static Bitmap Cell(Bitmap body, Bitmap garment, float[] yellow, float[] pink)
    {
        const int x0 = 150, y0 = 290, cw = 212, ch = 180; const float sc = 1.5f;
        var cell = new Bitmap((int)(cw * sc), (int)(ch * sc), PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(cell))
        {
            g.Clear(Color.FromArgb(88, 105, 88));
            g.InterpolationMode = InterpolationMode.NearestNeighbor; g.PixelOffsetMode = PixelOffsetMode.Half;
            var dst = new Rectangle(0, 0, cell.Width, cell.Height);
            g.DrawImage(body, dst, x0, y0, cw, ch, GraphicsUnit.Pixel);
            if (garment != null)
            {
                float k = garment.Width / 512f;
                g.DrawImage(garment, dst, x0 * k, y0 * k, cw * k, ch * k, GraphicsUnit.Pixel);
            }
            using (var py = new Pen(Color.FromArgb(255, 220, 0), 1f))
            using (var pp = new Pen(Color.FromArgb(255, 60, 160), 1f))
                for (int x = x0; x < x0 + cw - 1; x++)
                {
                    g.DrawLine(py, (x - x0) * sc, (yellow[x] * 512 - y0) * sc, (x + 1 - x0) * sc, (yellow[x + 1] * 512 - y0) * sc);
                    g.DrawLine(pp, (x - x0) * sc, (pink[x] * 512 - y0) * sc, (x + 1 - x0) * sc, (pink[x + 1] * 512 - y0) * sc);
                }
        }
        return cell;
    }

    public static void Board(string dest, string title, string[] heads, string[] rows, List<Bitmap[]> cells)
    {
        int cw = cells[0][0].Width, ch = cells[0][0].Height, lw = 190, hh = 40, pad = 4;
        var bmp = new Bitmap(lw + heads.Length * (cw + pad), 28 + hh + rows.Length * (ch + pad), PixelFormat.Format32bppArgb);
        using (var g = Graphics.FromImage(bmp))
        using (var big = new Font("Segoe UI", 12, FontStyle.Bold))
        using (var small = new Font("Segoe UI", 9))
        {
            g.Clear(Color.White);
            g.TextRenderingHint = System.Drawing.Text.TextRenderingHint.AntiAlias;
            g.DrawString(title, big, Brushes.Black, 4, 2);
            for (int c = 0; c < heads.Length; c++) g.DrawString(heads[c], big, Brushes.Black, lw + c * (cw + pad), 28);
            for (int r = 0; r < rows.Length; r++)
            {
                g.DrawString(rows[r], small, Brushes.Black, new RectangleF(4, 28 + hh + r * (ch + pad) + 6, lw - 8, ch));
                for (int c = 0; c < heads.Length; c++) g.DrawImage(cells[r][c], lw + c * (cw + pad), 28 + hh + r * (ch + pad));
            }
        }
        bmp.Save(dest, ImageFormat.Png);
    }
}
'@

$WS = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100'
$mod = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines'
$asm = [Reflection.Assembly]::LoadFrom("$mod\Mod\Assemblies\TailorMadeWaistlines.dll")
$detail = $asm.GetType('TailorMadeWaistlines.TrouserDetail', $true)
$facingType = $asm.GetType('TailorMadeWaistlines.Facing', $true)
function Invoke-Static($type, [string]$name, [object[]]$callArgs) { $r = $type.GetMethod($name).Invoke($null, [object[]]$callArgs); , $r }

$ab = "$WS\2986402536\Textures\Things\Pawn\Humanlike\Apparel"
$sources = @(
    @{ Label = "AB Pants (Pants_${Body}), raw shell"; Path = { param($f) "$ab\Pants\Pants_${Body}_$f.png" } },
    @{ Label = "AB Trousers (Trousers_${Body}), raw shell (VAE_Apparel_Trousers)"; Path = { param($f) "$ab\Trousers\Trousers_${Body}_$f.png" } },
    @{ Label = "AB Jeans (Jeans_${Body}), raw shell"; Path = { param($f) "$ab\Jeans\Jeans_${Body}_$f.png" } },
    @{ Label = "AB Shorts (Shorts_${Body}), raw shell"; Path = { param($f) "$ab\Shorts\Shorts_${Body}_$f.png" } },
    @{ Label = "General Textures Collection Pants_${Body} (retexture of AB's, Mods\VisiblePants)"; Path = { param($f) "$WS\3789119336\Mods\VisiblePants\Textures\Core\Things\Pawn\Humanlike\Apparel\Pants\Pants_${Body}_$f.png" } }
)
$facings = @('south', 'east', 'north')
$rows = New-Object 'System.Collections.Generic.List[System.Drawing.Bitmap[]]'
$rowLabels = @()
$lines = @{}
$bodies = @{}
foreach ($f in $facings) {
    $bw = 0; $bh = 0
    $bodyPx = [Waist]::Read("$WS\3527486510\Textures\Things\Pawn\Humanlike\Bodies\Naked_${Body}_$f.png", [ref]$bw, [ref]$bh)
    $bodies[$f] = [Waist]::ToBitmap($bodyPx, $bw, $bh, $false)
    $uw = "$WS\3527486510\Textures\UWUnderwear"
    $boxers = [Waist]::Read("$uw\boxers\boxers_${Body}_$f.png", [ref]$bw, [ref]$bh)
    $panties = [Waist]::Read("$uw\panties\panties_${Body}_$f.png", [ref]$bw, [ref]$bh)
    $tb = [Waist]::Top($boxers, $bw, $bh); $tp = [Waist]::Top($panties, $bw, $bh)
    $lines[$f] = @{ Yellow = [Waist]::Combine($tb, $tp, $true); Pink = [Waist]::Combine($tb, $tp, $false) }
}
foreach ($s in $sources) {
    $row = @()
    foreach ($f in $facings) {
        $p = & $s.Path $f
        $bmp = $null
        if (Test-Path -LiteralPath $p) { $w = 0; $h = 0; $px = [Waist]::Read($p, [ref]$w, [ref]$h); $bmp = [Waist]::ToBitmap($px, $w, $h, $true) }
        $row += [Waist]::Cell($bodies[$f], $bmp, [single[]]$lines[$f].Yellow, [single[]]$lines[$f].Pink)
    }
    $rows.Add([System.Drawing.Bitmap[]]$row); $rowLabels += $s.Label
}
# VTW's finished Pants (what TrouserArt.Detail makes: stretched to the yellow line, cut on it, details, smoothed)
$row = @()
$fi = 0
foreach ($f in $facings) {
    $sw = 0; $sh = 0; $rgba = [Waist]::Read("$ab\Pants\Pants_${Body}_$f.png", [ref]$sw, [ref]$sh)
    $yel = $lines[$f].Yellow
    $highest = ($yel | Measure-Object -Minimum).Minimum
    $s1 = Invoke-Static $detail 'StretchTop' @($rgba, [int]$sw, [int]$sh, [int][Math]::Round($highest * $sh, [MidpointRounding]::AwayFromZero))
    $rowsArr = New-Object 'int[]' $sw
    for ($x = 0; $x -lt $sw; $x++) { $rowsArr[$x] = [int][Math]::Round($yel[[Math]::Min($yel.Length - 1, [int][Math]::Floor($x * $yel.Length / $sw))] * $sh, [MidpointRounding]::AwayFromZero) }
    $s2 = Invoke-Static $detail 'CutAbove' @($s1, [int]$sw, [int]$sh, [int[]]([int[]]$rowsArr.Clone()))
    $s3 = Invoke-Static $detail 'Apply' @($s2, [int]$sw, [int]$sh, [Enum]::ToObject($facingType, $fi), $false)
    $s4 = Invoke-Static $detail 'SmoothAlpha' @($s3, [int]$sw, [int]$sh)
    $row += [Waist]::Cell($bodies[$f], [Waist]::ToBitmap($s4, $sw, $sh, $true), [single[]]$lines[$f].Yellow, [single[]]$lines[$f].Pink)
    $fi++
}
$rows.Add([System.Drawing.Bitmap[]]$row); $rowLabels += "VTW result on AB's Pants shell: stretched up to the yellow line, cut on it, details, smoothed"
$dest = "$mod\Art\work\captures\2026-11-06_trousers-at-the-waist-$($Body.ToLower()).png"
[Waist]::Board($dest, "Trousers of each source at the waist, $Body (orange = garment, yellow = higher underwear line, pink = lower)", [string[]]$facings, [string[]]$rowLabels, $rows)
$dest
