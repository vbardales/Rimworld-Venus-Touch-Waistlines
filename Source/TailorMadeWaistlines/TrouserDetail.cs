using System;

namespace TailorMadeWaistlines
{
    /// <summary>Which side of the pawn a worn-graphic texture shows.</summary>
    public enum Facing
    {
        South,
        East,
        North,
    }

    /// <summary>
    /// Gives a plain garment shell the marks that make it read as trousers.
    ///
    /// AB's Visible Pants draws its trousers as a bowl: an outline and an even fill, with no
    /// waistband, no fly, no seam and no gap between two legs. On a body retexture drawn as one
    /// legless shape that bowl is all there is, and it reads as a shell rather than as clothing.
    /// The art that has those marks exists, but only for the body types it was drawn for; this
    /// covers the rest by drawing them onto the shell that is already there.
    ///
    /// Pure on purpose: it works on 8-bit RGBA pixels, top row first, and touches no game or Unity
    /// type, so it can be run and looked at outside the game. Every mark is a multiplication of the
    /// colour that is already there and never a colour of its own, because the game tints these
    /// textures with the garment's colour. Alpha is never touched: the gap between the legs is
    /// painted black, so that it reads as the inside of the garment and never shows the ground.
    ///
    /// The shells are not one shape. A female or fat body gets a wide crescent whose top edge dips
    /// in the middle, a thin one a small cup, so nothing here is placed by a fixed row: the
    /// waistband follows the top edge column by column, and the fly and the seams are measured
    /// from it down to the point where the legs part.
    /// </summary>
    public static class TrouserDetail
    {
        public const int Channels = 4;

        /// <summary>A pixel at or above this alpha is part of the garment.</summary>
        private const int Solid = 128;

        // How much of the local colour survives. Lower is darker.
        private const float Band = 0.74f;
        private const float Seam = 0.50f;
        private const float Stitch = 0.62f;
        private const float Button = 0.38f;
        private const float Edge = 0.16f;

        /// <summary>
        /// Returns a copy of <paramref name="rgba"/> with the marks drawn on. A texture with
        /// nothing solid in it, or too small to hold the marks, comes back unchanged.
        /// </summary>
        public static byte[] Apply(byte[] rgba, int width, int height, Facing facing, bool bareLegs = false)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");

            var px = (byte[])rgba.Clone();
            var s = Measure(px, width, height);
            if (s == null || s.W < 12 || s.H < 8) return px;

            DrawWaistband(px, width, height, s);

            switch (facing)
            {
                case Facing.South: DrawFront(px, width, height, s); break;
                case Facing.North: DrawBack(px, width, height, s); break;
                default: DrawSide(px, width, height, s); break;
            }

            if (facing != Facing.East)
                CutBetweenTheLegs(px, width, height, s, bareLegs);

            return px;
        }

        /// <summary>
        /// Moves the whole picture down by a number of rows, leaving transparent rows at the top.
        /// It never cuts the garment: the shift is reduced until the lowest solid pixel is still
        /// inside the texture, so asking for too much moves it as far as it goes and stops.
        /// </summary>
        public static byte[] ShiftDown(byte[] rgba, int width, int height, int rows)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");

            var copy = (byte[])rgba.Clone();
            if (rows <= 0) return copy;

            int lowest = -1;
            for (int y = height - 1; y >= 0 && lowest < 0; y--)
                for (int x = 0; x < width; x++)
                    if (rgba[(y * width + x) * Channels + 3] >= Solid) { lowest = y; break; }
            if (lowest < 0) return copy;

            rows = Math.Min(rows, height - 1 - lowest);
            if (rows <= 0) return copy;

