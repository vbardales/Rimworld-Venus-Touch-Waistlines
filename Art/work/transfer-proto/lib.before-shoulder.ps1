$src = @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging; using System.Text;
public static class Layers {
  static byte[] Load(string path, out int w, out int h) {
    using (Bitmap b = new Bitmap(path)) { w = b.Width; h = b.Height;
      BitmapData d = b.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
      byte[] px = new byte[w * h * 4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, px, 0, px.Length); b.UnlockBits(d); return px; }
  }
  static void Save(byte[] o, int w, int h, string path) {
    using (Bitmap res = new Bitmap(w, h, PixelFormat.Format32bppArgb)) {
      BitmapData d = res.LockBits(new Rectangle(0, 0, w, h), ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
      System.Runtime.InteropServices.Marshal.Copy(o, 0, d.Scan0, o.Length); res.UnlockBits(d); res.Save(path, ImageFormat.Png); }
  }
  static void Extents(byte[] a, int w, int h, int[] L, int[] R, out int top, out int bottom) {
    top = -1; bottom = -1;
    for (int y = 0; y < h; y++) { L[y] = -1; R[y] = -1;
      for (int x = 0; x < w; x++) if (a[(y * w + x) * 4 + 3] > 40) { if (L[y] < 0) L[y] = x; R[y] = x; }
      if (L[y] >= 0) { if (top < 0) top = y; bottom = y; } }
  }
  static int[] OuterDist(byte[] a, int w, int h) {
    a = S3.ApplyHole(a, w, h);
    int[] d = new int[w * h]; for (int i = 0; i < d.Length; i++) d[i] = -1;
    Queue<int> q = new Queue<int>();
    for (int x = 0; x < w; x++) { S(a, w, d, q, x, 0); S(a, w, d, q, x, h - 1); }
    for (int y = 0; y < h; y++) { S(a, w, d, q, 0, y); S(a, w, d, q, w - 1, y); }
    while (q.Count > 0) { int i = q.Dequeue(); int x = i % w, y = i / w;
      for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; int j = yy * w + xx; if (d[j] == -1 && a[j*4+3] <= 40) { d[j] = 0; q.Enqueue(j); } } }
    Queue<int> q2 = new Queue<int>(); for (int i = 0; i < d.Length; i++) if (d[i] == 0) q2.Enqueue(i);
    while (q2.Count > 0) { int i = q2.Dequeue(); int x = i % w, y = i / w;
      for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; int j = yy * w + xx; if (d[j] == -1 && a[j*4+3] > 40) { d[j] = d[i] + 1; q2.Enqueue(j); } } }
    return d;
  }
  static void S(byte[] a, int w, int[] d, Queue<int> q, int x, int y) { int i = y * w + x; if (d[i] == -1 && a[i*4+3] <= 40) { d[i] = 0; q.Enqueue(i); } }
  static void CleanBand(byte[] px, int w, int h, int band) {
    int[] d = OuterDist(px, w, h);
    for (int k = band; k >= 1; k--) {
      List<int> todo = new List<int>(); for (int i = 0; i < d.Length; i++) if (d[i] == k) todo.Add(i);
      foreach (int i in todo) { if ((px[i*4] + px[i*4+1] + px[i*4+2]) / 3 >= 120) continue; int x = i % w, y = i / w; double r = 0, g = 0, b = 0; int n = 0;
        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x + dx, yy = y + dy; if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; int j = yy * w + xx; if (d[j] > k && (px[j*4] + px[j*4+1] + px[j*4+2]) / 3 > 120) { r += px[j*4+2]; g += px[j*4+1]; b += px[j*4]; n++; } }
        if (n == 0) { px[i*4+2] = 255; px[i*4+1] = 255; px[i*4] = 255; } else { px[i*4+2] = (byte)(r / n); px[i*4+1] = (byte)(g / n); px[i*4] = (byte)(b / n); } }
    }
  }
  static double[] Solve(double[,] m, double[] v) {
    int n = v.Length;
    for (int c = 0; c < n; c++) {
      int p = c; for (int r = c + 1; r < n; r++) if (Math.Abs(m[r, c]) > Math.Abs(m[p, c])) p = r;
      if (p != c) { for (int k = 0; k < n; k++) { double t = m[c, k]; m[c, k] = m[p, k]; m[p, k] = t; } double tv = v[c]; v[c] = v[p]; v[p] = tv; }
      for (int r = c + 1; r < n; r++) { double f = m[r, c] / m[c, c]; if (f == 0) continue; for (int k = c; k < n; k++) m[r, k] -= f * m[c, k]; v[r] -= f * v[c]; }
    }
    double[] x = new double[n];
    for (int r = n - 1; r >= 0; r--) { double s = v[r]; for (int k = r + 1; k < n; k++) s -= m[r, k] * x[k]; x[r] = s / m[r, r]; }
    return x;
  }
  static double U(double r2) { return r2 < 1e-9 ? 0 : 0.5 * r2 * Math.Log(r2); }
  class Spline { // maps target (tx,ty) to source
    public double[] fx, fy, wx, wy; public int n;
    public Spline(List<double[]> pairs, double lambda) { // pairs: tx, ty, sx, sy
      n = pairs.Count; fx = new double[n]; fy = new double[n]; double[] vx = new double[n + 3], vy = new double[n + 3]; double[,] A = new double[n + 3, n + 3];
      for (int i = 0; i < n; i++) { fx[i] = pairs[i][0]; fy[i] = pairs[i][1]; vx[i] = pairs[i][2]; vy[i] = pairs[i][3]; }
      for (int i = 0; i < n; i++) {
        for (int j = 0; j < n; j++) { double dx = fx[i] - fx[j], dy = fy[i] - fy[j]; A[i, j] = U(dx*dx + dy*dy); }
        A[i, i] += lambda; A[i, n] = 1; A[i, n+1] = fx[i]; A[i, n+2] = fy[i]; A[n, i] = 1; A[n+1, i] = fx[i]; A[n+2, i] = fy[i]; }
      wx = Solve((double[,])A.Clone(), vx); wy = Solve(A, vy);
    }
    public void Map(double x, double y, out double ox, out double oy) {
      ox = wx[n] + wx[n+1] * x + wx[n+2] * y; oy = wy[n] + wy[n+1] * x + wy[n+2] * y;
      for (int i = 0; i < n; i++) { double dx = x - fx[i], dy = y - fy[i]; double u = U(dx*dx + dy*dy); ox += wx[i] * u; oy += wy[i] * u; }
    }
  }
  static double Sample(byte[] a, int w, int h, double x, double y, int ch) {
    x -= 0.5; y -= 0.5; int x0 = (int)Math.Floor(x), y0 = (int)Math.Floor(y); double fx = x - x0, fy = y - y0, v = 0;
    for (int j = 0; j < 2; j++) for (int i = 0; i < 2; i++) { int xx = x0 + i, yy = y0 + j; double wgt = (i == 0 ? 1 - fx : fx) * (j == 0 ? 1 - fy : fy);
      if (xx < 0 || yy < 0 || xx >= w || yy >= h) continue; double alpha = a[(yy * w + xx) * 4 + 3]; v += wgt * (ch == 3 ? alpha : a[(yy * w + xx) * 4 + ch] * alpha / 255.0); }
    return v;
  }
  // A boundary polyline given as x ascending (left outer to right outer): y at x by interpolation, and a point at arc fraction u.
  class Line {
    public double[] x, y, s; public double total;
    public Line(int[] lx, int[] ly, int[] rx, int[] ry) { // left outer->sternum, right outer->sternum
      List<double> xs = new List<double>(), ys = new List<double>();
      for (int i = 0; i < lx.Length; i++) { xs.Add(lx[i]); ys.Add(ly[i]); }
      for (int i = rx.Length - 1; i >= 0; i--) { xs.Add(rx[i]); ys.Add(ry[i]); }
      x = xs.ToArray(); y = ys.ToArray(); s = new double[x.Length];
      for (int i = 1; i < x.Length; i++) s[i] = s[i-1] + Math.Sqrt((x[i]-x[i-1])*(x[i]-x[i-1]) + (y[i]-y[i-1])*(y[i]-y[i-1])); total = s[s.Length-1];
    }
    public double YAt(double px) { if (px <= x[0]) return y[0]; if (px >= x[x.Length-1]) return y[y.Length-1];
      for (int i = 1; i < x.Length; i++) if (px <= x[i]) { double d = x[i] - x[i-1]; double t = d == 0 ? 0 : (px - x[i-1]) / d; return y[i-1] + t * (y[i] - y[i-1]); } return y[y.Length-1]; }
    public void At(double u, out double px, out double py) { double t = u * total; for (int i = 1; i < x.Length; i++) if (t <= s[i]) { double d = s[i] - s[i-1]; double f = d == 0 ? 0 : (t - s[i-1]) / d; px = x[i-1] + f * (x[i] - x[i-1]); py = y[i-1] + f * (y[i] - y[i-1]); return; } px = x[x.Length-1]; py = y[y.Length-1]; }
  }
  public static string Run(string srcBody, string srcShirt, string tgtBody, double[] lmS, double[] lmT,
      int[] sLx, int[] sLy, int[] sRx, int[] sRy, int[] tLx, int[] tLy, int[] tRx, int[] tRy, string outPath, double lambda, int band) {
    int bw, bh, sw, sh, tw, th;
    byte[] sb = Load(srcBody, out bw, out bh), shirt = Load(srcShirt, out sw, out sh), tb = Load(tgtBody, out tw, out th);
    CleanBand(shirt, sw, sh, band);
    int[] sL = new int[bh], sR = new int[bh], tL = new int[th], tR = new int[th]; int sTop, sBot, tTop, tBot;
    Extents(sb, bw, bh, sL, sR, out sTop, out sBot); Extents(tb, tw, th, tL, tR, out tTop, out tBot);
    Line sl = new Line(sLx, sLy, sRx, sRy), tl = new Line(tLx, tLy, tRx, tRy);
    // boundary pairs
    List<double[]> bpairs = new List<double[]>(); int nb = 28;
    for (int i = 0; i <= nb; i++) { double u = (double)i / nb, a, b, c, d; tl.At(u, out a, out b); sl.At(u, out c, out d); bpairs.Add(new double[] { a, b, c, d }); }
    double sLineY = 0, tLineY = 0; for (int i = 0; i < sl.y.Length; i++) sLineY += sl.y[i]; sLineY /= sl.y.Length; for (int i = 0; i < tl.y.Length; i++) tLineY += tl.y[i]; tLineY /= tl.y.Length;
    double sNipY = (lmS[1] + lmS[3]) / 2, tNipY = (lmT[1] + lmT[3]) / 2;
    List<double[]> up = new List<double[]>(bpairs), lo = new List<double[]>(bpairs);
    up.Add(new double[] { lmT[0], lmT[1], lmS[0], lmS[1] }); up.Add(new double[] { lmT[2], lmT[3], lmS[2], lmS[3] });
    lo.Add(new double[] { lmT[4], lmT[5], lmS[4], lmS[5] }); lo.Add(new double[] { lmT[6], lmT[7], lmS[6], lmS[7] }); lo.Add(new double[] { lmT[8], lmT[9], lmS[8], lmS[9] }); lo.Add(new double[] { lmT[10], lmT[11], lmS[10], lmS[11] });
    // silhouette rows: upper from the top to the line, lower from the line to the bottom
    double[] ysS = { sTop + 1, sNipY, sLineY - 2 }, ysT = { tTop + 1, tNipY, tLineY - 2 }; int[] cu = { 4, 3 };
    for (int j = 0; j < 2; j++) for (int i = 0; i < cu[j]; i++) { double f = (double)i / cu[j]; int rt = (int)Math.Round(ysT[j] + f * (ysT[j+1] - ysT[j])), rs = (int)Math.Round(ysS[j] + f * (ysS[j+1] - ysS[j]));
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; up.Add(new double[] { tL[rt], rt, sL[rs], rs }); up.Add(new double[] { tR[rt], rt, sR[rs], rs }); }
    double[] ylS = { sLineY + 2, lmS[5], lmS[7], lmS[11], sBot - 2 }, ylT = { tLineY + 2, lmT[5], lmT[7], lmT[11], tBot - 2 }; int[] cl = { 3, 3, 2, 3 };
    for (int j = 0; j < 4; j++) { int c = cl[j] + (j == 3 ? 1 : 0); for (int i = 0; i < c; i++) { double f = (double)i / cl[j]; int rt = (int)Math.Round(ylT[j] + f * (ylT[j+1] - ylT[j])), rs = (int)Math.Round(ylS[j] + f * (ylS[j+1] - ylS[j]));
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; lo.Add(new double[] { tL[rt], rt, sL[rs], rs }); lo.Add(new double[] { tR[rt], rt, sR[rs], rs }); } }
    Spline fu = new Spline(up, lambda), fl = new Spline(lo, lambda);
    int[] dT = OuterDist(tb, tw, th);
    byte[] o = new byte[tw * th * 4];
    for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int idx = (y * tw + x) * 4; if (tb[idx + 3] <= 40) continue;
      bool dk = (tb[idx] + tb[idx+1] + tb[idx+2]) / 3 < 60;
      double yb = tl.YAt(x + 0.5);
      bool upper = y + 0.5 < yb;
      if (dk && (dT[y * tw + x] <= band || (CopyLine && Math.Abs(y + 0.5 - yb) <= 8))) { o[idx] = tb[idx]; o[idx+1] = tb[idx+1]; o[idx+2] = tb[idx+2]; o[idx+3] = tb[idx+3]; continue; }
      double qx, qy; if (upper) fu.Map(x + 0.5, y + 0.5, out qx, out qy); else fl.Map(x + 0.5, y + 0.5, out qx, out qy);
      double al = Sample(shirt, sw, sh, qx, qy, 3); if (al < 128) continue; o[idx + 3] = 255;
      for (int ch = 0; ch < 3; ch++) o[idx + ch] = (byte)Math.Min(255, Sample(shirt, sw, sh, qx, qy, ch) * 255.0 / al); }
    Save(o, tw, th, outPath);
    return "upper pairs " + up.Count + " lower pairs " + lo.Count + " target line y mean " + tLineY.ToString("0") + " source " + sLineY.ToString("0");
  }
  static bool IsDark(byte[] a, int i) { return a[i*4+3] > 40 && (a[i*4] + a[i*4+1] + a[i*4+2]) / 3 < 60; }
  static List<int>[] MakeGrid(bool[] m, int w, int h, int cell, out int gw, out int gh) {
    gw = w / cell + 1; gh = h / cell + 1; var g = new List<int>[gw * gh];
    for (int i = 0; i < m.Length; i++) if (m[i]) { int c = ((i / w) / cell) * gw + (i % w) / cell; if (g[c] == null) g[c] = new List<int>(); g[c].Add(i); }
    return g;
  }
  static bool Nearest(List<int>[] g, int w, int gw, int gh, int cell, double x, double y, double radius, out double nx, out double ny, out double dist) {
    nx = 0; ny = 0; dist = radius; bool found = false; int cx = (int)(x / cell), cy = (int)(y / cell), rc = (int)Math.Ceiling(radius / cell);
    for (int gy = Math.Max(0, cy - rc); gy <= Math.Min(gh - 1, cy + rc); gy++) for (int gx = Math.Max(0, cx - rc); gx <= Math.Min(gw - 1, cx + rc); gx++) {
      var l = g[gy * gw + gx]; if (l == null) continue;
      foreach (int j in l) { double dx = j % w + 0.5 - x, dy = j / w + 0.5 - y; double d = Math.Sqrt(dx*dx + dy*dy); if (d <= dist) { dist = d; nx = j % w + 0.5; ny = j / w + 0.5; found = true; } } }
    return found;
  }
  static List<double[]> Cap(List<double[]> l, int cap) { if (l.Count <= cap) return l; var r = new List<double[]>(); double st = (double)l.Count / cap; for (double i = 0; i < l.Count; i += st) r.Add(l[(int)i]); return r; }
  static string Stats(bool[] from, bool[] to, int w, int h, double radius, string name) {
    int gw, gh; var g = MakeGrid(to, w, h, 8, out gw, out gh); var ds = new List<double>(); int a = 0, b = 0, none = 0;
    for (int i = 0; i < from.Length; i++) if (from[i]) { double nx, ny, d; if (!Nearest(g, w, gw, gh, 8, i % w + 0.5, i / w + 0.5, radius, out nx, out ny, out d)) { none++; d = radius; } ds.Add(d); if (d <= 1.5) a++; if (d <= 3) b++; }
    int n = ds.Count; if (n == 0) return name + ": nothing"; ds.Sort(); double sum = 0; foreach (double d in ds) sum += d;
    return name + ": " + n + " px, mean " + (sum / n).ToString("0.00") + " px, 95th " + ds[(int)(0.95 * (n - 1))].ToString("0.0") + ", max " + ds[n - 1].ToString("0.0") + (none > 0 ? " (" + none + " px had none within " + radius + ", counted as " + radius + ")" : "") + ", within 1.5 px " + (100.0 * a / n).ToString("0.0") + "%, 3 px " + (100.0 * b / n).ToString("0.0") + "%";
  }
  // Layered registration refined both ways (source lines pulled to target lines and back), then the exactness measured.
  public static double[] Extra;
  public static int[] OffL, OffR; public static int OffTop, OffBot, OutlineW = 14; public static byte StrokeGray = 15; public static bool CopyLine = true; public static int FillBlur = 0; public static int[] HoleBoxL; public static string Info2 = ""; public static bool Redraw; public static int InkLuma = 60, FillDilate = 3; public static double TargetWidth = 0; public static string Info = "";
  // Single-layer transfer (no breast layer): one spline from silhouette landmarks and silhouette rows, strokes redrawn, outline from per-row offsets.
  public static string LastSingle = "";
  public static string Single(string srcBody, string srcShirt, string tgtBody, double[] ctrl, double[] rowPairs, string shirtOut, double lambda, int band) {
    int bw, bh, sw, sh, tw, th;
    byte[] sb = Load(srcBody, out bw, out bh), shirt = Load(srcShirt, out sw, out sh), tb = Load(tgtBody, out tw, out th);
    S3.HoleBox = HoleBoxL; CleanBand(shirt, sw, sh, band);
    StrokeData sd = null;
    if (Redraw) { string info; sd = S3.Prepare(shirt, sw, sh, band, InkLuma, FillDilate, out info); Info = info; }
    S3.HoleBox = null;
    int[] sL = new int[bh], sR = new int[bh], tL = new int[th], tR = new int[th]; int sTop, sBot, tTop, tBot;
    Extents(sb, bw, bh, sL, sR, out sTop, out sBot); Extents(tb, tw, th, tL, tR, out tTop, out tBot);
    List<double[]> pairs = new List<double[]>();
    for (int i = 0; i + 3 < ctrl.Length; i += 4) pairs.Add(new double[] { ctrl[i], ctrl[i+1], ctrl[i+2], ctrl[i+3] });
    for (int i = 0; i + 1 < rowPairs.Length; i += 2) { int rt = (int)Math.Round(rowPairs[i]), rs = (int)Math.Round(rowPairs[i+1]);
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; pairs.Add(new double[] { tL[rt], rt, sL[rs], rs }); pairs.Add(new double[] { tR[rt] + 1, rt, sR[rs] + 1, rs }); }
    Spline inv = new Spline(pairs, lambda); List<double[]> sw2 = new List<double[]>(); foreach (var p in pairs) sw2.Add(new double[] { p[2], p[3], p[0], p[1] }); Spline fwd = new Spline(sw2, lambda);
    string res = "control pairs " + pairs.Count; double worst = 0;
    string wp = ""; foreach (var p in pairs) { double qx, qy; inv.Map(p[0], p[1], out qx, out qy); double m = Math.Sqrt((qx - p[2]) * (qx - p[2]) + (qy - p[3]) * (qy - p[3])); if (m > worst) { worst = m; wp = " at t(" + p[0].ToString("0") + "," + p[1].ToString("0") + ") s(" + p[2].ToString("0") + "," + p[3].ToString("0") + ")"; } }
    res += ", worst control residual " + worst.ToString("0.00") + " px" + wp;
    bool[] inS = new bool[tw * th];
    for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { double qx, qy; inv.Map(x + 0.5, y + 0.5, out qx, out qy); if (Sample(shirt, sw, sh, qx, qy, 3) >= 128) inS[y * tw + x] = true; }
    byte[] sp = new byte[tw * th * 4]; for (int i = 0; i < tw * th; i++) if (inS[i]) sp[i * 4 + 3] = 255;
    int[] dT = OuterDist(sp, tw, th);
    byte[] o = new byte[tw * th * 4];
    for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int idx = (y * tw + x) * 4; if (!inS[y * tw + x]) continue;
      double qx, qy; inv.Map(x + 0.5, y + 0.5, out qx, out qy);
      if (dT[y * tw + x] <= OutlineW) { o[idx] = 0; o[idx+1] = 0; o[idx+2] = 0; o[idx+3] = 255; continue; }
      double al = Sample(shirt, sw, sh, qx, qy, 3);
      if (al < 128) { o[idx] = 255; o[idx+1] = 255; o[idx+2] = 255; o[idx+3] = 255; continue; }
      o[idx + 3] = 255; for (int ch = 0; ch < 3; ch++) o[idx + ch] = (byte)Math.Min(255, Sample(shirt, sw, sh, qx, qy, ch) * 255.0 / al); }
    if (Redraw) {
      Func<double, double, double[]> fm = (px2, py2) => { double ax, ay; fwd.Map(px2, py2, out ax, out ay); return new double[] { ax, ay }; };
      if (FillBlur > 0) { int rad = FillBlur; byte[] src = (byte[])o.Clone(); bool[] fillM = new bool[tw * th]; for (int i = 0; i < tw * th; i++) fillM[i] = o[i*4+3] > 0 && dT[i] > OutlineW;
        for (int pass = 0; pass < 3; pass++) { byte[] dst = (byte[])src.Clone();
          for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int i = y * tw + x; if (!fillM[i]) continue; double r = 0, g = 0, b = 0; int n = 0;
            for (int dy = -rad; dy <= rad; dy++) { int yy = y + dy; if (yy < 0 || yy >= th) continue; for (int dx = -rad; dx <= rad; dx++) { int xx = x + dx; if (xx < 0 || xx >= tw) continue; int j = yy * tw + xx; if (!fillM[j]) continue; r += src[j*4+2]; g += src[j*4+1]; b += src[j*4]; n++; } }
            if (n > 0) { dst[i*4+2] = (byte)(r / n); dst[i*4+1] = (byte)(g / n); dst[i*4] = (byte)(b / n); } }
          src = dst; }
        for (int i = 0; i < tw * th; i++) if (fillM[i]) { o[i*4] = src[i*4]; o[i*4+1] = src[i*4+1]; o[i*4+2] = src[i*4+2]; } }
      S3.Inside = null; S3.Dropped = 0;
      byte[] strokeA = S3.Draw(sd, fm, tw, th, TargetWidth, 4); res += ", dropped paths " + S3.Dropped;
      for (int i = 0; i < tw * th; i++) if (inS[i] && dT[i] > OutlineW && strokeA[i] >= 115) { o[i*4] = StrokeGray; o[i*4+1] = StrokeGray; o[i*4+2] = (byte)(StrokeGray + 3); o[i*4+3] = 255; }
    }
    Save(o, tw, th, shirtOut);
    LastSingle = res; return res;
  }
  // Independent checks of a body-to-body map: the source silhouette pushed through it against the target silhouette (distance transform both ways), and leave-one-out residuals of each landmark.
  static bool[] Edge(byte[] a, int w, int h) { bool[] e = new bool[w * h]; for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { if (a[(y*w+x)*4+3] <= 40) continue; bool b = x == 0 || y == 0 || x == w-1 || y == h-1 || a[(y*w+x-1)*4+3] <= 40 || a[(y*w+x+1)*4+3] <= 40 || a[((y-1)*w+x)*4+3] <= 40 || a[((y+1)*w+x)*4+3] <= 40; e[y*w+x] = b; } return e; }
  static string DStats(List<double> d, string name) { if (d.Count == 0) return name + ": none"; d.Sort(); double m = 0; foreach (double v in d) m += v; return name + ": mean " + (m / d.Count).ToString("0.00") + " 95th " + d[(int)(0.95 * (d.Count - 1))].ToString("0.0") + " max " + d[d.Count - 1].ToString("0.0"); }
  static List<double[]> BuildPairs(double[] ctrl, double[] rowPairs, int[] sL, int[] sR, int[] tL, int[] tR, int bh, int th, int skipPair, double skipRow) {
    List<double[]> pairs = new List<double[]>();
    for (int i = 0; i + 3 < ctrl.Length; i += 4) { if (i / 4 == skipPair) continue; pairs.Add(new double[] { ctrl[i], ctrl[i+1], ctrl[i+2], ctrl[i+3] }); }
    for (int i = 0; i + 1 < rowPairs.Length; i += 2) { if (skipRow >= 0 && Math.Abs(rowPairs[i] - skipRow) <= 10) continue; int rt = (int)Math.Round(rowPairs[i]), rs = (int)Math.Round(rowPairs[i+1]);
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; pairs.Add(new double[] { tL[rt], rt, sL[rs], rs }); pairs.Add(new double[] { tR[rt] + 1, rt, sR[rs] + 1, rs }); }
    return pairs;
  }
  public static string MapCheck(string srcBody, string tgtBody, double[] ctrl, double[] rowPairs, double lambda, string[] names, int nLoo) {
    int bw, bh, tw, th; byte[] sb = Load(srcBody, out bw, out bh), tb = Load(tgtBody, out tw, out th);
    int[] sL = new int[bh], sR = new int[bh], tL = new int[th], tR = new int[th]; int a, b, c, d; Extents(sb, bw, bh, sL, sR, out a, out b); Extents(tb, tw, th, tL, tR, out c, out d);
    List<double[]> all = BuildPairs(ctrl, rowPairs, sL, sR, tL, tR, bh, th, -1, -1);
    Spline inv = new Spline(all, lambda); List<double[]> sw2 = new List<double[]>(); foreach (var p in all) sw2.Add(new double[] { p[2], p[3], p[0], p[1] }); Spline fwd = new Spline(sw2, lambda);
    bool[] se = Edge(sb, bw, bh), te = Edge(tb, tw, th);
    bool[] notT = new bool[tw * th], notS = new bool[bw * bh]; for (int i = 0; i < notT.Length; i++) { notT[i] = !te[i]; notS[i] = !se[i]; }
    double[] dT = S3.Edt(notT, tw, th), dS = S3.Edt(notS, bw, bh);
    List<double> f = new List<double>(), r = new List<double>();
    for (int i = 0; i < se.Length; i++) if (se[i]) { double mx, my; fwd.Map(i % bw + 0.5, i / bw + 0.5, out mx, out my); int xi = (int)mx, yi = (int)my; f.Add(xi < 0 || yi < 0 || xi >= tw || yi >= th ? 50 : dT[yi * tw + xi]); }
    for (int i = 0; i < te.Length; i++) if (te[i]) { double mx, my; inv.Map(i % tw + 0.5, i / tw + 0.5, out mx, out my); int xi = (int)mx, yi = (int)my; r.Add(xi < 0 || yi < 0 || xi >= bw || yi >= bh ? 50 : dS[yi * bw + xi]); }
    string res = DStats(f, "source edge to target edge") + " | " + DStats(r, "target edge to source edge") + "\n    leave-one-out (landmark and its rows +-10 left out): ";
    double worst = 0; string worstName = "";
    for (int i = 0; i < nLoo; i++) { double sk = ctrl[i*4+1]; List<double[]> p = BuildPairs(ctrl, rowPairs, sL, sR, tL, tR, bh, th, i, sk); Spline iv = new Spline(p, lambda); double qx, qy; iv.Map(ctrl[i*4], ctrl[i*4+1], out qx, out qy);
      double e = Math.Sqrt((qx - ctrl[i*4+2]) * (qx - ctrl[i*4+2]) + (qy - ctrl[i*4+3]) * (qy - ctrl[i*4+3])); string nm = names != null && i < names.Length ? names[i] : ("p" + i); res += nm + " " + e.ToString("0.0") + "; "; if (e > worst) { worst = e; worstName = nm; } }
    return res + "\n    worst leave-one-out " + worst.ToString("0.0") + " px (" + worstName + ")";
  }
  public static string Exact(string srcBody, string srcShirt, string tgtBody, double[] lmS, double[] lmT,
      int[] sLx, int[] sLy, int[] sRx, int[] sRy, int[] tLx, int[] tLy, int[] tRx, int[] tRy, string rawOut, string shirtOut, string refShirt, int iters, double lambda, double radius, int band) {
    int bw, bh, sw, sh, tw, th;
    byte[] sb = Load(srcBody, out bw, out bh), shirt = Load(srcShirt, out sw, out sh), tb = Load(tgtBody, out tw, out th);
    S3.HoleBox = HoleBoxL; CleanBand(shirt, sw, sh, band);
    StrokeData sd = null;
    if (Redraw) { string info; sd = S3.Prepare(shirt, sw, sh, band, InkLuma, FillDilate, out info); Info = info; }
    S3.HoleBox = null;
    int[] sL = new int[bh], sR = new int[bh], tL = new int[th], tR = new int[th]; int sTop, sBot, tTop, tBot;
    Extents(sb, bw, bh, sL, sR, out sTop, out sBot); Extents(tb, tw, th, tL, tR, out tTop, out tBot);
    Line sl = new Line(sLx, sLy, sRx, sRy), tl = new Line(tLx, tLy, tRx, tRy);
    List<double[]> bpairs = new List<double[]>(); int nb = 28;
    for (int i = 0; i <= nb; i++) { double u = (double)i / nb, a, b, c, d; tl.At(u, out a, out b); sl.At(u, out c, out d); bpairs.Add(new double[] { a, b, c, d }); }
    double sLineY = 0, tLineY = 0; for (int i = 0; i < sl.y.Length; i++) sLineY += sl.y[i]; sLineY /= sl.y.Length; for (int i = 0; i < tl.y.Length; i++) tLineY += tl.y[i]; tLineY /= tl.y.Length;
    double sNipY = (lmS[1] + lmS[3]) / 2, tNipY = (lmT[1] + lmT[3]) / 2;
    List<double[]> up = new List<double[]>(bpairs), lo = new List<double[]>(bpairs);
    up.Add(new double[] { lmT[0], lmT[1], lmS[0], lmS[1] }); up.Add(new double[] { lmT[2], lmT[3], lmS[2], lmS[3] });
    lo.Add(new double[] { lmT[4], lmT[5], lmS[4], lmS[5] }); lo.Add(new double[] { lmT[6], lmT[7], lmS[6], lmS[7] }); lo.Add(new double[] { lmT[8], lmT[9], lmS[8], lmS[9] }); lo.Add(new double[] { lmT[10], lmT[11], lmS[10], lmS[11] });
    double[] ysS = { sTop + 1, sNipY, sLineY - 2 }, ysT = { tTop + 1, tNipY, tLineY - 2 }; int[] cu = { 4, 3 };
    for (int j = 0; j < 2; j++) for (int i = 0; i < cu[j]; i++) { double f = (double)i / cu[j]; int rt = (int)Math.Round(ysT[j] + f * (ysT[j+1] - ysT[j])), rs = (int)Math.Round(ysS[j] + f * (ysS[j+1] - ysS[j]));
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; up.Add(new double[] { tL[rt], rt, sL[rs], rs }); up.Add(new double[] { tR[rt], rt, sR[rs], rs }); }
    double[] ylS = { sLineY + 2, lmS[5], lmS[7], lmS[11], sBot - 2 }, ylT = { tLineY + 2, lmT[5], lmT[7], lmT[11], tBot - 2 }; int[] cl = { 3, 3, 2, 3 };
    for (int j = 0; j < 4; j++) { int c = cl[j] + (j == 3 ? 1 : 0); for (int i = 0; i < c; i++) { double f = (double)i / cl[j]; int rt = (int)Math.Round(ylT[j] + f * (ylT[j+1] - ylT[j])), rs = (int)Math.Round(ylS[j] + f * (ylS[j+1] - ylS[j]));
      if (rt < 0 || rt >= th || rs < 0 || rs >= bh || tL[rt] < 0 || sL[rs] < 0) continue; lo.Add(new double[] { tL[rt], rt, sL[rs], rs }); lo.Add(new double[] { tR[rt], rt, sR[rs], rs }); } }
    if (Extra != null) for (int i = 0; i + 3 < Extra.Length; i += 4) up.Add(new double[] { Extra[i], Extra[i+1], Extra[i+2], Extra[i+3] });
    List<double[]>[] baseP = { up, lo };
    bool[] tD = new bool[tw * th], sD = new bool[bw * bh];
    for (int i = 0; i < tD.Length; i++) tD[i] = IsDark(tb, i); for (int i = 0; i < sD.Length; i++) sD[i] = IsDark(sb, i);
    int tgw, tgh, sgw, sgh; var tGrid = MakeGrid(tD, tw, th, 8, out tgw, out tgh); var sGrid = MakeGrid(sD, bw, bh, 8, out sgw, out sgh);
    List<int> sSamp = new List<int>(), tSamp = new List<int>(); int cs = 0, ct = 0;
    for (int i = 0; i < sD.Length; i++) if (sD[i]) { cs++; if (cs % 9 == 0) sSamp.Add(i); }
    for (int i = 0; i < tD.Length; i++) if (tD[i]) { ct++; if (ct % 9 == 0) tSamp.Add(i); }
    List<double[]>[] pairs = { new List<double[]>(up), new List<double[]>(lo) };
    Spline[] inv = new Spline[2], fwd = new Spline[2];
    Action build = () => { for (int l = 0; l < 2; l++) { inv[l] = new Spline(pairs[l], lambda); List<double[]> sw2 = new List<double[]>(); foreach (var p in pairs[l]) sw2.Add(new double[] { p[2], p[3], p[0], p[1] }); fwd[l] = new Spline(sw2, lambda); } };
    build();
    string log = "";
    for (int it = 0; it < iters; it++) {
      List<double[]>[] add = { new List<double[]>(), new List<double[]>() };
      foreach (int i in sSamp) { double sx = i % bw + 0.5, sy = i / bw + 0.5; int l = sy < sl.YAt(sx) ? 0 : 1; double mx, my; fwd[l].Map(sx, sy, out mx, out my);
        double nx, ny, d; if (!Nearest(tGrid, tw, tgw, tgh, 8, mx, my, radius, out nx, out ny, out d)) continue; int lt = ny < tl.YAt(nx) ? 0 : 1; if (lt != l) continue; add[l].Add(new double[] { nx, ny, sx, sy }); }
      foreach (int i in tSamp) { double tx = i % tw + 0.5, ty = i / tw + 0.5; int l = ty < tl.YAt(tx) ? 0 : 1; double qx, qy; inv[l].Map(tx, ty, out qx, out qy);
        double nx, ny, d; if (!Nearest(sGrid, bw, sgw, sgh, 8, qx, qy, radius, out nx, out ny, out d)) continue; int ls = ny < sl.YAt(nx) ? 0 : 1; if (ls != l) continue; add[l].Add(new double[] { tx, ty, nx, ny }); }
      for (int l = 0; l < 2; l++) { pairs[l] = new List<double[]>(baseP[l]); pairs[l].AddRange(Cap(add[l], 230)); }
      build(); log += (it == 0 || it == iters - 1) ? " it" + it + " pairs " + pairs[0].Count + "/" + pairs[1].Count : "";
    }
    if (Extra != null) { string rs2 = ""; for (int i = 0; i + 3 < Extra.Length; i += 4) { double qx0, qy0; inv[0].Map(Extra[i], Extra[i+1], out qx0, out qy0); rs2 += " (" + Extra[i] + "," + Extra[i+1] + ")->(" + qx0.ToString("0.0") + "," + qy0.ToString("0.0") + ") wanted (" + Extra[i+2] + "," + Extra[i+3] + ") miss " + Math.Sqrt((qx0-Extra[i+2])*(qx0-Extra[i+2]) + (qy0-Extra[i+3])*(qy0-Extra[i+3])).ToString("0.0") + " px;"; } Info2 = rs2; }
    byte[] sp = new byte[tw * th * 4]; bool[] inS = new bool[tw * th];
    bool[] bodyM = new bool[tw * th], notBody = new bool[tw * th]; for (int i = 0; i < tw * th; i++) { bodyM[i] = tb[i * 4 + 3] > 40; notBody[i] = !bodyM[i]; }
    double[] distB = (OffL != null) ? S3.Edt(notBody, tw, th) : null;
    for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int i = y * tw + x; if (bodyM[i]) { inS[i] = true; continue; } if (distB == null) continue;
      double d; if (y < tTop) d = OffTop; else if (y > tBot) d = OffBot; else d = x < tw / 2 ? (y < OffL.Length ? OffL[y] : 0) : (y < OffR.Length ? OffR[y] : 0);
      if (distB[i] <= d) inS[i] = true; }
    for (int i = 0; i < tw * th; i++) if (inS[i]) sp[i * 4 + 3] = 255;
    int[] dT = OuterDist(sp, tw, th);
    byte[] raw = new byte[tw * th * 4], o = new byte[tw * th * 4]; bool[] W = new bool[tw * th], oD = new bool[tw * th];
    for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int idx = (y * tw + x) * 4; if (!inS[y * tw + x]) continue;
      int l = y + 0.5 < tl.YAt(x + 0.5) ? 0 : 1; double qx, qy; inv[l].Map(x + 0.5, y + 0.5, out qx, out qy);
      double sa = Sample(sb, bw, bh, qx, qy, 3);
      if (sa >= 40) { double lum = (Sample(sb, bw, bh, qx, qy, 0) + Sample(sb, bw, bh, qx, qy, 1) + Sample(sb, bw, bh, qx, qy, 2)) / 3.0 * 255.0 / sa; if (lum < 60) { raw[idx] = 0; raw[idx+1] = 0; raw[idx+2] = 255; raw[idx+3] = 255; W[y * tw + x] = true; } }
      if (dT[y * tw + x] <= OutlineW) { o[idx] = 0; o[idx+1] = 0; o[idx+2] = 0; o[idx+3] = 255; continue; }
      bool dk = tD[y * tw + x]; double yb = tl.YAt(x + 0.5);
      if (CopyLine && dk && Math.Abs(y + 0.5 - yb) <= 8) { o[idx] = tb[idx]; o[idx+1] = tb[idx+1]; o[idx+2] = tb[idx+2]; o[idx+3] = tb[idx+3]; continue; }
      double al = Sample(shirt, sw, sh, qx, qy, 3);
      if (al < 128) { o[idx] = 255; o[idx+1] = 255; o[idx+2] = 255; o[idx+3] = 255; continue; }
      o[idx + 3] = 255; for (int ch = 0; ch < 3; ch++) o[idx + ch] = (byte)Math.Min(255, Sample(shirt, sw, sh, qx, qy, ch) * 255.0 / al);
      if ((o[idx] + o[idx+1] + o[idx+2]) / 3 < 60 && dT[y * tw + x] > band) oD[y * tw + x] = true; }
    if (Redraw) {
      Func<double, double, double[]> fm = (px2, py2) => { int l = py2 < sl.YAt(px2) ? 0 : 1; double ax, ay; fwd[l].Map(px2, py2, out ax, out ay); return new double[] { ax, ay }; };
    if (FillBlur > 0) { // low-pass of the warped fill: box blur FillBlur px, three passes, over the garment pixels only (not the outline, not the strokes); ink is re-added after
      int rad = FillBlur; byte[] src = (byte[])o.Clone(); bool[] fillM = new bool[tw * th]; for (int i = 0; i < tw * th; i++) fillM[i] = o[i*4+3] > 0 && dT[i] > OutlineW;
      for (int pass = 0; pass < 3; pass++) { byte[] dst = (byte[])src.Clone();
        for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { int i = y * tw + x; if (!fillM[i]) continue; double r = 0, g = 0, b = 0; int n = 0;
          for (int dy = -rad; dy <= rad; dy++) { int yy = y + dy; if (yy < 0 || yy >= th) continue; for (int dx = -rad; dx <= rad; dx++) { int xx = x + dx; if (xx < 0 || xx >= tw) continue; int j = yy * tw + xx; if (!fillM[j]) continue; r += src[j*4+2]; g += src[j*4+1]; b += src[j*4]; n++; } }
          if (n > 0) { dst[i*4+2] = (byte)(r / n); dst[i*4+1] = (byte)(g / n); dst[i*4] = (byte)(b / n); } }
        src = dst; }
      for (int i = 0; i < tw * th; i++) if (fillM[i]) { o[i*4] = src[i*4]; o[i*4+1] = src[i*4+1]; o[i*4+2] = src[i*4+2]; } }
      S3.Inside = (ix, iy) => { int xi = (int)ix, yi = (int)iy; if (xi < 0 || yi < 0 || xi >= tw || yi >= th) return false; int ii = yi * tw + xi; return inS[ii] && dT[ii] > OutlineW - 2; }; S3.Dropped = 0;
      byte[] strokeA = S3.Draw(sd, fm, tw, th, TargetWidth, 4); Info2 += " dropped paths " + S3.Dropped + " source-band paths " + S3.DroppedSource + " above-ring paths " + S3.DroppedAbove; S3.DroppedSource = 0; S3.DroppedAbove = 0;
      for (int i = 0; i < tw * th; i++) if (inS[i] && dT[i] > OutlineW && strokeA[i] >= 115) { o[i*4] = StrokeGray; o[i*4+1] = StrokeGray; o[i*4+2] = (byte)(StrokeGray + 3); o[i*4+3] = 255; }
      for (int i = 0; i < tw * th; i++) oD[i] = o[i*4+3] > 40 && (o[i*4] + o[i*4+1] + o[i*4+2]) / 3 < 60 && dT[i] > band;
    }
    Save(raw, tw, th, rawOut); Save(o, tw, th, shirtOut);
    string res = "pairs" + log + "\n  body lines  " + Stats(tD, W, tw, th, 40, "target->warped") + "\n  body lines  " + Stats(W, tD, tw, th, 40, "warped->target");
    if (refShirt.Length > 0) {
      int rw, rh; byte[] rf = Load(refShirt, out rw, out rh); bool[] rD = new bool[tw * th];
      for (int i = 0; i < rD.Length; i++) rD[i] = IsDark(rf, i) && dT[i] > band;
      res += "\n  shirt lines vs WDI's own shirt (inside the outline band): " + Stats(rD, oD, tw, th, 40, "WDI->ours") + " | " + Stats(oD, rD, tw, th, 40, "ours->WDI");
    }
    return res;
  }
}
public class StrokeData { public List<double[]>[] Paths; public double MedianWidth; public int Count; }
public static class S3 {
  const double INF = 1e12;
  public static double RingTopY = 0; public static int DroppedAbove = 0; public static int SourceBand = 0, DroppedSource = 0; public static Func<double, double, bool> Inside; public static int Dropped; public static int[] HoleBox; public static double RadiusBias = 0; public static byte[] ApplyHole(byte[] a, int w, int h) { if (HoleBox == null) return a; byte[] c = (byte[])a.Clone(); for (int y = HoleBox[1]; y <= HoleBox[3]; y++) for (int x = HoleBox[0]; x <= HoleBox[2]; x++) { int i = (y * w + x) * 4 + 3; if (c[i] <= 40) c[i] = 255; } return c; }
  public static double LastMedian; public static bool Bridge; public static List<double[]> LastEnds;
  static void Dt1(double[] f, int n, double[] d, int[] v, double[] z) {
    int k = 0; v[0] = 0; z[0] = -INF; z[1] = INF;
    for (int q = 1; q < n; q++) { double s; while (true) { s = ((f[q] + (double)q * q) - (f[v[k]] + (double)v[k] * v[k])) / (2.0 * q - 2.0 * v[k]); if (s <= z[k]) k--; else break; if (k < 0) { k = 0; break; } } k++; v[k] = q; z[k] = s; z[k + 1] = INF; }
    k = 0; for (int q = 0; q < n; q++) { while (z[k + 1] < q) k++; d[q] = (q - v[k]) * (double)(q - v[k]) + f[v[k]]; }
  }
  // Euclidean distance from each foreground pixel to the nearest background pixel (background: 0).
  public static double[] Edt(bool[] fg, int w, int h) {
    double[] g = new double[w * h]; int m = Math.Max(w, h); double[] f = new double[m], d = new double[m], z = new double[m + 1]; int[] v = new int[m];
    for (int x = 0; x < w; x++) { for (int y = 0; y < h; y++) f[y] = fg[y * w + x] ? INF : 0; Dt1(f, h, d, v, z); for (int y = 0; y < h; y++) g[y * w + x] = d[y]; }
    for (int y = 0; y < h; y++) { for (int x = 0; x < w; x++) f[x] = g[y * w + x]; Dt1(f, w, d, v, z); for (int x = 0; x < w; x++) g[y * w + x] = Math.Sqrt(d[x]); }
    return g;
  }
  public static bool[] Thin(bool[] src, int w, int h) {
    bool[] a = (bool[])src.Clone(); bool changed = true; List<int> del = new List<int>();
    int[] dx = { 0, 1, 1, 1, 0, -1, -1, -1 }, dy = { -1, -1, 0, 1, 1, 1, 0, -1 };
    while (changed) { changed = false;
      for (int pass = 0; pass < 2; pass++) { del.Clear();
        for (int y = 1; y < h - 1; y++) for (int x = 1; x < w - 1; x++) { if (!a[y*w+x]) continue; int[] p = new int[8]; int b = 0; for (int k = 0; k < 8; k++) { p[k] = a[(y+dy[k])*w + x+dx[k]] ? 1 : 0; b += p[k]; }
          if (b < 2 || b > 6) continue; int t = 0; for (int k = 0; k < 8; k++) if (p[k] == 0 && p[(k+1)%8] == 1) t++; if (t != 1) continue;
          if (pass == 0) { if (p[0]*p[2]*p[4] != 0 || p[2]*p[4]*p[6] != 0) continue; } else { if (p[0]*p[2]*p[6] != 0 || p[0]*p[4]*p[6] != 0) continue; }
          del.Add(y*w+x); }
        if (del.Count > 0) { changed = true; foreach (int i in del) a[i] = false; } } }
    return a;
  }
  static int[] OuterDistS(byte[] a, int w, int h) {
    a = ApplyHole(a, w, h);
    int[] d = new int[w * h]; for (int i = 0; i < d.Length; i++) d[i] = -1; Queue<int> q = new Queue<int>();
    for (int x = 0; x < w; x++) { Sd(a, w, d, q, x, 0); Sd(a, w, d, q, x, h - 1); } for (int y = 0; y < h; y++) { Sd(a, w, d, q, 0, y); Sd(a, w, d, q, w - 1, y); }
    while (q.Count > 0) { int i = q.Dequeue(); int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (d[j] == -1 && a[j*4+3] <= 40) { d[j] = 0; q.Enqueue(j); } } }
    Queue<int> q2 = new Queue<int>(); for (int i = 0; i < d.Length; i++) if (d[i] == 0) q2.Enqueue(i);
    while (q2.Count > 0) { int i = q2.Dequeue(); int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (d[j] == -1 && a[j*4+3] > 40) { d[j] = d[i] + 1; q2.Enqueue(j); } } }
    for (int i = 0; i < d.Length; i++) if (d[i] < 0) d[i] = 100000;
    return d;
  }
  static void Sd(byte[] a, int w, int[] d, Queue<int> q, int x, int y) { int i = y * w + x; if (d[i] == -1 && a[i*4+3] <= 40) { d[i] = 0; q.Enqueue(i); } }
  static double Lum(byte[] a, int i) { return (a[i*4] + a[i*4+1] + a[i*4+2]) / 3.0; }
  public static byte[] Region;
  public static bool RelativeInk; public static int RelDrop = 40;
  public static bool[] InkMask(byte[] a, int w, int h, int band, int inkLuma) {
    int[] dOut = OuterDistS(Region != null ? Region : a, w, h); bool[] ink = new bool[w * h];
    if (!RelativeInk) { for (int i = 0; i < ink.Length; i++) ink[i] = a[i*4+3] > 40 && Lum(a, i) < inkLuma && dOut[i] > band; return ink; }
    double[] integ = new double[(w + 1) * (h + 1)]; double[] lm = new double[w * h]; for (int i = 0; i < lm.Length; i++) lm[i] = a[i*4+3] > 40 ? Lum(a, i) : 255.0;
    for (int y = 0; y < h; y++) { double row = 0; for (int x = 0; x < w; x++) { row += lm[y*w+x]; integ[(y+1)*(w+1)+x+1] = integ[y*(w+1)+x+1] + row; } }
    int r = 7;
    for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { int i = y*w+x; if (a[i*4+3] <= 40 || dOut[i] <= band) continue; int x0 = Math.Max(0, x - r), x1 = Math.Min(w, x + r + 1), y0 = Math.Max(0, y - r), y1 = Math.Min(h, y + r + 1);
      double s = integ[y1*(w+1)+x1] - integ[y0*(w+1)+x1] - integ[y1*(w+1)+x0] + integ[y0*(w+1)+x0]; double mean = s / ((x1 - x0) * (y1 - y0)); ink[i] = lm[i] < mean - RelDrop; }
    return ink;
  }
  // ring: the largest ink piece inside a box, its skeleton, n points taken by angle around the box centre (angle 0 = right, counter-clockwise on screen)
  public static double[] RingPointsBox(byte[] a, int w, int h, int band, int inkLuma, int bx0, int by0, int bx1, int by1, int n) {
    bool[] ink = InkMask(a, w, h, band, inkLuma); for (int i = 0; i < ink.Length; i++) { int x = i % w, y = i / w; if (x < bx0 || x > bx1 || y < by0 || y > by1) ink[i] = false; }
    int tot = w * h; bool[] seen = new bool[tot]; List<int> best = new List<int>(); Queue<int> q = new Queue<int>();
    for (int s = 0; s < tot; s++) { if (!ink[s] || seen[s]) continue; List<int> comp = new List<int>(); seen[s] = true; q.Enqueue(s);
      while (q.Count > 0) { int i = q.Dequeue(); comp.Add(i); int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (ink[j] && !seen[j]) { seen[j] = true; q.Enqueue(j); } } }
      if (comp.Count > best.Count) best = comp; }
    bool[] piece = new bool[tot]; foreach (int i in best) piece[i] = true; bool[] sk = Thin(piece, w, h);
    double cx = (bx0 + bx1) / 2.0, cy = (by0 + by1) / 2.0; double[] res = new double[2 * n];
    for (int k = 0; k < n; k++) { double th = 2 * Math.PI * k / n; double bd = 1e9; double px = cx, py = cy;
      for (int i = 0; i < tot; i++) if (sk[i]) { double x = i % w + 0.5, y = i / w + 0.5; double ang = Math.Atan2(-(y - cy), x - cx); if (ang < 0) ang += 2 * Math.PI; double d = Math.Abs(ang - th); d = Math.Min(d, 2 * Math.PI - d); if (d < bd) { bd = d; px = x; py = y; } }
      res[2*k] = px; res[2*k+1] = py; }
    return res;
  }
  public static string RingBoxIn(byte[] a, int w, int h, int band, int inkLuma, int bx0, int by0, int bx1, int by1) {
    bool[] ink = InkMask(a, w, h, band, inkLuma); int tot = w * h; bool[] seen = new bool[tot]; int bestN = 0, X0 = 0, Y0 = 0, X1 = 0, Y1 = 0; Queue<int> q = new Queue<int>();
    for (int s = 0; s < tot; s++) { int sx = s % w, sy = s / w; if (!ink[s] || seen[s] || sx < bx0 || sx > bx1 || sy < by0 || sy > by1) continue; int cnt = 0, x0 = w, y0 = h, x1 = 0, y1 = 0; seen[s] = true; q.Enqueue(s);
      while (q.Count > 0) { int i = q.Dequeue(); cnt++; int x = i % w, y = i / w; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx < bx0 || xx > bx1 || yy < by0 || yy > by1) continue; int j = yy*w+xx; if (ink[j] && !seen[j]) { seen[j] = true; q.Enqueue(j); } } }
      if (cnt > bestN) { bestN = cnt; X0 = x0; Y0 = y0; X1 = x1; Y1 = y1; } }
    return "ring piece " + bestN + " px, bbox (" + X0 + "," + Y0 + ")-(" + X1 + "," + Y1 + "), " + (X1 - X0 + 1) + " x " + (Y1 - Y0 + 1);
  }
  public static string Otsu3(byte[] a, int w, int h, int band) {
    int[] dOut = OuterDistS(a, w, h); double[] hist = new double[256]; double n = 0;
    for (int i = 0; i < w * h; i++) if (a[i*4+3] > 40 && dOut[i] > band) { hist[(int)Lum(a, i)]++; n++; }
    if (n == 0) return "no pixels"; double mu = 0; for (int i = 0; i < 256; i++) mu += i * hist[i]; mu /= n;
    double best = -1; int b1 = 0, b2 = 0;
    for (int t1 = 1; t1 < 254; t1++) { double w0 = 0, m0 = 0; for (int i = 0; i <= t1; i++) { w0 += hist[i]; m0 += i * hist[i]; } if (w0 == 0) continue;
      double w1 = 0, m1 = 0; for (int t2 = t1 + 1; t2 < 255; t2++) { w1 += hist[t2]; m1 += t2 * hist[t2]; if (w1 == 0) continue; double w2 = n - w0 - w1; if (w2 <= 0) continue; double m2 = mu * n - m0 - m1;
        double v = w0 * Math.Pow(m0 / w0 - mu, 2) + w1 * Math.Pow(m1 / w1 - mu, 2) + w2 * Math.Pow(m2 / w2 - mu, 2); if (v > best) { best = v; b1 = t1; b2 = t2; } } }
    double c0 = 0, c1 = 0; for (int i = 0; i < 256; i++) { if (i <= b1) c0 += hist[i]; else if (i <= b2) c1 += hist[i]; }
    return "multi-Otsu 3 classes on " + n + " interior pixels: ink up to " + b1 + " (" + (100 * c0 / n).ToString("0.0") + "%), shading " + (b1 + 1) + ".." + b2 + " (" + (100 * c1 / n).ToString("0.0") + "%), fill above (" + (100 * (n - c0 - c1) / n).ToString("0.0") + "%)";
  }
  class Node { public List<int> N = new List<int>(); }
  // Skeleton traced into ordered paths of (x, y, r); r = Euclidean radius of the ink at the skeleton pixel.
  static List<double[]>[] Trace(bool[] skel, double[] edt, int w, int h, out int count) {
    int n = w * h; int[] deg = new int[n]; List<int>[] nb = new List<int>[n];
    for (int i = 0; i < n; i++) if (skel[i]) { int x = i % w, y = i / w; nb[i] = new List<int>(); for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { if (dx == 0 && dy == 0) continue; int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (skel[j]) nb[i].Add(j); } deg[i] = nb[i].Count; }
    bool[] visited = new bool[n]; List<List<double[]>> paths = new List<List<double[]>>();
    Func<int, double[]> P = i => new double[] { i % w + 0.5, i / w + 0.5, Math.Max(0.6, edt[i] - 0.5) };
    for (int s = 0; s < n; s++) { if (!skel[s] || deg[s] == 2) continue;
      foreach (int m in nb[s]) { if (deg[m] == 2 && visited[m]) continue; if (deg[m] != 2 && m < s) continue;
        List<double[]> path = new List<double[]>(); path.Add(P(s)); int prev = s, cur = m;
        while (true) { path.Add(P(cur)); if (deg[cur] != 2) break; visited[cur] = true; int next = -1; foreach (int q in nb[cur]) if (q != prev) { next = q; break; } if (next < 0 || (deg[next] == 2 && visited[next])) break; prev = cur; cur = next; }
        paths.Add(path); } }
    for (int s = 0; s < n; s++) { if (!skel[s] || deg[s] != 2 || visited[s]) continue; List<double[]> path = new List<double[]>(); int prev = -1, cur = s;
      while (true) { visited[cur] = true; path.Add(P(cur)); int next = -1; foreach (int q in nb[cur]) if (q != prev && !visited[q]) { next = q; break; } if (next < 0) break; prev = cur; cur = next; }
      path.Add(P(s)); paths.Add(path); }
    for (int i = 0; i < n; i++) if (skel[i] && deg[i] == 0) paths.Add(new List<double[]> { P(i) });
    LastEnds = new List<double[]>(); for (int i = 0; i < n; i++) if (skel[i] && deg[i] == 1) LastEnds.Add(P(i));
    count = paths.Count; return paths.ToArray();
  }
  static void Smooth(List<double[]> p, int iters) {
    if (p.Count < 5) return; bool closed = Math.Abs(p[0][0] - p[p.Count-1][0]) < 0.01 && Math.Abs(p[0][1] - p[p.Count-1][1]) < 0.01;
    for (int it = 0; it < iters; it++) { double[][] c = new double[p.Count][]; for (int i = 0; i < p.Count; i++) c[i] = (double[])p[i].Clone();
      for (int i = 1; i < p.Count - 1; i++) for (int k = 0; k < 3; k++) p[i][k] = 0.25 * c[i-1][k] + 0.5 * c[i][k] + 0.25 * c[i+1][k];
      if (closed) { for (int k = 0; k < 3; k++) { double v = 0.25 * c[p.Count-2][k] + 0.5 * c[0][k] + 0.25 * c[1][k]; p[0][k] = v; p[p.Count-1][k] = v; } } }
  }
  static List<double> WidthList(bool[] ink, double[] edt, bool[] skel, int w, int h, List<int> rows) {
    List<double> ws = new List<double>(); for (int i = 0; i < skel.Length; i++) if (skel[i]) { ws.Add(2 * edt[i] - 1); if (rows != null) rows.Add(i / w); } return ws;
  }
  public static StrokeData Prepare(byte[] shirt, int sw, int sh, int band, int inkLuma, int dilate, out string info) {
    bool[] ink = InkMask(shirt, sw, sh, band, inkLuma); double[] edt = Edt(ink, sw, sh); bool[] skel = Thin(ink, sw, sh);
    int cnt; var paths = Trace(skel, edt, sw, sh, out cnt); foreach (var p in paths) Smooth(p, 3);
    if (RingTopY > 0) { // drop the paths that lie entirely above the collar ring's top (the source shirt's upper neck band): the ring is the garment's neckline, what is above it is outline
      List<List<double[]>> kl2 = new List<List<double[]>>(); foreach (var p in paths) { bool above = true; foreach (var q in p) if (q[1] > RingTopY - 2 * q[2]) { above = false; break; } if (above) DroppedAbove++; else kl2.Add(p); }
      paths = kl2.ToArray(); cnt = paths.Length; }
    if (SourceBand > 0) { // drop source paths that sit in the source shirt's own outline band (neck band, shoulder edge): they are outline, not garment strokes
      int[] dOut2 = OuterDistS(shirt, sw, sh); List<double[]>[] kept = new List<double[]>[0]; List<List<double[]>> kl = new List<List<double[]>>();
      foreach (var p in paths) { int near = 0; foreach (var q in p) { int xi = (int)q[0], yi = (int)q[1]; if (xi >= 0 && yi >= 0 && xi < sw && yi < sh && dOut2[yi * sw + xi] <= SourceBand) near++; } if (near < 0.5 * p.Count) kl.Add(p); else DroppedSource++; }
      paths = kl.ToArray(); cnt = paths.Length; }
    if (Bridge && LastEnds != null) { List<List<double[]>> pl = new List<List<double[]>>(paths); HashSet<long> done = new HashSet<long>(); var ends = LastEnds;
      for (int i = 0; i < ends.Count; i++) { int bj = -1; double bd = 1e9; for (int j = 0; j < ends.Count; j++) { if (j == i) continue; double dx = ends[i][0] - ends[j][0], dy = ends[i][1] - ends[j][1], d = Math.Sqrt(dx*dx + dy*dy); if (d < bd) { bd = d; bj = j; } }
        if (bj < 0) continue; double lim = 4.0 * (ends[i][2] + ends[bj][2]) / 2.0; if (bd < 1.5 || bd > lim) continue; long key = (long)Math.Min(i, bj) * 100000 + Math.Max(i, bj); if (!done.Add(key)) continue;
        pl.Add(new List<double[]> { ends[i], ends[bj] }); }
      paths = pl.ToArray(); cnt = paths.Length; }
    List<double> ws = WidthList(ink, edt, skel, sw, sh, null); ws.Sort(); double med = ws.Count > 0 ? ws[ws.Count / 2] : 5;
    StrokeData sd = new StrokeData(); sd.Paths = paths; sd.MedianWidth = med; sd.Count = cnt;
    // fill only: dilate the ink, then paint it over with the colours around it
    bool[] big = (bool[])ink.Clone(); for (int it = 0; it < dilate; it++) { bool[] nx = (bool[])big.Clone(); for (int i = 0; i < big.Length; i++) if (big[i]) { int x = i % sw, y = i / sw; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=sw||yy>=sh) continue; nx[yy*sw+xx] = true; } } big = nx; }
    bool[] known = new bool[sw * sh]; for (int i = 0; i < known.Length; i++) known[i] = !big[i];
    for (int pass = 0; pass < 26; pass++) { List<int> add = new List<int>(); List<byte[]> cols = new List<byte[]>();
      for (int i = 0; i < known.Length; i++) if (!known[i]) { int x = i % sw, y = i / sw; double r = 0, g = 0, b = 0; int c = 0;
        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=sw||yy>=sh) continue; int j = yy*sw+xx; if (known[j] && shirt[j*4+3] > 40) { r += shirt[j*4+2]; g += shirt[j*4+1]; b += shirt[j*4]; c++; } }
        if (c > 0) { add.Add(i); cols.Add(new byte[] { (byte)(b / c), (byte)(g / c), (byte)(r / c) }); } }
      if (add.Count == 0) break; for (int k = 0; k < add.Count; k++) { int i = add[k]; shirt[i*4] = cols[k][0]; shirt[i*4+1] = cols[k][1]; shirt[i*4+2] = cols[k][2]; known[i] = true; } }
    info = "ink " + ink.Length + " px mask, " + cnt + " paths, source median width " + med.ToString("0.0") + " px, ink dilated " + dilate + " px before the fill";
    return sd;
  }
  public static byte[] Draw(StrokeData sd, Func<double, double, double[]> map, int tw, int th, double targetWidth, int ss) {
    double k = targetWidth > 0 ? targetWidth / sd.MedianWidth : 1.0; byte[] res = new byte[tw * th];
    using (Bitmap bmp = new Bitmap(tw * ss, th * ss, PixelFormat.Format32bppArgb)) {
      using (Graphics g = Graphics.FromImage(bmp)) { g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias; g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.Half;
        using (Pen pen = new Pen(Color.Black, 1f)) { pen.StartCap = System.Drawing.Drawing2D.LineCap.Round; pen.EndCap = System.Drawing.Drawing2D.LineCap.Round; pen.LineJoin = System.Drawing.Drawing2D.LineJoin.Round;
          foreach (var p in sd.Paths) { double[][] m = new double[p.Count][]; int inside = 0; for (int i = 0; i < p.Count; i++) { double[] t = map(p[i][0], p[i][1]); if (Inside != null && Inside(t[0], t[1])) inside++; m[i] = new double[] { t[0] * ss, t[1] * ss, (p[i][2] * k * (1.0 + RadiusBias / 3.5)) * ss }; }
            if (Inside != null && inside < 0.8 * p.Count) { Dropped++; continue; } // stray-strokes rule: a path whose mapped points leave the garment interior is not drawn
            if (m.Length == 1) { double r = m[0][2]; g.FillEllipse(Brushes.Black, (float)(m[0][0] - r), (float)(m[0][1] - r), (float)(2 * r), (float)(2 * r)); continue; }
            for (int i = 1; i < m.Length; i++) { pen.Width = (float)(m[i-1][2] + m[i][2]); g.DrawLine(pen, (float)m[i-1][0], (float)m[i-1][1], (float)m[i][0], (float)m[i][1]); } } } }
      BitmapData d = bmp.LockBits(new Rectangle(0, 0, bmp.Width, bmp.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] big = new byte[bmp.Width * bmp.Height * 4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, big, 0, big.Length); bmp.UnlockBits(d);
      for (int y = 0; y < th; y++) for (int x = 0; x < tw; x++) { double s = 0; for (int dy = 0; dy < ss; dy++) for (int dx = 0; dx < ss; dx++) s += big[((y * ss + dy) * bmp.Width + x * ss + dx) * 4 + 3]; res[y * tw + x] = (byte)(s / (ss * ss)); } }
    return res;
  }
  static double Pct(List<double> s, double q) { return s[(int)(q * (s.Count - 1))]; }
  static string Summ(List<double> w) { if (w.Count == 0) return "none"; w.Sort(); double m = 0; foreach (double v in w) m += v; m /= w.Count; double sd = 0; foreach (double v in w) sd += (v - m) * (v - m); sd = Math.Sqrt(sd / w.Count);
    return "n " + w.Count + ", median " + Pct(w, 0.5).ToString("0.0") + ", IQR " + Pct(w, 0.25).ToString("0.0") + "-" + Pct(w, 0.75).ToString("0.0") + ", max " + w[w.Count - 1].ToString("0.0") + ", CV " + (sd / m).ToString("0.00"); }
  static void Comps(bool[] ink, int w, int h, out int comps, out int holes) {
    int n = w * h; bool[] seen = new bool[n]; comps = 0; holes = 0; Queue<int> q = new Queue<int>();
    for (int s = 0; s < n; s++) { if (!ink[s] || seen[s]) continue; int size = 0; seen[s] = true; q.Enqueue(s); while (q.Count > 0) { int i = q.Dequeue(); size++; int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (ink[j] && !seen[j]) { seen[j] = true; q.Enqueue(j); } } } if (size >= 10) comps++; }
    bool[] bs = new bool[n]; int[] d4x = { 1, -1, 0, 0 }, d4y = { 0, 0, 1, -1 };
    // background components (4-connected) that do not reach the picture border and hold at least 6 px are holes of the ink
    for (int s = 0; s < n; s++) { if (ink[s] || bs[s]) continue; int size = 0; bool border = false; bs[s] = true; q.Enqueue(s); while (q.Count > 0) { int i = q.Dequeue(); size++; int x = i % w, y = i / w; if (x == 0 || y == 0 || x == w - 1 || y == h - 1) border = true; for (int k = 0; k < 4; k++) { int xx = x + d4x[k], yy = y + d4y[k]; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (!ink[j] && !bs[j]) { bs[j] = true; q.Enqueue(j); } } } if (!border && size >= 6) holes++; }
  }
  // Width of the strokes (2 x Euclidean DT - 1 on the thinned skeleton), per region of the body, with the ink topology.
  public static string Widths(byte[] a, int w, int h, int band, int inkLuma, string name) {
    bool[] ink = InkMask(a, w, h, band, inkLuma); double[] edt = Edt(ink, w, h); bool[] skel = Thin(ink, w, h);
    int top = h, bot = 0; for (int i = 0; i < w * h; i++) if (a[i*4+3] > 40) { int y = i / w; if (y < top) top = y; if (y > bot) bot = y; }
    List<double> all = new List<double>(), r1 = new List<double>(), r2 = new List<double>(), r3 = new List<double>(); int inkN = 0;
    for (int i = 0; i < ink.Length; i++) { if (ink[i]) inkN++; if (!skel[i]) continue; double wd = 2 * edt[i] - 1; all.Add(wd); double f = (double)(i / w - top) / Math.Max(1, bot - top); if (f < 0.35) r1.Add(wd); else if (f < 0.75) r2.Add(wd); else r3.Add(wd); }
    int comps, holes; Comps(ink, w, h, out comps, out holes); List<double> c = new List<double>(all); c.Sort(); LastMedian = c.Count > 0 ? Pct(c, 0.5) : 0;
    return name + ": ink " + inkN + " px, components " + comps + ", loops " + holes + "\n      all strokes: " + Summ(all) + "\n      top 35% of the body (collar, shoulders): " + Summ(r1) + "\n      middle: " + Summ(r2) + "\n      bottom 25% (hem): " + Summ(r3);
  }
  public static string IoU(byte[] a, byte[] b, int w, int h, int band, int inkLuma) {
    bool[] ia = InkMask(a, w, h, band, inkLuma), ib = InkMask(b, w, h, band, inkLuma); int both = 0, onlyA = 0, onlyB = 0;
    for (int i = 0; i < ia.Length; i++) { if (ia[i] && ib[i]) both++; else if (ia[i]) onlyA++; else if (ib[i]) onlyB++; }
    return "ink IoU " + (100.0 * both / Math.Max(1, both + onlyA + onlyB)).ToString("0.0") + "% (both " + both + ", output only " + onlyA + ", input only " + onlyB + ")";
  }
  public static void Offsets(byte[] body, byte[] shirt, int w, int h, out int[] L, out int[] R, out int top, out int bot, out int outlineW) {
    L = new int[h]; R = new int[h]; int[] bl = new int[h], br = new int[h], sl = new int[h], sr = new int[h]; int bt = -1, bb = -1, st = -1, sb = -1;
    for (int y = 0; y < h; y++) { bl[y] = -1; br[y] = -1; sl[y] = -1; sr[y] = -1; for (int x = 0; x < w; x++) { if (body[(y*w+x)*4+3] > 40) { if (bl[y] < 0) bl[y] = x; br[y] = x; } if (shirt[(y*w+x)*4+3] > 40) { if (sl[y] < 0) sl[y] = x; sr[y] = x; } }
      if (bl[y] >= 0) { if (bt < 0) bt = y; bb = y; } if (sl[y] >= 0) { if (st < 0) st = y; sb = y; } }
    int[] rl = new int[h], rr = new int[h]; for (int y = 0; y < h; y++) if (bl[y] >= 0 && sl[y] >= 0) { rl[y] = Math.Max(0, bl[y] - sl[y]); rr[y] = Math.Max(0, sr[y] - br[y]); }
    for (int y = 0; y < h; y++) { double a = 0, b = 0; int c = 0; for (int k = -6; k <= 6; k++) { int yy = y + k; if (yy < 0 || yy >= h) continue; a += rl[yy]; b += rr[yy]; c++; } L[y] = (int)Math.Round(a / c); R[y] = (int)Math.Round(b / c); }
    top = Math.Max(0, bt - st); bot = Math.Max(0, sb - bb);
    List<int> runs = new List<int>(); for (int y = bt + 30; y < bb - 30; y += 10) { if (sl[y] < 0) continue; int n = 0; for (int x = sl[y]; x < w; x++) { int i = y * w + x; if (shirt[i*4+3] > 40 && (shirt[i*4] + shirt[i*4+1] + shirt[i*4+2]) / 3 < 60) n++; else break; } runs.Add(n); }
    runs.Sort(); outlineW = runs.Count > 0 ? runs[runs.Count / 2] : 14;
  }
  public static string RingBox(byte[] a, int w, int h, int band, int inkLuma, int rowMax) {
    bool[] ink = InkMask(a, w, h, band, inkLuma); int n = w * h; bool[] seen = new bool[n]; int bestN = 0; int bx0 = 0, by0 = 0, bx1 = 0, by1 = 0; Queue<int> q = new Queue<int>();
    for (int s = 0; s < n; s++) { if (!ink[s] || seen[s] || s / w > rowMax) continue; int cnt = 0, x0 = w, y0 = h, x1 = 0, y1 = 0; seen[s] = true; q.Enqueue(s);
      while (q.Count > 0) { int i = q.Dequeue(); cnt++; int x = i % w, y = i / w; if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y;
        for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (ink[j] && !seen[j]) { seen[j] = true; q.Enqueue(j); } } }
      if (cnt > bestN) { bestN = cnt; bx0 = x0; by0 = y0; bx1 = x1; by1 = y1; } }
    return "ring piece " + bestN + " px, bbox (" + bx0 + "," + by0 + ")-(" + bx1 + "," + by1 + "), " + (bx1 - bx0 + 1) + " x " + (by1 - by0 + 1);
  }
  public static string ChamferBox(byte[] a, byte[] b, int w, int h, int band, int inkLuma, int x0, int y0, int x1, int y1) {
    bool[] ia = InkMask(a, w, h, band, inkLuma), ib = InkMask(b, w, h, band, inkLuma); bool[] sa = Thin(ia, w, h), sb2 = Thin(ib, w, h);
    for (int i = 0; i < sa.Length; i++) { int x = i % w, y = i / w; if (x < x0 || x > x1 || y < y0 || y > y1) { sa[i] = false; sb2[i] = false; } }
    Func<bool[], bool[], string> one = (from, to) => { bool[] fg = new bool[w * h]; for (int i = 0; i < fg.Length; i++) fg[i] = !to[i]; double[] e = Edt(fg, w, h); List<double> d = new List<double>(); for (int i = 0; i < from.Length; i++) if (from[i]) d.Add(e[i]); if (d.Count == 0) return "no skeleton"; d.Sort(); double m = 0; foreach (double v in d) m += v; return d.Count + " pts, mean " + (m / d.Count).ToString("0.0") + " px, 95th " + Pct(d, 0.95).ToString("0.0") + ", max " + d[d.Count - 1].ToString("0.0"); };
    return "skeleton in the box ours->WDI: " + one(sa, sb2) + " | WDI->ours: " + one(sb2, sa);
  }
  public static string Chamfer(byte[] a, byte[] b, int w, int h, int band, int inkLuma) {
    bool[] ia = InkMask(a, w, h, band, inkLuma), ib = InkMask(b, w, h, band, inkLuma); bool[] sa = Thin(ia, w, h), sb2 = Thin(ib, w, h);
    Func<bool[], bool[], string> one = (from, to) => { bool[] fg = new bool[w * h]; for (int i = 0; i < fg.Length; i++) fg[i] = !to[i]; double[] e = Edt(fg, w, h); List<double> d = new List<double>(); for (int i = 0; i < from.Length; i++) if (from[i]) d.Add(e[i]); if (d.Count == 0) return "no skeleton"; d.Sort(); double m = 0; foreach (double v in d) m += v; return d.Count + " pts, mean " + (m / d.Count).ToString("0.0") + " px, 95th " + Pct(d, 0.95).ToString("0.0") + ", max " + d[d.Count - 1].ToString("0.0"); };
    return "skeleton ours->WDI: " + one(sa, sb2) + " | WDI->ours: " + one(sb2, sa);
  }
  // Known-width lines drawn with the two draw routines and measured with the estimator.
  public static string Calib() {
    StringBuilder sb = new StringBuilder(); int w = 240, h = 240;
    foreach (int ss in new int[] { 1, 4 }) foreach (double ang in new double[] { 0, 30, 45, 90 }) {
      bool[] ink = new bool[w * h];
      using (Bitmap bmp = new Bitmap(w * ss, h * ss, PixelFormat.Format32bppArgb)) {
        using (Graphics g = Graphics.FromImage(bmp)) { g.Clear(Color.White); g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias; g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.Half;
          double rad = ang * Math.PI / 180, cx = 120, cy = 120, len = 90; using (Pen pen = new Pen(Color.Black, 5f * ss)) { pen.StartCap = System.Drawing.Drawing2D.LineCap.Round; pen.EndCap = System.Drawing.Drawing2D.LineCap.Round; g.DrawLine(pen, (float)((cx - len * Math.Cos(rad)) * ss), (float)((cy - len * Math.Sin(rad)) * ss), (float)((cx + len * Math.Cos(rad)) * ss), (float)((cy + len * Math.Sin(rad)) * ss)); } }
        BitmapData d = bmp.LockBits(new Rectangle(0, 0, bmp.Width, bmp.Height), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] big = new byte[bmp.Width * bmp.Height * 4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, big, 0, big.Length); bmp.UnlockBits(d);
        for (int y = 0; y < h; y++) for (int x = 0; x < w; x++) { double s = 0; for (int dy = 0; dy < ss; dy++) for (int dx = 0; dx < ss; dx++) s += big[((y * ss + dy) * bmp.Width + x * ss + dx) * 4]; double lum = s / (ss * ss); ink[y * w + x] = ss == 1 ? lum < 128 : lum < 140; } }
      double[] edt = Edt(ink, w, h); bool[] skel = Thin(ink, w, h); List<double> ws = new List<double>(); for (int i = 0; i < skel.Length; i++) if (skel[i]) { int x = i % w, y = i / w; if (x > 30 && x < 210 && y > 30 && y < 210) ws.Add(2 * edt[i] - 1); }
      ws.Sort(); sb.AppendLine("  width 5 line at " + ang + " deg, " + (ss == 1 ? "drawn 1x, threshold 128" : "drawn 4x, downsampled, threshold 0.45") + ": estimated " + (ws.Count > 0 ? Pct(ws, 0.5).ToString("0.0") + " (IQR " + Pct(ws, 0.25).ToString("0.0") + "-" + Pct(ws, 0.75).ToString("0.0") + ")" : "no skeleton"));
    }
    return sb.ToString();
  }
}
public static class Lm {
  public static bool WeakWaist, WeakHip, WeakArm;
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  // Silhouette landmarks only. Order of the result (x,y pairs): neckL, neckR, shoulderL, shoulderR, armpitL, armpitR, waistL, waistR, hipL, hipR, crotch, topMid, bottomMid.
  public static double[] Detect(string path, out string info) {
    int w, h; byte[] a = Ld(path, out w, out h); int[] l = new int[h], r = new int[h]; int top = -1, bot = -1;
    for (int y = 0; y < h; y++) { l[y] = -1; r[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (l[y] < 0) l[y] = x; r[y] = x; } if (l[y] >= 0) { if (top < 0) top = y; bot = y; } }
    int[] wd = new int[h]; for (int y = 0; y < h; y++) wd[y] = l[y] >= 0 ? r[y] - l[y] + 1 : 0;
    int H = bot - top; Func<double, int> row = f => top + (int)Math.Round(f * H);
    // shoulders: widest row in the top 30 %
    int sh = top; for (int y = top; y < row(0.30); y++) if (wd[y] > wd[sh]) sh = y;
    // neck junction: first row from the top where the width reaches 55 % of the shoulder width
    int neck = top; for (int y = top; y <= sh; y++) if (wd[y] >= 0.55 * wd[sh]) { neck = y; break; }
    // crotch: from the bottom row going up the middle columns; a transparent gap at the bottom ends at the crotch, no gap = the bottom row
    int mid = (l[bot] + r[bot]) / 2; int crotch = bot; bool gap = true; for (int dx = -2; dx <= 2; dx++) if (a[(bot*w+mid+dx)*4+3] > 40) gap = false;
    if (gap) { int yy = bot; while (yy > top) { bool open = true; for (int dx = -2; dx <= 2; dx++) if (a[(yy*w+mid+dx)*4+3] > 40) open = false; if (!open) break; yy--; } crotch = yy; }
    // waist: narrowest row between 35 % and 62 % of the height, but above the crotch
    int wl = row(0.35), wh = Math.Min(row(0.62), crotch - 8); int waist = wl; for (int y = wl; y <= wh; y++) if (wd[y] < wd[waist]) waist = y;
    // hips: widest row between the waist and the crotch minus 4 % of the height (lower bound keeps the waist row from winning on bodies that do not narrow)
    int hl = waist + (int)(0.04 * H), hh = Math.Min(crotch - (int)(0.03 * H), waist + (int)(0.20 * H)); if (hh < hl) hh = hl; int hip = hl; for (int y = hl; y <= hh; y++) if (wd[y] >= wd[hip]) hip = y;
    // armpit: local minimum of the width below the shoulders, else a share of the way from the shoulders to the waist
    int arm = -1; for (int y = sh + 6; y < waist - 10; y++) if (wd[y] <= wd[y-1] && wd[y] <= wd[y+1] && wd[y] < 0.96 * wd[sh]) { arm = y; break; }
    string how = "min"; if (arm < 0) { arm = sh + (int)(0.40 * (waist - sh)); how = "share"; }
    WeakWaist = waist <= wl + 1 || waist >= wh - 1; WeakHip = hip <= hl + 1 || hip >= hh - 1; WeakArm = how == "share";
    info = "top " + top + " bottom " + bot + " neck " + neck + " shoulders " + sh + " armpits " + arm + "(" + how + ") waist " + waist + " hips " + hip + " crotch " + crotch + (gap ? "(notch)" : "(bottom)") + (WeakWaist ? " weakWaist" : "") + (WeakHip ? " weakHip" : "");
    return new double[] { l[neck], neck, r[neck] + 1, neck, l[sh], sh, r[sh] + 1, sh, l[arm], arm, r[arm] + 1, arm, l[waist], waist, r[waist] + 1, waist, l[hip], hip, r[hip] + 1, hip, mid + 0.5, crotch, (l[top] + r[top] + 1) / 2.0, top, mid + 0.5, bot };
  }
  public static int[] Ext(string path, int y) { int w, h; byte[] a = Ld(path, out w, out h); int l = -1, r = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (l < 0) l = x; r = x; } return new int[] { l, r + 1 }; }
}
public static class Cm {
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  class Pic { public byte[] a; public int w, h; public Pic(string p) { a = Ld(p, out w, out h); } public bool On(int x, int y) { return x >= 0 && y >= 0 && x < w && y < h && a[(y*w+x)*4+3] > 40; } }
  static double Ray(Pic p, double cx, double cy, double ang) { double best = 0; double dx = Math.Cos(ang), dy = Math.Sin(ang); for (double t = 0; t < 500; t += 0.5) if (p.On((int)(cx + dx * t), (int)(cy + dy * t))) best = t; return best; }
  public class Facts { public double Top, Bot, Area, ShoulderW, NeckW, NeckD, HemFrac, GarTop, AreaRatio; public double[] Off = new double[16], RB = new double[16]; }
  public static Facts Measure(string bodyP, string garP) {
    Pic b = new Pic(bodyP), g = new Pic(garP); Facts f = new Facts(); int top = -1, bot = -1; double sx = 0, sy = 0, n = 0;
    for (int y = 0; y < b.h; y++) for (int x = 0; x < b.w; x++) if (b.On(x, y)) { if (top < 0) top = y; bot = y; sx += x; sy += y; n++; }
    double cx = sx / n, cy = sy / n; f.Top = top; f.Bot = bot; double sw = 0; for (int y = top; y < top + 0.30 * (bot - top); y++) { int l = -1, r = -1; for (int x = 0; x < b.w; x++) if (b.On(x, y)) { if (l < 0) l = x; r = x; } if (l >= 0 && r - l + 1 > sw) sw = r - l + 1; } f.ShoulderW = sw;
    for (int k = 0; k < 16; k++) { double ang = 2 * Math.PI * k / 16; f.RB[k] = Ray(b, cx, cy, ang); f.Off[k] = Ray(g, cx, cy, ang) - f.RB[k]; }
    int gTop = -1, gBot = -1; double ga = 0; for (int y = 0; y < g.h; y++) for (int x = 0; x < g.w; x++) if (g.On(x, y)) { if (gTop < 0) gTop = y; gBot = y; ga++; }
    f.GarTop = gTop; f.Area = ga; f.AreaRatio = ga / n; f.HemFrac = (gBot - top) / (double)(bot - top);
    // neckline in the alpha: at the middle column the first garment row below the garment's top is the collar bottom; the opening width is the widest transparent gap between opaque pixels on the rows above it
    int mid = (int)Math.Round(cx); int cb = -1; for (int y = gTop; y < g.h; y++) if (g.On(mid, y)) { cb = y; break; }
    double nw = 0; for (int y = gTop; y < cb; y++) { int l = -1, r = -1; for (int x = 0; x < g.w; x++) if (g.On(x, y)) { if (l < 0) l = x; r = x; } if (l < 0) continue; int gap = 0, best = 0; for (int x = l; x <= r; x++) { if (!g.On(x, y)) { gap++; if (gap > best) best = gap; } else gap = 0; } if (best > nw) nw = best; }
    f.NeckW = nw; f.NeckD = cb < 0 ? 0 : cb - gTop; return f;
  }
  public static string Compare(string srcBody, string srcGar, string tgtBody, string tgtGar, out bool c1, out bool c2, out bool c3, out bool c5) {
    Facts s = Measure(srcBody, srcGar), t = Measure(tgtBody, tgtGar); StringBuilder sb = new StringBuilder();
    double worst = 0; int wk = 0; for (int k = 0; k < 16; k++) { double sc = s.RB[k] > 0 ? t.RB[k] / s.RB[k] : 1; double exp = s.Off[k] * sc; double d = Math.Abs(t.Off[k] - exp); if (d > worst) { worst = d; wk = k; } }
    c1 = worst <= 2.0; sb.AppendLine("    C1 outline offset vs source offset x local scale, 16 rays: worst " + worst.ToString("0.0") + " px at ray " + wk + " (limit 2) " + (c1 ? "PASS" : "FAIL") + "; source offsets min " + Min(s.Off).ToString("0.0") + " max " + Max(s.Off).ToString("0.0") + ", result min " + Min(t.Off).ToString("0.0") + " max " + Max(t.Off).ToString("0.0"));
    double sL = s.Bot - s.Top, tL = t.Bot - t.Top; double sNw = s.NeckW / s.ShoulderW, tNw = t.NeckW / t.ShoulderW, sNd = s.NeckD / sL, tNd = t.NeckD / tL;
    bool haveNeck = s.NeckW > 3; double dw = haveNeck ? Math.Abs(tNw - sNw) / sNw : 0, dd = s.NeckD > 3 ? Math.Abs(tNd - sNd) / sNd : 0; c2 = !haveNeck || (dw <= 0.05 && dd <= 0.05);
    sb.AppendLine("    C2 neckline in the alpha: width/shoulders source " + sNw.ToString("0.000") + " result " + tNw.ToString("0.000") + " (" + (100 * dw).ToString("0.0") + " %), depth/torso source " + sNd.ToString("0.000") + " result " + tNd.ToString("0.000") + " (" + (100 * dd).ToString("0.0") + " %), limit 5 % " + (haveNeck ? (c2 ? "PASS" : "FAIL") : "n/a (no opening in the alpha)"));
    double dh = Math.Abs(t.HemFrac - s.HemFrac); c3 = dh <= 0.03; sb.AppendLine("    C3 hem at fraction of torso length: source " + s.HemFrac.ToString("0.000") + " result " + t.HemFrac.ToString("0.000") + " (diff " + (100 * dh).ToString("0.0") + " points, limit 3) " + (c3 ? "PASS" : "FAIL"));
    double da = Math.Abs(t.AreaRatio - s.AreaRatio) / s.AreaRatio; c5 = da <= 0.05; sb.AppendLine("    C5 garment area / body area: source " + s.AreaRatio.ToString("0.000") + " result " + t.AreaRatio.ToString("0.000") + " (" + (100 * da).ToString("0.0") + " %, limit 5) " + (c5 ? "PASS" : "FAIL"));
    return sb.ToString();
  }
  static double Min(double[] a) { double m = 1e9; foreach (double v in a) if (v < m) m = v; return m; }
  static double Max(double[] a) { double m = -1e9; foreach (double v in a) if (v > m) m = v; return m; }
}
public static class W4 {
  static int[] Outer(byte[] a, int w, int h) {
    int[] d = new int[w * h]; for (int i = 0; i < d.Length; i++) d[i] = -1; Queue<int> q = new Queue<int>();
    for (int x = 0; x < w; x++) { St(a, w, d, q, x, 0); St(a, w, d, q, x, h - 1); } for (int y = 0; y < h; y++) { St(a, w, d, q, 0, y); St(a, w, d, q, w - 1, y); }
    while (q.Count > 0) { int i = q.Dequeue(); int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (d[j] == -1 && a[j*4+3] <= 40) { d[j] = 0; q.Enqueue(j); } } }
    Queue<int> q2 = new Queue<int>(); for (int i = 0; i < d.Length; i++) if (d[i] == 0) q2.Enqueue(i);
    while (q2.Count > 0) { int i = q2.Dequeue(); int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; int j = yy*w+xx; if (d[j] == -1 && a[j*4+3] > 40) { d[j] = d[i] + 1; q2.Enqueue(j); } } }
    for (int i = 0; i < d.Length; i++) if (d[i] < 0) d[i] = 100000; return d; }
  static void St(byte[] a, int w, int[] d, Queue<int> q, int x, int y) { int i = y * w + x; if (d[i] == -1 && a[i*4+3] <= 40) { d[i] = 0; q.Enqueue(i); } }
  static double Lu(byte[] a, int x, int y, int w, int h) { if (x < 0) x = 0; if (y < 0) y = 0; if (x >= w) x = w - 1; if (y >= h) y = h - 1; int i = (y * w + x) * 4; double al = a[i+3] / 255.0; return al * (a[i] + a[i+1] + a[i+2]) / 3.0 + (1 - al) * 255.0; }
  // Stroke width at 4x: ink = interior pixels darker than 60 (1x), then at 4x the bilinear luminance below 140 inside the ink dilated by 3 px; width = (2 x Euclidean distance - 1) / 4 on the skeleton.
  public static string Measure(byte[] a, int w, int h, int band, string name) {
    int[] dOut = Outer(a, w, h); bool[] ink1 = new bool[w * h]; for (int i = 0; i < ink1.Length; i++) ink1[i] = a[i*4+3] > 40 && (a[i*4] + a[i*4+1] + a[i*4+2]) / 3.0 < 60 && dOut[i] > band;
    bool[] dil = (bool[])ink1.Clone(); for (int it = 0; it < 3; it++) { bool[] nx = (bool[])dil.Clone(); for (int i = 0; i < dil.Length; i++) if (dil[i]) { int x = i % w, y = i / w; for (int dy = -1; dy <= 1; dy++) for (int dx = -1; dx <= 1; dx++) { int xx = x+dx, yy = y+dy; if (xx<0||yy<0||xx>=w||yy>=h) continue; nx[yy*w+xx] = true; } } dil = nx; }
    int W = w * 4, H = h * 4; bool[] ink = new bool[W * H]; int n4 = 0;
    for (int Y = 0; Y < H; Y++) for (int X = 0; X < W; X++) { if (!dil[(Y/4)*w + X/4]) continue; double fx = (X + 0.5) / 4.0 - 0.5, fy = (Y + 0.5) / 4.0 - 0.5; int x0 = (int)Math.Floor(fx), y0 = (int)Math.Floor(fy); double tx = fx - x0, ty = fy - y0;
      double v = Lu(a,x0,y0,w,h)*(1-tx)*(1-ty) + Lu(a,x0+1,y0,w,h)*tx*(1-ty) + Lu(a,x0,y0+1,w,h)*(1-tx)*ty + Lu(a,x0+1,y0+1,w,h)*tx*ty; if (v < 140) { ink[Y*W+X] = true; n4++; } }
    if (n4 == 0) return name + ": no ink";
    double[] edt = S3.Edt(ink, W, H); bool[] sk = S3.Thin(ink, W, H); List<double> ws = new List<double>(); for (int i = 0; i < ink.Length; i++) if (sk[i]) ws.Add((2 * edt[i] - 1) / 4.0);
    ws.Sort(); if (ws.Count == 0) return name + ": no skeleton"; Med = ws[ws.Count / 2]; Q1 = ws[(int)(0.25 * (ws.Count - 1))]; Q3 = ws[(int)(0.75 * (ws.Count - 1))]; Area = n4 / 16.0;
    return name + ": width4 median " + Med.ToString("0.00") + " IQR " + Q1.ToString("0.00") + "-" + Q3.ToString("0.00") + ", ink area " + Area.ToString("0") + " px";
  }
  public static double Med, Q1, Q3, Area;
}
public static class Gl {
  public static string Names = "", NeckKind = ""; public static double AsymLimit = 0.70; public static string Facing = "south"; public static string LastBlack = "";
  // Garment's own feature points (x,y): hem corners, sleeve ends, collar ring (8 points of the ring skeleton).
  // a neckline ring piece: at least 40 px, both sides of its box at least 10 px (a 5 px tall piece is the garment outline, not a collar), aspect between 1/8 and 8, and not a filled blob (pixels under 45 % of its box)
  public static int TopLim = 100000; static bool TopOk(string info) { var m = System.Text.RegularExpressions.Regex.Match(info, "bbox [(][0-9]+,([0-9]+)[)]"); return m.Success && int.Parse(m.Groups[1].Value) <= TopLim; }
  static bool RingOk(string info) { var m = System.Text.RegularExpressions.Regex.Match(info, "piece ([0-9]+) px, bbox [(]([0-9]+),([0-9]+)[)]-[(]([0-9]+),([0-9]+)[)]"); if (!m.Success) return false;
    int n = int.Parse(m.Groups[1].Value), bw = int.Parse(m.Groups[4].Value) - int.Parse(m.Groups[2].Value) + 1, bh = int.Parse(m.Groups[5].Value) - int.Parse(m.Groups[3].Value) + 1;
    return n >= 40 && bw >= 10 && bh >= 10 && bw <= 8 * bh && bh <= 8 * bw && n < 0.45 * bw * bh; }
  public static double[] Features(byte[] a, int w, int h, int band) {
    List<double> pts = new List<double>(); List<string> nm = new List<string>();
    int[] l = new int[h], r = new int[h], wd = new int[h]; int top = -1, bot = -1;
    for (int y = 0; y < h; y++) { l[y] = -1; r[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (l[y] < 0) l[y] = x; r[y] = x; } if (l[y] >= 0) { wd[y] = r[y] - l[y] + 1; if (top < 0) top = y; bot = y; } }
    int H = bot - top; int hy = bot - 3; pts.Add(l[hy]); pts.Add(hy); nm.Add("hemL"); pts.Add(r[hy] + 1); pts.Add(hy); nm.Add("hemR");
    int maxW = 0; for (int y = top; y <= top + (int)(0.55 * H); y++) if (wd[y] > maxW) maxW = wd[y];
    int sr = top; for (int y = top; y <= top + (int)(0.55 * H); y++) if (wd[y] >= 0.97 * maxW) sr = y;
    pts.Add(l[sr]); pts.Add(sr); nm.Add("sleeveL"); pts.Add(r[sr] + 1); pts.Add(sr); nm.Add("sleeveR");
    int mid = (l[top + H / 3] + r[top + H / 3]) / 2; int gw = wd[top + H / 3];
    // top of the central band (mid +- 30 % of the width): shoulder spikes, horns and backpacks above it do not move the neckline search
    int cb0 = mid - (int)(0.30 * gw), cb1 = mid + (int)(0.30 * gw), ctop = top; for (int y = top; y <= bot; y++) { bool any = false; for (int x = Math.Max(0, cb0); x <= Math.Min(w - 1, cb1); x++) if (a[(y*w+x)*4+3] > 40) { any = true; break; } if (any) { ctop = y; break; } }
    // asymmetric garment (one shoulder or diagonal: TribalA, Cape, Sash, Bandolier): mirror overlap of the top 40 % under 70 % over the full width AND under 90 % on the central band
    // (measured on 50 garments: those four 23-63 % full / 40-87 % central; FlakVest, Overalls, TankTop, JacketSpikecore at least 80 / 78; spiky DusterSpikecore and backpack GrenadierArmor fall in between and go to place)
    Func<int, int, int, int, double> mir = (y0, y1, x0, x1) => { int bo = 0, ei = 0; for (int y = y0; y <= y1; y++) for (int x = Math.Max(0, x0); x <= Math.Min(w - 1, x1); x++) { int xm = 2 * mid - x; bool p = a[(y*w+x)*4+3] > 40, q = xm >= 0 && xm < w && a[(y*w+xm)*4+3] > 40; if (p || q) ei++; if (p && q) bo++; } return ei > 0 ? (double)bo / ei : 1.0; };
    double mFull = mir(top, top + (int)(0.40 * H), 0, w - 1), mCen = mir(ctop, ctop + (int)(0.40 * H), cb0, cb1);
    if (Facing != "east" && mFull < AsymLimit && mCen < 0.90) { NeckKind = "asymmetric, neckline to place (mirror " + (100 * mFull).ToString("0") + " / " + (100 * mCen).ToString("0") + " %)"; Names = string.Join(" ", nm.ToArray()); return pts.ToArray(); }
    // open front (jacket, coat, cape): the middle column is bare on more than half of the garment's rows while the garment exists on both sides; neckline = the inner edges of the opening, 4 rows x L/R in the top 40 %
    int bare = 0, rowsBoth = 0; for (int y = top; y <= bot; y++) { if (l[y] < 0 || l[y] >= mid || r[y] <= mid) continue; rowsBoth++; if (a[(y*w+mid)*4+3] <= 40) bare++; }
    if (Facing != "east" && rowsBoth > 0 && bare > 0.5 * rowsBoth) { for (int k = 0; k < 4; k++) { int y = ctop + (int)((k + 1) * 0.40 * H / 5); int xl = mid; while (xl > 0 && a[(y*w+xl)*4+3] <= 40) xl--; int xr = mid; while (xr < w - 1 && a[(y*w+xr)*4+3] <= 40) xr++;
        if (xr - xl < 12) continue; if (xl > 0) { pts.Add(xl + 1); pts.Add(y); nm.Add("neck" + (2*k)); } if (xr < w - 1) { pts.Add(xr); pts.Add(y); nm.Add("neck" + (2*k+1)); } }
      if (nm.FindAll(s => s.StartsWith("neck")).Count < 4) { NeckKind = "open front, neckline to place"; Names = string.Join(" ", nm.ToArray()); return pts.ToArray(); }
      NeckKind = "open front"; Names = string.Join(" ", nm.ToArray()); return pts.ToArray(); }
    string info = S3.RingBoxIn(a, w, h, band, 60, mid - (int)(0.30 * gw), ctop, mid + (int)(0.30 * gw), ctop + (int)(0.40 * H));
    // side and back: a ring or line counts as the collar only when its box starts in the top 12 % (lower dark pieces are plates, straps or pockets)
    TopLim = Facing == "south" ? 100000 : ctop + (int)(0.12 * H); LastBlack = info; int piece = RingOk(info) && TopOk(info) ? 1000 : 0;
    // neckline, three kinds: a black ring (ink under 60), a grey line (40 levels darker than the 15 px local mean), or an opening cut in the garment (dip of its top contour)
    int bx0 = mid - (int)(0.30 * gw), bx1 = mid + (int)(0.30 * gw), by1 = ctop + (int)(0.40 * H); string kind = "";
    if (piece < 40) { S3.RelativeInk = true; string gi = S3.RingBoxIn(a, w, h, band, 60, bx0, ctop, bx1, by1); piece = RingOk(gi) && TopOk(gi) ? 1000 : 0; if (piece >= 40) kind = "grey"; else S3.RelativeInk = false; } else kind = "black";
    if (piece >= 40) { double[] ring = S3.RingPointsBox(a, w, h, band, 60, bx0, ctop, bx1, by1, 16); S3.RelativeInk = false; for (int k = 0; k < 16; k += 2) { pts.Add(ring[2*k]); pts.Add(ring[2*k+1]); nm.Add("ring" + k); } }
    else { int[] tc = new int[w]; int mn = h, cl = -1, cr = -1; for (int x = bx0; x <= bx1; x++) { tc[x] = -1; for (int y = ctop; y <= ctop + (int)(0.7 * H); y++) if (a[(y*w+x)*4+3] > 40) { tc[x] = y; break; } if (tc[x] >= 0 && tc[x] < mn) mn = tc[x]; }
      int deep = mid; for (int x = bx0; x <= bx1; x++) if (tc[x] > tc[deep]) deep = x;
      // side and back: a dip whose deepest column sits near the band edge is the rounded top of the garment, not an opening
      if (tc[deep] - mn > 8 && (Facing == "south" || (deep > bx0 + (bx1 - bx0) / 5 && deep < bx1 - (bx1 - bx0) / 5))) { kind = "opening"; cl = deep; while (cl > bx0 && tc[cl - 1] > mn + 2) cl--; cr = deep; while (cr < bx1 && tc[cr + 1] > mn + 2) cr++;
        for (int k = 0; k < 8; k++) { int x = cl + (int)Math.Round((cr - cl) * k / 7.0); pts.Add(x); pts.Add(tc[x] < 0 ? mn : tc[x]); nm.Add("neck" + k); } } }
    // side and back views: no ring, line or opening found -> 8 points on the garment top contour across the central band (the collar seen from the side)
    if (Facing != "south" && kind == "") { kind = Facing + ": top edge"; for (int k = 0; k < 8; k++) { int x = cb0 + (int)Math.Round((cb1 - cb0) * (k + 0.5) / 8.0); int yy = ctop; while (yy < bot && a[(yy*w+x)*4+3] <= 40) yy++; if (yy < bot) { pts.Add(x); pts.Add(yy); nm.Add("neck" + k); } } }
    NeckKind = kind;
    Names = string.Join(" ", nm.ToArray()); return pts.ToArray();
  }
}
public static class C1m {
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  static void Ext(byte[] a, int w, int h, int[] L, int[] R, out int top, out int bot) { top = -1; bot = -1; for (int y = 0; y < h; y++) { L[y] = -1; R[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (L[y] < 0) L[y] = x; R[y] = x; } if (L[y] >= 0) { if (top < 0) top = y; bot = y; } } }
  // C1 along the contour: 16 rows between the garment's top and hem (3 % to 97 %), left and right edge: signed offset of the garment edge outward from the body edge on the same row
  // (the garment edge is the outermost garment pixel of the row, the body edge the outermost body pixel). Result rows correspond by the fraction of the torso length.
  public static string Run(string srcBody, string srcGar, string tgtBody, string tgtGar, out double worst) {
    int w, h; byte[] sb = Ld(srcBody, out w, out h), sg = Ld(srcGar, out w, out h), tb = Ld(tgtBody, out w, out h), tg = Ld(tgtGar, out w, out h);
    int[] sbL = new int[h], sbR = new int[h], sgL = new int[h], sgR = new int[h], tbL = new int[h], tbR = new int[h], tgL = new int[h], tgR = new int[h]; int sbT, sbB, sgT, sgB, tbT, tbB, tgT, tgB;
    Ext(sb, w, h, sbL, sbR, out sbT, out sbB); Ext(sg, w, h, sgL, sgR, out sgT, out sgB); Ext(tb, w, h, tbL, tbR, out tbT, out tbB); Ext(tg, w, h, tgL, tgR, out tgT, out tgB);
    worst = 0; string worstAt = ""; int n = 0; int fail = 0;
    for (int i = 0; i < 16; i++) { double u = 0.03 + 0.94 * i / 15.0; int ys = (int)Math.Round(sgT + u * (sgB - sgT)); double f = (ys - sbT) / (double)(sbB - sbT); int yt = (int)Math.Round(tbT + f * (tbB - tbT));
      if (ys < 0 || ys >= h || yt < 0 || yt >= h || sbL[ys] < 0 || tbL[yt] < 0 || sgL[ys] < 0 || tgL[yt] < 0) continue;
      double halfS = (sbR[ys] - sbL[ys]) / 2.0 + 0.5, halfT = (tbR[yt] - tbL[yt]) / 2.0 + 0.5; double scale = halfT / halfS;
      for (int side = 0; side < 2; side++) {
        double offS = side == 0 ? sbL[ys] - sgL[ys] : sgR[ys] - sbR[ys]; double offT = side == 0 ? tbL[yt] - tgL[yt] : tgR[yt] - tbR[yt];
        double d = Math.Abs(offT - offS * scale); n++; if (d > 2.0) fail++; if (d > worst) { worst = d; worstAt = "row " + ys + "->" + yt + (side == 0 ? " L" : " R") + " src " + offS.ToString("0") + " res " + offT.ToString("0") + " expected " + (offS * scale).ToString("0.0"); } } }
    return "C1 along contour, " + n + " samples: worst " + worst.ToString("0.0") + " px (" + worstAt + "), " + fail + " samples over 2 px";
  }
}
public static class C1n {
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  static void Ext(byte[] a, int w, int h, int[] L, int[] R, out int top, out int bot) { top = -1; bot = -1; for (int y = 0; y < h; y++) { L[y] = -1; R[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (L[y] < 0) L[y] = x; R[y] = x; } if (L[y] >= 0) { if (top < 0) top = y; bot = y; } } }
  // signed distance to the body edge: positive outside, negative inside
  static double[] Signed(byte[] a, int w, int h) { bool[] fg = new bool[w*h], bg = new bool[w*h]; for (int i = 0; i < fg.Length; i++) { fg[i] = a[i*4+3] > 40; bg[i] = !fg[i]; } double[] ins = S3.Edt(fg, w, h), outs = S3.Edt(bg, w, h); double[] s = new double[w*h]; for (int i = 0; i < s.Length; i++) s[i] = fg[i] ? -(ins[i] - 0.5) : (outs[i] - 0.5); return s; }
  public static string Run(string srcBody, string srcGar, string tgtBody, string tgtGar, string label, int rows) {
    int w, h; byte[] sb = Ld(srcBody, out w, out h), sg = Ld(srcGar, out w, out h), tb = Ld(tgtBody, out w, out h), tg = Ld(tgtGar, out w, out h);
    int[] sbL = new int[h], sbR = new int[h], sgL = new int[h], sgR = new int[h], tbL = new int[h], tbR = new int[h], tgL = new int[h], tgR = new int[h]; int sbT, sbB, sgT, sgB, tbT, tbB, tgT, tgB;
    Ext(sb, w, h, sbL, sbR, out sbT, out sbB); Ext(sg, w, h, sgL, sgR, out sgT, out sgB); Ext(tb, w, h, tbL, tbR, out tbT, out tbB); Ext(tg, w, h, tgL, tgR, out tgT, out tgB);
    double[] sS = Signed(sb, w, h), sT = Signed(tb, w, h);
    List<string> detail = new List<string>(); double[] worst = { 0, 0 }; int[] n = { 0, 0 }, over = { 0, 0 }; double[] sum = { 0, 0 };
    for (int i = 0; i < rows; i++) { double u = 0.03 + 0.94 * i / (rows - 1.0); int ys = (int)Math.Round(sgT + u * (sgB - sgT)); double f = (ys - sbT) / (double)(sbB - sbT); int yt = (int)Math.Round(tbT + f * (tbB - tbT));
      if (ys < 6 || ys >= h - 6 || yt < 0 || yt >= h || sbL[ys] < 0 || tbL[yt] < 0 || sgL[ys] < 0 || tgL[yt] < 0) continue;
      double halfS = (sbR[ys] - sbL[ys]) / 2.0 + 0.5, halfT = (tbR[yt] - tbL[yt]) / 2.0 + 0.5, scale = halfT / halfS;
      for (int side = 0; side < 2; side++) {
        int sx = side == 0 ? sgL[ys] : sgR[ys], tx = side == 0 ? tgL[yt] : tgR[yt]; double ds = sS[ys * w + sx], dt = sT[yt * w + tx]; double d = Math.Abs(dt - ds * scale);
        int e1 = side == 0 ? sbL[Math.Max(0, ys - 6)] - sbL[Math.Min(h - 1, ys + 6)] : sbR[Math.Max(0, ys - 6)] - sbR[Math.Min(h - 1, ys + 6)]; int g = Math.Abs(e1) > 3 ? 1 : 0; // slanted body edge: sleeve, shoulder, hip curve
        n[g]++; sum[g] += d; if (d > 2.0) over[g]++; if (d > worst[g]) worst[g] = d; detail.Add(d.ToString("000.0") + " row " + ys + "->" + yt + (side == 0 ? " L" : " R") + " " + (g == 1 ? "slanted" : "torso") + ": src d " + ds.ToString("0.0") + " res d " + dt.ToString("0.0") + " exp " + (ds * scale).ToString("0.0") + "; body half width " + halfS.ToString("0") + "->" + halfT.ToString("0") + " scale " + scale.ToString("0.00") + "; garment half width src " + ((sgR[ys] - sgL[ys]) / 2).ToString("0") + " res " + ((tgR[yt] - tgL[yt]) / 2).ToString("0")); } }
    detail.Sort(); detail.Reverse();
    string res = label + " normal-to-contour, " + (n[0] + n[1]) + " samples: torso rows " + n[0] + " (worst " + worst[0].ToString("0.0") + ", mean " + (n[0] > 0 ? sum[0] / n[0] : 0).ToString("0.0") + ", " + over[0] + " over 2 px), slanted rows " + n[1] + " (worst " + worst[1].ToString("0.0") + ", mean " + (n[1] > 0 ? sum[1] / n[1] : 0).ToString("0.0") + ", " + over[1] + " over 2 px)";
    for (int k = 0; k < 2 && k < detail.Count; k++) res += "\n      " + detail[k];
    return res;
  }
}
public static class C1s {
  public static double ShortWorst, OverWorst, HemDiff; public static bool Pass;
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  static void Ext(byte[] a, int w, int h, int[] L, int[] R, out int top, out int bot) { top = -1; bot = -1; for (int y = 0; y < h; y++) { L[y] = -1; R[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (L[y] < 0) L[y] = x; R[y] = x; } if (L[y] >= 0) { if (top < 0) top = y; bot = y; } } }
  static double[] Signed(byte[] a, int w, int h) { bool[] fg = new bool[w*h], bg = new bool[w*h]; for (int i = 0; i < fg.Length; i++) { fg[i] = a[i*4+3] > 40; bg[i] = !fg[i]; } double[] ins = S3.Edt(fg, w, h), outs = S3.Edt(bg, w, h); double[] s = new double[w*h]; for (int i = 0; i < s.Length; i++) s[i] = fg[i] ? -(ins[i] - 0.5) : (outs[i] - 0.5); return s; }
  // Signed C1 (Virginie 2026-11-03): diff = result offset - expected offset (normal distance of the garment edge outward from the body edge). diff < -2 = shortfall (skin showing), diff > 8 = overshoot too far. A result row with no garment where the source has one counts as full shortfall. Hem: result hem row minus expected hem row (negative = above).
  public static string Run(string srcBody, string srcGar, string tgtBody, string tgtGar, string label, int rows) {
    int w, h; byte[] sb = Ld(srcBody, out w, out h), sg = Ld(srcGar, out w, out h), tb = Ld(tgtBody, out w, out h), tg = Ld(tgtGar, out w, out h);
    int[] sbL = new int[h], sbR = new int[h], sgL = new int[h], sgR = new int[h], tbL = new int[h], tbR = new int[h], tgL = new int[h], tgR = new int[h]; int sbT, sbB, sgT, sgB, tbT, tbB, tgT, tgB;
    Ext(sb, w, h, sbL, sbR, out sbT, out sbB); Ext(sg, w, h, sgL, sgR, out sgT, out sgB); Ext(tb, w, h, tbL, tbR, out tbT, out tbB); Ext(tg, w, h, tgL, tgR, out tgT, out tgB);
    double[] sS = Signed(sb, w, h), sT = Signed(tb, w, h);
    double[] shortW = { 0, 0 }, overW = { 0, 0 }; int[] n = { 0, 0 }, sOver = { 0, 0 }, oOver = { 0, 0 };
    for (int i = 0; i < rows; i++) { double u = 0.03 + 0.94 * i / (rows - 1.0); int ys = (int)Math.Round(sgT + u * (sgB - sgT)); double f = (ys - sbT) / (double)(sbB - sbT); int yt = (int)Math.Round(tbT + f * (tbB - tbT));
      if (ys < 6 || ys >= h - 6 || yt < 0 || yt >= h || sbL[ys] < 0 || tbL[yt] < 0 || sgL[ys] < 0) continue;
      double halfS = (sbR[ys] - sbL[ys]) / 2.0 + 0.5, halfT = (tbR[yt] - tbL[yt]) / 2.0 + 0.5, scale = halfT / halfS;
      for (int side = 0; side < 2; side++) {
        int sx = side == 0 ? sgL[ys] : sgR[ys]; double ds = sS[ys * w + sx]; double dt;
        if (tgL[yt] < 0) dt = -halfT; else { int tx = side == 0 ? tgL[yt] : tgR[yt]; dt = sT[yt * w + tx]; }
        double diff = dt - ds * scale; int e1 = side == 0 ? sbL[ys - 6] - sbL[ys + 6] : sbR[ys - 6] - sbR[ys + 6]; int g = Math.Abs(e1) > 3 ? 1 : 0;
        n[g]++; if (-diff > shortW[g]) shortW[g] = -diff; if (diff > overW[g]) overW[g] = diff; if (diff < -2.0) sOver[g]++; if (diff > 8.0) oOver[g]++; } }
    double hemExp = tbT + (sgB - sbT) / (double)(sbB - sbT) * (tbB - tbT); HemDiff = tgB - hemExp;
    ShortWorst = Math.Max(Math.Max(shortW[0], shortW[1]), Math.Max(0, -HemDiff)); OverWorst = Math.Max(Math.Max(overW[0], overW[1]), Math.Max(0, HemDiff));
    Pass = ShortWorst <= 2.0 && OverWorst <= 8.0;
    return label + " signed C1, " + (n[0] + n[1]) + " samples: torso " + n[0] + " (shortfall worst " + shortW[0].ToString("0.0") + ", " + sOver[0] + " over 2; overshoot worst " + overW[0].ToString("0.0") + ", " + oOver[0] + " over 8), slanted " + n[1] + " (shortfall worst " + shortW[1].ToString("0.0") + ", " + sOver[1] + " over 2; overshoot worst " + overW[1].ToString("0.0") + ", " + oOver[1] + " over 8), hem row " + (HemDiff >= 0 ? "+" : "") + HemDiff.ToString("0.0") + " px against expected -> shortfall " + ShortWorst.ToString("0.0") + " overshoot " + OverWorst.ToString("0.0") + " " + (Pass ? "PASS" : "FAIL");
  }
}
public class Pt { public string Name, Zone, Status; public double X, Y; public Pt(string n, string z, double x, double y, string s) { Name = n; Zone = z; X = x; Y = y; Status = s; } }
public static class Pts {
  public static bool MaleBody; public static string Kept = "";
  // outline middle: from the edge pixel (x + xo, xo = -1 on the right side where x = last pixel + 1) walk inward (dx,dy), through at most skip transparent pixels (top row gap, notch), then while opaque and dark (mean RGB < 60), at most 24 px (an outline is 8-20 px across; longer = the walk runs along a slanted stroke or into a drawn line, capped and logged); the point is the middle of that run; a run under 2 px (no outline) keeps the edge and is logged in Kept
  static int Run(Func<int,int,bool> on, Func<int,int,double> lum, int px, int py, int dx, int dy) { int n = 0; while (n < 24 && on(px + n*dx, py + n*dy) && lum(px + n*dx, py + n*dy) < 60) n++; return n; }
  static Pt Q(Func<int,int,bool> on, Func<int,int,double> lum, string name, string zone, double x, double y, int xo, int dx, int dy, int skip, string st) { int px = (int)Math.Floor(x) + xo, py = (int)Math.Floor(y); int k = 0; while (k < skip && !on(px + k*dx, py + k*dy)) k++; int n = Run(on, lum, px + k*dx, py + k*dy, dx, dy); if (n < 2) { Kept += (Kept.Length > 0 ? ", " : "") + name + " (run " + n + ")"; return new Pt(name, zone, x, y, st); } if (n == 24) Kept += (Kept.Length > 0 ? ", " : "") + name + " (run capped at 24)"; return new Pt(name, zone, x + dx * (k + (n - 1) / 2.0), y + dy * (k + (n - 1) / 2.0), st); }
  static byte[] Ld(string p, out int w, out int h) { using (Bitmap b = new Bitmap(p)) { w = b.Width; h = b.Height; BitmapData d = b.LockBits(new Rectangle(0,0,w,h), ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb); byte[] x = new byte[w*h*4]; System.Runtime.InteropServices.Marshal.Copy(d.Scan0, x, 0, x.Length); b.UnlockBits(d); return x; } }
  // Points of attention of a body texture (south). Status: detected, to place (estimate shown, weak or missing detection), not in texture.
  // Side view (east, the body faces right): front = right edge, back = left edge of each row. An extreme that lands on the edge of its search range is 'to place'.
  public static List<Pt> Side(string path) { Kept = "";
    int w, h; byte[] a = Ld(path, out w, out h); List<Pt> P = new List<Pt>();
    Func<int, int, bool> on = (x, y) => x >= 0 && y >= 0 && x < w && y < h && a[(y*w+x)*4+3] > 40;
    Func<int, int, double> lum = (x, y) => (a[(y*w+x)*4] + a[(y*w+x)*4+1] + a[(y*w+x)*4+2]) / 3.0;
    int[] l = new int[h], r = new int[h]; int top = -1, bot = -1;
    for (int y = 0; y < h; y++) { l[y] = -1; r[y] = -1; for (int x = 0; x < w; x++) if (on(x, y)) { if (l[y] < 0) l[y] = x; r[y] = x; } if (l[y] >= 0) { if (top < 0) top = y; bot = y; } }
    int H = bot - top; Func<double, int> row = f => top + (int)Math.Round(f * H);
    // extreme of the front (max r) or back (min l) between two shares of the height
    Action<string, string, double, double, bool, bool> add = (name, zone, f0, f1, front, most) => {
      int y0 = row(f0), y1 = row(f1), best = -1; for (int y = y0; y <= y1; y++) { if (l[y] < 0) continue; int v = front ? r[y] : -l[y]; if (best < 0 || (most ? v > (front ? r[best] : -l[best]) : v < (front ? r[best] : -l[best]))) best = y; }
      if (best < 0) { P.Add(new Pt(name, zone, -1, -1, "not in texture")); return; }
      bool edge = best <= y0 + 1 || best >= y1 - 1; double x = front ? r[best] + 1 : l[best];
      P.Add(Q(on, lum, name, zone, x, best, front ? -1 : 0, front ? -1 : 1, 0, 0, edge ? "to place" : "detected")); };
    P.Add(Q(on, lum, "top", "extremes", (l[top] + r[top] + 1) / 2.0, top, 0, 0, 1, 16, "detected"));
    P.Add(new Pt("bottom", "extremes", (l[bot] + r[bot] + 1) / 2.0, bot, "detected"));
    int maxW = 0; for (int y = top; y < row(0.30); y++) if (r[y] - l[y] > maxW) maxW = r[y] - l[y];
    int neck = top; for (int y = top; y < row(0.30); y++) if (r[y] - l[y] >= 0.55 * maxW) { neck = y; break; }
    P.Add(Q(on, lum, "neck front", "head/neck", r[neck] + 1, neck, -1, -1, 0, 0, neck - top < 6 ? "to place" : "detected"));
    P.Add(Q(on, lum, "neck back", "head/neck", l[neck], neck, 0, 1, 0, 0, neck - top < 6 ? "to place" : "detected"));
    add("upper back (shoulder blade)", "shoulders", 0.10, 0.40, false, true);
    add("chest front", "chest", 0.15, 0.50, true, true);
    // breast apex: pink pixels (nipple) if any, near the front
    double sx = 0, sy = 0; int sn = 0; for (int y = top; y < row(0.6); y++) for (int x = 0; x < w; x++) { if (!on(x, y)) continue; int i = (y*w+x)*4; int R = a[i+2], G = a[i+1], B = a[i]; if (R > 150 && R - G > 12 && R - B > 10) { sx += x; sy += y; sn++; } }
    if (sn > 5) P.Add(new Pt("breast apex", "chest", sx / sn, sy / sn, "detected")); else P.Add(new Pt("breast apex", "chest", -1, -1, "not in texture"));
    add("waist front", "torso", 0.35, 0.65, true, false);
    add("waist back (small of the back)", "torso", 0.35, 0.65, false, false);
    add("belly front", "torso", 0.50, 0.85, true, true);
    add("buttock back", "pelvis", 0.55, 0.92, false, true);
    int lb = bot - 2; P.Add(Q(on, lum, "leg bottom front", "legs", r[lb] + 1, lb, -1, -1, 0, 0, "detected")); P.Add(Q(on, lum, "leg bottom back", "legs", l[lb], lb, 0, 1, 0, 0, "detected"));
    foreach (string s in new string[] { "navel", "sex", "crotch point", "elbow", "wrist", "hand end", "knee", "ankle" }) P.Add(new Pt(s, "pelvis", -1, -1, "not in texture"));
    return P;
  }
  // Back view: points that only exist on the front are 'not in view'.
  static readonly string[] FrontOnly = { "breast apex L", "breast apex R", "cleavage", "under-breast fold L", "under-breast fold R", "navel", "sex", "groin crease L", "groin crease R", "jugular notch" };
  public static List<Pt> Body(string path) {
    if (Gl.Facing == "east") return Side(path);
    int w, h; byte[] a = Ld(path, out w, out h); List<Pt> P = new List<Pt>();
    Func<int, int, bool> on = (x, y) => x >= 0 && y >= 0 && x < w && y < h && a[(y*w+x)*4+3] > 40;
    Func<int, int, double> lum = (x, y) => (a[(y*w+x)*4] + a[(y*w+x)*4+1] + a[(y*w+x)*4+2]) / 3.0;
    int[] l = new int[h], r = new int[h]; int top = -1, bot = -1, minX = w, maxX = -1, minXy = 0, maxXy = 0;
    for (int y = 0; y < h; y++) { l[y] = -1; r[y] = -1; for (int x = 0; x < w; x++) if (on(x, y)) { if (l[y] < 0) l[y] = x; r[y] = x; } if (l[y] >= 0) { if (top < 0) top = y; bot = y; if (l[y] < minX) { minX = l[y]; minXy = y; } if (r[y] > maxX) { maxX = r[y]; maxXy = y; } } }
    string info; double[] v = Lm.Detect(path, out info); bool ww = Lm.WeakWaist, wh = Lm.WeakHip, wa = Lm.WeakArm;
    int H = bot - top; double mid = (l[top + H / 2] + r[top + H / 2] + 1) / 2.0;
    Kept = "";
    P.Add(Q(on, lum, "top", "extremes", (l[top] + r[top] + 1) / 2.0, top, 0, 0, 1, 16, "detected")); P.Add(Q(on, lum, "bottom", "extremes", (l[bot] + r[bot] + 1) / 2.0, bot, 0, 0, -1, 0, "detected"));
    P.Add(Q(on, lum, "leftmost", "extremes", minX, minXy, 0, 1, 0, 0, "detected")); P.Add(Q(on, lum, "rightmost", "extremes", maxX + 1, maxXy, -1, -1, 0, 0, "detected"));
    bool weakNeck = v[1] - v[23] < 6;
    P.Add(Q(on, lum, "neck base L", "head/neck", v[0], v[1], 0, 1, 0, 0, weakNeck ? "to place" : "detected")); P.Add(Q(on, lum, "neck base R", "head/neck", v[2], v[3], -1, -1, 0, 0, weakNeck ? "to place" : "detected"));
    P.Add(new Pt("jugular notch", "head/neck", mid, v[1], "to place"));
    P.Add(Q(on, lum, "shoulder tip L", "shoulders", v[4], v[5], 0, 1, 0, 0, "detected")); P.Add(Q(on, lum, "shoulder tip R", "shoulders", v[6], v[7], -1, -1, 0, 0, "detected"));
    P.Add(Q(on, lum, "armpit L", "shoulders", v[8], v[9], 0, 1, 0, 0, wa ? "to place" : "detected")); P.Add(Q(on, lum, "armpit R", "shoulders", v[10], v[11], -1, -1, 0, 0, wa ? "to place" : "detected"));
    // nipples: pink pixels (red well above green and blue) in the upper 60 % of the body, one cluster each side of the midline
    double[] sx = new double[2], sy = new double[2]; int[] sn = new int[2];
    for (int y = top; y < top + (int)(0.6 * H); y++) for (int x = 0; x < w; x++) { if (!on(x, y)) continue; int i = (y*w+x)*4; int R = a[i+2], G = a[i+1], B = a[i]; if (R > 150 && R - G > 12 && R - B > 10) { int s = x < mid ? 0 : 1; sx[s] += x; sy[s] += y; sn[s]++; } }
    bool nip = sn[0] > 5 && sn[1] > 5;
    double nlx = nip ? sx[0] / sn[0] : mid - 0.3 * (v[6] - v[4]), nly = nip ? sy[0] / sn[0] : v[5] + 0.45 * (v[13] - v[5]), nrx = nip ? sx[1] / sn[1] : mid + 0.3 * (v[6] - v[4]), nry = nip ? sy[1] / sn[1] : nly;
    P.Add(new Pt("breast apex L", "chest", nlx, nly, nip ? "detected" : "to place")); P.Add(new Pt("breast apex R", "chest", nrx, nry, nip ? "detected" : "to place"));
    P.Add(new Pt("cleavage", "chest", mid, (nly + nry) / 2, "to place"));
    double fold = 0.15 * (nrx - nlx); P.Add(new Pt("under-breast fold L", "chest", nlx, (nly + nry) / 2 + fold, "to place")); P.Add(new Pt("under-breast fold R", "chest", nrx, (nly + nry) / 2 + fold, "to place"));
    P.Add(Q(on, lum, "waist L", "torso", v[12], v[13], 0, 1, 0, 0, ww ? "to place" : "detected")); P.Add(Q(on, lum, "waist R", "torso", v[14], v[15], -1, -1, 0, 0, ww ? "to place" : "detected"));
    // sex: top of the dark stem on the middle column, going up from the bottom - 30 (drawn crotch); crotch point: silhouette notch between the legs
    int mc = (int)Math.Round(mid); int yy = bot - 30; Func<int, bool> dk = y2 => on(mc, y2) && lum(mc, y2) < 60; while (yy > top + H / 2 && !dk(yy)) yy--; bool stem = yy > top + H / 2; int sexY = yy; if (stem) { while (yy > top && dk(yy)) yy--; sexY = yy + 1; }
    // on the men the dark stem is the pubic line under the navel, not the drawn sex: sex left to place there
    bool sexOk = stem && !MaleBody;
    // navel: first dark run on the middle column between the waist minus 30 and 25 px above the stem top
    int navY = -1; int yEnd = stem ? sexY - 25 : bot - 40; for (int y = (int)v[13] - 30; y < yEnd; y++) if (on(mc, y) && lum(mc, y) < 110) { int y2 = y; while (y2 < yEnd && on(mc, y2) && lum(mc, y2) < 110) y2++; navY = (y + y2) / 2; break; }
    if (MaleBody && stem && navY < 0) navY = sexY - 8;
    P.Add(new Pt("navel", "torso", mid, navY > 0 ? navY : v[13] + 0.3 * (bot - v[13]), navY > 0 ? "detected" : "to place"));
    P.Add(Q(on, lum, "hip L", "torso", v[16], v[17], 0, 1, 0, 0, wh ? "to place" : "detected")); P.Add(Q(on, lum, "hip R", "torso", v[18], v[19], -1, -1, 0, 0, wh ? "to place" : "detected"));
    double crY = v[21]; bool notch = info.Contains("(notch)");
    P.Add(new Pt("groin crease L", "pelvis", (v[16] + mid) / 2, (v[17] + (stem ? sexY : crY)) / 2, "to place")); P.Add(new Pt("groin crease R", "pelvis", (v[18] + mid) / 2, (v[19] + (stem ? sexY : crY)) / 2, "to place"));
    P.Add(new Pt("sex", "pelvis", mid, sexOk ? sexY : bot - 0.10 * H, sexOk ? "detected" : "to place"));
    if (notch) P.Add(Q(on, lum, "crotch point", "pelvis", mid, crY, 0, 0, -1, 6, "detected")); else P.Add(new Pt("crotch point", "pelvis", mid, stem ? sexY + 0.5 * (bot - sexY) : bot, "to place"));
    // legs: bottom of each leg = centre of the left and right halves of the bottom rows
    int lb = bot - 2; P.Add(Q(on, lum, "leg bottom L", "legs", (l[lb] + mid) / 2, lb, 0, 0, -1, 0, "detected")); P.Add(Q(on, lum, "leg bottom R", "legs", (r[lb] + 1 + mid) / 2, lb, 0, 0, -1, 0, "detected"));
    foreach (string s in new string[] { "elbow L", "elbow R", "wrist L", "wrist R", "hand end L", "hand end R" }) P.Add(new Pt(s, "arms", -1, -1, "not in texture"));
    foreach (string s in new string[] { "knee L", "knee R", "ankle L", "ankle R" }) P.Add(new Pt(s, "legs", -1, -1, "not in texture"));
    int t0 = top; while (t0 < bot && !on(mc, t0)) t0++; int t1 = t0; while (t1 < bot && on(mc, t1) && lum(mc, t1) < 60) t1++; bool line = t1 - t0 >= 2; P.Add(new Pt("midline top", "axis", mid, line ? (t0 + t1 - 1) / 2.0 : t0, line ? "detected" : "to place")); P.Add(new Pt("midline crotch", "axis", mid, stem ? sexY : crY, stem || notch ? "detected" : "to place"));
    if (Gl.Facing == "north") foreach (Pt p in P) if (Array.IndexOf(FrontOnly, p.Name) >= 0) { p.Status = "not in view"; p.X = -1; p.Y = -1; }
    return P;
  }
  public static List<Pt> Garment(string garPath, int band) {
    int w, h; byte[] a = Ld(garPath, out w, out h); List<Pt> P = new List<Pt>(); double[] f = Gl.Features(a, w, h, band); string[] nm = Gl.Names.Split(' ');
    Func<int, int, bool> on = (x, y) => x >= 0 && y >= 0 && x < w && y < h && a[(y*w+x)*4+3] > 40;
    Func<int, int, double> lum = (x, y) => (a[(y*w+x)*4] + a[(y*w+x)*4+1] + a[(y*w+x)*4+2]) / 3.0;
    // hem corners and sleeve ends on the garment's own outline middle (hem: upward, sleeves: horizontal inward); ring points stay on the ring skeleton
    for (int k = 0; k < f.Length / 2; k++) { string n = nm[k]; int dx = n == "sleeveL" ? 1 : n == "sleeveR" ? -1 : 0, dy = n == "hemL" || n == "hemR" ? -1 : 0; P.Add(dx != 0 || dy != 0 ? Q(on, lum, "garment " + n, "garment", f[2*k], f[2*k+1], n.EndsWith("R") ? -1 : 0, dx, dy, 0, "detected") : new Pt("garment " + n, "garment", f[2*k], f[2*k+1], "detected")); }
    int bot = -1; int[] l = new int[h], r = new int[h]; for (int y = 0; y < h; y++) { l[y] = -1; for (int x = 0; x < w; x++) if (a[(y*w+x)*4+3] > 40) { if (l[y] < 0) l[y] = x; r[y] = x; } if (l[y] >= 0) bot = y; }
    // hem middle: the column nearest the middle that has fabric in the bottom 10 % of the garment, at its lowest fabric row; none when that column is more than 15 % of the width away (open front)
    int gtop = -1; for (int y = 0; y < h; y++) if (l[y] >= 0) { gtop = y; break; } int cxh = (l[bot] + r[bot] + 1) / 2, ylim = bot - (int)(0.10 * (bot - gtop)), best = -1, by = -1;
    for (int d = 0; d < w / 2 && best < 0; d++) foreach (int x in new int[] { cxh - d, cxh + d }) { if (x < 0 || x >= w || best >= 0) continue; for (int y = bot; y >= ylim; y--) if (on(x, y)) { best = x; by = y; break; } }
    if (best >= 0 && Math.Abs(best - cxh) <= 0.15 * (r[bot] - l[bot] + 1)) P.Add(Q(on, lum, "garment hem middle", "garment", best + 0.5, by, 0, 0, -1, 0, "detected")); else P.Add(new Pt("garment hem middle", "garment", -1, -1, "not in texture"));
    return P;
  }
  // Garment points with the body known. Sleeve end = last row where the garment's side edge still lies on the body outline (gap <= 2 px) before it leaves it inward for at least 6 rows,
  // searched from the shoulders down to 60 % of the body height; none when the garment is cut on the body silhouette (no sleeve drawn in the south view).
  public static List<Pt> Garment(string garPath, int band, string bodyPath) {
    List<Pt> P = Garment(garPath, band); P.RemoveAll(p => p.Name.Contains("sleeve")); string nk = Gl.NeckKind;
    int w, h; byte[] g = Ld(garPath, out w, out h), b = Ld(bodyPath, out w, out h);
    int[] gl = new int[h], gr = new int[h], bl = new int[h], br = new int[h]; int bt = -1, bb = -1;
    for (int y = 0; y < h; y++) { gl[y] = gr[y] = bl[y] = br[y] = -1; for (int x = 0; x < w; x++) { int i = (y*w+x)*4 + 3; if (g[i] > 40) { if (gl[y] < 0) gl[y] = x; gr[y] = x; } if (b[i] > 40) { if (bl[y] < 0) bl[y] = x; br[y] = x; } } if (bl[y] >= 0) { if (bt < 0) bt = y; bb = y; } }
    int sh = bt; for (int y = bt; y < bt + (int)(0.30 * (bb - bt)); y++) if (br[y] - bl[y] > br[sh] - bl[sh]) sh = y;
    int gt = -1; for (int y = 0; y < h; y++) if (gl[y] >= 0) { gt = y; break; } if (gt > bt + 0.35 * (bb - bt)) { foreach (Pt p in P) if (p.Name.Contains("neck") || p.Name.Contains("ring")) p.Name = p.Name.Replace("garment neck", "garment top edge ").Replace("garment ring", "garment top edge "); nk = "lower body: top edge"; if (!P.Exists(p => p.Name.Contains("top edge"))) { int x0 = w, x1 = -1; for (int x = 0; x < w; x++) for (int y = gt; y < gt + 40 && y < h; y++) if (g[(y*w+x)*4+3] > 40) { if (x < x0) x0 = x; if (x > x1) x1 = x; break; } for (int k = 0; k < 8; k++) { int x = x0 + (int)Math.Round((x1 - x0) * (k + 0.5) / 8.0); int yy = gt; while (yy < h - 1 && g[(yy*w+x)*4+3] <= 40) yy++; P.Add(new Pt("garment top edge " + k, "garment", x, yy, "detected")); } } } Gl.NeckKind = nk;
    int yEnd = bt + (int)(0.60 * (bb - bt));
    for (int side = 0; side < 2; side++) { int found = -1;
      Func<int, int> gap = y => gl[y] < 0 ? 999 : (side == 0 ? gl[y] - bl[y] : br[y] - gr[y]);
      for (int y = sh; y < yEnd - 6; y++) { if (gap(y) > 2) continue; bool leaves = true; for (int k = 1; k <= 6; k++) if (gap(y + k) <= 4) { leaves = false; break; } if (leaves) { found = y; break; } }
      string n = "garment sleeve end " + (side == 0 ? "L" : "R");
      if (found < 0) P.Add(new Pt(n, "garment", -1, -1, "not in texture")); else P.Add(new Pt(n, "garment", side == 0 ? gl[found] : gr[found] + 1, found, "detected")); }
    return P;
  }
  static Color ZoneColor(string z) { switch (z) { case "extremes": return Color.FromArgb(120,120,120); case "head/neck": return Color.FromArgb(150,60,200); case "shoulders": return Color.FromArgb(0,110,220); case "chest": return Color.FromArgb(230,40,120); case "torso": return Color.FromArgb(0,160,80); case "pelvis": return Color.FromArgb(230,120,0); case "legs": return Color.FromArgb(140,90,40); case "axis": return Color.FromArgb(0,170,190); default: return Color.FromArgb(200,20,20); } }
  // Picture: body (and garment) at 2x, crop around the body, filled dot = detected, ring = to place, short label.
  public static void Draw(string bodyPath, string garPath, List<Pt> P, string title, string outPath) {
    using (Bitmap body = new Bitmap(bodyPath)) {
      int x0 = 56, y0 = 96, cw = 400, ch = 416, s = 2, lab = 30; using (Bitmap pic = new Bitmap(cw * s + 260, ch * s + lab)) using (Graphics g = Graphics.FromImage(pic)) {
        g.Clear(Color.FromArgb(200,196,182)); g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.NearestNeighbor; g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.Half;
        Rectangle dst = new Rectangle(0, lab, cw * s, ch * s), src = new Rectangle(x0, y0, cw, ch); g.DrawImage(body, dst, src, GraphicsUnit.Pixel);
        if (!string.IsNullOrEmpty(garPath)) using (Bitmap gar = new Bitmap(garPath)) g.DrawImage(gar, dst, src, GraphicsUnit.Pixel);
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        using (Font tf = new Font("Arial", 13, FontStyle.Bold)) g.DrawString(title, tf, Brushes.Black, 6, 6);
        using (Font f = new Font("Arial", 8, FontStyle.Bold)) {
          Pt mt = P.Find(p => p.Name == "midline top"), mc = P.Find(p => p.Name == "midline crotch");
          if (mt != null && mc != null) using (Pen pen = new Pen(ZoneColor("axis"), 1.5f) { DashStyle = System.Drawing.Drawing2D.DashStyle.Dash }) g.DrawLine(pen, (float)((mt.X - x0) * s), (float)((mt.Y - y0) * s + lab), (float)((mc.X - x0) * s), (float)((mc.Y - y0) * s + lab));
          int ly = lab; foreach (Pt p in P) { Color c = ZoneColor(p.Zone);
            if (p.Status.StartsWith("not in")) continue;
            float px = (float)((p.X - x0) * s), py = (float)((p.Y - y0) * s + lab);
            using (SolidBrush b = new SolidBrush(c)) using (Pen pen = new Pen(c, 2f)) {
              if (p.Status == "detected") g.FillEllipse(b, px - 4, py - 4, 8, 8); else { g.DrawEllipse(pen, px - 6, py - 6, 12, 12); g.DrawLine(pen, px - 3, py, px + 3, py); }
              string t = p.Name.Replace("garment ", "g.") + (p.Status == "to place" ? " ?" : "");
              using (SolidBrush bg = new SolidBrush(Color.FromArgb(170, 255, 255, 255))) { SizeF sz = g.MeasureString(t, f); float tx = p.X < 256 ? px - sz.Width - 6 : px + 6; g.FillRectangle(bg, tx, py - 7, sz.Width, sz.Height); g.DrawString(t, f, b, tx, py - 7); } } }
          // legend
          float lx = cw * s + 10; float yy2 = lab + 4; foreach (string z in new string[] { "extremes", "head/neck", "shoulders", "chest", "torso", "pelvis", "legs", "axis", "garment" }) { using (SolidBrush b = new SolidBrush(ZoneColor(z))) { g.FillEllipse(b, lx, yy2 + 3, 9, 9); g.DrawString(z, f, Brushes.Black, lx + 14, yy2 + 1); } yy2 += 16; }
          yy2 += 8; g.DrawString("filled dot = detected", f, Brushes.Black, lx, yy2); yy2 += 16; g.DrawString("ring + ? = to place by eye", f, Brushes.Black, lx, yy2); yy2 += 16;
          string nit = ""; foreach (Pt p in P) if (p.Status.StartsWith("not in")) nit += (nit.Length > 0 ? ", " : "") + p.Name; g.DrawString("not in the texture / not in view:", f, Brushes.Black, lx, yy2 + 8); RectangleF rr = new RectangleF(lx, yy2 + 24, 245, 200); g.DrawString(nit, f, Brushes.Black, rr); }
        pic.Save(outPath, ImageFormat.Png); } }
  }
}
'@
