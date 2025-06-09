"""Mailer agent placeholder that emits email notifications."""

from __future__ import annotations

from threading import Event

from message_bus import MessageBus


def run(bus: MessageBus, stop_event: Event) -> None:
    """Consume trade plans and publish email notifications."""
    plan_q = bus.subscribe("trade-plan")
    while not stop_event.is_set():
        try:
            plan = bus.wait_for(plan_q, timeout=0.1)
        except TimeoutError:
            continue

        email = {"sent": True, "plan": plan}
        bus.publish("email-notify", email)


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
