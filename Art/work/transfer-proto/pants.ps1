param([string]$facing = 'south')
# Visible-pants mods studied as a new body: vanilla naked body + the mod's Pants drawn on it = the composite body; body points on the composite, garment points on the pants alone.
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
[Gl]::Facing = $facing
$w = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\'
$mods = @(
  @('AB', ($w + '2986402536\Textures\Things\Pawn\Humanlike\Apparel\Pants\')),
  @('XND', ($w + '2264108215\Common\Textures\Core\Things\Pawn\Humanlike\Apparel\Pants\')),
  @('catMonke', ($w + '3671309201\Textures\Core\Things\Pawn\Humanlike\Apparel\Pants\')))
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points\'
$rows = New-Object System.Collections.Generic.List[string]
$bodies = @('Male','Thin','Fat','Hulk','Female')
foreach ($m in $mods) {
  $pics = @()
  foreach ($b in $bodies) {
    $bp = $tmp + "core17_512\Naked_${b}_$facing.png"
    # pants at 512 (x4 nearest for 128 px textures), then the composite body
    $s = New-Object System.Drawing.Bitmap ($m[1] + "Pants_${b}_$facing.png")
    $pp = $tmp + "pants512_$($m[0])_${b}_$facing.png"; $cp = $tmp + "pantsbody_$($m[0])_${b}_$facing.png"
    $d = New-Object System.Drawing.Bitmap 512, 512; $gg = [System.Drawing.Graphics]::FromImage($d); $gg.InterpolationMode = 'NearestNeighbor'; $gg.PixelOffsetMode = 'Half'; $gg.DrawImage($s, 0, 0, 512, 512); $gg.Dispose(); $d.Save($pp, [System.Drawing.Imaging.ImageFormat]::Png); $s.Dispose()
    $c = New-Object System.Drawing.Bitmap $bp; $c2 = New-Object System.Drawing.Bitmap 512, 512; $gg = [System.Drawing.Graphics]::FromImage($c2); $gg.DrawImage($c, 0, 0, 512, 512); $gg.DrawImage($d, 0, 0, 512, 512); $gg.Dispose(); $c2.Save($cp, [System.Drawing.Imaging.ImageFormat]::Png); $c.Dispose(); $c2.Dispose(); $d.Dispose()
    $name = "$($m[0]) $b ($facing)"
    [Pts]::MaleBody = $false; $P = [Pts]::Body($cp)
    foreach ($q in [Pts]::Garment($pp, 15, $cp)) { $q.Name = 'pants ' + $q.Name; $P.Add($q) }
    $nk = [Gl]::NeckKind
    $pic = $tmp + "pantspts_$($m[0])_${b}_$facing.png"; $pics += $pic
    [Pts]::Draw($cp, $null, $P, $name, $pic)
    foreach ($p in $P) { $rows.Add(('{0}|{1}|{2}|{3}|{4}|{5}' -f $name, $p.Zone, $p.Name, $(if ($p.X -ge 0) { [Math]::Round($p.X) } else { '' }), $(if ($p.Y -ge 0) { [Math]::Round($p.Y) } else { '' }), $p.Status)) }
    "  $name : top kind = $nk"
  }
  # one sheet per mod and facing: the 5 bodies side by side
  $ims = $pics | % { [System.Drawing.Image]::FromFile($_) }; $cw = $ims[0].Width; $ch = $ims[0].Height
  $sh = New-Object System.Drawing.Bitmap ($cw * $ims.Count), $ch; $g = [System.Drawing.Graphics]::FromImage($sh)
  for ($i = 0; $i -lt $ims.Count; $i++) { $g.DrawImage($ims[$i], $i * $cw, 0, $cw, $ch); $ims[$i].Dispose() }
  $g.Dispose(); $sh.Save($out + "pants-$($m[0])-$facing.png", [System.Drawing.Imaging.ImageFormat]::Png); $sh.Dispose()
}
$rows | Set-Content -Encoding UTF8 ($out + "pants-$facing-table.txt")
"$facing : " + $rows.Count + " rows"
