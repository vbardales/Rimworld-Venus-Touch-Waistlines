<#
.SYNOPSIS
  Shared texture check: every texture path a mod writes resolves to a shipped file, and no shipped texture is an orphan.

.DESCRIPTION
  Replaces the hand-written texture loops that about eleven mods kept in their own Tests/ scripts (ImperialFurnishings
  Check-Content, ColorfulCoats*Renew Check-Coats, ACertainSeriesCreaturesAndHairRenew, ASlothModRenew, AnimalArk,
  AdaptiveStorageNeolithicRenew ...). Study of 2026-11-03: docs/LOCAL-SCRIPTS-SHARING-STUDY.md.

  Content roots: Mod/ itself plus every folder up to three levels below it that holds Defs, Patches or Textures
  (LoadFolders, version and DLC folders: 1.6/, Odyssey/, NoOdyssey/ ...). The conditions of LoadFolders are not
  modelled: a texture shipped in any root of the mod counts as shipped, and the textures of all roots count as
  possibly referenced.

  References read (Defs and Patches, an element of a def, the <value> of a patch, or the text a patch writes
  straight into an xpath that ends on such an element):
    texPath, maskPath, uiIconPath, iconPath   graphic by class (read from the sibling <graphicClass>):
        Graphic_Single / Mote / Terrain / Fleck ...  <path>.png, exact file
        Graphic_Multi                                <path>_north, _east, _south  (west is mirrored from east). The game falls back
                                                      to another direction when one is missing: all missing or a PawnKindDef or apparel with
                                                      a partial set is an ERROR, a building or item with a partial set a WARN
        Graphic_Random / StackCount / Collection     a folder holding at least one image
        no class, class inherited or unknown          lenient: <path> or <path>_<anything> or a folder is enough.
                                                      Exception: a PawnKindDef (or an operation aiming at one) is Multi.
        uiIconPath, iconPath, maskPath                exact file
    wornGraphicPath, wornGraphicPaths/li  <path>_<direction>, plus the body type <path>_<Male|Female|Thin|Fat|Hulk>_<direction>
        unless the apparel's LAST layer (highest drawOrder: OnSkin 0, Middle 100, Shell 200, Belt 300, Overhead 400,
        EyeCover 500) is Overhead or EyeCover: those draw without body type (Belt, drawn as a pack when it is a utility layer, accepts either form). Layers read from the def,
        following ParentName inside the mod; layers not known (patch, parent in another mod) accept either form.
  A path is matched with exact case (RimWorld on Linux and macOS is case sensitive; Windows is not): a file that only
  matches ignoring case is an ERROR. Extensions png, jpg, jpeg, dds.

  Levels:
    ERROR  a path resolved against nothing although its folder is shipped by the mod (typo, missing direction,
           wrong case, empty random folder). Exit code 1.
    WARN   a path whose folder the mod does not ship at all: vanilla or another mod's texture, not verifiable
           without -AlsoScan; and every orphan (a shipped image no path, no other XML text, and no .cs string
           under Source/ refers to). No effect on the exit code.

  -AlsoScan  folders of other mods (their Textures folder, or the mod root: Textures, <version>/Textures are found).
             They only make a path resolve, never count for orphans.
  The orphan list prints 20 entries; -Full prints all.

    powershell -NoProfile -ExecutionPolicy Bypass -File scripts\Check-Textures.ps1 -ModRoot C:\Users\nelim\Documents\rimworld\MoaRenew
