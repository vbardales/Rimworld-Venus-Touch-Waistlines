<#
.SYNOPSIS
  Completeness and consistency check of a mod's translation (DefInjected and Keyed), shared by every mod.

.DESCRIPTION
  Shared replacement for the per-mod Test-Translations.ps1 / Check-Translations.ps1 / Check-Localization.ps1 /
  Test-Localization.ps1 (owner rule of 2026-10-11, AGENTS.md "Local scripts"). Base: EdenGarden's Test-Translations.ps1.

  It answers a question Check-DefInjected.ps1 does not: Check-DefInjected proves that every DefInjected key RESOLVES;
  this script proves that every text the mod ships HAS a translation, and that nothing stale is left behind.

  Checks, all reported before the exit code (0 = clean, 1 = at least one finding):
    1. Inventory: every label, description, jobString (and the other text fields below) of every def in Mod/Defs and
       Mod/Patches, plus the label and description of each stage under <stages>, plus the text a PatchOperationReplace
       sets. A text field the inventory does not know ("new text path needs inventory support") is an error: extend
       -ExtraFields or report it, never ignore it.
    2. Coverage: each inventoried text has a DefInjected entry in Languages/<Language>/DefInjected/<DefType>/.
    3. No stale entry: a DefInjected entry whose key matches no inventoried text is reported.
    4. Duplicates: the same key twice in the translation (or twice in the inventory).
    5. Empty, TODO or (with -RejectCjk) CJK text in a translation entry.
    1b. A def that has no text field of its own inherits it from its ParentName chain (an abstract def with Name="..."): the
       inherited text is inventoried for that def too, because the game takes the translation by the child defName.
    6. Formatting tokens ({0}, <b>, \n ...) are identical in source and translation, for DefInjected and Keyed.
    7. Keyed: every "Mod.Key" or "Mod_Key".Translate() used in Source/**/*.cs exists in the source language AND the translation;
       with Source/ present, an entry used nowhere is reported (turn off with -AllowUnusedKeyed). -DependencyKeyed lists the keys
       of a dependency mod that this mod only translates (no source-language entry, no call here): neither reported.
    8. With -RejectIdentical: a translation identical to its source text (HairDef and -AllowIdentical keys excepted).

  What it does not do: resolve keys against the game's classes (Check-DefInjected.ps1 does), compare wording, or
  check handles of list elements other than <stages>. Run both.

    powershell -File scripts\Check-Translations.ps1 -ModRoot C:\Users\nelim\Documents\rimworld\EdenGarden
    powershell -File scripts\Check-Translations.ps1 -ModRoot ...\SomeMod -Language French -SourceLanguage English -RejectCjk
#>
param(
  [Parameter(Mandatory)][string]$ModRoot,
  [string]$Language = 'French',
  [string]$SourceLanguage = 'English',
  # Def fields that carry player-visible text, on top of the built-in list.
  [string[]]$ExtraFields = @(),
  [switch]$RejectCjk,
  [switch]$AllowUnusedKeyed,
  # Keyed entries kept on purpose without a call in the code (compatibility keys), each with its reason in the mod's docs.
  [string[]]$AllowUnused = @(),
  # Keyed entries that translate a DEPENDENCY's keys (the English text and the code are in that mod, this mod only ships the
  # translation): not required in the source language, never reported unused.
  [string[]]$DependencyKeyed = @(),
  # Make the warnings errors: an injection outside the inventory, a stage with no usable label handle.
  [switch]$Strict,
  # A translation identical to the source text is a finding (a text left untranslated), except HairDef and the keys of -AllowIdentical
  # (proper nouns, units, names that stay the same in the language). Off by default: many mods keep some texts on purpose.
  [switch]$RejectIdentical,
  [string[]]$AllowIdentical = @(),
  # Skip the Keyed part (a mod with no code).
  [switch]$NoKeyed,
  # A JSON file holding the SHA-256 of every inventoried source text. A source text edited (or added) after the baseline fails
  # until the translation is reviewed and the baseline refreshed with -UpdateBaseline.
  [string]$Baseline,
  [switch]$UpdateBaseline
)
$ErrorActionPreference = 'Stop'
$ModRoot = (Resolve-Path $ModRoot).Path
$modDir = if (Test-Path (Join-Path $ModRoot 'Mod\Defs')) { Join-Path $ModRoot 'Mod' } else { $ModRoot }
$findings = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
function Find($msg) { if (-not $findings.Contains($msg)) { $findings.Add($msg) } }
function Warn($msg) { if (-not $warnings.Contains($msg)) { $warnings.Add($msg) } }

