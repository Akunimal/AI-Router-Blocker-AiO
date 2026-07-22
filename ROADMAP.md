# CodeGate - Roadmap



Welcome to the future of **CodeGate**. Our goal is to create the ultimate open-source, privacy-first DevSecOps Gateway for developers navigating the AI era.



This roadmap outlines our technical vision, showing our completed work, upcoming milestones, and our commitment to using AI to secure and maintain the project itself.



---



## Roadmap Overview



| Phase | Description | Timeline | Progress |

|---|---|---|---|

| **Phase 0** | Core Desktop Blocker & i18n | Q1 2026 | `%%%%%%%%%%` 100% |

| **Phase 1** | Modularization, CLI & Multi-Provider | Q2 2026 | `%%%%%%%%%%` 100% |

| **Phase 2** | Network Backend Abstraction, Firewall Redirects & TLS Decryption | Q3 2026 | `%%%%%%%%%%` 100% |

| **Phase 3** | DLP Sanitization, Hybrid Guardrails & Threat Intel | Q4 2026 | `%%%%%%%%%%` 100% |

| **Phase 4** | System Daemons, TPM 2.0 & Enterprise Compliance | Q1 2027 | `%%%%%%%%%%` 0% |

| **Phase 5** | Confidential Computing & eBPF Telemetry Analysis | Q2 2027 | `%%%%%%%%%%` 0% |



---



## Continuous Track: AI-Assisted DevSecOps & Maintenance



We believe in *dogfooding* and leveraging AI to secure and accelerate our own development. This ongoing track operates parallel to all phases, ensuring the gateway is hardened using the best available AI tools.



- **AI-Driven Security Reviews:** Automated AI reviews on pull requests focused on detecting security regressions, unsafe subprocess usage, and cross-platform network operation vulnerabilities.

- **AI-Generated Regression Fuzzing:** Using AI to generate robust, edge-case regression tests for privileged operations (hosts file manipulation, OS firewall rules, and TLS certificate injection).

- **Automated Issue Triage & Repro:** Leveraging AI to analyze community bug reports, reproduce platform-specific failures (e.g., Windows WFP vs Linux eBPF nuances), and draft focused fixes.

- **Secure Dogfooding:** The gateway is built using AI coding assistants, and we actively use our own gateway to audit, sanitize, and protect our development traffic from accidental IP leaks.



---



## ' Phase 0: Core Desktop Blocker (Completed - v1.0 - v1.1)

- [x] **Cross-platform UI:** Built with Tkinter using a premium Catppuccin Mocha theme.

- [x] **Hosts File Engine:** Modify `/etc/hosts` and flush DNS silently across Windows, Linux, and macOS.

- [x] **Active Process Killer:** Scan and terminate active editor processes to prevent background data leaks.

- [x] **Internationalization (i18n):** Extracted translations supporting 10 languages with auto OS detection.



## = Phase 1: Modularization, CLI & Gateway (Completed - v1.2 - v1.2.1)

- [x] **Modular Package Refactoring:** Broke down the 92KB monolith into single-responsibility package submodules (config, constants, system_utils, block_actions, gateway, tray, ui).

- [x] **Headless CLI Interface:** Implemented pure terminal CLI argument parsing (`--block`, `--unblock`, `--status`) for scripting and headless servers.

- [x] **Package Manager Distribution:** Added Homebrew tap formulas and Scoop JSON manifests for developer installations.

- [x] **Local API Router (BYOK):** Intercept and transparently proxy requests to Ollama/LM Studio or custom endpoints.

- [x] **OpenAI DevSec Auditor:** Live process auditing via OpenAI API to find open leaks and suggest mitigation.

- [x] **Custom Domain Additions:** Interactively add domains to local configuration settings.

- [x] **Granular Category Toggles:** Profile-level category selectors (Work, Personal, Free) to control block scopes.



## > Phase 2: Network Interception & HTTPS TLS Decryption (Completed - v1.3 - v1.5)

