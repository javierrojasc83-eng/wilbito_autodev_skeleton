param(
  [int]$Iterations = 3,
  [switch]$StopOnFail
)
$env:PYTHONPATH = (Resolve-Path .\src).Path
$flags = @("--iterations", $Iterations.ToString())
if ($StopOnFail) { $flags += "--stop-on-fail" }
python tools\autodev_loop.py @flags
