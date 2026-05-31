# 🗺️ AI DevSec Gateway - Roadmap

Welcome to the future of **AI DevSec Gateway** (formerly AI Network Blocker). Our goal is to create the ultimate open-source, privacy-first DevSecOps Gateway for developers navigating the AI era.

This roadmap outlines our technical vision, showing our completed work and upcoming milestones.

---

## 📅 Roadmap Overview

| Phase | Description | Timeline | Progress |
|---|---|---|---|
| **Phase 0** | Core Desktop Blocker & i18n | Q1 2026 | `██████████` 100% |
| **Phase 1** | DevSec Auditor & Gateway Proxy | Q2 2026 (Current) | `████████░░` 80% |
| **Phase 2** | Deep Interception & Regex | Q3 2026 | `░░░░░░░░░░` 0% |
| **Phase 3** | Analytics & Cost Dashboard | Q4 2026 | `░░░░░░░░░░` 0% |
| **Phase 4** | System Daemon & Enterprise | Q1 2027 | `░░░░░░░░░░` 0% |

---

## ✅ Phase 0: Core Desktop Blocker (Completed - v1.0 - v1.1)
- [x] **Cross-platform UI:** Built with Tkinter using a premium Catppuccin Mocha theme.
- [x] **Hosts File Engine:** Modify `/etc/hosts` and flush DNS silently across Windows, Linux, and macOS.
- [x] **Active Process Killer:** Scan and terminate active editor processes to prevent background data leak.
- [x] **Internationalization (i18n):** Extracted translations supporting 10 languages with auto OS detection.

## 🚀 Phase 1: DevSec Auditor & Gateway Proxy (Current - v1.2 - v1.3)
- [x] **Local API Router (BYOK):** Intercept and transparently proxy requests to Ollama/LM Studio or custom endpoints.
- [x] **OpenAI DevSec Auditor:** Live process auditing via OpenAI API to find open leaks and suggest mitigation.
- [x] **Multi-Provider Auditors:** Expand the DevSec Auditor to use Anthropic (Claude), Google Gemini, and Mistral.
- [ ] **Granular Domain Control:** Allow users to toggle blocking by specific service category.
- [ ] **Custom Domain Addition:** Interactively add domains to local JSON configurations without code changes.

## 🧪 Phase 2: Deep Interception & Regex Blocking (v1.4 - v1.5)
- [ ] **Deep Packet Inspection (DPI) / TLS Decryption:**
  * Local root CA setup to decrypt and inspect HTTPS traffic.
  * Surgical path blocking (e.g., block `/v1/chat/completions` but allow `/v1/models`).
- [ ] **Regular Expression Domain Matching:** Block dynamic subnets and CDNs via wildcards/regex.

## 📊 Phase 3: Analytics & Budgeting (v1.6 - v1.7)
- [ ] **Token Usage Dashboard:** Live counter of input/output tokens sent through the DevSec Gateway.
- [ ] **Local Audit Logging:** Trace and log exact prompt payloads sent by IDEs to see what code snippets are leaving.
- [ ] **Cost Management limits:** Set budget caps per session/IDE (e.g. limit Cursor to $2.00/day).
- [ ] **Threat Intelligence Feeds:** Auto-update blocklists using community-maintained ad-block-style lists.

## 🛡️ Phase 4: System Daemon & Enterprise (v2.0+)
- [ ] **Headless Daemon:** Run the gateway core as a Windows Service / `systemd` daemon.
- [ ] **OS Native Alerts:** Send desktop notifications when a background editor attempts to resolve blocked AI endpoints.
- [ ] **Centralized Policy Deployment:** MDM and GPO configuration files to deploy settings across enterprise engineering teams.
- [ ] **Dockerized Deployment:** Router-level DNS proxy container to protect local development networks.

---

*Note: This roadmap is a living document. Priorities may shift based on community feedback and open-source contributions. We welcome PRs for any of the features listed above!*
