# src/wilbito/agents/council_v2.py
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional


def _event(
    db_path: str,
    level: str,
    message: str,
    data: dict[str, Any] | None = None,
    run_id: int | None = None,
    task_id: int | None = None,
):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO events(run_id, task_id, level, message, data_json, created_at) VALUES(?,?,?,?,?,?)",
            (
                run_id,
                task_id,
                level,
                message,
                json.dumps(data or {}, ensure_ascii=False),
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _mem_search(query: str, top_k: int, rag_tag: str | None, min_score: float) -> list[dict[str, Any]]:
    """Llama al CLI oficial para obtener contexto (RAG). Retorna lista de resultados."""
    args = [
        sys.executable,
        "-m",
        "wilbito.interfaces.cli",
        "mem-search",
        query,
        "--top-k",
        str(top_k),
    ]
    if rag_tag:
        args += ["--rag-tag", rag_tag]
    if min_score and min_score > 0:
        args += ["--min-score", str(min_score)]

    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"mem-search rc={p.returncode} stderr={p.stderr}")
    try:
        out = json.loads(p.stdout.strip())
        return out.get("results") or []
    except Exception as e:
        raise RuntimeError(f"Salida no JSON de mem-search: {p.stdout[:1000]}") from e


def run_council_v2(
    objetivo: str,
    db_path: str,
    use_context: bool = False,
    top_k: int = 5,
    rag_tag: str | None = None,
    min_score: float = 0.0,
) -> dict[str, Any]:
    """
    Consejo v2: arma RFC + research + plan + riesgos. Integra RAG opcional.
    Guarda eventos en DB.
    """
    _event(db_path, "info", "council_v2 start", {"objetivo": objetivo, "use_context": use_context})
    contexto: list[dict[str, Any]] = []
    if use_context:
        try:
            contexto = _mem_search(objetivo, top_k=top_k, rag_tag=rag_tag, min_score=min_score)
            _event(db_path, "info", "council_v2 context ok", {"found": len(contexto)})
        except Exception as e:
            _event(db_path, "warning", "council_v2 context failed", {"error": str(e)})
            contexto = []

    # Consejo "determinístico" (placeholder) — listo para luego enchufar LLM if needed
    rfc = {
        "title": f"RFC: {objetivo}",
        "summary": f"Propuesta técnica para abordar: {objetivo}.",
        "tasks": [
            "investigar",
            "prototipar",
            "pruebas",
            "evaluar",
            "documentar",
        ],
        "risks": [
            "incertidumbre de requisitos",
            "tiempos de integración",
            "dependencias externas",
        ],
    }
    research = {
        "topic": objetivo,
        "findings": [
            f"Hipótesis inicial sobre {objetivo}",
            "Buenas prácticas de robustez (lint + tests)",
            "Fallbacks y circuit-breakers en integraciones",
        ],
    }
    plan = {
        "milestones": [
            {"id": 1, "title": "PoC validada", "exit": "tests mínimas verdes"},
            {"id": 2, "title": "Integración con RAG", "exit": "mem-search útil (>1 resultado)"},
            {"id": 3, "title": "CI estable", "exit": "quality OK + backup + release"},
        ]
    }

    result = {
        "objetivo": objetivo,
        "rfc": rfc,
        "research": research,
        "plan": plan,
        "contexto": contexto,
    }

    _event(db_path, "info", "council_v2 done", {"objetivo": objetivo})
    return result
