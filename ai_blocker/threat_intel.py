# -*- coding: utf-8 -*-
"""AI-Powered Threat Intelligence: request pattern analysis and anomaly detection."""
from __future__ import annotations

import json
import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class RequestRecord:
    domain: str
    path: str = ""
    method: str = "POST"
    body_hash: str = ""
    token_count: int = 0
    timestamp: float = field(default_factory=time.time)

@dataclass
class AnomalyScore:
    domain: str
    request_rate: float
    token_rate: float
    rate_zscore: float
    token_zscore: float
    is_anomalous: bool = False
    reason: str = ""

class RequestAnalyzer:
    def __init__(self, window_seconds: int = 60, zscore_threshold: float = 3.0, max_domains: int = 50):
        self.window_seconds = window_seconds
        self.zscore_threshold = zscore_threshold
        self._records: dict[str, deque[RequestRecord]] = defaultdict(lambda: deque(maxlen=10000))
        self._baselines: dict[str, tuple[float, float]] = {}

    def record(self, domain: str, path: str = "", method: str = "POST", body_hash: str = "", token_count: int = 0) -> None:
        rec = RequestRecord(domain=domain, path=path, method=method, body_hash=body_hash, token_count=token_count)
        self._records[domain].append(rec)
        self._prune(domain)

    def analyze(self, domain: str | None = None) -> list[AnomalyScore]:
        domains = [domain] if domain else list(self._records.keys())
        results: list[AnomalyScore] = []
        now = time.time()
        for d in domains:
            self._prune(d)
            records = list(self._records.get(d, []))
            if len(records) < 5:
                continue
            window = now - self.window_seconds
            recent = [r for r in records if r.timestamp >= window]
            if not recent:
                continue
            duration = max(r.timestamp for r in recent) - min(r.timestamp for r in recent)
            duration = duration or 0.001
            rate = len(recent) / duration
            tokens = sum(r.token_count for r in recent)
            token_rate = tokens / duration
            mean_rate, std_rate = self._baselines.get(d, (rate, rate * 0.5))
            rate_z = (rate - mean_rate) / (std_rate or 0.001)
            mean_tokens, std_tokens = 0.0, 1.0
            token_vals = [r.token_count for r in recent if r.token_count > 0]
            if token_vals:
                mean_tokens = sum(token_vals) / len(token_vals)
                std_tokens = (sum((t - mean_tokens)**2 for t in token_vals) / len(token_vals))**0.5 or 0.001
                token_z = (token_rate - mean_tokens) / std_tokens
            else:
                token_z = 0.0
            is_anom = abs(rate_z) > self.zscore_threshold or abs(token_z) > self.zscore_threshold
            reasons = []
            if abs(rate_z) > self.zscore_threshold:
                reasons.append(f"request rate anomaly (z={rate_z:.1f})")
            if abs(token_z) > self.zscore_threshold:
                reasons.append(f"token volume anomaly (z={token_z:.1f})")
            results.append(AnomalyScore(domain=d, request_rate=rate, token_rate=token_rate, rate_zscore=rate_z, token_zscore=token_z, is_anomalous=is_anom, reason="; ".join(reasons) if reasons else "normal"))
            if d in self._baselines:
                old_mean, old_std = self._baselines[d]
                self._baselines[d] = (0.9 * old_mean + 0.1 * rate, 0.9 * old_std + 0.1 * std_rate)
            else:
                self._baselines[d] = (rate, std_rate)
        return results

    def _prune(self, domain: str) -> None:
        cutoff = time.time() - self.window_seconds * 2
        dq = self._records.get(domain)
        if dq:
            while dq and dq[0].timestamp < cutoff:
                dq.popleft()

    @property
    def domains(self) -> list[str]:
        return list(self._records.keys())

    @property
    def total_observations(self) -> int:
        return sum(len(v) for v in self._records.values())
@dataclass
class LoopDetectionResult:
    body_hash: str
    count: int
    domain: str
    timespan: float
    is_looping: bool = False
    similarity: float = 0.0

