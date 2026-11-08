$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$uw = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\UWUnderwear\'
# vanilla navel = bottom(width / 2) - FrontApexRise of the build (Virginie: at the crotch apex); WDI navel, bust (nipple row) and
# under-breast row (lowest point of the breast's lower stroke) read on the WDI texture (bust.ps1 and by eye)
$rise = @{ thin = 34; fat = 40; hulk = 52 }; $triseW = @{ thin = 44; fat = 42; hulk = 54 }; $tNav = @{ thin = 346; fat = 339; hulk = 394 }
$anchors = @{ none = @{ thin = -1; fat = -1; hulk = -1 }; bust = @{ thin = 264; fat = 278; hulk = 299 }; under = @{ thin = 287; fat = 321; hulk = 330 } }
foreach ($v in 'none', 'bust', 'under') {
  foreach ($k in 'thin', 'fat', 'hulk') { $tk = (Get-Culture).TextInfo.ToTitleCase($k) + '_Female'
    $bm = New-Object System.Drawing.Bitmap ($tmp + 'vbody512_' + $k + '.png'); $bot = -1; for ($y = 511; $y -ge 0; $y--) { if ($bm.GetPixel(256, $y).A -gt 40) { $bot = $y; break } }; $bm.Dispose()
    $sNav = $bot - $rise[$k]
    [Nav]::SetPink(($uw + 'boxers\boxers_' + $tk + '_south.png'), ($uw + 'panties\panties_' + $tk + '_south.png'), 512, 512)
    # vanilla anchor by relation: same share of top-to-crotch-apex as on WDI (the vanilla crotch apex is the vanilla navel row)
    $tb = New-Object System.Drawing.Bitmap ($wdi + 'Naked_' + $tk + '_south.png'); $tBot = -1; $tTopB = -1
    for ($y = 511; $y -ge 0; $y--) { if ($tb.GetPixel(256, $y).A -gt 40) { $tBot = $y; break } }
    for ($y = 0; $y -lt 512 -and $tTopB -lt 0; $y++) { for ($x = 0; $x -lt 512; $x += 2) { if ($tb.GetPixel($x, $y).A -gt 40) { $tTopB = $y; break } } }; $tb.Dispose()
    $sb = New-Object System.Drawing.Bitmap ($tmp + 'vbody512_' + $k + '.png'); $sTopB = -1
    for ($y = 0; $y -lt 512 -and $sTopB -lt 0; $y++) { for ($x = 0; $x -lt 512; $x += 2) { if ($sb.GetPixel($x, $y).A -gt 40) { $sTopB = $y; break } } }; $sb.Dispose()
    $tCr = $tBot - $triseW[$k]; $ta = $anchors[$v][$k]
    [Nav]::TAnchor = $ta; [Nav]::SAnchor = -1
    if ($ta -ge 0) { [Nav]::SAnchor = $sTopB + ($ta - $tTopB) / ($tCr - $tTopB) * ($sNav - $sTopB); "  vanilla $v row $([Math]::Round([Nav]::SAnchor)) (WDI $ta, WDI crotch apex $tCr)" }
    $r = [Nav]::Run(($tmp + 'vbody512_' + $k + '.png'), ($tmp + 'core512_' + $k + '.png'), ($wdi + 'Naked_' + $tk + '_south.png'), ($tmp + 'wshirt512_' + $tk + '.png'), $sNav, $tNav[$k], ($tmp + 'nav_' + $v + '_' + $tk + '.png'))
    "$v $tk : anchor $($anchors[$v][$k]); $r" } }
