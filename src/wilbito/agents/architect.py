from typing import Any, Dict


class ArchitectAgent:
    """Define estrategia (RFC) y divide objetivos."""

    def __init__(self, granularity: str = "normal") -> None:
        self.granularity = granularity

    def design(self, objetivo: str) -> dict[str, Any]:
        tasks = ["investigar", "prototipar", "evaluar", "documentar"]
        if self.granularity == "fine":
            tasks = ["investigar", "prototipar", "tests", "evaluar", "documentar", "retroalimentar"]
        return {
            "title": f"RFC: {objetivo}",
            "summary": "Plan de alto nivel para cumplir el objetivo.",
            "tasks": tasks,
            "risks": ["tiempo", "complejidad", "dependencias"],
        }
