# Changelog

All notable changes to this project will be documented in this file.

## [v1.4.2] - 2026-06-20
### Fixed
- Fixed rate limiting logic in the Local API Gateway where GET requests completely bypassed token checks.
- Fixed bidirectional HTTPS proxy tunnel timeout, increasing it from 10 to 300 seconds to prevent premature disconnections during long streaming generations.
- Fixed missing telemetry and audit logging for failed HTTP API requests (e.g. 400 Bad Request, 500 Internal Server Error).
- Fixed Content-Length calculation during DPI and guardrail block responses to properly account for UTF-8 byte lengths.
- Fixed static type checking (mypy) warnings in `domain_matcher.py` and `token_monitor.py`.

## [v1.3.2] - 2026-05-31
### Fixed
- Replaced remaining in-app legacy product name references with AI DevSec Gateway.

## [v1.3.1] - 2026-05-31
### Changed
- Documented the Local API Gateway's supported HTTP methods and request body forwarding behavior.

### Fixed
- Fixed the Local API Gateway so PUT, PATCH, and DELETE requests are proxied instead of being rejected by the base HTTP handler.
- Fixed the `mypy ai_blocker` baseline by annotating translation globals and using a typed platform-specific tray alias.
- Fixed the UI window title to use the package version instead of a hardcoded release string.

## [v1.2.1] - 2026-05-30
### Changed
- Updated the release workflow so pushes and pull requests build CI artifacts without publishing to an existing GitHub Release.
- Release publishing now happens only from published releases or an explicit manual workflow dispatch with release publishing enabled.

### Fixed
- Prevented the DevSec Auditor OpenAI API key from being persisted to `config.json`.
- Added runtime support for pre-filling the auditor key from `OPENAI_API_KEY`.
- Clarified the English release documentation for the three OS build artifacts.

## [v1.2.0] - 2026-05-30
### Added
- Added keyboard shortcuts (Ctrl+B to toggle block, Ctrl+Q to quit, Ctrl+L to toggle log panel).
- Added a "Copy Log" button to quickly copy the activity log to the clipboard.
- Display elapsed time since the last block toggle directly in the status card UI.
- Added xAI (Grok) domains to the blocklist.

### Fixed
- Fixed a bug in the button color animation during state transitions.

## [v1.1.4] - 2026-05-30
### Added
- Implemented selective category blocking allowing users to toggle individual AI service categories.
- Added blocking profiles (Work, Personal, Free, Custom) with a dropdown selector in the header.
- Implemented Windows system tray minimization with context menu toggle and state-colored tray icons.
- Added "Start with Windows" option for persistent autostart blocking.
- Implemented custom domain addition ("+") with local JSON configuration storage.
- Added smooth color fade transitions between PROTECTED and EXPOSED states.
- Replaced blocking modal dialogs with non-intrusive, dynamic-height, auto-dismissible toast notifications.
- Added a collapsible, scrollable Activity Log panel that persists action logs in config JSON.
- Implemented active background connectivity verification (DNS + TCP socket check to `api.openai.com`) with offline state handling.
- Generated custom Catppuccin themed shield and padlock icons (`icon.ico`, `icon_green.ico`, `icon_red.ico`).
- Extracted and separated internationalization strings from code into `translations.json`.
- Dynamic workflow release tags in GitHub Actions.

## [v1.1.3] - 2026-05-30
### Added
- Implemented real-time polling (every 3 seconds) for the active AI editors warning in the footer.
- Optimized process scanning using single-pass `tasklist` (Windows) and `ps` (Unix) to drastically reduce CPU usage during background polling.

## [v1.1.2] - 2026-05-30
### Added
- Added Single Instance Lock (mutex on Windows, flock on Unix) to prevent multiple instances from causing race conditions.

### Changed
- Replaced deprecated `locale.getdefaultlocale()` with modern environment variable checks and `locale.getlocale()` for Python 3.11+ compatibility.
- Optimized I/O operations by combining hosts file reads into a single pass at startup.

## [v1.1.1] - 2026-05-30
### Fixed
- Fixed substring matching bug in `activate_block` preventing false negative domain blocks (e.g., `openai.com` bypassed if `api.openai.com` was already in hosts).
- Fixed UAT elevation bug on Windows causing duplicated launch arguments when frozen.
- Fixed `ctypes` NameError on Linux/macOS inside language detection function.

## [v1.1.0]
### Added
- Added cross-platform support for Linux and macOS (hosts file editing and process killing).
- Added bilingual comments (EN/ES) to source code.

## [v1.0.1]
### Fixed
- Corrected application version display to v1.0.1.

## [v1.0.0]
### Added
- Premium UI with Catppuccin Mocha colors and modern Tkinter widgets.
- 10-language support with automatic OS language detection and UI selector.
- Auto-UAC elevation for Windows.
- Background scanning for active AI editor processes.
- Silent DNS cache flushing after modifying the hosts file.
- Initial `.exe` build scripts and standalone executable support.
