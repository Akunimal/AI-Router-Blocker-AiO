# 🗺️ AI DevSec Gateway - Roadmap

Welcome to the future of **AI DevSec Gateway** (formerly AI Network Blocker). Our goal is to create the ultimate open-source, privacy-first DevSecOps Gateway for developers navigating the AI era.

This roadmap outlines our technical vision, showing our completed work and upcoming milestones.

---

## 📅 Roadmap Overview

| Phase | Description | Timeline | Progress |
|---|---|---|---|
| **Phase 0** | Core Desktop Blocker & i18n | Q1 2026 | `██████████` 100% |
| **Phase 1** | Modularization, CLI & Multi-Provider | Q2 2026 (Current) | `██████████` 100% |
| **Phase 2** | Network Backend Abstraction, Firewall Redirects & TLS Decryption | Q3 2026 | `██░░░░░░░░` 20% |
| **Phase 3** | DLP Sanitization & Real-time Semantic Guardrails | Q4 2026 | `░░░░░░░░░░` 0% |
| **Phase 4** | System Daemons, TPM 2.0 & Enterprise MDM | Q1 2027 | `░░░░░░░░░░` 0% |
| **Phase 5** | Confidential Computing & eBPF Telemetry | Q2 2027 | `░░░░░░░░░░` 0% |

---

## ✅ Phase 0: Core Desktop Blocker (Completed - v1.0 - v1.1)
- [x] **Cross-platform UI:** Built with Tkinter using a premium Catppuccin Mocha theme.
- [x] **Hosts File Engine:** Modify `/etc/hosts` and flush DNS silently across Windows, Linux, and macOS.
- [x] **Active Process Killer:** Scan and terminate active editor processes to prevent background data leaks.
- [x] **Internationalization (i18n):** Extracted translations supporting 10 languages with auto OS detection.

## 🚀 Phase 1: Modularization, CLI & Gateway (Completed - v1.2 - v1.2.1)
- [x] **Modular Package Refactoring:** Broke down the 92KB monolith into single-responsibility package submodules (config, constants, system_utils, block_actions, gateway, tray, ui).
- [x] **Headless CLI Interface:** Implemented pure terminal CLI argument parsing (`--block`, `--unblock`, `--status`) for scripting and headless servers.
- [x] **Package Manager Distribution:** Added Homebrew tap formulas and Scoop JSON manifests for developer installations.
- [x] **Local API Router (BYOK):** Intercept and transparently proxy requests to Ollama/LM Studio or custom endpoints.
- [x] **OpenAI DevSec Auditor:** Live process auditing via OpenAI API to find open leaks and suggest mitigation.
- [x] **Custom Domain Additions:** Interactively add domains to local configuration settings.
- [x] **Granular Category Toggles:** Profile-level category selectors (Work, Personal, Free) to control block scopes.

## 🧪 Phase 2: Network Interception & HTTPS TLS Decryption (v1.3 - v1.5)
- [x] **Internal Network Backend Interface:**
  * Introduce a pluggable backend boundary so hosts-file blocking, firewall redirects, and future kernel-level interceptors can be implemented behind the same activate/deactivate/status contract.
  * Keep the hosts-file backend as the default behavior for existing GUI and CLI workflows.
- [x] **Non-kernel Firewall/Redirect Backend Foundation:**
  * Add a testable backend that can plan and execute OS firewall/redirect commands through an injectable command runner.
  * Treat firewall redirects as an intermediate layer before kernel drivers, not a replacement for eBPF/WFP.
- [ ] **Deep Packet Inspection (DPI) & TLS Decryption:**
  * Build on-the-fly local Root Certificate Authority (CA) generator.
  * Integrate generated CA certificates automatically into OS trust stores (Windows Registry, macOS Keychain, Linux ca-certificates) and specific IDE trust chains.
  * Surgical endpoint blocking (e.g. block `/v1/chat/completions` payload transmissions while keeping `/v1/models` structural reads open).
