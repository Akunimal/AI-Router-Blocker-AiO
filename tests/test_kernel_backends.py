"""Tests for kernel backend stubs (WFP, eBPF)."""
from unittest.mock import MagicMock, patch
import pytest
from ai_blocker.kernel_backends import WFPBackend, EBPFBackend
from ai_blocker.network_backends import BackendResult


class TestWFPBackend:
    def test_activate_raises(self):
        b = WFPBackend()
        with pytest.raises(NotImplementedError):
            b.activate(["evil.com"])

    def test_deactivate_raises(self):
        b = WFPBackend()
        with pytest.raises(NotImplementedError):
            b.deactivate()

    def test_status_on_windows_found(self):
        mock_run = MagicMock()
        mock_run.stdout = "Rule Name:     rule1\nRule Name:     rule2\n"
        b = WFPBackend(runner=lambda cmd: mock_run)
        with patch("ai_blocker.kernel_backends.CURRENT_OS", "Windows"):
            ok, cnt = b.status()
            assert ok is True
            assert cnt == 2

    def test_status_on_windows_not_found(self):
        mock_run = MagicMock()
        mock_run.stdout = "No rules match the specified criteria."
        b = WFPBackend(runner=lambda cmd: mock_run)
        with patch("ai_blocker.kernel_backends.CURRENT_OS", "Windows"):
            ok, cnt = b.status()
            assert ok is False
            assert cnt == 0

    def test_status_off_windows(self):
        b = WFPBackend()
        with patch("ai_blocker.kernel_backends.CURRENT_OS", "Linux"):
            assert b.status() == (False, 0)

    def test_plan_activate(self):
        b = WFPBackend()
        plans = b.plan_activate(["evil.com", "bad.com"])
        assert len(plans) == 2
        for p in plans:
            assert "netsh" in p
            assert any("block" in part for part in p)

    def test_plan_deactivate(self):
        b = WFPBackend()
        plans = b.plan_deactivate()
        assert len(plans) == 1
        assert "delete" in plans[0]


class TestEBPFBackend:
    def test_activate_raises(self):
        b = EBPFBackend()
        with pytest.raises(NotImplementedError):
            b.activate(["evil.com"])

    def test_deactivate_raises(self):
        b = EBPFBackend()
        with pytest.raises(NotImplementedError):
            b.deactivate()

    def test_status(self):
        b = EBPFBackend()
        assert b.status() == (False, 0)

    def test_plan_activate(self):
        b = EBPFBackend()
        plans = b.plan_activate(["evil.com"])
        assert len(plans) >= 2
        assert "bpftool" in plans[0]
        assert "bpftool" in plans[1]

    def test_plan_activate_multiple_domains(self):
        b = EBPFBackend()
        plans = b.plan_activate(["a.com", "b.com"])
        assert len(plans) == 4  # 2 load/attach + 2 domain entries

    def test_plan_deactivate(self):
        b = EBPFBackend()
        plans = b.plan_deactivate()
        assert len(plans) == 3
        assert "detach" in plans[0]
