$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
function LoadPx($path) { $bm = New-Object System.Drawing.Bitmap $path; $w = $bm.Width; $h = $bm.Height
  $d = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,$w,$h), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $px = New-Object byte[] ($w*$h*4); [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $px, 0, $px.Length); $bm.UnlockBits($d); $bm.Dispose(); return ,@($px, $w, $h) }
function Bbox($s) { if ($s -match 'bbox \((\d+),(\d+)\)-\((\d+),(\d+)\)') { return @([int]$Matches[1], [int]$Matches[2], [int]$Matches[3], [int]$Matches[4]) } return $null }
$pairs = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'), @('thin','Thin_Female'), @('fat','Fat_Female'), @('hulk','Hulk_Female'))
foreach ($pr in $pairs) {
  $sk = $pr[0]; $tk = $pr[1]; $sBodyP = $tmp + "vbody512_$sk.png"; $sGarP = $tmp + "imo512_$sk.png"; $tBodyP = $wdi + "Naked_${tk}_south.png"
  $sB = LoadPx $sBodyP; $sG = LoadPx $sGarP
  $L = $null; $R = $null; $ot = 0; $ob = 0; $oo = 0; [S3]::Offsets($sB[0], $sG[0], 512, 512, [ref]$L, [ref]$R, [ref]$ot, [ref]$ob, [ref]$oo); $band = [Math]::Max(15, $oo + 1)
  $sw = [Cm]::Measure($sBodyP, $sGarP); $bs = Bbox ([S3]::RingBoxIn($sG[0], 512, 512, $band, 60, 150, 100, 360, 330))
  "== $sk -> $tk"
  foreach ($rd in @(@('round 1', ($tmp + "s2_${tk}_off.png")), @('round 2', ($tmp + "s3_${tk}.png")))) {
    $o = LoadPx $rd[1]; $worst = 0.0
    $c1 = [C1m]::Run($sBodyP, $sGarP, $tBodyP, $rd[1], [ref]$worst)
    $tw = [Cm]::Measure($tBodyP, $rd[1]); $bt = Bbox ([S3]::RingBoxIn($o[0], 512, 512, $band, 60, 150, 100, 360, 330))
    $c2 = ''
    if ($bs -and $bt) {
      $sNw = ($bs[2]-$bs[0]+1) / $sw.ShoulderW; $tNw = ($bt[2]-$bt[0]+1) / $tw.ShoulderW
      $sNd = ($bs[3] - $sw.GarTop + 1) / ($sw.Bot - $sw.Top); $tNd = ($bt[3] - $tw.GarTop + 1) / ($tw.Bot - $tw.Top)
      $c2 = "C2 ring width/shoulders $([Math]::Round(100*[Math]::Abs($tNw/$sNw-1),1)) %, ring bottom depth below garment top / torso length $([Math]::Round(100*[Math]::Abs($tNd/$sNd-1),1)) %" }
    "  [$($rd[0])] $c1 | $c2"
  }
}
