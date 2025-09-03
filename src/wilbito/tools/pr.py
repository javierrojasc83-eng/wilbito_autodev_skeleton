def run_pr_review(objetivo: str):
    rfc = {
        "title": f"RFC: {objetivo}",
        "summary": "Plan de alto nivel para cumplir el objetivo.",
        "tasks": ["investigar", "prototipar", "evaluar", "documentar"],
        "risks": ["tiempo", "complejidad", "dependencias"],
    }
    comments = [
        f"[Architect] Revisa la claridad del objetivo: {objetivo}",
        f"[Researcher] Sugiere comparar con enfoques similares en {objetivo}",
    ]
    return {
        "objetivo": objetivo,
        "rfc": rfc,
        "comentarios": comments,
        "research": {
            "topic": objetivo,
            "findings": [
                f"Hipótesis sobre {objetivo}",
                "Patrón Strategy para seleccionar agentes",
                "Circuit-breaker para herramientas externas",
            ],
        },
    }
