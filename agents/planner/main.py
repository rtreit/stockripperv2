"""Planner agent placeholder with simple rule-based trade plan."""

from __future__ import annotations

from threading import Event

from message_bus import MessageBus


def run(bus: MessageBus, stop_event: Event) -> None:
    """Consume market insights and publish trade plans."""
    insight_q = bus.subscribe("market-insight")
    while not stop_event.is_set():
        try:
            insight = bus.wait_for(insight_q, timeout=0.1)
        except TimeoutError:
            continue

        plan = {"status": "READY", "insight": insight}
        bus.publish("trade-plan", plan)


def main() -> None:
    import threading
    bus = MessageBus()
    stop = Event()
    t = threading.Thread(target=run, args=(bus, stop))
    t.start()
    try:
        t.join()
    finally:
        stop.set()


if __name__ == "__main__":
    main()
