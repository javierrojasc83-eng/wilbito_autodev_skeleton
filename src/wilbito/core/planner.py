from typing import List, Dict

class Planner:
    """Descompone un objetivo en tareas simples."""
    def plan(self, objetivo: str) -> List[Dict]:
        subtareas = [t.strip() for t in objetivo.split("->") if t.strip()]
        if not subtareas:
            subtareas = ["investigar", "prototipar", "evaluar", "documentar"]
        return [{"id": i+1, "tipo": st, "payload": {"objetivo": objetivo}} for i, st in enumerate(subtareas)]
