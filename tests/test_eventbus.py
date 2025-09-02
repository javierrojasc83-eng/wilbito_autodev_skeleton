from wilbito.core.eventbus import EventBus

def test_eventbus_basic():
    bus = EventBus()
    box = {"hits": 0}
    def handler(evt): box["hits"] += evt.get("x", 0)
    bus.subscribe("tick", handler)
    bus.publish("tick", {"x": 2})
    bus.publish("tick", {"x": 3})
    assert box["hits"] == 5
