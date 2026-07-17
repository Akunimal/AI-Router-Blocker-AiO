# -*- coding: utf-8 -*-
"""Tests for system utilities."""
import sys
from unittest.mock import MagicMock, patch

import pytest

from ai_blocker.system_utils import (
    _get_subprocess_kwargs,
    count_total_domains,
    flush_dns,
    get_hosts_status,
    install_root_ca,
    is_admin,
    relaunch_as_admin,
)


class TestIsAdmin:
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows_admin(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.ctypes.windll.shell32.IsUserAnAdmin", return_value=True):
                assert is_admin() is True

    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows_not_admin(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.ctypes.windll.shell32.IsUserAnAdmin", return_value=False):
                assert is_admin() is False

    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows_exception(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.ctypes.windll.shell32.IsUserAnAdmin", side_effect=Exception("denied")):
                assert is_admin() is False

    def test_non_windows_root(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("ai_blocker.system_utils.os.geteuid", create=True, return_value=0):
                assert is_admin() is True

    def test_non_windows_not_root(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("ai_blocker.system_utils.os.geteuid", create=True, return_value=1000):
                assert is_admin() is False


class TestRelaunchAsAdmin:
    def test_non_windows_does_nothing(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            relaunch_as_admin()

    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows_calls_shell_execute(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.sys.exit") as me:
                with patch("ai_blocker.system_utils.ctypes.windll.shell32.ShellExecuteW") as ms:
                    relaunch_as_admin()
                    ms.assert_called_once()
                    me.assert_called_once_with(0)


class TestGetSubprocessKwargs:
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            assert "startupinfo" in _get_subprocess_kwargs()

    def test_non_windows(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            assert _get_subprocess_kwargs() == {}


class TestFlushDNS:
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                flush_dns()
                m.assert_called_once()
                assert "ipconfig" in m.call_args[0][0]

    def test_macos(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Darwin"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                flush_dns()
                assert m.call_count == 2

    def test_linux_systemd(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                m.return_value.returncode = 0
                flush_dns()
                m.assert_called_once()

    def test_linux_fallback(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                m.return_value.returncode = 1
                flush_dns()
                assert m.call_count == 2

    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_exception(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.subprocess.run", side_effect=Exception("boom")):
                flush_dns()


class TestCountTotalDomains:
    def test_unique(self):
        with patch("ai_blocker.system_utils.BLOCKLIST", {"a": ["x.com", "y.com"], "b": ["y.com", "z.com"]}):
            assert count_total_domains() == 3

    def test_empty(self):
        with patch("ai_blocker.system_utils.BLOCKLIST", {}):
            assert count_total_domains() == 0


class TestGetHostsStatus:
    def test_ok(self):
        mb = MagicMock()
        mb.status.return_value = (True, 42)
        with patch("ai_blocker.network_backends.HostsBackend", return_value=mb):
            assert get_hosts_status() == (True, 42)

    def test_exception(self):
        with patch("ai_blocker.network_backends.HostsBackend", side_effect=Exception("fail")):
            assert get_hosts_status() == (False, 0)


class TestInstallRootCA:
    @pytest.mark.skipif(not sys.platform.startswith("win"), reason="Windows-only test")
    def test_windows(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Windows"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                assert install_root_ca("C:/ca.crt") is True
                assert "certutil" in m.call_args[0][0]

    def test_macos(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Darwin"):
            with patch("ai_blocker.system_utils.subprocess.run") as m:
                assert install_root_ca("/tmp/ca.crt") is True
                assert "security" in m.call_args[0][0]

    def test_linux(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("shutil.copy") as cp:
                with patch("ai_blocker.system_utils.subprocess.run"):
                    assert install_root_ca("/tmp/ca.crt") is True
                    cp.assert_called_once()

    def test_failure(self):
        with patch("ai_blocker.system_utils.CURRENT_OS", "Linux"):
            with patch("shutil.copy", side_effect=Exception("fail")):
                assert install_root_ca("/tmp/ca.crt") is False
