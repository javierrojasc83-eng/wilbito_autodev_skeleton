from __future__ import annotations

import json
import sqlite3
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ----------------------------
# Utilidades de archivo / JSON
# ----------------------------


def _now_iso() -> str:
    return datetime.utcnow().replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")


def _read_json_file(path: Path) -> list[dict[str, Any]]:
    """
    Lee un archivo JSON y devuelve una lista de steps (dicts).
    Acepta tanto:
      - una lista de steps directamente
      - un objeto con clave "steps": [...]
    Lanza excepciones estándar si el archivo no existe o el JSON es inválido.
    """
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "steps" in data and isinstance(data["steps"], list):
        return data["steps"]
    raise ValueError(f"Formato de {path} inválido: debe ser lista o dict con 'steps'.")


# ----------------------------
# Esquema de base de datos
# ----------------------------

DEFAULT_DB_PATH = Path("state/executor.db")


SCHEMA_RUNS = """
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  started_at TEXT,
  finished_at TEXT,
  status TEXT,
  meta_json TEXT,
  run_name TEXT,
  created_at TEXT,
  updated_at TEXT
);
"""

SCHEMA_EVENTS = """
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  ts TEXT,
  level TEXT,
  event TEXT,
  details_json TEXT,
  created_at TEXT
);
"""

SCHEMA_TASKS = """
CREATE TABLE IF NOT EXISTS tasks(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER,
  step_id TEXT,
  cmd TEXT,
  status TEXT,
  rc INTEGER,
  started_at TEXT,
  finished_at TEXT,
  stdout TEXT,
  stderr TEXT,
  result_json TEXT
);
"""


# ----------------------------
# Tipos
# ----------------------------


@dataclass
class StepResult:
    step_id: str
    command: str
    status: str  # "ok" | "error"
    result: dict[str, Any] | None = None
    error: str | None = None


# ----------------------------
# Núcleo del executor
# ----------------------------


