from typing import Any, Dict, List

from .architect import ArchitectAgent
from .codegen import CodegenAgent
from .documenter import DocumenterAgent
from .evaluator import EvaluatorAgent
from .researcher import ResearcherAgent


class Council:
    """Consejo de IAs: Arquitecto, Researcher, Codegen, Evaluador, Documentador."""

    def __init__(self, diary_path: str, granularity: str = "normal"):
        self.arch = ArchitectAgent(granularity=granularity)
        self.res = ResearcherAgent()
        self.cod = CodegenAgent()
        self.eval = EvaluatorAgent()
        self.doc = DocumenterAgent(diary_path)

    def run(self, objetivo: str, max_iter: int = 1) -> list[dict[str, Any]]:
        rfc = self.arch.design(objetivo)
        research = self.res.research(objetivo)
        resultados = []
        for i in range(max_iter):
            arte = self.cod.implement({"payload": {"objetivo": objetivo}, "tipo": "codegen"})
            ev = self.eval.evaluate(arte)
            self.doc.document(objetivo, {"rfc": rfc, "research": research, "artefacto": arte, "eval": ev})
            resultados.append({"iter": i + 1, "artefacto": arte, "eval": ev})
        return [{"rfc": rfc, "research": research, "iteraciones": resultados}]
