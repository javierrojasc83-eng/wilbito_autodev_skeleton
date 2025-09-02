from typing import Callable, Dict, List, Any, DefaultDict
from collections import defaultdict

class EventBus:
    """Bus de eventos in-proc (pub/sub) muy simple."""
    def __init__(self) -> None:
        self._subs: DefaultDict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        self._subs[topic].append(handler)

    def publish(self, topic: str, event: Dict[str, Any]) -> None:
        for h in self._subs.get(topic, []):
            h(event)
