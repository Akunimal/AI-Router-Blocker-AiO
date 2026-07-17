# -*- coding: utf-8 -*-
"""Tests for ONNX-based semantic guardrails."""
from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ai_blocker.onnx_guardrail import (
    ONNXGuardrailModel,
    ONNXGuardrailRuntime,
    GuardrailFallbackChain,
    GuardrailResult,
    HAS_ONNX,
    HAS_NUMPY,
)


class TestONNXGuardrailModel(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.model = ONNXGuardrailModel(models_dir=self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_not_downloaded_initially(self):
        self.assertFalse(self.model.is_downloaded)

    def test_verify_integrity_no_file(self):
        self.assertFalse(self.model.verify_integrity())

    def test_verify_integrity_with_file(self):
        dummy = os.path.join(self.tmpdir, self.model.model_name + ".onnx")
        with open(dummy, "wb") as f:
            f.write(b"dummy_model_data")
        tok = os.path.join(self.tmpdir, self.model.model_name + ".tokenizer.json")
        with open(tok, "w") as f:
            f.write("{}")
        self.assertTrue(self.model.is_downloaded)

    def test_model_path_property(self):
        self.assertTrue(self.model.model_path.endswith(".onnx"))


class TestGuardrailFallbackChain(unittest.TestCase):
    def test_allow_when_no_onnx(self):
        chain = GuardrailFallbackChain()
        result = chain.classify("hello world")
        self.assertTrue(result.allowed)
        self.assertTrue(result.fallback)
        self.assertEqual(result.category, "safe")

    def test_heuristic_fallback(self):
        chain = GuardrailFallbackChain()
        def heuristic(text):
            if "bad" in text.lower():
                return GuardrailResult(allowed=False, category="unsafe", confidence=0.9, fallback=True)
            return None
        result = chain.classify("this is bad")
        self.assertFalse(result.allowed)
        self.assertEqual(result.category, "unsafe")

    def test_heuristic_allows_safe(self):
        chain = GuardrailFallbackChain()
        def heuristic(text):
            return None
        result = chain.classify("safe text")
        self.assertTrue(result.allowed)
        self.assertTrue(result.fallback)

    def test_stats_tracking(self):
        chain = GuardrailFallbackChain()
        chain.classify("test")
        self.assertEqual(chain.stats["total"], 1)
        self.assertGreaterEqual(chain.stats["bypass"], 1)

    def test_reset_stats(self):
        chain = GuardrailFallbackChain()
        chain.classify("test")
        chain.reset_stats()
        self.assertEqual(chain.stats["total"], 0)

    def test_multiple_classifications(self):
        chain = GuardrailFallbackChain()
        chain.classify("a")
        chain.classify("b")
        chain.classify("c")
        self.assertEqual(chain.stats["total"], 3)


if __name__ == "__main__":
    unittest.main()
