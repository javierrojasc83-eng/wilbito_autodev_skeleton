def run(objetivo: str, max_iter: int = 1):
    """
    Stub de Router Agent: simula un ciclo de autodesarrollo básico.
    """
    return [
        {
            "tarea": {"id": 1, "tipo": objetivo, "payload": {"objetivo": objetivo}},
            "artefacto": {
                "artefacto": "demo.py",
                "contenido": f"# Auto-generado para: {objetivo}\ndef demo():\n    return 'ok'\n",
            },
            "eval": {"passed": True, "metrics": {"tests": "ok"}},
        }
    ]
