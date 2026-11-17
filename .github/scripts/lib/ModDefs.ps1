<#
.SYNOPSIS
  Dot-sourced library: which folders, files and defs of a mod the game loads for a given set of active mods.

.DESCRIPTION
  One reading of LoadFolders.xml and MayRequire, written once (docs/LOCAL-SCRIPTS-SHARING-STUDY.md, 2026-11-03: the same walk
  was hand-written in ForTheOccasion, HandMeDowns, MechanoidFactory, EdenGarden, Extinguish, InsectsHaveNoBones).
  Game rules, read in Assembly-CSharp 1.6 (Verse.ModLoadFolders, Verse.LoadFolder.ShouldLoad,
  ModContentPack.GetAllFilesForModPreserveOrder):

    - LoadFolders.xml: the <v1.6> list, else the highest <vX.Y> below 1.6, else <default>. No usable list (or no file):
      the mod root, then its 1.6 folder.
    - IfModActive="a, b"     loads when ANY of the ids is active
      IfModActiveAll="a, b"  loads when ALL of them are
      IfModNotActive="a, b"  does not load when ANY of them is active
      Ids compare case-insensitively, without a _steam or _copy suffix (ModLister.*NoSuffix).
    - Folders load in list order; a file whose path RELATIVE TO ITS LOAD FOLDER (Defs/X.xml, Languages/French/DefInjected/
      ThingDef/X.xml) exists in two loaded folders is taken from the LATER folder only: the earlier copy is not read at all.
    - MayRequire="a,b" on a def or list element: kept when ALL are active. MayRequireAnyOf="a,b": when ANY is.

    . (Join-Path $Protocols 'scripts\lib\ModDefs.ps1')
    Get-ModLoadFolders -ModDir ...\Mod                      # every entry, with its conditions; $null without LoadFolders.xml
    Get-ModDefFolders  -ModDir ...\Mod -ActiveMods @('nelim.animalark')   # loaded folders, load order (later wins)
    Get-ModDefFolders  -ModDir ...\Mod -All                 # every folder the file names, whatever the state
    @(Get-ModLoadStates -ModDir ...\Mod -ExtraIds $mayRequireIds)  # the distinct states worth checking (one object each)
    Get-ModFolderFiles -Folders $folders -SubPath 'Defs'    # files the game reads (.Files) and the copies it drops (.Shadowed)
    Test-MayRequire    -Node $defElement -ActiveMods $ids
    Get-MayRequireIds  -Node $xmlDoc                        # ids the MayRequire / MayRequireAnyOf of its defs name (-Descendants: li too)

  -ActiveMods lists the OPTIONAL mods that are active; Core is always active. An id the list does not name is inactive.
#>

function ConvertTo-ModId([string]$id) {
  $s = $id.Trim().ToLowerInvariant()
  foreach ($suffix in '_steam', '_copy') { if ($s.EndsWith($suffix)) { $s = $s.Substring(0, $s.Length - $suffix.Length) } }
  return $s
}
function Split-ModIds([string]$list) { if (-not $list) { return @() }; return @($list.Split(',') | Where-Object { $_.Trim() } | ForEach-Object { ConvertTo-ModId $_ }) }
function New-ModIdSet($ids) {
  $set = New-Object 'System.Collections.Generic.HashSet[string]'
  foreach ($i in @($ids)) { if ($i) { [void]$set.Add((ConvertTo-ModId $i)) } }
  [void]$set.Add('ludeon.rimworld')
  return ,$set
}

