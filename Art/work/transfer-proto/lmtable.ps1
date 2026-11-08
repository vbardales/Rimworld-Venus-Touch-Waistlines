$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$names = 'neckL','neckR','shL','shR','armL','armR','waistL','waistR','hipL','hipR','crotch','top','bottom'
foreach ($k in 'male','thin','fat','hulk','female') { $info = ''; $v = [Lm]::Detect($tmp + "vbody512_$k.png", [ref]$info); "vanilla $k : $info" }
foreach ($k in 'Male','Thin','Fat','Hulk','Female','Thin_Female','Fat_Female','Hulk_Female') { $info = ''; $v = [Lm]::Detect($wdi + "Naked_${k}_south.png", [ref]$info); "WDI $k : $info" }
