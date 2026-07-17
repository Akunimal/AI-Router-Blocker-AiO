# -*- coding: utf-8 -*-
"""
Data Loss Prevention (DLP) engine for real-time sanitization of outbound AI
prompt request bodies.

Detects and redacts sensitive data including API keys, cloud credentials,
PII, private keys, and license-conflicting source code headers before they
are forwarded to cloud AI providers.
"""

from __future__ import annotations

import fnmatch
import json
import os
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
    INTERNAL_IP = "internal_ip"
    CLOUD_TOKEN = "cloud_token"
    DB_CONNECTION_STRING = "db_connection_string"
    ENV_VAR_REFERENCE = "env_var_reference"


@dataclass(frozen=True)
class DLPFinding:
    """A single sensitive data finding within a text body."""
    finding_type: FindingType
    matched_text: str
    start: int
    end: int
    confidence: float = 1.0  # 0.0?1.0

class DLPAction(Enum):
    """Action to take when DLP findings match."""
    REDACT = "redact"
    BLOCK = "block"
    LOG_ONLY = "log_only"
    PASS_THROUGH = "pass_through"


@dataclass
class DLPPolicy:
    """Per-domain or per-route DLP policy override."""
    action: DLPAction = DLPAction.REDACT
    scan_secrets: bool | None = None
    scan_pii: bool | None = None
    scan_licenses: bool | None = None
    scan_internal_ips: bool | None = None
    scan_cloud_tokens: bool | None = None
    scan_db_strings: bool | None = None
    scan_env_vars: bool | None = None


@dataclass
class DLPRouteOverride:
    """A route-specific DLP policy override."""
    domain_pattern: str = "*"
    path_pattern: str = "*"
    policy: DLPPolicy | None = None


def _default_policy_path() -> str:
    try:
        from ai_blocker.config import get_config_path
        base = os.path.dirname(get_config_path())
    except Exception:
        base = os.path.expanduser("~/.config/ai-devsec-gateway")
    return os.path.join(base, "dlp_policies.json")


class DLPPolicyManager:
    """Loads, resolves, and persists DLP policies."""

    def __init__(self, policies_path=None):
        self._policies_path = policies_path or _default_policy_path()
        self._default_policy = DLPPolicy()
        self._overrides = []
        self._load()

    @property
    def default_policy(self):
        return self._default_policy

    @default_policy.setter
    def default_policy(self, p):
        self._default_policy = p

    @property
    def overrides(self):
        return list(self._overrides)

    def resolve(self, domain, path):
        dl = domain.lower()
        pl = path.lower()
        for r in self._overrides:
            if fnmatch.fnmatch(dl, r.domain_pattern.lower()):
                if fnmatch.fnmatch(pl, r.path_pattern.lower()):
                    return r.policy
        return self._default_policy

    def add_override(self, domain, path="*", policy=None):
        self._overrides.append(DLPRouteOverride(
            domain_pattern=domain, path_pattern=path,
            policy=policy or DLPPolicy(),
        ))

    def save(self):
        d = self._to_dict()
        os.makedirs(os.path.dirname(self._policies_path), exist_ok=True)
        with open(self._policies_path, "w") as f:
            json.dump(d, f, indent=2)

    def reload(self):
        self._load()

    def _to_dict(self):
        def _pd(p):
            d = {"action": p.action.value}
            for cat in ("scan_secrets", "scan_pii", "scan_licenses",
                        "scan_internal_ips", "scan_cloud_tokens",
                        "scan_db_strings", "scan_env_vars"):
                val = getattr(p, cat)
                if val is not None:
                    d[cat] = val
            return d
        return {
            "default_policy": _pd(self._default_policy),
            "overrides": [
                {
                    "domain_pattern": r.domain_pattern,
                    "path_pattern": r.path_pattern,
                    "policy": _pd(r.policy),
                }
                for r in self._overrides
            ],
        }

    @staticmethod
    def _policy_from_dict(d: dict):
        am = {"redact": DLPAction.REDACT, "block": DLPAction.BLOCK,
              "log_only": DLPAction.LOG_ONLY, "pass_through": DLPAction.PASS_THROUGH}
        return DLPPolicy(
            action=am.get(d.get("action", "redact"), DLPAction.REDACT),
            scan_secrets=d.get("scan_secrets"),
            scan_pii=d.get("scan_pii"),
            scan_licenses=d.get("scan_licenses"),
            scan_internal_ips=d.get("scan_internal_ips"),
            scan_cloud_tokens=d.get("scan_cloud_tokens"),
            scan_db_strings=d.get("scan_db_strings"),
            scan_env_vars=d.get("scan_env_vars"),
        )

    def _load(self):
        """Load policies from JSON file."""
        try:
            import json
            with open(self._policies_path) as f:
                data = json.load(f)
        except (FileNotFoundError, ValueError):
            self._default_policy = DLPPolicy()
            self._overrides = []
            return
        self._default_policy = self._policy_from_dict(data.get("default_policy", {}))
        self._overrides = []
        for r in data.get("overrides", []):
            self._overrides.append(DLPRouteOverride(
                domain_pattern=r.get("domain_pattern", "*"),
                path_pattern=r.get("path_pattern", "*"),
                policy=self._policy_from_dict(r.get("policy", {})),
            ))

# ???? Pattern definitions ????????????????????????????????????????????????????????????????????????????????????????????????????????

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

