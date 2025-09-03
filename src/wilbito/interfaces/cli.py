# src/wilbito/interfaces/cli.py
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer
from rich import print

from wilbito.agents import council as council_agent

# --- Agents / Tools / Memory ---
from wilbito.agents import router as router_agent

# --- Config ---
from wilbito.config import get_default, load_config
from wilbito.memory.diario import write_entry
from wilbito.memory.vectorstore import VectorStore
from wilbito.tools import pr as pr_tools
from wilbito.tools import quality as quality_tools
from wilbito.tools import release as release_tool
from wilbito.tools import trading as trading_tools

app = typer.Typer(help="CLI Wilbito Autodev")

# Cargamos config (si existe). No hacemos fallar el CLI si no hay YAML.
CFG: dict[str, Any] = load_config()


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _repo_root() -> Path:
    return Path(os.getcwd()).resolve()


def _mem_db_path() -> Path:
    return _repo_root() / "memoria" / "vector_db" / "vectorstore.json"


def _ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def _echo_json(obj: Any):
    print(json.dumps(obj, ensure_ascii=False, indent=4))


# ----------------------------------------------------------------------
# PLAN
# ----------------------------------------------------------------------
@app.command("plan")
def plan_cmd(objetivo: str):
    """
    Planificar objetivo y mostrar tareas.
    """
    tasks = [
        {"id": 1, "tipo": "investigar", "payload": {"objetivo": objetivo}},
        {"id": 2, "tipo": "prototipar", "payload": {"objetivo": objetivo}},
        {"id": 3, "tipo": "evaluar", "payload": {"objetivo": objetivo}},
        {"id": 4, "tipo": "documentar", "payload": {"objetivo": objetivo}},
    ]
    _echo_json(tasks)


# ----------------------------------------------------------------------
# AUTODEV (con RAG knobs)
# ----------------------------------------------------------------------
@app.command("autodev")
def autodev_cmd(
    objetivo: str,
    max_iter: int = typer.Option(get_default(CFG, "router.max_iter_default", 1), help="Iteraciones máximas"),
    use_context: bool = typer.Option(
        get_default(CFG, "router.use_context_default", False),
        help="Activar recuperación de contexto (RAG)",
    ),
    top_k: int = typer.Option(get_default(CFG, "router.top_k_default", 5), help="Cantidad de resultados de memoria"),
    rag_tag: str | None = typer.Option(None, help="Tag preferente para RAG (codegen|marketing|trading)"),
    min_score: float = typer.Option(0.0, help="Umbral mínimo de score RAG (0.0-1.0)"),
):
    ctx: list[dict[str, Any]] = []
    if use_context:
        db_path = _mem_db_path()
        vdb = VectorStore.load(str(db_path))
        prefer_tags = [rag_tag] if rag_tag else None
        ctx = vdb.search(objetivo, top_k=top_k, min_score=min_score, prefer_tags=prefer_tags)

    result = {
        "objetivo": objetivo,
        "contexto": ctx,
        "iteraciones": router_agent.run(objetivo=objetivo, max_iter=max_iter),
    }
    _echo_json(result)


# ----------------------------------------------------------------------
# COUNCIL (con RAG knobs)
# ----------------------------------------------------------------------
@app.command("council")
def council_cmd(
    objetivo: str,
    max_iter: int = typer.Option(get_default(CFG, "council.max_iter_default", 2), help="Iteraciones de consejo"),
    granularity: str = typer.Option(get_default(CFG, "council.granularity_default", "coarse"), help="coarse|fine"),
    use_context: bool = typer.Option(
        get_default(CFG, "council.use_context_default", False),
        help="Activar recuperación de contexto (RAG)",
    ),
    top_k: int = typer.Option(get_default(CFG, "council.top_k_default", 5), help="Cantidad de resultados de memoria"),
    rag_tag: str | None = typer.Option(None, help="Tag preferente para RAG (codegen|marketing|trading)"),
    min_score: float = typer.Option(0.0, help="Umbral mínimo de score RAG (0.0-1.0)"),
):
    ctx: list[dict[str, Any]] = []
    if use_context:
        db_path = _mem_db_path()
        vdb = VectorStore.load(str(db_path))
        prefer_tags = [rag_tag] if rag_tag else None
        ctx = vdb.search(objetivo, top_k=top_k, min_score=min_score, prefer_tags=prefer_tags)

    result = council_agent.run(objetivo=objetivo, max_iter=max_iter, granularity=granularity)
    result["contexto"] = ctx
    _echo_json(result)


# ----------------------------------------------------------------------
# TRADING
# ----------------------------------------------------------------------
@app.command("trading-backtest")
def trading_backtest_cmd(
    par: str,
    n: int = typer.Option(100, help="Cantidad de trades simulados"),
):
    out = trading_tools.backtest(par=par, n=n)
    _echo_json(out)


# ----------------------------------------------------------------------
# DIARIO (+ auto-ingesta opcional a memoria)
# ----------------------------------------------------------------------
@app.command("diario")
def diario_cmd(
    texto: str,
    tag: str | None = typer.Option(None, help="Si se provee, auto-ingesta a memoria con este tag"),
):
    write_res = write_entry(texto)
    ingested = False
    if tag:
        db_path = _mem_db_path()
        vdb = VectorStore.load(str(db_path))
        ingested = vdb.add_text(texto, meta={"tag": tag})
        _ensure_parent(db_path)
        vdb.save(str(db_path))

    _echo_json({"ok": True, "file": write_res["file"], "ingested": bool(tag and ingested), "tag": tag})


