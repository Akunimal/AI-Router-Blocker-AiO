# 🛡️ AI Network Blocker — v2.1.0 (Multilingual Release)

**Version 2.1.0 introduces full internationalization supporting 10 languages with automatic detection and manual selection.**

This is a single-click desktop tool that gives you an on/off kill switch to instantly cut internet access to all major AI coding assistants and their backend APIs. Block them when you're done working. Unblock them when you need them again. Simple as that.

---

## ⬇️ Download

| File | Description |
|---|---|
| **`AI-Blocker.exe`** | Portable Windows executable (~12 MB). No installation needed. Just double-click. |

> **Note:** Windows may show a SmartScreen warning because the executable is not code-signed. Click "More info" → "Run anyway". The full source code is included in this repository for your review.

---

## 🆕 What's new in v2.1.0

### 🌍 Internationalization (i18n) & Localisation
- **10 languages supported**:
  - English 🇺🇸
  - Español 🇪🇸
  - Português 🇵🇹 / 🇧🇷
  - Français 🇫🇷
  - Deutsch 🇩🇪
  - Italiano 🇮🇹
  - Русский 🇷🇺
  - 中文 (简体) 🇨🇳
  - 日本語 🇯🇵
  - 한국어 🇰🇷
- **Automatic detection**: Automatically scans your Windows display language and LCID settings to match your language upon launch. If your system language is not supported, it defaults gracefully to English.
- **Manual selector**: Added a small, styled dark dropdown menu (`TCombobox`) in the header that lets you switch languages dynamically on the fly. All titles, buttons, descriptions, categories, and logs update instantly.

### Core Features
- ✅ **One-click block/unblock** of 35+ AI domains (OpenAI, Anthropic, Google, GitHub Copilot, Meta, Mistral, DeepSeek, Perplexity, and more)
- ✅ **Automatic process termination** — force-closes running AI editors (VS Code, Cursor, Windsurf, Claude, Trae, Augment, Roo, Cline)
- ✅ **DNS cache flush** (`ipconfig /flushdns`) after every action for instant effect
- ✅ **Safe hosts file editing** — only adds/removes lines marked with `# AI-Block`, never touches other entries
- ✅ **Auto UAC elevation** — requests administrator privileges automatically, no manual right-click needed

### User Interface & Styling
- ✅ **Premium dark theme** (Catppuccin Mocha palette)
- ✅ **Theme-aware dropdown**: Dropdown menu customized to match the dark aesthetic
- ✅ **Live status indicator** — green dot = protected, red dot = exposed
- ✅ **Category panel** — lists all blocked providers with emoji icons and domain counts
- ✅ **Running editors detection** — footer warns you if AI editors are still active
- ✅ **Non-blocking operations** — all tasks run in background threads, GUI never freezes

### Distribution & Auditability
- ✅ **Portable `.exe`** compiled with PyInstaller (single file, no dependencies)
- ✅ **Full source code** included — one Python file (~350 lines), fully commented in Spanish
- ✅ **Build script** (`build.bat`) to compile the `.exe` yourself
- ✅ **MIT License** — free to use, modify, and distribute for any purpose, non-profit

---

## 🔨 Build from source

```bash
# Clone the repo
git clone https://github.com/Akunimal/AI-Blocker.git
cd AI-Blocker

# Install PyInstaller
pip install pyinstaller

# Build the .exe
build.bat

# Or run directly without compiling:
python ai_blocker.py
```

---

## ⚙️ Requirements

- Windows 10 or 11
- Administrator privileges (requested automatically)
- Python 3.x (only if running from source)

---

## 📜 License

MIT License — free as in freedom. No commercial intent. No strings attached.
Do whatever you want with this code. See [LICENSE](https://github.com/Akunimal/AI-Blocker/blob/main/LICENSE) for details.

---

**Reclaim your sovereignty. One click. Total control.**
