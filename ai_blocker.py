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

# =====================================================================
# VERSIÓN / VERSION
# =====================================================================
APP_VERSION = "1.0.1"

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
    "Otros": [
        "api.perplexity.ai", "perplexity.ai",
        "app.wordware.ai",
    ],
}

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

CATEGORY_TRANSLATIONS = {
    "en": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Others"},
    "es": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Otros"},
    "pt": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Outros"},
    "fr": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Autres"},
    "de": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Andere"},
    "it": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Altri"},
    "ru": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "Другие"},
    "zh": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "其他"},
    "ja": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "その他"},
    "ko": {"OpenAI": "OpenAI", "Anthropic": "Anthropic", "GitHub Copilot": "GitHub Copilot", "Google AI": "Google AI", "Meta AI": "Meta AI", "Mistral AI": "Mistral AI", "Microsoft Copilot": "Microsoft Copilot", "DeepSeek": "DeepSeek", "Otros": "기타"},
}

STRINGS = {
    "en": {
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
        "admin_required_msg": "Administrator privileges are required.\n\nRight-click → 'Run as administrator'." if CURRENT_OS == "Windows" else "Root privileges are required.\n\nRun with: sudo python3 ai_blocker.py"
    },
    "es": {
        "protected_title": "PROTEGIDO — Bloqueo activo",
        "protected_desc": "{count} dominios redirigidos a 127.0.0.1",
        "exposed_title": "EXPUESTO — Sin protección",
        "exposed_desc": "Tu tráfico de red hacia IAs está abierto",
        "btn_block": "🔒  BLOQUEAR IA",
        "btn_unblock": "🔓  DESBLOQUEAR IA",
        "busy_text": "⏳  Procesando...",
        "categories_title": "Categorías bloqueadas",
        "domains_label": "{total} dominios",
        "running_warning": "⚠ Detectados: {editors}",
        "hosts_write_error_title": "Error de Permisos",
        "hosts_write_error_msg": "No se pudo escribir en el archivo hosts.\nPor favor, ejecuta la aplicación como Administrador.",
        "unexpected_error_title": "Error Inesperado",
        "unexpected_error_msg": "Ocurrió un error al intentar aplicar el bloqueo:\n{error}",
        "block_success_title": "Bloqueo de IA Activo",
        "block_success_msg": "¡Bloqueo activado con éxito!\n\n✓ {added_count} dominios bloqueados en el archivo hosts.\n{process_details}\n✓ Caché DNS limpiada.",
        "unblock_success_title": "Bloqueo Desactivado",
        "unblock_success_msg": "¡El bloqueo de IA ha sido desactivado!\n\n✓ {removed} entradas eliminadas del hosts.\n✓ Caché DNS limpiada.\n\nTodos los servicios de IA vuelven a estar accesibles.",
        "closed_processes_prefix": "✓ Se cerraron los siguientes procesos: ",
        "no_processes_detected": "• No se detectaron editores de IA abiertos.",
        "admin_required_title": "Acceso Denegado",
        "admin_required_msg": "Se requieren privilegios de Administrador.\n\nHaz clic derecho → 'Ejecutar como administrador'." if CURRENT_OS == "Windows" else "Se requieren privilegios de root.\n\nEjecuta con: sudo python3 ai_blocker.py"
    },
    "pt": {
        "protected_title": "PROTEGIDO — Bloqueio ativo",
        "protected_desc": "{count} domínios redirecionados para 127.0.0.1",
        "exposed_title": "EXPOSTO — Sem proteção",
        "exposed_desc": "Seu tráfego de rede para IA está aberto",
        "btn_block": "🔒  BLOQUEAR IA",
        "btn_unblock": "🔓  DESBLOQUEAR IA",
        "busy_text": "⏳  Processando...",
        "categories_title": "Categorias bloqueadas",
        "domains_label": "{total} domínios",
        "running_warning": "⚠ Detectados: {editors}",
        "hosts_write_error_title": "Erro de Permissão",
        "hosts_write_error_msg": "Não foi possível escrever no arquivo hosts.\nPor favor, execute o aplicativo como Administrador.",
        "unexpected_error_title": "Erro Inesperado",
        "unexpected_error_msg": "Ocurreu um erro:\n{error}",
        "block_success_title": "Bloqueio de IA Ativo",
        "block_success_msg": "Bloqueio ativado com sucesso!\n\n✓ {added_count} domínios bloqueados no arquivo hosts.\n{process_details}\n✓ Cache DNS limpo.",
        "unblock_success_title": "Bloqueio Desativado",
        "unblock_success_msg": "O bloqueio de IA foi desativado!\n\n✓ {removed} entradas removidas do hosts.\n✓ Cache DNS limpo.\n\nTodos os serviços de IA estão acessíveis novamente.",
        "closed_processes_prefix": "✓ Processos fechados: ",
        "no_processes_detected": "• Nenhum editor de IA aberto detectado.",
        "admin_required_title": "Acesso Negado",
        "admin_required_msg": "Privilégios de Administrador são necessários.\n\nClique com o botão direito → 'Executar como administrador'." if CURRENT_OS == "Windows" else "Privilégios de root são necessários.\n\nExecute com: sudo python3 ai_blocker.py"
    },
    "fr": {
        "protected_title": "PROTÉGÉ — Blocage actif",
        "protected_desc": "{count} domaines redirigés vers 127.0.0.1",
        "exposed_title": "EXPOSÉ — Sans protection",
        "exposed_desc": "Votre trafic réseau vers l'IA est ouvert",
        "btn_block": "🔒  BLOQUER L'IA",
        "btn_unblock": "🔓  DÉBLOQUER L'IA",
        "busy_text": "⏳  Traitement...",
        "categories_title": "Catégories bloquées",
        "domains_label": "{total} domaines",
        "running_warning": "⚠ Détectés: {editors}",
        "hosts_write_error_title": "Erreur d'autorisation",
        "hosts_write_error_msg": "Impossible d'écrire dans le fichier hosts.\nVeuillez lancer l'application en tant qu'Administrateur.",
        "unexpected_error_title": "Erreur inattendue",
        "unexpected_error_msg": "Une erreur est survenue :\n{error}",
        "block_success_title": "Blocage de l'IA Actif",
        "block_success_msg": "Blocage activé avec succès !\n\n✓ {added_count} domaines bloqués dans le fichier hosts.\n{process_details}\n✓ Cache DNS vidé.",
        "unblock_success_title": "Blocage Désactivé",
        "unblock_success_msg": "Le blocage de l'IA a été désactivé !\n\n✓ {removed} entrées supprimées du fichier hosts.\n✓ Cache DNS vidé.\n\nTous les services d'IA sont à nouveau accessibles.",
        "closed_processes_prefix": "✓ Processus fermés : ",
        "no_processes_detected": "• Aucun éditeur d'IA ouvert détecté.",
        "admin_required_title": "Accès Refusé",
        "admin_required_msg": "Des privilèges d'Administrateur sont requis.\n\nFaites un clic droit → 'Exécuter en tant qu'administrateur'." if CURRENT_OS == "Windows" else "Les privilèges root sont requis.\n\nExécutez avec : sudo python3 ai_blocker.py"
    },
    "de": {
        "protected_title": "GESCHÜTZT — Blockierung aktiv",
        "protected_desc": "{count} Domains umgeleitet auf 127.0.0.1",
        "exposed_title": "GEFÄHRDET — Kein Schutz",
        "exposed_desc": "Ihr Datenverkehr zu KI-Diensten ist offen",
        "btn_block": "🔒  KI BLOCKIEREN",
        "btn_unblock": "🔓  KI FREIGEBEN",
        "busy_text": "⏳  Verarbeiten...",
        "categories_title": "Blockierte Kategorien",
        "domains_label": "{total} Domains",
        "running_warning": "⚠ Erkannt: {editors}",
        "hosts_write_error_title": "Berechtigungsfehler",
        "hosts_write_error_msg": "Schreiben in die Hosts-Datei fehlgeschlagen.\nBitte führen Sie die Anwendung als Administrator aus.",
        "unexpected_error_title": "Unerwarteter Fehler",
        "unexpected_error_msg": "Ein Fehler ist aufgetreten:\n{error}",
        "block_success_title": "KI-Blockierung Aktiv",
        "block_success_msg": "Blockierung erfolgreich aktiviert!\n\n✓ {added_count} Domains in der Hosts-Datei blockiert.\n{process_details}\n✓ DNS-Cache geleert.",
        "unblock_success_title": "Blockierung Deaktiviert",
        "unblock_success_msg": "Die KI-Blockierung wurde deaktiviert!\n\n✓ {removed} Einträge aus der Hosts-Datei entfernt.\n✓ DNS-Cache geleert.\n\nAlle KI-Dienste sind wieder erreichbar.",
        "closed_processes_prefix": "✓ Geschlossene Prozesse: ",
        "no_processes_detected": "• Keine geöffneten KI-Editoren erkannt.",
        "admin_required_title": "Zugriff Verweigert",
        "admin_required_msg": "Administratorrechte sind erforderlich.\n\nRechtsklick → 'Als Administrator ausführen'." if CURRENT_OS == "Windows" else "Root-Rechte sind erforderlich.\n\nAusführen mit: sudo python3 ai_blocker.py"
    },
    "it": {
        "protected_title": "PROTETTO — Blocco attivo",
        "protected_desc": "{count} domini reindirizzati a 127.0.0.1",
        "exposed_title": "ESPOSTO — Nessuna protezione",
        "exposed_desc": "Il tuo traffico verso le IA è aperto",
        "btn_block": "🔒  BLOCCA IA",
        "btn_unblock": "🔓  SBLOCCA IA",
        "busy_text": "⏳  Elaborazione...",
        "categories_title": "Categorie bloccate",
        "domains_label": "{total} domini",
        "running_warning": "⚠ Rilevati: {editors}",
        "hosts_write_error_title": "Errore di Permesso",
        "hosts_write_error_msg": "Impossibile scrivere nel file hosts.\nEsegui l'applicazione como Amministratore.",
        "unexpected_error_title": "Errore Inaspettato",
        "unexpected_error_msg": "Si è verificato un errore:\n{error}",
        "block_success_title": "Blocco IA Attivo",
        "block_success_msg": "Blocco attivato con successo!\n\n✓ {added_count} domini bloccati nel file hosts.\n{process_details}\n✓ Cache DNS svuotata.",
        "unblock_success_title": "Blocco Disattivato",
        "unblock_success_msg": "Il blocco IA è stato disattivato!\n\n✓ {removed} voci rimosse dal file hosts.\n✓ Cache DNS svuotata.\n\nTutti i servizi IA sono nuovamente accessibili.",
        "closed_processes_prefix": "✓ Processi terminati: ",
        "no_processes_detected": "• Nessun editor IA aperto rilevato.",
        "admin_required_title": "Accesso Negato",
        "admin_required_msg": "Sono richiesti i privilegi di Amministratore.\n\nTasto destro → 'Esegui como amministratore'." if CURRENT_OS == "Windows" else "Sono richiesti i privilegi di root.\n\nEsegui con: sudo python3 ai_blocker.py"
    },
    "ru": {
        "protected_title": "ЗАЩИЩЕНО — Блокировка активна",
        "protected_desc": "{count} доменов перенаправлено на 127.0.0.1",
        "exposed_title": "УЯЗВИМО — Нет защиты",
        "exposed_desc": "Ваш сетевой трафик к ИИ открыт",
        "btn_block": "🔒  БЛОКИРОВАТЬ ИИ",
        "btn_unblock": "🔓  РАЗБЛОКИРОВАТЬ ИИ",
        "busy_text": "⏳  Обработка...",
        "categories_title": "Заблокированные категории",
        "domains_label": "{total} доменов",
        "running_warning": "⚠ Обнаружены: {editors}",
        "hosts_write_error_title": "Ошибка прав доступа",
        "hosts_write_error_msg": "Не удалось записать в файл hosts.\nПожалуйста, запустите приложение от имени Администратора.",
        "unexpected_error_title": "Неожиданная ошибка",
        "unexpected_error_msg": "Произошла ошибка:\n{error}",
        "block_success_title": "Блокировка ИИ Активна",
        "block_success_msg": "Блокировка успешно активирована!\n\n✓ {added_count} доменов заблокировано в файле hosts.\n{process_details}\n✓ Кэш DNS очищен.",
        "unblock_success_title": "Блокировка Отключена",
        "unblock_success_msg": "Блокировка ИИ отключена!\n\n✓ {removed} записей удалено из файла hosts.\n✓ Кэш DNS очищен.\n\nВсе ИИ-сервисы снова доступны.",
        "closed_processes_prefix": "✓ Закрытые процессы: ",
        "no_processes_detected": "• Запущенных ИИ-редакторов не обнаружено.",
        "admin_required_title": "Доступ запрещен",
        "admin_required_msg": "Требуются права Администратора.\n\nНажмите правой кнопкой мыши → 'Запуск от имени администратора'." if CURRENT_OS == "Windows" else "Требуются права root.\n\nЗапустите с помощью: sudo python3 ai_blocker.py"
    },
    "zh": {
        "protected_title": "已保护 — 拦截处于激活状态",
        "protected_desc": "{count} 个域名已被重定向至 127.0.0.1",
        "exposed_title": "未受保护 — 存在风险",
        "exposed_desc": "您的网络流量可以正常访问 AI 服务",
        "btn_block": "🔒  拦截 AI 流量",
        "btn_unblock": "🔓  恢复 AI 访问",
        "busy_text": "⏳  正在处理...",
        "categories_title": "已拦截类别",
        "domains_label": "{total} 个域名",
        "running_warning": "⚠ 检测到运行中: {editors}",
        "hosts_write_error_title": "权限错误",
        "hosts_write_error_msg": "无法写入 hosts 文件。\n请以管理员身份运行此程序。",
        "unexpected_error_title": "意外错误",
        "unexpected_error_msg": "发生错误:\n{error}",
        "block_success_title": "AI 拦截已启用",
        "block_success_msg": "成功启用拦截！\n\n✓ hosts 文件中已拦截 {added_count} 个域名。\n{process_details}\n✓ DNS 缓存已清空。",
        "unblock_success_title": "AI 拦截已禁用",
        "unblock_success_msg": "AI 拦截已成功关闭！\n\n✓ 已从 hosts 文件中移除 {removed} 条记录。\n✓ DNS 缓存已清空。\n\n所有 AI 服务已恢复网络访问。",
        "closed_processes_prefix": "✓ 已关闭的进程: ",
        "no_processes_detected": "• 未检测到运行中的 AI 编辑器。",
        "admin_required_title": "拒绝访问",
        "admin_required_msg": "需要管理员权限。\n\n请右键单击 → 选择 “以管理员身份运行”。" if CURRENT_OS == "Windows" else "需要 root 权限。\n\n请使用此命令运行：sudo python3 ai_blocker.py"
    },
    "ja": {
        "protected_title": "保護中 — ブロック有効",
        "protected_desc": "{count} 個のドメインを 127.0.0.1 にリダイレクト中",
        "exposed_title": "未保護 — 危険",
        "exposed_desc": "AI サービスへの通信がオープンになっています",
        "btn_block": "🔒  AI をブロックする",
        "btn_unblock": "🔓  ブロックを解除する",
        "busy_text": "⏳  処理中...",
        "categories_title": "ブロック対象カテゴリ",
        "domains_label": "{total} ドメイン",
        "running_warning": "⚠ 検出中: {editors}",
        "hosts_write_error_title": "権限エラー",
        "hosts_write_error_msg": "hosts 文件に書き込めませんでした。\n管理者としてアプリケーションを実行してください。",
        "unexpected_error_title": "予期せぬエラー",
        "unexpected_error_msg": "エラーが発生しました:\n{error}",
        "block_success_title": "AI ブロック有効化",
        "block_success_msg": "ブロックを正常に有効化しました！\n\n✓ hosts ファイルで {added_count} 個のドメインをブロックしました。\n{process_details}\n✓ DNS キャッシュをクリアしました。",
        "unblock_success_title": "AI ブロック解除",
        "unblock_success_msg": "AI ブロックを解除しました！\n\n✓ hosts ファイルから {removed} 件の項目を削除しました。\n✓ DNS キャッシュをクリアしました。\n\nすべての AI ツールが再び通信可能になりました。",
        "closed_processes_prefix": "✓ 終了したプロセス: ",
        "no_processes_detected": "• 起動中の AI エディタは検出されませんでした。",
        "admin_required_title": "アクセス拒否",
        "admin_required_msg": "管理者権限が必要です。\n\n右クリック → 「管理者として実行」を選択してください。" if CURRENT_OS == "Windows" else "root 権限が必要です。\n\n次のコマンドで実行してください: sudo python3 ai_blocker.py"
    },
    "ko": {
        "protected_title": "보호됨 — 블록 활성화됨",
        "protected_desc": "{count}개 도메인이 127.0.0.1로 리디렉션됨",
        "exposed_title": "노출됨 — 보호 없음",
        "exposed_desc": "AI 서비스로의 네트워크 통신이 열려 있습니다",
        "btn_block": "🔒  AI 네트워크 차단",
        "btn_unblock": "🔓  차단 해제하기",
        "busy_text": "⏳  처리 중...",
        "categories_title": "차단된 카테고리",
        "domains_label": "{total}개 도메인",
        "running_warning": "⚠ 감지됨: {editors}",
        "hosts_write_error_title": "권한 오류",
        "hosts_write_error_msg": "hosts 파일에 쓸 수 없습니다.\n관리자 권한으로 응용 프로그램을 실행해 주세요.",
        "unexpected_error_title": "예기치 않은 오류",
        "unexpected_error_msg": "오류가 발생했습니다:\n{error}",
        "block_success_title": "AI 차단 활성화됨",
        "block_success_msg": "차단이 성공적으로 활성화되었습니다!\n\n✓ hosts 파일에서 {added_count}개 도메인이 차단되었습니다.\n{process_details}\n✓ DNS 캐시가 플러시되었습니다.",
        "unblock_success_title": "AI 차단 비활성화됨",
        "unblock_success_msg": "AI 차단이 비활성화되었습니다!\n\n✓ hosts 파일에서 {removed}개 항목이 제거되었습니다.\n✓ DNS 캐시가 플러시되었습니다.\n\n모든 AI 서비스를 다시 정상적으로 사용할 수 있습니다.",
        "closed_processes_prefix": "✓ 종료된 프로세스: ",
        "no_processes_detected": "• 실행 중인 AI 에디터가 감지되지 않았습니다.",
        "admin_required_title": "액세스 거부",
        "admin_required_msg": "관리자 권한이 필요합니다。\n\n오른쪽 마우스 클릭 → '관리자 권한으로 실행'을 선택하세요." if CURRENT_OS == "Windows" else "root 권한이 필요합니다。\n\n다음 명령으로 실행하세요: sudo python3 ai_blocker.py"
    }
}

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
            else:
                executable = sys.executable
            
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", executable,
                " ".join(f'"{a}"' for a in sys.argv),
                None, 1
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


