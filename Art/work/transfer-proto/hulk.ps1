Add-Type -AssemblyName System.Drawing
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
function Hw($p, $rows) { $bm = New-Object System.Drawing.Bitmap $p; $o = @(); foreach ($y in $rows) { $l = -1; $r = -1; for ($x = 0; $x -lt 512; $x++) { if ($bm.GetPixel($x,$y).A -gt 40) { if ($l -lt 0) { $l = $x }; $r = $x } }; $o += ("{0}:{1}" -f $y, $(if ($l -ge 0) { [int](($r-$l)/2) } else { '-' })) }; $bm.Dispose(); return ($o -join ' ') }
"src body  rows 380-440: " + (Hw ($tmp + 'vbody512_hulk.png') (380,390,400,405,410,413,418,422,428,436,444))
"src shirt rows 380-440: " + (Hw ($tmp + 'imo512_hulk.png') (380,390,400,405,410,413,418,422,428,436,444))
"tgt body  rows 380-440: " + (Hw ($wdi + 'Naked_Hulk_south.png') (383,393,403,408,413,416,421,425,431,439,447))
"res r2    rows 380-440: " + (Hw ($tmp + 's3_Hulk.png') (383,393,403,408,413,416,421,425,431,439,447))
"res r1    rows 380-440: " + (Hw ($tmp + 's2_Hulk_off.png') (383,393,403,408,413,416,421,425,431,439,447))