class ExecutorLoop:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    # ---- JSON parsing que piden los tests ----
    def _extract_first_json_obj(self, s: str) -> dict:
        """
        Devuelve el primer objeto JSON válido encontrado en s.
        Lanza ValueError si no hay JSON o si el primer bloque JSON está malformado
        o no es un objeto (dict).
        """
        if not s:
            raise ValueError("No JSON object found")

        # 1) Intento directo (puro JSON)
        try:
            obj = json.loads(s)
            if isinstance(obj, dict):
                return obj
            raise ValueError("First JSON is not an object")
        except Exception:
            pass  # seguimos a escanear bloques {...}

        # 2) Búsqueda incremental del primer bloque {...} balanceado
        i = s.find("{")
        if i == -1:
            raise ValueError("No JSON object found")

        depth = 0
        in_str = False
        esc = False
        j = i
        while j < len(s):
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
                        frag = s[i : j + 1]
                        try:
                            obj = json.loads(frag)
                            if isinstance(obj, dict):
                                return obj
                            raise ValueError("First JSON is not an object")
                        except Exception:
                            # El primer bloque {...} encontrado es malformado
                            raise ValueError("Malformed JSON in first object")
            j += 1

        # Si terminamos el scan sin cerrar, también consideramos malformado
        raise ValueError("Malformed JSON in first object (unbalanced braces)")

    # ---- DB helpers ----
    def _connect(self):
        return sqlite3.connect(str(self.db_path))

    def _ensure_schema(self):
        with self._connect() as conn:
            # Crea si no existen
            conn.execute(SCHEMA_RUNS)
            conn.execute(SCHEMA_EVENTS)
            conn.execute(SCHEMA_TASKS)

            def have_cols(table: str) -> dict:
                return {row[1]: row[2] for row in conn.execute(f"PRAGMA table_info({table})")}

            # runs: columnas requeridas
            want_runs = {
                "name": "TEXT",
                "started_at": "TEXT",
                "finished_at": "TEXT",
                "status": "TEXT",
                "meta_json": "TEXT",
                "run_name": "TEXT",
                "created_at": "TEXT",
                "updated_at": "TEXT",
            }
            cols = have_cols("runs")
            for col, typ in want_runs.items():
                if col not in cols:
                    conn.execute(f"ALTER TABLE runs ADD COLUMN {col} {typ}")

            # events: columnas requeridas
            want_events = {
                "run_id": "INTEGER",
                "ts": "TEXT",
                "level": "TEXT",
                "event": "TEXT",
                "details_json": "TEXT",
                "created_at": "TEXT",
            }
            cols = have_cols("events")
            for col, typ in want_events.items():
                if col not in cols:
                    conn.execute(f"ALTER TABLE events ADD COLUMN {col} {typ}")

            # tasks: columnas requeridas
            want_tasks = {
                "run_id": "INTEGER",
                "step_id": "TEXT",
                "cmd": "TEXT",
                "status": "TEXT",
                "rc": "INTEGER",
                "started_at": "TEXT",
                "finished_at": "TEXT",
                "stdout": "TEXT",
                "stderr": "TEXT",
                "result_json": "TEXT",
            }
            cols = have_cols("tasks")
            for col, typ in want_tasks.items():
                if col not in cols:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {typ}")

            conn.commit()

    def _insert_run(self, run_name: str) -> int:
        with self._connect() as conn:
            ts = _now_iso()
            cur = conn.execute(
                "INSERT INTO runs(name, started_at, status, meta_json, run_name, created_at, updated_at) "
                "VALUES(?, ?, ?, ?, ?, ?, ?)",
                (run_name, ts, "running", None, run_name, ts, ts),
            )
            conn.commit()
            return int(cur.lastrowid)

    def _finish_run(self, run_id: int, status: str, meta: dict[str, Any] | None = None):
        with self._connect() as conn:
            conn.execute(
                "UPDATE runs SET finished_at=?, status=?, meta_json=?, updated_at=? WHERE id=?",
                (_now_iso(), status, json.dumps(meta) if meta else None, _now_iso(), run_id),
            )
            conn.commit()

    def _event(
        self,
        level: str,
        event: str,
        details: dict[str, Any] | None = None,
        run_id: int | None = None,
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO events(run_id, ts, level, event, details_json, created_at) VALUES(?,?,?,?,?,?)",
                (run_id, _now_iso(), level, event, json.dumps(details or {}), _now_iso()),
            )
            conn.commit()

    def _record_task(
        self,
        run_id: int,
        step_id: str,
        cmd_str: str,
        status: str,
        rc: int,
        started_at: str,
        finished_at: str,
        stdout: str,
        stderr: str,
        result: dict[str, Any] | None,
    ):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO tasks(run_id, step_id, cmd, status, rc, started_at, finished_at, stdout, stderr, result_json) "
                "VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    run_id,
                    step_id,
                    cmd_str,
                    status,
                    rc,
                    started_at,
                    finished_at,
                    stdout,
                    stderr,
                    json.dumps(result) if result is not None else None,
                ),
            )
            conn.commit()

    # ---- Exec helpers ----
    def _run_command(self, cmd: Sequence[str]) -> tuple[int, str, str]:
        """
        Ejecuta un comando y devuelve (rc, stdout, stderr) como strings.
        """
        proc = subprocess.run(
            list(cmd),
            capture_output=True,
            text=True,
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""

    def _validate_json_result(
        self,
        data: dict[str, Any],
        must_have: Sequence[str] | None = None,
        fail_if_empty_fields: Sequence[str] | None = None,
    ) -> str | None:
        """
        Devuelve None si pasa las validaciones, de lo contrario un string de error.
        """
        errors = []

        if must_have:
            for key in must_have:
                if key not in data:
                    errors.append(f"Falta clave requerida '{key}'.")

        if fail_if_empty_fields:
            for key in fail_if_empty_fields:
                if key in data:
                    val = data[key]
                    if val is None:
                        errors.append(f"Campo '{key}' está vacío (None).")
                    elif isinstance(val, (list, dict, str)) and len(val) == 0:
                        errors.append(f"Campo '{key}' está vacío.")
                else:
                    errors.append(f"Campo '{key}' no encontrado.")

        if errors:
            return "; ".join(errors)
        return None

    # ----------------------------
    # API pública
    # ----------------------------
    def run(
        self,
        commands_path: str | Path,
        rollback_path: str | Path | None = None,
        run_name: str | None = None,
    ) -> dict[str, Any]:
        commands_path = Path(commands_path)
        rollback_path = Path(rollback_path) if rollback_path else None
        run_id = self._insert_run(run_name or f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}")

        self._event("info", "executor start", {"commands_path": str(commands_path)}, run_id=run_id)

        executed: list[StepResult] = []
        overall_ok = True
        rollback_info: dict[str, Any] = {"status": "skipped"}

        try:
            steps = _read_json_file(commands_path)
        except Exception as e:
            msg = f"No se pudo leer commands.json: {e}"
            self._event("error", "commands read error", {"error": msg}, run_id=run_id)
            self._finish_run(run_id, "failed", {"error": msg})
            return {
                "ok": False,
                "run_id": run_id,
                "status": "failed",
                "executed": [],
                "rollback": {"status": "skipped"},
            }

        # Ejecutar steps
        for step in steps:
            step_id = str(step.get("step_id", "step"))
            cmd: Sequence[str] = step.get("cmd") or []
            expect_json: bool = bool(step.get("expect_json"))
            must_have = step.get("must_have") or []
            fail_if_empty_fields = step.get("fail_if_empty_fields") or []

            started = _now_iso()
            rc, stdout, stderr = self._run_command(cmd)
            finished = _now_iso()

            # Construcción del resultado
            cmd_str = " ".join(cmd) if cmd else ""
            result_obj: dict[str, Any] | None = None
            step_status = "ok"
            step_err: str | None = None

            if expect_json:
                try:
                    data = self._extract_first_json_obj(stdout)
                except Exception:
                    data = None
                if data is None:
                    # No pudimos parsear JSON (o wrapper rompió JSON cuando falla)
                    step_status = "error"
                    step_err = (
                        f"Salida no JSON de {cmd}: (rc={rc})\n"
                        f"STDOUT(preview):\n{stdout[:2000]}\n\n"
                        f"STDERR(preview):\n{stderr[:2000]}"
                    )
                else:
                    # Validar contenido si corresponde
                    val_err = self._validate_json_result(data, must_have, fail_if_empty_fields)
                    if val_err:
                        step_status = "error"
                        step_err = f"JSON inválido: {val_err}"
                    else:
                        result_obj = data
                        # Si el proceso devolvió rc != 0 aun con JSON, consideramos error.
                        if rc != 0:
                            step_status = "error"
                            step_err = f"Comando devolvió rc={rc} con JSON. STDERR(preview):\n{stderr[:2000]}"
            else:
                # No espera JSON: rc distinto de 0 es fallo.
                if rc != 0:
                    step_status = "error"
                    step_err = (
                        f"Comando devolvió rc={rc}.\nSTDOUT(preview):\n{stdout[:2000]}\n\nSTDERR(preview):\n{stderr[:2000]}"
                    )

            self._record_task(
                run_id=run_id,
                step_id=step_id,
                cmd_str=cmd[0] if cmd else "",
                status=step_status,
                rc=rc,
                started_at=started,
                finished_at=finished,
                stdout=stdout,
                stderr=stderr,
                result=result_obj,
            )

            if step_status == "ok":
                executed.append(
                    StepResult(
                        step_id=step_id,
                        command=(cmd[0] if cmd else ""),
                        status="ok",
                        result=result_obj,
                    )
                )
                self._event("info", "step ok", {"step_id": step_id}, run_id=run_id)
            else:
                executed.append(
                    StepResult(
                        step_id=step_id,
                        command=(cmd[0] if cmd else ""),
                        status="error",
                        error=step_err,
                    )
                )
                self._event("error", "step error", {"step_id": step_id, "error": step_err}, run_id=run_id)
                overall_ok = False
                break  # detenemos la ejecución al primer error

        # Rollback si algo falló y hay rollback.json
        if not overall_ok and rollback_path and rollback_path.exists():
            try:
                rb_steps = _read_json_file(rollback_path)
            except Exception as e:
                rollback_info = {"status": "failed", "error": f"No se pudo leer rollback.json: {e}"}
                self._event("error", "rollback read error", {"error": rollback_info["error"]}, run_id=run_id)
            else:
                # Ejecutar rollback "best-effort"
                all_ok = True
                for rb in rb_steps:
                    rb_cmd: Sequence[str] = rb.get("cmd") or []
                    rb_id = str(rb.get("step_id", "rollback"))
                    rc, stdout, stderr = self._run_command(rb_cmd)
                    if rc != 0:
                        all_ok = False
                        self._event(
                            "error",
                            "rollback step error",
                            {
                                "rollback_step_id": rb_id,
                                "rc": rc,
                                "stdout_head": (stdout[:1000] if stdout else ""),
                                "stderr_head": (stderr[:1000] if stderr else ""),
                            },
                            run_id=run_id,
                        )
                rollback_info = {"status": "done" if all_ok else "failed"}

        # Armar respuesta
        out = {
            "ok": overall_ok,
            "run_id": run_id,
            "status": "success" if overall_ok else "failed",
            "executed": [
                (
                    {
                        "step_id": r.step_id,
                        "command": r.command,
                        "status": r.status,
                        "result": r.result,
                    }
                    if r.status == "ok"
                    else {
                        "step_id": r.step_id,
                        "command": r.command,
                        "status": r.status,
                        "error": r.error,
                    }
                )
                for r in executed
            ],
            "rollback": rollback_info,
        }

        self._finish_run(run_id, out["status"], {"executed": len(executed)})
        return out
