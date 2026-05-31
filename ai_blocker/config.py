# -*- coding: utf-8 -*-
import json
import os
import sys

from ai_blocker.constants import CURRENT_OS

SENSITIVE_CONFIG_KEYS = {"openai_key"}

def get_config_path():
    if CURRENT_OS == "Windows":
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base_dir = os.path.expanduser("~/.config")
    app_dir = os.path.join(base_dir, "AI-Blocker")
    try:
        os.makedirs(app_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(app_dir, "config.json")

def load_config():
    path = get_config_path()
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key in SENSITIVE_CONFIG_KEYS:
                data.pop(key, None)
            return data
        except Exception:
            pass
    return {}

def save_config(config_data):
    path = get_config_path()
    try:
        safe_config = dict(config_data)
        for key in SENSITIVE_CONFIG_KEYS:
            safe_config.pop(key, None)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(safe_config, f, indent=4, ensure_ascii=False)
    except Exception:
        pass

def set_windows_autostart(enabled=True):
    if CURRENT_OS != "Windows":
        return False
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        # Determine script/executable command line
        if getattr(sys, 'frozen', False):
            cmd = f'"{sys.executable}" --minimized'
        else:
            # When modularized, the root file is still ai_blocker.py
            # But let's check: if we are running as module, we need to run main file
            root_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai_blocker.py"))
            cmd = f'"{sys.executable}" "{root_file}" --minimized'

        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.SetValueEx(key, "AIBlocker", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "AIBlocker")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def get_windows_autostart():
    if CURRENT_OS != "Windows":
        return False
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "AIBlocker")
        winreg.CloseKey(key)
        return True
    except Exception:
        return False
