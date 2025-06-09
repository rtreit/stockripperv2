from __future__ import annotations

from collections import defaultdict
from queue import Queue, Empty
from typing import Any, Dict, List


class MessageBus:
    """Simple in-memory message bus used for tests."""

    def __init__(self) -> None:
        self._topics: Dict[str, List[Queue]] = defaultdict(list)

    def publish(self, topic: str, message: Any) -> None:
        for q in list(self._topics[topic]):
            q.put(message)

    def subscribe(self, topic: str) -> Queue:
        q: Queue = Queue()
        self._topics[topic].append(q)
        return q

    def wait_for(self, queue: Queue, timeout: int | None = None) -> Any:
        try:
            return queue.get(timeout=timeout)
        except Empty as exc:
            raise TimeoutError("Timed out waiting for message") from exc
