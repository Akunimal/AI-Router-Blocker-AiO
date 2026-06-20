# -*- coding: utf-8 -*-
"""
Token traffic monitor with rate limiting and expenditure caps.

Tracks estimated input/output token counts per request, enforces
hourly caps, and provides aggregated traffic statistics.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field


@dataclass(frozen=True)
class RequestRecord:
    """A single request's token statistics."""
    timestamp: float
    tokens_in: int
    tokens_out: int
    domain: str = ""
    path: str = ""


@dataclass
class TokenMonitor:
    """Rate-limiting token monitor with configurable hourly caps.

    Attributes:
        max_tokens_per_hour: Hourly token cap (0 = unlimited).
        max_requests_per_minute: Per-minute request rate limit (0 = unlimited).
    """
    max_tokens_per_hour: int = 0
    max_requests_per_minute: int = 0

    _records: deque[RequestRecord] = field(default_factory=deque)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    @staticmethod
    def estimate_tokens(text: str | bytes) -> int:
        """Estimate token count using the ~4 chars per token heuristic."""
        if isinstance(text, bytes):
            text = text.decode("utf-8", errors="ignore")
        return max(1, len(text) // 4)

    def record(self, tokens_in: int, tokens_out: int, domain: str = "", path: str = "") -> None:
        """Record a completed request's token counts."""
        with self._lock:
            self._records.append(RequestRecord(
                timestamp=time.time(),
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                domain=domain,
                path=path,
            ))
            self._prune()

    def is_over_limit(self) -> bool:
        """Check whether the current traffic exceeds configured caps."""
        with self._lock:
            self._prune()
            if self.max_tokens_per_hour > 0:
                hourly = self._hourly_total()
                if hourly >= self.max_tokens_per_hour:
                    return True
            if self.max_requests_per_minute > 0:
                minute_count = self._minute_request_count()
                if minute_count >= self.max_requests_per_minute:
                    return True
        return False

    def get_hourly_summary(self) -> dict[str, int | float]:
        """Return token and request counts for the current hour window."""
        with self._lock:
            self._prune()
            now = time.time()
            cutoff = now - 3600
            tokens_in = 0
            tokens_out = 0
            count = 0
            for r in self._records:
                if r.timestamp >= cutoff:
                    tokens_in += r.tokens_in
                    tokens_out += r.tokens_out
                    count += 1
            return {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "total_tokens": tokens_in + tokens_out,
                "request_count": count,
                "cap": self.max_tokens_per_hour,
                "cap_usage_pct": (
                    round((tokens_in + tokens_out) / self.max_tokens_per_hour * 100, 1)
                    if self.max_tokens_per_hour > 0
                    else 0.0
                ),
            }

    def get_per_domain_breakdown(self) -> dict[str, dict[str, int]]:
        """Return per-domain token breakdown for the current hour."""
        with self._lock:
            self._prune()
            now = time.time()
            cutoff = now - 3600
            breakdown: dict[str, dict[str, int]] = {}
            for r in self._records:
                if r.timestamp >= cutoff:
                    key = r.domain or "unknown"
                    if key not in breakdown:
                        breakdown[key] = {"tokens_in": 0, "tokens_out": 0, "requests": 0}
                    breakdown[key]["tokens_in"] += r.tokens_in
                    breakdown[key]["tokens_out"] += r.tokens_out
                    breakdown[key]["requests"] += 1
            return breakdown

    def reset(self) -> None:
        """Clear all recorded data."""
        with self._lock:
            self._records.clear()

    # ── Private helpers ────────────────────────────────────────────────────

    def _prune(self) -> None:
        """Remove records older than 1 hour."""
        cutoff = time.time() - 3600
        while self._records and self._records[0].timestamp < cutoff:
            self._records.popleft()

    def _hourly_total(self) -> int:
        return sum(r.tokens_in + r.tokens_out for r in self._records)

    def _minute_request_count(self) -> int:
        cutoff = time.time() - 60
        return sum(1 for r in self._records if r.timestamp >= cutoff)
