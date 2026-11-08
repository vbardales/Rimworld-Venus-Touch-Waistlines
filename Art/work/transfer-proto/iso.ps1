$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
function Px($p) { $bm = New-Object System.Drawing.Bitmap $p; $w = $bm.Width; $h = $bm.Height
  $d = $bm.LockBits((New-Object System.Drawing.Rectangle 0,0,$w,$h), [System.Drawing.Imaging.ImageLockMode]::ReadOnly, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $a = New-Object byte[] ($w*$h*4); [System.Runtime.InteropServices.Marshal]::Copy($d.Scan0, $a, 0, $a.Length); $bm.UnlockBits($d); $bm.Dispose(); return ,@($a, $w, $h) }
function Ext($a, $w, $y) { $l = -1; $r = -1; for ($x = 0; $x -lt $w; $x++) { if ($a[($y*$w+$x)*4+3] -gt 40) { if ($l -lt 0) { $l = $x }; $r = $x } }; return @($l, $r) }
# One garment over its body: everything relative to the body's own landmarks.
function IsoMeasure($bodyP, $garP) {
  $info = ''; $v = [Lm]::Detect($bodyP, [ref]$info)
  $B = Px $bodyP; $G = Px $garP; $w = $B[1]; $h = $B[2]
  $neck = $v[1]; $sh = $v[5]; $arm = $v[9]; $wai = $v[13]; $hip = $v[17]; $cr = $v[21]; $top = $v[23]
  $gTop = -1; $gBot = -1; $gW = 0; $gWy = 0
  for ($y = 0; $y -lt $h; $y++) { $e = Ext $G[0] $w $y; if ($e[0] -ge 0) { if ($gTop -lt 0) { $gTop = $y }; $gBot = $y; if ($e[1] - $e[0] -gt $gW) { $gW = $e[1] - $e[0]; $gWy = $y } } }
  $T = $cr - $top; $o = [ordered]@{}
  $o['collar top (torso %)'] = 100 * ($gTop - $top) / $T
  $o['hem (torso %)'] = 100 * ($gBot - $top) / $T
  $o['widest row (torso %)'] = 100 * ($gWy - $top) / $T
  foreach ($p in @(@('neck', $neck), @('shoulder', $sh), @('armpit', $arm), @('waist', $wai), @('hip', $hip))) {
    $y = [int]$p[1]; $eb = Ext $B[0] $w $y; $eg = Ext $G[0] $w $y; $bw = $eb[1] - $eb[0] + 1
    if ($eg[0] -lt 0) { $o[$p[0] + ' outset px'] = 'n/a'; $o[$p[0] + ' width / body'] = 'n/a'; continue }
    $o[$p[0] + ' outset px'] = (($eb[0] - $eg[0]) + ($eg[1] - $eb[1])) / 2.0
    $o[$p[0] + ' width / body'] = ($eg[1] - $eg[0] + 1) / $bw }
  $o['widest / shoulder body'] = ($gW + 1) / ($v[6] - $v[4])
  $wi = [S3]::Widths($G[0], $w, $h, 0, 60, 'g'); $o['stroke'] = ($wi -replace '\s+', ' ')
  return $o }
$rows = @()
foreach ($k in 'thin', 'fat', 'hulk') { $K = (Get-Culture).TextInfo.ToTitleCase($k); $tk = $K + '_Female'
  $van = IsoMeasure ($tmp + 'vbody512_' + $k + '.png') ($tmp + 'core512_' + $k + '.png')
  $wd = IsoMeasure ($wdi + 'Naked_' + $tk + '_south.png') ($tmp + 'wshirt512_' + $tk + '.png')
  $mine = $null; $mp = $tmp + 's16wdi_' + $tk + '.png'; if (Test-Path $mp) { $mine = IsoMeasure ($wdi + 'Naked_' + $tk + '_south.png') $mp }
  "== $tk  (vanilla Core on vanilla $K | WDI shirt on WDI body | my transfer)"
  foreach ($key in $van.Keys) { $a = $van[$key]; $b = $wd[$key]; $c = if ($mine) { $mine[$key] } else { '-' }
    $f = { param($x) if ($x -is [double]) { $x.ToString('0.00') } else { "$x" } }
    '  {0,-26} {1,10} {2,10} {3,10}' -f $key, (& $f $a), (& $f $b), (& $f $c) } }
