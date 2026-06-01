# Codex for OSS Application Summary

This document summarizes why AI DevSec Gateway is a reasonable candidate for OpenAI's Codex for OSS program and how Codex would be used to maintain the project responsibly.

## Repository Summary

AI DevSec Gateway is an open-source privacy and DevSecOps tool for developers adopting AI coding assistants. It provides local controls to block known AI endpoints, inspect active AI editor processes, and route compatible API clients toward local or private inference servers.

The project focuses on a practical security problem: AI coding tools often run with broad access to source code, terminal context, repository metadata, and editor state. AI DevSec Gateway gives developers and teams an auditable, local-first way to reduce accidental data exposure.

## Why It Fits OSS Support

- It is MIT licensed and public.
- It targets a growing ecosystem risk around AI-assisted development.
- It has multi-OS CI for Windows, Linux, and macOS.
- It supports Python 3.10 through 3.13 in CI.
- It uses tests, coverage enforcement, Ruff, mypy, CodeQL, Dependabot, issue templates, a pull request template, and a security policy.
- It has package metadata and distribution paths for PyPI, Homebrew, Scoop, and portable binaries.
- It documents current capabilities separately from future TLS/DPI, eBPF, and Windows Filtering Platform work.

## How Codex Would Be Used

Codex would support maintenance work that directly benefits users and contributors:

- Review pull requests for security regressions, unsafe subprocess usage, and cross-platform behavior.
- Generate regression tests for privileged network operations, CLI behavior, config persistence, and release packaging.
- Triage issues by reproducing failures, identifying platform-specific behavior, and drafting focused fixes.
- Improve documentation so implemented behavior, experimental features, and roadmap items remain clearly separated.
- Assist release preparation by checking changelogs, packaging metadata, workflows, and smoke-test commands.

## Current Scope Boundaries

- The default enforcement backend is hosts-file blocking.
- The local API gateway currently handles loopback HTTP routing for compatible clients.
- The firewall backend is experimental and should be inspected with `--dry-run` before use.
- TLS/DPI interception, root CA installation, eBPF, and Windows Filtering Platform support are roadmap items, not current runtime behavior.

## Suggested Application Text

AI DevSec Gateway is an open-source privacy and security tool for developers adopting AI coding assistants. It gives teams local controls to block known AI endpoints, audit active AI editor processes, and route compatible API clients to local or private LLM infrastructure. The project is actively maintained with multi-OS CI, tests, linting, type checks, CodeQL, packaging metadata, a security policy, and a roadmap toward safer AI development workflows.

Codex would help maintain quality in a security-sensitive OSS tool where cross-platform behavior, safe defaults, and clear documentation matter. We would use Codex for PR review, issue triage, regression tests, release checks, and security hardening of network enforcement code paths.
