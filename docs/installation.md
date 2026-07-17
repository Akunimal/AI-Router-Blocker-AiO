# Installation & Quickstart

There are three ways to get started with DevGate, depending on whether you want a zero-dependency binary, a python script, or an installable library.

---

## Option A — Standalone Executable (Recommended)

This is the easiest option. The binaries are fully compiled and portable—no dependencies, python installations, or configuration steps required.

1.  Visit the [**GitHub Releases**](https://github.com/Akunimal/AI-Router-Blocker-AiO/releases) page.
2.  Download the binary corresponding to your OS.
3.  Run the application:
    *   **Windows:** Double-click the `AI-Router-Blocker-AiO.exe`. Agree to the UAC prompt (required to edit the hosts file).
    *   **macOS / Linux:** Run from terminal using sudo:
        ```bash
        sudo ./AI-Router-Blocker-AiO
        ```
4.  Toggle the big button to activate or deactivate the system-level blocks.

---

## Option B — Run from Source Code

If you prefer to audit the code yourself and run it raw, you can clone and run with Python 3.10+.

```bash
# 1. Clone the repo
git clone https://github.com/Akunimal/AI-Router-Blocker-AiO.git
cd AI-Router-Blocker-AiO

# 2. Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install in development mode
pip install -e ".[dev]"

# 4. Launch the application
# Windows (auto-elevates via UAC):
python ai_blocker.py

# macOS / Linux (requires sudo):
sudo python3 ai_blocker.py
```

---

## Option C — Install via PyPI (pip)

DevGate is published as a Python package. You can install it globally or in any environment.

```bash
# Install the package
pip install devgate

# Run the app
devgate
```

---

## OS Privileges Guide

Because this application modifies the system `hosts` file to perform DNS override blocking, it requires elevated administrator rights:

| Platform | Privilege Model | Behavior |
|---|---|---|
| **Windows** | User Account Control (UAC) | The app embeds a manifest that automatically triggers the UAC prompt on launch. |
| **macOS** | Root / `sudo` | Must be launched with `sudo` from terminal. |
| **Linux** | Root / `sudo` | Must be launched with `sudo` from terminal. |