#>
param(
  [Parameter(Mandatory)][string]$ModRoot,
  [string[]]$AlsoScan = @(),
  [switch]$Full,
  [switch]$NoOrphans,
  [switch]$NoDependencies   # do not add the Workshop folders of the About.xml modDependencies to -AlsoScan (lib/Dependencies.ps1)
)
$ErrorActionPreference = 'Stop'
# Resolved, not joined as given: a root still carrying a `Tests\..` hop is longer than the paths measured into it, which
# cut the relative names short and reported every texture as an orphan in two mods (ColorfulCoats*Renew, 2026-09).
$ModRoot = (Resolve-Path -LiteralPath $ModRoot).Path.TrimEnd('\')
$mod = Join-Path $ModRoot 'Mod'
if (-not (Test-Path -LiteralPath $mod)) { throw "No Mod/ folder under $ModRoot" }
# Dependencies (2026-11-11, SerenBiotechExtended): like Check-DefRefs, the Workshop folders of the mods declared in About.xml modDependencies are
# scanned for textures too (lib/Dependencies.ps1); -NoDependencies turns that off.
. (Join-Path $PSScriptRoot 'lib\Dependencies.ps1')
if (-not $NoDependencies) { $AlsoScan = Add-DependencyRoots -Existing $AlsoScan -ModPath $mod -Quiet }

$errors = New-Object System.Collections.Generic.List[string]
$warns = New-Object System.Collections.Generic.List[string]
function Rel([string]$p) { if ($p.StartsWith($ModRoot)) { $p.Substring($ModRoot.Length + 1) } else { $p } }

# ---- files git ignores are not shipped (a diagnostic Defs file kept out of the repository, 2026-11-05, VenusTouchWaistlines): neither read nor counted
$ignored = New-Object System.Collections.Generic.HashSet[string] ([StringComparer]::OrdinalIgnoreCase)
$inGit = $false
try { $inGit = (& git -C $ModRoot rev-parse --is-inside-work-tree 2>$null) -eq 'true' } catch { }
if ($inGit) {
  # A git warning on stderr (a dangling ignored symlink, 2026-11-09, EdenGarden) is a NativeCommandError under Stop: run this call under Continue.
  $eap = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
  try { foreach ($rel in (& git -C $ModRoot -c core.quotePath=false ls-files -o -i --exclude-standard 2>$null)) { if ($rel) { [void]$ignored.Add((Join-Path $ModRoot ($rel -replace '/', '\'))) } } }
  finally { $ErrorActionPreference = $eap }
}

# ---- content roots
$roots = New-Object System.Collections.Generic.HashSet[string]
foreach ($d in Get-ChildItem -LiteralPath $mod -Directory -Recurse -Depth 3 -ErrorAction SilentlyContinue) {
  if ($d.Name -in 'Defs', 'Patches', 'Textures') { [void]$roots.Add($d.Parent.FullName) }
}
$imgExt = '.png', '.jpg', '.jpeg', '.dds'

function New-Index { return @{ Keys = (New-Object System.Collections.Generic.HashSet[string]); Lower = @{}; Prefixes = (New-Object System.Collections.Generic.HashSet[string]); Dirs = (New-Object System.Collections.Generic.HashSet[string]); LowerPrefixes = (New-Object System.Collections.Generic.HashSet[string]) } }
function Add-Key($ix, [string]$key) {
  [void]$ix.Keys.Add($key)
  $lk = $key.ToLowerInvariant()
  if (-not $ix.Lower.ContainsKey($lk)) { $ix.Lower[$lk] = $key }
  # every cut at '_' (direction, body type, mask, number suffixes) and at '/' (folders) is a prefix a path may name
  for ($i = $key.Length - 1; $i -gt 0; $i--) {
    $c = $key[$i]
    if ($c -eq '_' -or $c -eq '/') {
      $pre = $key.Substring(0, $i)
      [void]$ix.Prefixes.Add($pre); [void]$ix.LowerPrefixes.Add($pre.ToLowerInvariant())
      if ($c -eq '/') { [void]$ix.Dirs.Add($pre) }
    }
  }
}
function Add-TextureDir($ix, [string]$dir) {
  $n = 0
  foreach ($f in Get-ChildItem -LiteralPath $dir -Recurse -File -ErrorAction SilentlyContinue) {
    if ($imgExt -notcontains $f.Extension.ToLowerInvariant()) { continue }
    if ($ignored.Contains($f.FullName)) { continue }
    $rel = $f.FullName.Substring($dir.Length + 1).Replace('\', '/')
    $key = $rel.Substring(0, $rel.Length - $f.Extension.Length)
    Add-Key $ix $key
    $n++
    if ($ix.Own) { $ix.Files[$key] = $f.FullName }
  }
  return $n
}

$own = New-Index; $own.Own = $true; $own.Files = [hashtable]::new()
$all = New-Index
$xmlFiles = New-Object System.Collections.Generic.List[string]
$texCount = 0  # set below from the unique keys
foreach ($r in $roots) {
  $t = Join-Path $r 'Textures'
  if (Test-Path -LiteralPath $t) { [void](Add-TextureDir $own $t); [void](Add-TextureDir $all $t) }
  foreach ($sub in 'Defs', 'Patches') {
    $p = Join-Path $r $sub
    if (Test-Path -LiteralPath $p) { foreach ($f in Get-ChildItem -LiteralPath $p -Recurse -Filter *.xml -File) { if (-not $ignored.Contains($f.FullName)) { $xmlFiles.Add($f.FullName) } } }
  }
}
foreach ($a in $AlsoScan) {
  if (-not (Test-Path -LiteralPath $a)) { $warns.Add("-AlsoScan folder not found: $a"); continue }
  $a = (Resolve-Path -LiteralPath $a).Path
  $dirs = @()
  if ((Split-Path $a -Leaf) -eq 'Textures') { $dirs = @($a) }
  else { $dirs = @(Get-ChildItem -LiteralPath $a -Directory -Recurse -Depth 2 -Filter Textures -ErrorAction SilentlyContinue | ForEach-Object FullName) }
  foreach ($d in $dirs) { [void](Add-TextureDir $all $d) }
}

$texCount = $own.Keys.Count
# ---- def inheritance map (own defs only) for apparel layers
$namedDefs = [hashtable]::new()
$docs = @{}
foreach ($f in $xmlFiles) {
  $doc = New-Object System.Xml.XmlDocument
  try { $doc.Load($f) } catch { $errors.Add("Malformed XML: $(Rel $f): $($_.Exception.InnerException.Message)"); continue }
  $docs[$f] = $doc
  if ($doc.DocumentElement.LocalName -eq 'Defs') {
    foreach ($d in $doc.DocumentElement.ChildNodes) {
      if ($d.NodeType -eq 'Element' -and $d.HasAttribute('Name')) { $namedDefs[$d.GetAttribute('Name')] = $d }
    }
  }
}

$layerOrder = @{ OnSkin = 0; Middle = 100; Shell = 200; Belt = 300; Overhead = 400; EyeCover = 500 }
function Get-LastLayer($def) {
  # returns the name of the highest known layer, '' when the def lists none, '?' when layers are unknown (inherited from outside)
  $guard = 0
  while ($def -and $guard -lt 10) {
    $lis = @($def.SelectNodes('apparel/layers/li'))
    if ($lis.Count) {
      $best = ''; $bo = -1
      foreach ($l in $lis) { $n = $l.InnerText.Trim(); if ($layerOrder.ContainsKey($n) -and $layerOrder[$n] -gt $bo) { $bo = $layerOrder[$n]; $best = $n } }
      if ($best) { return $best } else { return '?' }
    }
    if ($def.HasAttribute('ParentName')) {
      $pn = $def.GetAttribute('ParentName')
      if ($namedDefs.ContainsKey($pn)) { $def = $namedDefs[$pn]; $guard++; continue }
    }
    return '?'
  }
  return '?'
}

# ---- reference extraction
$graphicNames = @{ texPath = 'graphic'; maskPath = 'file'; uiIconPath = 'file'; iconPath = 'file'; wornGraphicPath = 'worn' }
$singleClasses = 'Graphic_Single', 'Graphic_Mote', 'Graphic_MoteWithAgeSecs', 'Graphic_Terrain', 'Graphic_Fleck', 'Graphic_FleckSplash'
$multiClasses = 'Graphic_Multi'
$folderClasses = 'Graphic_Random', 'Graphic_StackCount', 'Graphic_Collection', 'Graphic_Cluster'

function Get-DefContext($el) {
  # nearest top-level def (parent is the Defs element), or the first Defs/<Type> of the nearest xpath above the element
  $a = $el
  $xpathType = $null
  while ($a -and $a.NodeType -eq 'Element') {
    if ($a.ParentNode -and $a.ParentNode.NodeType -eq 'Element' -and $a.ParentNode.LocalName -eq 'Defs') { return @{ Def = $a; Type = $a.LocalName } }
    if (-not $xpathType) {
      $xp = $a.SelectSingleNode('xpath')
      if ($xp -and $xp.InnerText -match 'Defs/(\w+)') { $xpathType = $Matches[1] }
    }
    $a = $a.ParentNode
  }
  return @{ Def = $null; Type = $xpathType }
}

$refs = New-Object System.Collections.Generic.List[object]
$allText = New-Object System.Collections.Generic.HashSet[string]   # every leaf text, for the "referenced by something" fallback
function Add-Ref([string]$path, [string]$name, $el, [string]$file, [string]$cls, [string]$typeHint, $def) {
  $path = $path.Trim()
  if (-not $path -or $path -match '^(BaseContent/|\s)' -or $path -match '[{}<>]') { return }
  $kind = 'lenient'
  if ($name -eq 'wornGraphicPath') { $kind = 'worn' }
  elseif ($name -in 'uiIconPath', 'iconPath', 'maskPath') { $kind = 'single' }
  elseif ($singleClasses -contains $cls) { $kind = 'single' }
  elseif ($multiClasses -contains $cls) { $kind = 'multi' }
  elseif ($folderClasses -contains $cls) { $kind = 'folder' }
  elseif (-not $cls -and $el -and $el.ParentNode.LocalName -match "essicated") { $kind = "lenient" }   # drawn as a single file or as directions: not settled without the game
  elseif (-not $cls -and $typeHint -eq 'PawnKindDef') { $kind = 'multi' }
  $last = ''
  if ($kind -eq 'worn') { $last = if ($def) { Get-LastLayer $def } else { '?' } }
  $defName = if ($def -and $def.SelectSingleNode('defName')) { $def.SelectSingleNode('defName').InnerText.Trim() } elseif ($typeHint) { "patch on $typeHint" } else { 'patch' }
  $refs.Add([pscustomobject]@{ Path = $path; Element = $name; Kind = $kind; Class = $cls; Last = $last; File = $file; Def = $defName; Type = $typeHint; Parent = $(if ($el -and $el.ParentNode) { $el.ParentNode.LocalName } else { '' }) })
}

foreach ($f in $docs.Keys) {
  $doc = $docs[$f]
  foreach ($el in $doc.GetElementsByTagName('*')) {
    if ($el.SelectSingleNode('*')) { continue }  # leaf elements only
    $txt = $el.InnerText.Trim()
    $nm = $el.LocalName
    $isWornLi = ($nm -eq 'li' -and $el.ParentNode -and $el.ParentNode.LocalName -eq 'wornGraphicPaths')
    if (-not $graphicNames.ContainsKey($nm) -and -not $isWornLi) {
      # any other text may still name a shipped texture (a custom field, a mod extension): keep it for the orphan check only
      if ($txt -and $txt.Length -le 240 -and $txt -notmatch '\s') { [void]$allText.Add($txt) }
      continue
    }
    $ctx = Get-DefContext $el
    $cls = ''
    $gc = $el.ParentNode.SelectSingleNode('graphicClass')
    if ($gc) { $cls = $gc.InnerText.Trim() }
    $effective = if ($isWornLi) { 'wornGraphicPath' } else { $nm }
    Add-Ref $txt $effective $el $f $cls $ctx.Type $ctx.Def
  }
  # an operation that writes the text straight into an xpath ending on a path element: <xpath>.../texPath</xpath><value>Things/X</value>
  foreach ($op in $doc.SelectNodes('//Operation[xpath and value and not(value/*)]|//li[xpath and value and not(value/*)]')) {
    $xp = $op.SelectSingleNode('xpath').InnerText.Trim()
    if ($xp -match '/(texPath|uiIconPath|iconPath|wornGraphicPath|maskPath)\s*(\[[^\]]*\])?\s*$') {
      $en = $Matches[1]
      $t = if ($xp -match 'Defs/(\w+)') { $Matches[1] } else { '' }
      $cls = ''
      if ($en -eq 'texPath' -and $xp -match '(Graphic_\w+)') { $cls = $Matches[1] }
      Add-Ref $op.SelectSingleNode('value').InnerText $en $op $f $cls $t $null
    }
  }
}

# ---- resolve
$dirs4 = 'north', 'east', 'south'
$bodies = 'Male', 'Female', 'Thin', 'Fat', 'Hulk'
function Test-Exact([string]$key) { return $all.Keys.Contains($key) }
function Get-CaseHit([string]$key) { $lk = $key.ToLowerInvariant(); if ($all.Lower.ContainsKey($lk)) { return $all.Lower[$lk] } return $null }
function Get-Missing($r) {
  # list of missing keys (empty = resolved)
  $p = $r.Path
  switch ($r.Kind) {
    'single' { if (Test-Exact $p) { return @() } else { return @($p) } }
    'multi'  {
      if (-not $r.Class -and (Test-Exact $p)) { return @() }   # class inherited from a parent def: a single file is a valid Graphic_Single
      return @($dirs4 | ForEach-Object { "${p}_$_" } | Where-Object { -not (Test-Exact $_) })
    }
    'folder' { if ($all.Dirs.Contains($p)) { return @() } else { return @("$p/ (folder with images)") } }
    'worn' {
      $bodyless = @($dirs4 | ForEach-Object { "${p}_$_" } | Where-Object { -not (Test-Exact $_) })
      $withBody = @(foreach ($b in $bodies) { foreach ($d in $dirs4) { "${p}_${b}_$d" } }) | Where-Object { -not (Test-Exact $_) }
      if ($r.Last -in 'Overhead', 'EyeCover') { return $bodyless }
      if ($r.Last -in 'Belt', '?') { if ($bodyless.Count -eq 0 -or @($withBody).Count -eq 0) { return @() } else { return @($withBody) } }
      return @($withBody)
    }
    default { if ((Test-Exact $p) -or $all.Prefixes.Contains($p)) { return @() } else { return @($p) } }
  }
}

$seenRef = [hashtable]::new()  # case sensitive, unlike @{}
$checked = 0
foreach ($r in $refs) {
  $sig = "$($r.Kind)|$($r.Last)|$($r.Path)"
  if ($seenRef.ContainsKey($sig)) { continue }
  $seenRef[$sig] = $true
  $checked++
  $miss = @(Get-Missing $r)
  if ($miss.Count -eq 0) { continue }
  # case-only mismatch?
  $caseNote = @(); $fileForFolder = $false
  foreach ($m in $miss) {
    $k = $m -replace ' \(folder with images\)$', '' -replace '/$', ''
    $hit = Get-CaseHit $k
    if ($hit -and $hit -ceq $k) { $fileForFolder = $true }   # a file of that exact name where a folder is wanted
    elseif ($hit) { $caseNote += "$k exists as $hit" }
    elseif ($r.Kind -in 'folder', 'lenient') { $lp = $k.ToLowerInvariant(); if ($all.LowerPrefixes.Contains($lp)) { $caseNote += "$k exists with other case" } }
  }
  $parent = if ($r.Path.Contains('/')) { $r.Path.Substring(0, $r.Path.LastIndexOf('/')) } else { '' }
  $parentShipped = ($parent -eq '') -or $own.Dirs.Contains($parent)
  # a sibling file must share the start of the name (4 characters): a shipped folder can sit beside a vanilla path (Things/Building/Door)
  if ($parentShipped -and $parent -and $r.Kind -ne 'folder') {
    $leaf = $r.Path.Substring($parent.Length + 1).ToLowerInvariant(); $near = $false
    foreach ($k2 in $own.Keys) { if ($k2.StartsWith($parent + '/') -and $k2.IndexOf('/', $parent.Length + 1) -lt 0) { $s = $k2.Substring($parent.Length + 1).ToLowerInvariant(); $n = [Math]::Min($s.Length, $leaf.Length); $i = 0; while ($i -lt $n -and $s[$i] -eq $leaf[$i]) { $i++ }; if ($i -ge 4) { $near = $true; break } } }
    if (-not $near) { $parentShipped = $false }
  }
  $shown = ($miss | Select-Object -First 6) -join ', '
  if ($miss.Count -gt 6) { $shown += ", ... (+$($miss.Count - 6))" }
  $where = "$(Rel $r.File) [$($r.Def)]"
  $cls = if ($r.Class) { $r.Class } else { $r.Kind }
  # Graphic_Multi falls back to another direction when one is missing and only logs when all are: a partial set is an ERROR
  # for pawns (the animal or apparel is drawn wrong) and for apparel, a WARN elsewhere (buildings and items shipping two directions).
  $anyDir = $false
  if ($r.Kind -eq 'multi') { foreach ($d in 'north', 'east', 'south', 'west') { if (Test-Exact "$($r.Path)_$d") { $anyDir = $true } } }
  $strict = ($r.Type -eq 'PawnKindDef' -and $r.Parent -notmatch "essicated")
  $nonBody = ($r.Kind -eq 'worn' -and $r.Last -notin 'Overhead', 'EyeCover' -and $all.Prefixes.Contains($r.Path) -and -not (@($bodies | Where-Object { $all.Keys.Contains("$($r.Path)_${_}_south") }).Count))
  if ($caseNote.Count) { $errors.Add("ERROR: wrong case: $where $($r.Element) '$($r.Path)' ($cls): $($caseNote -join '; ')") }
  elseif ($r.Kind -eq 'multi' -and $anyDir -and -not $strict) { $warns.Add("WARN: partial directions (the game falls back to another one): $where $($r.Element) '$($r.Path)' ($cls): missing $shown") }
  elseif ($nonBody) { $warns.Add("WARN: worn texture suffix is not a body type (animal apparel of another mod?): $where $($r.Element) '$($r.Path)' ($cls): wanted $shown") }
  elseif ($fileForFolder) { $warns.Add("WARN: $where $($r.Element) '$($r.Path)' ($cls) is a file where a folder is expected; works only if the game accepts a single file for that class") }
  elseif ($r.Path -ceq 'Blank') { $warns.Add("WARN: texture 'Blank' is the game's own, not verifiable here: $where $($r.Element) ($cls)") }
  elseif ($parentShipped) { $errors.Add("ERROR: missing texture: $where $($r.Element) '$($r.Path)' ($cls): $shown") }
  else { $warns.Add("WARN: texture outside Mod/Textures (vanilla or another mod?): $where $($r.Element) '$($r.Path)' ($cls); pass -AlsoScan to verify") }
}

# ---- orphans
$orphans = New-Object System.Collections.Generic.List[string]
if (-not $NoOrphans) {
  $exact = New-Object System.Collections.Generic.HashSet[string]
  $folderClaims = New-Object System.Collections.Generic.HashSet[string]
  $lenient = New-Object System.Collections.Generic.HashSet[string]
  foreach ($r in $refs) {
    $p = $r.Path
    switch ($r.Kind) {
      'single' { [void]$exact.Add($p) }
      'multi'  { foreach ($d in 'north', 'east', 'south', 'west') { [void]$exact.Add("${p}_$d"); [void]$exact.Add("${p}Pack_$d") } }   # a pack animal draws its pack from <texPath>Pack
      'folder' { [void]$folderClaims.Add($p) }
      'worn'   {
        foreach ($d in 'north', 'east', 'south', 'west') { [void]$exact.Add("${p}_$d") }
        foreach ($b in $bodies + 'Baby' + 'Child') { foreach ($d in 'north', 'east', 'south', 'west') { [void]$exact.Add("${p}_${b}_$d") } }
        [void]$lenient.Add($p)   # animal apparel of other mods suffixes the race, not the body type
      }
      default  { [void]$lenient.Add($p) }
    }
  }
  # any other XML text equal to a shipped path or to a prefix of one counts as a reference; so does a string in Source/*.cs
  foreach ($t in $allText) { if ($own.Keys.Contains($t) -or $own.Prefixes.Contains($t)) { [void]$lenient.Add($t) } }
  foreach ($srcName in 'Source', 'src', 'Src') {
    $sd = Join-Path $ModRoot $srcName
    if (Test-Path -LiteralPath $sd) {
      foreach ($cs in Get-ChildItem -LiteralPath $sd -Recurse -Filter *.cs -File -ErrorAction SilentlyContinue) {
        foreach ($m in [regex]::Matches([IO.File]::ReadAllText($cs.FullName), '"([^"\\\r\n]{2,200})"')) {
          $s = $m.Groups[1].Value
          if ($own.Keys.Contains($s) -or $own.Prefixes.Contains($s)) { [void]$lenient.Add($s) }
        }
      }
    }
  }
  function Test-Claimed([string]$key) {
    if ($exact.Contains($key) -or $lenient.Contains($key)) { return $true }
    # cut at '/' : folder claims (Random, StackCount) and lenient directories
    # cut at '_' : lenient prefixes (direction, number, atlas suffixes of a path of unknown class), and the _m mask of a claimed file
    for ($i = $key.Length - 1; $i -gt 0; $i--) {
      $c = $key[$i]
      if ($c -eq '/') { $pre = $key.Substring(0, $i); if ($folderClaims.Contains($pre) -or $lenient.Contains($pre)) { return $true } }
      elseif ($c -eq '_') { $pre = $key.Substring(0, $i); if ($lenient.Contains($pre)) { return $true } }
    }
    if ($key.EndsWith('_m') -or $key.EndsWith('_Mask')) { $base = $key.Substring(0, $key.LastIndexOf('_')); if ($exact.Contains($base)) { return $true } }
    return $false
  }
  foreach ($k in ($own.Keys | Sort-Object)) {
    if (-not (Test-Claimed $k)) { $orphans.Add($own.Files[$k].Substring($ModRoot.Length + 1)) }
  }
  if ($orphans.Count) {
    $show = if ($Full) { $orphans } else { @($orphans | Select-Object -First 20) }
    $warns.Add("WARN: $($orphans.Count) orphan texture(s), shipped and referenced by nothing: " + ($show -join '; ') + $(if (-not $Full -and $orphans.Count -gt 20) { "; ... (+$($orphans.Count - 20), -Full lists all)" } else { '' }))
  }
}

foreach ($w in $warns) { Write-Host $(if ($w.StartsWith('WARN')) { $w } else { "WARN: $w" }) -ForegroundColor Yellow }
foreach ($e in $errors) { Write-Host $(if ($e.StartsWith('ERROR')) { $e } else { "ERROR: $e" }) -ForegroundColor Red }
$nOrph = $orphans.Count
$nWarn = $warns.Count - $(if ($nOrph) { 1 } else { 0 })
if ($errors.Count) { Write-Host "FAIL: $($errors.Count) error(s), $nWarn warning(s), $nOrph orphan(s); $checked path(s), $texCount texture(s)" -ForegroundColor Red; exit 1 }
Write-Host "PASS: 0 error(s), $nWarn warning(s), $nOrph orphan(s); $checked path(s), $texCount texture(s)."
exit 0
