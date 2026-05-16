# -*- coding: utf-8 -*-
"""
AI Network Blocker — Kill switch para editores de código con IA.
Bloquea/desbloquea dominios de IA editando el archivo hosts de Windows.
Requiere privilegios de Administrador.
"""

import os
import sys
import ctypes
import subprocess
import tkinter as tk
from tkinter import messagebox
import time
import threading

# =====================================================================
# VERSIÓN
# =====================================================================
APP_VERSION = "2.0.0"

# =====================================================================
# CONFIGURACIÓN DE DOMINIOS A BLOQUEAR
# =====================================================================
# Diccionario de dominios organizado por proveedor de IA.
# Edita esta lista para añadir o quitar dominios según necesites.
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
    "Otros": [
        "api.perplexity.ai", "perplexity.ai",
        "app.wordware.ai",
    ],
}

# Lista de ejecutables de editores de IA a cerrar al activar el bloqueo.
PROCESS_LIST = [
    "Code.exe", "Cursor.exe", "Windsurf.exe", "Claude.exe",
    "Trae.exe", "Cline.exe", "Roo.exe", "Augment.exe",
]

# Marca de comentario que identifica las líneas añadidas por esta app.
COMMENT_TAG = "# AI-Block"

# Ruta del archivo hosts (se construye dinámicamente para portabilidad).
HOSTS_PATH = os.path.join(
    os.environ.get("SystemRoot", r"C:\Windows"),
    r"System32\drivers\etc\hosts",
)

# =====================================================================
# PALETA DE COLORES — Catppuccin Mocha (dark premium)
# =====================================================================
COL_BASE      = "#1E1E2E"   # Fondo principal
COL_SURFACE0  = "#313244"   # Panel secundario
COL_SURFACE1  = "#45475A"   # Bordes sutiles
COL_TEXT      = "#CDD6F4"   # Texto principal
COL_SUBTEXT   = "#A6ADC8"   # Texto secundario
COL_RED       = "#F38BA8"   # Rojo suave
COL_GREEN     = "#A6E3A1"   # Verde suave
COL_YELLOW    = "#F9E2AF"   # Amarillo
COL_BLUE      = "#89B4FA"   # Azul accent
COL_MAUVE     = "#CBA6F7"   # Púrpura accent