_CLOUD_TOKEN_PATTERNS: list[tuple[FindingType, str, float]] = [
    (FindingType.CLOUD_TOKEN, r"ya29\.[a-zA-Z0-9_-]{50,}", 0.95),
    (FindingType.CLOUD_TOKEN, r"hf_[a-zA-Z0-9_-]{20,}", 0.95),
    (FindingType.CLOUD_TOKEN, r"AccountKey=[a-zA-Z0-9+/=]{40,}", 0.90),
    (FindingType.CLOUD_TOKEN, r"npm_[a-zA-Z0-9_-]{30,}", 0.90),
    (FindingType.CLOUD_TOKEN, r"xox[baprs]-[a-zA-Z0-9_-]{20,}", 0.90),
]

_INTERNAL_IP_PATTERNS: list[tuple[FindingType, str, float]] = [
    (FindingType.INTERNAL_IP, r'\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', 0.70),
    (FindingType.INTERNAL_IP, r'\b(?:172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b', 0.70),
    (FindingType.INTERNAL_IP, r'\b(?:192\.168\.\d{1,3}\.\d{1,3})\b', 0.70),
    (FindingType.INTERNAL_IP, r'\b(?:127\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', 0.60),
]

_DB_STRING_PATTERNS: list[tuple[FindingType, str, float]] = [
    (FindingType.DB_CONNECTION_STRING, '(?:postgresql|mysql|mongodb|redis|rediss)://[^\\s\x22\x27]+', 0.85),
    (FindingType.DB_CONNECTION_STRING, '(?:jdbc:[a-z]+://[^\\s\x22\x27]+)', 0.80),
]

_ENV_VAR_PATTERNS: list[tuple[FindingType, str, float]] = [
    (FindingType.ENV_VAR_REFERENCE, '(?:os\\.environ|os\\.getenv)(?:\\(|\\[)[\x22\x27][A-Z_]{3,}[\x22\x27](?:\\)|\\])', 0.50),
    (FindingType.ENV_VAR_REFERENCE, r'(?:process\.env\.)[A-Z_]{3,}', 0.50),
    (FindingType.ENV_VAR_REFERENCE, r'(?:export|set)\s+[A-Z_]{3,}\s*=', 0.40),
]


# ?=??=? Scanning engine ??????????????????????????????????????????????????????????????????????????????????????????????????????????????

@dataclass
class DLPEngine:
    """Scans text for sensitive data and optionally redacts it.

    Configuration flags control which categories of data are scanned:
      * ``scan_secrets`` ? API keys, cloud credentials, private keys
      * ``scan_pii`` ? emails, SSNs, credit cards, phone numbers
      * ``scan_licenses`` ? copyleft license headers
    """
    scan_secrets: bool = True
    scan_pii: bool = True
    scan_licenses: bool = False
    scan_internal_ips: bool = False
    scan_cloud_tokens: bool = True
    scan_db_strings: bool = True
    scan_env_vars: bool = False

    def scan(self, text: str, policy: DLPPolicy | None = None) -> list[DLPFinding]:
        """Return all findings in *text*.

        If *policy* is provided, its per-category overrides are applied
        on top of the engine's default flags.
        """
        findings: list[DLPFinding] = []

        patterns: list[tuple[FindingType, str, float]] = []
        if (policy is None and self.scan_secrets) or (policy is not None and policy.scan_secrets is None and self.scan_secrets) or (policy is not None and policy.scan_secrets is True):
            patterns.extend(_SECRET_PATTERNS)
        if (policy is None and self.scan_pii) or (policy is not None and policy.scan_pii is None and self.scan_pii) or (policy is not None and policy.scan_pii is True):
            patterns.extend(_PII_PATTERNS)
        if (policy is None and self.scan_licenses) or (policy is not None and policy.scan_licenses is None and self.scan_licenses) or (policy is not None and policy.scan_licenses is True):
            patterns.extend(_LICENSE_PATTERNS)
        if (policy is None and self.scan_internal_ips) or (policy is not None and policy.scan_internal_ips is None and self.scan_internal_ips) or (policy is not None and policy.scan_internal_ips is True):
            patterns.extend(_INTERNAL_IP_PATTERNS)
        if (policy is None and self.scan_cloud_tokens) or (policy is not None and policy.scan_cloud_tokens is None and self.scan_cloud_tokens) or (policy is not None and policy.scan_cloud_tokens is True):
            patterns.extend(_CLOUD_TOKEN_PATTERNS)
        if (policy is None and self.scan_db_strings) or (policy is not None and policy.scan_db_strings is None and self.scan_db_strings) or (policy is not None and policy.scan_db_strings is True):
            patterns.extend(_DB_STRING_PATTERNS)
        if (policy is None and self.scan_env_vars) or (policy is not None and policy.scan_env_vars is None and self.scan_env_vars) or (policy is not None and policy.scan_env_vars is True):
            patterns.extend(_ENV_VAR_PATTERNS)

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

    def redact_structured(self, text: str, policy: DLPPolicy | None = None) -> str:
        """Redact sensitive data in JSON text while preserving structure.

        Walks the parsed JSON tree depth-first.  String values are scanned
        and redacted individually.  Non-string JSON values are kept as-is.
        If *text* is not valid JSON, falls back to plain :meth:
edact.

        If *policy* is provided, it is forwarded to the scan step.
        """
        try:
            parsed = json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return self.redact(text) if policy is None else self.redact(text, self.scan(text, policy=policy))

        redacted = self._redact_value(parsed)

        # Compact output to preserve original whitespace intent
        result = json.dumps(redacted, ensure_ascii=False, indent=2)
        return result

    def _redact_value(self, value):
        """Recursively redact a parsed JSON value."""
        if isinstance(value, dict):
            return {k: self._redact_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._redact_value(v) for v in value]
        elif isinstance(value, str):
            findings = self.scan(value)
            if findings:
                return self.redact(value, findings)
            return value
        else:
            return value

    def has_sensitive_data(self, text: str) -> bool:
        """Return *True* if *text* contains any sensitive data."""
        return len(self.scan(text)) > 0

