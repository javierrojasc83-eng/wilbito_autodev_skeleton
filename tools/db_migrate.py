#!/usr/bin/env python3
"""
Migra/ajusta las bases SQLite del ejecutor:
- runs   -> id, run_name, status, created_at, updated_at
- events -> id, run_id, level, event, details_json, created_at
- tasks  -> id, run_id, step_id, cmd, status, created_at

Uso:
  python tools/db_migrate.py                # migra por defecto state/*.db y memoria/db/*.db
  python tools/db_migrate.py --db RUTA.DB   # migra sÃ³lo la DB indicada
"""

import argparse
import glob
import os
import sqlite3
import sys

# --- runs ---
EXPECTED_RUNS_COLS = [
    ("id", "INTEGER"),
    ("run_name", "TEXT"),
    ("status", "TEXT"),
    ("created_at", "TEXT"),
    ("updated_at", "TEXT"),
]
RUNS_ALTERS = {
    "run_name": "ALTER TABLE runs ADD COLUMN run_name TEXT",
    "status": "ALTER TABLE runs ADD COLUMN status TEXT",
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
    "run_id": "ALTER TABLE events ADD COLUMN run_id INTEGER",
    "level": "ALTER TABLE events ADD COLUMN level TEXT",
    "event": "ALTER TABLE events ADD COLUMN event TEXT",
    "details_json": "ALTER TABLE events ADD COLUMN details_json TEXT",
    "created_at": "ALTER TABLE events ADD COLUMN created_at TEXT",
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
    "run_id": "ALTER TABLE tasks ADD COLUMN run_id INTEGER",
    "step_id": "ALTER TABLE tasks ADD COLUMN step_id TEXT",
    "cmd": "ALTER TABLE tasks ADD COLUMN cmd TEXT",
    "status": "ALTER TABLE tasks ADD COLUMN status TEXT",
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
        ensure_table(conn, "runs", EXPECTED_RUNS_COLS, RUNS_ALTERS)
        ensure_table(conn, "events", EXPECTED_EVENTS_COLS, EVENTS_ALTERS)
        ensure_table(conn, "tasks", EXPECTED_TASKS_COLS, TASKS_ALTERS)
    finally:
        conn.close()
    if new_file:
        print(f"[new] creada DB {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="Ruta especÃ­fica de DB a migrar (opcional)")
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
