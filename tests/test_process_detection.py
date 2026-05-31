"""Tests for process detection and platform-specific behavior."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock, patch

import ai_blocker


def test_detect_running_editors_with_no_processes():
    """Should return empty list when no AI editors are running."""
    mock_result = MagicMock()
    mock_result.stdout = "System\nsvchost.exe\nexplorer.exe\n"

    with patch("ai_blocker.block_actions.subprocess.run", return_value=mock_result):
        result = ai_blocker.detect_running_ai_editors()
        assert isinstance(result, list)
        assert len(result) == 0


def test_detect_running_editors_finds_vscode():
    """Should detect VS Code (Code.exe) as a running AI editor."""
    if ai_blocker.CURRENT_OS != "Windows":
        return  # Skip on non-Windows

    mock_result = MagicMock()
    mock_result.stdout = "Code.exe  12345 Console  1  100,000 K\nsvchost.exe\n"

    with patch("ai_blocker.block_actions.subprocess.run", return_value=mock_result):
        result = ai_blocker.detect_running_ai_editors()
        assert "Code" in result


def test_force_close_returns_list():
    """force_close_processes should always return a list."""
    mock_result = MagicMock()
    mock_result.stdout = ""

    with patch("ai_blocker.block_actions.subprocess.run", return_value=mock_result):
        result = ai_blocker.force_close_processes()
        assert isinstance(result, list)


def test_process_list_is_populated():
    """PROCESS_LIST should contain common AI editor names."""
    assert len(ai_blocker.PROCESS_LIST) > 0
    # Check for at least VS Code and Cursor (key targets)
    lower_list = [p.lower().replace(".exe", "") for p in ai_blocker.PROCESS_LIST]
    assert "code" in lower_list
    assert "cursor" in lower_list