$cjk = '[\p{IsCJKUnifiedIdeographs}]'
$topFields = @('label', 'description', 'jobString', 'labelNoun', 'labelMale', 'labelFemale', 'labelPlural', 'pawnLabel', 'gerundLabel', 'ingestible/ingestCommandString', 'ingestible/ingestReportString') + $ExtraFields
$known = @('label', 'description', 'jobString', 'labelShort', 'reportString', 'customLabel', 'ingestCommandString', 'ingestReportString') + $ExtraFields

# --- inventory --------------------------------------------------------------
$inventory = @{}
$nested = @{}
function Add-Text($type, $key, $value) {
  $id = "$type/$key"
  if ([string]::IsNullOrWhiteSpace($value)) { Find "Missing source text: $id"; return }
  if ($RejectCjk -and $value -match $cjk) { Find "CJK in the source text: $id"; return }
  if ($inventory.ContainsKey($id)) { Find "Duplicate inventoried field: $id"; return }
  $inventory[$id] = $value
}
$sources = @()
# every Defs/ and Patches/ folder under Mod/, loadFolders subfolders included (Mod/Integrations/<X>/Patches, ...)
foreach ($d in Get-ChildItem $modDir -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -in 'Defs', 'Patches' -and $_.FullName -notmatch '[\\/](Languages|\.claude)[\\/]' }) { $sources += Get-ChildItem $d.FullName -Recurse -Filter *.xml -File }
# every def carrying Name="..." (abstract bases included), to walk a ParentName chain
$byName = @{}
$parsed = New-Object System.Collections.Generic.List[object]
foreach ($file in $sources) {
  $doc = New-Object System.Xml.XmlDocument
  try { $doc.Load($file.FullName) } catch { Find "Malformed XML: $($file.FullName)"; continue }
  $parsed.Add($doc)
  foreach ($n in $doc.SelectNodes('//*[@Name]')) { if (-not $byName.ContainsKey($n.GetAttribute('Name'))) { $byName[$n.GetAttribute('Name')] = $n } }
}
# first node of a text field found on the def's ParentName chain (cycle guard: 20 levels)
function Get-InheritedField($def, $f) {
  $p = $def.GetAttribute('ParentName')
  for ($i = 0; $p -and $i -lt 20; $i++) {
    $parent = $byName[$p]
    if (-not $parent) { return $null }
    $node = $parent.SelectSingleNode($f)
    if ($node) { return $node }
    $p = $parent.GetAttribute('ParentName')
  }
  return $null
}
foreach ($doc in $parsed) {
  foreach ($def in $doc.SelectNodes('//*[defName]')) {
    $own = @()
    foreach ($f in $topFields) { foreach ($node in $def.SelectNodes($f)) { $p = if ($f -like '*/*') { $f -replace '/', '.' } else { $node.LocalName }; Add-Text $def.LocalName "$($def.defName).$p" $node.InnerText; $own += $node } }
    # a top field the def does not write itself comes from its parent chain (a RecipeDef jobString set on an abstract base)
    foreach ($f in $topFields) {
      if ($def.SelectNodes($f).Count) { continue }
      $inh = Get-InheritedField $def $f
      if ($inh) { $p = if ($f -like '*/*') { $f -replace '/', '.' } else { $inh.LocalName }; Add-Text $def.LocalName "$($def.defName).$p" $inh.InnerText }
    }
    # the game numbers stages that share a handle: initial-0, initial-1
    $stageHandles = @($def.SelectNodes('stages/li') | ForEach-Object { ([string]$_.label) -replace '[^a-zA-Z0-9_ ]', '' -replace ' ', '_' })
    $stageSeen = @{}
    foreach ($stage in $def.SelectNodes('stages/li')) {
      $handle = ([string]$stage.label) -replace '[^a-zA-Z0-9_ ]', '' -replace ' ', '_'
      if ($handle -and @($stageHandles | Where-Object { $_ -ceq $handle }).Count -gt 1) { $n = [int]$stageSeen[$handle]; $stageSeen[$handle] = $n + 1; $handle = "$handle-$n" }
      if (-not $handle) { $m = "Stage without a usable label handle (index or manual review): $($def.defName)"; if ($Strict) { Find $m } else { Warn $m }; continue }
      foreach ($node in $stage.SelectNodes('label|description')) { Add-Text $def.LocalName "$($def.defName).stages.$handle.$($node.LocalName)" $node.InnerText; $own += $node }
    }
    $xp = ($known | ForEach-Object { ".//$_" }) -join '|'
    foreach ($node in $def.SelectNodes($xp)) {
      # A text deeper in the def (tools/li/label, body parts, work giver verbs...): its exact handle path needs the game's classes
      # (Check-DefInjected.ps1 proves a key resolves), but it can still be COUNTED: see the nested count check below.
      if ($own -notcontains $node) { $k = "$($def.LocalName)/$($def.defName)|$($node.LocalName)"; $nested[$k] = 1 + [int]$nested[$k] }
    }
  }
  foreach ($op in $doc.SelectNodes('//*[@Class="PatchOperationReplace"]')) {
    if ([string]$op.xpath -match 'Defs/(\w+)\[defName="([^"]+)"\]/(description|label|jobString)$') {
      $v = $op.value.SelectSingleNode($Matches[3])
      if ($v) { Add-Text $Matches[1] "$($Matches[2]).$($Matches[3])" $v.InnerText }
    }
  }
}

