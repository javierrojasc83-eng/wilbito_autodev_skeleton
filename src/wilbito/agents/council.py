from __future__ import annotations
from typing import Dict, Any, List

def run(objetivo: str, max_iter: int = 2, granularity: str = "coarse") -> Dict[str, Any]:
    """
    Consejo multi-agente mínimo.
    - Normaliza max_iter para que nunca sea None ni inválido.
    - Devuelve un RFC, findings de research y artefactos por iteración.
    """
    try:
        max_iter = int(max_iter) if max_iter is not None else 2
    except Exception:
        max_iter = 2
    if max_iter < 1:
        max_iter = 1

    rfc = {
        "title": f"RFC: {objetivo}",
        "summary": f"Plan de alto nivel para cumplir el objetivo {objetivo}.",
        "tasks": ["investigar", "prototipar", "tests", "evaluar", "documentar", "retroalimentar"],
        "risks": ["tiempo", "complejidad", "dependencias"],
    }

    research = {
        "topic": objetivo,
        "findings": [
            f"Hipótesis inicial sobre {objetivo}",
            "Patrón Strategy para agentes",
            "Circuit-breaker para herramientas externas",
        ],
    }

    iters: List[Dict[str, Any]] = []
    for i in range(max_iter):
        artefacto = {
            "artefacto": "demo.py",
            "contenido": f"# Auto-generado iter {i+1} para: {objetivo}\n"
                         "def demo():\n"
                         "    return 'ok'\n"
        }
        iters.append({
            "iter": i + 1,
            "artefacto": artefacto,
            "eval": {"passed": True, "metrics": {"tests": "ok"}},
        })

    return {"rfc": rfc, "research": research, "iteraciones": iters}