class RecursiveLoopDetector:
    def __init__(self, max_identical: int = 5, window_seconds: int = 300):
        self.max_identical = max_identical
        self.window_seconds = window_seconds
        self._history: dict[str, list[tuple[float, str, str]]] = defaultdict(list)

    def record(self, body: str, domain: str = "", path: str = ""):
        h = hash(body)
        now = time.time()
        self._prune()
        self._history[domain].append((now, str(h), path))

    def check(self, body: str, domain: str = "") -> LoopDetectionResult | None:
        h = hash(body)
        now = time.time()
        cutoff = now - self.window_seconds
        domain_hist = [r for r in self._history.get(domain, []) if r[0] >= cutoff]
        matches = [r for r in domain_hist if r[1] == str(h)]
        if not matches:
            return None
        timespan = max(r[0] for r in matches) - min(r[0] for r in matches)
        is_loop = len(matches) >= self.max_identical
        similarity = min(1.0, len(matches) / self.max_identical)
        return LoopDetectionResult(body_hash=str(h), count=len(matches), domain=domain, timespan=timespan, is_looping=is_loop, similarity=similarity)

    def analyze(self, body: str, domain: str = "") -> LoopDetectionResult | None:
        return self.check(body, domain)

    def _prune(self):
        cutoff = time.time() - self.window_seconds * 2
        for domain in list(self._history.keys()):
            self._history[domain] = [(ts, h, p) for ts, h, p in self._history[domain] if ts >= cutoff]
            if not self._history[domain]:
                del self._history[domain]
class ThreatFeed:
    def __init__(self, feed_dir: str = ""):
        self.feed_dir = feed_dir or os.path.join(os.path.dirname(__file__), "..", "threat_feeds")
        self._iocs: dict[str, list[dict]] = {"domains": [], "hashes": [], "patterns": []}
        self._load()

    def _load(self):
        os.makedirs(self.feed_dir, exist_ok=True)
        for kind in ["domains", "hashes", "patterns"]:
            path = os.path.join(self.feed_dir, f"{kind}.json")
            if os.path.exists(path):
                try:
                    data = json.load(open(path, encoding='utf-8'))
                    self._iocs[kind] = data if isinstance(data, list) else []
                except (json.JSONDecodeError, OSError):
                    self._iocs[kind] = []

    def match_domain(self, domain: str) -> list[dict]:
        return [ioc for ioc in self._iocs["domains"] if domain == ioc.get("value") or domain.endswith("." + ioc.get("value", ""))]

    def match_body(self, body: str) -> list[dict]:
        results = []
        body_lower = body.lower()
        for ioc in self._iocs["patterns"]:
            pattern = ioc.get("value", "").lower()
            if pattern and pattern in body_lower:
                results.append(ioc)
        return results

    @property
    def count(self) -> int:
        return sum(len(v) for v in self._iocs.values())
@dataclass
class ThreatAlert:
    alert_type: str
    severity: str
    domain: str
    detail: str
    timestamp: float = field(default_factory=time.time)

class AlertSystem:
    def __init__(self, max_alerts: int = 100):
        self.max_alerts = max_alerts
        self._alerts: list[ThreatAlert] = []

    def emit(self, alert_type: str, severity: str, domain: str, detail: str) -> ThreatAlert:
        alert = ThreatAlert(alert_type=alert_type, severity=severity, domain=domain, detail=detail)
        self._alerts.append(alert)
        if len(self._alerts) > self.max_alerts:
            self._alerts = self._alerts[-self.max_alerts:]
        return alert

    def recent(self, count: int = 20) -> list[ThreatAlert]:
        return self._alerts[-count:]

    def by_severity(self, severity: str) -> list[ThreatAlert]:
        return [a for a in self._alerts if a.severity == severity]

    @property
    def total(self) -> int:
        return len(self._alerts)

    def clear(self):
        self._alerts.clear()
