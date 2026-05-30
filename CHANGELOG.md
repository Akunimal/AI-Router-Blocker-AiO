# Changelog

All notable changes to this project will be documented in this file.

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