- [x] **Internal Network Backend Interface:** Pluggable backend boundary for hosts-file, firewall redirects, and kernel-level interceptors.

- [x] **Non-kernel Firewall/Redirect Backend Foundation:** Injectable command runner for OS firewall rules as an intermediate layer.

- [x] **Deep Packet Inspection (DPI) & TLS Decryption:** On-the-fly local Root CA generator and OS trust store integration for surgical endpoint blocking (e.g., `/v1/chat/completions`).

- [x] **Kernel-Level Socket Redirection:** eBPF (Linux) and WFP (Windows) foundations to redirect TCP ports `443` at the kernel layer.

- [x] **Dynamic Regular Expression Domain Matching:** Real-time wildcard resolution for dynamic content delivery networks (CDNs).



## = Phase 3: DLP Sanitization, Hybrid Guardrails & Threat Intel (v1.6 - v1.7)

- [x] **Real-Time DLP Sanitization Pipeline:** Regex and heuristic parsing of prompt request bodies to redact secrets, keys, PII, and proprietary source code before forwarding.

- [x] **DLP & Guardrails Toggle Flags:** Per-session enable/disable of DPI scanning and semantic guardrails. *(Implemented in v1.5.0)*

- [x] **Cloud-Assisted Semantic DLP (Hybrid Mode):** Optional integration with OpenAI API for deep semantic analysis of prompts when local heuristics require escalation to detect complex IP leaks.

- [x] **AI-Powered Threat Intelligence:** Analyze recursive loop patterns and network anomalies from autonomous AI agents (e.g., Devin, AutoGPT) using LLMs to distinguish between legitimate logic and jailbreak attempts.

- [x] **On-Device Semantic Guardrails:** Embed a lightweight ONNX runtime (Phi-3-mini/Llama-3) locally for real-time prompt safety classification (<15ms latency).

- [x] **Token Traffic Monitor:** Live visualization dashboard detailing input/output token counts, throughput, and hourly expenditure caps. *(Implemented in v1.5.0)*



---

## = Mega Plan: Phase 3 (v1.6 ! v1.7)



**DLP Sanitization, Hybrid Guardrails & Threat Intelligence**

Basado en el roadmap existente y el codigo actual (DLP engine, guardrails, DPI ya implementados).



---



### Wave 0   Foundation & Gap Analysis



Prep antes de tocar cdigo.



| # | Tarea | Artefacto |

|---|---|---|

| 0.1 | [OK] Auditar DLPEngine actual: qu findings categories cubre, qu falta (IPs internas, tokens especficos de proveedores cloud, vars de entorno) | dlp_engine.py review |

| 0.2 | [OK] Auditar PromptGuardrail: qu patrones de inyeccin cubre, falsos positivos conocidos | guardrails.py review |

| 0.3 | [OK] Documentar la arquitectura DLP ! Guardrail ! DPI pipeline en docs/architecture.md | docs/architecture.md |

| 0.4 | [OK] Agregar tests faltantes para edge cases del pipeline actual | 	ests/test_dlp_engine.py, 	ests/test_guardrails.py |



**Commit:** [OK] 91c1e6b feat: expand DLP engine with cloud/IP/DB/ENV patterns



---



### Wave 1   Real-Time DLP Sanitization Pipeline (v1.6)



Llevar el DLPEngine de "scan + redact" a un pipeline completo con polticas, estructura y mtricas.



#### 1.1 Polticas DLP configurables

- Nueva clase DLPPolicy: por-domain, por-endpoint, categoras habilitadas, accin (redact/block/log-only)

- Archivo de configuracin dlp_policies.json con poltica por defecto

- Integracin con gateway: _get_dlp_policy(domain, path) -> DLPPolicy



**Commit:** eat: add configurable DLP policies with per-domain overrides



#### 1.2 Redaccin estructurada (JSON-aware)

- DLPEngine.redact_structured(text) que parsea JSON, aplica redaccin campo a campo

- Preserva estructura JSON (no rompe el payload)

- Soporte para anidamiento profundo



