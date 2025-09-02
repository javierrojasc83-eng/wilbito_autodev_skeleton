from typing import Dict, Any, List
from ..agents.coordinator import Council

class CouncilPipeline:
    def __init__(self, diary_path: str, granularity: str = "normal"):
        self.council = Council(diary_path, granularity=granularity)

    def run(self, objetivo: str, max_iter: int = 1) -> List[Dict[str, Any]]:
        return self.council.run(objetivo, max_iter=max_iter)
