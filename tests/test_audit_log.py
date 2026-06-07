# -*- coding: utf-8 -*-
"""Tests for the audit log module."""

import os
import tempfile

from ai_blocker.audit_log import AuditEntry, AuditLog


class TestAuditLog:
    def setup_method(self):
        self.tmp = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp, "test_audit.db")
        self.log = AuditLog(db_path=self.db_path)

    def test_log_and_retrieve(self):
        entry = AuditEntry(
            direction="outbound",
            action="allowed",
            domain="api.openai.com",
            path="/v1/models",
            method="GET",
        )
        row_id = self.log.log_entry(entry)
        assert row_id > 0

        results = self.log.search_entries(domain="openai")
        assert len(results) == 1
        assert results[0].domain == "api.openai.com"

    def test_search_by_action(self):
        self.log.log_entry(AuditEntry(direction="outbound", action="allowed", domain="a.com"))
        self.log.log_entry(AuditEntry(direction="outbound", action="blocked", domain="b.com"))

        allowed = self.log.search_entries(action="allowed")
        assert len(allowed) == 1
        assert allowed[0].domain == "a.com"

    def test_entry_count(self):
        assert self.log.get_entry_count() == 0
        self.log.log_entry(AuditEntry(direction="outbound", action="allowed"))
        self.log.log_entry(AuditEntry(direction="outbound", action="blocked"))
        assert self.log.get_entry_count() == 2

    def test_export_json(self):
        self.log.log_entry(AuditEntry(direction="outbound", action="allowed", domain="test.com"))
        exported = self.log.export_json()
        assert "test.com" in exported
        assert "allowed" in exported

    def test_purge_keeps_recent(self):
        self.log.log_entry(AuditEntry(direction="outbound", action="allowed"))
        removed = self.log.purge_older_than(days=1)
        assert removed == 0
        assert self.log.get_entry_count() == 1

    def test_token_summary(self):
        self.log.log_entry(AuditEntry(
            direction="outbound", action="allowed",
            token_count_in=100, token_count_out=200,
        ))
        self.log.log_entry(AuditEntry(
            direction="outbound", action="allowed",
            token_count_in=50, token_count_out=75,
        ))
        summary = self.log.get_token_summary(hours=1)
        assert summary["tokens_in"] == 150
        assert summary["tokens_out"] == 275
        assert summary["request_count"] == 2

    def test_compute_hash(self):
        h1 = AuditLog.compute_hash("hello world")
        h2 = AuditLog.compute_hash("hello world")
        h3 = AuditLog.compute_hash("different")
        assert h1 == h2
        assert h1 != h3

    def test_dlp_findings_stored_as_json(self):
        entry = AuditEntry(
            direction="outbound", action="redacted",
            dlp_findings=[{"type": "api_key", "text": "sk-xxx"}],
        )
        self.log.log_entry(entry)
        results = self.log.search_entries(action="redacted")
        assert len(results) == 1
        assert results[0].dlp_findings[0]["type"] == "api_key"
