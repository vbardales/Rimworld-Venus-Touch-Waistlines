<#
  Shared offline interpreter of RimWorld PatchOperations, for test scripts.

    . (Join-Path $Protocols 'scripts\lib\PatchEngine.ps1')
    Invoke-PatchOperation $op $doc -ActiveMods @('Some mod name') -RequireMatch

  Runs one <Operation> element against an XmlDocument. Classes: Sequence, FindMod, Conditional,
  Add (order Prepend or Append), Replace, Remove, AddModExtension, AttributeSet, AttributeAdd,
  AttributeRemove. Any other class throws: a
  silent skip would make a test pass on a patch it never ran. MayRequire is not read.

  -ActiveMods  names matched by PatchOperationFindMod (the mod's <name> or packageId, as the patch writes it).
  -RequireMatch  an xpath matching zero nodes throws, unless the operation says success=Always.
                 Without it an unmatched operation is skipped, as RimWorld does.
  -OnChange    scriptblock called per node touched with ($class, $xpath, $oldXml, $newXml), for reports.

  A mod whose own CI runs the test carries a vendored copy at Tests/lib/PatchEngine.ps1, written
  only by scripts/Sync-PatchEngine.ps1 (never edit the copy). Edit this file, then sync.

  Not a RimWorld patch engine: a fixture or the real target defs go in, the XML that comes out is what
  the test asserts. Game loading, inheritance and Harmony patches need RimWorld.
#>

function Get-PatchText($Op, [string]$Child) { $n = $Op.SelectSingleNode($Child); if ($n) { $n.InnerText.Trim() } else { $null } }
function Select-PatchNodes($Doc, [string]$XPath) { return @($Doc.SelectNodes($XPath)) }

function Invoke-PatchOperation {
  param($Op, $Doc, [string[]]$ActiveMods = @(), [switch]$RequireMatch, [scriptblock]$OnChange)
  $class = $Op.GetAttribute('Class')
  $xpath = if ($Op.SelectSingleNode('xpath')) { $Op.SelectSingleNode('xpath').InnerText } else { $null }
  $sub = @{ ActiveMods = $ActiveMods; RequireMatch = $RequireMatch; OnChange = $OnChange }
  switch ($class) {
    'PatchOperationSequence' {
      foreach ($child in $Op.SelectNodes('operations/li')) { Invoke-PatchOperation $child $Doc @sub }
      return
    }
    'PatchOperationFindMod' {
      $hit = $false
      foreach ($m in $Op.SelectNodes('mods/li')) { if ($ActiveMods -contains $m.InnerText.Trim()) { $hit = $true } }
      $next = $Op.SelectSingleNode($(if ($hit) { 'match' } else { 'nomatch' }))
      if ($next) { Invoke-PatchOperation $next $Doc @sub }
      return
    }
    'PatchOperationConditional' {
      $hit = @(Select-PatchNodes $Doc $xpath).Count -gt 0
      $next = $Op.SelectSingleNode($(if ($hit) { 'match' } else { 'nomatch' }))
      if ($next) { Invoke-PatchOperation $next $Doc @sub }
      return
    }
    { $_ -in 'PatchOperationAdd', 'PatchOperationReplace', 'PatchOperationRemove', 'PatchOperationAddModExtension', 'PatchOperationAttributeSet', 'PatchOperationAttributeAdd', 'PatchOperationAttributeRemove' } { }
    default { throw "PatchEngine has no interpreter for $class (xpath $xpath): extend scripts/lib/PatchEngine.ps1 before trusting a result." }
  }
  $nodes = @(Select-PatchNodes $Doc $xpath)
  if ($nodes.Count -eq 0) {
    if ($RequireMatch -and (Get-PatchText $Op 'success') -ne 'Always') {
      throw "Unmatched XPath: $xpath"
    }
    return
  }
  $values = @($Op.SelectNodes('value/*'))
  foreach ($node in $nodes) {
    $old = $node.OuterXml
    switch ($class) {
      'PatchOperationAdd' {
        $prepend = (Get-PatchText $Op 'order') -eq 'Prepend'
        foreach ($v in $values) {
          $imp = $Doc.ImportNode($v, $true)
          if ($prepend -and $node.FirstChild) { [void]$node.InsertBefore($imp, $node.FirstChild) } else { [void]$node.AppendChild($imp) }
        }
        $new = $node.OuterXml
      }
      'PatchOperationReplace' {
        $anchor = $node
        foreach ($v in $values) {
          $imp = $Doc.ImportNode($v, $true)
          if ($anchor -eq $node) { [void]$node.ParentNode.ReplaceChild($imp, $node) } else { [void]$anchor.ParentNode.InsertAfter($imp, $anchor) }
          $anchor = $imp
        }
        $new = ($values | ForEach-Object { $_.OuterXml }) -join ''
      }
      'PatchOperationRemove' {
        [void]$node.ParentNode.RemoveChild($node)
        $new = $null
      }
      { $_ -in 'PatchOperationAttributeSet', 'PatchOperationAttributeAdd', 'PatchOperationAttributeRemove' } {
        # <attribute> names the attribute, <value> its text. Set: write it, creating it when missing.
        # Add: write it only when the node does not carry it yet. Remove: delete it (no <value>).
        $attr = Get-PatchText $Op 'attribute'
        if (-not $attr) { throw "$class has no <attribute> (xpath $xpath)" }
        if ($class -eq 'PatchOperationAttributeRemove') {
          [void]$node.RemoveAttribute($attr)
        } else {
          $val = Get-PatchText $Op 'value'
          if ($null -eq $val) { throw "$class has no <value> (xpath $xpath)" }
          if ($class -eq 'PatchOperationAttributeSet' -or -not $node.HasAttribute($attr)) { $node.SetAttribute($attr, $val) }
        }
        $new = $node.OuterXml
      }
      'PatchOperationAddModExtension' {
        $ext = $node.SelectSingleNode('modExtensions')
        if (-not $ext) { $ext = $Doc.CreateElement('modExtensions'); [void]$node.AppendChild($ext) }
        foreach ($v in $values) { [void]$ext.AppendChild($Doc.ImportNode($v, $true)) }
        $new = $ext.OuterXml
      }
    }
    if ($OnChange) { & $OnChange $class $xpath $old $new }
  }
}

function Invoke-PatchFile {
  param([string]$Path, $Doc, [string[]]$ActiveMods = @(), [switch]$RequireMatch, [scriptblock]$OnChange)
  $patch = New-Object System.Xml.XmlDocument
  $patch.Load($Path)
  foreach ($op in $patch.SelectNodes('/Patch/Operation')) {
    Invoke-PatchOperation $op $Doc -ActiveMods $ActiveMods -RequireMatch:$RequireMatch -OnChange $OnChange
  }
}
