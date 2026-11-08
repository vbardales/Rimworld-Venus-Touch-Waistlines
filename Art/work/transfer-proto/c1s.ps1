$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$pairs = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'), @('thin','Thin_Female'), @('fat','Fat_Female'), @('hulk','Hulk_Female'))
if (-not $rounds) { $rounds = @(@('round 1', 's2_{0}_off.png'), @('round 2', 's3_{0}.png')) }
foreach ($pr in $pairs) { $sk = $pr[0]; $tk = $pr[1]; "== $sk -> $tk"
  foreach ($rd in $rounds) { "  " + [C1s]::Run(($tmp + "vbody512_$sk.png"), ($tmp + "imo512_$sk.png"), ($wdi + "Naked_${tk}_south.png"), ($tmp + ($rd[1] -f $tk)), $rd[0], 24) } }