# ----------------------------------------------------------------------
# QUALITY (lint + pytest sin plugins externos; fallback a unittest)
# ----------------------------------------------------------------------
@app.command("quality")
def quality_cmd():
    # 1) Lint sintáctico simple (nuestro tool interno)
    lint_res = quality_tools.run_quality()

    tests_dir = _repo_root() / "tests"
    pytest_result: dict[str, Any] | None = None

    if tests_dir.exists():
        try:
            import subprocess

            # Ambiente "blindado": NO autoload de plugins externos
            env = os.environ.copy()
            env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
            # Belt & suspenders: si igual llega a cargar, negamos explícitos conocidos
            pytest_args = ["-q", "-p", "no:sympy", "-p", "no:sympy.utilities.pytest"]

            # Ejecutamos pytest embebido para evitar entry-points del exe
            code = (
                "import os, sys, pytest; "
                "os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'; "
                "sys.exit(pytest.main(" + repr(pytest_args) + "))"
            )
            r = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                env=env,
                cwd=str(_repo_root()),
            )
            pytest_result = {
                "returncode": r.returncode,
                "stdout": (r.stdout or "").strip()[-2000:],
                "stderr": (r.stderr or "").strip()[-2000:],
            }

            # 2) Fallback a unittest si pytest falló por entorno/plugines
            if r.returncode != 0 and "sympy" in ((r.stderr or "") + (r.stdout or "")):
                u = subprocess.run(
                    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"],
                    capture_output=True,
                    text=True,
                    env=env,
                    cwd=str(_repo_root()),
                )
                pytest_result = {
                    "note": "pytest falló por plugins externos; se corrió unittest discover",
                    "returncode": u.returncode,
                    "stdout": (u.stdout or "").strip()[-2000:],
                    "stderr": (u.stderr or "").strip()[-2000:],
                }

        except Exception as e:
            pytest_result = {"error": str(e)}

    _echo_json({"lint": lint_res, "pytest": pytest_result})


# ----------------------------------------------------------------------
# PR review
# ----------------------------------------------------------------------
@app.command("pr")
def pr_cmd(
    objetivo: str,
    use_context: bool = typer.Option(False, help="RAG opcional para enriquecer el PR"),
    top_k: int = typer.Option(5, help="Resultados de memoria"),
    rag_tag: str | None = typer.Option(None, help="Tag preferente para RAG"),
    min_score: float = typer.Option(0.0, help="Umbral mínimo de score RAG"),
):
    ctx: list[dict[str, Any]] = []
    if use_context:
        db_path = _mem_db_path()
        vdb = VectorStore.load(str(db_path))
        prefer_tags = [rag_tag] if rag_tag else None
        ctx = vdb.search(objetivo, top_k=top_k, min_score=min_score, prefer_tags=prefer_tags)

    out = pr_tools.run_pr_review(objetivo=objetivo)
    if ctx:
        out["contexto"] = ctx
    _echo_json(out)


# ----------------------------------------------------------------------
# RELEASE
# ----------------------------------------------------------------------
@app.command("release")
def release_cmd(
    bump: str = typer.Option("patch", help="major|minor|patch"),
):
    res = release_tool.run_release(bump=bump)
    _echo_json(res)


# ----------------------------------------------------------------------
# MEMORIA: ingest/search/backup/seed
# ----------------------------------------------------------------------
@app.command("mem-ingest")
def mem_ingest_cmd(
    texto: str,
    etiqueta: str | None = typer.Option(None, help="Tag opcional a guardar en meta"),
):
    db_path = _mem_db_path()
    vdb = VectorStore.load(str(db_path))
    added = vdb.add_text(texto, meta={"tag": etiqueta} if etiqueta else {})
    _ensure_parent(db_path)
    vdb.save(str(db_path))
    _echo_json({"ok": True, "ingested": 1 if added else 0, "tag": etiqueta})


@app.command("mem-search")
def mem_search_cmd(
    query: str,
    top_k: int = typer.Option(5, help="Resultados"),
    rag_tag: str | None = typer.Option(None, help="Tag preferente para RAG (boost)"),
    min_score: float = typer.Option(0.0, help="Umbral mínimo de score"),
):
    db_path = _mem_db_path()
    vdb = VectorStore.load(str(db_path))
    prefer_tags = [rag_tag] if rag_tag else None
    results = vdb.search(query, top_k=top_k, min_score=min_score, prefer_tags=prefer_tags)
    _echo_json({"query": query, "results": results})


@app.command("mem-backup")
def mem_backup_cmd():
    src = _mem_db_path()
    if not src.exists():
        _echo_json({"ok": False, "error": f"No existe {src.as_posix()}"})
        raise typer.Exit(code=0)
    backups = src.parent / "backups"
    backups.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    dst = backups / f"vectorstore_{ts}.json"
    latest = backups / "vectorstore_latest.json"
    data = src.read_bytes()
    dst.write_bytes(data)
    latest.write_bytes(data)
    _echo_json({"ok": True, "backup": dst.as_posix(), "latest": latest.as_posix()})


@app.command("mem-seed")
def mem_seed_cmd(
    path: str = typer.Option(..., help="Ruta a seeds.jsonl (1 JSON por línea con {text, tag?})"),
):
    src = Path(path)
    if not src.exists():
        _echo_json({"ok": False, "error": f"No existe {src.as_posix()}"})
        raise typer.Exit(code=0)

    db_path = _mem_db_path()
    vdb = VectorStore.load(str(db_path))

    ingested = 0
    with open(src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                text = obj.get("text")
                tag = obj.get("tag")
                if text:
                    if vdb.add_text(text, meta={"tag": tag} if tag else {}):
                        ingested += 1
            except Exception:
                # línea inválida, la ignoramos
                continue

    _ensure_parent(db_path)
    vdb.save(str(db_path))
    _echo_json({"ok": True, "ingested": ingested, "db": db_path.as_posix()})


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app()
