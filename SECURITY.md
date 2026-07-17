# Security Policy

## Supported Versions

We actively support and patch the latest version of CodeGate. If you are running an older version, please upgrade to the latest release before reporting a vulnerability.

| Version | Supported |
| ------- | --------- |
| >= 1.2.x | ' Yes |
| < 1.2.0 | 'L No |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, if you discover a security vulnerability, please report it via the **GitHub Security Advisories** tab in the repository by clicking "Report a vulnerability". Alternatively, if that is not available, please contact the maintainers directly.

When reporting a vulnerability, please include:
1. A detailed description of the vulnerability.
2. Steps to reproduce the issue (and a proof of concept if available).
3. The impact of the vulnerability and how it can be exploited.
4. The operating system and version of the application you tested.

We will acknowledge receipt of your report within 48 hours and work with you to coordinate a security patch and disclosure timeline.

## Our Security Commitment

CodeGate operates with elevated privileges (Administrator on Windows, root on Linux/macOS) in order to modify the system `hosts` file. Because of these privileges, we take security extremely seriously:

- **No Persistence of Keys:** API keys (such as OpenAI keys used by the DevSec Auditor) are loaded at runtime from environment variables or entered in memory, and are never saved to disk in `config.json`.
- **Minimal Privilege Modification:** We only modify lines in the `hosts` file that contain the `# AI-Block` tag. We never read or modify other lines.
- **Dependency Audit:** We keep dependencies to an absolute minimum (using the Python Standard Library where possible) to minimize the supply chain attack surface.
