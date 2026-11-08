$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
function LoadPx($path) { $bm = New-Object System.Drawing.Bitmap $path; $w = $bm.Width; $h = $bm.Height
  $d = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,$w,$h), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $px = New-Object byte[] ($w*$h*4); [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $px, 0, $px.Length); $bm.UnlockBits($d); $bm.Dispose(); return ,@($px, $w, $h) }
$band = 15; if (-not $kinds) { $kinds = @('vshirt') }
[Layers]::Redraw = $true; [Layers]::InkLuma = 60; [Layers]::FillDilate = 3; [Layers]::TargetWidth = 0.0; [Layers]::CopyLine = $false; [Layers]::StrokeGray = 15; [S3]::Bridge = $false; [S3]::RadiusBias = 0.4; [Layers]::FillBlur = 6; [S3]::SourceBand = 0; [S3]::RingTopY = 0; [Layers]::HoleBoxL = $null; [S3]::RelativeInk = $false; [Layers]::Extra = $null
$rows = New-Object System.Collections.Generic.List[double]
foreach ($k in 'male','thin','fat','hulk','female') {
  foreach ($kind in $kinds) {
    $bodyP = $tmp + "vbody512_$k.png"; $shirtP = $tmp + "${kind}512_$k.png"
    $body = LoadPx $bodyP; $shirt = LoadPx $shirtP
    $L = $null; $R = $null; $t = 0; $b = 0; $o = 0; [S3]::Offsets($body[0], $shirt[0], 512, 512, [ref]$L, [ref]$R, [ref]$t, [ref]$b, [ref]$o)
    $band = [Math]::Max(15, $o + 1); [Layers]::OffL = $L; [Layers]::OffR = $R; [Layers]::OffTop = $t; [Layers]::OffBot = $b; [Layers]::OutlineW = $o
    # identity rows: every 12 px over the body's rows
    $top = 0; $bot = 0; for ($y = 0; $y -lt 512; $y++) { $any = $false; for ($x = 0; $x -lt 512; $x += 1) { if ($body[0][($y*512+$x)*4+3] -gt 40) { $any = $true; break } }; if ($any) { if ($top -eq 0) { $top = $y }; $bot = $y } }
    $rp = New-Object System.Collections.Generic.List[double]; for ($y = $top + 2; $y -lt $bot - 1; $y += 12) { $rp.Add($y); $rp.Add($y) }
    $outP = $tmp + "id1_${kind}_$k.png"
    $r = [Layers]::Single($bodyP, $shirtP, $bodyP, [double[]]@(), [double[]]$rp.ToArray(), $outP, 2.0, $band)
    $out = LoadPx $outP
    "== $kind $k : offsets L$($L[300]) R$($R[300]) top $t bot $b outline $o; $r"
    "  input : " + ([S3]::Widths($shirt[0], 512, 512, $band, 60, 'in') -split "`n")[0..1] -join " | "
    "  output: " + ([S3]::Widths($out[0], 512, 512, $band, 60, 'out') -split "`n")[0..1] -join " | "
    "  " + [S3]::Chamfer($out[0], $shirt[0], 512, 512, $band, 60) + " | " + [S3]::IoU($out[0], $shirt[0], 512, 512, $band, 60)
  }
}
