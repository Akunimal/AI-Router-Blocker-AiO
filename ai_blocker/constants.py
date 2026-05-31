# -*- coding: utf-8 -*-
import os
import platform

CURRENT_OS = platform.system()  # 'Windows', 'Linux', 'Darwin'

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

if CURRENT_OS == "Windows":
    PROCESS_LIST = [
        "Code.exe", "Cursor.exe", "Windsurf.exe", "Claude.exe",
        "Trae.exe", "Cline.exe", "Roo.exe", "Augment.exe",
    ]
else:
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
    HOSTS_PATH = "/etc/hosts"

# Catppuccin Mocha colors
COL_BASE      = "#1E1E2E"
COL_SURFACE0  = "#313244"
COL_SURFACE1  = "#45475A"
COL_TEXT      = "#CDD6F4"
COL_SUBTEXT   = "#A6ADC8"
COL_RED       = "#F38BA8"
COL_GREEN     = "#A6E3A1"
COL_YELLOW    = "#F9E2AF"
COL_BLUE      = "#89B4FA"
COL_MAUVE     = "#CBA6F7"

def _get_ui_font():
    if CURRENT_OS == "Windows":
        return "Segoe UI"
    elif CURRENT_OS == "Darwin":
        return "Helvetica Neue"
    else:
        return "DejaVu Sans"

UI_FONT = _get_ui_font()
