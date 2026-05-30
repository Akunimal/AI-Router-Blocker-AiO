# 🛡️ AI Network Blocker — v1.1.0 (Cross-Platform Release)

**Version 1.1.0 introduces full cross-platform compatibility, allowing AI Network Blocker to run natively on Windows, Linux, and macOS.**

This is a single-click desktop tool that gives you an on/off kill switch to instantly cut internet access to all major AI coding assistants and their backend APIs. Block them when you're done working. Unblock them when you need them again. Simple as that.

---

## ⬇️ Download

| Operating System | Executable | Description |
|---|---|---|
| **Windows** | **`AI-Blocker.exe`** | Portable Windows executable (~12 MB). No installation needed. Just double-click. |
| **Linux / macOS** | **`AI-Blocker`** | Portable Unix binary. Run from terminal with root privileges. |

> [!NOTE]
> - **Windows**: Windows Defender / SmartScreen may show a warning because the executable is not code-signed. Click "More info" → "Run anyway".
> - **Linux & macOS**: The executable must be run with root privileges (using `sudo`) in order to modify the system hosts file.

---

## 🆕 What's new in v1.1.0

### 💻 Native Cross-Platform Support
- **Windows, Linux & macOS support**: The application now detects the host operating system dynamically and adapts its behavior and pathing.
- **Platform-specific Paths**: Automatically targets `C:\Windows\System32\drivers\etc\hosts` on Windows and `/etc/hosts` on macOS and Linux.
- **Smart Privilege Management**: Auto-elevates on Windows using standard UAC. On Linux/macOS, it checks if it's running as root (`geteuid() == 0`) and displays clear multilingual instructions to run with `sudo` if launched with normal user privileges.
- **Adaptive Process Killer**: Terminates running AI editors using the correct OS commands (`taskkill` on Windows, `killall` on Linux/macOS) and resolves the proper process names (handling `.exe` extensions on Windows vs native names on Unix).
- **Advanced DNS Cache Flushing**: 
  - **Windows**: Flushes DNS using `ipconfig /flushdns`.
  - **macOS**: Flushes DNS using `dscacheutil -flushcache` and `killall -HUP mDNSResponder`.
  - **Linux**: Flushes DNS utilizing `systemd-resolve --flush-caches` or `resolvectl flush-caches` depending on the system's setup.
- **Native Typography**: Adapts UI fonts to match the operating system's environment (`Segoe UI` for Windows, `Helvetica Neue` for macOS, `DejaVu Sans` for Linux) for a clean, integrated desktop feel.

### 🌍 Internationalization (i18n) & Localisation
- **10 languages supported**: Full support for English 🇺🇸, Español 🇪🇸, Português 🇵🇹, Français 🇫🇷, Deutsch 🇩🇪, Italiano 🇮🇹, Русский 🇷🇺, 中文 (简体) 🇨🇳, 日本語 🇯🇵, and 한국어 🇰🇷.
- **Automatic detection**: Automatically scans your system language on startup and applies the correct translations.
- **Manual selector**: Easily change the display language on the fly using the modern dark dropdown selector in the header.

---

## 🔨 Build from source

To package the binaries yourself:

```bash
# Clone the repo
git clone https://github.com/Akunimal/AI-Blocker.git
cd AI-Blocker

# Install PyInstaller
pip install pyinstaller

# Build the binary:
# On Windows:
build.bat

# On Linux / macOS:
chmod +x build.sh
./build.sh
```

---

## ⚙️ Requirements

| OS | Requirements |
|---|---|
| **Windows** | Windows 10 or 11, Administrator privileges (UAC prompt) |
| **Linux** | Any desktop distribution with Python 3 / Tkinter, running as `root` (via `sudo`) |
| **macOS** | macOS High Sierra or newer, running as `root` (via `sudo`) |

---

## 📜 License

MIT License — free as in freedom. No commercial intent. No strings attached.
Do whatever you want with this code. See [LICENSE](LICENSE) for details.

---

**Reclaim your sovereignty. One click. Total control.**
