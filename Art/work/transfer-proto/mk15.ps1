Add-Type -AssemblyName System.Drawing
$S = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$src = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2068281501\Textures\Things\Pawn\Humanlike\Bodies\'
New-Item -ItemType Directory -Force -Path ($S + 'bb512') | Out-Null
foreach ($k in 'Male', 'Thin', 'Fat', 'Hulk', 'Female') {
  foreach ($f in 'south', 'east', 'north') {
    $inp = $src + 'Naked_' + $k + '_' + $f + '.png'
    $dst = $S + 'bb512\Naked_' + $k + '_' + $f + '.png'
    $sb = New-Object System.Drawing.Bitmap $inp
    $o = New-Object System.Drawing.Bitmap 512, 512, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $g = [System.Drawing.Graphics]::FromImage($o)
    $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'
    $g.DrawImage($sb, 0, 0, 512, 512); $g.Dispose()
    $o.Save($dst); $sb.Dispose(); $o.Dispose()
  }
}
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
$t = Get-Content ($d + 'step14.ps1') -Raw
$old = '$wdi = ''C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'''
if (-not $t.Contains($old)) { throw 'wdi' }
$t = $t.Replace($old, '$wdi = ''' + $S + 'bb512\''')
$t = $t.Replace('s14${sfx}_${tk}.png', 's15${sfx}_${tk}.png').Replace('s14u${sfx}_${tk}.png', 's15u${sfx}_${tk}.png')
Set-Content ($d + 'step15.ps1') $t -Encoding UTF8
'ok'
