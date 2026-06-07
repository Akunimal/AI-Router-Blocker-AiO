# -*- coding: utf-8 -*-
"""
Data Loss Prevention (DLP) engine for real-time sanitization of outbound AI
prompt request bodies.

Detects and redacts sensitive data including API keys, cloud credentials,
PII, private keys, and license-conflicting source code headers before they
are forwarded to cloud AI providers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Sequence


class FindingType(Enum):
    """Category of a sensitive data finding."""
    API_KEY = "api_key"
    AWS_KEY = "aws_key"
    GITHUB_TOKEN = "github_token"
    PRIVATE_KEY = "private_key"
    JWT = "jwt"
    GENERIC_SECRET = "generic_secret"
    EMAIL = "email"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    PHONE = "phone"
    LICENSE_CONFLICT = "license_conflict"


@dataclass(frozen=True)
class DLPFinding:
    """A single sensitive data finding within a text body."""
    finding_type: FindingType
    matched_text: str
    start: int
    end: int
    confidence: float = 1.0  # 0.0–1.0


# ── Pattern definitions ────────────────────────────────────────────────────

_SECRET_PATTERNS: list[tuple[FindingType, str, float]] = [
    # OpenAI / Stripe-style keys
    (FindingType.API_KEY, r'(?:sk-|pk-)(?:proj-)?[a-zA-Z0-9_\-]{20,}', 0.95),
    # Anthropic keys
    (FindingType.API_KEY, r'sk-ant-[a-zA-Z0-9_\-]{20,}', 0.98),
    # AWS Access Key IDs
    (FindingType.AWS_KEY, r'AKIA[0-9A-Z]{16}', 0.98),
    # AWS Secret Access Keys (often appear near AKIA lines)
    (FindingType.AWS_KEY, r'(?:aws_secret_access_key|AWS_SECRET_ACCESS_KEY)\s*[=:]\s*[A-Za-z0-9/+=]{40}', 0.90),
    # GitHub tokens
    (FindingType.GITHUB_TOKEN, r'(?:ghp_|gho_|ghs_|ghr_)[a-zA-Z0-9]{36}', 0.98),
    # PEM private keys
    (FindingType.PRIVATE_KEY, r'-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----', 0.99),
    # JWTs (three base64url segments)
    (FindingType.JWT, r'eyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}', 0.85),
    # Generic secret assignments (key = "..." or token = "...")
    (FindingType.GENERIC_SECRET, r'(?:password|secret|token|api_key|apikey)\s*[=:]\s*["\'][^"\']{8,}["\']', 0.70),
]

_PII_PATTERNS: list[tuple[FindingType, str, float]] = [
    # Email addresses
    (FindingType.EMAIL, r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}', 0.80),
    # US Social Security Numbers
    (FindingType.SSN, r'\b\d{3}-\d{2}-\d{4}\b', 0.90),
    # Credit card numbers (Visa, MC, Amex, Discover)
    (FindingType.CREDIT_CARD, r'\b(?:4\d{3}|5[1-5]\d{2}|3[47]\d{2}|6011)[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 0.85),
    # US phone numbers
    (FindingType.PHONE, r'\b(?:\+1[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b', 0.60),
]

_LICENSE_PATTERNS: list[tuple[FindingType, str, float]] = [
    # GPL / AGPL headers in code
    (FindingType.LICENSE_CONFLICT, r'(?:GNU General Public License|GPL-[23]\.0|AGPL-3\.0)', 0.90),
    # LGPL headers
    (FindingType.LICENSE_CONFLICT, r'(?:GNU Lesser General Public License|LGPL-[23]\.0)', 0.85),
]


# ── Scanning engine ───────────────────────────────────────────────────────

@dataclass
class DLPEngine:
    """Scans text for sensitive data and optionally redacts it.

    Configuration flags control which categories of data are scanned:
      * ``scan_secrets`` — API keys, cloud credentials, private keys
      * ``scan_pii`` — emails, SSNs, credit cards, phone numbers
      * ``scan_licenses`` — copyleft license headers
    """
    scan_secrets: bool = True
    scan_pii: bool = True
    scan_licenses: bool = True

    def scan(self, text: str) -> list[DLPFinding]:
        """Return all findings in *text*."""
        findings: list[DLPFinding] = []

        patterns: list[tuple[FindingType, str, float]] = []
        if self.scan_secrets:
            patterns.extend(_SECRET_PATTERNS)
        if self.scan_pii:
            patterns.extend(_PII_PATTERNS)
        if self.scan_licenses:
            patterns.extend(_LICENSE_PATTERNS)

        for finding_type, pattern, confidence in patterns:
            try:
                for m in re.finditer(pattern, text):
                    findings.append(DLPFinding(
                        finding_type=finding_type,
                        matched_text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        confidence=confidence,
                    ))
            except re.error:
                continue

        # Deduplicate overlapping findings: keep higher confidence
        findings.sort(key=lambda f: (f.start, -f.confidence))
        deduplicated: list[DLPFinding] = []
        last_end = -1
        for f in findings:
            if f.start >= last_end:
                deduplicated.append(f)
                last_end = f.end

        return deduplicated

    def scan_for_secrets(self, text: str) -> list[DLPFinding]:
        """Scan only for secrets and credentials."""
        old_pii, old_lic = self.scan_pii, self.scan_licenses
        self.scan_pii = False
        self.scan_licenses = False
        try:
            return self.scan(text)
        finally:
            self.scan_pii = old_pii
            self.scan_licenses = old_lic

    def scan_for_pii(self, text: str) -> list[DLPFinding]:
        """Scan only for PII."""
        old_sec, old_lic = self.scan_secrets, self.scan_licenses
        self.scan_secrets = False
        self.scan_licenses = False
        try:
            return self.scan(text)
        finally:
            self.scan_secrets = old_sec
            self.scan_licenses = old_lic

    def redact(self, text: str, findings: Sequence[DLPFinding] | None = None) -> str:
        """Return *text* with all findings replaced by ``[REDACTED:<TYPE>]``.

        If *findings* is ``None``, a full scan is performed first.
        """
        if findings is None:
            findings = self.scan(text)

        if not findings:
            return text

        # Sort by start position in reverse to replace from end to start
        sorted_findings = sorted(findings, key=lambda f: f.start, reverse=True)
        result = text
        for f in sorted_findings:
            placeholder = f"[REDACTED:{f.finding_type.value.upper()}]"
            result = result[:f.start] + placeholder + result[f.end:]

        return result

    def has_sensitive_data(self, text: str) -> bool:
        """Return *True* if *text* contains any sensitive data."""
        return len(self.scan(text)) > 0
