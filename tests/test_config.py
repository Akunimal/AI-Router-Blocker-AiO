"""Tests for config module."""
import json
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ai_blocker.config import (
    get_config_path,
    get_windows_autostart,
    load_config,
    save_config,
    set_windows_autostart,
)


class TestGetConfigPath:
    def test_windows(self):
        with patch("ai_blocker.config.CURRENT_OS", "Windows"):
            with patch.dict("os.environ", {"APPDATA": "C:\\Users\\test\\AppData\\Roaming"}):
                path = get_config_path()
                assert "AppData" in path
                assert "config.json" in path

    def test_non_windows(self):
        with patch("ai_blocker.config.CURRENT_OS", "Linux"):
            with patch("os.path.expanduser", return_value="/home/test"):
                path = get_config_path()
                assert "config.json" in path
                assert "config.json" in path

    def test_creates_dir(self):
        with patch("ai_blocker.config.CURRENT_OS", "Linux"):
            with patch("ai_blocker.config.os.makedirs") as md:
                get_config_path()
                md.assert_called_once()

    def test_creates_dir_error_ignored(self):
        with patch("ai_blocker.config.CURRENT_OS", "Linux"):
            with patch("ai_blocker.config.os.makedirs", side_effect=PermissionError):
                path = get_config_path()
                assert path


class TestLoadConfig:
    def test_returns_empty_when_missing(self):
        with patch("ai_blocker.config.os.path.exists", return_value=False):
            assert load_config() == {}

    def test_returns_empty_on_corrupt_json(self):
        with patch("ai_blocker.config.os.path.exists", return_value=True):
            with patch("builtins.open", mock_open(read_data="not json")):
                assert load_config() == {}

    def test_filters_sensitive_keys(self):
        with patch("ai_blocker.config.os.path.exists", return_value=True):
            data = json.dumps({"lang": "es", "openai_key": "sk-secret"})
            with patch("builtins.open", mock_open(read_data=data)):
                cfg = load_config()
                assert cfg["lang"] == "es"
                assert "openai_key" not in cfg


class TestSaveConfig:
    def test_removes_sensitive_keys(self):
        m = mock_open()
        with patch("builtins.open", m):
            with patch("ai_blocker.config.get_config_path", return_value="/c.json"):
                save_config({"lang": "en", "openai_key": "sk-bad"})
        written = "".join(c[0][0] for c in m().write.call_args_list)
        data = json.loads(written)
        assert data["lang"] == "en"
        assert "openai_key" not in data

    def test_exception_ignored(self):
        with patch("ai_blocker.config.get_config_path", return_value="/c.json"):
            with patch("builtins.open", side_effect=PermissionError):
                save_config({"lang": "en"})


class TestWindowsAutostart:
    """Windows autostart registry tests using mock winreg module."""

    @pytest.fixture(autouse=True)
    def _setup_winreg(self):
        """Inject a mock winreg into sys.modules to avoid ModuleNotFoundError on non-Windows."""
        self._mock_winreg = MagicMock()
        self._mock_winreg.HKEY_CURRENT_USER = MagicMock()
        self._mock_winreg.KEY_SET_VALUE = MagicMock()
        self._mock_winreg.KEY_READ = MagicMock()
        self._mock_winreg.REG_SZ = MagicMock()
        self._mock_winreg.QueryValueEx.return_value = ("cmd", 0)
        with patch.dict("sys.modules", {"winreg": self._mock_winreg}):
            yield

    def test_set_non_windows(self):
        with patch("ai_blocker.config.CURRENT_OS", "Linux"):
            assert set_windows_autostart(True) is False

    def test_set_windows_enable(self):
        with patch("ai_blocker.config.CURRENT_OS", "Windows"):
            assert set_windows_autostart(True) is True

    def test_set_windows_disable(self):
        with patch("ai_blocker.config.CURRENT_OS", "Windows"):
            assert set_windows_autostart(False) is True

    def test_get_non_windows(self):
        with patch("ai_blocker.config.CURRENT_OS", "Linux"):
            assert get_windows_autostart() is False

    def test_get_windows_found(self):
        with patch("ai_blocker.config.CURRENT_OS", "Windows"):
            assert get_windows_autostart() is True

    def test_get_windows_not_found(self):
        with patch("ai_blocker.config.CURRENT_OS", "Windows"):
            with patch("winreg.OpenKey", side_effect=FileNotFoundError):
                assert get_windows_autostart() is False
