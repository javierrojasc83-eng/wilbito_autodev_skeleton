from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, Optional

DEFAULT_DB = Path("memoria") / "db" / "wilbito.db"


def _ts() -> str:
    return datetime.utcnow().isoformat()


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    p = Path(db_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str | Path = DEFAULT_DB) -> str:
    conn = connect(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS runs (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      objetivo TEXT NOT NULL,
      started_at TEXT NOT NULL,
      finished_at TEXT,
      status TEXT
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id INTEGER NOT NULL,
      step INTEGER NOT NULL,
      name TEXT NOT NULL,
      status TEXT,
      detail TEXT,
      created_at TEXT NOT NULL,
      FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS artifacts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id INTEGER NOT NULL,
      path TEXT NOT NULL,
      created_at TEXT NOT NULL,
      FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS events (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      run_id INTEGER NOT NULL,
      ts TEXT NOT NULL,
      kind TEXT NOT NULL,
      payload TEXT,
      FOREIGN KEY (run_id) REFERENCES runs(id)
    )""")

    conn.commit()
    conn.close()
    return str(Path(db_path).resolve().as_posix())


def start_run(objetivo: str, db_path: str | Path = DEFAULT_DB) -> int:
    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO runs (objetivo, started_at, status) VALUES (?, ?, ?)",
        (objetivo, _ts(), "running"),
    )
    run_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(run_id)


def finish_run(run_id: int, status: str = "ok", db_path: str | Path = DEFAULT_DB) -> None:
    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "UPDATE runs SET finished_at = ?, status = ? WHERE id = ?",
        (_ts(), status, run_id),
    )
    conn.commit()
    conn.close()


def log_task(run_id: int, step: int, name: str, status: str, detail: Dict[str, Any] | None,
             db_path: str | Path = DEFAULT_DB) -> int:
    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tasks (run_id, step, name, status, detail, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, step, name, status, json.dumps(detail or {}, ensure_ascii=False), _ts()),
    )
    task_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(task_id)


def log_event(run_id: int, kind: str, payload: Dict[str, Any] | None,
              db_path: str | Path = DEFAULT_DB) -> int:
    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO events (run_id, ts, kind, payload) VALUES (?, ?, ?, ?)",
        (run_id, _ts(), kind, json.dumps(payload or {}, ensure_ascii=False)),
    )
    ev_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(ev_id)


def add_artifact(run_id: int, rel_path: str, content: str,
                 db_path: str | Path = DEFAULT_DB) -> int:
    path = Path(rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    conn = connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO artifacts (run_id, path, created_at) VALUES (?, ?, ?)",
        (run_id, str(path.as_posix()), _ts()),
    )
    art_id = cur.lastrowid
    conn.commit()
    conn.close()
    return int(art_id)


def stats(db_path: str | Path = DEFAULT_DB) -> Dict[str, Any]:
    conn = connect(db_path)
    cur = conn.cursor()
    out: Dict[str, Any] = {}
    for table in ("runs", "tasks", "artifacts", "events"):
        cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
        out[table] = cur.fetchone()["n"]
    conn.close()
    return out
