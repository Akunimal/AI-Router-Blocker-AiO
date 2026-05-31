# Welcome to AI DevSec Gateway

> Take back control. Intercept, audit, and route your AI traffic.

**AI DevSec Gateway** (formerly known as AI Network Blocker) is a free, open-source, desktop tool that puts you back in charge of the AI coding assistants running on your local machine.

Originally created as a simple hosts-file DNS kill-switch, it has evolved into a complete local privacy proxy and security auditor.

---

## What does it do?

1.  **🔒 Hard DNS Kill-Switch:** Instantly block and unblock 38+ AI services and endpoints by routing them to loopback (`127.0.0.1`) in your hosts file.
2.  **🔀 Local API Gateway:** Transparently intercept API requests from editors like VS Code, Cursor, or Windsurf, and proxy them to local LLMs (Ollama, LM Studio) rather than remote servers.
3.  **🛡️ Environment Security Auditor:** Perform real-time scans of running editor processes to detect data exfiltration risks, backed by secure, memory-only OpenAI API security recommendations.
4.  **🌍 Multilingual GUI & CLI:** Easily switch between 10 languages, utilize a gorgeous Catppuccin Mocha themed GUI, or run it entirely headless in the terminal.

---

## Why does it exist?

AI-powered editors have deep access to your open code buffers, file lists, terminal outputs, and git histories. When you close the IDE, background node processes often remain active, keeping connections open.

Without a system-level override, you have zero visibility into what gets sent to cloud AI providers. **AI DevSec Gateway** gives you a deterministic, zero-trust way to control outbound traffic. If the domain resolves to loopback in the hosts file, it is physically impossible for the traffic to leak.

---

## Project Pages
*   **Installation & Quickstart:** Get up and running in 60 seconds.
*   **CLI Reference:** Read options for headless systems.
*   **Architecture Guide:** Learn how the hosts engines and proxy servers are structured.
*   **Threat Model:** Deep audit of security vectors and privilege isolation.
