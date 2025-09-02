# src/wilbito/tools/quality.py
from __future__ import annotations
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

def _compile_file(path: Path) -> Dict[str, Any]:
    try:
        code = path.read_text(encoding="utf-8")
        compile(code, str(path), "exec")
        return {"syntax_ok": True, "errors": []}
    except Exception as e:
        return {"syntax_ok": False, "errors": [str(e)]}

def run_quality() -> Dict[str, Any]:
    """
    1) Lint sintáctico por 'compile' de todos los .py en artifacts/.
    2) Ejecuta unittest discover en tests/ si existe.
    (Evitamos pytest por conflictos de plugins en el entorno del usuario)
    """
    root = Path(os.getcwd()).resolve()
    artifacts = root / "artifacts"
    lint_report: Dict[str, Any] = {}

    if artifacts.exists():
        for p in artifacts.rglob("*.py"):
            rel = p.relative_to(root).as_posix()
            lint_report[rel] = _compile_file(p)

    # ---- unittest (preferido, sin pytest) ----
    unittest_report: Dict[str, Any] = None  # type: ignore
    tests_dir = root / "tests"
    if tests_dir.exists():
        try:
            import subprocess
            # Aseguramos que el repo root esté en sys.path en el proceso hijo
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root) + os.pathsep + env.get("PYTHONPATH", "")
            # Descubrimiento estándar
            cmd = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"]
            r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(root), env=env)
            unittest_report = {
                "returncode": r.returncode,
                "stdout": r.stdout[-2000:],  # recorte por las dudas
                "stderr": r.stderr[-2000:],
            }
        except Exception as e:
            unittest_report = {"error": str(e)}

    return {
        "lint": lint_report,
        "unittest": unittest_report,
    }
