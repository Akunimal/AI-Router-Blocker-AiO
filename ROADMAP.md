# 🗺️ AI DevSec Gateway - Roadmap

Welcome to the future of **AI-Router-Blocker-AiO**. Our goal is to create the ultimate open-source, privacy-first DevSecOps Gateway for developers navigating the AI era. 

This roadmap outlines our planned features to demonstrate active continuity and long-term vision.

---

## 🚀 Phase 1: Deep Packet & Granular Control (v1.2 - v1.3)
Currently, our blocking mechanism is domain-based via the `hosts` file. We plan to introduce deep inspection for surgical control.

* **[ ] Deep Packet Inspection (DPI) & TLS Interception**
  * Intercept HTTPS traffic locally using a custom self-signed root CA.
  * Block specific API endpoints (e.g., `POST /v1/completions`) while allowing others.
* **[ ] Multi-Provider Security Auditors**
  * Expand the DevSec Auditor to use **Anthropic (Claude)**, **Google Gemini**, and **Mistral** APIs as alternatives to OpenAI for analyzing process telemetry.
* **[ ] Regular Expression (Regex) Domain Blocking**
  * Allow users to define wildcards and regex patterns to block entire cloud infrastructure subnets.

## 📊 Phase 2: Analytics & Budgeting (v1.4 - v1.5)
When using the Local Router to proxy BYOK (Bring Your Own Key) requests, developers need visibility into what their editors are consuming.

* **[ ] Token & Cost Management Dashboard**
  * Real-time monitoring of token usage when proxying to cloud providers.
  * Set hard budget limits per IDE (e.g., "Stop Cursor from spending more than $5 today").
* **[ ] Prompt Tracing & Logging**
  * Optional, strictly local logging of prompts sent by IDEs to audit exactly what code snippets are leaving your machine.
* **[ ] Community Threat Intelligence Feeds**
  * Subscribe to dynamic, community-maintained blocklists (similar to Pi-hole or uBlock Origin) instead of relying on static lists.

## 🛡️ Phase 3: Enterprise & Background Daemon (v2.0+)
Transforming the tool from a desktop GUI application into a headless, enterprise-ready infrastructure component.

* **[ ] Background Daemon Architecture**
  * Decouple the UI from the core logic. Run the Gateway as a lightweight system service (Windows Service / `systemd` daemon).
* **[ ] OS Native Notifications**
  * Trigger native system tray alerts when an AI editor attempts an unauthorized connection or a potential data leak is detected.
* **[ ] Policy Deployment (GPO/MDM)**
  * Allow IT administrators to deploy the Gateway across engineering teams using Active Directory Group Policies or MDM solutions.
* **[ ] Containerized Proxy Mode**
  * Provide an official Docker image to run the Gateway at the network router level, protecting the entire office/home network.

---

*Note: This roadmap is a living document. Priorities may shift based on community feedback and open-source contributions. We welcome PRs for any of the features listed above!*