            var shifted = new byte[rgba.Length];
            int stride = width * Channels;
            Buffer.BlockCopy(rgba, 0, shifted, rows * stride, (height - rows) * stride);
            return shifted;
        }

        /// <summary>
        /// Squeezes the picture towards its own centre column by <paramref name="factor"/> (below 1 narrows). Used for a
        /// body whose shell is wider than its trousers should be; alpha is only ever lost at the edges.
        /// </summary>
        public static byte[] Narrow(byte[] rgba, int width, int height, float factor)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var copy = (byte[])rgba.Clone();
            if (factor <= 0f || factor >= 1f) return copy;
            var s = Measure(rgba, width, height);
            if (s == null) return copy;

            var outPx = new byte[rgba.Length];
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int sx = Round(s.Cx + (x - s.Cx) / factor);
                    if (sx < 0 || sx >= width) continue;
                    Buffer.BlockCopy(rgba, (y * width + sx) * Channels, outPx, (y * width + x) * Channels, Channels);
                }
            return outPx;
        }

        /// <summary>
        /// Stretches the garment upwards so that its top edge lands on <paramref name="newTopRow"/> and its bottom stays where
        /// it is: the shell gets taller, it is neither moved nor cut. Does nothing when the row is not above the current top.
        /// </summary>
        /// <summary>
        /// Moves the top of the shape down by <paramref name="rows"/> and keeps its bottom where it is: the rows between are
        /// squeezed. Shifting the whole shape down instead pushes the hem below the body, which makes the pawn taller.
        /// </summary>
        public static byte[] CompressTop(byte[] rgba, int width, int height, int rows)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var s = Measure(rgba, width, height);
            if (s == null || rows <= 0 || rows >= s.Bottom - s.Top) return (byte[])rgba.Clone();
            var outPx = (byte[])rgba.Clone();
            int stride = width * Channels;
            int newTop = s.Top + rows;
            Array.Clear(outPx, s.Top * stride, rows * stride);
            int span = s.Bottom - s.Top, newSpan = s.Bottom - newTop;
            for (int y = newTop; y <= s.Bottom; y++)
            {
                int src = s.Top + (int)Math.Round((y - newTop) * (double)span / newSpan, MidpointRounding.AwayFromZero);
                src = Math.Max(s.Top, Math.Min(s.Bottom, src));
                Buffer.BlockCopy(rgba, src * stride, outPx, y * stride, stride);
            }
            return outPx;
        }

        /// <summary>
        /// Softens the stair steps of a silhouette drawn at a low resolution: the alpha channel goes through a 3 x 3 blur
        /// (1 2 1 / 2 4 2 / 1 2 1), and a pixel the blur makes visible takes the colour of its most solid neighbour, so no
        /// dark fringe appears. Colours of pixels that were already visible are left as they are.
        /// </summary>
        public static byte[] SmoothAlpha(byte[] rgba, int width, int height)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var outPx = (byte[])rgba.Clone();
            int[] k = { 1, 2, 1, 2, 4, 2, 1, 2, 1 };
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int sum = 0, bestA = -1, bestI = -1, i = 0;
                    for (int dy = -1; dy <= 1; dy++)
                        for (int dx = -1; dx <= 1; dx++, i++)
                        {
                            int nx = Math.Max(0, Math.Min(width - 1, x + dx)), ny = Math.Max(0, Math.Min(height - 1, y + dy));
                            int idx = (ny * width + nx) * Channels;
                            int a = rgba[idx + 3];
                            sum += a * k[i];
                            if (a > bestA) { bestA = a; bestI = idx; }
                        }
                    int o = (y * width + x) * Channels;
                    int na = sum / 16;
                    if (rgba[o + 3] == 0 && na > 0 && bestI >= 0)
                    {
                        outPx[o] = rgba[bestI]; outPx[o + 1] = rgba[bestI + 1]; outPx[o + 2] = rgba[bestI + 2];
                    }
                    outPx[o + 3] = (byte)na;
                }
            return outPx;
        }

        public static byte[] StretchTop(byte[] rgba, int width, int height, int newTopRow)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var copy = (byte[])rgba.Clone();
            var s = Measure(rgba, width, height);
            if (s == null || newTopRow < 0 || newTopRow >= s.Top) return copy;

            var outPx = new byte[rgba.Length];
            int span = s.Bottom - s.Top;
            int newSpan = s.Bottom - newTopRow;
            int stride = width * Channels;
            for (int y = newTopRow; y <= s.Bottom; y++)
            {
                int src = s.Top + (int)Math.Round((y - newTopRow) * (double)span / newSpan, MidpointRounding.AwayFromZero);
                src = Math.Max(s.Top, Math.Min(s.Bottom, src));
                Buffer.BlockCopy(rgba, src * stride, outPx, y * stride, stride);
            }
            // Below the old bottom nothing changes.
            for (int y = s.Bottom + 1; y < height; y++)
                Buffer.BlockCopy(rgba, y * stride, outPx, y * stride, stride);
            return outPx;
        }

        /// <summary>
        /// Erases, column by column, everything above that column's row, and fades the first rows under it so that the edge
        /// is not a ruler line. The mask is the top edge of the underwear, which the trousers must start on.
        /// </summary>
        public static byte[] CutAbove(byte[] rgba, int width, int height, int[] topRows)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (topRows == null || topRows.Length != width) throw new ArgumentException("one row per column.");
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            var px = (byte[])rgba.Clone();
            for (int x = 0; x < width; x++)
            {
                int top = Math.Max(0, Math.Min(height, topRows[x]));
                for (int y = 0; y < top; y++) px[(y * width + x) * Channels + 3] = 0;
                for (int k = 0; k < 2 && top + k < height; k++)
                {
                    int i = ((top + k) * width + x) * Channels + 3;
                    px[i] = (byte)(px[i] * ((k + 1) / 3f));
                }
            }
            return px;
        }

        /// <summary>The highest row with a solid pixel, or -1 when there is none.</summary>
        public static int TopRow(byte[] rgba, int width, int height)
        {
            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                    if (rgba[(y * width + x) * Channels + 3] >= Solid) return y;
            return -1;
        }

        /// <summary>The lowest row with a solid pixel, or -1 when there is none.</summary>
        public static int BottomRow(byte[] rgba, int width, int height)
        {
            for (int y = height - 1; y >= 0; y--)
                for (int x = 0; x < width; x++)
                    if (rgba[(y * width + x) * Channels + 3] >= Solid) return y;
            return -1;
        }

        /// <summary>
        /// The row where the legs of a trousers shell part (the same measure the fly and the back seam end on), or -1 when
        /// the picture is empty.
        /// </summary>
        public static int CrotchRow(byte[] rgba, int width, int height)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            Shape s = Measure(rgba, width, height);
            return s == null ? -1 : s.Crotch;
        }

        /// <summary>
        /// For shorts drawn as two legs side by side (Swimwear's trunks): the dark line down the middle is kept only below the
        /// crotch, as a seam, and the small gap left in the hem between the legs is closed with the hem's own colour. On a body
        /// drawn without legs the full-height line and the gap read as a garment cut in two (Virginie 2026-11-06).
        /// The waistband and the outline are left as drawn: a dark pixel counts as the middle line only where the fabric goes on
        /// at both sides of it in the same row. Returns the input itself when nothing changes.
        /// </summary>
        public static byte[] MendSplitLegs(byte[] rgba, int width, int height)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            Shape s = Measure(rgba, width, height);
            if (s == null) return rgba;
            byte[] o = (byte[])rgba.Clone();
            int reach = Math.Max(3, width / 40);
            bool changed = false;
            for (int y = s.Top; y < s.Crotch; y++)
                changed |= EraseMiddleLine(rgba, o, width, y, s.Cx, reach);
            for (int y = s.Crotch; y <= s.Bottom; y++)
            {
                for (int x = s.Cx - reach; x <= s.Cx + reach; x++)
                {
                    if (x <= 0 || x >= width - 1) continue;
                    int i = (y * width + x) * Channels;
                    bool solid = rgba[i + 3] >= Solid;
                    if (!solid && SolidAt(rgba, width, y, x, -1, reach) && SolidAt(rgba, width, y, x, 1, reach))
                    {
                        // the gap in the hem between the legs: the colour of the leg next to it
                        int src = Nearest(rgba, width, y, x, -1, reach);
                        Buffer.BlockCopy(rgba, src, o, i, Channels);
                        changed = true;
                    }
                }
            }
            return changed ? o : rgba;
        }

        private static int Lum(byte[] px, int i) => (px[i] + px[i + 1] + px[i + 2]) / 3;

        /// <summary>
        /// One row above the crotch: the run of pixels darker than the fabric around the middle (the line and its soft edges)
        /// is repainted with a blend of the fabric just left and right of it. A row whose fabric does not go on at both sides
        /// within twice the reach (the waistband, the outline) is left alone.
        /// </summary>
        private static bool EraseMiddleLine(byte[] src, byte[] dst, int width, int y, int cx, int reach)
        {
            int lo = Math.Max(1, cx - 2 * reach), hi = Math.Min(width - 2, cx + 2 * reach);
            int il = (y * width + lo) * Channels, ir = (y * width + hi) * Channels;
            if (src[il + 3] < Solid || src[ir + 3] < Solid) return false;
            int fabric = Math.Max(Lum(src, il), Lum(src, ir));
            if (fabric < 70) return false;
            int threshold = fabric - 25;
            // the darkest pixel near the middle, then the run around it
            int dark = -1, darkLum = threshold;
            for (int x = cx - reach; x <= cx + reach; x++)
            {
                int i = (y * width + x) * Channels;
                if (src[i + 3] < Solid) return false;
                if (Lum(src, i) < darkLum) { darkLum = Lum(src, i); dark = x; }
            }
            if (dark < 0) return false;
            int xl = dark, xr = dark;
            while (xl - 1 > lo && Lum(src, (y * width + xl - 1) * Channels) < threshold) xl--;
            while (xr + 1 < hi && Lum(src, (y * width + xr + 1) * Channels) < threshold) xr++;
            int a = (y * width + xl - 1) * Channels, b = (y * width + xr + 1) * Channels;
            if (Lum(src, a) < threshold || Lum(src, b) < threshold) return false;
            for (int x = xl; x <= xr; x++)
            {
                float t = (x - xl + 1f) / (xr - xl + 2f);
                int i = (y * width + x) * Channels;
                for (int c = 0; c < 3; c++) dst[i + c] = (byte)Math.Round(src[a + c] + (src[b + c] - src[a + c]) * t);
                dst[i + 3] = src[i + 3];
            }
            return true;
        }

        private static bool SolidAt(byte[] px, int width, int y, int x, int dir, int reach) => Nearest(px, width, y, x, dir, reach) >= 0;

        /// <summary>Index of the first solid pixel from x towards dir within reach, or -1.</summary>
        private static int Nearest(byte[] px, int width, int y, int x, int dir, int reach)
        {
            for (int k = 1; k <= reach; k++)
            {
                int xx = x + dir * k;
                if (xx < 0 || xx >= width) break;
                int i = (y * width + xx) * Channels;
                if (px[i + 3] >= Solid) return i;
            }
            return -1;
        }

        /// <summary>
        /// Stretches (or compresses) the part of the picture below <paramref name="pivotRow"/>, so that its lowest solid row lands on
        /// <paramref name="newBottomRow"/>; everything above the pivot stays as it is. Returns the input itself when there is
        /// nothing to do (the garment already reaches that row, or the pivot is not above its hem).
        /// </summary>
        public static byte[] StretchBottom(byte[] rgba, int width, int height, int pivotRow, int newBottomRow)
        {
            if (rgba == null) throw new ArgumentNullException(nameof(rgba));
            if (width <= 0 || height <= 0 || rgba.Length != width * height * Channels)
                throw new ArgumentException("rgba must hold width * height * 4 bytes.");
            int bottom = BottomRow(rgba, width, height);
            if (bottom < 0 || pivotRow < 0 || pivotRow >= bottom || newBottomRow == bottom || newBottomRow <= pivotRow || newBottomRow >= height) return rgba;

            var outPx = new byte[rgba.Length];
            int stride = width * Channels;
            Buffer.BlockCopy(rgba, 0, outPx, 0, (pivotRow + 1) * stride);
            int span = bottom - pivotRow;
            int newSpan = newBottomRow - pivotRow;
            for (int y = pivotRow + 1; y <= newBottomRow; y++)
            {
                int src = pivotRow + (int)Math.Round((y - pivotRow) * (double)span / newSpan, MidpointRounding.AwayFromZero);
                src = Math.Max(pivotRow + 1, Math.Min(bottom, src));
                Buffer.BlockCopy(rgba, src * stride, outPx, y * stride, stride);
            }
            return outPx;
        }

        // ------------------------------------------------------------------- the shape

        /// <summary>What was measured off the shell, in pixels.</summary>
        private sealed class Shape
        {
            public int Left, Top, Right, Bottom;
            public int W => Right - Left + 1;
            public int H => Bottom - Top + 1;
            public int Cx;
            /// <summary>First solid row of each column, or -1 where the column is empty.</summary>
            public int[] TopEdge;
            /// <summary>Rows of near-black along the top edge, in the middle.</summary>
            public int Outline;
            public int BandH;
            /// <summary>Row where the legs part, so the fly and the back seam have somewhere to end.</summary>
            public int Crotch;
            public int Thickness;

            /// <summary>First row of the waistband in a column.</summary>
            public int BandTop(int x) => TopEdge[Clamp(x)] + Outline;
            /// <summary>The seam line under the waistband in a column.</summary>
            public int SeamAt(int x) => BandTop(x) + BandH;

            private int Clamp(int x) => Math.Max(0, Math.Min(TopEdge.Length - 1, x));
        }

        private static Shape Measure(byte[] px, int width, int height)
        {
            var s = new Shape { Left = width, Top = height, Right = -1, Bottom = -1, TopEdge = new int[width] };
            for (int x = 0; x < width; x++)
            {
                s.TopEdge[x] = -1;
                for (int y = 0; y < height; y++)
                {
                    if (px[(y * width + x) * Channels + 3] < Solid) continue;
                    if (s.TopEdge[x] < 0) s.TopEdge[x] = y;
                    if (x < s.Left) s.Left = x;
                    if (x > s.Right) s.Right = x;
                    if (y < s.Top) s.Top = y;
                    if (y > s.Bottom) s.Bottom = y;
                }
            }
            if (s.Right < 0) return null;

            s.Cx = (s.Left + s.Right) / 2;
            // Where the middle column is empty (a shell that already has a gap) fall back to the
            // nearest column that is not.
            int probe = s.Cx;
            while (probe < s.Right && s.TopEdge[probe] < 0) probe++;
            s.Outline = OutlineThickness(px, width, s.TopEdge[probe], s.Bottom, probe);
            s.BandH = Math.Max(2, Round(s.H * 0.20f));
            s.Thickness = s.W >= 56 ? 2 : 1;

            int notch = Math.Max(2, Round(s.H * 0.34f));
            s.Crotch = s.Bottom - notch;
            return s;
        }

        private static int OutlineThickness(byte[] px, int width, int from, int bottom, int x)
        {
            int rows = 0;
            for (int y = from; y <= bottom && rows < 4; y++)
            {
                int i = (y * width + x) * Channels;
                if (px[i + 3] < Solid) break;
                if ((px[i] + px[i + 1] + px[i + 2]) / 3 > 70) break;
                rows++;
            }
            return Math.Max(1, rows);
        }

        // ------------------------------------------------------------------ the marks

        private static void DrawWaistband(byte[] px, int width, int height, Shape s)
        {
            for (int x = s.Left; x <= s.Right; x++)
            {
                if (s.TopEdge[x] < 0) continue;
                for (int y = s.BandTop(x); y < s.SeamAt(x); y++)
                    ToneAt(px, width, height, x, y, Band);
                // The seam under it stops short of the outline at either end.
                if (x >= s.Left + s.Outline && x <= s.Right - s.Outline)
                    ToneAt(px, width, height, x, s.SeamAt(x), Seam);
            }
        }

        private static void DrawFront(byte[] px, int width, int height, Shape s)
        {
            // The fly, from the waistband to where the legs part, and the button that closes it.
            for (int t = 0; t < s.Thickness; t++)
                Line(px, width, height, s.Cx + t, s.SeamAt(s.Cx) + 1, s.Cx + t, s.Crotch - 1, Seam, 0);
            for (int t = 0; t < s.Thickness; t++)
                ToneAt(px, width, height, s.Cx + t, s.BandTop(s.Cx) + s.BandH / 2, Button);

            // A pocket opening on each hip, running from the waistband towards the fly.
            int reach = Math.Max(3, Round(s.W * 0.32f));
            int near = Math.Max(1, Round(s.W * 0.14f));
            foreach (int side in new[] { -1, 1 })
            {
                int x0 = s.Cx + side * reach;
                int x1 = s.Cx + side * near;
                int y0 = s.SeamAt(x0) + 1;
                int y1 = Math.Min(s.Crotch - 2, y0 + Math.Max(3, Round((s.Crotch - y0) * 0.75f)));
                Line(px, width, height, x0, y0, x1, y1, Stitch, 2);
            }
        }

        private static void DrawBack(byte[] px, int width, int height, Shape s)
        {
            // The centre back seam, down to where the legs part.
            for (int t = 0; t < s.Thickness; t++)
                Line(px, width, height, s.Cx + t, s.SeamAt(s.Cx) + 1, s.Cx + t, s.Crotch - 1, Seam, 0);

            // Two patch pockets, drawn as three edges: the top of a pocket is the waistband's seam.
            int inner = Math.Max(2, Round(s.W * 0.13f));
            int outer = Math.Max(inner + 3, Round(s.W * 0.36f));
            foreach (int side in new[] { -1, 1 })
            {
                int a = s.Cx + side * inner;
                int b = s.Cx + side * outer;
                int top = Math.Min(s.SeamAt(a), s.SeamAt(b)) + 2;
                int bottom = Math.Min(s.Crotch - 2, top + Math.Max(3, Round((s.Crotch - top) * 0.55f)));
                Line(px, width, height, a, s.SeamAt(a) + 1, a, bottom, Stitch, 0);
                Line(px, width, height, b, s.SeamAt(b) + 1, b, bottom, Stitch, 0);
                Line(px, width, height, Math.Min(a, b), bottom, Math.Max(a, b), bottom, Stitch, 0);
            }
        }

        private static void DrawSide(byte[] px, int width, int height, Shape s)
        {
            // From the side there is only the seam that runs down the leg.
            Line(px, width, height, s.Cx, s.SeamAt(s.Cx) + 1, s.Cx, s.Bottom - s.Outline - 1, Stitch, 0);
        }

        // -------------------------------------------------------------------- the gap

        /// <summary>
        /// Paints a black wedge on the bottom edge so the shell reads as two legs, then darkens the
        /// pixels that now border it so the gap has an edge like every other side of the shape. The
        /// wedge keeps its alpha: what shows through it is the garment's own dark, not the body or the
        /// ground, which only shows where the legs are bare.
        /// </summary>
        private static void CutBetweenTheLegs(byte[] px, int width, int height, Shape s, bool bareLegs)
        {
            int depth = s.Bottom - s.Crotch;
            float halfBase = Math.Max(1f, s.W * 0.09f);
            var cut = new bool[width * height];

            for (int y = s.Crotch + 1; y <= s.Bottom; y++)
            {
                float reach = halfBase * (y - s.Crotch) / depth;
                int from = (int)Math.Ceiling(s.Cx - reach);
                int to = (int)Math.Floor(s.Cx + reach);
                for (int x = from; x <= to; x++)
                {
                    if (x < 0 || x >= width) continue;
                    int i = (y * width + x) * Channels;
                    if (px[i + 3] < Solid) continue;
                    // Trousers cover the legs, so the gap is the inside of the garment: black. Shorts leave the legs bare, so
                    // the gap is open and shows whatever is behind it.
                    if (bareLegs) px[i + 3] = 0;
                    else px[i] = px[i + 1] = px[i + 2] = 0;
                    cut[y * width + x] = true;
                }
            }

            for (int y = 0; y < height; y++)
                for (int x = 0; x < width; x++)
                {
                    int i = (y * width + x) * Channels;
                    if (px[i + 3] < Solid || !TouchesCut(cut, width, height, x, y)) continue;
                    Scale(px, i, Edge);
                }
        }

        private static bool TouchesCut(bool[] cut, int width, int height, int x, int y)
        {
            return (x > 0 && cut[y * width + x - 1])
                || (x < width - 1 && cut[y * width + x + 1])
                || (y > 0 && cut[(y - 1) * width + x])
                || (y < height - 1 && cut[(y + 1) * width + x]);
        }

        // ------------------------------------------------------------------ drawing

        private static void ToneAt(byte[] px, int width, int height, int x, int y, float factor)
        {
            if (x < 0 || x >= width || y < 0 || y >= height) return;
            int i = (y * width + x) * Channels;
            if (px[i + 3] >= Solid) Scale(px, i, factor);
        }

        /// <summary>A line that is only drawn where the garment is; a dash of 0 means unbroken.</summary>
        private static void Line(byte[] px, int width, int height, int x0, int y0, int x1, int y1, float factor, int dash)
        {
            int dx = Math.Abs(x1 - x0), sx = x0 < x1 ? 1 : -1;
            int dy = -Math.Abs(y1 - y0), sy = y0 < y1 ? 1 : -1;
            int err = dx + dy;
            int step = 0;
            while (true)
            {
                if (dash <= 0 || step % (dash + 1) < dash)
                    ToneAt(px, width, height, x0, y0, factor);
                if (x0 == x1 && y0 == y1) break;
                int e2 = 2 * err;
                if (e2 >= dy) { err += dy; x0 += sx; }
                if (e2 <= dx) { err += dx; y0 += sy; }
                step++;
            }
        }

        private static void Scale(byte[] px, int i, float factor)
        {
            for (int c = 0; c < 3; c++)
                px[i + c] = (byte)Math.Max(0, Math.Min(255, Round(px[i + c] * factor)));
        }

        private static int Round(float value) => (int)Math.Round(value, MidpointRounding.AwayFromZero);
    }
}
