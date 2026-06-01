# -*- coding: utf-8 -*-
import os
import subprocess

from ai_blocker.constants import BLOCKLIST, CURRENT_OS, HOSTS_PATH, PROCESS_LIST
from ai_blocker.i18n import STRINGS
from ai_blocker.network_backends import (
    HostsBackend,
    get_network_backend,
    plan_backend_activation,
    plan_backend_deactivation,
    unique_domains,
)
from ai_blocker.system_utils import _get_subprocess_kwargs, flush_dns


def force_close_processes():
    closed = []
    kwargs = _get_subprocess_kwargs()

    try:
        if CURRENT_OS == "Windows":
            args = ["taskkill", "/F"]
            for proc in PROCESS_LIST:
                args.extend(["/IM", proc])
            result = subprocess.run(args, capture_output=True, text=True, **kwargs)
            out_lower = result.stdout.lower()
            for proc in PROCESS_LIST:
                if f'"{proc.lower()}"' in out_lower or f'{proc.lower()}' in out_lower:
                    closed.append(proc.replace(".exe", ""))
        else:
            active = detect_running_ai_editors()
            if active:
                args = ["killall"] + active
                subprocess.run(args, capture_output=True, text=True, **kwargs)
                closed = active
    except Exception:
        pass
    return closed

def detect_running_ai_editors():
    running = []
    kwargs = _get_subprocess_kwargs()

    try:
        if CURRENT_OS == "Windows":
            result = subprocess.run(["tasklist", "/NH"], capture_output=True, text=True, **kwargs)
            out_lower = result.stdout.lower()
            for proc in PROCESS_LIST:
                if proc.lower() in out_lower:
                    running.append(proc.replace(".exe", ""))
        else:
            result = subprocess.run(["ps", "-A", "-o", "comm="], capture_output=True, text=True, **kwargs)
            out_lines = result.stdout.splitlines()
            active = set()
            for line in out_lines:
                active.add(os.path.basename(line.strip()).lower())

            for proc in PROCESS_LIST:
                if proc.lower() in active:
                    running.append(proc)
    except Exception:
        pass
    return running

def _domains_for_categories(categories_to_block):
    domains_to_block = []
    for cat in categories_to_block:
        if cat in BLOCKLIST:
            domains_to_block.extend(BLOCKLIST[cat])
    return unique_domains(domains_to_block)


def _get_backend(backend_name):
    if backend_name == HostsBackend.name:
        return HostsBackend(HOSTS_PATH, flush_func=flush_dns)
    return get_network_backend(backend_name)


def _format_command_plan(commands):
    if not commands:
        return "No command plan available for this backend."
    return "\n".join(" ".join(cmd) for cmd in commands)


def activate_block(lang, categories_to_block=None, backend_name="hosts", dry_run=False):
    if categories_to_block is None:
        categories_to_block = list(BLOCKLIST.keys())

    closed_list = force_close_processes()
    s = STRINGS[lang]

    try:
        domains = _domains_for_categories(categories_to_block)
        if dry_run:
            planned_commands = plan_backend_activation(backend_name, domains)
            msg = (
                f"[DRY-RUN] Backend '{backend_name}' activation plan for {len(domains)} domains:\n"
                f"{_format_command_plan(planned_commands)}"
            )
            return True, msg

        backend = _get_backend(backend_name)
        result = backend.activate(domains)

        if closed_list:
            process_details = f"{s['closed_processes_prefix']}{', '.join(closed_list)}"
        else:
            process_details = s["no_processes_detected"]

        msg = s["block_success_msg"].format(
            added_count=result.count,
            process_details=process_details
        )
        return True, msg

    except PermissionError:
        return False, s["hosts_write_error_msg"]
    except Exception as e:
        return False, s["unexpected_error_msg"].format(error=str(e))

def deactivate_block(lang, backend_name="hosts", dry_run=False):
    s = STRINGS[lang]
    try:
        if dry_run:
            planned_commands = plan_backend_deactivation(backend_name)
            msg = (
                f"[DRY-RUN] Backend '{backend_name}' deactivation plan:\n"
                f"{_format_command_plan(planned_commands)}"
            )
            return True, msg

        backend = _get_backend(backend_name)
        result = backend.deactivate()
        msg = s["unblock_success_msg"].format(removed=result.count)
        return True, msg

    except PermissionError:
        return False, s["hosts_write_error_msg"]
    except Exception as e:
        return False, s["unexpected_error_msg"].format(error=str(e))
