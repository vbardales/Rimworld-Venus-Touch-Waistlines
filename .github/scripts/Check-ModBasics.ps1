<#
.SYNOPSIS
  The generic static checks every mod needs, in one shared script (what the per-mod Check-Mod.ps1 / Check-Content.ps1 all repeated).

.DESCRIPTION
  Owner rule of 2026-10-11 (AGENTS.md "Local scripts"): the per-mod Check-Mod.ps1 copies (AlphaMythology, BeefEaters,
  ColorfulCoatsDodos, ResolveThisInstead, RimScentExtended x4, VenusTouchWaistlines) and Check-Content.ps1 (ACBGE) each
  mixed the same generic checks with checks of their own content. This script holds the generic part; what is specific
  to a mod (an expected number of creatures, a guarded patch, a settings contract) stays in that mod's own script, which
  calls this one first.

  Checks, every finding reported before the exit code (0 clean, 1 at least one finding):
    1. Every XML file under Mod/ is well formed.
    2. No defName is declared twice for the same def type under Mod/Defs.
    3. Every <xpath> in Mod/Patches compiles (XPath 1.0, as the game).
    4. Mod/About/About.xml: packageId is lowercase and starts with `nelim.`; name and description are present;
       supportedVersions names 1.6; each modDependencies entry has a packageId and a displayName and a
       steamWorkshopUrl or downloadUrl; with -Unofficial the name ends with "(unofficial)".
    5. ATTRIBUTION.md and LICENSE, when present both at the repo root and in Mod/, are the same text (line endings ignored).
    6. Mod/About/Preview.png and ModIcon.png exist and are PNG files; Preview.png is under 1 MiB.
    7. Mod/About/PublishedFileId.txt, when present, holds digits only (and, with -OriginalWorkshopId, not that id).
    8. WARN only (no effect on the exit code): once Art/Preview.ico exists, desktop.ini and Mod/desktop.ini exist and
       their icon target exists (AUDIT.md 10.c bis).

    9. WARN / NOTE only (added 2026-11-03 from the local-scripts sharing study; no effect on the exit code):
       9.1 ModIcon.png is 128x128 and Preview.png 896x504 (STYLE_RIMWORLD.md);
       9.2 the About.xml description ends with `[url=<its <url>>]Source code on GitHub[/url]` and, for a port
           (-Unofficial or a name ending "(unofficial)"), starts with `UNOFFICIAL.` (PUBLISHING.md);
       9.3 nothing ships in Mod/ that must not: .pdb, a .dds with no PNG sibling, editor or intermediate files
           (.psd .xcf .kra .blend .aseprite .bak .tmp .orig .user .log, Thumbs.db), a DLL when the repo has no Source/;
       9.4 every IfModActive id of LoadFolders.xml is in About.xml loadAfter (WARN); a loadAfter id that gates no
           folder is only a NOTE;
       9.5 README.md, ATTRIBUTION.md, LICENSE and STATUS.md at the mod root hold no French (8+ French function
           words and 3+ accented letters, code and URLs ignored).
       9.6 the mod root and Art/ hold only what the closed lists allow (STYLE_RIMWORLD.md, "Dossiers a la racine d'un
           mod"); tracked or untracked-not-ignored entries, so ignored Build/ and local files do not count.
       The LICENSE / ATTRIBUTION copy comparison (rule 5 above) already existed and is an error.

    powershell -File scripts\Check-ModBasics.ps1 -ModRoot C:\Users\nelim\Documents\rimworld\BeefEatersRenew -Unofficial
#>
param(
  [Parameter(Mandatory)][string]$ModRoot,
  # Require the "(unofficial)" suffix in the mod name (a Renew port of somebody else's mod).
  [switch]$Unofficial,
  # The workshop id of the ORIGINAL mod: PublishedFileId.txt must never hold it.
  [string]$OriginalWorkshopId
)
$ErrorActionPreference = 'Stop'
$ModRoot = (Resolve-Path $ModRoot).Path
$mod = Join-Path $ModRoot 'Mod'
if (-not (Test-Path $mod)) { throw "No Mod/ folder under $ModRoot" }
$findings = New-Object System.Collections.Generic.List[string]
function Find($m) { $findings.Add($m) }
function Rel($p) { $p.Substring($ModRoot.Length + 1) }

# 1-3: XML
$files = @(Get-ChildItem $mod -Recurse -Filter *.xml -File)
$seen = @{}
foreach ($f in $files) {
  $doc = New-Object System.Xml.XmlDocument
  try { $doc.Load($f.FullName) } catch { Find "Malformed XML: $(Rel $f.FullName): $($_.Exception.InnerException.Message)"; continue }
  $inDefs = $f.FullName -match '[\\/]Defs[\\/]'
  if ($inDefs -and $doc.DocumentElement.LocalName -eq 'Defs') {
    foreach ($d in $doc.DocumentElement.ChildNodes) {
      if ($d.NodeType -ne 'Element') { continue }
      $dn = $d.SelectSingleNode('defName')
      if (-not $dn) { continue }
      $key = $d.LocalName + ':' + $dn.InnerText.Trim()
      if ($seen.ContainsKey($key)) { Find "Duplicate defName $key in $(Rel $f.FullName) and $($seen[$key])" } else { $seen[$key] = Rel $f.FullName }
    }
  }
  foreach ($x in $doc.SelectNodes('//xpath')) {
    try { [void][System.Xml.XPath.XPathExpression]::Compile($x.InnerText) } catch { Find "Bad XPath in $(Rel $f.FullName): $($x.InnerText)" }
  }
}

# 4: About.xml
$aboutPath = Join-Path $mod 'About\About.xml'
if (-not (Test-Path $aboutPath)) { Find 'Mod/About/About.xml is missing' }
else {
  $about = New-Object System.Xml.XmlDocument
  try {
    $about.Load($aboutPath)
    $meta = $about.DocumentElement
    $packageId = [string]$meta.SelectSingleNode('packageId').InnerText
    if ($packageId -cnotmatch '^nelim\.[a-z0-9.]+$') { Find "About: packageId '$packageId' must be lowercase and start with nelim." }
    $name = [string]$meta.SelectSingleNode('name').InnerText
    if (-not $name.Trim()) { Find 'About: name is empty' }
    elseif ($Unofficial -and $name -notmatch '\(unofficial\)$') { Find "About: name '$name' must end with (unofficial)" }
    if (-not ([string]$meta.SelectSingleNode('description').InnerText).Trim()) { Find 'About: description is empty' }
    if (@($meta.SelectNodes('supportedVersions/li') | ForEach-Object { $_.InnerText.Trim() }) -notcontains '1.6') { Find 'About: supportedVersions does not name 1.6' }
    foreach ($dep in $meta.SelectNodes('modDependencies/li')) {
      $id = [string]$dep.packageId
      if (-not $id) { Find 'About: a modDependencies entry has no packageId'; continue }
      if ($id -like 'Ludeon.*') { continue }   # an official DLC: no download link to give
      if (-not [string]$dep.displayName) { Find "About: dependency $id has no displayName" }
      if (-not [string]$dep.steamWorkshopUrl -and -not [string]$dep.downloadUrl) { Find "About: dependency $id has neither steamWorkshopUrl nor downloadUrl" }
    }
  } catch { Find "About.xml is not readable: $($_.Exception.Message)" }
}

# 5: notices
foreach ($n in 'ATTRIBUTION.md', 'LICENSE') {
  $a = Join-Path $ModRoot $n; $b = Join-Path $mod $n
  # Same text is enough: git's line-ending conversion may leave one copy CRLF and the other LF in the working tree (BurnBarrel, 2026-11-02).
  if ((Test-Path $a) -and (Test-Path $b) -and (([IO.File]::ReadAllText($a) -replace "`r`n", "`n") -cne ([IO.File]::ReadAllText($b) -replace "`r`n", "`n"))) { Find "$n differs between the repo root and Mod/ (text, not just line endings)" }
}

# 6: images
foreach ($img in 'Preview.png', 'ModIcon.png') {
  $p = Join-Path $mod "About\$img"
  if (-not (Test-Path $p)) { Find "Mod/About/$img is missing"; continue }
  $bytes = [IO.File]::ReadAllBytes($p)
  if ($bytes.Length -lt 24 -or ([BitConverter]::ToString($bytes, 0, 8) -ne '89-50-4E-47-0D-0A-1A-0A')) { Find "Mod/About/$img is not a PNG file"; continue }
  if ($img -eq 'Preview.png' -and $bytes.Length -ge 1MB) { Find 'Mod/About/Preview.png is 1 MiB or more' }
}

# 7: PublishedFileId
$idFile = Join-Path $mod 'About\PublishedFileId.txt'
if (Test-Path $idFile) {
  $id = ([IO.File]::ReadAllText($idFile)).Trim()
  if ($id -notmatch '^\d+$') { Find 'PublishedFileId.txt must hold digits only' }
  elseif ($OriginalWorkshopId -and $id -eq $OriginalWorkshopId) { Find 'PublishedFileId.txt holds the ORIGINAL mod id' }
}

# 8: Windows folder icons (warning only, AUDIT.md 10.c bis): due once Preview has been rendered (Art/Preview.ico exists)
$warnings = New-Object System.Collections.Generic.List[string]
if (Test-Path (Join-Path $ModRoot 'Art\Preview.ico')) {
  foreach ($pair in @(@('desktop.ini', 'Art\ModIcon.ico'), @('Mod\desktop.ini', 'Art\Preview.ico'))) {
    $ini = Join-Path $ModRoot $pair[0]
    if (-not (Test-Path $ini)) { $warnings.Add("$($pair[0]) is missing (folder icon, AUDIT.md 10.c bis)"); continue }
    if (-not (Test-Path (Join-Path $ModRoot $pair[1]))) { $warnings.Add("$($pair[0]) points to $($pair[1]), which is missing") }
  }
}

# 9: shared rules lifted from the per-mod Tests/* copies (study of 2026-11-03). All WARN (or NOTE): no mod turns red because of them.
$notes = New-Object System.Collections.Generic.List[string]
function ReadPngSize($p) {
  $b = [IO.File]::ReadAllBytes($p)
  if ($b.Length -lt 24 -or ([BitConverter]::ToString($b, 0, 8) -ne '89-50-4E-47-0D-0A-1A-0A')) { return $null }
  $w = ([int]$b[16] -shl 24) + ([int]$b[17] -shl 16) + ([int]$b[18] -shl 8) + [int]$b[19]
  $h = ([int]$b[20] -shl 24) + ([int]$b[21] -shl 16) + ([int]$b[22] -shl 8) + [int]$b[23]
  return @($w, $h)
}
# 9.1 PNG dimensions (STYLE_RIMWORLD.md "ModIcon" 128x128; "Preview 896x504")
foreach ($spec in @(@('ModIcon.png', 128, 128), @('Preview.png', 896, 504))) {
  $p = Join-Path $mod "About\$($spec[0])"
  if (-not (Test-Path $p)) { continue }
  $sz = ReadPngSize $p
  if ($sz -and ($sz[0] -ne $spec[1] -or $sz[1] -ne $spec[2])) { $warnings.Add("Mod/About/$($spec[0]) is $($sz[0])x$($sz[1]), expected $($spec[1])x$($spec[2])") }
}
# 9.2 About.xml description: final source link, UNOFFICIAL opening for ports (PUBLISHING.md)
$about2 = $null
if (Test-Path $aboutPath) { try { $about2 = New-Object System.Xml.XmlDocument; $about2.Load($aboutPath) } catch { $about2 = $null } }
if ($about2) {
  $meta2 = $about2.DocumentElement
  $desc = ([string]$meta2.SelectSingleNode('description').InnerText).Trim()
  $url = ([string]$meta2.SelectSingleNode('url').InnerText).Trim()
  $name2 = ([string]$meta2.SelectSingleNode('name').InnerText).Trim()
  if ($desc) {
    if (-not $url) { $warnings.Add('About: no <url> field (the repository link of the description has nothing to match)') }
    else {
      $link = "[url=$url]Source code on GitHub[/url]"
      if (-not $desc.EndsWith($link)) { $warnings.Add("About: description must end with $link") }
    }
    $isPort = $Unofficial -or $name2 -match '\(unofficial\)$'
    if ($isPort -and -not $desc.StartsWith('UNOFFICIAL.')) { $warnings.Add('About: a port (unofficial) must open its description with the UNOFFICIAL. notice') }
  }
}
# 9.3 files that must not ship in Mod/ ("has Source" = a Source/ folder, or any .cs outside Mod/ such as the per-tool folders of PickleTools)
$hasSource = $null   # computed on the first DLL only
foreach ($f in Get-ChildItem $mod -Recurse -File) {
  $r = Rel $f.FullName; $ext = $f.Extension.ToLower()
  if ($ext -eq '.pdb') { $warnings.Add("${r}: debug symbols must not ship") }
  elseif ($ext -eq '.dds') { if (-not (Test-Path ([IO.Path]::ChangeExtension($f.FullName, '.png')))) { $warnings.Add("${r}: .dds with no PNG sibling (.dds is a local derivative, never the only copy)") } }
  elseif ($ext -in '.psd', '.xcf', '.kra', '.blend', '.aseprite', '.ase', '.bak', '.tmp', '.orig', '.rej', '.user', '.log' -or $f.Name -eq 'Thumbs.db') { $warnings.Add("${r}: intermediate or editor file must not ship") }
  elseif ($ext -eq '.dll' -and -not $(if ($null -eq $hasSource) { $hasSource = (Test-Path (Join-Path $ModRoot 'Source')) -or [bool](Get-ChildItem $ModRoot -Recurse -Filter *.cs -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -notlike "$mod*" } | Select-Object -First 1) }; $hasSource)) { $warnings.Add("${r}: bundled DLL but the mod has no Source/") }
}
# 9.4 LoadFolders.xml IfModActive ids vs About.xml loadAfter
$lfPath = @('LoadFolders.xml', 'loadFolders.xml') | ForEach-Object { Join-Path $mod $_ } | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($lfPath -and $about2) {
  $lf = New-Object System.Xml.XmlDocument
  $gated = @{}
  try {
    $lf.Load($lfPath)
    foreach ($li in $lf.SelectNodes('//li[@IfModActive]')) { foreach ($id in ($li.GetAttribute('IfModActive') -split ',')) { if ($id.Trim()) { $gated[$id.Trim().ToLower()] = $true } } }
    $after = @{}
    foreach ($li in $about2.DocumentElement.SelectNodes('loadAfter/li | loadAfterByVersion//li')) { $after[$li.InnerText.Trim().ToLower()] = $true }
    foreach ($id in $gated.Keys) { if (-not $after.ContainsKey($id)) { $warnings.Add("LoadFolders.xml gates a folder on $id, which is not in About.xml loadAfter") } }
    foreach ($id in $after.Keys) { if (-not $gated.ContainsKey($id) -and $id -notlike 'ludeon.*' -and $id -ne 'brrainz.harmony') { $notes.Add("About.xml loadAfter $id gates no folder in LoadFolders.xml") } }
  } catch { $warnings.Add("LoadFolders.xml is not readable: $($_.Exception.Message)") }
}
# 9.5 root docs in English: cheap scan of French function words (code, links and URLs removed first)
$frWords = 'le|la|les|des|une|est|pour|avec|dans|sur|que|qui|pas|mais|sont|cette|nous|vous|ou'
foreach ($n in 'README.md', 'ATTRIBUTION.md', 'LICENSE', 'STATUS.md') {
  $p = Join-Path $ModRoot $n
  if (-not (Test-Path $p)) { continue }
  $t = [IO.File]::ReadAllText($p)
  $t = [regex]::Replace($t, '(?s)```.*?```', ' ')
  $t = [regex]::Replace($t, '`[^`\r\n]*`', ' ')
  $t = [regex]::Replace($t, '\]\([^)]*\)|https?://\S+', ' ')
  $hits = [regex]::Matches($t, "(?<![\w'-])($frWords)(?![\w'-])").Count
  $accents = [regex]::Matches($t, '[éèêàùçôîâ]').Count
  if ($hits -ge 8 -and $accents -ge 3) { $warnings.Add("$n looks French ($hits function-word hits, $accents accented letters); docs are English only") }
}
# 9.6 closed list of the mod root and of Art/ (owner 2026-10-28, STYLE_RIMWORLD.md "Dossiers a la racine d'un mod"): tracked or untracked-not-ignored entries only
$rootOk = 'Mod', 'Art', 'Source', 'Tests', 'Docs', 'Build', '.github', '.git', '.claude', 'STATUS.md', 'README.md', 'ATTRIBUTION.md', 'CHANGELOG.md', 'LICENSE', 'TESTING.md', 'PUBLICATION.md', 'FRENCH_REVIEW.md', 'BACKLOG.md', 'mod.json', '.gitignore', '.gitattributes', 'desktop.ini'
$artOk = 'Preview-source.png', 'ModIcon-source.png', 'echo-source.png', 'echo-preview.png', 'echo-concept.png', 'Preview.config.json', 'Preview.ico', 'ModIcon.ico', 'Gallery', 'Gallery-clean', '.render', 'desktop.ini'
$listed = $null
if (Test-Path (Join-Path $ModRoot '.git')) {
  $listed = @(& git -C $ModRoot -c core.quotepath=off ls-files --cached --others --exclude-standard 2>$null)
  if ($LASTEXITCODE -ne 0) { $listed = $null }
}
if ($listed) {
  $top = $listed | ForEach-Object { ($_ -split '/')[0] } | Sort-Object -Unique
  foreach ($t in $top) {
    if ($rootOk -contains $t) { continue }
    if ($t -like 'PROMPT_*.md') { $notes.Add("root file $t exists only while the illustration is made (2.f)"); continue }
    $warnings.Add("root entry '$t' is not on the closed list (STYLE_RIMWORLD.md): move it to Docs/ or Tests/, or ask Audit")
  }
  $art = $listed | Where-Object { $_ -like 'Art/*' } | ForEach-Object { ($_ -split '/')[1] } | Sort-Object -Unique
  foreach ($a in $art) { if ($artOk -notcontains $a) { $warnings.Add("Art/$a is not in the closed Art/ set (STYLE_RIMWORLD.md)") } }
}

foreach ($w in $notes) { Write-Host "NOTE: $w" -ForegroundColor Cyan }
foreach ($w in $warnings) { Write-Host "WARN: $w" -ForegroundColor Yellow }
foreach ($f in $findings) { Write-Host $f -ForegroundColor Red }
if ($findings.Count) { Write-Host "FAIL: $($findings.Count) finding(s)" -ForegroundColor Red; exit 1 }
Write-Host "PASS: $($files.Count) XML files, $($seen.Count) defs, About.xml, notices and images checked."
exit 0
