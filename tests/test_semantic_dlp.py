# -*- coding: utf-8 -*-
"""Tests for the cloud-assisted semantic DLP client."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from ai_blocker.semantic_dlp import SemanticDLPCache, SemanticDLPClient, SemanticResult


class TestSemanticResult(unittest.TestCase):
    """SemanticResult dataclass tests."""

    def test_defaults(self):
        r = SemanticResult(category="safe", risk_score=0.0, explanation="ok")
        self.assertEqual(r.category, "safe")
        self.assertEqual(r.risk_score, 0.0)
        self.assertEqual(r.explanation, "ok")
        self.assertEqual(r.model, "")

    def test_full_constructor(self):
        r = SemanticResult(
            category="proprietary_code",
            risk_score=0.85,
            explanation="contains proprietary algo",
            model="gpt-4o",
        )
        self.assertEqual(r.model, "gpt-4o")


class TestSemanticDLPClient(unittest.TestCase):
    """SemanticDLPClient tests."""

    def setUp(self):
        self.client = SemanticDLPClient(api_key="sk-test123")

    def test_is_available_with_key(self):
        self.assertTrue(self.client.is_available)

    def test_is_available_without_key(self):
        c = SemanticDLPClient(api_key="")
        self.assertFalse(c.is_available)

    def test_is_available_from_env(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-env-key"}):
            c = SemanticDLPClient()
            self.assertTrue(c.is_available)

    def test_classify_raises_without_key(self):
        c = SemanticDLPClient(api_key="")
        with self.assertRaises(RuntimeError):
            c.classify("hello")

    @patch("ai_blocker.semantic_dlp.urllib_request.urlopen")
    def test_classify_success(self, mock_urlopen):
        mock_resp = MagicMock()
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "category": "safe",
                            "risk_score": 0.02,
                            "explanation": "No sensitive content detected.",
                        })
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.client.classify("Hello, how are you?")
        self.assertEqual(result.category, "safe")
        self.assertAlmostEqual(result.risk_score, 0.02)
        self.assertEqual(result.model, "gpt-4o-mini")

    @patch("ai_blocker.semantic_dlp.urllib_request.urlopen")
    def test_classify_markdown_fence(self, mock_urlopen):
        """Handle responses wrapped in markdown code fences."""
        mock_resp = MagicMock()
        api_response = {
            "choices": [
                {
                    "message": {
                        "content": """`json
{"category": "pii", "risk_score": 0.75, "explanation": "Contains email address"}
`"""
                    }
                }
            ]
        }
        mock_resp.read.return_value = json.dumps(api_response).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = self.client.classify("my email is test@example.com")
        self.assertEqual(result.category, "pii")
        self.assertAlmostEqual(result.risk_score, 0.75)

    @patch("ai_blocker.semantic_dlp.urllib_request.urlopen")
    def test_classify_retry_on_failure(self, mock_urlopen):
        """Retry on network errors."""
        from urllib.error import URLError

        api_response = {
            "choices": [
                {"message": {"content": json.dumps({"category": "safe", "risk_score": 0.0, "explanation": "ok"})}}
            ]
        }
        mock_success_resp = MagicMock()
        mock_success_resp.read.return_value = json.dumps(api_response).encode("utf-8")
        mock_success_cm = MagicMock()
        mock_success_cm.__enter__.return_value = mock_success_resp

        mock_urlopen.side_effect = [
            URLError("refused"),
            URLError("timeout"),
            mock_success_cm,
        ]

        result = self.client.classify("test")
        self.assertEqual(result.category, "safe")
        self.assertEqual(mock_urlopen.call_count, 3)

    @patch("ai_blocker.semantic_dlp.urllib_request.urlopen")
    def test_classify_raises_after_retries(self, mock_urlopen):
        """Raise RuntimeError after exhausting retries."""
        from urllib.error import URLError

        mock_urlopen.side_effect = URLError("Always down")

        with self.assertRaises(RuntimeError):
            self.client.classify("test")

    def test_constructor_defaults(self):
        c = SemanticDLPClient()
        self.assertEqual(c.model, "gpt-4o-mini")
        self.assertEqual(c.timeout, 15)
        self.assertEqual(c.max_retries, 2)




class TestSemanticDLPCache(unittest.TestCase):
    """SemanticDLPCache tests."""

    def setUp(self):
        self.cache = SemanticDLPCache(maxsize=3, ttl_seconds=60)
        self.result = SemanticResult(category="safe", risk_score=0.0, explanation="ok")

    def test_get_miss(self):
        self.assertIsNone(self.cache.get("unknown"))

    def test_put_and_get(self):
        self.cache.put("hello", self.result)
        cached = self.cache.get("hello")
        self.assertIsNotNone(cached)
        self.assertEqual(cached.category, "safe")

    def test_invalidate(self):
        self.cache.put("hello", self.result)
        self.cache.invalidate("hello")
        self.assertIsNone(self.cache.get("hello"))

    def test_clear(self):
        self.cache.put("a", self.result)
        self.cache.put("b", self.result)
        self.cache.clear()
        self.assertEqual(self.cache.size, 0)

    def test_lru_eviction(self):
        for i in range(5):
            self.cache.put(f"key-{i}", self.result)
        # Cache maxsize is 3, so only the last 3 should remain
        self.assertEqual(self.cache.size, 3)
        self.assertIsNone(self.cache.get("key-0"))
        self.assertIsNone(self.cache.get("key-1"))
        self.assertIsNotNone(self.cache.get("key-2"))
        self.assertIsNotNone(self.cache.get("key-3"))

    def test_lru_touch_recently_used(self):
        # Fill cache, then access key-0 to make it recently used
        for i in range(3):
            self.cache.put(f"key-{i}", self.result)
        self.cache.get("key-0")  # touch
        self.cache.put("key-3", self.result)  # should evict key-1 (oldest untouched)
        self.assertIsNotNone(self.cache.get("key-0"))
        self.assertIsNone(self.cache.get("key-1"))
        self.assertIsNotNone(self.cache.get("key-2"))

    def test_ttl_expiry(self):
        import time as _time_module
        cache = SemanticDLPCache(maxsize=10, ttl_seconds=0)  # 0 = immediate expiry
        cache.put("hello", self.result)
        _time_module.sleep(0.01)
        self.assertIsNone(cache.get("hello"))

    def test_ttl_property(self):
        self.assertEqual(self.cache.ttl, 60)

if __name__ == "__main__":
    unittest.main()
