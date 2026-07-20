# Changelog

All notable changes to this project will be documented in this file.


## [Unreleased]
### Added
- Dry-run mode visual in GUI with toggle, plan preview, and toast notifications. (Wave 5.1)
- HostsBackend plan_activate/plan_deactivate methods for dry-run command previews.

### Changed
- Bump version to 1.8.0 for Wave 5 release.
- pyproject.toml synchronized with __init__.py version (1.8.0).

### Fixed
- [Bug #1] HostsBackend missing plan_activate/plan_deactivate methods.
- [Bug #2] Dry-run mode executing _update_visuals(), _refresh_editors_label(), _run_connectivity_check().
- [Bug #3] Dry-run mode modifying category_vars as side-effect.
- [Bug #4] Hardcoded "Dry-Run Preview" string lacking i18n support.
- [Bug #5] _handle_reapply_block not respecting dry-run mode.

## [v1.7.0] - 2026-07-17
### Added
- DLP & Guardrails UI panel: live findings table with refresh, DLP toggle, guardrails toggle, /findings endpoint. (3.5)
- Token usage dashboard: cap display, total consumption, usage% with color-coded thresholds in UI. (4.2)
- Token cap configuration: configurable usage limit, hourly enforcement, percentage display. (4.2)
- Cloud-Assisted Semantic DLP with LRU result cache and escalation protocol.
- Hybrid DLP mode UI controls (toggle, API key entry, test button).
- AI-Powered Threat Intelligence: request pattern analyzer, recursive loop detection, alerting system.
- Threat intelligence dashboard UI with status indicators and auto-refresh.
- On-Device ONNX Guardrail pipeline with fallback chain (ONNX -> Heuristic -> Allow).
- Integration tests for DLP+Guardrails+TokenMonitor pipeline in gateway. (3.6)
- TokenMonitor flag check and per-request token tracking in gateway. (3.3)
- Renamed project from AI DevSec Gateway to CodeGate for cleaner branding.

### Changed
- GatewayHandler now integrates DLP scanning (redact/block), PromptGuardrail (classify/reject), and TokenMonitor (track caps) in end-to-end proxy flow. (3.1-3.3)
- CLI now accepts --dlp, --guardrails, --token-monitor flags with config persistence. (3.4)
- DLP engine now supports optional escalation to cloud semantic analysis.
- Gateway configuration includes Cloud DLP enable/disable flag.
- All documentation, package metadata, and CLI commands updated to CodeGate branding.
- ROADMAP updated: Phase 3 progress at 30%, all Wave 2 items complete.



## [v1.6.1] - 2026-07-17
### Added
- DLP audit logging enhanced with per-finding metadata (finding type, confidence, position), scan duration, and request body hash.
- DLP performance metrics and circuit breaker: tracks total scans, findings by type, redacted/blocked/passed counts; auto-opens after 3 slow scans (>500ms), retries after 60s.
- DLPMetrics dataclass with to_dict() serialization exposed via /stats endpoint.

### Changed
- DLP findings now include full detail in audit log entries instead of just count.
- _log_audit accepts dlp_findings list and body for request hash computation.
- Bumped version to 1.6.1.

## [v1.6.0] - 2026-07-17
### Added
- Real-time DLP engine with regex patterns for API keys, cloud credentials, PII, private keys, JWT, credit cards, and more.
- Configurable DLP policies with per-domain/route overrides (REDACT, BLOCK, LOG_ONLY, PASS_THROUGH).
- Structured JSON redaction preserving payload structure.
- DLPPolicy and DLPPolicyManager for persistent YAML-based policy configuration.
- Circuit breaker pattern for DLP metrics (tracking).
- Initial DLP engine tests covering scan, redact, redact_structured.

### Changed
- Gateway integrates DLP pipeline: _apply_dlp with policy resolution, circuit breaker checks, and audit logging.
- Bumped version to 1.6.0.

## [v1.5.0] - 2026-07-16
### Added
- Exposed /stats HTTP endpoint on the Local API Gateway returning hourly token summary and per-domain breakdown as JSON.
- Added comprehensive test coverage for /stats endpoint (200 with data, 503 when monitor unavailable, non-interference with normal proxy routes).
- Added DLP and guardrails toggle flags in gateway configuration with corresponding test coverage.
- Gateway coverage improved from 76% to 82%.

### Changed
- Bumped version to 1.5.0.

## [v1.4.2] - 2026-06-20
### Fixed
- Fixed rate limiting logic in the Local API Gateway where GET requests completely bypassed token checks.
- Fixed bidirectional HTTPS proxy tunnel timeout, increasing it from 10 to 300 seconds to prevent premature disconnections during long streaming generations.
- Fixed missing telemetry and audit logging for failed HTTP API requests (e.g. 400 Bad Request, 500 Internal Server Error).
- Fixed Content-Length calculation during DPI and guardrail block responses to properly account for UTF-8 byte lengths.
- Fixed static type checking (mypy) warnings in `domain_matcher.py` and `token_monitor.py`.

## [v1.3.2] - 2026-05-31
### Fixed
- Replaced remaining in-app legacy product name references with CodeGate.

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
