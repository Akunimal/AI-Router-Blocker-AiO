# -*- coding: utf-8 -*-
import os
import sys
import subprocess
from ai_blocker.constants import CURRENT_OS, HOSTS_PATH, COMMENT_TAG, BLOCKLIST

if CURRENT_OS == "Windows":
    import ctypes

def is_admin():
    if CURRENT_OS == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def relaunch_as_admin():
    if CURRENT_OS == "Windows":
        try:
            if getattr(sys, "frozen", False):
                executable = sys.executable
                params = " ".join(f'"{a}"' for a in sys.argv[1:])
            else:
                executable = sys.executable
                params = " ".join(f'"{a}"' for a in sys.argv)

            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable, params, None, 1
            )
        except Exception:
            pass
        sys.exit(0)

def _get_subprocess_kwargs():
    if CURRENT_OS == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return {"startupinfo": si}
    return {}

def flush_dns():
    try:
        kwargs = _get_subprocess_kwargs()
        if CURRENT_OS == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, **kwargs)
        elif CURRENT_OS == "Darwin":
            subprocess.run(["dscacheutil", "-flushcache"], capture_output=True, **kwargs)
            subprocess.run(["killall", "-HUP", "mDNSResponder"], capture_output=True, **kwargs)
        else:
            result = subprocess.run(
                ["systemd-resolve", "--flush-caches"], capture_output=True, **kwargs
            )
            if result.returncode != 0:
                subprocess.run(
                    ["resolvectl", "flush-caches"], capture_output=True, **kwargs
                )
    except Exception:
        pass

def count_total_domains():
    seen = set()
    for domains in BLOCKLIST.values():
        seen.update(domains)
    return len(seen)

def get_hosts_status():
    is_blocked = False
    count = 0
    if not os.path.exists(HOSTS_PATH):
        return is_blocked, count
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if COMMENT_TAG in line:
                    is_blocked = True
                    if line.strip() and not line.strip().startswith("#"):
                        count += 1
    except Exception:
        pass
    return is_blocked, count
