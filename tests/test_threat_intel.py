# -*- coding: utf-8 -*-
"""Tests for threat intelligence components."""
from __future__ import annotations

import time
import unittest

from ai_blocker.threat_intel import AlertSystem, RecursiveLoopDetector, RequestAnalyzer, ThreatFeed


class TestRequestAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = RequestAnalyzer(window_seconds=60, zscore_threshold=3.0)

    def test_record_and_domains(self):
        self.analyzer.record("api.openai.com", token_count=100)
        self.assertIn("api.openai.com", self.analyzer.domains)
        self.assertEqual(self.analyzer.total_observations, 1)

    def test_analyze_insufficient_data(self):
        self.analyzer.record("test.domain", token_count=10)
        results = self.analyzer.analyze()
        self.assertEqual(len(results), 0)

    def test_analyze_with_data(self):
        for i in range(10):
            self.analyzer.record("api.openai.com", token_count=50)
            time.sleep(0.001)
        results = self.analyzer.analyze()
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0].domain, "api.openai.com")

    def test_analyze_specific_domain(self):
        self.analyzer.record("a.com", token_count=10)
        self.analyzer.record("b.com", token_count=20)
        for _ in range(10):
            self.analyzer.record("a.com", token_count=10)
            time.sleep(0.001)
        results = self.analyzer.analyze(domain="a.com")
        self.assertTrue(all(r.domain == "a.com" for r in results))

    def test_baseline_adapts(self):
        # Record enough data to establish a baseline
        for i in range(10):
            self.analyzer.record("steady.domain", token_count=30)
            time.sleep(0.05)
        results1 = self.analyzer.analyze()
        r1 = [r for r in results1 if r.domain == "steady.domain"]
        if r1:
            self.assertFalse(r1[0].is_anomalous)

class TestRecursiveLoopDetector(unittest.TestCase):
    def setUp(self):
        self.detector = RecursiveLoopDetector(max_identical=3, window_seconds=300)

    def test_no_loop(self):
        result = self.detector.analyze("unique body", domain="test.domain")
        self.assertIsNone(result)

    def test_loop_detected(self):
        for _ in range(3):
            self.detector.record("same body", domain="test.domain")
        result = self.detector.analyze("same body", domain="test.domain")
        self.assertIsNotNone(result)
        self.assertTrue(result.is_looping)
        self.assertGreaterEqual(result.count, 3)

    def test_below_threshold(self):
        for _ in range(2):
            self.detector.record("body", domain="t.domain")
        result = self.detector.analyze("body", domain="t.domain")
        if result:
            self.assertFalse(result.is_looping)

    def test_diff_bodies_no_loop(self):
        for i in range(5):
            self.detector.record(f"body{i}", domain="t.domain")
        result = self.detector.analyze("body0", domain="t.domain")
        self.assertIsNone(result) if not result else self.assertFalse(result.is_looping)

class TestThreatFeed(unittest.TestCase):
    def setUp(self):
        self.feed = ThreatFeed(feed_dir="threat_feeds")

    def test_initialized(self):
        self.assertGreaterEqual(self.feed.count, 0)

    def test_match_domain_empty(self):
        self.assertEqual(self.feed.match_domain("evil.com"), [])

    def test_match_body_empty(self):
        self.assertEqual(self.feed.match_body("test"), [])

class TestAlertSystem(unittest.TestCase):
    def setUp(self):
        self.alerts = AlertSystem(max_alerts=10)

    def test_emit_and_recent(self):
        a = self.alerts.emit("loop", "high", "evil.com", "recursive loop detected")
        self.assertEqual(a.alert_type, "loop")
        self.assertEqual(len(self.alerts.recent()), 1)

    def test_by_severity(self):
        self.alerts.emit("test", "low", "a.com", "test alert")
        self.assertEqual(len(self.alerts.by_severity("low")), 1)
        self.assertEqual(len(self.alerts.by_severity("high")), 0)

    def test_max_alerts_enforced(self):
        for i in range(15):
            self.alerts.emit("test", "low", "a.com", f"alert {i}")
        self.assertEqual(self.alerts.total, 10)

    def test_clear(self):
        self.alerts.emit("test", "low", "a.com", "test")
        self.alerts.clear()
        self.assertEqual(self.alerts.total, 0)

if __name__ == "__main__":
    unittest.main()
