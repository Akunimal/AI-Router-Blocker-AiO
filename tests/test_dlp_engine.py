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
        self.engine = DLPEngine(scan_secrets=False, scan_pii=False)

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
