from wilbito.agents.architect import ArchitectAgent
from wilbito.agents.researcher import ResearcherAgent
from wilbito.agents.codegen import CodegenAgent
from wilbito.agents.evaluator import EvaluatorAgent
from wilbito.agents.documenter import DocumenterAgent

def test_agents_minimal(tmp_path):
    arch = ArchitectAgent()
    r = arch.design("objetivo-x")
    assert "tasks" in r and len(r["tasks"]) >= 1

    res = ResearcherAgent().research("topic")
    assert "findings" in res

    arte = CodegenAgent().implement({"payload": {"objetivo": "x"}, "tipo": "codegen"})
    ev = EvaluatorAgent().evaluate(arte)
    doc = DocumenterAgent(str(tmp_path)).document("x", {"arte": arte, "eval": ev})
    assert ev["passed"] is True
