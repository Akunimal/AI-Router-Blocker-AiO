# 🛡️ AI Network Blocker (Bloqueador de Red de IA)

> **Retoma el control. Decide cuándo tus editores de IA pueden comunicarse con la nube.**

<p align="center">
  <img src="assets/screenshot.png" alt="Interfaz de AI Network Blocker" width="600">
</p>

![Python](https://img.shields.io/badge/Python-3.x-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-0078D4?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-22c55e)
![Release](https://img.shields.io/github/v/release/Akunimal/AI-Blocker?color=blue&label=Última%20Versión)

[English](README.md) | [Español](README.es.md)

---

## 📖 ¿Qué es esto?

**AI Network Blocker** es una herramienta de escritorio gratuita, de código abierto y de un solo clic que bloquea todo el tráfico de red entre tu máquina y los principales proveedores de IA en la nube. Funciona editando el archivo `hosts` del sistema — sin procesos en segundo plano, sin reglas de firewall, sin drivers. Es compatible con Windows, Linux y macOS.

Con un clic:
1. **Mata** los procesos de editores de IA en ejecución (VS Code, Cursor, Windsurf, Claude, etc.).
2. **Redirige** más de 35 dominios de IA a `127.0.0.1` en tu archivo hosts.
3. **Limpia** la caché DNS para que el bloqueo tenga efecto **inmediatamente**.

Con un segundo clic **deshace todo** limpiamente, eliminando solo las líneas que agregó.

---

## 🤔 ¿Por qué existe esto?

Los asistentes de programación de IA tienen acceso profundo y sin restricciones a tus archivos, tu portapapeles y tu terminal. Incluso cuando dejas de usarlos, sus procesos siguen ejecutándose en segundo plano, manteniendo conexiones abiertas con servidores remotos de forma silenciosa. Eso significa:

- El código que escribiste *hace horas* podría seguir transmitiéndose.
- Los prompts que contienen lógica propietaria podrían almacenarse en caché o registrarse en servidores de terceros.
- No tienes **ninguna visibilidad** sobre qué datos se envían, o cuándo.

**AI Network Blocker te da un interruptor de apagado duro y determinista.** Sin ambigüedades. Sin necesidad de confiar. El archivo hosts es una anulación a nivel de sistema: si un dominio se resuelve en `127.0.0.1`, nada pasa. Punto.

---

## ✨ Características (Features)

| Característica | Descripción |
|---|---|
| 🔒 **Interruptor de un clic** | Bloquea o desbloquea todos los servicios de IA al instante |
| 🌍 **Soporte multilingüe** | 10 idiomas soportados con detección automática del sistema y selector manual |
| 🎨 **Interfaz oscura premium** | Tema moderno Catppuccin Mocha con estados codificados por colores |
| 🔑 **Elevación inteligente** | UAC automático en Windows, instrucciones claras de `sudo` en Unix |
| 🧹 **Limpieza de caché DNS** | Limpia automáticamente el DNS para efecto instantáneo en todos los SO |
| 👁️ **Detección de procesos en vivo** | El pie de página encuesta continuamente y muestra qué editores de IA se están ejecutando |
| 🛡️ **Concurrencia segura** | El bloqueo de instancia única evita que múltiples ventanas corrompan el archivo hosts |
| 📊 **Desglose por categoría** | Panel visual que lista todos los proveedores bloqueados con recuento de dominios |
| 📦 **Portable** | Ejecutables de un solo archivo disponibles |
| ⚡ **Interfaz sin bloqueos** | Todas las operaciones se ejecutan en hilos de fondo: la GUI nunca se congela |
| 🔍 **Totalmente auditable** | Un archivo Python, extensamente comentado |

---

## 🎯 Proveedores y Dominios Bloqueados

La lista de bloqueo por defecto apunta a **más de 35 dominios** en 9 categorías:

| Proveedor | # Dominios | Dominios clave |
|---|---|---|
| 🟢 OpenAI | 9 | `api.openai.com` · `chatgpt.com` · `platform.openai.com` |
| 🟠 Anthropic | 4 | `claude.ai` · `api.anthropic.com` · `anthropic.com` |
| 🐙 GitHub Copilot | 4 | `copilot.github.com` · `api.githubcopilot.com` |
| 🔵 Google AI | 4 | `gemini.google.com` · `aistudio.google.com` |
| 🟦 Microsoft Copilot | 3 | `copilot.microsoft.com` · `bing.com` |
| 🔷 Meta AI | 2 | `meta.ai` · `ai.meta.com` |
| 🌊 Mistral AI | 2 | `mistral.ai` · `api.mistral.ai` |
| 🔮 DeepSeek | 2 | `deepseek.com` · `api.deepseek.com` |
| 📦 Otros | 3 | `perplexity.ai` · `app.wordware.ai` |

---

## 🚀 Inicio Rápido

### Opción A — Descargar el ejecutable listo para usar

1. Ve a la página de [**Releases**](https://github.com/Akunimal/AI-Blocker/releases).
2. Descarga el binario para tu sistema operativo.
3. Ejecuta el archivo.
   - **Windows**: Haz doble clic en `AI-Blocker.exe`. Haz clic en **Sí** en el aviso de UAC.
   - **Linux / macOS**: Abre una terminal y ejecuta `sudo ./AI-Blocker`.
4. Haz clic en el botón grande para activar o desactivar el bloqueo. Eso es todo.

### Opción B — Ejecutar desde el código fuente

```bash
# 1. Clonar el repositorio
git clone https://github.com/Akunimal/AI-Blocker.git
cd AI-Blocker

# 2. Ejecutar el script (Requiere Python 3.x)
# En Windows (se eleva automáticamente vía UAC):
python ai_blocker.py

# En Linux / macOS (requiere sudo):
sudo python3 ai_blocker.py
```

---

## 📜 Licencia — Libre como en la Libertad

Este proyecto se publica bajo la **Licencia MIT** — consulta [LICENSE](LICENSE) para ver el texto completo.
**Este es un proyecto impulsado por la comunidad y sin fines de lucro.** Sin anuncios. Sin telemetría. Sin rastreo. Sin monetización. Nunca.
