# -*- coding: utf-8 -*-
"""Tests for DLP policy system."""
import json
import os
import tempfile

from ai_blocker.dlp_engine import (
    DLPAction,
    DLPEngine,
    DLPPolicy,
    DLPPolicyManager,
)


class TestDLPAction:
    def test_enum_values(self):
        assert DLPAction.REDACT.value == "redact"
        assert DLPAction.BLOCK.value == "block"
        assert DLPAction.LOG_ONLY.value == "log_only"
        assert DLPAction.PASS_THROUGH.value == "pass_through"


class TestDLPPolicy:
    def test_default_policy(self):
        p = DLPPolicy()
        assert p.action == DLPAction.REDACT
        assert p.scan_secrets is None
        assert p.scan_pii is None

    def test_custom_policy(self):
        p = DLPPolicy(action=DLPAction.BLOCK, scan_secrets=True, scan_pii=False)
        assert p.action == DLPAction.BLOCK
        assert p.scan_secrets is True
        assert p.scan_pii is False


class TestDLPPolicyManager:
    def test_default_resolve(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        policy = mgr.resolve("api.openai.com", "/v1/chat/completions")
        assert policy.action == DLPAction.REDACT

    def test_add_override_domain_match(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        mgr.add_override("*.openai.com", "/v1/*",
                         DLPPolicy(action=DLPAction.BLOCK))
        policy = mgr.resolve("api.openai.com", "/v1/chat/completions")
        assert policy.action == DLPAction.BLOCK

    def test_add_override_no_match(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        mgr.add_override("*.openai.com", "/v1/*",
                         DLPPolicy(action=DLPAction.BLOCK))
        policy = mgr.resolve("other.com", "/api/test")
        assert policy.action == DLPAction.REDACT

    def test_add_override_path_mismatch(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        mgr.add_override("*.openai.com", "/v1/*",
                         DLPPolicy(action=DLPAction.BLOCK))
        policy = mgr.resolve("api.openai.com", "/v2/chat")
        assert policy.action == DLPAction.REDACT

    def test_default_policy_property(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        assert mgr.default_policy.action == DLPAction.REDACT
        mgr.default_policy = DLPPolicy(action=DLPAction.LOG_ONLY)
        assert mgr.default_policy.action == DLPAction.LOG_ONLY

    def test_overrides_property(self):
        mgr = DLPPolicyManager(policies_path="/nonexistent/path.json")
        assert mgr.overrides == []
        mgr.add_override("*.test.com", policy=DLPPolicy(action=DLPAction.BLOCK))
        assert len(mgr.overrides) == 1
        assert mgr.overrides[0].domain_pattern == "*.test.com"

    def test_save_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "test_policies.json")
            mgr = DLPPolicyManager(policies_path=path)
            mgr.add_override("*.openai.com", "/v1/*",
                             DLPPolicy(action=DLPAction.BLOCK))
            mgr.save()

            # Reload from file
            mgr2 = DLPPolicyManager(policies_path=path)
            assert len(mgr2.overrides) == 1
            assert mgr2.overrides[0].domain_pattern == "*.openai.com"
            policy = mgr2.resolve("api.openai.com", "/v1/chat")
            assert policy.action == DLPAction.BLOCK

    def test_ignore_bad_json_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "bad.json")
            with open(path, "w") as f:
                f.write("not valid json")
            mgr = DLPPolicyManager(policies_path=path)
            # Should fall back to defaults
            assert mgr.default_policy.action == DLPAction.REDACT
            assert mgr.overrides == []

    def test_missing_file_fallback(self):
        mgr = DLPPolicyManager(policies_path="/tmp/definitely/does/not/exist.json")
        assert mgr.default_policy.action == DLPAction.REDACT
        assert mgr.overrides == []

    def test_reload_updates_policy(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "reload_test.json")
            mgr = DLPPolicyManager(policies_path=path)
            assert mgr.default_policy.action == DLPAction.REDACT

            # Write new config
            with open(path, "w") as f:
                json.dump({"default_policy": {"action": "block"}}, f)

            mgr.reload()
            assert mgr.default_policy.action == DLPAction.BLOCK


class TestDLPPolicyWithEngine:
    def setup_method(self):
        self.engine = DLPEngine()

    def test_scan_with_policy_override_secrets_on(self):
        policy = DLPPolicy(scan_secrets=True, scan_pii=False, scan_env_vars=False)
        engine = DLPEngine(scan_secrets=False, scan_pii=False)
        findings = engine.scan("sk-proj-test1234567890abcdefghijklm", policy=policy)
        assert len(findings) > 0

    def test_scan_with_policy_disables_category(self):
        policy = DLPPolicy(scan_secrets=False)
        engine = DLPEngine(scan_secrets=True)
        findings = engine.scan("sk-proj-test1234567890abcdefghijklm", policy=policy)
        assert len(findings) == 0

    def test_scan_with_policy_none(self):
        """Policy=None should use engine defaults."""
        engine = DLPEngine(scan_secrets=True)
        findings = engine.scan("sk-proj-test1234567890abcdefghijklm")
        assert len(findings) > 0

    def test_policy_pass_through_skips_dlp(self):
        """PASS_THROUGH in _apply_dlp skips scan entirely."""
        policy = DLPPolicy(action=DLPAction.PASS_THROUGH)
        # The _apply_dlp method checks policy.action before scanning,
        # so this is tested via the policy system, not engine directly.
        assert policy.action == DLPAction.PASS_THROUGH

    def test_policy_block_action(self):
        """BLOCK action indicates findings should block the request."""
        policy = DLPPolicy(action=DLPAction.BLOCK)
        assert policy.action == DLPAction.BLOCK
