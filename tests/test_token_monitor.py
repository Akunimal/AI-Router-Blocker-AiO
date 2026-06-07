# -*- coding: utf-8 -*-
"""Tests for the token monitor module."""


from ai_blocker.token_monitor import TokenMonitor


class TestTokenMonitor:
    def test_estimate_tokens(self):
        # ~4 chars per token
        assert TokenMonitor.estimate_tokens("a" * 100) == 25
        assert TokenMonitor.estimate_tokens("a" * 3) == 1  # minimum 1

    def test_estimate_tokens_bytes(self):
        assert TokenMonitor.estimate_tokens(b"hello world") >= 1

    def test_record_and_summary(self):
        monitor = TokenMonitor()
        monitor.record(100, 200, domain="openai.com", path="/v1/chat")
        monitor.record(50, 75, domain="openai.com", path="/v1/chat")

        summary = monitor.get_hourly_summary()
        assert summary["tokens_in"] == 150
        assert summary["tokens_out"] == 275
        assert summary["total_tokens"] == 425
        assert summary["request_count"] == 2

    def test_per_domain_breakdown(self):
        monitor = TokenMonitor()
        monitor.record(100, 200, domain="openai.com")
        monitor.record(50, 75, domain="anthropic.com")

        breakdown = monitor.get_per_domain_breakdown()
        assert "openai.com" in breakdown
        assert "anthropic.com" in breakdown
        assert breakdown["openai.com"]["tokens_in"] == 100
        assert breakdown["anthropic.com"]["requests"] == 1

    def test_is_over_limit_tokens(self):
        monitor = TokenMonitor(max_tokens_per_hour=100)
        monitor.record(60, 50)  # total = 110 > 100
        assert monitor.is_over_limit()

    def test_is_under_limit(self):
        monitor = TokenMonitor(max_tokens_per_hour=1000)
        monitor.record(10, 20)
        assert not monitor.is_over_limit()

    def test_no_limit_never_over(self):
        monitor = TokenMonitor(max_tokens_per_hour=0)
        monitor.record(999999, 999999)
        assert not monitor.is_over_limit()

    def test_is_over_limit_requests(self):
        monitor = TokenMonitor(max_requests_per_minute=2)
        monitor.record(1, 1)
        monitor.record(1, 1)
        assert monitor.is_over_limit()

    def test_reset_clears_data(self):
        monitor = TokenMonitor()
        monitor.record(100, 200)
        monitor.reset()
        summary = monitor.get_hourly_summary()
        assert summary["request_count"] == 0

    def test_cap_usage_percentage(self):
        monitor = TokenMonitor(max_tokens_per_hour=1000)
        monitor.record(100, 100)  # total = 200 / 1000 = 20%
        summary = monitor.get_hourly_summary()
        assert summary["cap_usage_pct"] == 20.0
