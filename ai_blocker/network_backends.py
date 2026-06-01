# -*- coding: utf-8 -*-

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Callable, Iterable, Protocol

from ai_blocker.constants import COMMENT_TAG, CURRENT_OS, HOSTS_PATH
from ai_blocker.system_utils import _get_subprocess_kwargs, flush_dns

CommandRunner = Callable[[list[str]], subprocess.CompletedProcess]
FlushDns = Callable[[], None]


@dataclass(frozen=True)
class BackendResult:
    success: bool
    count: int
    error: str | None = None


class NetworkBackend(Protocol):
    name: str

    def activate(self, domains: Iterable[str]) -> BackendResult:
        ...

    def deactivate(self) -> BackendResult:
        ...

    def status(self) -> tuple[bool, int]:
        ...


def unique_domains(domains: Iterable[str]) -> list[str]:
    seen = set()
    result = []
    for domain in domains:
        if domain not in seen:
            seen.add(domain)
            result.append(domain)
    return result


class HostsBackend:
    name = "hosts"

    def __init__(self, hosts_path: str = HOSTS_PATH, comment_tag: str = COMMENT_TAG, flush_func: FlushDns = flush_dns):
        self.hosts_path = hosts_path
        self.comment_tag = comment_tag
        self.flush_dns = flush_func

    def activate(self, domains: Iterable[str]) -> BackendResult:
        domains_to_block = unique_domains(domains)
        existing_lines = []
        if os.path.exists(self.hosts_path):
            with open(self.hosts_path, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        cleaned_lines = [line for line in existing_lines if self.comment_tag not in line]
        if cleaned_lines and not cleaned_lines[-1].endswith("\n"):
            cleaned_lines[-1] += "\n"

        new_entries = [f"127.0.0.1 {domain} {self.comment_tag}\n" for domain in domains_to_block]
        with open(self.hosts_path, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines + new_entries)

        self.flush_dns()
        return BackendResult(True, len(new_entries))

    def deactivate(self) -> BackendResult:
        if not os.path.exists(self.hosts_path):
            return BackendResult(True, 0)

        with open(self.hosts_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        cleaned = [line for line in lines if self.comment_tag not in line]
        removed = len(lines) - len(cleaned)
        with open(self.hosts_path, "w", encoding="utf-8") as f:
            f.writelines(cleaned)

        self.flush_dns()
        return BackendResult(True, removed)

    def status(self) -> tuple[bool, int]:
        is_blocked = False
        count = 0
        if not os.path.exists(self.hosts_path):
            return is_blocked, count

        with open(self.hosts_path, "r", encoding="utf-8") as f:
            for line in f:
                if self.comment_tag in line:
                    is_blocked = True
                    if line.strip() and not line.strip().startswith("#"):
                        count += 1
        return is_blocked, count


class FirewallRedirectBackend:
    name = "firewall-redirect"
    linux_chain = "AI_DEVSEC_GATEWAY"
    windows_group = "AI DevSec Gateway"

    def __init__(self, runner: CommandRunner | None = None, redirect_port: int = 8080):
        self.redirect_port = redirect_port
        self.runner = runner or self._default_runner

    def activate(self, domains: Iterable[str]) -> BackendResult:
        domains_to_redirect = unique_domains(domains)
        commands = self.plan_activate(domains_to_redirect)
        for command in commands:
            self.runner(command)
        return BackendResult(True, len(domains_to_redirect))

    def deactivate(self) -> BackendResult:
        commands = self.plan_deactivate()
        for command in commands:
            self.runner(command)
        return BackendResult(True, len(commands))

    def status(self) -> tuple[bool, int]:
        return False, 0

    def plan_activate(self, domains: Iterable[str]) -> list[list[str]]:
        domains_to_redirect = unique_domains(domains)
        if CURRENT_OS == "Windows":
            return [
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name=AI DevSec Gateway redirect {domain}",
                    f"group={self.windows_group}",
                    "dir=out",
                    "action=block",
                    f"remotehost={domain}",
                    "protocol=TCP",
                    "remoteport=443",
                ]
                for domain in domains_to_redirect
            ]
        if CURRENT_OS == "Darwin":
            return []
        commands = [
            ["iptables", "-t", "nat", "-N", self.linux_chain],
            ["iptables", "-t", "nat", "-F", self.linux_chain],
            ["iptables", "-t", "nat", "-C", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", self.linux_chain],
            ["iptables", "-t", "nat", "-I", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", self.linux_chain],
        ]
        commands.extend(
            [
                "iptables",
                "-t",
                "nat",
                "-A",
                self.linux_chain,
                "-p",
                "tcp",
                "--dport",
                "443",
                "-m",
                "comment",
                "--comment",
                f"AI-Block {domain}",
                "-j",
                "REDIRECT",
                "--to-ports",
                str(self.redirect_port),
            ]
            for domain in domains_to_redirect
        )
        return commands

    def plan_deactivate(self) -> list[list[str]]:
        if CURRENT_OS == "Windows":
            return [["netsh", "advfirewall", "firewall", "delete", "rule", f"group={self.windows_group}"]]
        if CURRENT_OS == "Darwin":
            return []
        return [
            ["iptables", "-t", "nat", "-D", "OUTPUT", "-p", "tcp", "--dport", "443", "-j", self.linux_chain],
            ["iptables", "-t", "nat", "-F", self.linux_chain],
            ["iptables", "-t", "nat", "-X", self.linux_chain],
        ]

    @staticmethod
    def _default_runner(command: list[str]) -> subprocess.CompletedProcess:
        return subprocess.run(command, capture_output=True, text=True, check=False, **_get_subprocess_kwargs())


def get_network_backend(name: str = "hosts") -> NetworkBackend:
    if name == HostsBackend.name:
        return HostsBackend()
    if name == FirewallRedirectBackend.name:
        return FirewallRedirectBackend()
    raise ValueError(f"Unknown network backend: {name}")
