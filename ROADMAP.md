# 🗺️ AI DevSec Gateway - Roadmap

Welcome to the future of **AI DevSec Gateway** (formerly AI Network Blocker). Our goal is to create the ultimate open-source, privacy-first DevSecOps Gateway for developers navigating the AI era.

This roadmap outlines our technical vision, showing our completed work, upcoming milestones, and our commitment to using AI to secure and maintain the project itself.

---

## 📅 Roadmap Overview

| Phase | Description | Timeline | Progress |
|---|---|---|---|
| **Phase 0** | Core Desktop Blocker & i18n | Q1 2026 | `██████████` 100% |
| **Phase 1** | Modularization, CLI & Multi-Provider | Q2 2026 (Current) | `██████████` 100% |
| **Phase 2** | Network Backend Abstraction, Firewall Redirects & TLS Decryption | Q3 2026 | `██████████` 100% |
| **Phase 3** | DLP Sanitization, Hybrid Guardrails & Threat Intel | Q4 2026 | `░░░░░░░░░░` 0% |
| **Phase 4** | System Daemons, TPM 2.0 & Enterprise Compliance | Q1 2027 | `░░░░░░░░░░` 0% |
| **Phase 5** | Confidential Computing & eBPF Telemetry Analysis | Q2 2027 | `░░░░░░░░░░` 0% |

---

## 🔄 Continuous Track: AI-Assisted DevSecOps & Maintenance

We believe in *dogfooding* and leveraging AI to secure and accelerate our own development. This ongoing track operates parallel to all phases, ensuring the gateway is hardened using the best available AI tools.

- **AI-Driven Security Reviews:** Automated AI reviews on pull requests focused on detecting security regressions, unsafe subprocess usage, and cross-platform network operation vulnerabilities.
- **AI-Generated Regression Fuzzing:** Using AI to generate robust, edge-case regression tests for privileged operations (hosts file manipulation, OS firewall rules, and TLS certificate injection).
- **Automated Issue Triage & Repro:** Leveraging AI to analyze community bug reports, reproduce platform-specific failures (e.g., Windows WFP vs Linux eBPF nuances), and draft focused fixes.
- **Secure Dogfooding:** The gateway is built using AI coding assistants, and we actively use our own gateway to audit, sanitize, and protect our development traffic from accidental IP leaks.

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

## 🧪 Phase 2: Network Interception & HTTPS TLS Decryption (Completed - v1.3 - v1.5)
- [x] **Internal Network Backend Interface:** Pluggable backend boundary for hosts-file, firewall redirects, and kernel-level interceptors.
- [x] **Non-kernel Firewall/Redirect Backend Foundation:** Injectable command runner for OS firewall rules as an intermediate layer.
- [x] **Deep Packet Inspection (DPI) & TLS Decryption:** On-the-fly local Root CA generator and OS trust store integration for surgical endpoint blocking (e.g., `/v1/chat/completions`).
- [x] **Kernel-Level Socket Redirection:** eBPF (Linux) and WFP (Windows) foundations to redirect TCP ports `443` at the kernel layer.
- [x] **Dynamic Regular Expression Domain Matching:** Real-time wildcard resolution for dynamic content delivery networks (CDNs).

## 📊 Phase 3: DLP Sanitization, Hybrid Guardrails & Threat Intel (v1.6 - v1.7)
- [ ] **Real-Time DLP Sanitization Pipeline:** Regex and heuristic parsing of prompt request bodies to redact secrets, keys, PII, and proprietary source code before forwarding.
- [ ] **Cloud-Assisted Semantic DLP (Hybrid Mode):** Optional integration with OpenAI API for deep semantic analysis of prompts when local heuristics require escalation to detect complex IP leaks.
- [ ] **AI-Powered Threat Intelligence:** Analyze recursive loop patterns and network anomalies from autonomous AI agents (e.g., Devin, AutoGPT) using LLMs to distinguish between legitimate logic and jailbreak attempts.
- [ ] **On-Device Semantic Guardrails:** Embed a lightweight ONNX runtime (Phi-3-mini/Llama-3) locally for real-time prompt safety classification (<15ms latency).
- [ ] **Token Traffic Monitor:** Live visualization dashboard detailing input/output token counts, throughput, and hourly expenditure caps.
- [ ] **Local Audit Tracing:** Log exact prompt history locally in SQLite with JSON search queries.

## 🛡️ Phase 4: System Daemons, TPM 2.0 & Enterprise Compliance (v2.0+)
- [ ] **Hardware Security Integration:** Bind proxy authorization keys and local CA private keys securely to TPM 2.0 modules or Apple Secure Enclaves.
- [ ] **System Daemons:** Run core proxy routing servers as headless background daemons (`systemd` / Windows Service).
- [ ] **Centralized Enterprise Policies:** MDM, GPO, and plist profiles to distribute security rules across engineering teams.
- [ ] **AI-Assisted Compliance Reporting:** Automatically generate readable enterprise compliance and security posture reports from local audit logs using API integrations.
- [ ] **Zero-Knowledge Code Proofs:** Offline validation architectures to verify code structures locally without sending code tokens.
- [ ] **Cryptographically Verifiable Audit Logs:** Append-only Merkle tree ledger of audit logs signed locally.

## 🔒 Phase 5: Confidential Computing & eBPF Telemetry Analysis (v3.0+)
- [ ] **Trusted Execution Environments (TEEs):** Deploy the gateway proxy within hardware-isolated confidential VMs (Intel SGX, AMD SEV).
- [ ] **eBPF-based Syscall Telemetry & Process Sandboxing:** Trace file-read syscalls by IDE processes to detect exfiltration of sensitive configuration (`.git/config`, `.env`) files.
- [ ] **LLM-Powered Anomaly Explanation:** Route complex eBPF kernel telemetry anomalies through language models to generate human-readable security alerts for SOC teams.
- [ ] **Homomorphic Proxy Routing:** Prefix-matching and routing of encrypted prompt tokens using homomorphic encryption.

---

*Note: This roadmap is a living document. Priorities may shift based on community feedback and open-source contributions. We welcome PRs for any of the features listed above!*