def check_block_status():
    """
    Determina si el bloqueo está activo actualmente.
    Determines if the block is currently active.
    """
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
    """
    Retorna cuántos dominios marcados con AI-Block están activos en el hosts.
    Returns how many domains marked with AI-Block are active in hosts.
    """
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


def detect_system_language():
    """
    Detecta el idioma del sistema Windows de forma robusta.
    Retorna el código de dos letras (es, en, pt, fr, de, it, ru, zh, ja, ko).
    Si no está soportado o falla, retorna 'en' (inglés).

    Robustly detects the Windows system language.
    Returns the two-letter code (es, en, pt, fr, de, it, ru, zh, ja, ko).
    If unsupported or fails, returns 'en' (English).
    """
    try:
        lang, _ = locale.getdefaultlocale()
        if lang:
            code = lang.split('_')[0].lower()
            if code in STRINGS:
                return code
    except Exception:
        pass
    
    # Alternativa en Windows / Windows alternative
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


# =====================================================================
# ACCIONES DE BLOQUEO / DESBLOQUEO / BLOCKING / UNBLOCKING ACTIONS
# =====================================================================
def force_close_processes():
    """
    Cierra de forma forzada los editores de IA en ejecución.
    Force closes running AI editors.
    """
    closed = []
    kwargs = _get_subprocess_kwargs()

    for proc in PROCESS_LIST:
        try:
            if CURRENT_OS == "Windows":
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", proc],
                    capture_output=True, text=True, **kwargs,
                )
                if result.returncode == 0:
                    closed.append(proc.replace(".exe", ""))
            else:
                # Linux/macOS: usar killall
                # Linux/macOS: use killall
                result = subprocess.run(
                    ["killall", proc],
                    capture_output=True, text=True, **kwargs,
                )
                if result.returncode == 0:
                    closed.append(proc)
        except Exception:
            pass
    return closed


