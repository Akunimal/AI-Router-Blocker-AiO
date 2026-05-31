# AI DevSec Gateway v1.3.2

Version 1.3.2 is a product naming cleanup release. It replaces remaining in-app legacy product name references with AI DevSec Gateway so the desktop UI, tray, CLI, auditor prompt, and build scripts present a consistent product name.

## Downloads

| Operating System | Release Asset | Notes |
|---|---|---|
| Windows | `AI-Router-Blocker-AiO-Windows.exe` | Portable executable with UAC elevation for hosts-file access. |
| Linux | `AI-Router-Blocker-AiO-Linux` | Portable binary. Run with `sudo` to allow `/etc/hosts` edits. |
| macOS | `AI-Router-Blocker-AiO-macOS` / `AI-Router-Blocker-AiO-macOS.app.zip` | Portable binary and zipped app bundle. Run with root privileges when modifying `/etc/hosts`. |

## What's changed

### Product naming

- Main window title and header now use AI DevSec Gateway.
- Windows tray tooltip and hidden tray window name now use AI DevSec Gateway.
- CLI description and single-instance message now use AI DevSec Gateway.
- DevSec Auditor prompt now refers to AI DevSec Gateway.
- Build script banners now use AI DevSec Gateway.
- The first app tab is labeled `Blocker` instead of the legacy product name.

## Verification

- `python -m pytest -q`
- `python -m ruff check .`
- `python -m mypy ai_blocker`

## Requirements

| OS | Requirements |
|---|---|
| Windows | Windows 10/11, Administrator privileges through UAC. |
| Linux | Desktop Linux with Tkinter support, run as root via `sudo` for hosts-file changes. |
| macOS | macOS with Tkinter support, run with root privileges for hosts-file changes. |

MIT License. No telemetry, no ads, no monetization.
