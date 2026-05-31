# -*- coding: utf-8 -*-
"""
AI Network Blocker — Kill switch para editores de código con IA.
Bloquea/desbloquea dominios de IA editando el archivo hosts del sistema.
Soporte para Windows, Linux y macOS.
Soporte para 10 idiomas con detección automática y selector manual.
Requiere privilegios de Administrador / root.

--- EN ---
AI Network Blocker — Kill switch for AI-powered code editors.
Blocks/unblocks AI domains by editing the system hosts file.
Supports Windows, Linux and macOS.
Supports 10 languages with automatic detection and manual selector.
Requires Administrator / root privileges.
"""

import os
import sys
import platform
if platform.system() == "Windows":
    import ctypes
import locale

# =====================================================================
# DETECCIÓN DE PLATAFORMA / PLATFORM DETECTION
# =====================================================================
CURRENT_OS = platform.system()  # 'Windows', 'Linux', 'Darwin'
import subprocess
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import threading
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# =====================================================================
# VERSIÓN / VERSION
# =====================================================================
APP_VERSION = "1.2.1"

# =====================================================================
# CONFIGURACIÓN LOCAL / LOCAL CONFIGURATION
# =====================================================================
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

# =====================================================================
# CONFIGURACIÓN DE DOMINIOS A BLOQUEAR / BLOCKLIST DOMAIN CONFIGURATION
# =====================================================================
BLOCKLIST = {
    "OpenAI": [
        "api.openai.com", "chatgpt.com", "chat.openai.com",
        "platform.openai.com", "openai.com", "auth.openai.com",
        "oaistatic.com", "oaiusercontent.com", "labs.openai.com",
    ],
    "Anthropic": [
        "api.anthropic.com", "claude.ai", "anthropic.com",
        "claudeusercontent.com",
    ],
    "GitHub Copilot": [
        "api.githubcopilot.com", "copilot.github.com",
        "githubcopilot.com", "api.individual.githubcopilot.com",
    ],
    "Google AI": [
        "generativelanguage.googleapis.com", "aistudio.google.com",
        "gemini.google.com", "ai.google.dev",
    ],
    "Meta AI": [
        "meta.ai", "ai.meta.com",
    ],
    "Mistral AI": [
        "api.mistral.ai", "mistral.ai",
    ],
    "Microsoft Copilot": [
        "copilot.microsoft.com", "bing.com", "edgeservices.bing.com",
    ],
    "DeepSeek": [
        "deepseek.com", "api.deepseek.com",
    ],
    "xAI": [
        "api.x.ai", "grok.x.ai", "x.ai",
    ],
    "Otros": [
        "api.perplexity.ai", "perplexity.ai",
        "app.wordware.ai",
    ],
}

CATEGORY_ICONS = {
    "OpenAI": "🟢", "Anthropic": "🟠", "GitHub Copilot": "🐙",
    "Google AI": "🔵", "Meta AI": "🔷", "Mistral AI": "🌊",
    "Microsoft Copilot": "🟦", "DeepSeek": "🔮", "xAI": "🤖", "Otros": "📦",
}

# Merge custom domains from local config into BLOCKLIST at startup
_startup_config = load_config()
_custom_domains = _startup_config.get("custom_domains", {})
for _cat, _domains in _custom_domains.items():
    if _cat in BLOCKLIST:
        for _domain in _domains:
            if _domain not in BLOCKLIST[_cat]:
                BLOCKLIST[_cat].append(_domain)
    else:
        BLOCKLIST[_cat] = _domains

if CURRENT_OS == "Windows":
    PROCESS_LIST = [
        "Code.exe", "Cursor.exe", "Windsurf.exe", "Claude.exe",
        "Trae.exe", "Cline.exe", "Roo.exe", "Augment.exe",
    ]
else:
    # En Linux/macOS los procesos no tienen extensión .exe
    # On Linux/macOS processes don't have .exe extension
    PROCESS_LIST = [
        "code", "cursor", "windsurf", "claude",
        "trae", "cline", "roo", "augment",
    ]

COMMENT_TAG = "# AI-Block"

if CURRENT_OS == "Windows":
    HOSTS_PATH = os.path.join(
        os.environ.get("SystemRoot", r"C:\Windows"),
        r"System32\drivers\etc\hosts",
    )
else:
    # Linux y macOS usan /etc/hosts
    # Linux and macOS use /etc/hosts
    HOSTS_PATH = "/etc/hosts"

# =====================================================================
# PALETA DE COLORES — Catppuccin Mocha (dark premium) / COLOR PALETTE
# =====================================================================
COL_BASE      = "#1E1E2E"   # Fondo principal / Main background
COL_SURFACE0  = "#313244"   # Panel secundario / Secondary surface panel
COL_SURFACE1  = "#45475A"   # Bordes sutiles / Subtle borders
COL_TEXT      = "#CDD6F4"   # Texto principal / Main text
COL_SUBTEXT   = "#A6ADC8"   # Texto secundario / Secondary text
COL_RED       = "#F38BA8"   # Rojo suave / Soft red
COL_GREEN     = "#A6E3A1"   # Verde suave / Soft green
COL_YELLOW    = "#F9E2AF"   # Amarillo / Yellow
COL_BLUE      = "#89B4FA"   # Azul accent / Accent blue
COL_MAUVE     = "#CBA6F7"   # Púrpura accent / Accent purple

# =====================================================================
# FUENTE DEL SISTEMA / SYSTEM FONT
# =====================================================================
def _get_ui_font():
    if CURRENT_OS == "Windows":
        return "Segoe UI"
    elif CURRENT_OS == "Darwin":
        return "Helvetica Neue"
    else:
        return "DejaVu Sans"

UI_FONT = _get_ui_font()

# =====================================================================
# TRADUCCIONES PARA 10 IDIOMAS / TRANSLATIONS FOR 10 LANGUAGES
# =====================================================================
import json

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
        # Load relative to script directory to support frozen exe and development mode
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        trans_path = os.path.join(base_dir, "translations.json")
        # Try PyInstaller temporary folder fallback (if bundled as data file)
        if not os.path.exists(trans_path) and hasattr(sys, '_MEIPASS'):
            trans_path = os.path.join(sys._MEIPASS, "translations.json")
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

# Load the translations now
load_translations()


# =====================================================================
# UTILIDADES DE SISTEMA / SYSTEM UTILITIES
# =====================================================================
def is_admin():
    """
    Retorna True si el proceso corre con privilegios de Administrador / root.
    Returns True if the process runs with Administrator / root privileges.
    """
    if CURRENT_OS == "Windows":
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception:
            return False
    else:
        # Linux / macOS: verificar si somos root (euid == 0)
        # Linux / macOS: check if we are root (euid == 0)
        return os.geteuid() == 0


def relaunch_as_admin():
    """
    En Windows: re-lanza el ejecutable solicitando elevación UAC.
    En Linux/macOS: no se auto-relanza, se muestra mensaje al usuario.

    On Windows: relaunches the executable requesting UAC elevation.
    On Linux/macOS: does not auto-relaunch, shows message to user.
    """
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
    else:
        # En Linux/macOS no intentamos auto-relanzar.
        # El flujo principal mostrará el mensaje de error.
        # On Linux/macOS we don't attempt auto-relaunch.
        # The main flow will show the error message.
        pass


def _get_subprocess_kwargs():
    """
    Retorna argumentos adicionales para subprocess según el OS.
    En Windows, oculta la ventana de consola. En otros OS, retorna dict vacío.

    Returns additional subprocess arguments based on OS.
    On Windows, hides the console window. On other OSes, returns empty dict.
    """
    if CURRENT_OS == "Windows":
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        return {"startupinfo": si}
    return {}


def flush_dns():
    """
    Limpia la caché DNS del sistema de forma silenciosa.
    Silently flushes the system DNS cache.
    """
    try:
        kwargs = _get_subprocess_kwargs()
        if CURRENT_OS == "Windows":
            subprocess.run(["ipconfig", "/flushdns"], capture_output=True, **kwargs)
        elif CURRENT_OS == "Darwin":
            # macOS: dscacheutil + mDNSResponder
            subprocess.run(["dscacheutil", "-flushcache"], capture_output=True, **kwargs)
            subprocess.run(["killall", "-HUP", "mDNSResponder"], capture_output=True, **kwargs)
        else:
            # Linux: intentar systemd-resolve primero, luego resolvectl
            # Linux: try systemd-resolve first, then resolvectl
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
    """
    Retorna el número total de dominios únicos en la BLOCKLIST.
    Returns the total number of unique domains in the BLOCKLIST.
    """
    seen = set()
    for domains in BLOCKLIST.values():
        seen.update(domains)
    return len(seen)


