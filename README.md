# 🛡️ CodeGate

> **Local gateway for AI developer traffic: block, route, audit, and protect locally.**

[![Python Version](https://img.shields.io/badge/Python-3.10%20|%203.11%20|%203.12%20|%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-0078D4?logo=windows&logoColor=white)](https://github.com/Akunimal/CodeGate#readme)
[![Test Suite Status](https://github.com/Akunimal/CodeGate/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Akunimal/CodeGate/actions/workflows/test.yml)
[![Security Scan Status](https://github.com/Akunimal/CodeGate/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/Akunimal/CodeGate/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/Akunimal/CodeGate/graph/badge.svg)](https://codecov.io/gh/Akunimal/CodeGate)
[![License](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)

[English](README.md) | [Español](README.es.md)

---

## What is this?

**CodeGate** is an open-source privacy and DevSecOps tool for developers adopting AI coding assistants. It provides local controls to block known AI endpoints, route API traffic to local inference servers, and audit active AI editor processes.

Originally created as a simple GUI to block AI endpoints, it is evolving into a **Zero-Trust Gateway** for safer AI-assisted development. The current release focuses on deterministic hosts-file blocking, a local HTTP router, safe-by-default CLI controls, and a security auditor that keeps API keys in memory only.

1. **Block:** A deterministic OS-level override via the hosts file that drops connections to 38+ known AI domains.
2. **Route:** A local HTTP proxy that can route compatible API clients to local LLMs such as Ollama, LM Studio, or vLLM.
3. **Audit:** Process-aware security checks that help identify active AI tools and data-leak risk signals.
4. **Protect:** Real-time DLP sanitization, semantic guardrails, and token usage monitoring for AI-assisted development.

---

## Features

| Feature | Description |
|---|---|
| Live Token Dashboard | Real-time token in/out and request counts with auto-refresh every 5s. Fetch stats via /stats HTTP endpoint. |
| DLP & Guardrails UI Panel | Live findings panel with refresh button, toggles for DLP and semantic guardrails per-session. |
| Transparent API Router | Seamlessly reroute Copilot/Cursor HTTP traffic to your own Local LLM inference servers. |
| AI DevSec Auditor | Live process analysis with on-demand AI recommendations. API keys are memory-only, never persisted. |
| Native CLI Interface | Full headless control for CI/CD environments: codegate --status, codegate --block. |
| Deterministic Kill Switch | Hard OS-level blocking through managed hosts entries. No reliance on remote DNS filtering. |
| Universal Distribution | Install via pip, brew, scoop, or as a portable single-file binary. |
| Multilingual GUI | Catppuccin Mocha interface with 10 supported languages and smart OS elevation (UAC/sudo). |
| Data Loss Prevention (DLP) | Regex-based redaction/blocking of API keys, cloud credentials, PII, private keys, JWT, DB URIs, and more. |
| Configurable DLP Policies | Per-domain and per-route policies: REDACT, BLOCK, LOG_ONLY, PASS_THROUGH with circuit breaker. |
| Cloud-Assisted Semantic DLP | Optional AI integration for deep semantic analysis of low-confidence DLP findings with LRU cache. |
| AI-Powered Threat Intelligence | Request pattern analyzer, recursive loop detection, anomaly alerting for autonomous AI agents. |
| On-Device ONNX Guardrails | Lightweight ONNX runtime (Phi-3-mini) for real-time prompt safety classification with fallback chain. |
| CLI Flags for DLP/Guardrails | --dlp, --guardrails, --token-monitor flags with config persistence for headless CI/CD. |
| Enhanced Audit Logging | Granular per-finding audit trail with metadata (domain, endpoint, categories, scan time, request hash). |
| Token Cap & Usage Dashboard | Token usage cap, total consumption and percentage display with color-coded thresholds in UI. |

---

## Data Loss Prevention (DLP)

CodeGate includes a built-in DLP engine that inspects all outbound API traffic for sensitive data before it leaves your network. The DLP engine supports optional Cloud-Assisted Semantic Analysis via AI API for deep semantic inspection of low-confidence regex findings, with an LRU result cache to avoid redundant analysis and a configurable escalation protocol for hybrid local+cloud detection.

### Detection Categories

| Category | Examples | Default Action |
|---|---|---|
| API Keys and Tokens | OpenAI sk-*, Anthropic sk-ant-*, GitHub ghp_*, xoxb-* | REDACT |
| Cloud Credentials | AWS keys, GCP tokens, Azure secrets, DigitalOcean, Heroku | REDACT |
| PII | Emails, US SSN, credit cards, phone numbers | REDACT |
| Private Keys | RSA/EC/DSA/OpenSSH private keys | BLOCK |
| Cloud DLP | AI-powered semantic analysis of low-confidence findings | ESCALATE |
| JWT Tokens | JSON Web Tokens (eyJ.) | REDACT |
| Internal IPs | RFC 1918 addresses (10.x, 172.16-31.x, 192.168.x) | LOG_ONLY |
| License Conflicts | AGPL-3.0, GPL-3.0 copyleft license headers | LOG_ONLY |
| DB Connection Strings | PostgreSQL, MySQL, MongoDB, Redis URIs | REDACT |
| Environment Variables | AWS_SECRET_ACCESS_KEY, DB_PASSWORD, API_KEY references | LOG_ONLY |

### DLP Policies

- **REDACT** (default): Replace sensitive content with [REDACTED] while preserving structure
- **BLOCK**: Return 403 and prevent the request from being sent
- **LOG_ONLY**: Log findings without modifying the request
- **PASS_THROUGH**: Skip DLP entirely for trusted domains

---

## Guardrails & Threat Intelligence

CodeGate includes multi-layered prompt safety classification with automatic fallback chain: ONNX runtime (Phi-3-mini) > heuristic classifier > allow. The AI-Powered Threat Intelligence module detects autonomous AI agent anomalies, recursive loops, and suspicious request patterns.

| Layer | Technology | Latency |
|---|---|---|
| Primary | ONNX Phi-3-mini (local) | <15ms |
| Fallback | Heuristic pattern matching | <2ms |
| Threat Intel | Request pattern analyzer | Real-time |

---

## Token Monitoring

The built-in TokenMonitor tracks per-request token usage (in/out), aggregates hourly summaries, and enforces configurable caps. The live dashboard in the GUI displays:

- **Tokens In / Out** per request and cumulative
- **Total Consumption** with hourly breakdown
- **Request Count** tracked per domain
- **Usage Cap** configurable limit (0 = unlimited)
- **Usage Percentage** color-coded (green <50%, yellow <80%, red >80%)

---

## Supported Providers

The default interception engine targets 38+ domains across major providers: OpenAI, Anthropic, GitHub Copilot, Google AI, Microsoft, Meta AI, Mistral, DeepSeek, xAI, and more.

The blocklist is dynamically configurable via ai_blocker/constants.py.

---

## Quick Start

### 1. Python Package (Pip)

```bash
pip install codegate

codegate --status
codegate --block
codegate --unblock
```

### 2. Package Managers

**macOS (Homebrew):**
```bash
brew tap Akunimal/codegate https://github.com/Akunimal/CodeGate
brew install codegate
sudo codegate --status
```

**Windows (Scoop):**
```powershell
scoop bucket add codegate https://github.com/Akunimal/CodeGate.git
scoop install codegate
codegate --status
```

### 3. Portable GUI Binaries

1. Visit the [Releases](https://github.com/Akunimal/CodeGate/releases) page.
2. Download the executable for your OS (.exe, macOS binary, or Linux AppImage).
3. Run the application (auto-requests Admin/sudo when toggling the network switch).

---

## Security Model

- **Zero-Persistence BYOK:** API keys are strictly kept in-memory. Never written to disk.
- **Surgical OS Modifications:** Targeted parsing injects AI-Block markers into the OS hosts file. Absolute isolation from existing DNS mappings.
- **Isolated Telemetry:** Zero tracking, analytics, or hidden phone-home mechanics.

---

## Architecture

CodeGate operates at the boundary between your local development environment and the cloud. For in-depth details on modular structure, Deep Packet Inspection (DPI), and threat models, read the [Architecture Documentation](docs/architecture.md).

---

## Roadmap and Future Vision

- Data Loss Prevention (DLP) - *Implemented in v1.6.0*
- Cloud-Assisted Semantic DLP - *Implemented in v1.6.0*
- On-Device Semantic Guardrails (ONNX Phi-3-mini) - *Implemented in v1.7.0*
- AI-Powered Threat Intelligence - *Implemented in v1.7.0*
- Token Traffic Monitor Dashboard - *Implemented in v1.7.0*
- DLP & Guardrails UI Panel with Live Findings - *Implemented in v1.7.0*
- CLI Flags for DLP/Guardrails/TokenMonitor - *Implemented in v1.7.0*
- eBPF Kernel Telemetry (detect.git/config exfiltration at kernel level)
- Confidential Computing (Trusted Execution Environments like Intel SGX)
- Dry-Run Mode in GUI

See [ROADMAP.md](ROADMAP.md) for the full vision.

---

## Open Source and Governance

Security tools must be 100% transparent. This project is built under strict open-source governance:
- [Architecture Guide](docs/architecture.md)
- [Contributing Guide](CONTRIBUTING.md)
- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Security Policy](SECURITY.md)
- [License: MIT](LICENSE)

---

> Audit the unseen. Route the restricted. Trust no packets.