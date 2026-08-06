from __future__ import annotations

from collections import deque
from typing import Any


class KafkaProducer:
    def __init__(self) -> None:
        self.messages: deque[dict[str, Any]] = deque()

    def publish(self, topic: str, payload: dict[str, Any]) -> None:
        self.messages.append({"topic": topic, "payload": payload})
