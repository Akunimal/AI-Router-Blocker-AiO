# -*- coding: utf-8 -*-
"""
Differential privacy context anonymizer for source code.

Uses Python's ``ast`` module to parse code and replace proprietary
variable names, function names, and class names with generic
identifiers while preserving syntactic structure.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass


@dataclass
class AnonymizationResult:
    """Result of a code anonymization pass."""
    anonymized_code: str
    mapping: dict[str, str]
    names_replaced: int


class CodeAnonymizer:
    """Replaces identifiers in Python code with generic names.

    The anonymizer uses AST parsing for Python code and falls back to
    regex-based replacement for non-Python or unparseable text.
    """

    # Identifiers to never replace (Python builtins, common stdlib names)
    _SAFE_NAMES: frozenset[str] = frozenset({
        "self", "cls", "None", "True", "False", "print", "len", "range",
        "str", "int", "float", "bool", "list", "dict", "set", "tuple",
        "type", "object", "super", "isinstance", "issubclass", "hasattr",
        "getattr", "setattr", "delattr", "property", "staticmethod",
        "classmethod", "open", "close", "read", "write", "append",
        "extend", "pop", "get", "keys", "values", "items", "update",
        "format", "join", "split", "strip", "replace", "find", "index",
        "count", "sort", "sorted", "filter", "map", "zip", "enumerate",
        "min", "max", "sum", "abs", "round", "all", "any", "iter", "next",
        "input", "exit", "quit", "Exception", "ValueError", "TypeError",
        "KeyError", "IndexError", "AttributeError", "ImportError",
        "RuntimeError", "OSError", "IOError", "StopIteration",
        "return", "yield", "import", "from", "as", "if", "elif", "else",
        "for", "while", "try", "except", "finally", "with", "raise",
        "pass", "break", "continue", "def", "class", "lambda", "and",
        "or", "not", "in", "is", "del", "global", "nonlocal", "assert",
        "__init__", "__str__", "__repr__", "__len__", "__getitem__",
        "__setitem__", "__delitem__", "__contains__", "__iter__",
        "__next__", "__call__", "__enter__", "__exit__", "__name__",
        "__main__", "__file__", "__doc__", "__all__",
    })

    def __init__(self, prefix: str = "id"):
        self.prefix = prefix

    def anonymize_python(self, source: str) -> AnonymizationResult:
        """Anonymize Python source code using AST-based renaming."""
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return self._anonymize_fallback(source)

        # Collect all user-defined names
        names_to_replace: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name not in self._SAFE_NAMES:
                    names_to_replace.add(node.name)
            elif isinstance(node, ast.ClassDef):
                if node.name not in self._SAFE_NAMES:
                    names_to_replace.add(node.name)
            elif isinstance(node, ast.Name):
                if node.id not in self._SAFE_NAMES and not node.id.startswith("_"):
                    names_to_replace.add(node.id)
            elif isinstance(node, ast.arg):
                if node.arg not in self._SAFE_NAMES:
                    names_to_replace.add(node.arg)

        # Build deterministic mapping
        sorted_names = sorted(names_to_replace)
        mapping: dict[str, str] = {}
        for i, name in enumerate(sorted_names):
            mapping[name] = f"{self.prefix}_{i}"

        # Apply replacements via regex (word-boundary aware)
        anonymized = source
        for original, replacement in sorted(mapping.items(), key=lambda x: -len(x[0])):
            anonymized = re.sub(
                rf'\b{re.escape(original)}\b',
                replacement,
                anonymized,
            )

        return AnonymizationResult(
            anonymized_code=anonymized,
            mapping=mapping,
            names_replaced=len(mapping),
        )

    def _anonymize_fallback(self, text: str) -> AnonymizationResult:
        """Regex-based fallback for non-Python or unparseable code."""
        # Find camelCase and snake_case identifiers that look like user names
        pattern = r'\b([a-z][a-zA-Z0-9_]{3,})\b'
        found = set(re.findall(pattern, text))
        found -= self._SAFE_NAMES

        sorted_names = sorted(found)
        mapping = {name: f"{self.prefix}_{i}" for i, name in enumerate(sorted_names)}

        anonymized = text
        for original, replacement in sorted(mapping.items(), key=lambda x: -len(x[0])):
            anonymized = re.sub(
                rf'\b{re.escape(original)}\b',
                replacement,
                anonymized,
            )

        return AnonymizationResult(
            anonymized_code=anonymized,
            mapping=mapping,
            names_replaced=len(mapping),
        )

    def anonymize(self, text: str, language: str = "python") -> AnonymizationResult:
        """Anonymize code in the specified language.

        Currently supports ``"python"`` (AST-based) with a regex fallback
        for other languages.
        """
        if language.lower() == "python":
            return self.anonymize_python(text)
        return self._anonymize_fallback(text)
