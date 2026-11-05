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
       -VanillaKeyed lists keys of the game itself that the code calls (no entry in this mod): not reported as missing.
    7b. Plural families (TRANSLATIONS.md "Counts and plurals"): in each language Base.One needs Base.Many and the reverse, Base.Zero
       needs both, and no bare Base entry sits beside them. A .Zero in one language only is accepted when the code falls back on
       .Many ((key + ".Zero").CanTranslate()), otherwise it is required in both. A plural helper (a class writing ".One" and ".Many")
       called with a literal base needs that base's .One and .Many in both languages.
    8. With -RejectIdentical: a translation identical to its source text (HairDef and -AllowIdentical keys excepted).

  LoadFolders mode (a mod with LoadFolders.xml, scripts\lib\ModDefs.ps1): checks 1 to 6 run once per distinct state of the
  optional mods (-ActiveMods picks one), on the Defs, Patches and DefInjected files of the folders that state loads, MayRequire
  defs dropped when their mod is off. On top: a language file (DefInjected or Keyed) at the same path in two loaded folders loses
  the keys only the earlier copy holds (HandMeDowns 53aaf2f); a DefInjected key for a def of this mod that the state does not load
  is reported. A finding true in some states only ends with [in: <states>]. Keyed coverage reads every folder. -NoLoadFolders: off.

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
  # Keys the code calls that belong to the GAME (vanilla Keyed, e.g. "TextMote_Dodge"): not required in this mod's Keyed files.
  # List each one with its reason in the mod's docs.
  [string[]]$VanillaKeyed = @(),
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
  [switch]$UpdateBaseline,
  # LoadFolders mode (a mod with LoadFolders.xml): the optional mods active in the ONE state to check, by packageId.
  # Left out: every distinct state of the optional mods the file and the MayRequire attributes name is checked.
  [string[]]$ActiveMods = @(),
  # Read every Defs, Patches and Languages folder of a LoadFolders mod as one, as before 2026-11-03.
  [switch]$NoLoadFolders
)
$ErrorActionPreference = 'Stop'
$ModRoot = (Resolve-Path $ModRoot).Path
$modDir = if (Test-Path (Join-Path $ModRoot 'Mod\Defs')) { Join-Path $ModRoot 'Mod' } else { $ModRoot }
. (Join-Path $PSScriptRoot 'lib\ModDefs.ps1')
# LoadFolders mode: Mod\LoadFolders.xml (or one at -ModRoot) decides which folders load, per state of the optional mods.
$lfEntries = $null
if (-not $NoLoadFolders) {
  foreach ($c in @((Join-Path $ModRoot 'Mod'), $ModRoot)) { if (Test-Path -LiteralPath (Join-Path $c 'LoadFolders.xml')) { $lfEntries = Get-ModLoadFolders -ModDir $c; if ($null -ne $lfEntries) { $modDir = $c }; break } }
}
$lfMode = $null -ne $lfEntries
$findings = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$outside = 0
function Find($msg) { if (-not $findings.Contains($msg)) { $findings.Add($msg) } }
function Warn($msg) { if (-not $warnings.Contains($msg)) { $warnings.Add($msg) } }

$cjk = '[\p{IsCJKUnifiedIdeographs}]'
$topFields = @('label', 'description', 'jobString', 'labelNoun', 'labelMale', 'labelFemale', 'labelPlural', 'pawnLabel', 'gerundLabel', 'verb', 'gerund', 'ingestible/ingestCommandString', 'ingestible/ingestReportString') + $ExtraFields
$known = @('label', 'description', 'jobString', 'verb', 'gerund', 'labelShort', 'reportString', 'customLabel', 'visualLabel', 'ingestCommandString', 'ingestReportString') + $ExtraFields

