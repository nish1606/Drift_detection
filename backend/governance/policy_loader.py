from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from backend.core.config import get_settings
from backend.utils.validators import validate_policy_config


@dataclass
class LoadedPolicy:
    name: str
    version: str
    policy_type: str
    enabled: bool
    config: dict[str, Any]
    source_path: str


class PolicyLoader:
    def __init__(self, policies_path: str | None = None) -> None:
        self.policies_path = Path(policies_path or get_settings().policies_path)

    def load(self) -> list[LoadedPolicy]:
        if not self.policies_path.exists():
            return []
        policies: list[LoadedPolicy] = []
        for path in sorted(self.policies_path.glob("*.yaml")):
            data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            validate_policy_config(data)
            policies.append(
                LoadedPolicy(
                    name=data["name"],
                    version=str(data.get("version", "1.0")),
                    policy_type=str(data.get("policy_type", "threshold")),
                    enabled=bool(data.get("enabled", True)),
                    config=dict(data),
                    source_path=str(path),
                )
            )
        return policies