# --- baseline of the source texts --------------------------------------------
if ($Baseline) {
  $sha = [System.Security.Cryptography.SHA256]::Create()
  $current = [ordered]@{}
  foreach ($id in ($inventory.Keys | Sort-Object)) {
    $current[$id] = ([BitConverter]::ToString($sha.ComputeHash([Text.Encoding]::UTF8.GetBytes([string]$inventory[$id]))) -replace '-', '').ToLowerInvariant()
  }
  if ($UpdateBaseline) {
    [IO.File]::WriteAllText($Baseline, ($current | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
    Write-Host "Baseline written: $($current.Count) source texts -> $Baseline" -ForegroundColor DarkGray
  } elseif (-not (Test-Path -LiteralPath $Baseline)) {
    Find "Baseline file missing: $Baseline (create it with -UpdateBaseline)"
  } else {
    $old = @{}
    foreach ($p in ((Get-Content -LiteralPath $Baseline -Raw -Encoding UTF8) | ConvertFrom-Json).PSObject.Properties) { $old[$p.Name] = [string]$p.Value }
    foreach ($id in $current.Keys) {
      if (-not $old.ContainsKey($id)) { Find "Source text not in the baseline (new): $id" }
      elseif ($old[$id] -ne $current[$id]) { Find "Source text changed since the baseline, review its translation: $id" }
    }
    foreach ($id in $old.Keys) { if (-not $current.Contains($id)) { Warn "Baseline entry without a source text any more: $id" } }
  }
}

# --- language files ---------------------------------------------------------
function Read-Language($language, $kind) {
  $entries = @{}
  # Languages/ folders anywhere under Mod/: a loadFolders subfolder carries its own (Mod/Integrations/<X>/Languages/...)
  $dirs = @(Get-ChildItem $modDir -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $kind -and $_.Parent.Name -eq $language -and $_.Parent.Parent.Name -eq 'Languages' -and $_.FullName -notmatch '[\\/]\.claude[\\/]' })
  foreach ($file in ($dirs | ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter *.xml -File })) {
    $doc = New-Object System.Xml.XmlDocument
    try { $doc.Load($file.FullName) } catch { Find "Malformed XML: $($file.FullName)"; continue }
    if ($doc.DocumentElement.Name -cne 'LanguageData') { Find "Invalid language root: $($file.FullName)"; continue }
    foreach ($node in $doc.DocumentElement.SelectNodes('*')) {
      $key = if ($kind -eq 'DefInjected') { "$($file.Directory.Name)/$($node.LocalName)" } else { $node.LocalName }
      if ($entries.ContainsKey($key)) { Find "Duplicate $language $kind key: $key"; continue }
      if ([string]::IsNullOrWhiteSpace($node.InnerText) -or $node.InnerText -match 'TODO' -or ($RejectCjk -and $node.InnerText -match $cjk)) {
        Find "Empty or untranslated $language $kind key: $key"; continue
      }
      $entries[$key] = $node.InnerText
    }
  }
  return $entries
}
# Formatting tokens that must survive translation: {0} arguments and tags. Not compared: line breaks (a source def may hold real
# newlines where the translation writes \n) and grammar switches such as {PAWN_gender ? é : ée} (a language-specific form with
# no counterpart in the source).
function Tokens($text) { $t = [regex]::Replace($text, '\{[^{}]*\?[^{}]*\}', ''); (@([regex]::Matches($t, '\{[^{}]+\}|</?[^>]+>') | ForEach-Object Value | Sort-Object) -join '|') }

