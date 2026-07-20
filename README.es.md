# 🛡️ CodeGate

> **Controles locales para bloquear, auditar, enrutar y proteger tráfico de IA en entornos de desarrollo.**

[![Python Version](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-0078D4?logo=windows&logoColor=white)](https://github.com/Akunimal/CodeGate#readme)
[![Test Suite Status](https://github.com/Akunimal/CodeGate/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/Akunimal/CodeGate/actions/workflows/test.yml)
[![Security Scan Status](https://github.com/Akunimal/CodeGate/actions/workflows/codeql.yml/badge.svg?branch=main)](https://github.com/Akunimal/CodeGate/actions/workflows/codeql.yml)
[![codecov](https://codecov.io/gh/Akunimal/CodeGate/graph/badge.svg)](https://codecov.io/gh/Akunimal/CodeGate)
[![License](https://img.shields.io/badge/License-MIT-22c55e)](LICENSE)

[English](README.md) | [Español](README.es.md)

---

## ¿Qué es esto?

**CodeGate** es una herramienta open-source de privacidad y DevSecOps para desarrolladores que adoptan asistentes de código con IA. Ofrece controles locales para bloquear endpoints conocidos de IA, enrutar tráfico API hacia servidores de inferencia locales, auditar procesos activos de editores con IA y proteger datos sensibles mediante DLP.

Creado originalmente como una simple interfaz gráfica para bloquear dominios de IA, está evolucionando hacia un **Gateway Zero-Trust** para desarrollo asistido por IA más seguro.

1. **Bloquear:** Anulación determinista a nivel de SO mediante el archivo `hosts` que descarta conexiones a 38+ dominios conocidos de IA.
2. **Enrutar:** Proxy HTTP local que dirige clientes API compatibles hacia LLMs locales (Ollama, LM Studio, vLLM).
3. **Auditar:** Revisiones de seguridad de procesos activos para detectar herramientas de IA y señales de riesgo de fuga de datos.
4. **Proteger:** Sanitización DLP en tiempo real, guardrails semánticos y monitoreo de uso de tokens.

---

## Características

| Función | Descripción |
|---|---|
| Live Token Dashboard | Tokens in/out en tiempo real con auto-refresh cada 5s. Estadísticas via endpoint /stats HTTP. |
| Panel DLP & Guardrails | Panel en vivo de hallazgos con botón de refresco, toggles DLP y guardrails por sesión. |
| Enrutador API Transparente | Redirige tráfico Copilot/Cursor a servidores LLM locales. |
| AI DevSec Auditor | Análisis en vivo de procesos con recomendaciones de OpenAI. Claves solo en memoria. |
| Interfaz CLI Nativa | Control completo para CI/CD: codegate --status, codegate --block. |
| Interruptor de Apagado Determinista | Bloqueo a nivel SO vía hosts. Sin dependencia DNS remota. |
| Distribución Universal | Instalable via pip, brew, scoop o binario portable. |
| Interfaz Multilingüe | Catppuccin Mocha con 10 idiomas y elevación inteligente (UAC/sudo). |
| Prevención de Fuga de Datos (DLP) | Redacción/bloqueo por regex de API keys, credenciales cloud, PII, claves privadas, JWT, URIs DB. |
| Políticas DLP Configurables | Por dominio/ruta: REDACT, BLOCK, LOG_ONLY, PASS_THROUGH con circuit breaker. |
| DLP Semántico Asistido por Cloud | Integración opcional con IA para análisis semántico profundo con caché LRU. |
| Inteligencia de Amenazas IA | Analizador de patrones, detección de loops recursivos, alertas de agentes autónomos. |
| Guardrails ONNX Locales | Runtime ONNX liviano (Phi-3-mini) para clasificación de seguridad en tiempo real. |
| Flags CLI para DLP/Guardrails | --dlp, --guardrails, --token-monitor con persistencia de configuración. |
| Auditoría Mejorada | Trazabilidad granular con metadatos (dominio, endpoint, categorías, hash del request). |
| Dashboard de Cap de Tokens | Límite de uso, consumo total y porcentaje con códigos de color en UI. |

---

## Prevención de Fuga de Datos (DLP)

CodeGate incluye un motor DLP incorporado que inspecciona todo el tráfico API saliente en busca de datos sensibles. Soporta análisis semántico asistido por cloud vía API de IA con caché LRU y protocolo de escalación configurable.

### Categorías de Detección

| Categoría | Ejemplos | Acción por Defecto |
|---|---|---|
| API Keys y Tokens | OpenAI sk-*, Anthropic sk-ant-*, GitHub ghp_*, xoxb-* | REDACT |
| Credenciales Cloud | AWS keys, GCP tokens, Azure secrets | REDACT |
| PII | Emails, SSN, tarjetas de crédito, teléfonos | REDACT |
| Claves Privadas | RSA/EC/DSA/OpenSSH private keys | BLOCK |
| Cloud DLP | Análisis semántico IA de hallazgos de baja confianza | ESCALATE |
| JWT Tokens | JSON Web Tokens (eyJ.) | REDACT |
| IPs Internas | RFC 1918 (10.x, 172.16-31.x, 192.168.x) | LOG_ONLY |
| Licencias Conflictivas | AGPL-3.0, GPL-3.0 | LOG_ONLY |
| Conexiones a BD | PostgreSQL, MySQL, MongoDB, Redis URIs | REDACT |
| Variables de Entorno | AWS_SECRET_ACCESS_KEY, DB_PASSWORD | LOG_ONLY |

---

## Guardrails e Inteligencia de Amenazas

CodeGate incluye clasificación multicapa de seguridad de prompts con cadena de fallback automática: ONNX runtime (Phi-3-mini) > clasificador heurístico > permitir.

---

## Monitoreo de Tokens

El TokenMonitor incorporado rastrea uso de tokens por request, agrega resúmenes por hora y aplica límites configurables. El dashboard en vivo en la GUI muestra tokens in/out, consumo total, conteo de requests por dominio y porcentaje de uso con código de colores.

---

## Proveedores Soportados

El motor de intercepción apunta a 38+ dominios: OpenAI, Anthropic, GitHub Copilot, Google AI, Microsoft, Meta AI, Mistral, DeepSeek, xAI, y más. Lista configurable en `ai_blocker/constants.py`.

---

## Inicio Rápido

### 1. Paquete de Python (Pip)

```bash
pip install codegate

codegate --status
codegate --block
codegate --unblock
```

### 2. Gestores de Paquetes

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

### 3. Binarios GUI Portables

1. Visita la página de [Releases](https://github.com/Akunimal/CodeGate/releases).
2. Descarga el ejecutable para tu SO (.exe, macOS binary, Linux AppImage).
3. Ejecuta la aplicación (pide Admin/sudo al activar el interruptor de red).

---

## Modelo de Seguridad

- **Zero-Persistence BYOK:** Claves API estrictamente en memoria RAM. Nunca en disco.
- **Modificaciones Quirúrgicas del SO:** Inyección de marcadores AI-Block en hosts. Aislamiento total.
- **Telemetría Aislada:** Cero rastreo, análisis o mecanismos phone-home.

---

## Roadmap y Visión Futura

- DLP (Prevención de Fuga de Datos) - *Implementado en v1.6.0*
- DLP Semántico Asistido por Cloud - *Implementado en v1.6.0*
- Guardrails ONNX Locales - *Implementado en v1.7.0*
- Inteligencia de Amenazas IA - *Implementado en v1.7.0*
- Dashboard de Monitoreo de Tokens - *Implementado en v1.7.0*
- Panel DLP & Guardrails en UI - *Implementado en v1.7.0*
- Flags CLI para DLP/Guardrails/TokenMonitor - *Implementado en v1.7.0*
- Dry-Run Mode en GUI (próximo)
- Telemetría Kernel eBPF
- Computación Confidencial (SGX)

---

## Código Abierto y Gobernanza

- [Guía de Arquitectura](docs/architecture.md)
- [Guía de Contribución](CONTRIBUTING.md)
- [Código de Conducta](CODE_OF_CONDUCT.md)
- [Política de Seguridad](SECURITY.md)
- [Licencia: MIT](LICENSE)

---

> Audita lo invisible. Enruta lo restringido. No confíes en ningún paquete.