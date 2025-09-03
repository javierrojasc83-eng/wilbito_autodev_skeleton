import queue
from typing import Any


class TaskQueue:
    """Cola ligera basada en queue.Queue, para trabajos in-proceso."""

    def __init__(self, maxsize: int = 0) -> None:
        self.q: queue.Queue[Any] = queue.Queue(maxsize=maxsize)

    def put(self, item: Any) -> None:
        self.q.put(item)

    def get(self) -> Any:
        return self.q.get()

    def empty(self) -> bool:
        return self.q.empty()

    def task_done(self) -> None:
        self.q.task_done()
