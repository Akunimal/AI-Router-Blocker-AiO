import sys
import os
import pytest
from unittest.mock import mock_open, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import ai_blocker

def test_count_total_domains():
    """Test total domains counter."""
    total = ai_blocker.count_total_domains()
    assert total > 0
    
    # Calculate unique domains
    seen = set()
    for domains in ai_blocker.BLOCKLIST.values():
        seen.update(domains)
    assert total == len(seen)

@patch("os.path.exists")
def test_get_hosts_status_blocked(mock_exists):
    """Test hosts status detector when blocked."""
    mock_exists.return_value = True
    hosts_content = (
        "127.0.0.1 localhost\n"
        f"127.0.0.1 api.openai.com {ai_blocker.COMMENT_TAG}\n"
        f"127.0.0.1 claude.ai {ai_blocker.COMMENT_TAG}\n"
    )
    
    with patch("builtins.open", mock_open(read_data=hosts_content)):
        is_blocked, count = ai_blocker.get_hosts_status()
        assert is_blocked is True
        assert count == 2

@patch("os.path.exists")
def test_get_hosts_status_unblocked(mock_exists):
    """Test hosts status detector when not blocked."""
    mock_exists.return_value = True
    hosts_content = (
        "127.0.0.1 localhost\n"
        "::1 localhost\n"
    )
    
    with patch("builtins.open", mock_open(read_data=hosts_content)):
        is_blocked, count = ai_blocker.get_hosts_status()
        assert is_blocked is False
        assert count == 0

@patch("ai_blocker.HOSTS_PATH", "/mock/hosts")
@patch("os.path.exists")
@patch("ai_blocker.force_close_processes")
@patch("ai_blocker.flush_dns")
def test_activate_block(mock_flush, mock_close, mock_exists):
    """Test block activation writes correct hosts format."""
    mock_exists.return_value = True
    mock_close.return_value = ["Code"]
    hosts_content = "127.0.0.1 localhost\n"
    
    m_open = mock_open(read_data=hosts_content)
    with patch("builtins.open", m_open):
        success, msg = ai_blocker.activate_block("en", categories_to_block=["OpenAI"])
        assert success is True
        
        # Verify hosts file was opened for writing
        m_open.assert_any_call("/mock/hosts", "w", encoding="utf-8")
        
        # Check written data
        handle = m_open()
        written_args = [args[0] for args, kwargs in handle.writelines.call_args_list]
        assert len(written_args) > 0
        
        written_lines = written_args[0]
        # Should include comment tags and openai domains
        has_block_line = any(ai_blocker.COMMENT_TAG in line for line in written_lines)
        assert has_block_line is True
        
        has_openai = any("api.openai.com" in line for line in written_lines)
        assert has_openai is True

@patch("ai_blocker.HOSTS_PATH", "/mock/hosts")
@patch("os.path.exists")
@patch("ai_blocker.flush_dns")
def test_deactivate_block(mock_flush, mock_exists):
    """Test block deactivation removes all block lines."""
    mock_exists.return_value = True
    hosts_content = (
        "127.0.0.1 localhost\n"
        f"127.0.0.1 api.openai.com {ai_blocker.COMMENT_TAG}\n"
    )
    
    m_open = mock_open(read_data=hosts_content)
    with patch("builtins.open", m_open):
        success, msg = ai_blocker.deactivate_block("en")
        assert success is True
        
        handle = m_open()
        written_args = [args[0] for args, kwargs in handle.writelines.call_args_list]
        written_lines = written_args[0]
        
        # All AI-Block lines must be removed
        has_block_line = any(ai_blocker.COMMENT_TAG in line for line in written_lines)
        assert has_block_line is False
