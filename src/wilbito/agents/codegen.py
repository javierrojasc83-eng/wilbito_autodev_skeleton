from typing import Dict, Any
from rich import print

class CodegenAgent:
    def implement(self, tarea: Dict[str, Any]) -> Dict[str, Any]:
        objetivo = tarea.get("payload", {}).get("objetivo", "")
        code = f"""# Auto-generado para: {objetivo}
def demo():
    return "ok"
"""
        print("[green]Codegen[/green] → Generó código de ejemplo.")
        return {"artefacto": "demo.py", "contenido": code}