# =====================================================================
# UTILIDADES DE SISTEMA
# =====================================================================
def is_admin():
    """Retorna True si el proceso corre con privilegios de Administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def relaunch_as_admin():
    """
    Re-lanza el ejecutable actual solicitando elevación UAC.
    Funciona tanto desde .py como desde .exe empaquetado.
    """
    try:
        if getattr(sys, "frozen", False):
            # Si estamos corriendo como .exe empaquetado por PyInstaller
            executable = sys.executable
        else:
            # Si estamos corriendo como script .py
            executable = sys.executable  # python.exe
        
        # ShellExecuteW con "runas" muestra el diálogo UAC
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable,
            " ".join(f'"{a}"' for a in sys.argv),
            None, 1
        )
    except Exception:
        pass
    sys.exit(0)


def flush_dns():
    """
    Ejecuta ipconfig /flushdns para que los cambios en el hosts surtan
    efecto inmediato sin esperar al TTL de la caché DNS.
    """
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = subprocess.SW_HIDE
        subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True, startupinfo=si,
        )
    except Exception:
        pass


def count_total_domains():
    """Retorna el número total de dominios únicos en la BLOCKLIST."""
    seen = set()
    for domains in BLOCKLIST.values():
        seen.update(domains)
    return len(seen)


def check_block_status():
    """Lee el hosts y retorna True si encuentra al menos una línea con la marca AI-Block."""
    if not os.path.exists(HOSTS_PATH):
        return False
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if COMMENT_TAG in line:
                    return True
    except Exception:
        pass
    return False


def get_blocked_domains_count():
    """Retorna cuántos dominios marcados con AI-Block están activos en el hosts."""
    count = 0
    if not os.path.exists(HOSTS_PATH):
        return count
    try:
        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if COMMENT_TAG in line and line.strip() and not line.strip().startswith("#"):
                    count += 1
    except Exception:
        pass
    return count


# =====================================================================
# ACCIONES DE BLOQUEO / DESBLOQUEO
# =====================================================================
def force_close_processes():
    """
    Cierra de forma forzada los editores de IA en ejecución.
    Retorna una lista con los nombres de los procesos cerrados.
    """
    closed = []
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE

    for proc in PROCESS_LIST:
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", proc],
                capture_output=True, text=True, startupinfo=si,
            )
            if result.returncode == 0:
                closed.append(proc.replace(".exe", ""))
        except Exception:
            pass
    return closed


def detect_running_ai_editors():
    """
    Detecta qué editores de IA están en ejecución actualmente (sin cerrarlos).
    Retorna una lista de nombres.
    """
    running = []
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE

    for proc in PROCESS_LIST:
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {proc}", "/NH"],
                capture_output=True, text=True, startupinfo=si,
            )
            if proc.lower() in result.stdout.lower():
                running.append(proc.replace(".exe", ""))
        except Exception:
            pass
    return running


def activate_block():
    """
    1. Cierra procesos de editores de IA.
    2. Agrega al hosts los dominios de BLOCKLIST redirigiendo a 127.0.0.1.
    3. Limpia la caché DNS.
    Retorna (éxito: bool, mensaje: str).
    """
    # Paso 1: cerrar procesos
    closed_list = force_close_processes()

    # Paso 2: modificar archivo hosts
    try:
        existing_lines = []
        if os.path.exists(HOSTS_PATH):
            with open(HOSTS_PATH, "r", encoding="utf-8") as f:
                existing_lines = f.readlines()

        hosts_text = "".join(existing_lines)
        new_entries = []
        added_count = 0

        for category, domains in BLOCKLIST.items():
            for domain in domains:
                entry = f"127.0.0.1 {domain} {COMMENT_TAG}\n"
                if domain not in hosts_text:
                    new_entries.append(entry)
                    added_count += 1

        if new_entries:
            if existing_lines and not existing_lines[-1].endswith("\n"):
                existing_lines[-1] += "\n"
            with open(HOSTS_PATH, "w", encoding="utf-8") as f:
                f.writelines(existing_lines + new_entries)

        # Paso 3: limpiar caché DNS
        flush_dns()

        # Construir mensaje
        parts = [f"✓ {added_count} dominios bloqueados en el archivo hosts."]
        if closed_list:
            parts.append(f"✓ Procesos cerrados: {', '.join(closed_list)}")
        else:
            parts.append("• No se detectaron editores de IA abiertos.")
        parts.append("✓ Caché DNS limpiada.")

        return True, "\n".join(parts)

    except PermissionError:
        return False, "Error: no se pudo escribir en el archivo hosts.\nEjecuta como Administrador."
    except Exception as e:
        return False, f"Error inesperado:\n{e}"


def deactivate_block():
    """
    Elimina del hosts las líneas con la marca AI-Block.
    Retorna (éxito: bool, mensaje: str).
    """
    try:
        if not os.path.exists(HOSTS_PATH):
            return True, "El archivo hosts no existe. Bloqueo ya inactivo."

        with open(HOSTS_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()

        original_count = len(lines)
        cleaned = [l for l in lines if COMMENT_TAG not in l]
        removed = original_count - len(cleaned)

        with open(HOSTS_PATH, "w", encoding="utf-8") as f:
            f.writelines(cleaned)

        flush_dns()

        return True, f"✓ {removed} entradas eliminadas del hosts.\n✓ Caché DNS limpiada.\n\nTodos los servicios de IA vuelven a estar accesibles."

    except PermissionError:
        return False, "Error: no se pudo escribir en el archivo hosts.\nEjecuta como Administrador."
    except Exception as e:
        return False, f"Error inesperado:\n{e}"


# =====================================================================
# INTERFAZ GRÁFICA PREMIUM
# =====================================================================
class AIBlockerApp:
    """Ventana principal de AI Network Blocker con interfaz moderna."""

    def __init__(self, root):
        self.root = root
        self.root.title("AI Network Blocker")
        self.root.geometry("520x620")
        self.root.minsize(480, 580)
        self.root.configure(bg=COL_BASE)

        # Intentar poner el icono si existe
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        # Estado actual
        self.is_blocked = check_block_status()
        self.is_busy = False  # Previene doble-clic

        # Construir la interfaz
        self._build_header()
        self._build_status_card()
        self._build_toggle_button()
        self._build_info_panel()
        self._build_footer()

        # Actualizar visualización basada en el estado actual
        self._update_visuals()

    # -----------------------------------------------------------------
    # Header — Título y versión
    # -----------------------------------------------------------------
    def _build_header(self):
        header = tk.Frame(self.root, bg=COL_BASE)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))

        tk.Label(
            header, text="🛡️  AI Network Blocker",
            font=("Segoe UI", 18, "bold"),
            bg=COL_BASE, fg=COL_TEXT,
        ).pack(side=tk.LEFT)

        tk.Label(
            header, text=f"v{APP_VERSION}",
            font=("Segoe UI", 10),
            bg=COL_BASE, fg=COL_SUBTEXT,
        ).pack(side=tk.RIGHT, pady=(6, 0))

    # -----------------------------------------------------------------
    # Card de estado — indicador visual grande
    # -----------------------------------------------------------------
    def _build_status_card(self):
        self.card_frame = tk.Frame(
            self.root, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        self.card_frame.pack(fill=tk.X, padx=24, pady=(16, 0))

        inner = tk.Frame(self.card_frame, bg=COL_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=14)

        # Indicador circular simulado con texto
        self.status_dot = tk.Label(
            inner, text="●", font=("Segoe UI", 22),
            bg=COL_SURFACE0,
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 10))

        text_col = tk.Frame(inner, bg=COL_SURFACE0)
        text_col.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.status_title = tk.Label(
            text_col, text="", font=("Segoe UI", 13, "bold"),
            bg=COL_SURFACE0, fg=COL_TEXT, anchor="w",
        )
        self.status_title.pack(fill=tk.X)

        self.status_subtitle = tk.Label(
            text_col, text="", font=("Segoe UI", 9),
            bg=COL_SURFACE0, fg=COL_SUBTEXT, anchor="w",
        )
        self.status_subtitle.pack(fill=tk.X)

    # -----------------------------------------------------------------
    # Botón toggle principal
    # -----------------------------------------------------------------
    def _build_toggle_button(self):
        btn_frame = tk.Frame(self.root, bg=COL_BASE)
        btn_frame.pack(fill=tk.X, padx=24, pady=(16, 0))

        self.toggle_btn = tk.Button(
            btn_frame, text="",
            font=("Segoe UI", 15, "bold"),
            bd=0, cursor="hand2",
            activeforeground="#FFFFFF",
            relief="flat", height=2,
            command=self._handle_toggle,
        )
        self.toggle_btn.pack(fill=tk.X, ipady=6)

    # -----------------------------------------------------------------
    # Panel informativo — categorías y conteo de dominios
    # -----------------------------------------------------------------
    def _build_info_panel(self):
        panel = tk.Frame(
            self.root, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        panel.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 0))

        # Título del panel
        title_bar = tk.Frame(panel, bg=COL_SURFACE0)
        title_bar.pack(fill=tk.X, padx=14, pady=(10, 4))

        tk.Label(
            title_bar, text="Categorías bloqueadas",
            font=("Segoe UI", 10, "bold"),
            bg=COL_SURFACE0, fg=COL_TEXT, anchor="w",
        ).pack(side=tk.LEFT)

        total = count_total_domains()
        tk.Label(
            title_bar, text=f"{total} dominios",
            font=("Segoe UI", 9),
            bg=COL_SURFACE0, fg=COL_MAUVE, anchor="e",
        ).pack(side=tk.RIGHT)

        # Separador sutil
        tk.Frame(panel, bg=COL_SURFACE1, height=1).pack(fill=tk.X, padx=14)

        # Lista de categorías con conteo
        list_frame = tk.Frame(panel, bg=COL_SURFACE0)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 10))

        # Símbolos por categoría para darle personalidad
        category_icons = {
            "OpenAI": "🟢", "Anthropic": "🟠", "GitHub Copilot": "🐙",
            "Google AI": "🔵", "Meta AI": "🔷", "Mistral AI": "🌊",
            "Microsoft Copilot": "🟦", "DeepSeek": "🔮", "Otros": "📦",
        }

        for cat, domains in BLOCKLIST.items():
            row = tk.Frame(list_frame, bg=COL_SURFACE0)
            row.pack(fill=tk.X, pady=1)

            icon = category_icons.get(cat, "•")
            tk.Label(
                row, text=f"  {icon}  {cat}",
                font=("Segoe UI", 9), bg=COL_SURFACE0,
                fg=COL_TEXT, anchor="w",
            ).pack(side=tk.LEFT)

            tk.Label(
                row, text=f"{len(domains)}",
                font=("Segoe UI", 9, "bold"), bg=COL_SURFACE0,
                fg=COL_BLUE, anchor="e",
            ).pack(side=tk.RIGHT, padx=(0, 4))

    # -----------------------------------------------------------------
    # Footer — créditos y enlace
    # -----------------------------------------------------------------
    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COL_BASE)
        footer.pack(fill=tk.X, padx=24, pady=(8, 12))

        tk.Label(
            footer,
            text="Open Source · github.com/Akunimal/AI-Blocker",
            font=("Segoe UI", 8),
            bg=COL_BASE, fg=COL_SUBTEXT,
        ).pack(side=tk.LEFT)

        # Detección rápida de editores activos
        self.editors_label = tk.Label(
            footer, text="",
            font=("Segoe UI", 8),
            bg=COL_BASE, fg=COL_YELLOW,
        )
        self.editors_label.pack(side=tk.RIGHT)
        self._refresh_editors_label()

    # -----------------------------------------------------------------
    # Lógica de interacción
    # -----------------------------------------------------------------
    def _handle_toggle(self):
        """Toggle entre bloquear y desbloquear. Se ejecuta en un hilo para no congelar la GUI."""
        if self.is_busy:
            return
        self.is_busy = True
        self.toggle_btn.configure(state="disabled", text="⏳  Procesando…")

        def task():
            if self.is_blocked:
                ok, msg = deactivate_block()
                if ok:
                    self.is_blocked = False
            else:
                ok, msg = activate_block()
                if ok:
                    self.is_blocked = True

            # Volver al hilo principal de tkinter para actualizar la GUI
            self.root.after(0, lambda: self._on_task_done(ok, msg))

        threading.Thread(target=task, daemon=True).start()

    def _on_task_done(self, ok, msg):
        """Callback que se ejecuta en el hilo principal tras completar el bloqueo/desbloqueo."""
        self.is_busy = False
        self.toggle_btn.configure(state="normal")
        self._update_visuals()
        self._refresh_editors_label()

        if ok:
            messagebox.showinfo("AI Network Blocker", msg)
        else:
            messagebox.showerror("Error", msg)

    def _update_visuals(self):
        """Actualiza colores, textos e indicadores según el estado actual."""
        blocked_count = get_blocked_domains_count()

        if self.is_blocked:
            # BLOQUEADO — estado seguro
            self.status_dot.configure(fg=COL_GREEN)
            self.status_title.configure(text="PROTEGIDO — Bloqueo activo")
            self.status_subtitle.configure(
                text=f"{blocked_count} dominios redirigidos a 127.0.0.1"
            )
            self.toggle_btn.configure(
                text="🔓  DESBLOQUEAR IA",
                bg="#2D6A4F", fg="#A6E3A1",
                activebackground="#1B4332",
            )
            self.card_frame.configure(highlightbackground=COL_GREEN)
        else:
            # DESBLOQUEADO — expuesto
            self.status_dot.configure(fg=COL_RED)
            self.status_title.configure(text="EXPUESTO — Sin protección")
            self.status_subtitle.configure(
                text="Tu tráfico de red hacia IAs está abierto"
            )
            self.toggle_btn.configure(
                text="🔒  BLOQUEAR IA",
                bg="#6B1E2B", fg="#F38BA8",
                activebackground="#4C1220",
            )
            self.card_frame.configure(highlightbackground=COL_RED)

    def _refresh_editors_label(self):
        """Actualiza la etiqueta del footer mostrando editores de IA detectados."""
        def scan():
            running = detect_running_ai_editors()
            if running:
                text = f"⚠ Detectados: {', '.join(running)}"
            else:
                text = ""
            self.root.after(0, lambda: self.editors_label.configure(text=text))

        threading.Thread(target=scan, daemon=True).start()


# =====================================================================
# PUNTO DE ENTRADA PRINCIPAL
# =====================================================================
if __name__ == "__main__":
    # Si no somos admin, intentar re-lanzar con elevación UAC
    if not is_admin():
        relaunch_as_admin()
        # Si relaunch falla, mostramos error
        root_temp = tk.Tk()
        root_temp.withdraw()
        messagebox.showerror(
            "Acceso Denegado",
            "Se requieren privilegios de Administrador.\n\n"
            "Haz clic derecho → 'Ejecutar como administrador'.",
        )
        root_temp.destroy()
        sys.exit(1)

    # Iniciar la aplicación
    root = tk.Tk()
    app = AIBlockerApp(root)
    root.mainloop()
