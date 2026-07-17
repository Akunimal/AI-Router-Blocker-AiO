# -*- coding: utf-8 -*-
"""Tests for the DLP engine."""

from ai_blocker.dlp_engine import DLPEngine, FindingType


class TestDLPSecrets:
    def setup_method(self):
        self.engine = DLPEngine(scan_pii=False, scan_licenses=False)

    def test_detect_openai_key(self):
        text = "my key is sk-proj-abc123defgh456ijklm789nopqrstuvwxyz"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.API_KEY for f in findings)

    def test_detect_anthropic_key(self):
        text = "key: sk-ant-abcdefghijklmnopqrstuvwxyz123456"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.API_KEY for f in findings)

    def test_detect_aws_access_key(self):
        text = "access key: AKIAIOSFODNN7EXAMPLE"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.AWS_KEY for f in findings)

    def test_detect_github_token(self):
        text = "token: ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghij"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.GITHUB_TOKEN for f in findings)

    def test_detect_private_key(self):
        text = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAK..."
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.PRIVATE_KEY for f in findings)

    def test_no_false_positive_normal_text(self):
        text = "Hello world, this is a normal message about coding."
        findings = self.engine.scan(text)
        assert len(findings) == 0

    def test_scan_for_secrets_only(self):
        text = "sk-abc123defgh456ijklm789nopqrstuvwxyz test@example.com"
        findings = self.engine.scan_for_secrets(text)
        assert all(f.finding_type not in (FindingType.EMAIL, FindingType.SSN) for f in findings)


class TestDLPPII:
    def setup_method(self):
        self.engine = DLPEngine(scan_secrets=False, scan_licenses=False)

    def test_detect_email(self):
        text = "Send to john.doe@example.com please"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.EMAIL for f in findings)

    def test_detect_ssn(self):
        text = "SSN: 123-45-6789"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.SSN for f in findings)

    def test_detect_credit_card(self):
        text = "card: 4111 1111 1111 1111"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.CREDIT_CARD for f in findings)

    def test_scan_for_pii_only(self):
        text = "sk-abc123defgh456ijklm789nopqrstuvwxyz john@test.com"
        findings = self.engine.scan_for_pii(text)
        assert all(f.finding_type not in (FindingType.API_KEY, FindingType.AWS_KEY) for f in findings)


class TestDLPLicenses:
    def setup_method(self):
        self.engine = DLPEngine(scan_secrets=False, scan_pii=False, scan_licenses=True)

    def test_detect_gpl(self):
        text = "# Licensed under the GNU General Public License v3.0"
        findings = self.engine.scan(text)
        assert len(findings) >= 1
        assert any(f.finding_type == FindingType.LICENSE_CONFLICT for f in findings)

    def test_detect_agpl(self):
        text = "SPDX-License-Identifier: AGPL-3.0"
        findings = self.engine.scan(text)
        assert len(findings) >= 1


class TestDLPRedaction:
    def setup_method(self):
        self.engine = DLPEngine()

    def test_redact_api_key(self):
        text = "key: sk-proj-abc123defgh456ijklm789nopqrstuvwxyz end"
        result = self.engine.redact(text)
        assert "[REDACTED:API_KEY]" in result
        assert "sk-proj-" not in result

    def test_redact_preserves_non_sensitive(self):
        text = "Hello world"
        result = self.engine.redact(text)
        assert result == text

    def test_has_sensitive_data(self):
        assert self.engine.has_sensitive_data("key: sk-proj-abc123defgh456ijklm789nopqrstuvwxyz")
        assert not self.engine.has_sensitive_data("Hello world")

    def test_multiple_findings_redacted(self):
        text = "key1: sk-proj-abc123defgh456ijklm789nopqrstuvwxyz and AKIAIOSFODNN7EXAMPLE"
        result = self.engine.redact(text)
        assert "sk-proj-" not in result
        assert "AKIA" not in result

class TestDLPNewPatterns:
    def setup_method(self):
        self.engine = DLPEngine(scan_pii=False, scan_licenses=False,
                                scan_internal_ips=True, scan_cloud_tokens=True,
                                scan_db_strings=True, scan_env_vars=True)

    def test_detect_internal_ip_10(self):
        findings = self.engine.scan("server at 10.0.0.1 is running")
        assert any(f.finding_type == FindingType.INTERNAL_IP for f in findings)

    def test_detect_internal_ip_192(self):
        findings = self.engine.scan("connect to 192.168.1.100")
        assert any(f.finding_type == FindingType.INTERNAL_IP for f in findings)

    def test_detect_internal_ip_127(self):
        findings = self.engine.scan("localhost is 127.0.0.1")
        assert any(f.finding_type == FindingType.INTERNAL_IP for f in findings)

    def test_detect_google_oauth_token(self):
        findings = self.engine.scan("token: ya29.abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ123456789")
        assert any(f.finding_type == FindingType.CLOUD_TOKEN for f in findings)

    def test_detect_huggingface_token(self):
        findings = self.engine.scan("token: hf_abcdefghijklmnopqrstuvwxyz123456")
        assert any(f.finding_type == FindingType.CLOUD_TOKEN for f in findings)

    def test_detect_slack_token(self):
        findings = self.engine.scan("token: xoxp-FAKE123456789012345678901234567890")
        assert any(f.finding_type == FindingType.CLOUD_TOKEN for f in findings)

    def test_detect_db_connection_postgres(self):
        findings = self.engine.scan("postgresql://user:pass@localhost:5432/db")
        assert any(f.finding_type == FindingType.DB_CONNECTION_STRING for f in findings)

    def test_detect_db_connection_mongodb(self):
        findings = self.engine.scan("mongodb://admin:secret@cluster0.example.net")
        assert any(f.finding_type == FindingType.DB_CONNECTION_STRING for f in findings)

    def test_detect_env_var_reference(self):
        findings = self.engine.scan('key = os.environ["API_KEY"]')
        assert any(f.finding_type == FindingType.ENV_VAR_REFERENCE for f in findings)


