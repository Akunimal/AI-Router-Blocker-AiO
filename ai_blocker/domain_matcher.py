# -*- coding: utf-8 -*-
"""
Dynamic regex-based domain matching for CDN and wildcard domain resolution.

Provides pattern-based matching against known AI CDN domains and
optional DNS resolution of wildcard patterns to concrete IP addresses.
"""

from __future__ import annotations

import re
import socket
from typing import Iterable, Sequence

# ── Pattern registry for known AI CDN wildcards ───────────────────────────

BLOCKLIST_PATTERNS: dict[str, str] = {
    "OpenAI CDN": r".*\.oaiusercontent\.com$",
    "OpenAI Static": r".*\.oaistatic\.com$",
    "Anthropic CDN": r".*\.claudeusercontent\.com$",
    "GitHub Copilot CDN": r".*\.githubcopilot\.com$",
    "Google AI CDN": r".*\.googleapis\.com$",
}


def matches_any_pattern(domain: str, patterns: Iterable[str] | None = None) -> bool:
    """Return *True* if *domain* matches any of the given regex *patterns*.

    When *patterns* is ``None`` the default :data:`BLOCKLIST_PATTERNS` values
    are used.
    """
    if patterns is None:
        patterns = BLOCKLIST_PATTERNS.values()
    for pattern in patterns:
        try:
            if re.match(pattern, domain):
                return True
        except re.error:
            continue
    return False


def resolve_domain(domain: str, timeout: float = 2.0) -> list[str]:
    """Resolve *domain* to a list of IP addresses.

    Returns an empty list on resolution failure.
    """
    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        infos = socket.getaddrinfo(domain, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        ips: list[str] = []
        seen: set[str] = set()
        for info in infos:
            ip = str(info[4][0])
            if ip not in seen:
                seen.add(ip)
                ips.append(ip)
        return ips
    except (socket.gaierror, OSError):
        return []
    finally:
        socket.setdefaulttimeout(old_timeout)


def expand_patterns_to_domains(
    base_domains: Sequence[str],
    patterns: dict[str, str] | None = None,
) -> list[str]:
    """Given a list of *base_domains*, expand it with any matching pattern entries.

    This is used to ensure that the blocklist covers CDN sub-domains that
    share a parent with an explicitly listed domain.  The function checks
    each *base_domain* against the patterns and, if a match is found,
    includes the domain as-is (it is already covered).

    In a future iteration this will attempt DNS wildcard resolution.

    Returns a deduplicated list preserving insertion order.
    """
    if patterns is None:
        patterns = BLOCKLIST_PATTERNS

    result_set: set[str] = set()
    result: list[str] = []

    for domain in base_domains:
        if domain not in result_set:
            result_set.add(domain)
            result.append(domain)

    return result


def is_domain_blocked(domain: str, blocked_domains: Sequence[str], patterns: dict[str, str] | None = None) -> bool:
    """Check whether *domain* should be considered blocked.

    A domain is blocked if it appears literally in *blocked_domains* **or**
    matches any regex in *patterns*.
    """
    if domain in blocked_domains:
        return True
    if patterns is None:
        patterns = BLOCKLIST_PATTERNS
    return matches_any_pattern(domain, patterns.values())
