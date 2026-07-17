# -*- coding: utf-8 -*-
import os
import subprocess
import sys

from ai_blocker.constants import BLOCKLIST, CURRENT_OS

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
    try:
        from ai_blocker.network_backends import HostsBackend
        return HostsBackend().status()
    except Exception:
        return False, 0

def install_root_ca(ca_cert_path):
    """
    Installs the specified root CA certificate into the system's trust store.
    This may require administrative privileges or trigger an OS prompt.
    """
    kwargs = _get_subprocess_kwargs()
    try:
        if CURRENT_OS == "Windows":
            # Using -user avoids the need for strict elevation, but still prompts the user safely.
            subprocess.run(["certutil", "-addstore", "-user", "Root", ca_cert_path], check=True, **kwargs)
        elif CURRENT_OS == "Darwin":
            # macOS requires sudo for system keychain modifications
            subprocess.run(["security", "add-trusted-cert", "-d", "-r", "trustRoot", "-k", "/Library/Keychains/System.keychain", ca_cert_path], check=True, **kwargs)
        else:
            # Linux typically requires copying the file to /usr/local/share/ca-certificates and running update-ca-certificates
            import shutil
            dest = "/usr/local/share/ca-certificates/codegate_root_ca.crt"
            shutil.copy(ca_cert_path, dest)
            subprocess.run(["update-ca-certificates"], check=True, **kwargs)
        return True
    except Exception as e:
        print(f"Failed to install Root CA: {e}")
        return False
