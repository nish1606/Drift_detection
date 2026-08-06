from __future__ import annotations

from collections import deque
from typing import Any, Iterable


class KafkaConsumer:
    def __init__(self, source: Iterable[dict[str, Any]] | None = None) -> None:
        self.source = deque(source or [])

    def consume(self) -> dict[str, Any] | None:
        if not self.source:
            return None
        return self.source.popleft()
