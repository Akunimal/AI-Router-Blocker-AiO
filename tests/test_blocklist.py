"""Tests for block actions."""
import sys
from unittest.mock import MagicMock, patch

import pytest

from ai_blocker.block_actions import (
    _domains_for_categories,
    _get_backend,
    activate_block,
    deactivate_block,
    detect_running_ai_editors,
    force_close_processes,
)
from ai_blocker.network_backends import HostsBackend


class TestBlocklistIntegrity:
    def test_blocklist_not_empty(self):
        from ai_blocker import BLOCKLIST
        assert isinstance(BLOCKLIST, dict)
        assert len(BLOCKLIST) > 0

    def test_blocklist_format(self):
        from ai_blocker import BLOCKLIST, CATEGORY_TRANSLATIONS
        for cat, domains in BLOCKLIST.items():
            assert isinstance(cat, str)
            assert isinstance(domains, list)
            assert len(domains) > 0
            for d in domains:
                assert "." in d
            assert cat in CATEGORY_TRANSLATIONS.get("en", {})


class TestForceCloseProcesses:
    def test_windows(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Windows"):
            with patch("ai_blocker.block_actions.subprocess.run") as m:
                m.return_value.returncode = 0
                closed = force_close_processes()
                assert len(closed) > 0
                assert m.call_count > 0

    def test_non_windows(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Linux"):
            with patch("ai_blocker.block_actions.detect_running_ai_editors", return_value=["code"]):
                with patch("ai_blocker.block_actions.subprocess.run"):
                    closed = force_close_processes()
                    assert len(closed) > 0

    def test_exception(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Windows"):
            with patch("ai_blocker.block_actions.subprocess.run", side_effect=Exception("boom")):
                assert force_close_processes() == []


class TestDetectRunning:
    def test_windows(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Windows"):
            with patch("ai_blocker.block_actions.subprocess.run") as m:
                m.return_value.stdout = "code.exe\ncursor.exe\n"
                running = detect_running_ai_editors()
                assert len(running) > 0

    @pytest.mark.skipif(sys.platform == "win32", reason="tests non-Windows path")
    def test_non_windows(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Linux"):
            with patch("ai_blocker.block_actions.subprocess.run") as m:
                m.return_value.stdout = "code\ncursor\n"
                running = detect_running_ai_editors()
                assert len(running) > 0

    def test_exception(self):
        with patch("ai_blocker.block_actions.CURRENT_OS", "Windows"):
            with patch("ai_blocker.block_actions.subprocess.run", side_effect=Exception("boom")):
                assert detect_running_ai_editors() == []


class TestDomainsForCategories:
    def test_merges_domains(self):
        with patch("ai_blocker.block_actions.BLOCKLIST", {
            "cat1": ["a.com", "b.com"],
            "cat2": ["b.com", "c.com"],
        }):
            domains = _domains_for_categories(["cat1", "cat2"])
            assert sorted(domains) == ["a.com", "b.com", "c.com"]

    def test_empty_category(self):
        with patch("ai_blocker.block_actions.BLOCKLIST", {}):
            assert _domains_for_categories(["missing"]) == []


class TestGetBackend:
    def test_hosts_backend(self):
        with patch("ai_blocker.block_actions.HOSTS_PATH", "/etc/hosts"):
            be = _get_backend("hosts")
            assert isinstance(be, HostsBackend)


class TestActivateBlock:
    def test_dry_run(self):
        with patch("ai_blocker.block_actions.BLOCKLIST", {"cat": ["x.com"]}):
            with patch("ai_blocker.block_actions.plan_backend_activation", return_value=[["cmd"]]):
                ok, msg = activate_block("en", categories_to_block=["cat"], dry_run=True)
                assert ok is True
                assert "DRY-RUN" in msg

    def test_success(self):
        mock_be = MagicMock()
        mock_be.activate.return_value.count = 1
        with patch("ai_blocker.block_actions.BLOCKLIST", {"cat": ["x.com"]}):
            with patch("ai_blocker.block_actions.force_close_processes", return_value=[]):
                with patch("ai_blocker.block_actions._get_backend", return_value=mock_be):
                    ok, msg = activate_block("en", categories_to_block=["cat"])
                    assert ok is True
                    assert "1" in msg

    def test_permission_error(self):
        mock_be = MagicMock()
        mock_be.activate.side_effect = PermissionError("denied")
        with patch("ai_blocker.block_actions.BLOCKLIST", {"cat": ["x.com"]}):
            with patch("ai_blocker.block_actions.force_close_processes", return_value=[]):
                with patch("ai_blocker.block_actions._get_backend", return_value=mock_be):
                    ok, _ = activate_block("en", categories_to_block=["cat"])
                    assert ok is False


class TestDeactivateBlock:
    def test_dry_run(self):
        with patch("ai_blocker.block_actions.plan_backend_deactivation", return_value=[["cmd"]]):
            ok, msg = deactivate_block("en", dry_run=True)
            assert ok is True
            assert "DRY-RUN" in msg

    def test_success(self):
        mock_be = MagicMock()
        mock_be.deactivate.return_value.count = 5
        with patch("ai_blocker.block_actions._get_backend", return_value=mock_be):
            ok, msg = deactivate_block("en")
            assert ok is True
            assert "5" in msg
