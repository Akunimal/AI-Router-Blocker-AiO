# -*- coding: utf-8 -*-
"""
Kernel-level network backend stubs for Windows Filtering Platform (WFP) and
Linux eBPF socket redirection.

These backends implement the :class:`~ai_blocker.network_backends.NetworkBackend`
protocol but are **experimental stubs**.  Real kernel-level interception
requires platform-specific drivers (WFP callout driver on Windows, BPF
programs on Linux) that cannot be shipped as pure Python.

The stubs document the intended command surface and can be used for dry-run
planning and integration testing.
"""

from __future__ import annotations

import subprocess
from typing import Iterable

from ai_blocker.constants import CURRENT_OS
from ai_blocker.network_backends import BackendResult, CommandRunner, unique_domains
from ai_blocker.system_utils import _get_subprocess_kwargs


class WFPBackend:
    """Windows Filtering Platform backend (experimental stub).

    Uses ``netsh`` WFP commands to block outbound TCP/443 connections to
    AI provider IP ranges.  This is an intermediate approach between
    hosts-file blocking and a real WFP callout driver.

    .. warning::
       A production WFP implementation would require a signed kernel-mode
       driver (``.sys``) registered via ``FwpmFilterAdd0``.  This stub
       uses ``netsh advfirewall`` as an approximation.
    """

    name = "wfp"
    windows_group = "AI CodeGate WFP"

    def __init__(self, runner: CommandRunner | None = None):
        self.runner = runner or self._default_runner

    def activate(self, domains: Iterable[str]) -> BackendResult:
        raise NotImplementedError("WFPBackend is an experimental stub. Use hosts or firewall-redirect for production.")

        domains_list = unique_domains(domains)
        commands = self.plan_activate(domains_list)
        errors: list[str] = []
        for cmd in commands:
            try:
                self.runner(cmd)
            except Exception as e:
                errors.append(str(e))

        if errors:
            return BackendResult(False, len(domains_list), error="; ".join(errors))
        return BackendResult(True, len(domains_list))

    def deactivate(self) -> BackendResult:
        raise NotImplementedError("WFPBackend is an experimental stub. Use hosts or firewall-redirect for production.")

        commands = self.plan_deactivate()
        for cmd in commands:
            try:
                self.runner(cmd)
            except Exception:
                pass
        return BackendResult(True, len(commands))

    def status(self) -> tuple[bool, int]:
        """WFP status requires querying the firewall rule group."""
        if CURRENT_OS != "Windows":
            return False, 0
        try:
            result = self.runner([
                "netsh", "advfirewall", "firewall", "show", "rule",
                f"group={self.windows_group}",
            ])
            if hasattr(result, "stdout") and result.stdout:
                # Count rule entries in output
                count = result.stdout.lower().count("rule name:")
                return count > 0, count
        except Exception:
            pass
        return False, 0

    def plan_activate(self, domains: Iterable[str]) -> list[list[str]]:
        domains_list = unique_domains(domains)
        return [
            [
                "netsh", "advfirewall", "firewall", "add", "rule",
                f"name=AI DevSec WFP block {domain}",
                f"group={self.windows_group}",
                "dir=out", "action=block",
                f"remotehost={domain}",
                "protocol=TCP", "remoteport=443",
            ]
            for domain in domains_list
        ]

    def plan_deactivate(self) -> list[list[str]]:
        return [
            ["netsh", "advfirewall", "firewall", "delete", "rule",
             f"group={self.windows_group}"],
        ]

    @staticmethod
    def _default_runner(command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            command, capture_output=True, text=True, check=False,
            **_get_subprocess_kwargs(),
        )


class EBPFBackend:
    """Linux eBPF socket filter backend (experimental stub).

    Documents the architecture for kernel-level TCP redirection using
    eBPF programs attached to cgroup socket hooks.

    .. warning::
       This backend is a **non-functional stub**.  A real implementation
       requires:

       - A compiled BPF program (C !' BPF bytecode via ``clang``/``llvm``)
       - ``bcc`` or ``libbpf`` Python bindings
       - Root privileges and a Linux kernel "e 5.7 with BTF support
       - The BPF program attached to ``cgroup/connect4`` or ``sockops``

    The stub provides ``plan_activate``/``plan_deactivate`` methods that
    return the ``bpftool`` commands that *would* be needed.
    """

    name = "ebpf"

    # Reference BPF program path (would be compiled at install time)
    _bpf_prog_path = "/opt/devgate/redirect_ai.bpf.o"
    _cgroup_path = "/sys/fs/cgroup"
    _map_name = "codegate_blocked_ips"

    def activate(self, domains: Iterable[str]) -> BackendResult:
        raise NotImplementedError("EBPFBackend is an experimental stub. Use hosts or firewall-redirect for production.")

    def deactivate(self) -> BackendResult:
        raise NotImplementedError("EBPFBackend is an experimental stub. Use hosts or firewall-redirect for production.")

    def status(self) -> tuple[bool, int]:
        return False, 0

    def plan_activate(self, domains: Iterable[str]) -> list[list[str]]:
        """Return the bpftool commands needed to load and attach the BPF program.

        In a real implementation:
        1. Compile the BPF C source to ``.bpf.o``
        2. Load the program and pin the map
        3. Populate the map with resolved IP addresses
        4. Attach the program to the root cgroup
        """
        domains_list = unique_domains(domains)
        commands: list[list[str]] = [
            # Load the BPF program
            ["bpftool", "prog", "load", self._bpf_prog_path,
             "/sys/fs/bpf/codegate_redirect",
             "pinmaps", "/sys/fs/bpf/codegate_maps"],
            # Attach to cgroup for outbound connect interception
            ["bpftool", "cgroup", "attach", self._cgroup_path,
             "connect4", "pinned", "/sys/fs/bpf/codegate_redirect"],
        ]
        # Populate the blocked IPs map (one entry per domain)
        for domain in domains_list:
            commands.append([
                "bpftool", "map", "update", "pinned",
                f"/sys/fs/bpf/codegate_maps/{self._map_name}",
                "key", f"hex {domain}",
                "value", "hex 01",
            ])
        return commands

    def plan_deactivate(self) -> list[list[str]]:
        return [
            ["bpftool", "cgroup", "detach", self._cgroup_path,
             "connect4", "pinned", "/sys/fs/bpf/codegate_redirect"],
            ["rm", "-f", "/sys/fs/bpf/codegate_redirect"],
            ["rm", "-rf", "/sys/fs/bpf/codegate_maps"],
        ]
