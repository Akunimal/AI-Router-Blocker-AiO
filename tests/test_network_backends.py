import os
import sys
from subprocess import CompletedProcess

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_blocker.constants import CURRENT_OS
from ai_blocker.network_backends import (
    FirewallRedirectBackend,
    HostsBackend,
    get_backend_info,
    list_network_backends,
    plan_backend_activation,
    unique_domains,
)


def test_unique_domains_preserves_order():
    assert unique_domains(["api.openai.com", "claude.ai", "api.openai.com"]) == ["api.openai.com", "claude.ai"]


def test_hosts_backend_status_counts_tagged_entries(tmp_path):
    hosts_file = tmp_path / "hosts"
    hosts_file.write_text(
        "127.0.0.1 localhost\n"
        "127.0.0.1 api.openai.com # AI-Block\n"
        "# 127.0.0.1 commented.example # AI-Block\n",
        encoding="utf-8",
    )

    assert HostsBackend(str(hosts_file)).status() == (True, 1)


def test_hosts_backend_activate_replaces_only_managed_entries(tmp_path):
    hosts_file = tmp_path / "hosts"
    hosts_file.write_text(
        "127.0.0.1 localhost\n"
        "127.0.0.1 old.example # AI-Block\n",
        encoding="utf-8",
    )

    backend = HostsBackend(str(hosts_file))
    result = backend.activate(["api.openai.com", "api.openai.com"])

    assert result.success is True
    assert result.count == 1
    content = hosts_file.read_text(encoding="utf-8")
    assert "127.0.0.1 localhost" in content
    assert "old.example" not in content
    assert "127.0.0.1 api.openai.com # AI-Block" in content


def test_firewall_redirect_backend_uses_injected_runner():
    commands = []

    def runner(command):
        commands.append(command)
        return CompletedProcess(command, 0, "", "")

    backend = FirewallRedirectBackend(runner=runner, redirect_port=18080)
    result = backend.activate(["api.openai.com", "api.openai.com"])

    assert result.success is True
    assert result.count == 1
    assert commands == backend.plan_activate(["api.openai.com"])


def test_firewall_redirect_backend_plans_platform_command():
    backend = FirewallRedirectBackend(redirect_port=18080)
    command = backend.plan_activate(["api.openai.com"])[0] if CURRENT_OS != "Darwin" else []

    if CURRENT_OS == "Windows":
        assert command[:5] == ["netsh", "advfirewall", "firewall", "add", "rule"]
        assert "remoteport=443" in command
    elif CURRENT_OS == "Linux":
        assert command == ["iptables", "-t", "nat", "-N", backend.linux_chain]
        assert any("--to-ports" in planned and "18080" in planned for planned in backend.plan_activate(["api.openai.com"]))
    else:
        assert backend.plan_activate(["api.openai.com"]) == []


def test_list_network_backends_exposes_hosts_and_firewall():
    names = {item.name for item in list_network_backends()}
    assert "hosts" in names
    assert "firewall-redirect" in names


def test_get_backend_info_unknown_raises():
    try:
        get_backend_info("invalid-backend")
        assert False, "Expected ValueError for unknown backend"
    except ValueError as exc:
        assert "Unknown network backend" in str(exc)


def test_plan_backend_activation_for_hosts_has_no_commands():
    assert plan_backend_activation("hosts", ["api.openai.com"]) == []
