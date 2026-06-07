# -*- coding: utf-8 -*-
"""Tests for the domain matcher module."""

from ai_blocker.domain_matcher import (
    BLOCKLIST_PATTERNS,
    expand_patterns_to_domains,
    is_domain_blocked,
    matches_any_pattern,
    resolve_domain,
)


class TestMatchesAnyPattern:
    def test_oai_cdn(self):
        assert matches_any_pattern("files.oaiusercontent.com")
        assert matches_any_pattern("cdn.oaiusercontent.com")

    def test_claude_cdn(self):
        assert matches_any_pattern("uploads.claudeusercontent.com")

    def test_copilot_cdn(self):
        assert matches_any_pattern("proxy.githubcopilot.com")

    def test_no_match_unrelated(self):
        assert not matches_any_pattern("example.com")
        assert not matches_any_pattern("google.com")

    def test_custom_patterns(self):
        patterns = [r".*\.custom\.ai$"]
        assert matches_any_pattern("api.custom.ai", patterns)
        assert not matches_any_pattern("custom.ai.com", patterns)

    def test_invalid_pattern_no_crash(self):
        patterns = [r"[invalid("]
        assert not matches_any_pattern("anything", patterns)


class TestIsDomainBlocked:
    def test_literal_match(self):
        blocked = ["api.openai.com", "claude.ai"]
        assert is_domain_blocked("api.openai.com", blocked)

    def test_pattern_match(self):
        blocked = ["api.openai.com"]
        assert is_domain_blocked("cdn.oaiusercontent.com", blocked)

    def test_not_blocked(self):
        blocked = ["api.openai.com"]
        assert not is_domain_blocked("example.com", blocked)

    def test_empty_blocklist(self):
        assert not is_domain_blocked("example.com", [], patterns={})


class TestExpandPatterns:
    def test_preserves_base_domains(self):
        base = ["api.openai.com", "claude.ai"]
        result = expand_patterns_to_domains(base)
        assert "api.openai.com" in result
        assert "claude.ai" in result

    def test_deduplicates(self):
        base = ["api.openai.com", "api.openai.com"]
        result = expand_patterns_to_domains(base)
        assert result.count("api.openai.com") == 1


class TestResolveDomain:
    def test_resolve_localhost(self):
        ips = resolve_domain("localhost")
        # localhost should resolve to 127.0.0.1 or ::1
        assert len(ips) > 0

    def test_resolve_nonexistent(self):
        ips = resolve_domain("this.domain.does.not.exist.example.invalid", timeout=1.0)
        assert ips == []


class TestBlocklistPatterns:
    def test_patterns_dict_not_empty(self):
        assert len(BLOCKLIST_PATTERNS) > 0

    def test_all_patterns_are_valid_regex(self):
        import re
        for name, pattern in BLOCKLIST_PATTERNS.items():
            try:
                re.compile(pattern)
            except re.error:
                raise AssertionError(f"Invalid regex pattern for {name}: {pattern}")
