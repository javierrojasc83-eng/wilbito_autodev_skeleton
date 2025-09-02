from typing import Dict, Any
from rich import print

class Router:
    """Asigna tareas a agentes por tipo."""
    def dispatch(self, tarea: Dict[str, Any]):
        tipo = tarea.get("tipo")
        print(f"[cyan]Router[/cyan] → Enviando tarea tipo: [bold]{tipo}[/bold]")
        return tipo
