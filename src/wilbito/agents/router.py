from typing import Any, Dict, List
from wilbito.memory.context import retrieve_context

def run(objetivo: str, max_iter: int = 1, use_context: bool = False, top_k: int = 5):
    """
    Router Agent: simula un ciclo de autodesarrollo básico.
    Si use_context=True, recupera contexto de memoria y lo agrega al resultado.
    """
    context = retrieve_context(objetivo, top_k=top_k) if use_context else []

    # Simulación de ciclo mínimo
    result: List[Dict[str, Any]] = [
        {
            "tarea": {
                "id": 1,
                "tipo": objetivo,
                "payload": {"objetivo": objetivo}
            },
            "artefacto": {
                "artefacto": "demo.py",
                "contenido": f"# Auto-generado para: {objetivo}\n"
                             f"def demo():\n"
                             f"    return 'ok'\n"
            },
            "eval": {"passed": True, "metrics": {"tests": "ok"}}
        }
    ]

    return {
        "objetivo": objetivo,
        "contexto": context,   # lista de hits del vectorstore
        "iteraciones": result
    }
