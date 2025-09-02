from typing import Dict, Any

class LLMs:
    """Placeholder para integrar GPT/Gemini/etc."""
    def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
        # Evita dependencias de APIs reales en el skeleton
        return {"model": "mock-llm", "output": f"Respuesta simulada a: {prompt[:60]}..."}
