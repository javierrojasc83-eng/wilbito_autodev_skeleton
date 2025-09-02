from typing import Dict, Any, List
from ..agents.architect import ArchitectAgent
from ..agents.researcher import ResearcherAgent

class PRReviewPipeline:
    def __init__(self):
        self.arch = ArchitectAgent()
        self.res = ResearcherAgent()

    def run(self, objetivo: str) -> Dict[str, Any]:
        rfc = self.arch.design(objetivo)
        research = self.res.research(objetivo)
        comentarios = [
            f"[Architect] Revisa la claridad del objetivo: {objetivo}",
            f"[Researcher] Sugiere comparar con enfoques similares en {objetivo}"
        ]
        return {"objetivo": objetivo, "rfc": rfc, "research": research, "comentarios": comentarios}
