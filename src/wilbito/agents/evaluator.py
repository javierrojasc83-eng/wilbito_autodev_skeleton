import os, datetime
from typing import Dict, Any
from rich import print
from ..tools.lint import check_syntax

class EvaluatorAgent:
    def evaluate(self, artefacto: Dict[str, Any]) -> Dict[str, Any]:
        code = (artefacto or {}).get("contenido", "")
        name = (artefacto or {}).get("artefacto", "artifact.py")
        # Guardar en artifacts/
        folder = os.path.join("artifacts", "codegen")
        os.makedirs(folder, exist_ok=True)
        fn = os.path.join(folder, name)
        with open(fn, "w", encoding="utf-8") as f:
            f.write(code)
        # Lint sintáctico básico
        lint = check_syntax(code)
        passed = bool(lint.get("syntax_ok"))
        print("[yellow]Evaluator[/yellow] → Syntax:", "OK" if passed else "ERROR")
        return {"passed": passed, "syntax": lint, "file": fn, "ts": datetime.datetime.utcnow().isoformat()+"Z"}