**Commit:** eat: add structured JSON redaction to DLP engine



#### 1.3 Mtricas y circuit breaker

- Contadores de findings por tipo, tiempo de scan, tasa de falsos positivos

- Circuit breaker: si DLP tarda >500ms, pasa a log-only

- Exportar mtricas va el /stats endpoint existente



**Commit:** eat: add DLP performance metrics and circuit breaker



#### 1.4 Audit logging mejorado

- Log granular de cada accin DLP (scan, redact, block, bypass)

- Metadata completa: dominio, endpoint, categoras encontradas, tiempo de scan

- Integracin con AuditLog existente



**Commit:** eat: enhance DLP audit logging with per-finding metadata



---



### Wave 2   Cloud-Assisted Semantic DLP (v1.6)



Integracin opcional con OpenAI API para anlisis semntico profundo.



#### 2.1 Mdulo SemanticDLPClient

- Nueva clase SemanticDLPClient en i_blocker/semantic_dlp.py

- Llamada a OpenAI API con prompt template para clasificar texto

- Timeout configurable, retry lgico, manejo de errores

- API key desde config o variable de entorno (nunca persistida)



**Commit:** eat: add SemanticDLPClient for cloud-assisted DLP analysis



#### 2.2 Protocolo de escalacin

- Si DLP local encuentra algo sospechoso -> enviar a SemanticDLPClient

- Template de prompt que devuelve JSON estructurado: {"category", "risk_score", "explanation"}

- Threshold configurable para escalar (ej: findings con confianza < 0.8)



**Commit:** eat: implement DLP escalation protocol (local -> cloud)



#### 2.3 Cach de resultados

- Cache LRU para evitar re-anlisis de texto idntico

- TTL configurable (default 5 min)

- Invalidacin manual desde UI



**Commit:** eat: add LRU result cache for semantic DLP



#### 2.4 UI para hybrid mode

- Toggle "Cloud DLP" en la UI (tab CodeGate)

- Indicador de estado (disponible/no disponible)

- Configuracin de threshold y API key (in-memory, no persistida)



**Commit:** eat: add hybrid DLP mode UI controls



---



### Wave 3   AI-Powered Threat Intelligence (v1.7)



Deteccin de patrones anmalos y amenazas de agentes autnomos.



#### 3.1 Analizador de patrones de requests

- Nueva clase RequestAnalyzer en i_blocker/threat_intel.py

- Ventana deslizante de requests (ltimos N segundos/minutos)

- Deteccin de anomalas: frecuencia inusual, volumen de tokens, endpoints inusuales

- Almacenamiento en memoria con poda peridica



**Commit:** eat: add request pattern analyzer for anomaly detection



#### 3.2 Deteccin de loops recursivos

- Identificar patrones de agente autnomo: request -> response -> request (idntico o similar)

- Hash de contenido + similitud coseno para detectar ciclos

- Alerta si mismo contenido se enva >N veces en ventana de tiempo



**Commit:** eat: add recursive loop detection for autonomous agents



#### 3.3 Threat feed y alerting