$tr = Read-Language $Language 'DefInjected'
foreach ($key in $inventory.Keys) {
  if (-not $tr.ContainsKey($key)) { Find "$Language coverage missing: $key"; continue }
  if ((Tokens $inventory[$key]) -cne (Tokens $tr[$key])) { Find "Formatting tokens differ: $key" }
  if ($RejectIdentical -and $key -notlike 'HairDef/*' -and $AllowIdentical -cnotcontains $key -and ([string]$inventory[$key]).Trim() -ceq ([string]$tr[$key]).Trim()) { Find "$Language text identical to the source (untranslated, or list the key in -AllowIdentical): $key" }
}
# The inventory is not exhaustive (nested list texts such as tools/li/label are not walked), so an injection it does
# not list is a warning; Check-DefInjected.ps1 proves the key resolves. -Strict makes it an error.
# Nested texts: for each (def type, defName, field name) the XML writes N times below the top level, the translation must hold at
# least N injections for that def ending in that field (more is fine: an inherited list adds elements the def's own XML does not
# show). The handle path itself is Check-DefInjected.ps1's business.
$frCount = @{}
foreach ($key in $tr.Keys) {
  if ($inventory.ContainsKey($key)) { continue }
  $slash = $key.IndexOf('/'); $type = $key.Substring(0, $slash); $rest = $key.Substring($slash + 1)
  $def = $rest.Split('.')[0]; $field = $rest.Split('.')[-1]
  $k = "$type/$def|$field"; $frCount[$k] = 1 + [int]$frCount[$k]
}
foreach ($k in $nested.Keys) {
  $have = [int]$frCount[$k]
  if ($have -lt $nested[$k]) { $p = $k.Split('|'); Find "$Language coverage missing for nested text: $($p[0]) field $($p[1]) ($have injection(s) for $($nested[$k]) text(s))" }
}
foreach ($key in $tr.Keys) {
  if ($inventory.ContainsKey($key)) { continue }
  $slash = $key.IndexOf('/'); $rest = $key.Substring($slash + 1)
  if ($nested.ContainsKey("$($key.Substring(0, $slash))/$($rest.Split('.')[0])|$($rest.Split('.')[-1])")) { continue }
  $m = "$Language path outside the text inventory: $key"; if ($Strict) { Find $m } else { Warn $m }
}

