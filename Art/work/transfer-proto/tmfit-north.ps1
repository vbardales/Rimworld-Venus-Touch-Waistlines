# Vanilla to WDI, TailorMade's method (TexBake.BakeFitted, decompiled 2026-11-05) with Virginie's bands instead of its single
# vertical scale. Male, ShirtButton south, 512 px.
# - rows: piecewise-linear WDI row -> vanilla row through the band edges (collar, pecs, under the pecs, the vanilla trousers
#   waistband onto the WDI blue line, the shirt tail under it);
# - columns, per row: the BODY edges (not the garment's), averaged over 3 rows, vanilla body at the source row and WDI body at
#   the target row, one linear map across the row;
# - bilinear sample, alpha times the WDI body alpha, then TailorMade's outline: every pixel with alpha >= 0.1 within 4 px
#   (2 px at 256, square neighbourhood) of a transparent pixel becomes 15/15/18 and keeps its alpha;
# - split: the body of the shirt is cut on the pink line (hem drawn by the same outline), the tail below it is kept apart and
#   goes under the trousers (tucked) or over them (untucked), a per-garment setting later.
$d = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\transfer-proto\'
Add-Type -TypeDefinition (Get-Content ($d + 'nav.cs.txt') -Raw) -ReferencedAssemblies System.Drawing, System.Core
Add-Type -AssemblyName System.Drawing
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition (Get-Content ($d + 'tmfit.cs.txt') -Raw)
$film = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Tests\Pickle\Inbox\2026-11-03_vanilla-shaped-tops\screenshots\film\pickletools-texture-save--vanilla-shirtbutton-'
$vb = 'C:\Users\nelim\AppData\Local\Temp\claude\C--Users-nelim-Documents-rimworld-VenusTouchWaistlines\bee87564-3e6f-4779-92f2-04aa7a22cc7b\scratchpad\vbody512_'
$wb = 'C:\Program Files (x86)\Steam\steamapps\workshop\content\294100\3527486510\Textures\'
$tmp = 'C:\Users\nelim\AppData\Local\Temp\claude\215bed336962f00b\721abab5-386d-4049-bb90-c33b897be7b0\scratchpad\'
# Male, back view (north). Vanilla ShirtButton east from the 1.7 decode (core17, 128 px). Bands: top -> WDI top, vanilla trousers
# waistband (AB/XND north, 372 at the middle) -> WDI blue line (higher of the boxers/panties top at the body's middle column),
# tail under it x0.65. No chest anchor: the side 'chest front' point jumps along flat fronts (delta-east).
$tk = 'Male'; $f = 'east'; $cell = 400
$gar = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\core17\ShirtButton_Male_north.png'
$vbody = $vb + 'Male_north.png'; $body = $wb + 'Things\Pawn\Humanlike\Bodies\Naked_Male_north.png'
$bx = $wb + 'UWUnderwear\boxers\boxers_Male_north.png'; $pt = $wb + 'UWUnderwear\panties\panties_Male_north.png'
function Edge($p, $fromTop, $x) { [TmFit]::Edge($p, $fromTop, $x) }
$mid = [TmFit]::Mid($body)
$blue = [Math]::Min((Edge $bx $true $mid), (Edge $pt $true $mid)); $vt = Edge $vbody $true (-1); $wt = Edge $body $true (-1); $gb = Edge $gar $false (-1)
$bxReal = $bx; $wbv = 372; $pinkMid = [Math]::Max((Edge $bx $true $mid), (Edge $pt $true $mid))
# collar band as on the front (vanilla 247 -> top + 60); tail end counted from the pink line (Virginie 2026-11-05: untucked and
# tucked looked the same, the tail ended 6 px under the pink line)
$v = @($vt, 247, $wbv, $gb); $w = @($wt, ($wt + 60), $pinkMid, ($pinkMid + [int](0.65 * ($gb - $wbv))))  # waistband on the pink line, as on the front (2026-11-05, "c"); "mid $mid v=$($v -join ',') w=$($w -join ',')"
# trousers stand-in: the WDI body under the blue line (higher of the boxers/panties top, per column), in denim blue
$pants = $tmp + 'tmn_pants.png'; [TmFit]::Pants($body, $bx, $pt, $pants); $bx = $pants
"mid $mid v=$($v -join ',') w=$($w -join ',')"
[Nav]::SetPink($bxReal, $pt, 512, 512); [TmFit]::TailPink = [Nav]::Pink; [TmFit]::TailLen = 38; [TmFit]::Shift = [double[]]((Get-Content ($d + 'hemshift_Male_north.txt')) -split ';' | ForEach-Object { [double]::Parse($_, [cultureinfo]::InvariantCulture) })
$full = [TmFit]::Bake($gar, $vbody, $body, $v, $w)
[TmFit]::Save($full, 4, ($tmp + 'tmn_full.png')); [TmFit]::Save([TmFit]::Cut([TmFit]::Px($tmp + 'tmn_full.png'), [Nav]::Pink, $false), 0, ($tmp + 'tmn_main.png'))
$out = 'C:\Users\nelim\Documents\rimworld\VenusTouchWaistlines\Art\work\captures\2026-11-05_shirtbutton-tailormade-male-north.png'
$cols = @(@($vbody, $gar), @($body, $gar), @($body, ($tmp + 'tmn_full.png'), $bx, ($tmp + 'tmn_main.png')), @($body, $bx, ($tmp + 'tmn_full.png')))
$heads = 'vanilla', 'vanilla tel quel sur WDI', 'rentree (pan sous)', 'sortie (pan dessus)'
$bmp = New-Object System.Drawing.Bitmap (4 * $cell), ($cell + 20); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::FromArgb(255, 90, 110, 90))
$g.InterpolationMode = 'NearestNeighbor'; $g.PixelOffsetMode = 'Half'; $fo = New-Object System.Drawing.Font 'Arial', 10
for ($c = 0; $c -lt 4; $c++) { foreach ($p in $cols[$c]) { $im = New-Object System.Drawing.Bitmap $p; $g.DrawImage($im, $c * $cell, 20, $cell, $cell); $im.Dispose() }
  $g.DrawString($heads[$c], $fo, [System.Drawing.Brushes]::Yellow, $c * $cell + 6, 2) }
$g.Dispose(); $bmp.Save($out); $bmp.Dispose(); $out


