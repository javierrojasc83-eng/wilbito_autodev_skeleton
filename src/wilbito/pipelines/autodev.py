from typing import Dict, Any, List
from ..core.planner import Planner
from ..core.router import Router
from ..agents.codegen import CodegenAgent
from ..agents.evaluator import EvaluatorAgent
from ..agents.documenter import DocumenterAgent
from ..safety.gates import SafetyGate

class AutodevPipeline:
    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.planner = Planner()
        self.router = Router()
        self.codegen = CodegenAgent()
        self.evaluator = EvaluatorAgent()
        self.doc = DocumenterAgent(cfg["memory"]["diary_path"])
        self.gate = SafetyGate(cfg["safety"])

    def run(self, objetivo: str, max_iter: int = 1) -> List[Dict[str, Any]]:
        if self.gate.check_kill_switch():
            return [{"status":"aborted"}]
        tareas = self.planner.plan(objetivo)
        resultados = []
        for i, t in enumerate(tareas[:max_iter]):
            tipo = self.router.dispatch(t)
            artefacto = self.codegen.implement(t) if tipo else None
            evalres = self.evaluator.evaluate(artefacto or {})
            self.doc.document(objetivo, {"artefacto": artefacto, "eval": evalres})
            resultados.append({"tarea": t, "artefacto": artefacto, "eval": evalres})
        return resultados
