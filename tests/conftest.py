import os
import sys
import threading
from typing import Any

import pytest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from message_bus import MessageBus
from agents import planner, mailer


class DummyClient:
    """Simple client that interacts with an in-memory MessageBus."""

    def __init__(self) -> None:
        self.bus = MessageBus()
        self.trade_plan_q = self.bus.subscribe("trade-plan")
        self.email_q = self.bus.subscribe("email-notify")
        self._stop = threading.Event()
        self._threads = [
            threading.Thread(target=planner.run, args=(self.bus, self._stop), daemon=True),
            threading.Thread(target=mailer.run, args=(self.bus, self._stop), daemon=True),
        ]
        for t in self._threads:
            t.start()

    def post(self, path: str, json: dict) -> None:
        if path != "/a2a/publish":
            raise ValueError(f"Unsupported path: {path}")
        self.bus.publish("market-insight", json)

    def wait_for(self, topic: str, timeout: int = 30) -> Any:
        if topic == "trade-plan":
            return self.bus.wait_for(self.trade_plan_q, timeout)
        if topic == "email-notify":
            return self.bus.wait_for(self.email_q, timeout)
        raise ValueError(f"Unsupported topic: {topic}")

    def close(self) -> None:
        self._stop.set()
        for t in self._threads:
            t.join(timeout=1)


@pytest.fixture
def client():
    c = DummyClient()
    try:
        yield c
    finally:
        c.close()
