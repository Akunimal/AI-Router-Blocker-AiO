# Welcome to CodeGate

> Take back control. Intercept, audit, and route your AI traffic.

**CodeGate** known as CodeGate) is a free, open-source, desktop tool that puts you back in charge of the AI coding assistants running on your local machine.

Originally created as a simple hosts-file DNS kill-switch, it is evolving into a local privacy gateway and security auditor for AI-assisted development.

---

## What does it do?

1.  **Hard DNS Kill-Switch:** Block and unblock 38+ known AI services and endpoints by routing them to loopback (`127.0.0.1`) in your hosts file.
2.  **Local API Gateway:** Route compatible API clients to local LLMs such as Ollama or LM Studio.
3.  **Environment Security Auditor:** Scan running editor processes and request memory-only OpenAI security recommendations.
4.  **Multilingual GUI & CLI:** Use the Tkinter GUI or run entirely headless in the terminal.

---

## Why does it exist?

AI-powered editors have deep access to your open code buffers, file lists, terminal outputs, and git histories. When you close the IDE, background node processes often remain active, keeping connections open.

Without a system-level override, you have zero visibility into what gets sent to cloud AI providers. **CodeGate** gives you a deterministic, zero-trust way to control outbound traffic. If the domain resolves to loopback in the hosts file, it is physically impossible for the traffic to leak.

---

## Project Pages
*   **Installation & Quickstart:** Get up and running in 60 seconds.
*   **CLI Reference:** Read options for headless systems.
*   **Architecture Guide:** Learn how the hosts engines and proxy servers are structured.
*   **Threat Model:** Deep audit of security vectors and privilege isolation.
*   **Enterprise Use Cases:** Real-world scenarios and deployment patterns for DevSecOps teams.