def get_hosts_status():
    """
    Lee el archivo hosts una sola vez y retorna el estado de bloqueo y la cantidad de dominios.
    Reads the hosts file once and returns the block status and domain count.
    """
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


def detect_system_language():
    """
    Detecta el idioma del sistema de forma robusta y moderna.
    Retorna el código de dos letras (es, en, pt, fr, de, it, ru, zh, ja, ko).
    Si no está soportado o falla, retorna 'en' (inglés).

    Robustly and modernly detects the system language.
    Returns the two-letter code (es, en, pt, fr, de, it, ru, zh, ja, ko).
    If unsupported or fails, returns 'en' (English).
    """
    # 1. Variables de entorno (cross-platform, moderno)
    for env_var in ('LANGUAGE', 'LC_ALL', 'LC_CTYPE', 'LANG'):
        val = os.environ.get(env_var)
        if val:
            code = val.split('_')[0].split('.')[0].lower()
            if code in STRINGS:
                return code

    # 2. locale.getlocale() (locale.getdefaultlocale() está deprecado en Python 3.11+)
    try:
        if hasattr(locale, 'getlocale'):
            lang, _ = locale.getlocale()
            if lang:
                code = lang.split('_')[0].lower()
                if code in STRINGS:
                    return code
    except Exception:
        pass
    
    # Alternativa en Windows / Windows alternative
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


def set_windows_autostart(enabled=True):
    if CURRENT_OS != "Windows":
        return False
    import winreg
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        if getattr(sys, 'frozen', False):
            cmd = f'"{sys.executable}" --minimized'
        else:
            cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" --minimized'
            
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


# =====================================================================
# ACCIONES DE BLOQUEO / DESBLOQUEO / BLOCKING / UNBLOCKING ACTIONS
# =====================================================================
def force_close_processes():
    """
    Cierra de forma forzada los editores de IA en ejecución de forma optimizada.
    Force closes running AI editors efficiently.
    """
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
            # En Unix, primero detectamos cuáles están abiertos para saber qué cerrar
            # On Unix, detect which ones are running first
            active = detect_running_ai_editors()
            if active:
                args = ["killall"] + active
                subprocess.run(args, capture_output=True, text=True, **kwargs)
                closed = active
    except Exception:
        pass
    return closed


def detect_running_ai_editors():
    """
    Detecta qué editores de IA están en ejecución actualmente de forma optimizada.
    Detects which AI editors are currently running efficiently.
    """
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
            # En Unix, listamos los comandos activos una sola vez
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
    """
    Aplica el bloqueo de red de IAs para las categorías seleccionadas.
    Applies the AI network block for selected categories.
    """
    if categories_to_block is None:
        categories_to_block = list(BLOCKLIST.keys())

    # 1. Cierra procesos activos / 1. Close active processes
    closed_list = force_close_processes()
    s = STRINGS[lang]

    # 2. Modifica el archivo hosts / 2. Modify hosts file
    try:
        existing_lines = []
        if os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        # Remove all existing AI-Block lines first so we rebuild cleanly
        cleaned_lines = [l for l in existing_lines if COMMENT_TAG not in l]

        if cleaned_lines and not cleaned_lines[-1].endswith("\n"):
            cleaned_lines[-1] += "\n"

        new_entries = []
        added_count = 0

        # Build list of unique domains to block based on selected categories
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

        # 3. Limpia caché DNS / 3. Flush DNS cache
        flush_dns()

        # Construye detalles de procesos / Build process details
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
    """
    Desactiva el bloqueo de red de IAs.
    Deactivates the AI network block.
    """
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

        # Limpia caché DNS / Flush DNS cache
        flush_dns()

        # Construye mensaje de éxito / Build success message
        msg = s["unblock_success_msg"].format(removed=removed)
        return True, msg

    except PermissionError:
        return False, s["hosts_write_error_msg"]
    except Exception as e:
        return False, s["unexpected_error_msg"].format(error=str(e))


