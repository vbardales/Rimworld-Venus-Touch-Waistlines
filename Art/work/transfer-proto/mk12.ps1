$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
$t = Get-Content ($d + 'step11.ps1') -Raw
$a = 'Add-Type -AssemblyName System.Drawing'
$t = $t.Replace($a, $a + "`r`nAdd-Type -TypeDefinition (Get-Content '" + $d + "r7.cs.txt' -Raw)")
$anchor = '  $px = $out[0]; $removed = 0;'
if (-not $t.Contains($anchor)) { throw 'anchor' }
$reb = '  $info7 = ''''; $wo7 = [int][Math]::Max(6, $oo); $rb = [R7]::Rebuild($px1, 512, $wo7, 60, [ref]$info7); $out[0] = $rb; "  [round 7 rebuild] outline stroke width $wo7 px (source outline), $info7"' + "`r`n"
$t = $t.Replace($anchor, $reb + $anchor)
$i = $t.IndexOf('  $ws = [S3]::Widths($srcGar[0]')
if ($i -lt 0) { throw 'ws' }
$c5 = @'
  # C5 rebased by Audit 2026-11-03 (one-sided): result garment area / target outline area (body + profile) over the rows where the result has garment, against the source ratio minus 5 %, no upper limit
  $sgA = 0; $sbA = 0
  for ($y = 0; $y -lt 512; $y++) { $hasG = $false; for ($x = 0; $x -lt 512; $x++) { if ($srcGar[0][($y*512+$x)*4+3] -gt 40) { $hasG = $true; break } }; if (-not $hasG) { continue }; for ($x = 0; $x -lt 512; $x++) { if ($srcGar[0][($y*512+$x)*4+3] -gt 40) { $sgA++ }; if ($sB[0][($y*512+$x)*4+3] -gt 40) { $sbA++ } } }
  $rgA = 0; $toA = 0
  for ($y = 0; $y -lt 512; $y++) { $hasG = $false; for ($x = 0; $x -lt 512; $x++) { if ($out[0][($y*512+$x)*4+3] -gt 40) { $rgA++; $hasG = $true } }; if (-not $hasG) { continue }; $bl = -1; $br = -1; for ($x = 0; $x -lt 512; $x++) { if ($tb6[0][($y*512+$x)*4+3] -gt 40) { if ($bl -lt 0) { $bl = $x }; $br = $x } }; if ($bl -lt 0) { continue }; if ($wL) { $eL = $wL[$y]; $eR = $wR[$y] } else { $eL = $tightOff; $eR = $tightOff }; $toA += ($br + $eR) - ($bl - $eL) + 1 }
  $sr = $sgA / [Math]::Max(1, $sbA); $rr = $rgA / [Math]::Max(1, $toA)
  "    C5 REBASED (Audit 2026-11-03): result garment / target outline area $([Math]::Round($rr,3)), source ratio (garment / body, rows with garment) $([Math]::Round($sr,3)), required >= $([Math]::Round($sr*0.95,3)) -> $(if ($rr -ge $sr * 0.95) { 'PASS' } else { 'FAIL' })"
'@
$t = $t.Insert($i, $c5 + "`r`n")
$t = $t.Replace('s10${sfx}_${tk}.png', 's12${sfx}_${tk}.png').Replace('s10u${sfx}_${tk}.png', 's12u${sfx}_${tk}.png')
Set-Content ($d + 'step12.ps1') $t -Encoding UTF8
'ok'
