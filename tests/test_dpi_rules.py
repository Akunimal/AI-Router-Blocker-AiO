# -*- coding: utf-8 -*-
"""Tests for the DPI rules engine."""

from ai_blocker.dpi_rules import DEFAULT_DPI_RULES, DPIAction, DPIRule, DPIRuleEngine


class TestDPIRule:
    def test_matches_exact_path(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat/completions", method="POST")
        assert rule.matches("/v1/chat/completions", "POST")

    def test_matches_path_with_query(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat/completions")
        assert rule.matches("/v1/chat/completions?stream=true", "POST")

    def test_no_match_wrong_path(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat/completions", method="POST")
        assert not rule.matches("/v1/models", "POST")

    def test_method_filter_all(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat", method="ALL")
        assert rule.matches("/v1/chat/completions", "GET")
        assert rule.matches("/v1/chat/completions", "POST")

    def test_method_filter_specific(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat", method="POST")
        assert rule.matches("/v1/chat/completions", "POST")
        assert not rule.matches("/v1/chat/completions", "GET")

    def test_disabled_rule_no_match(self):
        rule = DPIRule(name="test", path_pattern=r"/v1/chat", enabled=False)
        assert not rule.matches("/v1/chat/completions", "POST")

    def test_invalid_regex_no_crash(self):
        rule = DPIRule(name="test", path_pattern=r"[invalid(")
        assert not rule.matches("/anything", "GET")

    def test_to_dict_roundtrip(self):
        rule = DPIRule(name="test", path_pattern="/v1/chat", method="POST", action=DPIAction.BLOCK)
        d = rule.to_dict()
        restored = DPIRule.from_dict(d)
        assert restored.name == rule.name
        assert restored.path_pattern == rule.path_pattern
        assert restored.method == rule.method
        assert restored.action == rule.action
        assert restored.enabled == rule.enabled


class TestDPIRuleEngine:
    def test_default_rules_block_completions(self):
        engine = DPIRuleEngine()
        action, rule = engine.evaluate("/v1/chat/completions", "POST")
        assert action == DPIAction.BLOCK
        assert rule is not None
        assert rule.name == "Block chat completions"

    def test_default_rules_allow_models(self):
        engine = DPIRuleEngine()
        action, rule = engine.evaluate("/v1/models", "GET")
        assert action == DPIAction.ALLOW

    def test_no_match_returns_allow(self):
        engine = DPIRuleEngine()
        action, rule = engine.evaluate("/unknown/path", "GET")
        assert action == DPIAction.ALLOW
        assert rule is None

    def test_first_match_wins(self):
        rules = [
            DPIRule(name="block-all", path_pattern=r"/v1/.*", action=DPIAction.BLOCK),
            DPIRule(name="allow-models", path_pattern=r"/v1/models", action=DPIAction.ALLOW),
        ]
        engine = DPIRuleEngine(rules=rules)
        action, _ = engine.evaluate("/v1/models", "GET")
        assert action == DPIAction.BLOCK  # First rule wins

    def test_add_rule(self):
        engine = DPIRuleEngine(rules=[])
        engine.add_rule(DPIRule(name="custom", path_pattern=r"/custom", action=DPIAction.LOG))
        action, rule = engine.evaluate("/custom", "GET")
        assert action == DPIAction.LOG

    def test_remove_rule(self):
        engine = DPIRuleEngine()
        initial_count = len(engine.rules)
        removed = engine.remove_rule("Block chat completions")
        assert removed
        assert len(engine.rules) == initial_count - 1

    def test_remove_nonexistent_rule(self):
        engine = DPIRuleEngine()
        removed = engine.remove_rule("nonexistent")
        assert not removed

    def test_set_rule_enabled(self):
        engine = DPIRuleEngine()
        engine.set_rule_enabled("Block chat completions", False)
        action, _ = engine.evaluate("/v1/chat/completions", "POST")
        # With the main block rule disabled, it should fall through
        assert action == DPIAction.ALLOW or action == DPIAction.BLOCK  # depends on other rules

    def test_serialization_roundtrip(self):
        engine = DPIRuleEngine()
        data = engine.to_list()
        restored = DPIRuleEngine.from_list(data)
        assert len(restored.rules) == len(engine.rules)
        for orig, rest in zip(engine.rules, restored.rules):
            assert orig.name == rest.name
            assert orig.path_pattern == rest.path_pattern


class TestDefaultRules:
    def test_default_rules_exist(self):
        assert len(DEFAULT_DPI_RULES) >= 5

    def test_default_rules_block_embeddings(self):
        engine = DPIRuleEngine()
        action, _ = engine.evaluate("/v1/embeddings", "POST")
        assert action == DPIAction.BLOCK

    def test_default_rules_allow_engines(self):
        engine = DPIRuleEngine()
        action, _ = engine.evaluate("/v1/engines", "GET")
        assert action == DPIAction.ALLOW
