Add-Type -AssemblyName System.Drawing
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$v = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\1814987817\Textures\Things\Apparel\CasualTShirt\'
foreach ($k in @(@('male','Male'),@('thin','Thin'),@('fat','Fat'),@('hulk','Hulk'),@('female','Female'))) {
  $src = New-Object System.Drawing.Bitmap ($v + "CasualTShirt_$($k[1])_south.png"); $dst = New-Object System.Drawing.Bitmap 512, 512
  $g = [System.Drawing.Graphics]::FromImage($dst); $g.InterpolationMode = 'HighQualityBicubic'; $g.PixelOffsetMode = 'Half'; $g.DrawImage($src, 0, 0, 512, 512); $g.Dispose()
  $dst.Save($tmp + "vae512_$($k[0]).png", [System.Drawing.Imaging.ImageFormat]::Png); $dst.Dispose(); $src.Dispose() }
'ok'
