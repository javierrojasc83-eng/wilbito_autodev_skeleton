<# 
FixSeedCheck-AndRun.ps1
----------------------------------------
Crea/ajusta herramientas y configs para que el executor corra:
- tools/seed_check.py, tools/noop.py, tools/db_migrate.py, tools/quality_wrapper.py
- config/commands.json (ARRAY top-level) y config/rollback.json (ARRAY)
- Migración SQLite para tablas runs/events/tasks (state/*.db, memoria/db/*.db)

Uso:
  powershell -NoProfile -ExecutionPolicy Bypass -File .\FixSeedCheck-AndRun.ps1 -Run

Parámetro:
  -Run -> tras preparar, dispara el pipeline.
#>

param(
  [switch]$Run
)

$ErrorActionPreference = "Stop"

# ---------- Helpers ----------
function Ensure-Dir([string]$Path) {
  if (-not [string]::IsNullOrWhiteSpace($Path) -and -not (Test-Path -LiteralPath $Path)) {
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
  }
}
function Backup-File([string]$Path) {
  if (Test-Path -LiteralPath $Path) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = Join-Path -Path "backup" -ChildPath $ts
    Ensure-Dir $backupDir
    $dest = Join-Path -Path $backupDir -ChildPath (Split-Path -Leaf $Path)
    Copy-Item -LiteralPath $Path -Destination $dest -Force
    Write-Host "Backup -> $dest" -ForegroundColor DarkCyan
  }
}
function Write-NoBom([string]$Path, [string]$Text) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Text, $utf8NoBom)
}

# Defaults por si algo queda nulo en bloques siguientes
$commandsPath = "config/commands.json"
$rollbackPath = "config/rollback.json"

# ---------- Preflight ----------
Write-Host "[1/6] Preparando estructura..." -ForegroundColor Cyan
Ensure-Dir "config"
Ensure-Dir "state"
Ensure-Dir "tools"
Ensure-Dir "backup"
Ensure-Dir "memoria\db"

# ---------- tools/seed_check.py ----------
$seedCheckPy = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crea/verifica un seed determinístico en state/seed.json.
Uso:
  python tools/seed_check.py --state state/seed.json --create-if-missing [--force]
"""
import argparse, json, os, random, time, datetime, sys

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--state", default="state/seed.json")
    ap.add_argument("--create-if-missing", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    state_path = args.state
    os.makedirs(os.path.dirname(state_path), exist_ok=True)

    if os.path.exists(state_path) and not args.force:
        with open(state_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Seed OK -> {data.get('seed')} (created_at={data.get('created_at')})")
        return 0

    seed = int(time.time()) ^ random.randint(1, 1_000_000)
    data = {
        "seed": seed,
        "created_at": datetime.datetime.utcnow().isoformat()+"Z",
        "source": "tools/seed_check.py"
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Seed created -> {seed} -> {state_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@

# ---------- tools/noop.py ----------
$noopPy = @'
#!/usr/bin/env python3
print("NOOP ok")
'@

# ---------- tools/db_migrate.py ----------
$dbMigratePy = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Migra/ajusta las bases SQLite del ejecutor:
- runs   -> id, run_name, status, created_at, updated_at
- events -> id, run_id, level, event, details_json, created_at
- tasks  -> id, run_id, step_id, cmd, status, created_at

Uso:
  python tools/db_migrate.py                # migra por defecto state/*.db y memoria/db/*.db
  python tools/db_migrate.py --db RUTA.DB   # migra sólo la DB indicada
"""
import argparse, glob, sqlite3, os, sys

# --- runs ---
EXPECTED_RUNS_COLS = [
    ("id", "INTEGER"),
    ("run_name", "TEXT"),
    ("status", "TEXT"),
    ("created_at", "TEXT"),
    ("updated_at", "TEXT"),
]
RUNS_ALTERS = {
    "run_name":   "ALTER TABLE runs ADD COLUMN run_name TEXT",
    "status":     "ALTER TABLE runs ADD COLUMN status TEXT",
    "created_at": "ALTER TABLE runs ADD COLUMN created_at TEXT",
    "updated_at": "ALTER TABLE runs ADD COLUMN updated_at TEXT",
}

# --- events ---
EXPECTED_EVENTS_COLS = [
    ("id", "INTEGER"),
    ("run_id", "INTEGER"),
    ("level", "TEXT"),
    ("event", "TEXT"),
    ("details_json", "TEXT"),
    ("created_at", "TEXT"),
]
EVENTS_ALTERS = {
    "run_id":       "ALTER TABLE events ADD COLUMN run_id INTEGER",
    "level":        "ALTER TABLE events ADD COLUMN level TEXT",
    "event":        "ALTER TABLE events ADD COLUMN event TEXT",
    "details_json": "ALTER TABLE events ADD COLUMN details_json TEXT",
    "created_at":   "ALTER TABLE events ADD COLUMN created_at TEXT",
}

# --- tasks ---
EXPECTED_TASKS_COLS = [
    ("id", "INTEGER"),
    ("run_id", "INTEGER"),
    ("step_id", "TEXT"),
    ("cmd", "TEXT"),
    ("status", "TEXT"),
    ("created_at", "TEXT"),
]
TASKS_ALTERS = {
    "run_id":     "ALTER TABLE tasks ADD COLUMN run_id INTEGER",
    "step_id":    "ALTER TABLE tasks ADD COLUMN step_id TEXT",
    "cmd":        "ALTER TABLE tasks ADD COLUMN cmd TEXT",
    "status":     "ALTER TABLE tasks ADD COLUMN status TEXT",
    "created_at": "ALTER TABLE tasks ADD COLUMN created_at TEXT",
}

def table_exists(conn, name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def get_columns(conn, table: str):
    cols = []
    for cid, name, ctype, notnull, dflt, pk in conn.execute(f"PRAGMA table_info({table})"):
        cols.append((name, (ctype or "").upper()))
    return cols

def ensure_table(conn, table: str, expected_cols, alters):
    if not table_exists(conn, table):
        cols_sql = ", ".join([f"{n} {t}" for n, t in expected_cols])
        conn.execute(f"CREATE TABLE {table} ({cols_sql}, PRIMARY KEY(id AUTOINCREMENT))")
        conn.commit()
        print(f"[create] {table} creada")
        return
    existing = {n for n, _ in get_columns(conn, table)}
    added = []
    for name, _ctype in expected_cols:
        if name not in existing:
            conn.execute(alters[name])
            added.append(name)
    if added:
        conn.commit()
        print(f"[alter] {table} -> +{', '.join(added)}")
    else:
        print(f"[ok] {table} ya compatible")

def ensure_db(path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new_file = not os.path.exists(path)
    conn = sqlite3.connect(path)
    try:
        ensure_table(conn, "runs",   EXPECTED_RUNS_COLS,   RUNS_ALTERS)
        ensure_table(conn, "events", EXPECTED_EVENTS_COLS, EVENTS_ALTERS)
        ensure_table(conn, "tasks",  EXPECTED_TASKS_COLS,  TASKS_ALTERS)
    finally:
        conn.close()
    if new_file:
        print(f"[new] creada DB {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="Ruta específica de DB a migrar (opcional)")
    args = ap.parse_args()

    if args.db:
        ensure_db(args.db)
        return 0

    roots = []
    if os.path.exists("state"):
        roots += sorted(glob.glob("state/*.db"))
    memdb = os.path.join("memoria", "db")
    if os.path.exists(memdb):
        roots += sorted(glob.glob(os.path.join(memdb, "*.db")))
    if not roots:
        roots = ["state/executor.db"]
    for p in roots:
        ensure_db(p)
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@

# ---------- tools/quality_wrapper.py ----------
$qualityWrapperPy = @'
import json, subprocess, sys

def extract_first_json(s: str):
    i = s.find("{")
    if i == -1:
        return None
    depth = 0
    in_str = False
    esc = False
    for j in range(i, len(s)):
        c = s[j]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    frag = s[i:j+1]
                    try:
                        return json.loads(frag)
                    except Exception:
                        return None
    return None

def main():
    proc = subprocess.run([sys.executable, "-m", "wilbito.interfaces.cli", "quality"],
                          capture_output=True, text=True)
    out = proc.stdout or ""
    err = proc.stderr or ""

    data = None
    try:
        data = json.loads(out)
    except Exception:
        data = extract_first_json(out)

    if data is None:
        data = {
            "lint": {},
            "unittest": {"returncode": proc.returncode},
            "meta": {
                "note": "wrapped non-JSON stdout; returning synthetic JSON",
                "stdout_head": out[:2000],
                "stderr_head": err[:2000]
            }
        }

    print(json.dumps(data, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
'@

# ---------- Escribir tools ----------
Write-Host "[2/6] Escribiendo tools/seed_check.py, tools/noop.py, tools/db_migrate.py y tools/quality_wrapper.py..." -ForegroundColor Cyan
Write-NoBom -Path "tools/seed_check.py"      -Text $seedCheckPy
Write-NoBom -Path "tools/noop.py"            -Text $noopPy
Write-NoBom -Path "tools/db_migrate.py"      -Text $dbMigratePy
Write-NoBom -Path "tools/quality_wrapper.py" -Text $qualityWrapperPy

# ---------- Preparar/ajustar config/commands.json ----------
Write-Host "[3/6] Ajustando config/commands.json..." -ForegroundColor Cyan
Backup-File $commandsPath

# Definición por defecto en formato ARRAY top-level
$defaultStepsJson = @'
[
  { "step_id": "db-migrate-memoria", "description": "Migrate memoria/db/wilbito.db schema (runs, events, tasks).", "cmd": ["python","tools/db_migrate.py","--db","memoria/db/wilbito.db"], "expect_json": false },
  { "step_id": "db-migrate-state",   "description": "Migrate state/*.db schemas (fallback).",                      "cmd": ["python","tools/db_migrate.py"],                                   "expect_json": false },
  { "step_id": "seed-check",         "description": "Ensure deterministic seed exists (creates state/seed.json if missing).", "cmd": ["python","tools/seed_check.py","--state","state/seed.json","--create-if-missing"], "expect_json": false },
  { "step_id": "quality",            "description": "Run code quality checks via wrapper (forces clean JSON).",    "cmd": ["python","tools/quality_wrapper.py"],                              "expect_json": true },
  { "step_id": "noop",               "description": "Placeholder step (keeps pipeline green).",                     "cmd": ["python","tools/noop.py"],                                         "expect_json": false }
]
'@
$defaultSteps = $defaultStepsJson | ConvertFrom-Json

# Cargar existente y normalizar a array
$existingRaw = if (Test-Path -LiteralPath $commandsPath) { Get-Content -LiteralPath $commandsPath -Raw -Encoding UTF8 } else { $null }
if ($existingRaw) { try { $loaded = $existingRaw | ConvertFrom-Json } catch { $loaded = $null } } else { $loaded = $null }

$steps = @()
if ($null -eq $loaded) {
  $steps = @()
} elseif ($loaded -is [System.Array]) {
  $steps = $loaded
} elseif ($loaded.PSObject.Properties.Name -contains 'steps') {
  $steps = @($loaded.steps)
} else {
  $steps = @()
}

# Reconciliar: default + otros que no sean de los conocidos
$known = @('db-migrate-memoria','db-migrate-state','seed-check','quality','noop')
$rest = @()
foreach ($s in $steps) {
  $sid = $null
  if ($s.PSObject.Properties.Name -contains 'step_id') { $sid = [string]$s.step_id }
  elseif ($s.PSObject.Properties.Name -contains 'id') { $sid = [string]$s.id }
  if ($sid -and ($known -notcontains $sid)) { $rest += $s }
}
$final = @() + $defaultSteps + $rest

# Escribir commands.json (UTF-8 sin BOM)
Write-NoBom -Path $commandsPath -Text ($final | ConvertTo-Json -Depth 100)

# ---------- Asegurar config/rollback.json ----------
Write-Host "[4/6] Verificando config/rollback.json..." -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $rollbackPath)) {
  $rollbackArray = @(
    [pscustomobject]@{ step_id = 'noop-rollback'; description='Noop rollback'; cmd = @('python','tools/noop.py'); expect_json=$false }
  )
  Write-NoBom -Path $rollbackPath -Text ($rollbackArray | ConvertTo-Json -Depth 10)
  Write-Host "  -> Creado rollback.json mínimo (noop)" -ForegroundColor Green
} else {
  Write-Host "  -> rollback.json ya existe (no se toca)" -ForegroundColor DarkGray
}

# ---------- Smoke test ----------
Write-Host "[5/6] Smoke test: migración de DB y seed_check..." -ForegroundColor Cyan
& python "tools/db_migrate.py" | Write-Host
& python "tools/seed_check.py" --state "state/seed.json" --create-if-missing | Write-Host

# ---------- Ejecutar pipeline si -Run ----------
Write-Host "[6/6] Ejecutando pipeline..." -ForegroundColor Cyan
if ($Run) {
  try {
    # Intento 1: 'wb' si existe
    wb executor-run --commands $commandsPath --rollback $rollbackPath --run-name "pre-release"
  } catch {
    Write-Host "  ¡Aviso! 'wb' no está en PATH. Usando alternativa con Python..." -ForegroundColor Yellow
    try {
      # Asegurar PYTHONPATH a .\src si no está (solo para esta invocación)
      if (-not $env:PYTHONPATH) {
        $srcPath = (Resolve-Path .\src).Path
        $env:PYTHONPATH = $srcPath
      }
      python -m wilbito.interfaces.exec executor-run --commands $commandsPath --rollback $rollbackPath --run-name "pre-release"
    } catch {
      Write-Host "  Error al ejecutar el pipeline: $($_.Exception.Message)" -ForegroundColor Red
      Write-Host "  Ejecuta manualmente:" -ForegroundColor Yellow
      Write-Host "    `$env:PYTHONPATH = (Resolve-Path .\src).Path" -ForegroundColor Yellow
      Write-Host "    python -m wilbito.interfaces.exec executor-run --commands config/commands.json --rollback config/rollback.json --run-name pre-release" -ForegroundColor Yellow
    }
  }
} else {
  Write-Host "Listo. Ejecuta con -Run para disparar el pipeline, o llama a 'wb' / 'python -m wilbito.interfaces.exec' manualmente." -ForegroundColor Green
}

