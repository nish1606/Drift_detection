from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.governance.policy_loader import LoadedPolicy


@dataclass
class PolicyEvaluation:
    policy_name: str
    passed: bool
    action: str
    rationale: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    def __init__(self, policies: list[LoadedPolicy] | None = None) -> None:
        self.policies = policies or []

    def evaluate(self, context: dict[str, Any]) -> list[PolicyEvaluation]:
        evaluations: list[PolicyEvaluation] = []
        for policy in self.policies:
            if not policy.enabled:
                continue
            rules = policy.config.get("rules", [])
            passed = True
            rationale: list[str] = []
            action = "allow"
            for rule in rules:
                condition = rule.get("if", {})
                then = rule.get("then", {})
                if self._matches(condition, context):
                    action = str(then.get("action", action))
                    rationale.append(str(then.get("reason", f"matched rule in {policy.name}")))
                    if action in {"block", "freeze"}:
                        passed = False
                        break
            evaluations.append(
                PolicyEvaluation(
                    policy_name=policy.name,
                    passed=passed,
                    action=action,
                    rationale=rationale,
                    metadata={"version": policy.version, "type": policy.policy_type},
                )
            )
        return evaluations

    def _matches(self, condition: dict[str, Any], context: dict[str, Any]) -> bool:
        for key, expected in condition.items():
            actual = context.get(key)
            if key.endswith("_gte"):
                field = key.removesuffix("_gte")
                if float(context.get(field, 0.0)) < float(expected):
                    return False
            elif key.endswith("_lte"):
                field = key.removesuffix("_lte")
                if float(context.get(field, 0.0)) > float(expected):
                    return False
            elif key.endswith("_in"):
                field = key.removesuffix("_in")
                if context.get(field) not in set(expected):
                    return False
            elif actual != expected:
                return False
        return True
