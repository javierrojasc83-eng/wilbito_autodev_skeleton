from collections import defaultdict
from collections.abc import Callable
from typing import Any, DefaultDict, Dict, List


class EventBus:
    """Bus de eventos in-proc (pub/sub) muy simple."""

    def __init__(self) -> None:
        self._subs: defaultdict[str, list[Callable[[dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, event: dict[str, Any]) -> None:
        for h in self._subs.get(topic, []):
            h(event)
