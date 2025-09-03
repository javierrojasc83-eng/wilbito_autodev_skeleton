from typing import Any, Dict

from rich import print


class Router:
    """Asigna tareas a agentes por tipo."""

    def dispatch(self, tarea: dict[str, Any]):
        tipo = tarea.get("tipo")
        print(f"[cyan]Router[/cyan] → Enviando tarea tipo: [bold]{tipo}[/bold]")
        return tipo