# =====================================================================
# API GATEWAY & PROXY LOGIC / LÓGICA DEL GATEWAY Y PROXY
# =====================================================================
class GatewayHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._proxy_request("GET")
    
    def do_POST(self):
        self._proxy_request("POST")

    def do_OPTIONS(self):
        self._proxy_request("OPTIONS")
        
    def _proxy_request(self, method):
        target = self.server.target_url.rstrip("/") + self.path
        headers = {}
        for k, v in self.headers.items():
            if k.lower() not in ['host', 'accept-encoding']:
                headers[k] = v
        
        data = None
        if method in ['POST', 'PUT', 'PATCH']:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                data = self.rfile.read(content_length)
                
        req = urllib.request.Request(target, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                self.send_response(response.status)
                for k, v in response.headers.items():
                    if k.lower() not in ['transfer-encoding']:
                        self.send_header(k, v)
                self.end_headers()
                
                while True:
                    chunk = response.read(1024)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    self.wfile.flush()
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ['transfer-encoding']:
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(f"Gateway Error: {e}".encode())

# =====================================================================
# INTERFAZ GRÁFICA PREMIUM CON INTERNACIONALIZACIÓN / PREMIUM GUI WITH i18n
# =====================================================================
class AIBlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Router-Blocker-AiO")
        self.root.geometry("520x650")
        self.root.minsize(480, 600)
        self.root.configure(bg=COL_BASE)

        # Intentar poner el icono si existe / Try to load icon if it exists
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Configurar tema para Combobox moderno / Configure theme for modern Combobox
        self._setup_ttk_styles()

        # Cargar configuración local / Load local configuration
        self.config = load_config()

        # Detectar/cargar idioma inicial / Detect/load initial language
        self.current_lang = self.config.get("language", detect_system_language())
        if self.current_lang not in STRINGS:
            self.current_lang = "en"
        
        # Estado actual del archivo hosts / Current status of the hosts file
        self.is_blocked, _ = get_hosts_status()
        self.is_busy = False
        self._scan_after_id = None
        self.last_visuals_blocked = self.is_blocked
        self._anim_id = 0
        self.active_toasts = []
        self.logs = self.config.get("logs", [])
        self.log_expanded = False
        self.last_toggle_time = self.config.get("last_toggle_time", None)
        self.gateway_server = None
        self.gateway_running = False

        # Cargar perfil guardado / Load saved profile
        self.selected_profile_key = self.config.get("profile", "work")

        # Estado de categorías y variables / Category state and variables
        self.category_vars = {}
        self.category_checkboxes = {}
        checked_cats = self.config.get("checked_categories", {})
        for cat in BLOCKLIST:
            # Por defecto True, salvo si está en las preferencias guardadas
            default_val = checked_cats.get(cat, True)
            self.category_vars[cat] = tk.BooleanVar(value=default_val)

        # Configurar bandeja del sistema / Configure system tray
        if CURRENT_OS == "Windows":
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
            self.root.bind("<Unmap>", self._on_window_unmap)
            self.tray_icon = WindowsTrayIcon(self)
        else:
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        # Atajos de teclado / Keyboard shortcuts
        self.root.bind("<Control-b>", lambda e: self._handle_toggle())
        self.root.bind("<Control-q>", lambda e: self.exit_app())
        self.root.bind("<Control-l>", lambda e: self._toggle_log_panel())

        # Configurar Notebook (Pestañas) / Configure Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Tab 1: Blocker (Original)
        self.tab_blocker = tk.Frame(self.notebook, bg=COL_BASE)
        self.notebook.add(self.tab_blocker, text=" 🛡️ AI Blocker ")

        # Tab 2: DevSec Gateway (Nuevas funciones)
        self.tab_gateway = tk.Frame(self.notebook, bg=COL_BASE)
        self.notebook.add(self.tab_gateway, text=" ⚡ DevSec Gateway ")

        # Construir la interfaz de la pestaña 1 / Build Tab 1 interface
        self._build_header()
        self._build_status_card()
        self._build_toggle_button()
        self._build_info_panel()
        self._build_log_panel()
        self._build_footer()

        # Construir la interfaz de la pestaña 2 / Build Tab 2 interface
        self._build_gateway_tab()

        # Actualizar visualización e idioma / Update display and language
        self._update_language_ui()

        # Iniciar verificación de conectividad activa / Start active connectivity check
        self._schedule_connectivity_check()

    def _setup_ttk_styles(self):
        """
        Configura estilos oscuros modernos para widgets ttk.
        Configures modern dark styles for ttk widgets.
        """
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure(
            "TCombobox",
            fieldbackground=COL_SURFACE0,
            background=COL_SURFACE1,
            foreground=COL_TEXT,
            bordercolor=COL_SURFACE1,
            arrowcolor=COL_TEXT,
            lightcolor=COL_SURFACE1,
            darkcolor=COL_SURFACE1
        )
        # Configurar colores de la lista desplegable del Combobox / Configure dropdown list colors for Combobox
        self.root.option_add("*TCombobox*Listbox.background", COL_SURFACE0)
        self.root.option_add("*TCombobox*Listbox.foreground", COL_TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COL_BLUE)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        self.root.option_add("*TCombobox*Listbox.font", ("Segoe UI", 9))

    # -----------------------------------------------------------------
    # Header — Título, Versión y Dropdown de Idioma / Header — Title, Version and Language Dropdown
    # -----------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.tab_blocker, bg=COL_BASE)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))

        # Título principal / Main title
        self.title_label = tk.Label(
            header, text="🛡️  AI-Router-Blocker-AiO",
            font=("Segoe UI", 16, "bold"),
            bg=COL_BASE, fg=COL_TEXT,
        )
        self.title_label.pack(side=tk.LEFT)

        # Contenedor a la derecha / Right-side panel
        right_panel = tk.Frame(header, bg=COL_BASE)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Selector de perfil (Combobox) / Profile selector (Combobox)
        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            right_panel,
            textvariable=self.profile_var,
            state="readonly",
            width=12,
            font=("Segoe UI", 9)
        )
        self.profile_combo.pack(side=tk.LEFT, padx=(0, 10), pady=(4, 0))
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)

        # Selector de idioma (Combobox) / Language selector (Combobox)
        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(
            right_panel,
            textvariable=self.lang_var,
            values=list(LANG_DISPLAY_MAP.keys()),
            state="readonly",
            width=12,
            font=("Segoe UI", 9)
        )
        self.lang_combo.pack(side=tk.LEFT, padx=(0, 10), pady=(4, 0))
        
        # Sincronizar el valor inicial del Combobox con el idioma detectado / Synchronize initial Combobox value with detected language
        initial_display = LANG_CODE_MAP.get(self.current_lang, "English")
        self.lang_combo.set(initial_display)
        
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        # Etiqueta de versión / Version label
        self.version_label = tk.Label(
            right_panel, text=f"v{APP_VERSION}",
            font=(UI_FONT, 9),
            bg=COL_BASE, fg=COL_SUBTEXT,
        )
        self.version_label.pack(side=tk.RIGHT, pady=(6, 0))

    # -----------------------------------------------------------------
    # Card de estado — indicador visual grande / Status card — large visual indicator
    # -----------------------------------------------------------------
    def _build_status_card(self):
        self.card_frame = tk.Frame(
            self.tab_blocker, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        self.card_frame.pack(fill=tk.X, padx=24, pady=(16, 0))

        inner = tk.Frame(self.card_frame, bg=COL_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=14)

        # Indicador de estado (círculo) / Status indicator (dot)
        self.status_dot = tk.Label(
            inner, text="●", font=(UI_FONT, 22),
            bg=COL_SURFACE0,
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 10))

        text_col = tk.Frame(inner, bg=COL_SURFACE0)
        text_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_title = tk.Label(
            text_col, text="", font=(UI_FONT, 13, "bold"),
            bg=COL_SURFACE0, fg=COL_TEXT, anchor="w",
        )
        self.status_title.pack(fill=tk.X)

        self.status_subtitle = tk.Label(
            text_col, text="", font=(UI_FONT, 9),
            bg=COL_SURFACE0, fg=COL_SUBTEXT, anchor="w",
        )
        self.status_subtitle.pack(fill=tk.X)

        self.verification_label = tk.Label(
            text_col, text="", font=(UI_FONT, 8, "italic"),
            bg=COL_SURFACE0, fg=COL_SUBTEXT, anchor="w",
        )
        self.verification_label.pack(fill=tk.X, pady=(2, 0))

    # -----------------------------------------------------------------
    # Botón toggle principal / Main toggle button
    # -----------------------------------------------------------------
    def _build_toggle_button(self):
        btn_frame = tk.Frame(self.tab_blocker, bg=COL_BASE)
        btn_frame.pack(fill=tk.X, padx=24, pady=(16, 0))

        self.toggle_btn = tk.Button(
            btn_frame, text="",
            font=(UI_FONT, 15, "bold"),
            bd=0, cursor="hand2",
            activeforeground="#FFFFFF",
            relief="flat", height=2,
            command=self._handle_toggle,
        )
        self.toggle_btn.pack(fill=tk.X, ipady=6)

    # -----------------------------------------------------------------
    # Panel informativo — categorías y conteo de dominios / Info panel — categories and domain count
    # -----------------------------------------------------------------
    def _build_info_panel(self):
        self.info_panel = tk.Frame(
            self.tab_blocker, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        self.info_panel.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 0))

        # Título del panel de categorías / Title of the categories panel
        self.title_bar = tk.Frame(self.info_panel, bg=COL_SURFACE0)
        self.title_bar.pack(fill=tk.X, padx=14, pady=(10, 4))

        self.categories_title_label = tk.Label(
            self.title_bar, text="",
            font=(UI_FONT, 10, "bold"),
            bg=COL_SURFACE0, fg=COL_TEXT, anchor="w",
        )
        self.categories_title_label.pack(side=tk.LEFT)

        # Botón "+" de dominios personalizados / "+" button for custom domains
        self.add_custom_btn = tk.Button(
            self.title_bar, text="＋",
            font=(UI_FONT, 9, "bold"),
            bg=COL_SURFACE0, fg=COL_BLUE,
            activebackground=COL_SURFACE1, activeforeground="#FFFFFF",
            bd=0, cursor="hand2",
            padx=4, pady=0,
            command=self._on_add_custom_domain
        )
        self.add_custom_btn.pack(side=tk.LEFT, padx=(8, 0))

        self.categories_total_domains_label = tk.Label(
            self.title_bar, text="",
            font=(UI_FONT, 9),
            bg=COL_SURFACE0, fg=COL_MAUVE, anchor="e",
        )
        self.categories_total_domains_label.pack(side=tk.RIGHT)

        # Separador sutil / Subtle separator
        tk.Frame(self.info_panel, bg=COL_SURFACE1, height=1).pack(fill=tk.X, padx=14)

        # Lista de categorías / Categories list
        self.list_frame = tk.Frame(self.info_panel, bg=COL_SURFACE0)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 10))

        # Emojis temáticos / Thematic emojis
        self.category_icons = {
            "OpenAI": "🟢", "Anthropic": "🟠", "GitHub Copilot": "🐙",
            "Google AI": "🔵", "Meta AI": "🔷", "Mistral AI": "🌊",
            "Microsoft Copilot": "🟦", "DeepSeek": "🔮", "xAI": "🤖", "Otros": "📦",
        }

        # Dibujar la lista inicial / Draw the initial list
        self._populate_category_list()

    def _populate_category_list(self):
        # Limpiar lista anterior / Clear previous list
        for child in self.list_frame.winfo_children():
            child.destroy()

        self.category_checkboxes = {}

        for cat, domains in BLOCKLIST.items():
            # Asegurar que existe una variable para esta categoría / Ensure variable exists for this category
            if cat not in self.category_vars:
                self.category_vars[cat] = tk.BooleanVar(value=True)

            row = tk.Frame(self.list_frame, bg=COL_SURFACE0)
            row.pack(fill=tk.X, pady=1)

            icon = self.category_icons.get(cat, "📦") # fallback to box for custom
            chk = tk.Checkbutton(
                row,
                text=f"  {icon}  {cat}",
                variable=self.category_vars[cat],
                onvalue=True,
                offvalue=False,
                command=self._on_category_toggled,
                font=(UI_FONT, 9),
                bg=COL_SURFACE0,
                fg=COL_TEXT,
                selectcolor=COL_SURFACE0,
                activebackground=COL_SURFACE0,
                activeforeground=COL_TEXT,
                bd=0,
                relief="flat",
                highlightthickness=0,
                anchor="w"
            )
            chk.pack(side=tk.LEFT, fill=tk.X, expand=True)
            self.category_checkboxes[cat] = chk

            tk.Label(
                row, text=f"{len(domains)}",
                font=(UI_FONT, 9, "bold"), bg=COL_SURFACE0,
                fg=COL_BLUE, anchor="e",
            ).pack(side=tk.RIGHT, padx=(0, 4))
            
        # Traducir nombres al idioma actual / Translate names to current language
        translations = CATEGORY_TRANSLATIONS.get(self.current_lang, CATEGORY_TRANSLATIONS["en"])
        for cat, chk in self.category_checkboxes.items():
            translated_name = translations.get(cat, cat)
            icon = self.category_icons.get(cat, "📦")
            chk.configure(text=f"  {icon}  {translated_name}")

    def _save_current_config(self):
        checked = {cat: var.get() for cat, var in self.category_vars.items()}
        self.config["language"] = self.current_lang
        self.config["profile"] = self.selected_profile_key
        self.config["checked_categories"] = checked
        save_config(self.config)

    def _on_add_custom_domain(self):
        # Open a small dialog
        dialog = tk.Toplevel(self.root)
        dialog.title(STRINGS[self.current_lang].get("add_custom_title", "Add Custom Domain"))
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.configure(bg=COL_BASE)
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

        # Input labels and entries
        s = STRINGS[self.current_lang]
        
        lbl_domain = tk.Label(dialog, text=s.get("add_domain_label", "Domain (e.g. example.com):"), bg=COL_BASE, fg=COL_TEXT, font=(UI_FONT, 9))
        lbl_domain.pack(anchor="w", padx=20, pady=(20, 0))
        
        entry_domain = tk.Entry(dialog, bg=COL_SURFACE0, fg=COL_TEXT, insertbackground=COL_TEXT, bd=1, relief="flat", font=(UI_FONT, 9))
        entry_domain.pack(fill=tk.X, padx=20, pady=(4, 0))
        entry_domain.focus_set()

        lbl_cat = tk.Label(dialog, text=s.get("add_cat_label", "Category:"), bg=COL_BASE, fg=COL_TEXT, font=(UI_FONT, 9))
        lbl_cat.pack(anchor="w", padx=20, pady=(10, 0))
        
        entry_cat = tk.Entry(dialog, bg=COL_SURFACE0, fg=COL_TEXT, insertbackground=COL_TEXT, bd=1, relief="flat", font=(UI_FONT, 9))
        entry_cat.pack(fill=tk.X, padx=20, pady=(4, 0))
        entry_cat.insert(0, s.get("profile_custom", "Custom"))

        def save():
            domain = entry_domain.get().strip().lower()
            cat = entry_cat.get().strip()
            
            if not domain:
                return
                
            # Basic domain validation
            if "." not in domain or len(domain) < 4:
                self.show_toast(s.get("unexpected_error_title", "Error"), s.get("invalid_domain_msg", "Please enter a valid domain."), "error")
                return
                
            self._add_custom_domain_to_list(domain, cat)
            self.log_action("log_custom_domain", domain=domain)
            dialog.destroy()

        btn_save = tk.Button(
            dialog, text=s.get("btn_save", "Save"),
            bg=COL_BLUE, fg="#000000", activebackground="#6aa1f7",
            font=(UI_FONT, 9, "bold"), bd=0, cursor="hand2",
            command=save, height=1
        )
        btn_save.pack(side=tk.RIGHT, padx=20, pady=20)

    def _add_custom_domain_to_list(self, domain, cat):
        if not cat:
            cat = "Otros"
            
        # Ensure category is in BLOCKLIST
        if cat not in BLOCKLIST:
            BLOCKLIST[cat] = []
        if domain not in BLOCKLIST[cat]:
            BLOCKLIST[cat].append(domain)
            
        # Update config
        custom_domains = self.config.get("custom_domains", {})
        if cat not in custom_domains:
            custom_domains[cat] = []
        if domain not in custom_domains[cat]:
            custom_domains[cat].append(domain)
            
        self.config["custom_domains"] = custom_domains
        self._save_current_config()
        
        # Repopulate UI list
        self._populate_category_list()
        
        # Update domain count labels
        s = STRINGS[self.current_lang]
        total_domains = count_total_domains()
        self.categories_total_domains_label.configure(
            text=s["domains_label"].format(total=total_domains)
        )
        
        # Re-apply block if active
        if self.is_blocked:
            self._handle_reapply_block()
        else:
            self._update_visuals()

    def hide_window(self):
        self.root.withdraw()

    def show_window(self):
        self.root.deiconify()
        self.root.state("normal")
        self.root.focus_force()

    def exit_app(self):
        if CURRENT_OS == "Windows" and hasattr(self, 'tray_icon'):
            self.tray_icon.remove()
        self.root.destroy()
        sys.exit(0)

    def _on_window_unmap(self, event=None):
        if event and event.widget == self.root:
            self.root.after(10, self.root.withdraw)

    def show_tray_menu(self):
        if not hasattr(self, 'tray_menu'):
            self.tray_menu = tk.Menu(
                self.root, tearoff=0,
                bg=COL_SURFACE0, fg=COL_TEXT,
                activebackground=COL_BLUE, activeforeground="#000000",
                font=(UI_FONT, 9)
            )
            
        self.tray_menu.delete(0, tk.END)
        s = STRINGS[self.current_lang]
        
        toggle_text = s["btn_unblock"] if self.is_blocked else s["btn_block"]
        self.tray_menu.add_command(label=toggle_text, command=self._handle_toggle)
        self.tray_menu.add_separator()
        self.tray_menu.add_command(label=s.get("menu_show", "Show App"), command=self.show_window)
        self.tray_menu.add_command(label=s.get("menu_exit", "Exit"), command=self.exit_app)
        
        x, y = self.root.winfo_pointerxy()
        self.tray_menu.post(x, y)

    # -----------------------------------------------------------------
    # Footer — créditos y aviso de editores detectados / Footer — credits and warning of detected editors
    # -----------------------------------------------------------------
    def _build_footer(self):
        footer = tk.Frame(self.tab_blocker, bg=COL_BASE)
        footer.pack(fill=tk.X, padx=24, pady=(8, 12))

        self.footer_label = tk.Label(
            footer,
            text="Open Source · github.com/Akunimal/AI-Blocker",
            font=(UI_FONT, 8),
            bg=COL_BASE, fg=COL_SUBTEXT,
        )
        self.footer_label.pack(side=tk.LEFT)

        # Checkbox de auto-inicio (solo Windows) / Autostart checkbox (Windows only)
        if CURRENT_OS == "Windows":
            self.autostart_var = tk.BooleanVar(value=get_windows_autostart())
            self.autostart_chk = tk.Checkbutton(
                footer,
                text="", # Will be set in _update_language_ui
                variable=self.autostart_var,
                onvalue=True,
                offvalue=False,
                command=self._on_autostart_toggled,
                font=(UI_FONT, 8),
                bg=COL_BASE,
                fg=COL_SUBTEXT,
                selectcolor=COL_BASE,
                activebackground=COL_BASE,
                activeforeground=COL_SUBTEXT,
                bd=0,
                relief="flat",
                highlightthickness=0
            )
            self.autostart_chk.pack(side=tk.LEFT, padx=(16, 0))

        # Aviso en tiempo real de editores de IA activos / Real-time warning of active AI editors
        self.editors_label = tk.Label(
            footer, text="",
            font=(UI_FONT, 8),
            bg=COL_BASE, fg=COL_YELLOW,
        )
        self.editors_label.pack(side=tk.RIGHT)
        self._refresh_editors_label()

    # -----------------------------------------------------------------
    # DevSec Gateway & Auditor UI
    # -----------------------------------------------------------------
    def _build_gateway_tab(self):
        container = tk.Frame(self.tab_gateway, bg=COL_BASE)
        container.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)
        
        # Section 1: AI API Router
        router_frame = tk.Frame(container, bg=COL_SURFACE0, highlightbackground=COL_SURFACE1, highlightthickness=1)
        router_frame.pack(fill=tk.X, pady=(0, 16))
        
        tk.Label(router_frame, text="⚡ Local AI Router", font=(UI_FONT, 11, "bold"), bg=COL_SURFACE0, fg=COL_TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(router_frame, text="Point your IDE to http://127.0.0.1:8080 to bypass cloud AI.", font=(UI_FONT, 9), bg=COL_SURFACE0, fg=COL_SUBTEXT).pack(anchor="w", padx=16)
        
        url_frame = tk.Frame(router_frame, bg=COL_SURFACE0)
        url_frame.pack(fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(url_frame, text="Target URL:", bg=COL_SURFACE0, fg=COL_TEXT).pack(side=tk.LEFT)
        self.target_url_var = tk.StringVar(value=self.config.get("target_url", "http://localhost:11434"))
        tk.Entry(url_frame, textvariable=self.target_url_var, bg=COL_BASE, fg=COL_TEXT, insertbackground=COL_TEXT, relief="flat").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        
        self.gateway_btn = tk.Button(router_frame, text="▶ Start Gateway", font=(UI_FONT, 10, "bold"), bg=COL_GREEN, fg="#000000", bd=0, command=self._toggle_gateway)
        self.gateway_btn.pack(fill=tk.X, padx=16, pady=12)
        
        # Section 2: Auditor
        audit_frame = tk.Frame(container, bg=COL_SURFACE0, highlightbackground=COL_SURFACE1, highlightthickness=1)
        audit_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(audit_frame, text="🛡️ DevSec Auditor", font=(UI_FONT, 11, "bold"), bg=COL_SURFACE0, fg=COL_TEXT).pack(anchor="w", padx=16, pady=(12, 4))
        tk.Label(audit_frame, text="Analyze running processes using OpenAI API for security recommendations.", font=(UI_FONT, 9), bg=COL_SURFACE0, fg=COL_SUBTEXT).pack(anchor="w", padx=16)
        
        key_frame = tk.Frame(audit_frame, bg=COL_SURFACE0)
        key_frame.pack(fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(key_frame, text="OpenAI API Key (not saved):", bg=COL_SURFACE0, fg=COL_TEXT).pack(side=tk.LEFT)
        self.openai_key_var = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        tk.Entry(key_frame, textvariable=self.openai_key_var, show="*", bg=COL_BASE, fg=COL_TEXT, insertbackground=COL_TEXT, relief="flat").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)
        
        self.audit_btn = tk.Button(audit_frame, text="Run Security Audit", font=(UI_FONT, 10, "bold"), bg=COL_BLUE, fg="#000000", bd=0, command=self._run_audit)
        self.audit_btn.pack(fill=tk.X, padx=16, pady=12)
        
        self.audit_result = tk.Text(audit_frame, height=8, bg=COL_BASE, fg=COL_TEXT, font=(UI_FONT, 9), relief="flat", wrap=tk.WORD)
        self.audit_result.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 16))
        self.audit_result.insert(tk.END, "Awaiting audit...")
        self.audit_result.configure(state="disabled")

    def _toggle_gateway(self):
        if not self.gateway_running:
            target = self.target_url_var.get().strip()
            self.config["target_url"] = target
            self._save_current_config()
            try:
                self.gateway_server = ThreadingHTTPServer(('127.0.0.1', 8080), GatewayHandler)
                self.gateway_server.target_url = target
                threading.Thread(target=self.gateway_server.serve_forever, daemon=True).start()
                self.gateway_running = True
                self.gateway_btn.configure(text="■ Stop Gateway", bg=COL_RED)
                self.log_action("log_gateway_started", url=target)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start gateway: {e}")
        else:
            if self.gateway_server:
                self.gateway_server.shutdown()
                self.gateway_server.server_close()
            self.gateway_running = False
            self.gateway_btn.configure(text="▶ Start Gateway", bg=COL_GREEN)
            self.log_action("log_gateway_stopped")

    def _run_audit(self):
        api_key = self.openai_key_var.get().strip()
        if not api_key:
            messagebox.showerror("Error", "Please enter an OpenAI API Key.")
            return
            
        self._save_current_config()
        
        self.audit_btn.configure(state="disabled", text="Auditing...")
        self.audit_result.configure(state="normal")
        self.audit_result.delete("1.0", tk.END)
        self.audit_result.insert(tk.END, "Gathering active processes and network info...\n")
        self.audit_result.configure(state="disabled")
        
        def task():
            running = detect_running_ai_editors()
            running_str = ", ".join(running) if running else "No active AI editors detected."
            is_blocked, count = get_hosts_status()
            
            prompt = (
                f"You are a DevSecOps AI Auditor. I am running a desktop tool called 'AI Blocker'.\n"
                f"Current state: Block Active = {is_blocked} ({count} domains blocked).\n"
                f"Active AI processes detected: {running_str}\n\n"
                f"Please write a short (max 4 sentences) security analysis of my current development environment. "
                f"Warn me about potential data leaks if my block is off and editors are running, or commend my setup. "
                f"Keep it professional and actionable."
            )
            
            req_data = json.dumps({"model": "gpt-4o-mini", "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
            req = urllib.request.Request(
                "https://api.openai.com/v1/chat/completions", data=req_data, method="POST",
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
            )
            
            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_data = json.loads(response.read().decode("utf-8"))
                    result_text = res_data["choices"][0]["message"]["content"]
            except Exception as e:
                result_text = f"Error during audit: {e}"
                
            def update_ui():
                self.audit_result.configure(state="normal")
                self.audit_result.delete("1.0", tk.END)
                self.audit_result.insert(tk.END, result_text)
                self.audit_result.configure(state="disabled")
                self.audit_btn.configure(state="normal", text="Run Security Audit")
                
            self.root.after(0, update_ui)
            
        threading.Thread(target=task, daemon=True).start()

    # -----------------------------------------------------------------
    # Panel Log
    # -----------------------------------------------------------------
    def _on_language_selected(self, event):
        """
        Manejador al cambiar idioma en el desplegable combobox.
        Event handler when changing the language in the dropdown combobox.
        """
        selected_display = self.lang_combo.get()
        selected_code = LANG_DISPLAY_MAP.get(selected_display, "en")
        
        if selected_code != self.current_lang:
            self.current_lang = selected_code
            self._update_language_ui()
            self._save_current_config()

    def _update_language_ui(self):
        """
        Actualiza todas las etiquetas de la GUI al idioma actual.
        Updates all GUI labels to the current language.
        """
        s = STRINGS[self.current_lang]
        
        # 1. Título de la aplicación en la cabecera / 1. Application title in the header
        self.title_label.configure(text="🛡️  AI Network Blocker")
        
        # 2. Título de la ventana / 2. Window title
        self.root.title(f"AI Network Blocker v{APP_VERSION}")

        # 3. Traducir y poblar perfiles / Translate and populate profiles
        try:
            old_index = self.profile_combo.current()
            keys = ["work", "personal", "free", "custom"]
            if 0 <= old_index < len(keys):
                selected_key = keys[old_index]
            else:
                selected_key = "work"
        except Exception:
            selected_key = "work"

        profile_names = [s["profile_work"], s["profile_personal"], s["profile_free"], s["profile_custom"]]
        self.profile_combo['values'] = profile_names
        self.profile_combo.set(s[f"profile_{selected_key}"])

        # 4. Categorías e Información / 4. Categories and Info
        self.categories_title_label.configure(text=s["categories_title"])
        total_domains = count_total_domains()
        self.categories_total_domains_label.configure(
            text=s["domains_label"].format(total=total_domains)
        )

        # 5. Traducir los nombres de categorías en el listado / 5. Translate category names in the list
        translations = CATEGORY_TRANSLATIONS.get(self.current_lang, CATEGORY_TRANSLATIONS["en"])
        for cat, chk in self.category_checkboxes.items():
            translated_name = translations.get(cat, cat)
            icon = self.category_icons.get(cat, "•")
            chk.configure(text=f"  {icon}  {translated_name}")

        # 6. Estado y Botón (usando la lógica de visuals existente) / 6. Status and Button (using existing visuals logic)
        self._update_visuals()

        # 7. Traducir checkbox de auto-inicio / Translate autostart checkbox
        if CURRENT_OS == "Windows" and hasattr(self, 'autostart_chk'):
            self.autostart_chk.configure(text=s.get("autostart_label", "Start with Windows"))

        # 8. Traducir cabecera del historial / Translate log header
        if hasattr(self, 'log_toggle_btn'):
            arrow = "▼" if self.log_expanded else "▶"
            self.log_toggle_btn.configure(text=f"{arrow}  {s.get('log_title', 'Activity Log')}")
            self._update_log_display()

    # -----------------------------------------------------------------
    # Lógica de Interacción y Estados / Interaction and States Logic
    # -----------------------------------------------------------------
    def _get_active_categories(self):
        return [cat for cat, var in self.category_vars.items() if var.get()]

    def _on_profile_selected(self, event=None):
        selected_display = self.profile_combo.get()
        s = STRINGS[self.current_lang]
        profile_key = None
        for key in ["work", "personal", "free", "custom"]:
            if s.get(f"profile_{key}", "") == selected_display:
                profile_key = key
                break
        
        if not profile_key or profile_key == "custom":
            return
            
        self.selected_profile_key = profile_key

        # Update category variables
        if profile_key == "work":
            for cat in self.category_vars:
                self.category_vars[cat].set(True)
        elif profile_key == "personal":
            for cat in self.category_vars:
                is_copilot = "copilot" in cat.lower()
                self.category_vars[cat].set(is_copilot)
        elif profile_key == "free":
            for cat in self.category_vars:
                self.category_vars[cat].set(False)
                
        # Save current preferences
        self._save_current_config()
        self.log_action("log_profile", profile=s[f"profile_{profile_key}"])

        # Apply the changes
        if self.is_blocked:
            self._handle_reapply_block()
        else:
            self._update_visuals()

    def _on_category_toggled(self):
        # Determine if the current selection matches one of the profiles
        active_cats = self._get_active_categories()
        all_cats = list(self.category_vars.keys())
        copilot_cats = [c for c in all_cats if "copilot" in c.lower()]
        
        s = STRINGS[self.current_lang]
        if len(active_cats) == len(all_cats):
            self.selected_profile_key = "work"
        elif len(active_cats) == 0:
            self.selected_profile_key = "free"
        elif sorted(active_cats) == sorted(copilot_cats):
            self.selected_profile_key = "personal"
        else:
            self.selected_profile_key = "custom"
            
        self.profile_combo.set(s[f"profile_{self.selected_profile_key}"])
        
        # Save current preferences
        self._save_current_config()
        self.log_action("log_profile", profile=s[f"profile_{self.selected_profile_key}"])

        if self.is_blocked:
            self._handle_reapply_block()
        else:
            self._update_visuals()

    def _on_autostart_toggled(self):
        if CURRENT_OS == "Windows":
            enabled = self.autostart_var.get()
            set_windows_autostart(enabled)

    def _handle_reapply_block(self):
        if self.is_busy:
            return
        self.is_busy = True
        s = STRINGS[self.current_lang]
        self.toggle_btn.configure(state="disabled", text=s["busy_text"])

        def task():
            active_cats = self._get_active_categories()
            if not active_cats:
                ok, msg = deactivate_block(self.current_lang)
            else:
                ok, msg = activate_block(self.current_lang, active_cats)
            
            if ok:
                self.is_blocked = bool(active_cats)
            self.root.after(0, lambda: self._on_reapply_done(ok, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_reapply_done(self, ok, msg):
        self.is_busy = False
        self.toggle_btn.configure(state="normal")
        
        if ok:
            import time
            self.last_toggle_time = time.time()
            self.config["last_toggle_time"] = self.last_toggle_time
            self._save_current_config()
            
        self._update_visuals()
        self._refresh_editors_label()
        self._run_connectivity_check()
        if not ok:
            s = STRINGS[self.current_lang]
            title = s["hosts_write_error_title"] if "hosts" in msg else s["unexpected_error_title"]
            self.show_toast(title, msg, "error")
            self.log_action("log_error", error=msg)
        else:
            actual_blocked, blocked_count = get_hosts_status()
            if actual_blocked:
                self.log_action("log_blocked", count=blocked_count)
            else:
                self.log_action("log_unblocked")

    def _handle_toggle(self):
        """
        Ejecuta la acción de bloqueo/desbloqueo en un hilo independiente.
        Executes the block/unblock action in an independent thread.
        """
        if self.is_busy:
            return
        self.is_busy = True
        
        s = STRINGS[self.current_lang]
        self.toggle_btn.configure(state="disabled", text=s["busy_text"])

        def task():
            if self.is_blocked:
                ok, msg = deactivate_block(self.current_lang)
                if ok:
                    self.is_blocked = False
            else:
                active_cats = self._get_active_categories()
                # If nothing is selected, check them all to avoid empty block
                if not active_cats:
                    for cat in self.category_vars:
                        self.category_vars[cat].set(True)
                    active_cats = list(self.category_vars.keys())
                ok, msg = activate_block(self.current_lang, active_cats)
                if ok:
                    self.is_blocked = True

            self.root.after(0, lambda: self._on_task_done(ok, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_task_done(self, ok, msg):
        """
        Callback al terminar la acción en segundo plano.
        Callback when the background action completes.
        """
        self.is_busy = False
        self.toggle_btn.configure(state="normal")
        
        if ok:
            import time
            self.last_toggle_time = time.time()
            self.config["last_toggle_time"] = self.last_toggle_time
            self._save_current_config()
            
        self._update_visuals()
        self._refresh_editors_label()
        self._run_connectivity_check()

        s = STRINGS[self.current_lang]
        if ok:
            title = s["block_success_title"] if self.is_blocked else s["unblock_success_title"]
            self.show_toast(title, msg, "success")
            actual_blocked, blocked_count = get_hosts_status()
            if actual_blocked:
                self.log_action("log_blocked", count=blocked_count)
            else:
                self.log_action("log_unblocked")
        else:
            title = s["hosts_write_error_title"] if "hosts" in msg else s["unexpected_error_title"]
            self.show_toast(title, msg, "error")
            self.log_action("log_error", error=msg)

    def _run_connectivity_check(self):
        def task():
            s = STRINGS[self.current_lang]
            self.root.after(0, lambda: self.verification_label.configure(text=s.get("verifying_text", "⚡ Verifying connectivity..."), fg=COL_SUBTEXT))
            
            import socket
            domain_to_check = "api.openai.com"
            try:
                ip = socket.gethostbyname(domain_to_check)
                if ip in ("127.0.0.1", "0.0.0.0"):
                    status_text = s.get("verify_blocked", "🛡️ Active check: api.openai.com is blocked")
                    color = COL_GREEN
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.2)
                    try:
                        sock.connect((domain_to_check, 443))
                        sock.close()
                        status_text = s.get("verify_exposed", "⚠️ Active check: api.openai.com is accessible!")
                        color = COL_RED
                    except socket.timeout:
                        status_text = s.get("verify_blocked", "🛡️ Active check: api.openai.com is blocked")
                        color = COL_GREEN
                    except Exception:
                        try:
                            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            test_sock.settimeout(1.0)
                            test_sock.connect(("1.1.1.1", 53))
                            test_sock.close()
                            status_text = s.get("verify_blocked", "🛡️ Active check: api.openai.com is blocked")
                            color = COL_GREEN
                        except Exception:
                            status_text = s.get("verify_no_internet", "🔌 Active check: No internet connection")
                            color = COL_YELLOW
            except Exception:
                try:
                    test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    test_sock.settimeout(1.0)
                    test_sock.connect(("1.1.1.1", 53))
                    test_sock.close()
                    status_text = s.get("verify_blocked", "🛡️ Active check: api.openai.com is blocked")
                    color = COL_GREEN
                except Exception:
                    status_text = s.get("verify_no_internet", "🔌 Active check: No internet connection")
                    color = COL_YELLOW

            def update_ui():
                if hasattr(self, 'verification_label') and self.verification_label.winfo_exists():
                    self.verification_label.configure(text=status_text, fg=color)
            
            self.root.after(0, update_ui)

        threading.Thread(target=task, daemon=True).start()

    def _schedule_connectivity_check(self):
        self._run_connectivity_check()
        self._conn_check_id = self.root.after(10000, self._schedule_connectivity_check)

    def log_action(self, event_key, **kwargs):

        import datetime
        now = datetime.datetime.now().strftime("%H:%M:%S")
        s = STRINGS[self.current_lang]
        template = s.get(event_key, event_key)
        try:
            formatted_message = template.format(**kwargs)
        except Exception:
            formatted_message = template
        log_entry = f"{now} — {formatted_message}"
        
        self.logs.append(log_entry)
        if len(self.logs) > 50:
            self.logs = self.logs[-50:]
            
        self.config["logs"] = self.logs
        self._save_current_config()
        self._update_log_display()

    def _update_log_display(self):
        if not hasattr(self, 'log_text') or not self.log_text.winfo_exists():
            return
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        for log in self.logs:
            self.log_text.insert(tk.END, log + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _copy_log(self):
        if self.logs:
            self.root.clipboard_clear()
            self.root.clipboard_append("\n".join(self.logs))
            s = STRINGS[self.current_lang]
            title = s.get("log_copied_title", "Copied")
            msg = s.get("log_copied_msg", "Activity log copied to clipboard.")
            self.show_toast(title, msg, "info")

    def _toggle_log_panel(self):
        s = STRINGS[self.current_lang]
        title = s.get("log_title", "Activity Log")
        
        try:
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            x = self.root.winfo_x()
            y = self.root.winfo_y()
        except Exception:
            w, h, x, y = 520, 650, 100, 100

        if self.log_expanded:
            self.log_box_frame.pack_forget()
            self.log_toggle_btn.configure(text=f"▶  {title}")
            self.log_expanded = False
            try:
                new_h = max(600, h - 120)
                self.root.geometry(f"{w}x{new_h}+{x}+{y}")
            except Exception:
                pass
        else:
            self.log_box_frame.pack(fill=tk.X, pady=(6, 0))
            self.log_toggle_btn.configure(text=f"▼  {title}")
            self.log_expanded = True
            self._update_log_display()
            try:
                new_h = h + 120
                self.root.geometry(f"{w}x{new_h}+{x}+{y}")
            except Exception:
                pass

    def _build_log_panel(self):
        s = STRINGS[self.current_lang]
        title = s.get("log_title", "Activity Log")

        self.log_container = tk.Frame(self.tab_blocker, bg=COL_BASE)
        self.log_container.pack(fill=tk.X, padx=24, pady=(12, 0))

        log_header = tk.Frame(self.log_container, bg=COL_BASE)
        log_header.pack(fill=tk.X)

        self.log_toggle_btn = tk.Button(
            log_header, text=f"▶  {title}",
            font=(UI_FONT, 9, "bold"),
            bg=COL_BASE, fg=COL_SUBTEXT,
            activebackground=COL_BASE, activeforeground=COL_TEXT,
            bd=0, cursor="hand2", anchor="w",
            command=self._toggle_log_panel
        )
        self.log_toggle_btn.pack(side=tk.LEFT)

        self.log_copy_btn = tk.Button(
            log_header, text="📋",
            font=(UI_FONT, 9),
            bg=COL_BASE, fg=COL_SUBTEXT,
            activebackground=COL_BASE, activeforeground=COL_TEXT,
            bd=0, cursor="hand2", anchor="e",
            command=self._copy_log
        )
        self.log_copy_btn.pack(side=tk.RIGHT)

        self.log_box_frame = tk.Frame(
            self.log_container, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1
        )

        self.log_text = tk.Text(
            self.log_box_frame, height=5,
            bg=COL_SURFACE0, fg=COL_TEXT,
            font=(UI_FONT, 8), relief="flat",
            state="disabled", wrap=tk.WORD
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(8, 0), pady=6)

        scrollbar = tk.Scrollbar(self.log_box_frame, command=self.log_text.yview, bg=COL_SURFACE0)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 4), pady=6)
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def show_toast(self, title, message, level="info"):

        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.configure(bg=COL_SURFACE0, highlightbackground=COL_SURFACE1, highlightthickness=1)
        
        # Prevent stealing focus on show
        try:
            toast.attributes("-topmost", True)
            toast.attributes("-alpha", 0.0)
        except Exception:
            pass

        # Determine level color
        if level == "success":
            accent_color = COL_GREEN
            icon = "✓"
        elif level == "error":
            accent_color = COL_RED
            icon = "✗"
        elif level == "warning":
            accent_color = COL_YELLOW
            icon = "⚠"
        else:
            accent_color = COL_BLUE
            icon = "ℹ"

        # Accent bar on the left
        bar = tk.Frame(toast, bg=accent_color, width=4)
        bar.pack(side=tk.LEFT, fill=tk.Y)

        # Content frame
        content = tk.Frame(toast, bg=COL_SURFACE0)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Header of toast (title + close button)
        header_frame = tk.Frame(content, bg=COL_SURFACE0)
        header_frame.pack(fill=tk.X)

        title_label = tk.Label(
            header_frame, text=f"{icon}  {title}",
            font=(UI_FONT, 10, "bold"),
            bg=COL_SURFACE0, fg=accent_color,
            anchor="w"
        )
        title_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        close_btn = tk.Label(
            header_frame, text="×", font=(UI_FONT, 14, "bold"),
            bg=COL_SURFACE0, fg=COL_SUBTEXT, cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT)

        # Message
        msg_label = tk.Label(
            content, text=message,
            font=(UI_FONT, 9),
            bg=COL_SURFACE0, fg=COL_TEXT,
            anchor="nw", justify=tk.LEFT,
            wraplength=290
        )
        msg_label.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        # Calculate height dynamically based on length of message
        lines = message.count("\n") + max(1, len(message) // 38)
        toast_height = max(80, 50 + lines * 16)
        toast.toast_height = toast_height

        # Bind close actions
        def on_close(e=None):
            self._close_toast(toast)

        close_btn.bind("<Button-1>", on_close)
        toast.bind("<Button-1>", on_close)
        content.bind("<Button-1>", on_close)
        title_label.bind("<Button-1>", on_close)
        msg_label.bind("<Button-1>", on_close)

        # Add to list and position
        self.active_toasts.append(toast)
        self._reposition_toasts()

        # Fade in
        self._fade_in(toast)

        # Schedule auto close
        self.root.after(4500, on_close)

    def _close_toast(self, toast):
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
            self._reposition_toasts()
        self._fade_out_and_destroy(toast)

    def _reposition_toasts(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        toast_width = 340
        margin_x = 20
        margin_y = 60 # above taskbar
        
        self.active_toasts = [t for t in self.active_toasts if t.winfo_exists()]
        
        current_y = screen_height - margin_y
        for toast in self.active_toasts:
            h = getattr(toast, "toast_height", 90)
            current_y -= (h + 10)
            x = screen_width - toast_width - margin_x
            try:
                toast.geometry(f"{toast_width}x{h}+{x}+{current_y}")
            except Exception:
                pass

    def _fade_in(self, toast, alpha=0.0):
        try:
            if not toast.winfo_exists():
                return
            if alpha < 0.95:
                alpha += 0.15
                toast.attributes("-alpha", alpha)
                self.root.after(15, lambda: self._fade_in(toast, alpha))
            else:
                toast.attributes("-alpha", 1.0)
        except Exception:
            try:
                toast.attributes("-alpha", 1.0)
            except Exception:
                pass

    def _fade_out_and_destroy(self, toast, alpha=1.0):
        try:
            if not toast.winfo_exists():
                return
            if alpha > 0.1:
                alpha -= 0.15
                toast.attributes("-alpha", alpha)
                self.root.after(15, lambda: self._fade_out_and_destroy(toast, alpha))
            else:
                toast.destroy()
        except Exception:
            try:
                toast.destroy()
            except Exception:
                pass

    def _interpolate_color(self, color1, color2, factor):
        c1 = color1.lstrip("#")
        c2 = color2.lstrip("#")
        r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
        r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
        r = int(r1 + (r2 - r1) * factor)
        g = int(g1 + (g2 - g1) * factor)
        b = int(b1 + (b2 - b1) * factor)
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return f"#{r:02X}{g:02X}{b:02X}"

    def _animation_tick(self, anim_id, src_hl, dst_hl, src_bg, dst_bg, src_fg, dst_fg, total_steps, current_step):
        if anim_id != self._anim_id:
            return
        if current_step > total_steps:
            self.card_frame.configure(highlightbackground=dst_hl)
            self.status_dot.configure(fg=dst_hl)
            self.toggle_btn.configure(bg=dst_bg, fg=dst_fg)
            return
            
        factor = current_step / total_steps
        curr_hl = self._interpolate_color(src_hl, dst_hl, factor)
        curr_bg = self._interpolate_color(src_bg, dst_bg, factor)
        curr_fg = self._interpolate_color(src_fg, dst_fg, factor)
        
        self.card_frame.configure(highlightbackground=curr_hl)
        self.status_dot.configure(fg=curr_hl)
        self.toggle_btn.configure(bg=curr_bg, fg=curr_fg)
        
        self.root.after(15, lambda: self._animation_tick(
            anim_id, src_hl, dst_hl, src_bg, dst_bg, src_fg, dst_fg, total_steps, current_step + 1
        ))

    def _update_visuals(self):
        """
        Actualiza colores y etiquetas según el estado de bloqueo.
        Updates colors and labels according to the block status.
        """
        s = STRINGS[self.current_lang]
        actual_blocked, blocked_count = get_hosts_status()
        self.is_blocked = actual_blocked  # Sincronizar estado real del archivo hosts

        import time
        time_str = ""
        if hasattr(self, 'last_toggle_time') and self.last_toggle_time:
            mins = int((time.time() - self.last_toggle_time) / 60)
            if mins > 0:
                time_str = f" ({mins}m)"
            else:
                time_str = " (now)"

        # Define targets
        if self.is_blocked:
            target_dot_fg = COL_GREEN
            target_title = s["protected_title"]
            target_subtitle = s["protected_desc"].format(count=blocked_count) + time_str
            target_btn_text = s["btn_unblock"]
            target_btn_bg = "#2D6A4F"
            target_btn_fg = "#A6E3A1"
            target_btn_activebg = "#1B4332"
            target_hl = COL_GREEN
        else:
            target_dot_fg = COL_RED
            target_title = s["exposed_title"]
            target_subtitle = s["exposed_desc"] + time_str
            target_btn_text = s["btn_block"]
            target_btn_bg = "#6B1E2B"
            target_btn_fg = "#F38BA8"
            target_btn_activebg = "#4C1220"
            target_hl = COL_RED

        # Configure texts
        self.status_title.configure(text=target_title)
        self.status_subtitle.configure(text=target_subtitle)
        self.toggle_btn.configure(text=target_btn_text, activebackground=target_btn_activebg)

        # Decide whether to animate color changes
        if self.last_visuals_blocked != self.is_blocked:
            # We are transitioning states, animate!
            self._anim_id += 1
            
            # Source colors are the opposite state
            if self.is_blocked:
                # Transitioning from EXPOSED to PROTECTED
                src_hl = COL_RED
                src_bg = "#6B1E2B"
                src_fg = "#F38BA8"
            else:
                # Transitioning from PROTECTED to EXPOSED
                src_hl = COL_GREEN
                src_bg = "#2D6A4F"
                src_fg = "#A6E3A1"

            self._animation_tick(
                self._anim_id,
                src_hl, target_hl,
                src_bg, target_btn_bg,
                src_fg, target_btn_fg,
                15, 0
            )
            self.last_visuals_blocked = self.is_blocked
        else:
            # No transition (startup, profile change within same state, or language change)
            self._anim_id += 1 # Cancel any active animation
            self.card_frame.configure(highlightbackground=target_hl)
            self.status_dot.configure(fg=target_dot_fg)
            self.toggle_btn.configure(bg=target_btn_bg, fg=target_btn_fg)

        # Update system tray icon if available
        if CURRENT_OS == "Windows" and hasattr(self, 'tray_icon'):
            self.tray_icon.update_icon()

    def _refresh_editors_label(self):
        """
        Efectúa escaneo rápido y recurrente en segundo plano de editores de IA.
        Performs a quick, recurring background scan of AI editors.
        """
        if getattr(self, '_scan_after_id', None):
            self.root.after_cancel(self._scan_after_id)
            self._scan_after_id = None

        def scan():
            running = detect_running_ai_editors()
            s = STRINGS[self.current_lang]
            if running:
                text = s["running_warning"].format(editors=", ".join(running))
            else:
                text = ""
            
            def update_ui():
                self.editors_label.configure(text=text)
                self._scan_after_id = self.root.after(3000, self._refresh_editors_label)
                
            self.root.after(0, update_ui)

        threading.Thread(target=scan, daemon=True).start()


# =====================================================================
# WIN32 SYSTEM TRAY INTERFACE
# =====================================================================
if CURRENT_OS == "Windows":
    import ctypes
    from ctypes import wintypes
    
    WM_USER = 1024
    WM_TRAYICON = WM_USER + 20
    NIM_ADD = 0
    NIM_MODIFY = 1
    NIM_DELETE = 2
    NIF_ICON = 2
    NIF_MESSAGE = 1
    NIF_TIP = 4
    WM_LBUTTONDBLCLK = 515
    WM_RBUTTONUP = 517
    WM_DESTROY = 2
    
    user32 = ctypes.windll.user32
    shell32 = ctypes.windll.shell32
    kernel32 = ctypes.windll.kernel32
    
    class WNDCLASSW(ctypes.Structure):
        _fields_ = [
            ("style", wintypes.UINT),
            ("lpfnWndProc", ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)),
            ("cbClsExtra", ctypes.c_int),
            ("cbWndExtra", ctypes.c_int),
            ("hInstance", wintypes.HINSTANCE),
            ("hIcon", wintypes.HICON),
            ("hCursor", wintypes.HANDLE),
            ("hbrBackground", wintypes.HBRUSH),
            ("lpszMenuName", wintypes.LPCWSTR),
            ("lpszClassName", wintypes.LPCWSTR),
        ]
        
    class NOTIFYICONDATAW(ctypes.Structure):
        _fields_ = [
            ("cbSize", wintypes.DWORD),
            ("hWnd", wintypes.HWND),
            ("uID", wintypes.UINT),
            ("uFlags", wintypes.UINT),
            ("uCallbackMessage", wintypes.UINT),
            ("hIcon", wintypes.HICON),
            ("szTip", ctypes.c_wchar * 128),
            ("dwState", wintypes.DWORD),
            ("dwStateMask", wintypes.DWORD),
            ("szInfo", ctypes.c_wchar * 256),
            ("uTimeout", wintypes.UINT),
            ("szInfoTitle", ctypes.c_wchar * 64),
            ("dwInfoFlags", wintypes.DWORD),
            ("guidItem", ctypes.c_byte * 16),
            ("hBalloonIcon", wintypes.HICON),
        ]

    class WindowsTrayIcon:
        def __init__(self, app):
            self.app = app
            self.hwnd = None
            self.tip = "AI Network Blocker"
            self._added = False
            
            # Start message loop in a daemon thread
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            
        def _run_loop(self):
            WndProcType = ctypes.WINFUNCTYPE(ctypes.c_int64, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)
            
            @WndProcType
            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_TRAYICON:
                    if lparam == WM_LBUTTONDBLCLK:
                        self.app.root.after(0, self.app.show_window)
                    elif lparam == WM_RBUTTONUP:
                        self.app.root.after(0, self.app.show_tray_menu)
                    return 0
                elif msg == WM_DESTROY:
                    user32.PostQuitMessage(0)
                    return 0
                return user32.DefWindowProcW(hwnd, msg, wparam, lparam)
                
            self.wnd_proc_ref = wnd_proc  # Keep reference
            
            hinstance = kernel32.GetModuleHandleW(None)
            class_name = "AIBlockerTrayClass"
            
            wndclass = WNDCLASSW()
            wndclass.style = 0
            wndclass.lpfnWndProc = wnd_proc
            wndclass.cbClsExtra = 0
            wndclass.cbWndExtra = 0
            wndclass.hInstance = hinstance
            wndclass.hIcon = 0
            wndclass.hCursor = 0
            wndclass.hbrBackground = 0
            wndclass.lpszMenuName = None
            wndclass.lpszClassName = class_name
            
            user32.RegisterClassW(ctypes.byref(wndclass))
            
            self.hwnd = user32.CreateWindowExW(
                0, class_name, "AI Blocker Tray Window",
                0, 0, 0, 0, 0,
                0, 0, hinstance, None
            )
            
            self.update_icon()
            
            msg = wintypes.MSG()
            while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
                
        def update_icon(self):
            if not self.hwnd:
                return
                
            # Try to load state-specific icon
            if self.app.is_blocked:
                icon_name = "icon_green.ico"
            else:
                icon_name = "icon_red.ico"
                
            icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), icon_name)
            if not os.path.exists(icon_path):
                # Fallback to standard icon.ico
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
                
            hicon = 0
            if os.path.exists(icon_path):
                hicon = user32.LoadImageW(
                    0, icon_path, 1, 0, 0, 16 | 80  # IMAGE_ICON, LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
                
            nid = NOTIFYICONDATAW()
            nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
            nid.hWnd = self.hwnd
            nid.uID = 1
            nid.uFlags = NIF_ICON | NIF_MESSAGE | NIF_TIP
            nid.uCallbackMessage = WM_TRAYICON
            nid.hIcon = hicon
            nid.szTip = self.tip
            
            if self._added:
                shell32.Shell_NotifyIconW(NIM_MODIFY, ctypes.byref(nid))
            else:
                shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
                self._added = True
                
        def remove(self):
            if self.hwnd and self._added:
                nid = NOTIFYICONDATAW()
                nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
                nid.hWnd = self.hwnd
                nid.uID = 1
                shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))
                self._added = False


# =====================================================================
# BLOQUEO DE INSTANCIA ÚNICA / SINGLE INSTANCE LOCK
# =====================================================================
def acquire_single_instance_lock():
    """
    Asegura que solo se ejecute una instancia de la aplicación a la vez.
    Ensures only one instance of the application runs at a time.
    """
    if CURRENT_OS == "Windows":
        mutex_name = "Global\\AIBlocker_SingleInstance_Mutex"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
        if ctypes.windll.kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            return False, None
        return True, mutex
    else:
        try:
            import fcntl
            lock_file = "/tmp/ai_blocker.lock"
            fp = open(lock_file, "w")
            fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return True, fp
        except (IOError, OSError, ImportError):
            return False, None


# =====================================================================
# PUNTO DE ENTRADA PRINCIPAL / MAIN ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    # Asegurar que solo hay una instancia abierta / Ensure only one instance is open
    ok, lock_ref = acquire_single_instance_lock()
    if not ok:
        print("AI Network Blocker is already running.")
        sys.exit(0)

    # Comprobar privilegios de administrador antes de lanzar la app
    # Check administrator privileges before launching the app
    if not is_admin():
        relaunch_as_admin()
        
        # En caso de que falle la auto-elevación UAC, se muestra el error traducido detectado
        # In case UAC auto-elevation fails, show the detected translated error
        detected_lang = detect_system_language()
        s = STRINGS[detected_lang]
        
        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showerror(
            s["admin_required_title"],
            s["admin_required_msg"]
        )
        root_temp.destroy()
        sys.exit(1)

    # Iniciar la aplicación / Start the application
    root = tk.Tk()
    app = AIBlockerApp(root)
    if "--minimized" in sys.argv and CURRENT_OS == "Windows":
        root.withdraw()
    root.mainloop()