# --- Keyed ------------------------------------------------------------------
$calls = @()
if (-not $NoKeyed) {
  $srcKeys = Read-Language $SourceLanguage 'Keyed'
  $trKeys = Read-Language $Language 'Keyed'
  $srcDir = Join-Path $ModRoot 'Source'
  $haveSource = Test-Path $srcDir
  if ($haveSource) {
    $code = (Get-ChildItem $srcDir -Filter *.cs -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/](obj|bin)[\\/]' } | ForEach-Object { [IO.File]::ReadAllText($_.FullName) }) -join "`n"
    # a Keyed key can also be consumed by an XML def (<li>MM_Yes</li>, a report key): its name as an element text counts as a use
    $xmlText = (Get-ChildItem $modDir -Recurse -Filter *.xml -File | Where-Object { $_.FullName -notmatch '[\\/](Languages|\.claude)[\\/]' } | ForEach-Object { [IO.File]::ReadAllText($_.FullName) }) -join "`n"
    $prefixes = @([regex]::Matches($code, '"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    $calls = @([regex]::Matches($code, '"((?=[A-Za-z0-9_.]*[._])[A-Za-z0-9_.]+)"\s*\.Translate(?:Simple)?\(') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    foreach ($key in $calls) {
      if (-not $srcKeys.ContainsKey($key) -or -not $trKeys.ContainsKey($key)) { Find "Missing Keyed entry (needs $SourceLanguage and $Language): $key"; continue }
    }
  }
  foreach ($key in $srcKeys.Keys) {
    if ($trKeys.ContainsKey($key) -and (Tokens $srcKeys[$key]) -cne (Tokens $trKeys[$key])) { Find "Keyed formatting tokens differ: $key" }
    if (-not $trKeys.ContainsKey($key)) { Find "$Language Keyed entry missing: $key" }
  }
  foreach ($key in $trKeys.Keys) { if (-not $srcKeys.ContainsKey($key) -and $DependencyKeyed -cnotcontains $key) { Find "$SourceLanguage Keyed entry missing: $key" } }
  if ($haveSource -and -not $AllowUnusedKeyed) {
    # A key counts as used when its string literal appears anywhere in the code (helpers such as
    # LocalizedAction("Key", ...) pass it along), or when it is listed in -AllowUnused.
    foreach ($key in @($srcKeys.Keys) + @($trKeys.Keys) | Select-Object -Unique) {
      # Plural families (TRANSLATIONS.md, "Counts and plurals"): Base.One / Base.Many / Base.Zero are picked by a helper from
      # the count, so the entry is used when its BASE is referenced as a literal.
      $base = $key -replace '\.(One|Many|Zero|Other|Few)$', ''
      # a key built at run time ("Mod.Perm." + permission) is used when a code literal ending with a dot is a prefix of it
      if ($AllowUnused -contains $key -or $DependencyKeyed -ccontains $key -or $xmlText.Contains(">$key<") -or @($prefixes | Where-Object { $key.StartsWith($_) }).Count -or $code.Contains("`"$key`"") -or ($base -ne $key -and $code.Contains("`"$base`""))) { continue }
      if ($calls -cnotcontains $key) { Find "Unused Keyed entry (no .Translate() call in Source): $key" }
    }
  }
}

# warnings: things the inventory cannot judge (an injection outside it, a stage with no label handle, a stale baseline entry); Check-DefInjected.ps1 proves a key resolves
foreach ($w in ($warnings | Select-Object -First 10)) { Write-Host "WARN: $w" -ForegroundColor Yellow }
if ($warnings.Count -gt 10) { Write-Host "WARN: ... and $($warnings.Count - 10) more" -ForegroundColor Yellow }
foreach ($f in $findings) { Write-Host $f -ForegroundColor Red }
if ($findings.Count) { Write-Host "FAIL: $($findings.Count) finding(s)" -ForegroundColor Red; exit 1 }
$nestedTotal = 0; foreach ($v in $nested.Values) { $nestedTotal += $v }
Write-Host "PASS: $($inventory.Count) source texts (+ $nestedTotal nested, counted per field) and $Language injections; $($calls.Count) Keyed calls; coverage, stale entries, duplicates and formatting tokens checked."
exit 0
