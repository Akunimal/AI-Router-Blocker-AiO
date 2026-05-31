import json
import os
import sys
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ai_blocker


def test_sensitive_keys_filtering():
    """Verify that sensitive config keys (like API keys) are not persisted to config file."""
    config_data = {
        "language": "es",
        "openai_key": "sk-1234567890abcdef",  # Should be removed
        "last_toggle_time": 1700000000
    }

    m_open = mock_open()
    with patch("builtins.open", m_open):
        with patch("ai_blocker.get_config_path", return_value="/mock/config.json"):
            ai_blocker.save_config(config_data)

            # Verify open was called
            m_open.assert_called_once_with("/mock/config.json", "w", encoding="utf-8")

            # Capture what was written
            handle = m_open()
            write_calls = handle.write.call_args_list
            written_str = "".join(call[0][0] for call in write_calls)
            written_json = json.loads(written_str)

            # Verify sensitive key was removed
            assert "language" in written_json
            assert "last_toggle_time" in written_json
            assert "openai_key" not in written_json

@patch("os.path.exists")
def test_load_config_filters_sensitive_keys(mock_exists):
    """Verify loading config does not return sensitive keys even if they somehow got in."""
    mock_exists.return_value = True
    raw_config = {
        "language": "pt",
        "openai_key": "dangerous_persisted_key"
    }

    with patch("builtins.open", mock_open(read_data=json.dumps(raw_config))):
        with patch("ai_blocker.get_config_path", return_value="/mock/config.json"):
            config = ai_blocker.load_config()
            assert config["language"] == "pt"
            assert "openai_key" not in config
