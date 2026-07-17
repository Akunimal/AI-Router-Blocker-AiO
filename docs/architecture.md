# Architecture & Internal Flow

This document details the high-level architecture, design decisions, and internals of AI DevSec Gateway.

---

## System Overview

AI DevSec Gateway integrates three distinct engines under a unified user interface:

```
┌─────────────────────────────────────────────────────┐
│                  AI DevSec Gateway                  │
│                                                     │
│  ┌──────────────┐  ┌──────────┐  ┌──────────────┐  │
│  │ Hosts Engine │  │ API      │  │ DevSec       │  │
│  │ (DNS Override│  │ Gateway  │  │ Auditor      │  │
│  │  & Kill      │  │ (Proxy)  │  │ (LLM-powered)│  │
│  │  Switch)     │  │          │  │              │  │
│  └──────────────┘  └──────────┘  └──────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │                 GUI & CLI Interfaces         │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## Context Diagram (C4 Level 1)

```mermaid
graph TD
    Dev["Developer"] --> App["AI DevSec Gateway"]
    IDE["IDE / AI Editor<br>(Cursor, VS Code, etc.)"] --> Hosts["OS Hosts File"]
    Hosts --> Loopback["127.0.0.1<br>Connection Refused"]
    IDE --> Gateway["Local API Gateway<br>127.0.0.1:PORT"]
    Gateway --> LocalLLM["Local LLM<br>(Ollama / LM Studio)"]
    Gateway -.->|"Audit telemetry"| CloudAI["Cloud AI API<br>(OpenAI, Anthropic, etc.)"]
    App -->|"Modifies"| Hosts
    App -->|"Manages"| Gateway
    App -->|"Invokes"| CloudAI
```

---

## Module Breakdown

With the v1.2.1 package refactoring, logic is isolated into clean Python modules:

### 1. Network Backends (`network_backends.py`)
Defines the internal enforcement contract used by blocking workflows:
`activate(domains)`, `deactivate()`, and `status()`.

The production default is `HostsBackend`, which preserves the current hosts-file behavior. `FirewallRedirectBackend` is a non-kernel foundation that builds OS command plans through an injectable runner, making firewall/redirect behavior testable without changing machine network rules during unit tests.

Linux eBPF and Windows Filtering Platform (WFP) are future backend implementations behind this interface, not current runtime dependencies.

### 2. Hosts Engine (`block_actions.py` & `system_utils.py`)
Responsible for reading the OS hosts file (`/etc/hosts` or `System32\drivers\etc\hosts`), removing any previous configurations containing the `# AI-Block` tag, and writing fresh rules mapping blocked domains to `127.0.0.1`.
After editing, it calls system executables (`ipconfig /flushdns`, `resolvectl`, `dscacheutil`) to silently flush the system DNS cache.

### 3. Local Proxy Gateway (`gateway.py`)
Uses standard library HTTP handlers (`BaseHTTPRequestHandler`) to spin up a threaded proxy server. It captures outbound requests (GET, POST, PUT, PATCH, DELETE, OPTIONS) and forwards them to a configured URL (e.g. `http://localhost:11434` for Ollama).
*   **SSE Streaming Support:** Features streaming response redirection in 1KB chunks to preserve Server-Sent Events (SSE) for real-time editor completion lists.
*   **Request Body Preservation:** For mutating methods, request bodies are forwarded whenever `Content-Length` is present, including DELETE requests from REST clients.
*   **Zero-Dependency:** Uses `urllib.request` exclusively, avoiding dependency bloat.
*   **TLS Status:** The current gateway does not terminate TLS or perform DPI. Root CA generation, trust-store installation, and surgical HTTPS endpoint filtering remain planned Phase 2 work.

### 4. Active Process Monitor (`block_actions.py`)
Uses subprocess pipelines (`tasklist` on Windows, `ps -A` on Unix) to scan running system processes every 3 seconds, alerting users if blocked applications (like Cursor, Windsurf, or Copilot node processes) are active.

---

