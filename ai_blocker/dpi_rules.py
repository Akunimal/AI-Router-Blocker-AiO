# -*- coding: utf-8 -*-
"""
Configurable DPI (Deep Packet Inspection) rules for surgical endpoint blocking.

Each rule defines a URL path pattern, an HTTP method filter, and an action to take.
Rules are evaluated in order; the first match wins. If no rule matches, the
request is allowed by default.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class DPIAction(Enum):
    """Action to take when a DPI rule matches a request."""
    BLOCK = "block"
    ALLOW = "allow"
    LOG = "log"


@dataclass(frozen=True)
class DPIRule:
    """A single Deep Packet Inspection rule.

    Attributes:
        name: Human-readable identifier for the rule.
        path_pattern: Regex matched against the request path (e.g. ``/v1/chat/completions``).
        method: HTTP method filter. ``"ALL"`` matches every method.
        action: The :class:`DPIAction` to take when the rule matches.
        enabled: Whether the rule is active.
    """
    name: str
    path_pattern: str
    method: str = "ALL"
    action: DPIAction = DPIAction.BLOCK
    enabled: bool = True

    def matches(self, path: str, method: str) -> bool:
        """Return *True* if this rule matches the given *path* and *method*."""
        if not self.enabled:
            return False
        if self.method != "ALL" and self.method.upper() != method.upper():
            return False
        try:
            return bool(re.search(self.path_pattern, path))
        except re.error:
            return False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path_pattern": self.path_pattern,
            "method": self.method,
            "action": self.action.value,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> DPIRule:
        return cls(
            name=data.get("name", ""),
            path_pattern=data.get("path_pattern", ""),
            method=data.get("method", "ALL"),
            action=DPIAction(data.get("action", "block")),
            enabled=data.get("enabled", True),
        )


# ── Default rule set ───────────────────────────────────────────────────────

DEFAULT_DPI_RULES: list[DPIRule] = [
    # Block chat/completion payload endpoints (data transmission)
    DPIRule(
        name="Block chat completions",
        path_pattern=r"/v1/chat/completions",
        method="POST",
        action=DPIAction.BLOCK,
    ),
    DPIRule(
        name="Block responses endpoint",
        path_pattern=r"/v1/responses",
        method="POST",
        action=DPIAction.BLOCK,
    ),
    DPIRule(
        name="Block embeddings endpoint",
        path_pattern=r"/v1/embeddings",
        method="POST",
        action=DPIAction.BLOCK,
    ),
    # Allow structural/read-only endpoints
    DPIRule(
        name="Allow model listing",
        path_pattern=r"/v1/models",
        method="GET",
        action=DPIAction.ALLOW,
    ),
    DPIRule(
        name="Allow engine listing",
        path_pattern=r"/v1/engines",
        method="GET",
        action=DPIAction.ALLOW,
    ),
]


# ── Rule engine ────────────────────────────────────────────────────────────

@dataclass
class DPIRuleEngine:
    """Evaluates an ordered list of DPI rules against incoming requests.

    The first matching rule wins.  If no rule matches, the default action
    (``DPIAction.ALLOW``) is returned.
    """
    rules: list[DPIRule] = field(default_factory=lambda: list(DEFAULT_DPI_RULES))

    def evaluate(self, path: str, method: str) -> tuple[DPIAction, DPIRule | None]:
        """Return the action and matched rule for the given request.

        Returns ``(DPIAction.ALLOW, None)`` when no rule matches.
        """
        for rule in self.rules:
            if rule.matches(path, method):
                return rule.action, rule
        return DPIAction.ALLOW, None

    # ── Persistence helpers ────────────────────────────────────────────────

    def to_list(self) -> list[dict]:
        return [r.to_dict() for r in self.rules]

    @classmethod
    def from_list(cls, data: list[dict]) -> DPIRuleEngine:
        rules = [DPIRule.from_dict(d) for d in data]
        return cls(rules=rules)

    # ── Mutation helpers ───────────────────────────────────────────────────

    def add_rule(self, rule: DPIRule) -> None:
        self.rules.append(rule)

    def remove_rule(self, name: str) -> bool:
        before = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < before

    def set_rule_enabled(self, name: str, enabled: bool) -> bool:
        for i, rule in enumerate(self.rules):
            if rule.name == name:
                self.rules[i] = DPIRule(
                    name=rule.name,
                    path_pattern=rule.path_pattern,
                    method=rule.method,
                    action=rule.action,
                    enabled=enabled,
                )
                return True
        return False
