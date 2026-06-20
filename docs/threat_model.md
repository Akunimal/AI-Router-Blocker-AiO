# Threat Model & Security Posture

As a DevSecOps utility that operates with elevated system privileges and manages network traffic, maintaining a rigorous security posture is critical. This document details our threat landscape and mitigation strategies.

---

## 1. Asset Definitions

*   **System Hosts File:** The principal target of modification. Corruption of this file can break system-wide DNS resolution.
*   **Developer API Keys:** Used by the DevSec Auditor to call OpenAI API endpoints.
*   **Local Network Traffic:** Intercepted requests flowing from the IDE to the local API gateway.
*   **App Configuration (`config.json`):** Holds user settings (selected profile, interface language, custom domain additions).

---

## 2. Threat Analysis & Mitigations

### Threat 1 — Privilege Escalation / Abuse
*   **Description:** An attacker attempts to exploit the elevated privilege check (`Administrator`/`root`) to run arbitrary shell commands on the developer's machine.
*   **Mitigation:** The application does not accept external scripting input and executes system utilities (`ipconfig`, `killall`, `taskkill`) using strict static arguments through `subprocess.run()`. No user-supplied command strings are evaluated or run inside system shells.

### Threat 2 — Hosts File Corruption
*   **Description:** A bug in the host engine corrupts the hosts file, deleting existing developer overrides (e.g. database routing shortcuts) or leaving the file unreadable.
*   **Mitigation:** The Hosts engine operates with an atomic read-clean-write cycle. It is restricted to modify lines that contain the `# AI-Block` comment tag. If the tag is absent on a line, it is preserved verbatim.

### Threat 3 — Developer API Key Leakage
*   **Description:** The developer's OpenAI key is persisted to disk, making it vulnerable to extraction by local malware or accidentally pushed to public repositories.
*   **Mitigation:** *Zero-Persistence BYOK.* API keys entered in the UI are held exclusively in volatile RAM. Before saving configurations to `config.json`, the `SENSITIVE_CONFIG_KEYS` filter explicitly strips keys out.

### Threat 4 — Local Port Hijacking
*   **Description:** The transparent gateway binds to a port, allowing other machines on the local area network (LAN) to route requests or hijack completions.
*   **Mitigation:** The `ThreadingHTTPServer` binds strictly to the loopback interface (`127.0.0.1`), ensuring the gateway is completely isolated from external network interfaces.

### Threat 5 — Supply Chain Attacks
*   **Description:** A malicious update to a third-party dependency compromises the build package.
*   **Mitigation:** The application is built with **zero runtime third-party dependencies**. It relies entirely on Python's standard library (`tkinter`, `urllib`, `ctypes`, `subprocess`).

### Threat 6 — Experimental Network Backend Misuse
*   **Description:** A user enables an experimental firewall/redirect backend and unintentionally applies broad or platform-specific network rules.
*   **Mitigation:** The hosts backend remains the default. Experimental backends require explicit CLI selection, expose dry-run command planning, and are documented separately from the stable runtime path. Kernel-level eBPF/WFP interception remains future work, not active behavior.

### Threat 7 — Prompt Injection & Payload Jailbreaks
*   **Description:** An attacker crafts a malicious codebase or pull request. When a developer uses an AI assistant to review or auto-complete the code, the assistant is subjected to a prompt injection, causing it to exfiltrate data or write malicious logic.
*   **Mitigation:** The Gateway is evolving to include **On-Device Semantic Guardrails**. By running a lightweight local model (e.g., ONNX Phi-3) to classify prompt intent *before* transmission, the Gateway can detect and drop payloads attempting to jailbreak the upstream AI provider.

### Threat 8 — Data Exfiltration via Agentic Loops
*   **Description:** Autonomous AI coding agents (e.g., AutoGPT) run with local execution rights. If compromised, they could systematically read configuration files (`.git/config`, `~/.aws/credentials`) and exfiltrate them through legitimate-looking API queries.
*   **Mitigation:** Upcoming eBPF telemetry integration will monitor file-read syscalls by IDE processes. Combined with **LLM-Powered Anomaly Explanation**, the Gateway will detect when an AI agent accesses sensitive files not related to its immediate coding context and sever its network access.

---

## 3. Privilege Isolation Matrix

| Component | Requires Elevation | Purpose |
|---|---|---|
| **GUI Layout & Tabs** | ❌ No | Renders Tkinter window. |
| **API Gateway Server** | ❌ No | Binds and listens on `127.0.0.1:8080`. |
| **Process Detection** | ❌ No | Queries running tasks via `ps` or `tasklist`. |
| **Hosts Writer** | ✅ Yes | Requires write access to write to `/etc/hosts` or `etc/hosts`. |
| **DNS Cache Flusher** | ✅ Yes | Requires rights to run flush commands. |
| **Firewall Redirect Backend** | ✅ Yes | Experimental opt-in backend; inspect with `--dry-run` before applying. |
