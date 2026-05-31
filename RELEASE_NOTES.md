# AI DevSec Gateway v1.3.1

Version 1.3.1 is a gateway compatibility and type-checking maintenance release. It fixes REST method proxying in the Local API Gateway, documents the supported HTTP behavior, and restores a clean `mypy ai_blocker` baseline.

## Downloads

| Operating System | Release Asset | Notes |
|---|---|---|
| Windows | `AI-Router-Blocker-AiO-Windows.exe` | Portable executable with UAC elevation for hosts-file access. |
| Linux | `AI-Router-Blocker-AiO-Linux` | Portable binary. Run with `sudo` to allow `/etc/hosts` edits. |
| macOS | `AI-Router-Blocker-AiO-macOS` / `AI-Router-Blocker-AiO-macOS.app.zip` | Portable binary and zipped app bundle. Run with root privileges when modifying `/etc/hosts`. |

## What's changed

### Local API Gateway

- PUT, PATCH, and DELETE requests are now proxied instead of being rejected by the base HTTP handler.
- DELETE request bodies are preserved when `Content-Length` is present.
- Gateway architecture docs now list all supported HTTP methods and request body forwarding behavior.

### Type checking

- `mypy ai_blocker` now passes cleanly.
- Translation globals are explicitly typed.
- Windows tray support uses a typed platform-specific implementation alias.
- The UI window title now reads the package version instead of a hardcoded release string.

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
