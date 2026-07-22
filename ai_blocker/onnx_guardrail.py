# -*- coding: utf-8 -*-
"""On-Device Semantic Guardrails with ONNX Runtime.

Provides local prompt classification using ONNX-exported models
with automatic fallback to heuristic guardrails when ONNX is
unavailable or exceeds latency budget.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import time
from dataclasses import dataclass
from typing import Any

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
if HAS_NUMPY:
    pass

try:
    import onnxruntime as ort  # type: ignore[import-not-found]
    HAS_ONNX = True
except ImportError:
    HAS_ONNX = False

MODELS_DIR = os.path.expanduser(os.path.join("~", ".cache", "devgate", "models"))


@dataclass
class GuardrailResult:
    allowed: bool
    category: str = "safe"
    confidence: float = 1.0
    model: str = ""
    latency_ms: float = 0.0
    fallback: bool = False


class ONNXGuardrailModel:
    """Manage ONNX model download, caching, and integrity verification."""

    def __init__(self, model_name: str = "phi-3-mini-guard", models_dir: str = MODELS_DIR):
        self.model_name = model_name
        self.models_dir = models_dir
        self._model_path = os.path.join(models_dir, f"{model_name}.onnx")
        self._tokenizer_path = os.path.join(models_dir, f"{model_name}.tokenizer.json")
        os.makedirs(models_dir, exist_ok=True)

    @property
    def is_downloaded(self) -> bool:
        return os.path.exists(self._model_path) and os.path.exists(self._tokenizer_path)

    @property
    def model_path(self) -> str:
        return self._model_path

    def verify_integrity(self, expected_sha256: str = "") -> bool:
        if not os.path.exists(self._model_path):
            return False
        if not expected_sha256:
            return True
        h = hashlib.sha256()
        with open(self._model_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest() == expected_sha256


class ONNXGuardrailRuntime:
    """ONNX classification runtime with latency tracking.

    Operates only when onnxruntime and numpy are available and
    a model has been downloaded. Falls back gracefully on any failure.
    """

    def __init__(self, model: ONNXGuardrailModel, timeout_ms: int = 15):
        self.model = model
        self.timeout_ms = timeout_ms
        self._session: Any = None
        self._input_name: str = "input"
        self._loaded = False

    def load(self) -> bool:
        if not HAS_ONNX or not HAS_NUMPY or not self.model.is_downloaded:
            return False
        try:
            self._session = ort.InferenceSession(
                self.model.model_path,
                providers=["CPUExecutionProvider"],
            )
            self._input_name = self._session.get_inputs()[0].name
            self._loaded = True
            return True
        except Exception:
            self._loaded = False
            return False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def classify(self, text: str) -> GuardrailResult | None:
        if not self._loaded:
            return None
        start = time.monotonic()
        try:
            tokens = self._tokenize(text)
            result = self._session.run(None, {self._input_name: tokens})
            elapsed = (time.monotonic() - start) * 1000
            if elapsed > self.timeout_ms:
                return None  # timeout, fallback
            label, score = self._postprocess(result)
            return GuardrailResult(
                allowed=(label == "safe"),
                category=label,
                confidence=float(score),
                model=self.model.model_name,
                latency_ms=elapsed,
                fallback=False,
            )
        except Exception:
            return None

    def _tokenize(self, text: str) -> Any:
        import numpy as np  # type: ignore[import-not-found]
        simple_ids = [min(ord(c), 50255) for c in text[:512]]
        arr = np.array([simple_ids], dtype=np.int64)
        return arr

    def _postprocess(self, result: list[Any]) -> tuple[str, float]:
        import numpy as np  # type: ignore[import-not-found]
        logits = result[0]
        if isinstance(logits, (list, tuple)):
            logits = np.array(logits)
        idx = int(logits.argmax())
        labels = ["safe", "unsafe", "jailbreak", "pii"]
        label = labels[idx] if idx < len(labels) else "safe"
        scores = np.exp(logits - logits.max())
        scores = scores / scores.sum()
        return label, float(scores[idx])


class GuardrailFallbackChain:
    """Chain of guardrail classifiers with automatic fallback.

    ONNX -> Heuristic -> Allow (if ONNX is unavailable or times out)
    """

    def __init__(self, onnx_runtime: ONNXGuardrailRuntime | None = None):
        self.onnx = onnx_runtime
        self._stats: dict[str, Any] = {
            "total": 0, "onnx": 0, "heuristic": 0, "timeout": 0, "bypass": 0,
        }

    def classify(self, text: str, heuristic_fn=None) -> GuardrailResult:
        start = time.monotonic()
        self._stats["total"] += 1

        # Level 1: ONNX (fast path)
        if self.onnx and self.onnx.is_loaded:
            result = self.onnx.classify(text)
            if result is not None:
                self._stats["onnx"] += 1
                return result
            self._stats["timeout"] += 1

        # Level 2: Heuristic fallback
        if heuristic_fn:
            result = heuristic_fn(text)
            if result is not None:
                self._stats["heuristic"] += 1
                return result
            self._stats["bypass"] += 1

        # Level 3: Allow (no classification available)
        elapsed = (time.monotonic() - start) * 1000
        return GuardrailResult(
            allowed=True, category="safe",
            confidence=0.5, latency_ms=elapsed, fallback=True,
        )

    @property
    def stats(self) -> dict[str, Any]:
        return {**self._stats}

    def reset_stats(self) -> None:
        for k in self._stats:
            self._stats[k] = 0
