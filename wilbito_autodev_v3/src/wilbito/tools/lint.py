import os, sys, subprocess, tempfile, json
from typing import Dict, Any, List

def check_syntax(code: str) -> Dict[str, Any]:
    try:
        compile(code, "<string>", "exec")
        return {"syntax_ok": True, "errors": []}
    except SyntaxError as e:
        return {"syntax_ok": False, "errors": [f"{e.msg} at line {e.lineno}: {e.text}"]}

def run_pytest(path: str) -> Dict[str, Any]:
    try:
        import pytest  # noqa
    except Exception:
        return {"pytest_available": False, "exit_code": None, "summary": "pytest no instalado"}
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=path, capture_output=True, text=True)
    return {
        "pytest_available": True,
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:]
    }
