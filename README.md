# 🛡️ AI Network Blocker for Windows

> **Take back control. Decide when your AI-powered editors can talk to the cloud.**

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Release](https://img.shields.io/github/v/release/Akunimal/AI-Blocker?color=blue&label=Latest%20Release)

---

## 📖 What is this?

**AI Network Blocker** is a free, open-source, single-click Windows desktop tool that blocks all network traffic between your machine and the major AI cloud providers. It works by editing the Windows `hosts` file — no background processes, no firewall rules, no drivers.

With one click it:
1. **Kills** running AI editor processes (VS Code, Cursor, Windsurf, Claude, etc.).
2. **Redirects** 35+ AI domains to `127.0.0.1` in your hosts file.
3. **Flushes** the DNS cache so the block takes effect **immediately**.

With a second click it **undoes everything** cleanly, removing only the lines it added.

---

## 🤔 Why does this exist?

AI coding assistants have deep, unrestricted access to your files, your clipboard, and your terminal. Even when you stop using them, their processes keep running in the background, silently maintaining open connections to remote servers. That means:

- Code you wrote *hours ago* could still be transmitted.
- Prompts containing proprietary logic could be cached or logged on third-party servers.
- You have **no visibility** into what data is being sent, or when.

**AI Network Blocker gives you a hard, deterministic kill switch.** No ambiguity. No trust required. The hosts file is a system-level override — if a domain resolves to `127.0.0.1`, nothing gets through. Period.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔒 **One-click toggle** | Block or unblock all AI services instantly |
| 🌍 **Multilingual support** | 10 languages supported with automatic system detection & manual selector |
| 🎨 **Premium dark UI** | Modern Catppuccin Mocha theme with color-coded status |
| 🔑 **Auto UAC elevation** | Automatically requests administrator privileges — no right-click needed |
| 🧹 **DNS cache flush** | Runs `ipconfig /flushdns` after every change for instant effect |
| 👁️ **Live process detection** | Footer shows which AI editors are currently running |
| 📊 **Category breakdown** | Visual panel listing all blocked providers with domain counts |
| 📦 **Portable .exe** | Single-file executable (~12 MB), zero installation |
| ⚡ **Non-blocking UI** | All operations run on background threads — the GUI never freezes |
| 🔍 **Fully auditable** | One Python file, ~350 lines, extensively commented in Spanish |

---

## 🎯 Blocked Providers & Domains

The default blocklist targets **35+ domains** across 9 categories:

| Provider | # Domains | Key domains |
|---|---|---|
| 🟢 OpenAI | 9 | `api.openai.com` · `chatgpt.com` · `platform.openai.com` |
| 🟠 Anthropic | 4 | `claude.ai` · `api.anthropic.com` · `anthropic.com` |
| 🐙 GitHub Copilot | 4 | `copilot.github.com` · `api.githubcopilot.com` |
| 🔵 Google AI | 4 | `gemini.google.com` · `aistudio.google.com` |
| 🟦 Microsoft Copilot | 3 | `copilot.microsoft.com` · `bing.com` |
| 🔷 Meta AI | 2 | `meta.ai` · `ai.meta.com` |
| 🌊 Mistral AI | 2 | `mistral.ai` · `api.mistral.ai` |
| 🔮 DeepSeek | 2 | `deepseek.com` · `api.deepseek.com` |
| 📦 Others | 3 | `perplexity.ai` · `app.wordware.ai` |

> **Want to add or remove domains?** Edit the `BLOCKLIST` dictionary at the top of [`ai_blocker.py`](ai_blocker.py). It's a simple Python dict — no recompilation needed if you run from source.

---

## 🚀 Quick Start

### Option A — Download the ready-to-use executable

1. Go to the [**Releases**](https://github.com/Akunimal/AI-Blocker/releases) page.
2. Download **`AI-Blocker.exe`** from the latest release.
3. Double-click it. Windows will show a UAC prompt — click **Yes**.
4. Click the big button to toggle the block on or off. That's it.

> The `.exe` is a self-contained, portable file. No installation, no dependencies, no Python required.

### Option B — Run from source code

```bash
# 1. Clone the repository
git clone https://github.com/Akunimal/AI-Blocker.git
cd AI-Blocker

# 2. Run the script (Python 3.x required)
python ai_blocker.py
```

The script will automatically request admin elevation via UAC. No need to right-click → "Run as administrator" manually.

---

## 🔨 Building the .exe yourself

If you want to compile the executable from source (to verify it, modify it, or just learn how), follow these steps:

### Prerequisites

- **Python 3.x** installed and available in your PATH
- **PyInstaller** (the packaging tool):

```bash
pip install pyinstaller
```

### Method 1 — Using the included build script

```bash
# Just run the batch file:
build.bat
```

The script will:
1. Clean any previous build artifacts (`build/`, `dist/`, `*.spec`)
2. Compile `ai_blocker.py` into a single `.exe` with admin manifest
3. Copy the final `AI-Blocker.exe` to the project root

### Method 2 — Manual command

```bash
pyinstaller --onefile --windowed --uac-admin --name "AI-Blocker" --clean ai_blocker.py
```

**Flags explained:**

| Flag | Purpose |
|---|---|
| `--onefile` | Packages everything into a single portable `.exe` |
| `--windowed` | Hides the console window (GUI-only application) |
| `--uac-admin` | Embeds a Windows manifest that triggers UAC elevation on launch |
| `--name "AI-Blocker"` | Sets the output filename |
| `--clean` | Clears PyInstaller cache before building |

The compiled executable will be in the `dist/` folder.

---

## 📁 Project Structure

```
AI-Blocker/
├── ai_blocker.py      # Full source code (Python 3, tkinter GUI)
├── build.bat          # One-click build script for compiling to .exe
├── AI-Blocker.exe     # Pre-compiled portable executable
├── README.md          # This file
├── LICENSE            # MIT License — free as in freedom
└── .gitignore         # Git ignore rules
```

---

## ⚙️ System Requirements

| Requirement | Details |
|---|---|
| **Operating System** | Windows 10 or Windows 11 |
| **Privileges** | Administrator (requested automatically via UAC) |
| **Python** | 3.x — only needed if running from source |
| **Dependencies** | None. Uses only Python standard library (`tkinter`, `ctypes`, `subprocess`) |
| **Disk space** | ~12 MB for the `.exe`, ~15 KB for the `.py` source |

---

## ⚠️ Disclaimer

This tool modifies your system's `hosts` file located at:
```
C:\Windows\System32\drivers\etc\hosts
```

It **only** adds or removes lines that contain the marker comment `# AI-Block`. It will **never** touch other entries in your hosts file.

That said:
- Always keep a backup of your hosts file before using any tool that modifies it.
- Use this software at your own risk.
- The authors are not responsible for any unintended consequences.

---

## 📜 License — Free as in Freedom

This project is released under the **MIT License** — see [LICENSE](LICENSE) for the full text.

**In plain language:** you are free to use, copy, modify, merge, publish, distribute, sublicense, and even sell copies of this software. There is no restriction whatsoever. This project was made **without any commercial intent** and is offered to the community as a public good.

Do whatever you want with it. Fork it, rebrand it, translate it, embed it in your own tools — no attribution required (though it's always appreciated). The only condition is that the license text stays included if you redistribute it.

**This is a non-profit, community-driven project.** No ads. No telemetry. No tracking. No monetization. Ever.

---

## 🤝 Contributing

Contributions are welcome! If you want to:
- Add new AI domains or providers to the blocklist
- Add support for other operating systems (Linux, macOS)
- Improve the UI or add features
- Translate the interface to another language

Just open a Pull Request or an Issue. All contributions, big or small, are valued.

---

## 💡 Why open source?

Trust is everything when a tool touches your system files. AI Network Blocker is:

- **Short** — one Python file, ~350 lines
- **Commented** — every function has docstrings in Spanish
- **Auditable** — no obfuscation, no compiled blobs, no network calls
- **Deterministic** — it either edits the hosts file or it doesn't. Nothing else.

You own your machine. You set the rules.

---

<p align="center">
  <strong>Reclaim your sovereignty.</strong><br>
  One click. Total control.
</p>
