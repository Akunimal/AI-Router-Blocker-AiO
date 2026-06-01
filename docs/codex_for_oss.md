# Codex for OSS Application Notes

This page keeps the project application narrative honest, concise, and easy to reuse when applying for OpenAI's Codex for OSS program or similar OSS support programs.

## Why this repository matters

AI DevSec Gateway is an open-source privacy and security tool for developers adopting AI coding assistants. It helps teams apply local controls to known AI endpoints, inspect active AI editor processes, and route compatible API clients toward local or private inference servers.

The project is relevant to the software ecosystem because AI-assisted development increases the risk of accidentally sending source code, secrets, terminal output, or repository metadata to third-party services. AI DevSec Gateway provides a transparent, local-first mitigation path that developers can audit and run themselves.

## Current maintenance signals

- MIT licensed, public, and designed for self-hosted/local use.
- Multi-OS GitHub Actions test matrix for Windows, Linux, and macOS.
- Python 3.10 through 3.13 support in CI.
- Unit tests with coverage threshold enforcement.
- Ruff, mypy, CodeQL, Dependabot, issue templates, PR template, and security policy.
- Package metadata and distribution paths for PyPI, Homebrew, Scoop, and portable binaries.
- Roadmap separates implemented behavior from future TLS/DPI, eBPF, and WFP work.

## How Codex would be used

Codex credits would be used for maintenance work that benefits users and contributors:

- Review pull requests for security regressions, unsafe subprocess usage, and cross-platform behavior.
- Generate and update tests around privileged network operations, CLI behavior, config persistence, and release packaging.
- Triage issues by reproducing failures, identifying platform-specific behavior, and drafting fixes.
- Harden documentation so implemented capabilities, experimental features, and roadmap items remain clearly separated.
- Assist release preparation by checking changelogs, packaging metadata, workflows, and smoke-test commands.

## Suggested application answer

AI DevSec Gateway is an open-source privacy/security tool for developers adopting AI coding assistants. It gives teams local controls to block known AI endpoints, audit active AI editor processes, and route compatible API clients to local/private LLM infrastructure. The project is actively maintained with multi-OS CI, tests, linting, type checks, CodeQL, packaging metadata, a security policy, and a roadmap toward safer AI development workflows.

Codex would help maintain quality in a security-sensitive OSS tool where cross-platform behavior, safe defaults, and clear documentation matter. We would use Codex for PR review, issue triage, regression tests, release checks, and security hardening of network enforcement code paths.

## Current scope boundaries

- The default enforcement backend is hosts-file blocking.
- The local API gateway currently handles loopback HTTP routing for compatible clients.
- The firewall backend is experimental and should be inspected with dry-run before use.
- TLS/DPI interception, root CA installation, eBPF, and Windows Filtering Platform support are roadmap items, not current runtime behavior.
