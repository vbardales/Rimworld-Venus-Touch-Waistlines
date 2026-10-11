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
    5. ATTRIBUTION.md and LICENSE, when present both at the repo root and in Mod/, are byte-identical.
    6. Mod/About/Preview.png and ModIcon.png exist and are PNG files; Preview.png is under 1 MiB.
    7. Mod/About/PublishedFileId.txt, when present, holds digits only (and, with -OriginalWorkshopId, not that id).

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
  if ((Test-Path $a) -and (Test-Path $b) -and ((Get-FileHash $a).Hash -ne (Get-FileHash $b).Hash)) { Find "$n differs between the repo root and Mod/" }
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

foreach ($f in $findings) { Write-Host $f -ForegroundColor Red }
if ($findings.Count) { Write-Host "FAIL: $($findings.Count) finding(s)" -ForegroundColor Red; exit 1 }
Write-Host "PASS: $($files.Count) XML files, $($seen.Count) defs, About.xml, notices and images checked."
exit 0