def detect_running_ai_editors():
    """
    Detecta qué editores de IA están en ejecución actualmente (sin cerrarlos).
    Detects which AI editors are currently running (without closing them).
    """
    running = []
    kwargs = _get_subprocess_kwargs()

    for proc in PROCESS_LIST:
        try:
            if CURRENT_OS == "Windows":
                result = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {proc}", "/NH"],
                    capture_output=True, text=True, **kwargs,
                )
                if proc.lower() in result.stdout.lower():
                    running.append(proc.replace(".exe", ""))
            else:
                # Linux/macOS: usar pgrep -x para buscar por nombre exacto
                # Linux/macOS: use pgrep -x for exact name match
                result = subprocess.run(
                    ["pgrep", "-x", proc],
                    capture_output=True, text=True, **kwargs,
                )
                if result.returncode == 0 and result.stdout.strip():
                    running.append(proc)
        except Exception:
            pass
    return running


def activate_block(lang):
    """
    Aplica el bloqueo de red de IAs.
    Applies the AI network block.
    """
    # 1. Cierra procesos activos / 1. Close active processes
    closed_list = force_close_processes()
    s = STRINGS[lang]

    # 2. Modifica el archivo hosts / 2. Modify hosts file
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
# INTERFAZ GRÁFICA PREMIUM CON INTERNACIONALIZACIÓN / PREMIUM GUI WITH i18n
# =====================================================================
class AIBlockerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Network Blocker")
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

        # Detectar idioma inicial / Detect initial language
        self.current_lang = detect_system_language()
        
        # Estado actual del archivo hosts / Current status of the hosts file
        self.is_blocked = check_block_status()
        self.is_busy = False

        # Construir la interfaz / Build the interface
        self._build_header()
        self._build_status_card()
        self._build_toggle_button()
        self._build_info_panel()
        self._build_footer()

        # Actualizar visualización e idioma / Update display and language
        self._update_language_ui()

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
        header = tk.Frame(self.root, bg=COL_BASE)
        header.pack(fill=tk.X, padx=24, pady=(20, 0))

        # Título principal / Main title
        self.title_label = tk.Label(
            header, text="🛡️  AI Network Blocker",
            font=("Segoe UI", 16, "bold"),
            bg=COL_BASE, fg=COL_TEXT,
        )
        self.title_label.pack(side=tk.LEFT)

        # Contenedor a la derecha / Right-side panel
        right_panel = tk.Frame(header, bg=COL_BASE)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

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
            self.root, bg=COL_SURFACE0,
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

    # -----------------------------------------------------------------
    # Botón toggle principal / Main toggle button
    # -----------------------------------------------------------------
    def _build_toggle_button(self):
        btn_frame = tk.Frame(self.root, bg=COL_BASE)
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
            self.root, bg=COL_SURFACE0,
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
            "Microsoft Copilot": "🟦", "DeepSeek": "🔮", "Otros": "📦",
        }

        # Guardar referencias de los labels de categorías para poder traducirlos dinámicamente
        # Store references of category labels to translate them dynamically
        self.category_labels = {}

        for cat, domains in BLOCKLIST.items():
            row = tk.Frame(self.list_frame, bg=COL_SURFACE0)
            row.pack(fill=tk.X, pady=1)

            icon = self.category_icons.get(cat, "•")
            cat_label = tk.Label(
                row, text=f"  {icon}  {cat}",
                font=(UI_FONT, 9), bg=COL_SURFACE0,
                fg=COL_TEXT, anchor="w",
            )
            cat_label.pack(side=tk.LEFT)
            self.category_labels[cat] = cat_label

            tk.Label(
                row, text=f"{len(domains)}",
                font=(UI_FONT, 9, "bold"), bg=COL_SURFACE0,
                fg=COL_BLUE, anchor="e",
            ).pack(side=tk.RIGHT, padx=(0, 4))

    # -----------------------------------------------------------------
    # Footer — créditos y aviso de editores detectados / Footer — credits and warning of detected editors
    # -----------------------------------------------------------------
    def _build_footer(self):
        footer = tk.Frame(self.root, bg=COL_BASE)
        footer.pack(fill=tk.X, padx=24, pady=(8, 12))

        self.footer_label = tk.Label(
            footer,
            text="Open Source · github.com/Akunimal/AI-Blocker",
            font=(UI_FONT, 8),
            bg=COL_BASE, fg=COL_SUBTEXT,
        )
        self.footer_label.pack(side=tk.LEFT)

        # Aviso en tiempo real de editores de IA activos / Real-time warning of active AI editors
        self.editors_label = tk.Label(
            footer, text="",
            font=(UI_FONT, 8),
            bg=COL_BASE, fg=COL_YELLOW,
        )
        self.editors_label.pack(side=tk.RIGHT)
        self._refresh_editors_label()

    # -----------------------------------------------------------------
    # Gestión de Idiomas / Language Management
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

        # 3. Categorías e Información / 3. Categories and Info
        self.categories_title_label.configure(text=s["categories_title"])
        total_domains = count_total_domains()
        self.categories_total_domains_label.configure(
            text=s["domains_label"].format(total=total_domains)
        )

        # 4. Traducir los nombres de categorías en el listado / 4. Translate category names in the list
        translations = CATEGORY_TRANSLATIONS.get(self.current_lang, CATEGORY_TRANSLATIONS["en"])
        for cat, label in self.category_labels.items():
            translated_name = translations.get(cat, cat)
            icon = self.category_icons.get(cat, "•")
            label.configure(text=f"  {icon}  {translated_name}")

        # 5. Estado y Botón (usando la lógica de visuals existente) / 5. Status and Button (using existing visuals logic)
        self._update_visuals()

    # -----------------------------------------------------------------
    # Lógica de Interacción y Estados / Interaction and States Logic
    # -----------------------------------------------------------------
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
                ok, msg = activate_block(self.current_lang)
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
        self._update_visuals()
        self._refresh_editors_label()

        s = STRINGS[self.current_lang]
        if ok:
            title = s["block_success_title"] if self.is_blocked else s["unblock_success_title"]
            messagebox.showinfo(title, msg)
        else:
            title = s["hosts_write_error_title"] if "hosts" in msg else s["unexpected_error_title"]
            messagebox.showerror(title, msg)

    def _update_visuals(self):
        """
        Actualiza colores y etiquetas según el estado de bloqueo.
        Updates colors and labels according to the block status.
        """
        s = STRINGS[self.current_lang]
        blocked_count = get_blocked_domains_count()

        if self.is_blocked:
            # Estado protegido (bloqueo activo) / Protected state (active blocking)
            self.status_dot.configure(fg=COL_GREEN)
            self.status_title.configure(text=s["protected_title"])
            self.status_subtitle.configure(
                text=s["protected_desc"].format(count=blocked_count)
            )
            self.toggle_btn.configure(
                text=s["btn_unblock"],
                bg="#2D6A4F", fg="#A6E3A1",
                activebackground="#1B4332",
            )
            self.card_frame.configure(highlightbackground=COL_GREEN)
        else:
            # Estado expuesto (bloqueo inactivo) / Exposed state (inactive blocking)
            self.status_dot.configure(fg=COL_RED)
            self.status_title.configure(text=s["exposed_title"])
            self.status_subtitle.configure(text=s["exposed_desc"])
            self.toggle_btn.configure(
                text=s["btn_block"],
                bg="#6B1E2B", fg="#F38BA8",
                activebackground="#4C1220",
            )
            self.card_frame.configure(highlightbackground=COL_RED)

    def _refresh_editors_label(self):
        """
        Efectúa escaneo rápido en segundo plano de editores de IA.
        Performs a quick background scan of AI editors.
        """
        def scan():
            running = detect_running_ai_editors()
            s = STRINGS[self.current_lang]
            if running:
                text = s["running_warning"].format(editors=", ".join(running))
            else:
                text = ""
            self.root.after(0, lambda: self.editors_label.configure(text=text))

        threading.Thread(target=scan, daemon=True).start()


# =====================================================================
# PUNTO DE ENTRADA PRINCIPAL / MAIN ENTRY POINT
# =====================================================================
if __name__ == "__main__":
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
    root.mainloop()
