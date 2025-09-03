from datetime import datetime
from typing import Any, Dict

from rich import print

from ..memory.diary import Diario


class DocumenterAgent:
    def __init__(self, diary_path: str):
        self.diario = Diario(diary_path)

    def document(self, objetivo: str, resultado: dict[str, Any]) -> str:
        entry = f"""# Entrada {datetime.utcnow().isoformat()}Z
Objetivo: {objetivo}
Resultado: {resultado}
"""
        self.diario.escribir(entry)
        print("[blue]Documenter[/blue] → Diario actualizado.")
        return entry
