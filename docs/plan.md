# Plan: DB + Council v2 + Executor Loop

## Objetivo
Estandarizar la ejecución de pipelines (commands.json) con logging duradero en SQLite y un Council v2 que produzca decisiones auditablemente.

## Arquitectura (texto)
- **Executor Loop**: lee `config/commands.json`, ejecuta los pasos usando `wilbito.interfaces.cli`, loguea en `memoria/db/wilbito.db`.
- **Rollback**: `config/rollback.json` define acciones ante fallas (retry|abort|log).
- **Council v2**: genera RFC + research + plan, opcionalmente integra RAG (mem-search) y persiste eventos.

## Tablas (SQLite)
- `runs(id, name, started_at, finished_at, status, meta_json)`
- `tasks(id, run_id, step_id, command, args_json, started_at, finished_at, status, result_json, error)`
- `artifacts(id, run_id, task_id, path, kind, bytes, meta_json, created_at)`
- `events(id, run_id, task_id, level, message, data_json, created_at)`

## Comandos
```powershell
wb db-init
wb db-stats
wb executor-run --commands config/commands.json --rollback config/rollback.json --run-name "smoke"
wb council-v2 "plan de marketing 30 días" --use-context --rag-tag marketing --top-k 5 --min-score 0.1
wb db-stats
