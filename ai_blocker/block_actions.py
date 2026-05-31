# -*- coding: utf-8 -*-
import os
import subprocess

from ai_blocker.constants import BLOCKLIST, COMMENT_TAG, CURRENT_OS, HOSTS_PATH, PROCESS_LIST
from ai_blocker.i18n import STRINGS
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

def activate_block(lang, categories_to_block=None):
    if categories_to_block is None:
        categories_to_block = list(BLOCKLIST.keys())

    closed_list = force_close_processes()
    s = STRINGS[lang]

    try:
        existing_lines = []
        if os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        cleaned_lines = [l for l in existing_lines if COMMENT_TAG not in l]

        if cleaned_lines and not cleaned_lines[-1].endswith("\n"):
            cleaned_lines[-1] += "\n"

        new_entries = []
        added_count = 0

        domains_to_block = []
        for cat in categories_to_block:
            if cat in BLOCKLIST:
                for domain in BLOCKLIST[cat]:
                    if domain not in domains_to_block:
                        domains_to_block.append(domain)

        for domain in domains_to_block:
            entry = f"127.0.0.1 {domain} {COMMENT_TAG}\n"
            new_entries.append(entry)
            added_count += 1

        with open(HOSTS_PATH, "w", encoding="utf-8") as f:
            f.writelines(cleaned_lines + new_entries)

        flush_dns()

        if closed_list:
            process_details = f"{s['closed_processes_prefix']}{', '.join(closed_list)}"
        else:
            process_details = s["no_processes_detected"]

        msg = s["block_success_msg"].format(
            added_count=added_count,
            process_details=process_details
        )
        return True, msg

    except PermissionError:
        return False, s["hosts_write_error_msg"]
    except Exception as e:
        return False, s["unexpected_error_msg"].format(error=str(e))

def deactivate_block(lang):
    s = STRINGS[lang]
    try:
        if not os.path.exists(HOSTS_PATH):
            return True, s["unblock_success_msg"].format(removed=0)

        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_count = len(lines)
        cleaned = [l for l in lines if COMMENT_TAG not in l]
        removed = original_count - len(cleaned)

        with open(HOSTS_PATH, "w", encoding="utf-8") as f:
            f.writelines(cleaned)

        flush_dns()

        msg = s["unblock_success_msg"].format(removed=removed)
        return True, msg

    except PermissionError:
        return False, s["hosts_write_error_msg"]
    except Exception as e:
        return False, s["unexpected_error_msg"].format(error=str(e))
