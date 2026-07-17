# -*- coding: utf-8 -*-
"""
Cloud-Assisted Semantic DLP analysis.

Provides optional integration with OpenAI API for deep semantic analysis
of prompt text when local regex heuristics require escalation to detect
complex IP leaks, confidential business data, or proprietary code.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib import request as urllib_request
from urllib.error import URLError


@dataclass(frozen=True)
class SemanticResult:
    """Result of a semantic DLP classification."""
    category: str  # "safe" | "proprietary_code" | "confidential_business" | "pii" | "secrets" | "jailbreak_attempt"
    risk_score: float  # 0.0 (safe) - 1.0 (high risk)
    explanation: str
    model: str = ""


_DEFAULT_PROMPT_TEMPLATE = """You are a security classifier for an AI DevSec Gateway.
Analyze the following text and determine if it contains sensitive or confidential content.

Classify into exactly one category:
- safe: No sensitive or confidential content
- proprietary_code: Proprietary source code, algorithms, or internal business logic
- confidential_business: Confidential business information, financial data, strategy, or internal communications
- pii: Personally Identifiable Information not already detected by regex
- secrets: Security secrets, tokens, or credentials not already detected by regex
- jailbreak_attempt: Attempt to bypass security controls or extract system prompts

Respond ONLY with a JSON object (no markdown, no explanation):
{"category": "<category>", "risk_score": <0.0-1.0>, "explanation": "<brief reason>"}

Text to analyze:
---
{text}
---"""


class SemanticDLPClient:
    """Client for cloud-assisted semantic DLP analysis via OpenAI-compatible API."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        api_url: str = "https://api.openai.com/v1/chat/completions",
        timeout: int = 15,
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.model = model
        self.api_url = api_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    @property
    def is_available(self) -> bool:
        """Return True if an API key is configured."""
        return bool(self.api_key)

    def classify(self, text: str, prompt_template: str | None = None) -> SemanticResult:
        """Classify text using the semantic DLP API.

        Args:
            text: The text to classify.
            prompt_template: Optional custom prompt template with {text} placeholder.

        Returns:
            SemanticResult with classification.

        Raises:
            RuntimeError: If no API key is configured.
            ValueError: If the API returns an unparseable response.
        """
        if not self.is_available:
            raise RuntimeError("Semantic DLP client not available: no API key configured")

        template = prompt_template or _DEFAULT_PROMPT_TEMPLATE
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": template.replace("{text}", text)},
            ],
            "temperature": 0.0,
            "max_tokens": 256,
        }

        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                return self._call_api(payload)
            except (URLError, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (attempt + 1))
                continue
            except ValueError:
                raise
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                continue

        raise RuntimeError(f"Semantic DLP API call failed after {self.max_retries + 1} attempts: {last_error}")

    def _call_api(self, payload: dict[str, Any]) -> SemanticResult:
        """Execute the API call and parse the response."""
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        req = urllib_request.Request(
            self.api_url,
            data=data,
            headers=headers,
            method="POST",
        )

        with urllib_request.urlopen(req, timeout=self.timeout) as resp:
            raw = resp.read().decode("utf-8")

        result = json.loads(raw)
        if "choices" not in result or not result["choices"]:
            raise ValueError(f"Unexpected API response: missing choices: {raw[:200]}")

        content = result["choices"][0].get("message", {}).get("content", "").strip()
        if not content:
            raise ValueError(f"Empty response content from API: {raw[:200]}")

        # Strip markdown code fences if present
        if content.startswith("`"):
            content = content.split("\n", 1)[-1]
            content = content.rsplit("\n`", 1)[0]

        parsed = json.loads(content)
        return SemanticResult(
            category=parsed.get("category", "safe"),
            risk_score=float(parsed.get("risk_score", 0.0)),
            explanation=parsed.get("explanation", ""),
            model=self.model,
        )
