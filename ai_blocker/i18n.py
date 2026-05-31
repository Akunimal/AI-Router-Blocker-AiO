# -*- coding: utf-8 -*-
import os
import sys
import json
import locale
from ai_blocker.constants import CURRENT_OS

if CURRENT_OS == "Windows":
    import ctypes

LANG_DISPLAY_MAP = {
    "English": "en",
    "Español": "es",
    "Português": "pt",
    "Français": "fr",
    "Deutsch": "de",
    "Italiano": "it",
    "Русский": "ru",
    "中文 (简体)": "zh",
    "日本語": "ja",
    "한국어": "ko"
}
LANG_CODE_MAP = {v: k for k, v in LANG_DISPLAY_MAP.items()}

CATEGORY_TRANSLATIONS = {}
STRINGS = {}

def load_translations():
    global CATEGORY_TRANSLATIONS, STRINGS
    try:
        # Load relative to package or executable directory
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))

        trans_path = os.path.join(base_dir, "translations.json")
        
        # Fallback to parent directory if in development subfolder
        if not os.path.exists(trans_path):
            trans_path = os.path.join(os.path.dirname(base_dir), "translations.json")
            
        # Try PyInstaller temporary folder fallback (if bundled as data file)
        if not os.path.exists(trans_path) and hasattr(sys, '_MEIPASS'):
            trans_path = os.path.join(sys._MEIPASS, "translations.json")
            
        # Fallback if still not found
        if not os.path.exists(trans_path):
            trans_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "translations.json")

        with open(trans_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            CATEGORY_TRANSLATIONS = data["category_translations"]
            STRINGS = data["strings"]
    except Exception as e:
        print(f"Warning: Failed to load translations.json: {e}")
        # Minimal hardcoded fallback
        CATEGORY_TRANSLATIONS = {"en": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "xAI": "xAI", "Otros": "Others"}}
        STRINGS = {"en": {
            "protected_title": "PROTECTED — Blocking active",
            "protected_desc": "{count} domains redirected to 127.0.0.1",
            "exposed_title": "EXPOSED — No protection",
            "exposed_desc": "Your network traffic to AI is open",
            "btn_block": "🔒  BLOCK AI",
            "btn_unblock": "🔓  UNBLOCK AI",
            "busy_text": "⏳  Processing...",
            "categories_title": "Blocked Categories",
            "domains_label": "{total} domains",
            "running_warning": "⚠ Detected: {editors}",
            "hosts_write_error_title": "Permission Error",
            "hosts_write_error_msg": "Could not write to the hosts file.\nPlease run the application as Administrator.",
            "unexpected_error_title": "Unexpected Error",
            "unexpected_error_msg": "An error occurred:\n{error}",
            "block_success_title": "AI Blocking Active",
            "block_success_msg": "Block successfully activated!\n\n✓ {added_count} domains blocked in hosts file.\n{process_details}\n✓ DNS cache flushed.",
            "unblock_success_title": "AI Blocking Disabled",
            "unblock_success_msg": "Block successfully deactivated!\n\n✓ {removed} entries removed from hosts file.\n✓ DNS cache flushed.\n\nAll AI tools can access the network again.",
            "closed_processes_prefix": "✓ Closed processes: ",
            "no_processes_detected": "• No open AI editors detected.",
            "admin_required_title": "Access Denied",
            "admin_required_msg_windows": "Administrator privileges are required.\n\nRight-click → 'Run as administrator'.",
            "admin_required_msg_unix": "Root privileges are required.\n\nRun with: sudo python3 ai_blocker.py",
            "profile_work": "Work",
            "profile_personal": "Personal",
            "profile_free": "Free",
            "profile_custom": "Custom"
        }}

    # Resolve platform specific strings
    for lang in STRINGS:
        if CURRENT_OS == "Windows":
            STRINGS[lang]["admin_required_msg"] = STRINGS[lang].get("admin_required_msg_windows", "")
        else:
            STRINGS[lang]["admin_required_msg"] = STRINGS[lang].get("admin_required_msg_unix", "")

def detect_system_language():
    # 1. Environment variables
    for env_var in ('LANGUAGE', 'LC_ALL', 'LC_CTYPE', 'LANG'):
        val = os.environ.get(env_var)
        if val:
            code = val.split('_')[0].split('.')[0].lower()
            if code in STRINGS:
                return code

    # 2. locale.getlocale()
    try:
        if hasattr(locale, 'getlocale'):
            lang, _ = locale.getlocale()
            if lang:
                code = lang.split('_')[0].lower()
                if code in STRINGS:
                    return code
    except Exception:
        pass

    # Windows LCID query
    if CURRENT_OS == "Windows":
        try:
            lcid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            lcid_map = {
                1034: "es", 2058: "es", 3082: "es", 4106: "es", 5130: "es", 6154: "es",
                1046: "pt", 2070: "pt",
                1036: "fr", 2060: "fr", 3084: "fr",
                1031: "de", 2055: "de",
                1040: "it",
                1049: "ru",
                2052: "zh", 1028: "zh", 3076: "zh",
                1041: "ja",
                1042: "ko",
            }
            for k, v in lcid_map.items():
                if lcid == k or (lcid & 0x3FF) == (k & 0x3FF):
                    return v
        except Exception:
            pass

    return "en"

# Run initial load on import
load_translations()
