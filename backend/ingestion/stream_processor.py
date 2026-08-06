from __future__ import annotations

from collections import deque
from typing import Any, Callable


class StreamProcessor:
    def __init__(self) -> None:
        self.queue: deque[dict[str, Any]] = deque()

    def ingest(self, event: dict[str, Any]) -> None:
        self.queue.append(event)

    def process(self, handler: Callable[[dict[str, Any]], Any]) -> list[Any]:
        results: list[Any] = []
        while self.queue:
            results.append(handler(self.queue.popleft()))
        return results