# --- inventory --------------------------------------------------------------
$inventory = @{}
$nested = @{}
function Add-Text($type, $key, $value) {
  $id = "$type/$key"
  if ([string]::IsNullOrWhiteSpace($value)) { Find "Missing source text: $id"; return }
  if ($RejectCjk -and $value -match $cjk) { Find "CJK in the source text: $id"; return }
  if ($inventory.ContainsKey($id)) { Find "Duplicate inventoried field: $id"; return }
  $inventory[$id] = $value
  if ($script:curSoft) { $script:softIds[$id] = 1 }
}
$sources = @()
# every Defs/ and Patches/ folder under Mod/, loadFolders subfolders included (Mod/Integrations/<X>/Patches, ...)
foreach ($d in Get-ChildItem $modDir -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -in 'Defs', 'Patches' -and $_.FullName -notmatch '[\\/](Languages|\.claude|\.local)[\\/]' }) { $sources += Get-ChildItem $d.FullName -Recurse -Filter *.xml -File }
# A git repository: files ignored by git are never shipped (local diagnostic defs, scratch patches), so they are not inventoried.
# Not a repository, or git missing: nothing is skipped.
if ($sources.Count -gt 0 -and (Test-Path (Join-Path $ModRoot '.git'))) {
  # Relative forward-slash paths, NUL-separated (-z): Windows PowerShell 5.1 ends each piped line with CRLF, which git would read as part of the
  # path, and without -z git quotes unusual names. A closing NUL keeps that CRLF out of the last path.
  $rel = @{}
  foreach ($s in $sources) { $rel[$s.FullName.Substring($ModRoot.Length).TrimStart('\', '/').Replace('\', '/')] = $s.FullName }
  $gitOut = ((($rel.Keys -join [char]0) + [char]0) | git -C $ModRoot check-ignore --stdin -z 2>$null) -join ''
  $ignored = @($gitOut.Split([char]0) | Where-Object { $_ -and $rel.ContainsKey($_) } | ForEach-Object { $rel[$_] })
  if ($ignored.Count -gt 0) {
    $sources = @($sources | Where-Object { $ignored -notcontains $_.FullName })
    Write-Host "Skipped $($ignored.Count) git-ignored def/patch file(s) (not shipped)."
  }
}
$parsed = New-Object System.Collections.Generic.List[object]
$parsedPath = @{}
foreach ($file in $sources) {
  $doc = New-Object System.Xml.XmlDocument
  try { $doc.Load($file.FullName) } catch { Find "Malformed XML: $($file.FullName)"; continue }
  $parsed.Add($doc)
  $parsedPath[$file.FullName] = $doc
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
# The text inventory of a set of def/patch documents (every parsed one, or those a load state reads).
function Invoke-Inventory($docs) {
  $script:inventory = @{}; $script:nested = @{}; $script:stateDefNames = @{}
  # every def carrying Name="..." (abstract bases included), to walk a ParentName chain
  $script:byName = @{}
  foreach ($doc in $docs) { foreach ($n in $doc.SelectNodes('//*[@Name]')) { if (-not $byName.ContainsKey($n.GetAttribute('Name'))) { $byName[$n.GetAttribute('Name')] = $n } } }
  foreach ($doc in $docs) {
  foreach ($def in $doc.SelectNodes('//*[defName]')) {
    # LoadFolders mode: a def whose MayRequire mods are not active in this state is not loaded
    if ($script:lfState -and -not (Test-MayRequire $def $script:lfState.Active)) { continue }
    $script:stateDefNames[[string]$def.defName] = 1
    # LoadFolders mode: a def a PatchOperationFindMod / Conditional creates exists only with mods named by NAME, not packageId, so
    # no state can tell: its translation is required in at least one state, not in each (MechanoidFactory VFE_FishTrapper).
    $script:curSoft = $script:lfState -and $def.SelectSingleNode('ancestor::*[@Class="PatchOperationFindMod" or @Class="PatchOperationConditional"]')
    # An Abstract="True" def is never loaded as a def, so nothing translates it (JapaneseHomestead: 25 false findings, 2026-11-01).
    if ($def.GetAttribute('Abstract') -eq 'True') { continue }
    # A HediffDef whose every stage has becomeVisible false never shows in the health tab: no text to translate (MintchocoConfectionery relay hediffs, 2026-11-02).
    if ($def.LocalName -eq 'HediffDef') { $st = @($def.SelectNodes('stages/li')); if ($st.Count -gt 0 -and @($st | Where-Object { ([string]$_.becomeVisible).Trim() -ceq 'false' }).Count -eq $st.Count) { continue } }
    $own = @()
    foreach ($f in $topFields) { foreach ($node in $def.SelectNodes($f)) { if ($node.SelectSingleNode('*')) { continue }; $p = if ($f -like '*/*') { $f -replace '/', '.' } else { $node.LocalName }; Add-Text $def.LocalName "$($def.defName).$p" $node.InnerText; $own += $node } }
    # a top field the def does not write itself comes from its parent chain (a RecipeDef jobString set on an abstract base)
    foreach ($f in $topFields) {
      if ($def.SelectNodes($f).Count) { continue }
      $inh = Get-InheritedField $def $f
      if ($inh -and -not $inh.SelectSingleNode('*')) { $p = if ($f -like '*/*') { $f -replace '/', '.' } else { $inh.LocalName }; Add-Text $def.LocalName "$($def.defName).$p" $inh.InnerText }
    }
    # the game numbers stages that share a handle: initial-0, initial-1
    $stageHandles = @($def.SelectNodes('stages/li') | ForEach-Object { ([string]$_.label) -replace '[^a-zA-Z0-9_ ]', '' -replace ' +', '_' } | Where-Object { $_ -match '[a-zA-Z]' })
    $stageSeen = @{}
    $stageIndex = -1
    foreach ($stage in $def.SelectNodes('stages/li')) {
      $stageIndex++
      $handle = ([string]$stage.label) -replace '[^a-zA-Z0-9_ ]', '' -replace ' +', '_'
      # A label with no letter ({0}, a bare number) is no usable name: the stage is injected by its index (PreciousStonesAndJewelryRenew, 2026-11-02).
      if ($handle -match '^[0-9_]*$') { $handle = [string]$stageIndex; $stageSeen[$handle] = 1 }
      if ($handle -and @($stageHandles | Where-Object { $_ -ceq $handle }).Count -gt 1) { $n = [int]$stageSeen[$handle]; $stageSeen[$handle] = $n + 1; $handle = "$handle-$n" }
      if (-not $handle) { $m = "Stage without a usable label handle (index or manual review): $($def.defName)"; if ($Strict) { Find $m } else { Warn $m }; continue }
      foreach ($node in $stage.SelectNodes('label|description')) { if ($node.InnerText -match '^\s*(\{[^{}]*\}\s*)+$') { $own += $node; continue }  # a text made only of tokens ({0}) is filled in by code: nothing to translate
        Add-Text $def.LocalName "$($def.defName).stages.$handle.$($node.LocalName)" $node.InnerText; $own += $node }
    }
    $xp = ($known | ForEach-Object { ".//$_" }) -join '|'
    # A QuestScriptDef is a tree of quest nodes (<label> there is a node argument, not a text): its texts are rulesStrings, proved by Check-DefInjected (MechanoidFactory, 2026-11-02).
    foreach ($node in $(if ($def.LocalName -eq 'QuestScriptDef') { @() } else { $def.SelectNodes($xp) })) {
      # A text deeper in the def (tools/li/label, body parts, work giver verbs...): its exact handle path needs the game's classes
      # (Check-DefInjected.ps1 proves a key resolves), but it can still be COUNTED: see the nested count check below.
      # <verb> of a ManeuverDef is a nested VerbProperties struct, not a text
      if ($node.SelectSingleNode('*')) { continue }
      if ($own -notcontains $node) { $k = "$($def.LocalName)/$($def.defName)|$($node.LocalName)"; $nested[$k] = 1 + [int]$nested[$k] }
    }
  }
  $script:curSoft = $false
  foreach ($op in $doc.SelectNodes('//*[@Class="PatchOperationReplace"]')) {
    if ([string]$op.xpath -match 'Defs/(\w+)\[defName="([^"]+)"\]/(description|label|jobString)$') {
      $v = $op.value.SelectSingleNode($Matches[3])
      # A patch rewrites a text the def already holds (often inside a PatchOperationFindMod branch): one key, the patched text wins, no duplicate (MedievalHomestead, 2026-11-02).
      if ($v) { $pid2 = "$($Matches[1])/$($Matches[2]).$($Matches[3])"; if ($inventory.ContainsKey($pid2) -and -not [string]::IsNullOrWhiteSpace($v.InnerText)) { $inventory[$pid2] = $v.InnerText } else { Add-Text $Matches[1] "$($Matches[2]).$($Matches[3])" $v.InnerText } }
    }
  }
  }
}

# --- language files ---------------------------------------------------------
function Read-Language($language, $kind) {
  # Languages/ folders anywhere under Mod/: a loadFolders subfolder carries its own (Mod/Integrations/<X>/Languages/...)
  $dirs = @(Get-ChildItem $modDir -Recurse -Directory -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq $kind -and $_.Parent.Name -eq $language -and $_.Parent.Parent.Name -eq 'Languages' -and $_.FullName -notmatch '[\\/](\.claude|\.local)[\\/]' })
  return Read-LanguageFiles @($dirs | ForEach-Object { Get-ChildItem $_.FullName -Recurse -Filter *.xml -File }) $language $kind
}
function Read-LanguageFiles($files, $language, $kind) {
  $entries = @{}
  foreach ($file in $files) {
    $doc = New-Object System.Xml.XmlDocument
    try { $doc.Load($file.FullName) } catch { Find "Malformed XML: $($file.FullName)"; continue }
    if ($doc.DocumentElement.Name -cne 'LanguageData') { Find "Invalid language root: $($file.FullName)"; continue }
    foreach ($node in $doc.DocumentElement.SelectNodes('*')) {
      $key = if ($kind -eq 'DefInjected') { "$($file.Directory.Name)/$($node.LocalName)" } else { $node.LocalName }
      if ($entries.ContainsKey($key)) { Find "Duplicate $language $kind key: $key"; continue }
      if ([string]::IsNullOrWhiteSpace($node.InnerText) -or $node.InnerText -cmatch '\bTODO\b' -or ($RejectCjk -and $node.InnerText -match $cjk)) {
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
# Field of an injection path: the last segment, or the one before it when that is a list index (rulesStrings.3 -> rulesStrings).
function FieldOf($rest) { $seg = $rest.Split('.'); if ($seg.Count -gt 2 -and $seg[-1] -match '^\d+$') { $seg[-2] } else { $seg[-1] } }
# Pronoun tokens of the source ({PAWN_pronoun}, {PAWN_objective}...) have no 1:1 counterpart when the translation writes a grammar switch
# ({PAWN_gender ? il : elle}) in their place: drop them from both sides when the translation holds a switch.
function TokensPair($src, $dst) {
  if ($dst -match '\{[^{}]*\?[^{}]*\}') { $strip = '\{[A-Za-z]+_(pronoun|objective|possessive)\}'; $src = [regex]::Replace($src, $strip, ''); $dst = [regex]::Replace($dst, $strip, '') }
  return ,@((Tokens $src), (Tokens $dst))
}

# Coverage of the current inventory by the DefInjected entries $tr.
$outsideKeys = @{}
$softIds = @{}; $script:curSoft = $false
$soft = [char]1 + 'soft:'
function Invoke-Coverage($tr) {
foreach ($key in $inventory.Keys) {
  if (-not $tr.ContainsKey($key)) { Find "$(if ($softIds.ContainsKey($key)) { $soft })$Language coverage missing: $key"; continue }
  $tp = TokensPair $inventory[$key] $tr[$key]; if ($tp[0] -cne $tp[1]) { Find "Formatting tokens differ: $key" }
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
  $def = $rest.Split('.')[0]; $field = (FieldOf $rest)
  $k = "$type/$def|$field"; $frCount[$k] = 1 + [int]$frCount[$k]
}
foreach ($k in $nested.Keys) {
  $have = [int]$frCount[$k]
  if ($have -lt $nested[$k]) { $p = $k.Split('|'); Find "$Language coverage missing for nested text: $($p[0]) field $($p[1]) ($have injection(s) for $($nested[$k]) text(s))" }
}
foreach ($key in $tr.Keys) {
  if ($inventory.ContainsKey($key)) { continue }
  $slash = $key.IndexOf('/'); $rest = $key.Substring($slash + 1)
  # LoadFolders mode: a key for a def of this mod that this state does not load aims at nothing (a MayRequire def, a def of
  # another load folder translated from an ungated one: ImperialFurnishings Royalty, HandMeDowns AnimalArk).
  $dn = $rest.Split('.')[0]
  if ($script:lfState -and $allModDefNames.ContainsKey($dn) -and -not $stateDefNames.ContainsKey($dn)) { Find "$Language key for a def this load state does not load: $key"; continue }
  if ($nested.ContainsKey("$($key.Substring(0, $slash))/$($rest.Split('.')[0])|$((FieldOf $rest))")) { continue }
  # RulePack strings (logRulesInitiator.rulesStrings.N) are nested list texts the inventory does not walk: Check-DefInjected.ps1 proves them.
  # The inventory is a shortcut, not the truth: Check-DefInjected.ps1 resolves every injection against the loaded defs. A path the inventory does not
  # list is therefore counted, not warned about one by one (false positives: rulesStrings.N, lifeStages.N.label, inherited labelPlural, 2026-11-02).
  # -Strict still makes each one an error.
  if ($Strict) { Find "$Language path outside the text inventory: $key" } else { $script:outsideKeys[$key] = 1 }
}
}

# Language files of a load state read the way the game reads them: one file per path relative to its load folder, the later
# folder's copy only. A dropped copy holding keys the kept one lacks loses them (HandMeDowns 53aaf2f): a finding.
function Get-StateLanguageFiles($folders, $language, $kind) {
  $r = Get-ModFolderFiles -Folders $folders -SubPath "Languages\$language\$kind"
  foreach ($sh in $r.Shadowed) {
    $keysOf = { param($p) try { $d = New-Object System.Xml.XmlDocument; $d.Load($p); @($d.DocumentElement.SelectNodes('*') | ForEach-Object LocalName) } catch { @() } }
    $kept = @(& $keysOf $sh.Winner); $lost = @(& $keysOf $sh.Path | Where-Object { $kept -cnotcontains $_ })
    if ($lost.Count) { Find "Two loaded folders hold the same $language $kind file ($($sh.Rel)): $($sh.Winner.Substring($modDir.Length + 1)) replaces $($sh.Path.Substring($modDir.Length + 1)), so $($lost.Count) key(s) never load: $((@($lost) | Select-Object -First 5) -join ', ')$(if ($lost.Count -gt 5) { ', ...' })" }
  }
  return @($r.Files | Where-Object { $_.Path -notmatch '[\\/](\.claude|\.local)[\\/]' } | ForEach-Object { Get-Item -LiteralPath $_.Path })
}

$script:lfState = $null
if (-not $lfMode) {
  Invoke-Inventory $parsed
  $tr = Read-Language $Language 'DefInjected'
  Invoke-Coverage $tr
} else {
  # Each state of the optional mods: its folders, its defs (MayRequire), its language files. A finding true in some states only
  # says which ones.
  $allModDefNames = @{}; $mayIds = @()
  foreach ($doc in $parsed) { foreach ($def in $doc.SelectNodes('//*[defName]')) { $allModDefNames[[string]$def.defName] = 1 }; $mayIds += Get-MayRequireIds $doc }
  $mayIds = @($mayIds | Sort-Object -Unique)
  $states = @(if ($PSBoundParameters.ContainsKey('ActiveMods')) { [pscustomobject]@{ Label = $(if ($ActiveMods.Count) { (@($ActiveMods) | ForEach-Object { "+$(ConvertTo-ModId $_)" }) -join ' ' } else { 'base' }); Active = @($ActiveMods | ForEach-Object { ConvertTo-ModId $_ }) } } else { Get-ModLoadStates -ModDir $modDir -ExtraIds $mayIds })
  Write-Host "LoadFolders.xml: $($states.Count) load state(s) checked: $((@($states | Select-Object -First 6 | ForEach-Object Label)) -join '; ')$(if ($states.Count -gt 6) { '; ...' })" -ForegroundColor DarkGray
  $seenFolder = @{}; foreach ($e in $lfEntries) { if ($seenFolder.ContainsKey($e.Path)) { Find "LoadFolders.xml lists folder '$($e.Rel)' twice for 1.6 (the game reports a repeating folder)" }; $seenFolder[$e.Path] = 1 }
  $global = $findings; $globalWarn = $warnings
  $perState = [ordered]@{}; $warnState = [ordered]@{}
  $unionInventory = @{}; $unionNested = @{}
  foreach ($s in $states) {
    $script:findings = New-Object System.Collections.Generic.List[string]
    $script:warnings = New-Object System.Collections.Generic.List[string]
    $script:lfState = [pscustomobject]@{ Label = $s.Label; Active = (New-ModIdSet $s.Active) }
    $folders = Get-ModDefFolders -ModDir $modDir -ActiveMods $s.Active
    $docs = @(foreach ($sub in 'Defs', 'Patches') { foreach ($f in (Get-ModFolderFiles -Folders $folders -SubPath $sub).Files) { if ($parsedPath.ContainsKey($f.Path)) { $parsedPath[$f.Path] } } })
    Invoke-Inventory $docs
    foreach ($id in $inventory.Keys) { $unionInventory[$id] = $inventory[$id] }
    foreach ($k in $nested.Keys) { if ([int]$unionNested[$k] -lt $nested[$k]) { $unionNested[$k] = $nested[$k] } }
    $tr = Read-LanguageFiles (Get-StateLanguageFiles $folders $Language 'DefInjected') $Language 'DefInjected'
    Invoke-Coverage $tr
    if (-not $NoKeyed) { foreach ($l in @($SourceLanguage, $Language) | Select-Object -Unique) { [void](Get-StateLanguageFiles $folders $l 'Keyed') } }
    foreach ($m in $findings) { if (-not $perState.Contains($m)) { $perState[$m] = New-Object System.Collections.Generic.List[string] }; $perState[$m].Add($s.Label) }
    foreach ($m in $warnings) { if (-not $warnState.Contains($m)) { $warnState[$m] = New-Object System.Collections.Generic.List[string] }; $warnState[$m].Add($s.Label) }
  }
  $script:lfState = $null
  $script:findings = $global; $script:warnings = $globalWarn
  $tag = { param($m, $in) if ($in.Count -lt $states.Count) { "$m [in: $((@($in) | Select-Object -First 4) -join '; ')$(if ($in.Count -gt 4) { "; +$($in.Count - 4) more" })]" } else { $m } }
  foreach ($m in $perState.Keys) { if ($m.StartsWith($soft)) { if ($perState[$m].Count -eq $states.Count) { Find $m.Substring($soft.Length) } } else { Find (& $tag $m $perState[$m]) } }
  foreach ($m in $warnState.Keys) { Warn (& $tag $m $warnState[$m]) }
  $inventory = $unionInventory; $nested = $unionNested
}
$outside = $outsideKeys.Count

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

# --- Keyed ------------------------------------------------------------------
$calls = @()
if (-not $NoKeyed) {
  $srcKeys = Read-Language $SourceLanguage 'Keyed'
  $trKeys = Read-Language $Language 'Keyed'
  # Keys the GAME defines (English Keyed of Core and each DLC under Data/): never required in this mod, no -VanillaKeyed list to keep per mod.
  $coreKeyed = @{}
  $dataDir = 'C:\Program Files (x86)\Steam\steamapps\common\RimWorld\Data'
  foreach ($coreDir in @(Get-ChildItem -LiteralPath $dataDir -Directory -ErrorAction SilentlyContinue | ForEach-Object { Join-Path $_.FullName 'Languages\English\Keyed' } | Where-Object { Test-Path -LiteralPath $_ })) { foreach ($f in Get-ChildItem -LiteralPath $coreDir -Filter *.xml -File) { try { $d = New-Object System.Xml.XmlDocument; $d.Load($f.FullName); foreach ($n in $d.DocumentElement.ChildNodes) { if ($n.NodeType -eq 'Element') { $coreKeyed[$n.LocalName] = 1 } } } catch {} } }
  $srcDir = Join-Path $ModRoot 'Source'
  $haveSource = Test-Path $srcDir
  if ($haveSource) {
    $code = (Get-ChildItem $srcDir -Filter *.cs -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/](obj|bin)[\\/]' } | ForEach-Object { [IO.File]::ReadAllText($_.FullName) }) -join "`n"
    # a Keyed key can also be consumed by an XML def (<li>MM_Yes</li>, a report key): its name as an element text counts as a use
    $xmlText = (Get-ChildItem $modDir -Recurse -Filter *.xml -File | Where-Object { $_.FullName -notmatch '[\\/](Languages|\.claude|\.local)[\\/]' } | ForEach-Object { [IO.File]::ReadAllText($_.FullName) }) -join "`n"
    $prefixes = @([regex]::Matches($code, '"([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)*\.)"') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    $calls = @([regex]::Matches($code, '"((?=[A-Za-z0-9_.]*[._])[A-Za-z0-9_.]+)"\s*\.Translate(?:Simple)?\(') | ForEach-Object { $_.Groups[1].Value } | Sort-Object -Unique)
    foreach ($key in $calls) {
      if ($VanillaKeyed -ccontains $key -or $coreKeyed.ContainsKey($key)) { continue }
      if (-not $srcKeys.ContainsKey($key) -or -not $trKeys.ContainsKey($key)) { Find "Missing Keyed entry (needs $SourceLanguage and $Language): $key"; continue }
    }
  }
  # Plural families (TRANSLATIONS.md "Counts and plurals", 2026-09-25): Base.One and Base.Many go together in each language, and
  # Base.Zero needs both. A .Zero may exist in one language only (French reads 0 as a singular, English does not) when the code
  # falls back on .Many for a missing one, i.e. tests (key + ".Zero").CanTranslate() (BillAutopilot CountForm). Without that
  # fallback the code asks for .Zero in every language (ArchitectStudio CountedText): a .Zero in one needs it in the other.
  $zeroFallback = $haveSource -and $code -match '"\.Zero"\s*\)\s*\.CanTranslate\('
  $families = @{}
  foreach ($pair in @(@($SourceLanguage, $srcKeys), @($Language, $trKeys))) {
    $lang = $pair[0]; $tab = $pair[1]
    foreach ($key in $tab.Keys) {
      if ($key -notmatch '^(.+)\.(One|Many|Zero)$') { continue }
      $b = $Matches[1]; $form = $Matches[2]; $families[$b] = 1
      if ($form -eq 'One' -and -not $tab.ContainsKey("$b.Many")) { Find "Plural family incomplete ($lang): $key has no $b.Many" }
      if ($form -eq 'Many' -and -not $tab.ContainsKey("$b.One")) { Find "Plural family incomplete ($lang): $key has no $b.One" }
      if ($form -eq 'Zero' -and -not ($tab.ContainsKey("$b.One") -and $tab.ContainsKey("$b.Many"))) { Find "Plural family incomplete ($lang): $key has no $b.One and $b.Many" }
    }
  }
  foreach ($b in $families.Keys) {
    # the code names the family by its base; the base itself is no entry (a bare Base beside Base.One and Base.Many is a leftover)
    foreach ($pair in @(@($SourceLanguage, $srcKeys), @($Language, $trKeys))) { if ($pair[1].ContainsKey($b) -and $pair[1].ContainsKey("$b.One") -and $pair[1].ContainsKey("$b.Many")) { Find "Plural family with a bare base entry ($($pair[0])): $b (the code asks for $b.One / $b.Many, never $b)" } }
  }
  # A plural helper (a class whose code writes both ".One" and ".Many": CountForm.Text, CountedText.Get) is called with the BASE:
  # that base must be a family, .One and .Many in both languages (BillAutopilot ValidateXml, ArchitectStudio Validate-Mod).
  if ($haveSource) {
    $helpers = @()
    foreach ($cs in Get-ChildItem $srcDir -Filter *.cs -Recurse -File | Where-Object { $_.FullName -notmatch '[\\/](obj|bin)[\\/]' }) {
      $t = [IO.File]::ReadAllText($cs.FullName)
      if (-not ($t.Contains('".One"') -and $t.Contains('".Many"'))) { continue }
      foreach ($cm in [regex]::Matches($t, '\bclass\s+(\w+)')) { foreach ($mm in [regex]::Matches($t, '\bstatic\s+[\w<>\[\].]+\s+(\w+)\s*\(\s*string\s')) { $helpers += "$($cm.Groups[1].Value).$($mm.Groups[1].Value)" } }
    }
    foreach ($h in ($helpers | Sort-Object -Unique)) {
      foreach ($hm in [regex]::Matches($code, [regex]::Escape($h) + '\(\s*"([A-Za-z0-9_.]+)"')) {
        $b = $hm.Groups[1].Value
        foreach ($pair in @(@($SourceLanguage, $srcKeys), @($Language, $trKeys))) { foreach ($form in 'One', 'Many') { if (-not $pair[1].ContainsKey("$b.$form")) { Find "Plural helper $h(`"$b`") needs $b.$form ($($pair[0]))" } } }
      }
    }
  }
  # an optional .Zero: present in one language, absent from the other, and the family's .One and .Many are there
  function Test-OptionalZero($key, $other) { $zeroFallback -and $key -match '^(.+)\.Zero$' -and $other.ContainsKey("$($Matches[1]).One") -and $other.ContainsKey("$($Matches[1]).Many") }
  foreach ($key in $srcKeys.Keys) {
    if ($trKeys.ContainsKey($key) -and ($tp = TokensPair $srcKeys[$key] $trKeys[$key]) -and $tp[0] -cne $tp[1]) { Find "Keyed formatting tokens differ: $key" }
    if (-not $trKeys.ContainsKey($key) -and -not (Test-OptionalZero $key $trKeys)) { Find "$Language Keyed entry missing: $key" }
  }
  foreach ($key in $trKeys.Keys) { if (-not $srcKeys.ContainsKey($key) -and $DependencyKeyed -cnotcontains $key -and -not (Test-OptionalZero $key $srcKeys)) { Find "$SourceLanguage Keyed entry missing: $key" } }
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
if ($outside -gt 0) { Write-Host "NOTE: $outside $Language injection path(s) not in the text inventory (nested or inherited texts); run Check-DefInjected.ps1 to prove them, or -Strict to list them as errors." -ForegroundColor DarkYellow }
foreach ($w in ($warnings | Select-Object -First 10)) { Write-Host "WARN: $w" -ForegroundColor Yellow }
if ($warnings.Count -gt 10) { Write-Host "WARN: ... and $($warnings.Count - 10) more" -ForegroundColor Yellow }
foreach ($f in $findings) { Write-Host $f -ForegroundColor Red }
if ($findings.Count) { Write-Host "FAIL: $($findings.Count) finding(s)" -ForegroundColor Red; exit 1 }
$nestedTotal = 0; foreach ($v in $nested.Values) { $nestedTotal += $v }
Write-Host "PASS: $($inventory.Count) source texts (+ $nestedTotal nested, counted per field) and $Language injections; $($calls.Count) Keyed calls; coverage, stale entries, duplicates and formatting tokens checked."
exit 0
