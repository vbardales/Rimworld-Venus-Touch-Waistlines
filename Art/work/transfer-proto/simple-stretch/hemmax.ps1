# Lowest row of the stretched shirt per body and facing, against the pubis row used (landmarks_used.json, written by simple.ps1).
# Usage: hemmax.ps1 -Bodies Male,Female -Suffix _pubcap
param([string[]]$Bodies = @('Male'), [string]$Suffix = '_pubcap')
Add-Type -AssemblyName System.Drawing
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\simple-stretch'
$bodies = @($Bodies | ForEach-Object { $_ -split ',' })
$lm = Get-Content "$d\landmarks_used.json" -Raw | ConvertFrom-Json
foreach ($b in $bodies) {
    foreach ($f in 'south', 'east', 'north') {
        $pubis = [int]$lm.pubis.$b.$f
        $bmp = New-Object System.Drawing.Bitmap "$d\${b}_${f}${Suffix}_step3.png"
        $maxRow = -1; $maxX = -1; $over = 0
        for ($x = 0; $x -lt 512; $x++) {
            $last = -1
            for ($y = 511; $y -ge 0; $y--) { if ($bmp.GetPixel($x, $y).A -ge 128) { $last = $y; break } }
            if ($last -gt $maxRow) { $maxRow = $last; $maxX = $x }
            if ($last -gt $pubis) { $over++ }
        }
        "$b $f$Suffix : lowest shirt row $maxRow at x=$maxX ; pubis row $pubis ; columns below: $over"
        $bmp.Dispose()
    }
}