- Feed local JSON-based (	hreat_feeds/*.json) con IOCs conocidos

- Notificaciones en UI cuando se detecta amenaza

- Log de eventos de amenaza con timestamp, categora, dominio



**Commit:** eat: add local threat feed and alerting system



#### 3.4 Visualizacin en dashboard

- Nueva seccin "Threats" en la UI

- Timeline de eventos, contadores por categora

- Integracin con el sistema de notificaciones existente



**Commit:** eat: add threat intelligence dashboard to UI



---



### Wave 4   On-Device Semantic Guardrails (v1.7)



Clasificacin ONNX local para guardrails en <15ms.



#### 4.1 Model loader y download manager

- Nueva clase ONNXGuardrailModel en i_blocker/onnx_guardrail.py

- Descarga de modelo Phi-3-mini desde HuggingFace

- Cache de modelo en ~/.cache/codegate/models/

- Verificacin de integridad (SHA256)



**Commit:** eat: add ONNX model loader and download manager



#### 4.2 Runtime de clasificacin

- Carga del modelo ONNX con onnxruntime

- Preprocesamiento de texto (tokenizacin)

- Inferencia con timeout (target 15ms)

- Postprocesamiento: categoras + confidence score



**Commit:** eat: add ONNX classification runtime for prompt guardrails



#### 4.3 Cadena de fallback

- ONNX -> Heuristic -> Allow (si ONNX no disponible, cae a heursticas)

- Si ONNX tarda >15ms, timeout y fallback automtico

- Log de modo y tiempo de inferencia



**Commit:** eat: implement fallback chain for on-device guardrails



#### 4.4 Benchmarks y optimizacin

- Pruebas de rendimiento: latency, throughput, memory

- Quantization del modelo (INT8) para reducir tamao y mejorar velocidad

- Documentacin de resultados



**Commit:** perf: benchmark and optimize ONNX guardrail inference



---



### Wave 5   Verification & Release v1.7



| # | Tarea | Comando/Archivo |

|---|---|---|

| 5.1 | Ruff check + fix | 

uff check ai_blocker tests --fix |

| 5.2 | Mypy | mypy ai_blocker |

| 5.3 | Tests + coverage | pytest --cov=ai_blocker --tb=short -q |

| 5.4 | Version bump 1.6.x -> 1.7.0 | pyproject.toml, __init__.py |

| 5.5 | CHANGELOG | CHANGELOG.md |

| 5.6 | Tag + release | git tag v1.7.0 && git push origin v1.7.0 |



**Commits:**

- chore: fix lint and type issues for v1.7

- 

elease: bump version to 1.7.0 and update CHANGELOG



---



### Resumen de Commits



| Wave | Commits | Versin |

|---|---|---|

| Wave 0 | 1 | v1.6 base |

| Wave 1 | 4/4 | v1.6 ' |

| Wave 2 | 4/4 | v1.6 ' |

| Wave 3 | 4 | v1.7 |

| Wave 4 | 4 | v1.7 |

| Wave 5 | 3 | v1.7 |

| **Total** | **~20 commits** | |



- [ ] **Local Audit Tracing:** Log exact prompt history locally in SQLite with JSON search queries.



## = Phase 4: System Daemons, TPM 2.0 & Enterprise Compliance (v2.0+)

- [ ] **Hardware Security Integration:** Bind proxy authorization keys and local CA private keys securely to TPM 2.0 modules or Apple Secure Enclaves.

- [ ] **System Daemons:** Run core proxy routing servers as headless background daemons (`systemd` / Windows Service).

- [ ] **Centralized Enterprise Policies:** MDM, GPO, and plist profiles to distribute security rules across engineering teams.

- [ ] **AI-Assisted Compliance Reporting:** Automatically generate readable enterprise compliance and security posture reports from local audit logs using API integrations.

- [ ] **Zero-Knowledge Code Proofs:** Offline validation architectures to verify code structures locally without sending code tokens.

- [ ] **Cryptographically Verifiable Audit Logs:** Append-only Merkle tree ledger of audit logs signed locally.



## = Phase 5: Confidential Computing & eBPF Telemetry Analysis (v3.0+)

- [ ] **Trusted Execution Environments (TEEs):** Deploy the gateway proxy within hardware-isolated confidential VMs (Intel SGX, AMD SEV).

- [ ] **eBPF-based Syscall Telemetry & Process Sandboxing:** Trace file-read syscalls by IDE processes to detect exfiltration of sensitive configuration (`.git/config`, `.env`) files.

- [ ] **LLM-Powered Anomaly Explanation:** Route complex eBPF kernel telemetry anomalies through language models to generate human-readable security alerts for SOC teams.

- [ ] **Homomorphic Proxy Routing:** Prefix-matching and routing of encrypted prompt tokens using homomorphic encryption.



---



*Note: This roadmap is a living document. Priorities may shift based on community feedback and open-source contributions. We welcome PRs for any of the features listed above!*

