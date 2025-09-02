# src/wilbito/interfaces/exec.py
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import typer
from rich import print

from wilbito.executor.loop import ExecutorLoop
from wilbito.agents.council_v2 import run_council_v2

app = typer.Typer(help="Exec/DB/Council v2")

# -------------------------------------------------------------------
# Paths & DB helpers
# -------------------------------------------------------------------
def repo_root() -> Path:
    return Path(os.getcwd()).resolve()

def db_path() -> Path:
    return repo_root() / "memoria" / "db" / "wilbito.db"

def ensure_parent(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)

def _echo_json(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=4))

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    meta_json TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    step_id TEXT,
    command TEXT,
    args_json TEXT,
    started_at TEXT,
    finished_at TEXT,
    status TEXT,
    result_json TEXT,
    error TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id)
);
CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    task_id INTEGER,
    path TEXT,
    kind TEXT,
    bytes INTEGER,
    meta_json TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    task_id INTEGER,
    level TEXT,
    message TEXT,
    data_json TEXT,
    created_at TEXT,
    FOREIGN KEY(run_id) REFERENCES runs(id),
    FOREIGN KEY(task_id) REFERENCES tasks(id)
);
"""

def db_connect() -> sqlite3.Connection:
    p = db_path()
    ensure_parent(p)
    conn = sqlite3.connect(p.as_posix())
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def db_init() -> None:
    conn = db_connect()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()

# -------------------------------------------------------------------
# Commands
# -------------------------------------------------------------------
@app.command("db-init")
def db_init_cmd():
    """
    Crea (si no existe) memoria/db/wilbito.db con tablas runs/tasks/artifacts/events
    """
    ensure_parent(db_path())
    db_init()
    _echo_json({"ok": True, "db": db_path().as_posix()})

@app.command("db-stats")
def db_stats_cmd():
    """
    Cuenta filas por tabla.
    """
    ensure_parent(db_path())
    db_init()
    conn = db_connect()
    try:
        def count(tab):
            try:
                return conn.execute(f"SELECT COUNT(*) FROM {tab}").fetchone()[0]
            except Exception:
                return 0
        stats = {
            "runs": count("runs"),
            "tasks": count("tasks"),
            "artifacts": count("artifacts"),
            "events": count("events"),
        }
        _echo_json({"ok": True, "db": db_path().as_posix(), "stats": stats})
    finally:
        conn.close()

@app.command("executor-run")
def executor_run_cmd(
    commands: str = typer.Option(..., help="Ruta a config/commands.json"),
    rollback: Optional[str] = typer.Option(None, help="Ruta a config/rollback.json"),
    run_name: Optional[str] = typer.Option(None, help="Nombre del run (opcional)")
):
    """
    Ejecuta una lista secuencial de comandos (JSON) con logging en DB y manejo de rollback.
    """
    ensure_parent(db_path())
    db_init()
    loop = ExecutorLoop(db_path=db_path().as_posix())
    res = loop.run(commands_path=commands, rollback_path=rollback, run_name=run_name)
    _echo_json(res)

@app.command("council-v2")
def council_v2_cmd(
    objetivo: str = typer.Argument(...),
    use_context: bool = typer.Option(False, help="(Opcional) integrar RAG con mem-search"),
    top_k: int = typer.Option(5, help="Resultados de memoria"),
    rag_tag: Optional[str] = typer.Option(None, help="Tag preferente (codegen|marketing|trading)"),
    min_score: float = typer.Option(0.0, help="Score mínimo")
):
    """
    Invoca el consejo v2, guarda eventos en DB, y devuelve un dict con RFC + research + plan.
    """
    ensure_parent(db_path())
    db_init()
    result = run_council_v2(
        objetivo=objetivo,
        db_path=db_path().as_posix(),
        use_context=use_context,
        top_k=top_k,
        rag_tag=rag_tag,
        min_score=min_score,
    )
    _echo_json(result)

if __name__ == "__main__":
    app()
