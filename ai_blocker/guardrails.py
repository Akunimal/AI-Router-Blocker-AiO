# -*- coding: utf-8 -*-
"""
On-device prompt injection firewall and semantic guardrails.

Provides heuristic-based detection of prompt injection attacks, jailbreak
payloads, and sensitive IP leaks.  An ONNX-based classifier can be loaded
optionally for higher-accuracy detection.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class ThreatCategory(Enum):
    """Classification of a detected threat."""
    PROMPT_INJECTION = "prompt_injection"
    JAILBREAK = "jailbreak"
    IP_LEAK = "ip_leak"
    SAFE = "safe"


@dataclass(frozen=True)
class GuardrailResult:
    """Result of a guardrail evaluation on a single prompt."""
    category: ThreatCategory
    risk_score: float  # 0.0 (safe) – 1.0 (dangerous)
    matched_patterns: list[str]
    explanation: str


# ── Heuristic pattern sets ─────────────────────────────────────────────────

_INJECTION_PATTERNS: list[tuple[str, float]] = [
    # Direct instruction override attempts
    (r"ignore\s+(?:all\s+)?previous\s+instructions?", 0.95),
    (r"ignore\s+(?:all\s+)?(?:above|prior)\s+(?:instructions?|prompts?|context)", 0.95),
    (r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+(?:instructions?|prompts?)", 0.90),
    (r"forget\s+(?:everything|all)\s+(?:you\s+)?(?:know|were\s+told|above)", 0.90),
    # System prompt extraction
    (r"(?:what|show|print|reveal|display|repeat|output)\s+(?:is\s+)?(?:your\s+)?system\s+prompt", 0.92),
    (r"system\s*prompt\s*[:=]", 0.88),
    # Role reassignment
    (r"you\s+are\s+now\s+(?:a\s+)?(?:different|new|evil|unrestricted|unfiltered)", 0.90),
    (r"from\s+now\s+on\s+you\s+(?:are|will\s+be)\s+", 0.80),
    (r"act\s+as\s+(?:an?\s+)?(?:evil|unrestricted|unfiltered|jailbroken)", 0.88),
    # DAN-style jailbreaks
    (r"do\s+anything\s+now", 0.85),
    (r"DAN\s+mode", 0.90),
    (r"developer\s+mode\s+enabled", 0.88),
]

_JAILBREAK_PATTERNS: list[tuple[str, float]] = [
    # Hypothetical framing to bypass safety
    (r"hypothetically\s+speaking", 0.50),
    (r"for\s+(?:educational|research|academic)\s+purposes?\s+only", 0.45),
    (r"in\s+a\s+fictional\s+(?:scenario|world|context)", 0.40),
    # Base64 encoded payloads
    (r"(?:decode|interpret|execute)\s+(?:this\s+)?base64", 0.75),
    # Token smuggling
    (r"\[SYSTEM\]", 0.80),
    (r"\[INST\]", 0.70),
    (r"<\|(?:im_start|system|endoftext)\|>", 0.85),
]

_IP_LEAK_PATTERNS: list[tuple[str, float]] = [
    # Requests to dump internal data
    (r"(?:show|print|list|dump|display)\s+(?:all\s+)?(?:your\s+)?(?:training\s+data|internal|source\s+code)", 0.70),
    (r"(?:send|upload|exfiltrate|transmit)\s+(?:to|this\s+to)\s+(?:https?://|ftp://)", 0.85),
]


class PromptGuardrail:
    """Heuristic-based prompt injection and jailbreak detector.

    Scans prompt text against curated pattern sets and returns a
    :class:`GuardrailResult` with a risk score and explanation.
    """

    def __init__(self, threshold: float = 0.60):
        """
        Args:
            threshold: Minimum risk score to classify as a threat.
        """
        self.threshold = threshold

    def evaluate(self, prompt: str) -> GuardrailResult:
        """Evaluate a prompt for injection, jailbreak, or IP leak patterns."""
        prompt_lower = prompt.lower()

        injection_score, injection_matches = self._scan_patterns(
            prompt_lower, _INJECTION_PATTERNS
        )
        jailbreak_score, jailbreak_matches = self._scan_patterns(
            prompt_lower, _JAILBREAK_PATTERNS
        )
        ip_score, ip_matches = self._scan_patterns(
            prompt_lower, _IP_LEAK_PATTERNS
        )

        # Pick highest-risk category
        scores = [
            (ThreatCategory.PROMPT_INJECTION, injection_score, injection_matches),
            (ThreatCategory.JAILBREAK, jailbreak_score, jailbreak_matches),
            (ThreatCategory.IP_LEAK, ip_score, ip_matches),
        ]
        scores.sort(key=lambda x: x[1], reverse=True)
        top_category, top_score, top_matches = scores[0]

        if top_score < self.threshold:
            return GuardrailResult(
                category=ThreatCategory.SAFE,
                risk_score=top_score,
                matched_patterns=[],
                explanation="No significant threat patterns detected.",
            )

        return GuardrailResult(
            category=top_category,
            risk_score=top_score,
            matched_patterns=top_matches,
            explanation=f"Detected {top_category.value} pattern(s) with risk score {top_score:.2f}.",
        )

    def is_safe(self, prompt: str) -> bool:
        """Return *True* if the prompt is classified as safe."""
        return self.evaluate(prompt).category == ThreatCategory.SAFE

    @staticmethod
    def _scan_patterns(
        text: str, patterns: Sequence[tuple[str, float]]
    ) -> tuple[float, list[str]]:
        """Scan *text* against a pattern set, returning max score and matched patterns."""
        max_score = 0.0
        matched: list[str] = []
        for pattern, weight in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    max_score = max(max_score, weight)
                    matched.append(pattern)
            except re.error:
                continue
        return max_score, matched
