"""Tests for DNS flush, UI font selection, and platform detection."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch

import ai_blocker


def test_current_os_is_valid():
    """CURRENT_OS should be one of the three supported platforms."""
    assert ai_blocker.CURRENT_OS in ("Windows", "Linux", "Darwin")


def test_hosts_path_exists_as_string():
    """HOSTS_PATH should be a non-empty string pointing to a valid path."""
    assert isinstance(ai_blocker.HOSTS_PATH, str)
    assert len(ai_blocker.HOSTS_PATH) > 0


def test_comment_tag_format():
    """COMMENT_TAG should start with '#' for hosts file compatibility."""
    assert ai_blocker.COMMENT_TAG.startswith("#")
    assert "AI-Block" in ai_blocker.COMMENT_TAG


def test_ui_font_returns_string():
    """_get_ui_font should return a non-empty font family string."""
    font = ai_blocker._get_ui_font()
    assert isinstance(font, str)
    assert len(font) > 0


def test_app_version_format():
    """APP_VERSION should follow semver-like format."""
    parts = ai_blocker.APP_VERSION.split(".")
    assert len(parts) >= 2
    for part in parts:
        assert part.isdigit()


def test_color_palette_hex_format():
    """All color constants should be valid hex color strings."""
    colors = [
        ai_blocker.COL_BASE, ai_blocker.COL_SURFACE0, ai_blocker.COL_SURFACE1,
        ai_blocker.COL_TEXT, ai_blocker.COL_SUBTEXT, ai_blocker.COL_RED,
        ai_blocker.COL_GREEN, ai_blocker.COL_YELLOW, ai_blocker.COL_BLUE,
        ai_blocker.COL_MAUVE,
    ]
    for color in colors:
        assert color.startswith("#"), f"{color} is not a hex color"
        assert len(color) == 7, f"{color} is not a 7-char hex color"


def test_flush_dns_does_not_raise():
    """flush_dns should handle all OS paths gracefully without exceptions."""
    with patch("ai_blocker.system_utils.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        # Should not raise regardless of OS
        try:
            ai_blocker.flush_dns()
        except Exception as e:
            assert False, f"flush_dns raised {e}"


def test_sensitive_config_keys_defined():
    """SENSITIVE_CONFIG_KEYS should include openai_key to prevent persistence."""
    assert "openai_key" in ai_blocker.SENSITIVE_CONFIG_KEYS
