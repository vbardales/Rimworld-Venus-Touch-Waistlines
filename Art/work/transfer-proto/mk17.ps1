Add-Type -AssemblyName System.Drawing
$S = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-02_vanilla-bodies-3\screenshots\film\pickletools-texture-save--vanilla-'
$imo = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\2660249018\Textures\Things\Pawn\Humanlike\Apparel\ShirtBasic\ShirtBasic_'
$wdiShirt = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Apparel\ShirtBasic\ShirtBasic_'
function Scale($inp, $dst, $f) {
  $b = New-Object System.Drawing.Bitmap $inp
  $o = New-Object System.Drawing.Bitmap 512, 512, ([System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $g = [System.Drawing.Graphics]::FromImage($o)
  $g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'
  $g.DrawImage($b, 0, 0, 512, 512); $g.Dispose(); $o.Save($dst); "$dst from $($b.Width)x$($b.Height)"; $b.Dispose(); $o.Dispose()
}
foreach ($fc in 'east', 'north') {
  foreach ($k in 'male', 'thin', 'fat', 'hulk', 'female') {
    $K = (Get-Culture).TextInfo.ToTitleCase($k)
    Scale ($film + $k + '-' + $fc + '\0000.png') ($S + 'vbody512_' + $k + '_' + $fc + '.png') 4
    Scale ($imo + $K + '_' + $fc + '.png') ($S + 'imo512_' + $k + '_' + $fc + '.png') 1
  }
  foreach ($k in 'Thin_Female', 'Fat_Female', 'Hulk_Female') {
    Scale ($wdiShirt + $k + '_' + $fc + '.png') ($S + 'wshirt512_' + $k + '_' + $fc + '.png') 2
  }
}
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
$t = Get-Content ($d + 'step16.ps1') -Raw
$t = $t.Replace('vbody512_$sk.png', 'vbody512_${sk}${fs}.png').Replace('imo512_$sk.png', 'imo512_${sk}${fs}.png')
$t = $t.Replace('Naked_${tk}_south.png', 'Naked_${tk}_${facing}.png').Replace('wshirt512_$tk.png', 'wshirt512_${tk}${fs}.png')
$t = $t.Replace('s16${sfx}_${tk}.png', 's17${sfx}_${facing}_${tk}.png').Replace('s16u${sfx}_${tk}.png', 's17u${sfx}_${facing}_${tk}.png')
Set-Content ($d + 'step17.ps1') $t -Encoding UTF8
'ok'
