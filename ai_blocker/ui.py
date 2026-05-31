# -*- coding: utf-8 -*-
import datetime
import json
import os
import socket
import sys
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from tkinter import messagebox, ttk

from ai_blocker.block_actions import activate_block, deactivate_block, detect_running_ai_editors
from ai_blocker.config import get_windows_autostart, load_config, save_config, set_windows_autostart
from ai_blocker.constants import (
    BLOCKLIST,
    CATEGORY_ICONS,
    COL_BASE,
    COL_BLUE,
    COL_GREEN,
    COL_MAUVE,
    COL_RED,
    COL_SUBTEXT,
    COL_SURFACE0,
    COL_SURFACE1,
    COL_TEXT,
    COL_YELLOW,
    CURRENT_OS,
    UI_FONT,
)
from ai_blocker.gateway import GatewayHandler
from ai_blocker.i18n import CATEGORY_TRANSLATIONS, LANG_CODE_MAP, LANG_DISPLAY_MAP, STRINGS, detect_system_language
from ai_blocker.system_utils import count_total_domains, get_hosts_status
from ai_blocker.tray import WindowsTrayIcon


class AIBlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI-Router-Blocker-AiO")
        self.root.geometry("520x650")
        self.root.minsize(480, 600)
        self.root.configure(bg=COL_BASE)

        # Try to load icon with package directory fallback
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icon.ico")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(base_dir), "icon.ico")

        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass

        self._setup_ttk_styles()
        self.config = load_config()

        self.current_lang = self.config.get("language", detect_system_language())
        if self.current_lang not in STRINGS:
            self.current_lang = "en"

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

        self.selected_profile_key = self.config.get("profile", "work")

        self.category_vars = {}
        self.category_checkboxes = {}
        checked_cats = self.config.get("checked_categories", {})
        for cat in BLOCKLIST:
            default_val = checked_cats.get(cat, True)
            self.category_vars[cat] = tk.BooleanVar(value=default_val)

        if CURRENT_OS == "Windows":
            self.root.protocol("WM_DELETE_WINDOW", self.hide_window)
            self.root.bind("<Unmap>", self._on_window_unmap)
            self.tray_icon = WindowsTrayIcon(self)
        else:
            self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.root.bind("<Control-b>", lambda e: self._handle_toggle())
        self.root.bind("<Control-q>", lambda e: self.exit_app())
        self.root.bind("<Control-l>", lambda e: self._toggle_log_panel())

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Tab 1: Blocker
        self.tab_blocker = tk.Frame(self.notebook, bg=COL_BASE)
        self.notebook.add(self.tab_blocker, text=" 🛡️ AI Blocker ")

        # Tab 2: DevSec Gateway
        self.tab_gateway = tk.Frame(self.notebook, bg=COL_BASE)
        self.notebook.add(self.tab_gateway, text=" ⚡ DevSec Gateway ")

        self._build_header()
        self._build_status_card()
        self._build_toggle_button()
        self._build_info_panel()
        self._build_log_panel()
        self._build_footer()

        self._build_gateway_tab()

        self._update_language_ui()
        self._schedule_connectivity_check()

    def _setup_ttk_styles(self):
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
        self.root.option_add("*TCombobox*Listbox.background", COL_SURFACE0)
        self.root.option_add("*TCombobox*Listbox.foreground", COL_TEXT)
        self.root.option_add("*TCombobox*Listbox.selectBackground", COL_BLUE)
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#000000")
        self.root.option_add("*TCombobox*Listbox.font", (UI_FONT, 9))

    def _build_header(self):
        header = tk.Frame(self.tab_blocker, bg=COL_BASE)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))

        self.title_label = tk.Label(
            header, text="🛡️  AI-Router-Blocker-AiO",
            font=(UI_FONT, 16, "bold"),
            bg=COL_BASE, fg=COL_TEXT,
        )
        self.title_label.pack(side=tk.LEFT)

        right_panel = tk.Frame(header, bg=COL_BASE)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        self.profile_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            right_panel,
            textvariable=self.profile_var,
            state="readonly",
            width=12,
            font=(UI_FONT, 9)
        )
        self.profile_combo.pack(side=tk.LEFT, padx=(0, 10), pady=(4, 0))
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)

        self.lang_var = tk.StringVar()
        self.lang_combo = ttk.Combobox(
            right_panel,
            textvariable=self.lang_var,
            values=list(LANG_DISPLAY_MAP.keys()),
            state="readonly",
            width=12,
            font=(UI_FONT, 9)
        )
        self.lang_combo.pack(side=tk.LEFT, padx=(0, 10), pady=(4, 0))

        initial_display = LANG_CODE_MAP.get(self.current_lang, "English")
        self.lang_combo.set(initial_display)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        from ai_blocker import __version__
        self.version_label = tk.Label(
            right_panel, text=f"v{__version__}",
            font=(UI_FONT, 9),
            bg=COL_BASE, fg=COL_SUBTEXT,
        )
        self.version_label.pack(side=tk.RIGHT, pady=(6, 0))

    def _build_status_card(self):
        self.card_frame = tk.Frame(
            self.tab_blocker, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        self.card_frame.pack(fill=tk.X, padx=24, pady=(16, 0))

        inner = tk.Frame(self.card_frame, bg=COL_SURFACE0)
        inner.pack(fill=tk.X, padx=16, pady=14)

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

    def _build_info_panel(self):
        self.info_panel = tk.Frame(
            self.tab_blocker, bg=COL_SURFACE0,
            highlightbackground=COL_SURFACE1, highlightthickness=1,
        )
        self.info_panel.pack(fill=tk.BOTH, expand=True, padx=24, pady=(16, 0))

        self.title_bar = tk.Frame(self.info_panel, bg=COL_SURFACE0)
        self.title_bar.pack(fill=tk.X, padx=14, pady=(10, 4))

        self.categories_title_label = tk.Label(
            self.title_bar, text="",
            font=(UI_FONT, 10, "bold"),
            bg=COL_SURFACE0, fg=COL_TEXT, anchor="w",
        )
        self.categories_title_label.pack(side=tk.LEFT)

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

        tk.Frame(self.info_panel, bg=COL_SURFACE1, height=1).pack(fill=tk.X, padx=14)

        self.list_frame = tk.Frame(self.info_panel, bg=COL_SURFACE0)
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(6, 10))

        self.category_icons = CATEGORY_ICONS

        self._populate_category_list()

    def _populate_category_list(self):
        for child in self.list_frame.winfo_children():
            child.destroy()

        self.category_checkboxes = {}

        for cat, domains in BLOCKLIST.items():
            if cat not in self.category_vars:
                self.category_vars[cat] = tk.BooleanVar(value=True)

            row = tk.Frame(self.list_frame, bg=COL_SURFACE0)
            row.pack(fill=tk.X, pady=1)

            icon = self.category_icons.get(cat, "📦")
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
        dialog = tk.Toplevel(self.root)
        dialog.title(STRINGS[self.current_lang].get("add_custom_title", "Add Custom Domain"))
        dialog.geometry("350x200")
        dialog.resizable(False, False)
        dialog.configure(bg=COL_BASE)
        dialog.transient(self.root)
        dialog.grab_set()

        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 200) // 2
        dialog.geometry(f"+{x}+{y}")

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

        if cat not in BLOCKLIST:
            BLOCKLIST[cat] = []
        if domain not in BLOCKLIST[cat]:
            BLOCKLIST[cat].append(domain)

        custom_domains = self.config.get("custom_domains", {})
        if cat not in custom_domains:
            custom_domains[cat] = []
        if domain not in custom_domains[cat]:
            custom_domains[cat].append(domain)

        self.config["custom_domains"] = custom_domains
        self._save_current_config()

        self._populate_category_list()

        s = STRINGS[self.current_lang]
        total_domains = count_total_domains()
        self.categories_total_domains_label.configure(
            text=s["domains_label"].format(total=total_domains)
        )

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

        if CURRENT_OS == "Windows":
            self.autostart_var = tk.BooleanVar(value=get_windows_autostart())
            self.autostart_chk = tk.Checkbutton(
                footer,
                text="",
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

        self.current_editors = []
        self.editors_btn = tk.Button(
            footer, text="",
            font=(UI_FONT, 8, "bold"),
            bg=COL_BASE, fg=COL_YELLOW,
            activebackground=COL_BASE, activeforeground=COL_TEXT,
            bd=0, cursor="hand2", relief="flat",
            command=self._show_running_editors
        )
        self._refresh_editors_label()

    def _show_running_editors(self):
        if not self.current_editors:
            return
        editors_str = "\n".join(f"• {e}" for e in self.current_editors)
        self.show_toast("Active AI Editors", editors_str, "warning")

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

    def _on_language_selected(self, event):
        selected_display = self.lang_combo.get()
        selected_code = LANG_DISPLAY_MAP.get(selected_display, "en")

        if selected_code != self.current_lang:
            self.current_lang = selected_code
            self._update_language_ui()
            self._save_current_config()

    def _update_language_ui(self):
        s = STRINGS[self.current_lang]

        self.title_label.configure(text="🛡️  AI Network Blocker")
        self.root.title("AI Network Blocker v1.2.1")

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

        self.categories_title_label.configure(text=s["categories_title"])
        total_domains = count_total_domains()
        self.categories_total_domains_label.configure(
            text=s["domains_label"].format(total=total_domains)
        )

        translations = CATEGORY_TRANSLATIONS.get(self.current_lang, CATEGORY_TRANSLATIONS["en"])
        for cat, chk in self.category_checkboxes.items():
            translated_name = translations.get(cat, cat)
            icon = self.category_icons.get(cat, "•")
            chk.configure(text=f"  {icon}  {translated_name}")

        self._update_visuals()

        if CURRENT_OS == "Windows" and hasattr(self, 'autostart_chk'):
            self.autostart_chk.configure(text=s.get("autostart_label", "Start with Windows"))

        if hasattr(self, 'log_toggle_btn'):
            arrow = "▼" if self.log_expanded else "▶"
            self.log_toggle_btn.configure(text=f"{arrow}  {s.get('log_title', 'Activity Log')}")
            self._update_log_display()

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

        self._save_current_config()
        self.log_action("log_profile", profile=s[f"profile_{profile_key}"])

        if self.is_blocked:
            self._handle_reapply_block()
        else:
            self._update_visuals()

    def _on_category_toggled(self):
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
        self.is_busy = False
        self.toggle_btn.configure(state="normal")

        if ok:
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

        try:
            toast.attributes("-topmost", True)
            toast.attributes("-alpha", 0.0)
        except Exception:
            pass

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

        bar = tk.Frame(toast, bg=accent_color, width=4)
        bar.pack(side=tk.LEFT, fill=tk.Y)

        content = tk.Frame(toast, bg=COL_SURFACE0)
        content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=10)

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

        msg_label = tk.Label(
            content, text=message,
            font=(UI_FONT, 9),
            bg=COL_SURFACE0, fg=COL_TEXT,
            anchor="nw", justify=tk.LEFT,
            wraplength=290
        )
        msg_label.pack(fill=tk.BOTH, expand=True, pady=(4, 0))

        lines = message.count("\n") + max(1, len(message) // 38)
        toast_height = max(80, 50 + lines * 16)
        toast.toast_height = toast_height

        def on_close(e=None):
            self._close_toast(toast)

        close_btn.bind("<Button-1>", on_close)
        toast.bind("<Button-1>", on_close)
        content.bind("<Button-1>", on_close)
        title_label.bind("<Button-1>", on_close)
        msg_label.bind("<Button-1>", on_close)

        self.active_toasts.append(toast)
        self._reposition_toasts()

        self._fade_in(toast)

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
        margin_y = 60

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
        s = STRINGS[self.current_lang]
        actual_blocked, blocked_count = get_hosts_status()
        self.is_blocked = actual_blocked

        time_str = ""
        if hasattr(self, 'last_toggle_time') and self.last_toggle_time:
            mins = int((time.time() - self.last_toggle_time) / 60)
            if mins > 0:
                time_str = f" ({mins}m)"
            else:
                time_str = " (now)"

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

        self.status_title.configure(text=target_title)
        self.status_subtitle.configure(text=target_subtitle)
        self.toggle_btn.configure(text=target_btn_text, activebackground=target_btn_activebg)

        if self.last_visuals_blocked != self.is_blocked:
            self._anim_id += 1

            if self.is_blocked:
                src_hl = COL_RED
                src_bg = "#6B1E2B"
                src_fg = "#F38BA8"
            else:
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
            self._anim_id += 1
            self.card_frame.configure(highlightbackground=target_hl)
            self.status_dot.configure(fg=target_dot_fg)
            self.toggle_btn.configure(bg=target_btn_bg, fg=target_btn_fg)

        if CURRENT_OS == "Windows" and hasattr(self, 'tray_icon'):
            self.tray_icon.update_icon()

    def _refresh_editors_label(self):
        if getattr(self, '_scan_after_id', None):
            self.root.after_cancel(self._scan_after_id)
            self._scan_after_id = None

        def scan():
            running = detect_running_ai_editors()
            s = STRINGS[self.current_lang]
            if running:
                text = s["running_warning"].format(editors=f"{len(running)} 💻")
            else:
                text = ""

            def update_ui():
                self.current_editors = running
                if text:
                    self.editors_btn.configure(text=text)
                    if not self.editors_btn.winfo_ismapped():
                        self.editors_btn.pack(side=tk.RIGHT)
                else:
                    if self.editors_btn.winfo_ismapped():
                        self.editors_btn.pack_forget()
                self._scan_after_id = self.root.after(3000, self._refresh_editors_label)

            self.root.after(0, update_ui)

        threading.Thread(target=scan, daemon=True).start()