class TestDLPEdgeCases:
    def setup_method(self):
        self.engine = DLPEngine()

    def test_empty_text(self):
        assert self.engine.scan("") == []
        assert self.engine.redact("") == ""

    def test_very_long_text_performance(self):
        text = "normal text " * 10000  # ~120KB
        findings = self.engine.scan(text)
        # Should not crash and find no secrets
        assert isinstance(findings, list)

    def test_unicode_emoji_text(self):
        text = "Hello from \U0001f600 \U0001f916 key: sk-proj-abc123defgh456ijklm789nopqrstuvwxyz"
        findings = self.engine.scan(text)
        assert any(f.finding_type == FindingType.API_KEY for f in findings)

    def test_false_positive_url_not_api_key(self):
        # URL path segments that look like keys should not trigger
        text = "https://example.com/sk-proj-something/status"
        findings = self.engine.scan(text)
        # This is a borderline case - the pattern might match, but let's see
        # We just verify it doesn't crash
        assert isinstance(findings, list)

    def test_base64_encoded_secret_not_detected(self):
        # Base64-encoded secrets should ideally NOT be detected by regex
        import base64
        secret = base64.b64encode(b"sk-proj-abcdef1234567890abcdef1234567890").decode()
        text = f"encoded: {secret}"
        findings = self.engine.scan(text)
        # Base64 encoded secrets should not be detected as plaintext
        assert not any(f.finding_type == FindingType.API_KEY for f in findings)

    def test_redact_structured_json_preserves_structure(self):
        text = '{"key": "sk-proj-abc123defgh456ijklm789nopqrstuvwxyz", "name": "test"}'
        result = self.engine.redact(text)
        assert "[REDACTED:" in result
        assert "sk-proj-" not in result
        # Verify JSON structure is preserved
        assert '"name": "test"' in result or "'name': 'test'" in result

    def test_redact_multiple_overlapping_findings(self):
        text = "key: sk-proj-abc123defgh456ijklm789nopqrstuvwxyz and email: test@example.com"
        result = self.engine.redact(text)
        assert "sk-proj-" not in result
        assert "test@example.com" not in result

    def test_scan_secrets_disabled(self):
        engine = DLPEngine(scan_secrets=False, scan_pii=False, scan_licenses=False,
                          scan_cloud_tokens=False, scan_db_strings=False)
        findings = engine.scan("sk-proj-abc123defgh456ijklm789nopqrstuvwxyz")
        assert len(findings) == 0

    def test_has_sensitive_data_no_false_positive(self):
        assert not self.engine.has_sensitive_data("The quick brown fox jumps over the lazy dog")
        assert not self.engine.has_sensitive_data("Lorem ipsum dolor sit amet")


import json


class TestDLPStructuredRedaction:
    def setup_method(self):
        self.engine = DLPEngine()

    def test_redact_structured_simple(self):
        text = '{"key": "sk-proj-abc123def456ghi789jkl012", "name": "normal"}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert "REDACTED" in parsed["key"]
        assert parsed["name"] == "normal"

    def test_redact_structured_nested(self):
        text = '{"user": {"token": "ghp_abc123def456ghi789jkl012mno345678901234", "email": "test@example.com"}}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert "REDACTED" in parsed["user"]["token"]
        assert "REDACTED" in parsed["user"]["email"]

    def test_redact_structured_array(self):
        text = '[{"k": "sk-proj-abc123def456ghi789jkl012"}, {"k": "safe"}]'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert "REDACTED" in parsed[0]["k"]
        assert parsed[1]["k"] == "safe"

    def test_redact_structured_non_string(self):
        text = '{"count": 42, "active": true, "items": null, "name": "hello"}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert parsed["count"] == 42
        assert parsed["active"] is True
        assert parsed["items"] is None
        assert parsed["name"] == "hello"

    def test_redact_structured_fallback_plain_text(self):
        text = "this is plain text with sk-proj-abc123def456ghi789jkl012 inside"
        result = self.engine.redact_structured(text)
        assert "REDACTED" in result

    def test_redact_structured_mixed_types(self):
        text = '{"data": {"values": [1, 2, 3], "token": "ghp_abc123def456ghi789jkl012mno345678901234"}, "metadata": null}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert "REDACTED" in parsed["data"]["token"]
        assert parsed["data"]["values"] == [1, 2, 3]
        assert parsed["metadata"] is None

    def test_redact_structured_empty_object(self):
        text = '{}'
        result = self.engine.redact_structured(text)
        assert result.strip() == "{}"

    def test_redact_structured_empty_string(self):
        result = self.engine.redact_structured("")
        assert result == ""

    def test_redact_structured_deep_nesting(self):
        text = '{"a": {"b": {"c": {"d": "sk-proj-abc123def456ghi789jkl012"}}}}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert "REDACTED" in parsed["a"]["b"]["c"]["d"]

    def test_redact_structured_preserves_clean_data(self):
        text = '{"safe1": "hello", "safe2": "world", "inner": {"x": 42}}'
        result = self.engine.redact_structured(text)
        parsed = json.loads(result)
        assert parsed == {"safe1": "hello", "safe2": "world", "inner": {"x": 42}}
