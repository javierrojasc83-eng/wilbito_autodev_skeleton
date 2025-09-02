param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $projectRoot
try {
  $env:PYTHONPATH = (Resolve-Path .\src).Path
  python -m wilbito.interfaces.exec @Args
} finally {
  Pop-Location
}
