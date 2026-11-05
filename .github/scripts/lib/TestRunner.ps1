<#
.SYNOPSIS
  Dot-sourced library: the small test runner the per-mod Run-Functional-Tests.ps1 copies each wrote.

.DESCRIPTION
  Test-That "name" { ...returns $true, or 'skip' ... }   one numbered line, ok / FAIL / SKIP; an exception is a FAIL with its message
  Note "text"                                            a grey detail line under the last test
  Complete-Tests                                         prints the totals and exits 1 when anything failed, 0 otherwise

  It "name" { 'problem one'; 'problem two' }            the block returns the problems; nothing returned = pass (lists every faulty element)

  Trap (seen by DalmatiansRenew): the block is run in the caller's dynamic scope. The parameters are named $TrName and $TrBody so that a
  caller's own $body or $name is not shadowed; a wrapper that calls its own $body from inside a block passed here must use
  .GetNewClosure() or another name.

  A test that returns nothing or $false fails: write negative tests so that they cannot pass on empty input (count the inputs
  first), a mistake the harness cannot see for you.

    . "<protocols>\scripts\lib\TestRunner.ps1"
    Test-That 'the defs loaded' { $defs.Count -eq 5 }
    Complete-Tests
#>

$script:TRPass = 0; $script:TRFail = 0; $script:TRSkip = 0; $script:TRN = 0

# One numbered result line, and the details of a failure under it.
function Write-TestResult([string]$outcome, [string]$name, [string[]]$details = @()) {
  $script:TRN++
  switch ($outcome) {
    'pass' { $script:TRPass++; Write-Host ("  {0,2}. ok    {1}" -f $script:TRN, $name) -ForegroundColor DarkGreen }
    'skip' { $script:TRSkip++; Write-Host ("  {0,2}. SKIP  {1}" -f $script:TRN, $name) -ForegroundColor DarkGray }
    default {
      $script:TRFail++
      Write-Host ("  {0,2}. FAIL  {1}" -f $script:TRN, $name) -ForegroundColor Red
      foreach ($d in $details) { Write-Host ("        {0}" -f $d) -ForegroundColor DarkRed }
    }
  }
}

function Test-That([string]$TrName, [scriptblock]$TrBody) {
  try { $r = & $TrBody } catch { Write-TestResult 'fail' $TrName @($_.Exception.GetBaseException().Message); return }
  if (($r -is [string]) -and ($r -eq 'skip')) { Write-TestResult 'skip' $TrName }
  elseif ($r) { Write-TestResult 'pass' $TrName }
  else { Write-TestResult 'fail' $TrName }
}

# A test that lists every faulty element instead of answering true/false: the block returns the PROBLEMS (strings); nothing
# returned is a pass. Each problem is printed under the failing line.
function It([string]$TrName, [scriptblock]$TrBody) {
  try { $problems = @(& $TrBody | Where-Object { $_ }) }
  catch { $problems = @("threw: $($_.Exception.GetBaseException().Message)") }
  Write-TestResult $(if ($problems.Count) { 'fail' } else { 'pass' }) $TrName $problems
}

function Note([string]$text) { Write-Host ("        " + $text) -ForegroundColor DarkGray }

# Always read text with -Encoding UTF8: Windows PowerShell 5.1 reads a BOM-less file through the system code page, and a
# test looking for an accented word finds mojibake instead.
function Read-Text([string]$p) { Get-Content $p -Raw -Encoding UTF8 }

function Complete-Tests {
  Write-Host ''
  Write-Host ("{0} passed, {1} failed, {2} skipped" -f $script:TRPass, $script:TRFail, $script:TRSkip) -ForegroundColor $(if ($script:TRFail) { 'Red' } else { 'Green' })
  if ($script:TRFail) { exit 1 }
  exit 0
}
