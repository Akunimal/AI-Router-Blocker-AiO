# -*- coding: utf-8 -*-
"""Tests for the context anonymizer module."""

from ai_blocker.context_anonymizer import CodeAnonymizer


class TestCodeAnonymizer:
    def setup_method(self):
        self.anon = CodeAnonymizer(prefix="id")

    def test_anonymize_function_name(self):
        source = "def calculate_revenue(amount):\n    return amount * 1.1\n"
        result = self.anon.anonymize_python(source)
        assert "calculate_revenue" not in result.anonymized_code
        assert result.names_replaced > 0

    def test_anonymize_class_name(self):
        source = "class CustomerManager:\n    pass\n"
        result = self.anon.anonymize_python(source)
        assert "CustomerManager" not in result.anonymized_code

    def test_preserves_builtins(self):
        source = "x = len([1, 2, 3])\nprint(x)\n"
        result = self.anon.anonymize_python(source)
        assert "len" in result.anonymized_code
        assert "print" in result.anonymized_code

    def test_preserves_self(self):
        source = "class Foo:\n    def bar(self):\n        self.x = 1\n"
        result = self.anon.anonymize_python(source)
        assert "self" in result.anonymized_code

    def test_mapping_is_deterministic(self):
        source = "def my_func(param):\n    return param\n"
        r1 = self.anon.anonymize_python(source)
        r2 = self.anon.anonymize_python(source)
        assert r1.mapping == r2.mapping

    def test_mapping_returned(self):
        source = "def secret_algo(data):\n    return data\n"
        result = self.anon.anonymize_python(source)
        assert "secret_algo" in result.mapping
        assert result.mapping["secret_algo"].startswith("id_")

    def test_fallback_for_invalid_python(self):
        source = "this is not valid python {{{"
        result = self.anon.anonymize_python(source)
        # Should not crash
        assert isinstance(result.anonymized_code, str)

    def test_anonymize_generic_language(self):
        source = "function calculateTotal(items) { return items.reduce((a, b) => a + b); }"
        result = self.anon.anonymize(source, language="javascript")
        assert isinstance(result.anonymized_code, str)

    def test_empty_source(self):
        result = self.anon.anonymize_python("")
        assert result.anonymized_code == ""
        assert result.names_replaced == 0