# Entries of the LoadFolders list the game picks for $Version, in file order: Rel ('' for the root), Path, AnyOf, AllOf, NoneOf.
# $null when the mod has no LoadFolders.xml or no usable list in it (the game then loads the root and the version folder).
function Get-ModLoadFolders {
  param([Parameter(Mandatory)][string]$ModDir, [string]$Version = '1.6')
  $file = Get-ChildItem -LiteralPath $ModDir -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ieq 'LoadFolders.xml' } | Select-Object -First 1
  if (-not $file) { return $null }
  $doc = New-Object System.Xml.XmlDocument
  $doc.Load($file.FullName)
  $lists = @{}
  foreach ($n in $doc.DocumentElement.ChildNodes) {
    if ($n.NodeType -ne 'Element') { continue }
    $name = $n.Name.ToLowerInvariant()
    if ($name -eq 'default') { $lists['default'] = $n; continue }
    if ($name.StartsWith('v')) { $v = $null; if ([version]::TryParse($name.Substring(1), [ref]$v)) { if (-not $lists.ContainsKey($name.Substring(1))) { $lists[$name.Substring(1)] = $n } } }
  }
  $pick = $null
  if ($lists.ContainsKey($Version)) { $pick = $lists[$Version] }
  else {
    $best = $lists.Keys | Where-Object { $_ -ne 'default' -and [version]$_ -le [version]$Version } | Sort-Object { [version]$_ } -Descending | Select-Object -First 1
    if ($best) { $pick = $lists[$best] } elseif ($lists.ContainsKey('default')) { $pick = $lists['default'] }
  }
  if (-not $pick) { return $null }
  $out = @()
  foreach ($li in $pick.ChildNodes) {
    if ($li.NodeType -ne 'Element') { continue }
    $t = $li.InnerText.Trim()
    $rel = if ($t -eq '/' -or $t -eq '\') { '' } else { $t.Replace('\', '/').Trim('/') }
    $out += [pscustomobject]@{
      Rel    = $rel
      Path   = $(if ($rel) { Join-Path $ModDir ($rel.Replace('/', '\')) } else { $ModDir })
      AnyOf  = @(Split-ModIds $li.GetAttribute('IfModActive'))
      AllOf  = @(Split-ModIds $li.GetAttribute('IfModActiveAll'))
      NoneOf = @(Split-ModIds $li.GetAttribute('IfModNotActive'))
    }
  }
  return ,$out
}

function Test-LoadFolderEntry($Entry, $Active) {
  if ($Entry.AnyOf.Count -and -not @($Entry.AnyOf | Where-Object { $Active.Contains($_) }).Count) { return $false }
  if ($Entry.AllOf.Count -and @($Entry.AllOf | Where-Object { -not $Active.Contains($_) }).Count) { return $false }
  if ($Entry.NoneOf.Count -and @($Entry.NoneOf | Where-Object { $Active.Contains($_) }).Count) { return $false }
  return $true
}

# Absolute folders the game loads for this mod, in load order (a later folder's file replaces an earlier one's).
# -All: every folder LoadFolders.xml names, whatever its condition (a union, not a game state).
function Get-ModDefFolders {
  param([Parameter(Mandatory)][string]$ModDir, [string[]]$ActiveMods = @(), [switch]$All, [string]$Version = '1.6')
  $entries = Get-ModLoadFolders -ModDir $ModDir -Version $Version
  if ($null -eq $entries) {
    $out = @($ModDir)
    $vdir = Join-Path $ModDir $Version
    if (Test-Path -LiteralPath $vdir -PathType Container) { $out += $vdir }
    return ,$out
  }
  $active = New-ModIdSet $ActiveMods
  $out = @()
  foreach ($e in $entries) { if (($All -or (Test-LoadFolderEntry $e $active)) -and $out -notcontains $e.Path) { $out += $e.Path } }
  return ,$out
}

# Every id a MayRequire / MayRequireAnyOf attribute names on the defs of a document (or on a def element itself), normalized:
# the ids that decide whether a def exists. -Descendants: list elements too (<li MayRequire=...>).
function Get-MayRequireIds($Node, [switch]$Descendants) {
  $ids = @()
  $xp = if ($Descendants) { 'descendant-or-self::*[@MayRequire or @MayRequireAnyOf]' } elseif ($Node -is [System.Xml.XmlDocument]) { '/*/*[@MayRequire or @MayRequireAnyOf]' } else { 'self::*[@MayRequire or @MayRequireAnyOf]' }
  foreach ($n in @($Node.SelectNodes($xp))) { $ids += Split-ModIds $n.GetAttribute('MayRequire'); $ids += Split-ModIds $n.GetAttribute('MayRequireAnyOf') }
  return @($ids | Sort-Object -Unique)
}

# A def (or list element) the game keeps for this active set. $ActiveMods: ids, or a set from New-ModIdSet.
function Test-MayRequire($Node, $ActiveMods) {
  $active = if ($ActiveMods -is [System.Collections.Generic.HashSet[string]]) { $ActiveMods } else { New-ModIdSet $ActiveMods }
  $all = @(Split-ModIds $Node.GetAttribute('MayRequire'))
  if (@($all | Where-Object { -not $active.Contains($_) }).Count) { return $false }
  $any = @(Split-ModIds $Node.GetAttribute('MayRequireAnyOf'))
  if ($any.Count -and -not @($any | Where-Object { $active.Contains($_) }).Count) { return $false }
  return $true
}

# The states worth checking: each is @{ Label = 'base' | '+id -id ...'; Active = string[] }, deduplicated on the folder set
# they load AND on the optional ids they hold (a MayRequire id changes the defs even when no folder changes).
# Optional ids = every id of the LoadFolders conditions plus -ExtraIds (the MayRequire ids of the mod's defs).
# Up to -MaxFull ids: every combination. More: nothing active, everything active, and each id alone on and alone off.
function Get-ModLoadStates {
  param([Parameter(Mandatory)][string]$ModDir, [string[]]$ExtraIds = @(), [int]$MaxFull = 6, [string]$Version = '1.6')
  $entries = Get-ModLoadFolders -ModDir $ModDir -Version $Version
  $ids = @()
  if ($entries) { foreach ($e in $entries) { $ids += $e.AnyOf + $e.AllOf + $e.NoneOf } }
  $ids = @(@($ids) + @($ExtraIds | ForEach-Object { ConvertTo-ModId $_ }) | Where-Object { $_ -and $_ -ne 'ludeon.rimworld' } | Sort-Object -Unique)
  $sets = @()
  if ($ids.Count -le $MaxFull) {
    for ($mask = 0; $mask -lt [math]::Pow(2, $ids.Count); $mask++) { $s = @(); for ($i = 0; $i -lt $ids.Count; $i++) { if ($mask -band (1 -shl $i)) { $s += $ids[$i] } }; $sets += ,$s }
  } else {
    $sets += ,@(); $sets += ,$ids
    foreach ($id in $ids) { $sets += ,@($id); $sets += ,@($ids | Where-Object { $_ -ne $id }) }
  }
  $seen = @{}; $out = @()
  foreach ($s in $sets) {
    $folders = (Get-ModDefFolders -ModDir $ModDir -ActiveMods $s -Version $Version) -join '|'
    $sig = $folders + '#' + (@($s | Where-Object { $ExtraIds -contains $_ } | Sort-Object) -join ',')
    if ($seen.ContainsKey($sig)) { continue }
    $seen[$sig] = 1
    # 'base' (no optional mod), '+a +b' (only those), 'all' or 'all -a' (every optional mod but those)
    $label = if ($s.Count -eq 0) { 'base' } elseif ($s.Count * 2 -gt $ids.Count -and $ids.Count -gt 1) { (@('all') + @($ids | Where-Object { $s -notcontains $_ } | ForEach-Object { "-$_" })) -join ' ' } else { (@($s) | ForEach-Object { "+$_" }) -join ' ' }
    $out += [pscustomobject]@{ Label = $label; Active = @($s) }
  }
  return $out   # one object per state: wrap the call in @()
}

# Files under <folder>\<SubPath> of each loaded folder, as the game reads them: one file per path relative to its load folder,
# taken from the LAST folder that holds it. .Files: Rel, Path, Folder. .Shadowed: Rel, Path (the dropped copy), Winner (the path kept).
function Get-ModFolderFiles {
  param([Parameter(Mandatory)][string[]]$Folders, [Parameter(Mandatory)][string]$SubPath, [string]$Filter = '*.xml')
  # ordinal, as the game's HashSet<string> of relative paths (LoadedLanguage.TryRegisterFileIfNew): case counts
  $byRel = New-Object System.Collections.Specialized.OrderedDictionary ([System.StringComparer]::Ordinal); $shadowed = @()
  foreach ($f in $Folders) {
    $dir = Join-Path $f $SubPath
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { continue }
    foreach ($file in Get-ChildItem -LiteralPath $dir -Recurse -File -Filter $Filter) {
      $rel = $SubPath.Replace('\', '/').Trim('/') + '/' + $file.FullName.Substring($dir.Length).TrimStart('\', '/').Replace('\', '/')
      if ($byRel.Contains($rel)) { $shadowed += [pscustomobject]@{ Rel = $rel; Path = $byRel[$rel].Path; Winner = $file.FullName } }
      $byRel[$rel] = [pscustomobject]@{ Rel = $rel; Path = $file.FullName; Folder = $f }
    }
  }
  return [pscustomobject]@{ Files = @($byRel.Values); Shadowed = $shadowed }
}
