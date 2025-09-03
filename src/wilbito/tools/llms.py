from typing import Any, Dict


class LLMs:
    """Placeholder para integrar GPT/Gemini/etc."""

    def complete(self, prompt: str, **kwargs) -> dict[str, Any]:
        # Evita dependencias de APIs reales en el skeleton
        return {"model": "mock-llm", "output": f"Respuesta simulada a: {prompt[:60]}..."}