- [ ] **Kernel-Level Socket Redirection:**
  * **Linux:** Implement eBPF (Extended Berkeley Packet Filter) socket filters to redirect TCP ports `443` for specific AI IP subnets directly at the kernel layer, eliminating hosts file dependency.
  * **Windows:** Develop a Windows Filtering Platform (WFP) network driver to intercept outbound connections programmatically.
  * eBPF and WFP are future backend implementations behind the internal network backend interface.
- [ ] **Dynamic Regular Expression Domain Matching:** Real-time wildcard resolution for dynamic content delivery networks (CDNs).

## 📊 Phase 3: DLP Sanitization & Real-Time Semantic Guardrails (v1.6 - v1.7)
- [ ] **Real-Time DLP Sanitization Pipeline (Data Loss Prevention):**
  * Parse prompt request bodies on the fly (before forwarding) using regex and heuristics.
  * Auto-strip or redact secrets, access keys (API tokens, AWS keys), personally identifiable info (PII/SSNs), or proprietary source files with conflicting copyleft licenses (e.g., GPL code blocks in closed-source repos).
- [ ] **Token Traffic Monitor:** Live visualization dashboard detailing input/output token counts, throughput, and hourly expenditure caps.
- [ ] **Differential Privacy Context Anonymizer:** Heuristically mask structural variable names and function layouts in code payloads before forwarding to cloud models.
- [ ] **Local Audit Tracing:** Log exact prompt history locally in SQLite with JSON search queries.
- [ ] **On-Device Semantic Guardrails & Prompt Injection Firewall:**
  * Embed a lightweight ONNX runtime engine to run quantized models (e.g., Phi-3-mini or Llama-3-8B-Instruct) locally for real-time prompt safety classification with <15ms latency.
  * Block active prompt injections, jailbreak payloads, and sensitive intellectual property (IP) leaks.
  * Integrate vector database search (e.g., local FAISS/USearch) to match outbound code snippets against proprietary or patent-protected IP blocks before transmission.

## 🛡️ Phase 4: System Daemons, TPM 2.0 & Enterprise MDM (v2.0+)
- [ ] **Hardware Security Integration (TPM 2.0 / Secure Enclave):**
  * Bind proxy authorization keys, local CA private keys, and auditor credentials securely to hardware TPM 2.0 modules or Apple Secure Enclave coprocessors.
- [ ] **System Daemons:** Run core proxy routing servers as headless background daemons (`systemd` units / Windows Service).
- [ ] **Zero-Knowledge Code Proofs:** Explore offline validation architectures to verify code structures locally without sending code tokens.
- [ ] **Autonomous Agent Throttling & Network Quarantine:**
  * Detect recursive loop patterns and anomalous request frequencies from AI coding agents (e.g. Devin, AutoGPT).
  * Enforce automated rate-limiting, cooldown policies, and network quarantine of agent containers when limits are exceeded.
- [ ] **Centralized Enterprise Policies:** Ready-to-deploy MDM, GPO, and plist profiles to easily distribute security rules across distributed engineering teams.
- [ ] **Cryptographically Verifiable Audit Logs:**
  * Build an append-only Merkle tree ledger of audit logs, signing each block locally to prevent tampering by developers with local administrator privileges.

## 🔒 Phase 5: Confidential Computing & eBPF Telemetry (v3.0+)
- [ ] **Trusted Execution Environments (TEEs):**
  * Deploy the gateway proxy within hardware-isolated confidential virtual machines (Intel SGX, AMD SEV) for secure enterprise cloud relays.
- [ ] **eBPF-based Syscall Telemetry & Process Sandboxing:**
  * Use eBPF kernel telemetry to trace file-read syscalls by IDE processes to detect exfiltration of sensitive configuration (`.git/config`, `.env`) files.
  * Enforce zero-trust sandbox policies restricting execution context of IDE extensions.
- [ ] **Homomorphic Proxy Routing:**
  * Investigate prefix-matching and routing of encrypted prompt tokens using homomorphic encryption or secure multi-party computation, preventing raw text decryption.

---

*Note: This roadmap is a living document. Priorities may shift based on community feedback and open-source contributions. We welcome PRs for any of the features listed above!*
