from typing import Any, Dict, List

from ..agents.coordinator import Council


class CouncilPipeline:
    def __init__(self, diary_path: str, granularity: str = "normal"):
        self.council = Council(diary_path, granularity=granularity)

    def run(self, objetivo: str, max_iter: int = 1) -> list[dict[str, Any]]:
        return self.council.run(objetivo, max_iter=max_iter)