## Core Execution Flow

```mermaid
flowchart TD
    A["User clicks BLOCK / CLI Trigger"] --> B["force_close_processes()"]
    B --> C["Kill active AI editors<br>(taskkill/killall)"]
    C --> D["Read hosts file"]
    D --> E["Remove existing # AI-Block lines"]
    E --> F["Write new block entries<br>for selected categories"]
    F --> G["flush_dns()"]
    G --> H["Update UI state / Output status"]
```

---

## 5. DLP & Guardrails Pipeline

The gateway integrates three layers of content inspection that form a configurable security pipeline:

```
Request Body
    |
    v
[1. DPI Rules Engine]  -->  Block if DPI rule matches (URL/path patterns)
    |
    v
[2. DLP Engine]        -->  Scan & Redact sensitive data (secrets, PII, licenses)
    |                        Optional: escalate to Cloud Semantic DLP
    v
[3. Prompt Guardrail]  -->  Block if injection/jailbreak detected
    |
    v
Forward to upstream
```

### 5.1 DLP Engine (`dlp_engine.py`)

The `DLPEngine` class scans text with regex patterns across five categories:

| Category | Examples | Default |
|---|---|---|
| `scan_secrets` | API keys, AWS keys, GitHub tokens, JWTs, private keys | Enabled |
| `scan_cloud_tokens` | GCP (ya29.), HuggingFace (hf_), Slack (xox*), npm, Azure keys | Enabled |
| `scan_db_strings` | PostgreSQL, MySQL, MongoDB, Redis connection URIs | Enabled |
| `scan_pii` | Emails, SSNs, credit cards, phone numbers | Enabled |
| `scan_licenses` | GPL/AGPL/LGPL license headers | Disabled |
| `scan_internal_ips` | RFC 1918 addresses (10.x, 172.16-31.x, 192.168.x) | Disabled |
| `scan_env_vars` | os.environ/process.env references, export statements | Disabled |

Scanning methods:
- `scan(text)` - return all findings
- `scan_for_secrets(text)` - secrets/cloud tokens only
- `scan_for_pii(text)` - PII only
- `redact(text, findings)` - replace matches with `[REDACTED:<TYPE>]` placeholders
- `has_sensitive_data(text)` - boolean check

### 5.2 Prompt Guardrail (`guardrails.py`)

The `PromptGuardrail` class evaluates prompts for security threats:

| Pattern Set | Examples | Weight Range |
|---|---|---|
| Injection | "ignore previous instructions", "system prompt extraction" | 0.80-0.95 |
| Jailbreak | "DAN mode", base64 smuggling, token smuggling | 0.40-0.90 |
| Leetspeak bypass | "1gn0r3", "d4n m0d3", obfuscated wording | 0.70-0.85 |
| IP leak | data exfiltration URLs, pastebin/gist links | 0.50-0.85 |

The guardrail returns a `GuardrailResult` with category, risk score (0.0-1.0), matched patterns, and explanation. A configurable threshold (default 0.60) determines when to block.

### 5.3 Pipeline Integration (`gateway.py`)

The gateway handler applies these checks in `_proxy_request()`:

1. **DPI Rules** (`_get_dpi_engine`): Match request URL/path against configured patterns. Block with 403 if matched.
2. **DLP Scan** (`_apply_dlp`): Scan request body for sensitive data. Redact findings before forwarding. Log redaction events to `AuditLog`.
3. **Guardrail Check** (`_check_guardrails`): Evaluate prompt for injection/jailbreak. Block with 451 if risk score exceeds threshold.

All three layers can be individually toggled via server attributes:
- `server.dlp_enabled` (boolean, default True)
- `server.guardrails_enabled` (boolean, default True)
- `server.dpi_engine` (DPIRuleEngine instance or None)

### 5.4 Cloud-Assisted Semantic DLP (planned)

The roadmap includes an optional `SemanticDLPClient` that escalates ambiguous findings to OpenAI API for deep semantic classification. See ROADMAP.md for details.

