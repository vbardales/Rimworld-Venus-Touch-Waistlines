param([string]$which = 'wdi')
$rowsLin = $false; $relBottom = $true; $sfx = $which
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
if ($which -eq 'wdi') {
  $pairsToRun = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'), @('thin','Thin_Female'), @('fat','Fat_Female'), @('hulk','Hulk_Female'))
  . ($d + 'step16.ps1')
} else {
  $pairsToRun = @(@('male','Male'), @('thin','Thin'), @('fat','Fat'), @('hulk','Hulk'), @('female','Female'))
  . ($d + 'step16bb.ps1')
}
