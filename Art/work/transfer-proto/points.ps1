param([int]$stage = 1, [string]$facing = 'south')
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\'
. ($tmp + 'lib.ps1')
Add-Type -TypeDefinition $src -ReferencedAssemblies System.Drawing
Add-Type -AssemblyName System.Drawing
$wdi = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\Things\Pawn\Humanlike\Bodies\'
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-03_points\'
$rows = New-Object System.Collections.Generic.List[string]
if ($stage -eq 1) { $items = @('Male','Thin','Fat','Hulk','Female','Thin_Female','Fat_Female','Hulk_Female') | ForEach-Object { ,@("WDI $_", ($wdi + "Naked_${_}_south.png"), $null, "1-wdi-$_") } }
if ($stage -eq 2) { $items = @('male','thin','fat','hulk','female') | ForEach-Object { ,@("vanilla $_ + VAE CasualTShirt", ($tmp + "vbody512_$_.png"), ($tmp + "vae512_$_.png"), "2-vanilla-$_-garment") } }
if ($stage -eq 3) { $items = @('male','thin','fat','hulk','female') | ForEach-Object { ,@("vanilla $_ (no garment)", ($tmp + "vbody512_$_.png"), $null, "3-vanilla-$_") } }
if ($stage -eq 4) { $items = @("Thin_Female","Fat_Female","Hulk_Female") | ForEach-Object { ,@("WDI $_ + WDI ShirtBasic", ($wdi + "Naked_${_}_south.png"), ($tmp + "shirt512_$_.png"), "4-wdi-$_-garment") } }
[Gl]::Facing = $facing
if ($facing -ne 'south') {
  # side (east) and back (north): WDI bodies from WDI, vanilla bodies from the 1.7 decode (x4 nearest), names prefixed with the facing
  if ($stage -eq 1) { $items = @('Male','Thin','Fat','Hulk','Female','Thin_Female','Fat_Female','Hulk_Female') | ForEach-Object { ,@("WDI $_ ($facing)", ($wdi + "Naked_${_}_$facing.png"), $null, "$facing-1-wdi-$_") } }
  if ($stage -eq 3) { $items = @('Male','Thin','Fat','Hulk','Female') | ForEach-Object { ,@("vanilla $_ ($facing)", ($tmp + "core17_512\Naked_${_}_$facing.png"), $null, "$facing-3-vanilla-$_") } }
  if ($stage -eq 2 -or $stage -eq 4) { 'stages 2 and 4 are south only'; return }
}
foreach ($it in $items) {
  [Pts]::MaleBody = ($it[0] -match "WDI (Male|Thin|Fat|Hulk)$"); $P = [Pts]::Body($it[1])
  if ($it[2]) { foreach ($q in [Pts]::Garment($it[2], 15, $it[1])) { $P.Add($q) } }
  if ([Pts]::Kept) { "  " + $it[0] + " : outline rule exceptions: " + [Pts]::Kept }
  [Pts]::Draw($it[1], $it[2], $P, $it[0], ($out + $it[3] + '.png'))
  foreach ($p in $P) { $rows.Add(('{0}|{1}|{2}|{3}|{4}|{5}' -f $it[0], $p.Zone, $p.Name, $(if ($p.X -ge 0) { [Math]::Round($p.X) } else { '' }), $(if ($p.Y -ge 0) { [Math]::Round($p.Y) } else { '' }), $p.Status)) }
}
$rows | Set-Content -Encoding UTF8 ($out + $(if ($facing -ne 'south') { "$facing-" } else { '' }) + "stage$stage-table.txt")
"stage $stage : " + $items.Count + " pictures, " + $rows.Count + " rows"
