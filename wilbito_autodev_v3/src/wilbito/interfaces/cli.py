import os
from typing import Optional

import typer
from rich import print

from ..agents.trading import TradingAgent
from ..memory.diary import Diario
from ..pipelines.autodev import AutodevPipeline
from ..pipelines.council import CouncilPipeline
from ..pipelines.pr_review import PRReviewPipeline
from ..pipelines.quality import QualityPipeline
from ..pipelines.release import ReleasePipeline

app = typer.Typer(add_completion=False, help="CLI Wilbito Autodev")


def load_cfg() -> dict:
    import yaml

    with open(os.path.join(os.path.dirname(__file__), "..", "config", "base.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def _resolve_objetivo(objetivo_arg: str | None, objetivo_opt: str | None) -> str:
    if objetivo_opt:
        return objetivo_opt
    if objetivo_arg:
        return objetivo_arg
    raise typer.BadParameter("Debes indicar un objetivo (posicional o --objetivo).")


@app.command("quality")
def quality_run():
    """Corre pruebas de calidad (pytest + lint simple)."""
    pipe = QualityPipeline(os.getcwd())
    res = pipe.run_checks()
    print(res)


@app.command("release")
def release_create(bump: str = typer.Option("patch", "--bump", help="patch|minor|major")):
    """Genera un release y actualiza CHANGELOG.md"""
    pipe = ReleasePipeline(os.getcwd())
    version = pipe.create_release(bump=bump)
    print({"version": version})


@app.command("pr")
def pr_review(
    objetivo: str | None = typer.Argument(None),
    objetivo_opt: str | None = typer.Option(None, "--objetivo", "-o"),
):
    """Ejecuta revisión de PR simulada."""
    final_obj = _resolve_objetivo(objetivo, objetivo_opt)
    pipe = PRReviewPipeline()
    res = pipe.run(final_obj)
    print(res)


if __name__ == "__main__":
    app()
