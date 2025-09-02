param(
  [ValidateSet("patch","minor","major")]
  [string]$Bump = "patch"
)

$ErrorActionPreference = "Stop"

function Show-Step($title) {
  Write-Host "== $title ==" -ForegroundColor Cyan
}

function WB-Json {
  param([Parameter(Mandatory, ValueFromRemainingArguments=$true)][string[]]$CmdArgs)
  # Ejecuta wb con los args y captura stdout como string
  $raw = & wb @CmdArgs | Out-String
  if (-not $raw -or ($raw.Trim() -eq "")) {
    throw "wb $($CmdArgs -join ' ') no devolvió salida."
  }
  try {
    return $raw | ConvertFrom-Json
  } catch {
    Write-Host $raw
    throw "Salida no-JSON de: wb $($CmdArgs -join ' ')"
  }
}

# 1) QUALITY
Show-Step "QUALITY"
$quality = WB-Json quality
$unit = $quality.lint.unittest
if ($null -eq $unit) {
  throw "Quality: no encontré sección unittest en el JSON."
}
if ($unit.returncode -ne 0) {
  Write-Host ($quality | ConvertTo-Json -Depth 8)
  throw "Quality/tests no pasaron (unittest.returncode=$($unit.returncode)). Abortando release."
}
Write-Host "Quality OK (unittest)" -ForegroundColor Green

# 2) MEM SEARCH SMOKE (no bloqueante, solo aviso si vacío)
Show-Step "MEM SEARCH SMOKE"
$ms1 = WB-Json mem-search "regresión codegen" --rag-tag codegen --min-score 0.1 --top-k 3
$ms2 = WB-Json mem-search "marketing 30 días" --rag-tag marketing --min-score 0.1 --top-k 3
if (($ms1.results.Count -lt 1) -or ($ms2.results.Count -lt 1)) {
  Write-Warning "Alguna búsqueda devolvió 0 resultados. Revisá seeds/memoria."
} else {
  Write-Host "RAG smoke OK" -ForegroundColor Green
}

# 3) AUTODEV/COUNCIL SMOKE (solo validar que devuelven JSON)
Show-Step "AUTODEV/COUNCIL SMOKE"
$ad = WB-Json autodev "mejorar robustez de codegen" --use-context --rag-tag codegen --min-score 0.1 --top-k 3
$co = WB-Json council "plan de marketing 30 días" --granularity fine --use-context --rag-tag marketing --min-score 0.1 --top-k 3
Write-Host "Autodev/Council OK" -ForegroundColor Green

# 4) MEM BACKUP
Show-Step "MEM BACKUP"
$bk = WB-Json mem-backup
if (-not $bk.ok) { throw "mem-backup falló: $($bk | ConvertTo-Json -Depth 6)" }
Write-Host "Backup OK -> $($bk.backup)" -ForegroundColor Green

# 5) RELEASE
Show-Step "RELEASE"
$rel = WB-Json release --bump $Bump
Write-Host "Release $($rel.version)" -ForegroundColor Green
Write-Host "ZIP: $($rel.zip)"
Write-Host "CHANGELOG: $($rel.changelog)"

Write-Host "Pre-release OK" -ForegroundColor Green
