import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_blocker.__main__ import main


def test_cli_list_backends(capsys):
    with patch.object(sys, "argv", ["ai-blocker", "--list-backends"]):
        try:
            main()
        except SystemExit as exc:
            assert exc.code == 0

    out = capsys.readouterr().out
    assert "hosts" in out
    assert "firewall-redirect" in out


def test_cli_firewall_dry_run_block(capsys):
    with patch("ai_blocker.__main__.is_admin", return_value=True):
        with patch.object(sys, "argv", ["ai-blocker", "--backend", "firewall-redirect", "--block", "work", "--dry-run"]):
            try:
                main()
            except SystemExit as exc:
                assert exc.code == 0

    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "firewall-redirect" in out


def test_cli_dry_run_does_not_require_admin(capsys):
    with patch("ai_blocker.__main__.is_admin", return_value=False):
        with patch.object(sys, "argv", ["ai-blocker", "--backend", "firewall-redirect", "--block", "work", "--dry-run"]):
            try:
                main()
            except SystemExit as exc:
                assert exc.code == 0

    out = capsys.readouterr().out
    assert "[DRY-RUN]" in out
    assert "Administrator/root privileges" not in out
