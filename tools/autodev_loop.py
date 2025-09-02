# -*- coding: utf-8 -*-
"""Auto-dev loop robusto: ejecuta el executor-run varias veces y consolida resultados.

- Intenta parsear JSON de stdout (ideal), si falla intenta heurísticas:
  - Buscar objetos/arrays JSON balanceados en stdout/stderr.
  - Elegir el mejor candidato (dict con claves típicas: ok/status/run_id).
- Devuelve siempre un resumen JSON al final.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------- utilidades de limpieza/parsing ---------------------- #

_ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")


def _clean_text(s: str) -> str:
    """Quita ANSI, normaliza saltos de línea y recorta extremos."""
    if not s:
        return ""
    s = _ANSI_RE.sub("", s)
    s = s.replace("\r", "")
    s = s.strip()
    return s


def _scan_balanced_json(
    s: str,
    start: int,
    open_ch: str,
    close_ch: str,
) -> Tuple[Optional[Any], int]:
    """Desde s[start]==open_ch, busca el cierre balanceado y hace json.loads del fragmento."""
    depth = 0
    in_str = False
    esc = False
    i = start
    while i < len(s):
        c = s[i]
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
            elif c == open_ch:
                depth += 1
            elif c == close_ch:
                depth -= 1
                if depth == 0:
                    frag = s[start : i + 1]
                    try:
                        return json.loads(frag), i + 1
                    except Exception:
                        return None, i + 1
        i += 1
    return None, i


def _extract_json_objects(s: str) -> List[Any]:
    """Extrae todos los objetos/arrays JSON balanceados embebidos en s."""
    out: List[Any] = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "{":
            obj, j = _scan_balanced_json(s, i, "{", "}")
            if obj is not None:
                out.append(obj)
            i = j
            continue
        if ch == "[":
            obj, j = _scan_balanced_json(s, i, "[", "]")
            if obj is not None:
                out.append(obj)
            i = j
            continue
        i += 1
    return out


def _choose_best_json(objs: List[Any]) -> Optional[Dict[str, Any]]:
    """Entre varios candidatos, favorece dicts que parezcan la salida del executor."""
    dicts: List[Dict[str, Any]] = [o for o in objs if isinstance(o, dict)]
    if not dicts:
        return None
    # Score simple: +1 por cada clave típica presente.
    def score(d: Dict[str, Any]) -> int:
        keys = ("ok", "status", "run_id", "executed")
        return sum(1 for k in keys if k in d)

    ranked = sorted(((score(d), i, d) for i, d in enumerate(dicts)), reverse=True)
    return ranked[0][2]


def _parse_executor_json(
    stdout_text: str,
    stderr_text: str,
    verbose: bool = False,
) -> Optional[Dict[str, Any]]:
    """Intenta parsear JSON de la ejecución del executor."""
    out = _clean_text(stdout_text or "")
    err = _clean_text(stderr_text or "")

    # 1) Intento directo con stdout
    try:
        return json.loads(out)
    except Exception:
        pass

    # 2) Buscar objetos embebidos en stdout
    objs_out = _extract_json_objects(out)
    if objs_out:
        best = _choose_best_json(objs_out)
        if isinstance(best, dict):
            return best

    # 3) Intentos con stderr (menos común, pero posible)
    try:
        return json.loads(err)
    except Exception:
        pass

    objs_err = _extract_json_objects(err)
    if objs_err:
        best = _choose_best_json(objs_err)
        if isinstance(best, dict):
            return best

    if verbose:
        print("DBG: no se pudo extraer JSON; heads:", file=sys.stderr)
        if out:
            print("RAW_STDOUT_HEAD:", out[:400], file=sys.stderr)
        if err:
            print("RAW_STDERR_HEAD:", err[:400], file=sys.stderr)
    return None


# ------------------------------ ejecución runner ------------------------------ #

def _run_executor_subprocess(
    root: Path,
    commands_path: str,
    run_name: str,
    verbose: bool,
) -> Tuple[Optional[Dict[str, Any]], int, str, str]:
    """Ejecuta el executor-run y devuelve (data, rc, stdout, stderr)."""
    src = str(root / "src")
    if src not in (os.environ.get("PYTHONPATH") or ""):
        os.environ["PYTHONPATH"] = (
            src + os.pathsep + os.environ.get("PYTHONPATH", "")
        ).strip(os.pathsep)

    cmd = [
        sys.executable,
        "-m",
        "wilbito.interfaces.exec",
        "executor-run",
        "--commands",
        str(commands_path),
        "--run-name",
        run_name,
    ]
    proc = subprocess.run(
        cmd,
        cwd=root,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
    out_text = proc.stdout or ""
    err_text = proc.stderr or ""
    data = _parse_executor_json(out_text, err_text, verbose=verbose)
    return data, proc.returncode, out_text, err_text


def run_once(
    commands_path: str,
    run_name: str,
    verbose: bool,
) -> Dict[str, Any]:
    """Corre una vez el pipeline y devuelve el dict JSON (o un error uniforme)."""
    root = Path(__file__).resolve().parents[1]

    data, rc, out_text, err_text = _run_executor_subprocess(
        root,
        commands_path,
        run_name,
        verbose=verbose,
    )
    if isinstance(data, dict):
        return data

    # Si no hubo forma de extraer JSON válido:
    return {
        "ok": False,
        "status": "failed",
        "error": "non-JSON executor output",
        "returncode": rc,
        "stdout_head": (out_text or "")[:1000],
        "stderr_head": (err_text or "")[:1000],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Auto-dev loop simple")
    ap.add_argument(
        "--commands",
        default="config/commands.autodev.json",
        help="Ruta al commands.json en cada iteración",
    )
    ap.add_argument(
        "--iterations",
        type=int,
        default=2,
        help="Número de iteraciones (default: 2)",
    )
    ap.add_argument(
        "--stop-on-fail",
        action="store_true",
        help="Detiene si alguna iteración falla",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Muestra heads de stdout/stderr si no hay JSON",
    )
    args = ap.parse_args()

    results: List[Dict[str, Any]] = []
    for i in range(1, args.iterations + 1):
        run_name = f"autodev-loop-{i}-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        data = run_once(args.commands, run_name, args.verbose)
        results.append(
            {
                "i": i,
                "ok": bool(data.get("ok")),
                "status": data.get("status"),
                "run_id": data.get("run_id"),
                "error": data.get("error"),
            }
        )
        if not data.get("ok") and args.stop_on_fail:
            break

    summary = {
        "ok": all(r.get("ok") for r in results),
        "iterations": len(results),
        "results": results,
    }
    print(json.dumps(summary, ensure_ascii=False))
    sys.exit(0 if summary["ok"] else 1)


if __name__ == "__main__":
    main()
