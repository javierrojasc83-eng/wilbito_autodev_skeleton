def run(objetivo: str, max_iter: int = 2, granularity: str = "coarse"):
    """
    Stub de Council Agent: simula debate multi-agente.
    """
    return {
        "rfc": {
            "title": f"RFC: {objetivo}",
            "summary": f"Plan de alto nivel para cumplir el objetivo {objetivo}.",
            "tasks": ["investigar", "prototipar", "evaluar", "documentar"],
            "risks": ["tiempo", "complejidad", "dependencias"]
        },
        "research": {
            "topic": objetivo,
            "findings": [
                f"Hipótesis inicial sobre {objetivo}",
                "Patrón Strategy para agentes",
                "Circuit-breaker para herramientas externas"
            ]
        },
        "iteraciones": [
            {
                "iter": i+1,
                "artefacto": {
                    "artefacto": "demo.py",
                    "contenido": f"# Auto-generado iter {i+1} para: {objetivo}\ndef demo():\n    return 'ok'\n"
                },
                "eval": {"passed": True, "metrics": {"tests": "ok"}}
            }
            for i in range(max_iter)
        ]
    }
