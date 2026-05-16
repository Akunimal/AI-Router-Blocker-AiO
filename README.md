# AI Network Blocker for Windows

**Take back control. Decide when your AI-powered editors can talk to the cloud.**

![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

## What is this?

AI Network Blocker is a simple, open-source Windows application that gives you an on/off switch to instantly cut internet access to all major AI coding assistants and their backend APIs. With one click, it prevents tools like VS Code with Copilot, Cursor, Windsurf, or Claude Desktop from sending your code, prompts, or data to external servers.

## Why is this necessary?

AI coding assistants have deep access to your files and system. When you stop using them, they often remain running in the background and can still communicate with the internet. This leaves an open channel you don't fully control.

AI Network Blocker was created to:
- **Ensure privacy** – block data exfiltration when you are not actively working with AI.
- **Prevent accidental sharing** – avoid unintentional uploads of sensitive code or information.
- **Give you peace of mind** – you decide the exact moment these tools are allowed to connect.
- **Be lightweight and transparent** – uses only the Windows hosts file. No background services, no complex firewall rules.

## How it works

When you click **"🔒 BLOCK AI"**, the application performs three actions in sequence:
1. **Force-closes** common AI editors (VS Code, Cursor, Windsurf, Claude, Trae, Augment, etc.).
2. **Adds entries** to the Windows hosts file that redirect all requests to the major AI providers to `127.0.0.1`, effectively blocking them.
3. **Flushes the DNS cache** (`ipconfig /flushdns`) so the block takes effect immediately.

When you click **"🔓 UNBLOCK AI"**, it removes those specific entries from the hosts file and flushes DNS again, restoring normal internet access.

No data is sent anywhere. No telemetry. No network monitoring. Just a clean, deterministic kill switch.

## Features

- **One-click toggle** – block or unblock all AI services instantly
- **Premium dark UI** – modern Catppuccin-themed interface with status indicators
- **Auto UAC elevation** – automatically requests administrator privileges
- **DNS cache flush** – changes take effect immediately, no restart needed
- **Process detection** – shows which AI editors are currently running
- **Category breakdown** – visual list of all blocked providers and domain counts
- **Portable .exe** – single-file executable, no installation required
- **Threaded operations** – GUI never freezes during blocking/unblocking

## Supported targets

The default list blocks **35+ domains** from:

| Provider | Domains | Examples |
|---|---|---|
| OpenAI | 9 | `api.openai.com`, `chatgpt.com` |
| Anthropic | 4 | `claude.ai`, `api.anthropic.com` |
| GitHub Copilot | 4 | `copilot.github.com` |
| Google AI | 4 | `gemini.google.com`, `aistudio.google.com` |
| Microsoft Copilot | 3 | `copilot.microsoft.com`, `bing.com` |
| Meta AI | 2 | `meta.ai` |
| Mistral AI | 2 | `mistral.ai` |
| DeepSeek | 2 | `deepseek.com` |
| Others | 3 | `perplexity.ai`, `app.wordware.ai` |

You can easily modify the list by editing the `BLOCKLIST` dictionary at the top of the script.

## Usage

### Option A: Run the portable executable
1. Download `AI-Blocker.exe` from [Releases](https://github.com/Akunimal/AI-Blocker/releases).
2. Double-click it. The app will automatically request administrator privileges.
3. Click the big button to toggle blocking on or off.

### Option B: Run from source
```bash
# Clone the repository
git clone https://github.com/Akunimal/AI-Blocker.git
cd AI-Blocker

# Run (will auto-request admin elevation)
python ai_blocker.py
```

### Build the .exe yourself
```bash
# Install PyInstaller
pip install pyinstaller

# Run the build script
build.bat

# Or manually:
pyinstaller --onefile --windowed --uac-admin --name "AI-Blocker" ai_blocker.py
```

## Requirements

- Windows 10/11
- Administrator privileges (requested automatically)
- Python 3.x (only if running the `.py` script)

## Disclaimer

This tool modifies your system's hosts file. It only adds or removes lines containing the comment `# AI-Block` and will not touch other entries. Use at your own risk. Always make sure you have a backup of your hosts file before using any tool that edits it.

## Why open source?

Trust is everything. The code is deliberately short, fully commented, and easy to audit. No hidden surprises. You own your machine, you set the rules.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

**Reclaim your sovereignty.**  
One click. Total control.
