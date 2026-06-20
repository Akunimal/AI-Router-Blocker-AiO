# Contributing to AI DevSec Gateway

First off, **thank you** for considering a contribution! Every bug report, feature request, translation fix, and code improvement makes this project better for every developer who uses it.

This document explains the process for contributing to the project and the standards we follow.

---

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
  - [Reporting Bugs](#-reporting-bugs)
  - [Suggesting Features](#-suggesting-features)
  - [Adding Domains to the Blocklist](#-adding-domains-to-the-blocklist)
  - [Translating the Interface](#-translating-the-interface)
  - [Submitting Code Changes](#-submitting-code-changes)
- [Development Setup](#-development-setup)
- [Coding Standards](#-coding-standards)
- [Commit Convention](#-commit-convention)
- [Pull Request Process](#-pull-request-process)

---

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior by opening a private security advisory.

---

## How Can I Contribute?

### 🐛 Reporting Bugs

If you found a bug, please [open a Bug Report issue](https://github.com/Akunimal/AI-Router-Blocker-AiO/issues/new?template=bug_report.yml). Before doing so:

1. **Search existing issues** to make sure it hasn't already been reported.
2. **Use the latest version** — the bug may already be fixed.
3. **Fill out the template completely** — this helps us reproduce and fix it faster.

### 💡 Suggesting Features

Have an idea? [Open a Feature Request issue](https://github.com/Akunimal/AI-Router-Blocker-AiO/issues/new?template=feature_request.yml). We especially welcome ideas for:

- New AI providers or domains to block
- Security auditing improvements
- UI/UX improvements
- New language translations

### 🌐 Adding Domains to the Blocklist

One of the easiest ways to contribute is adding new AI service domains:

1. Edit the `BLOCKLIST` dictionary in `ai_blocker.py`
2. Add domains to an existing category, or create a new one
3. Update the domain count in `README.md` and `README.es.md`
4. Add a test case in `tests/test_blocklist.py`
5. Submit a PR

### 🗣️ Translating the Interface

We support 10 languages and always welcome improvements:

1. Edit `translations.json`
2. Find your language code (e.g., `"es"` for Spanish, `"fr"` for French)
3. Translate missing strings or improve existing translations
4. Test by running the app with your language set
5. Submit a PR with the label `i18n`

### 🔧 Submitting Code Changes

For any code changes, please follow the [Pull Request Process](#-pull-request-process) below.

---

## 🛠️ Development Setup

### Prerequisites

- **Python 3.10+** installed and available in your PATH
- **Git** for version control
- **(Optional)** A virtual environment manager (`venv`, `conda`)

### Getting Started

```bash
# 1. Fork and clone the repository
git clone https://github.com/<your-username>/AI-Router-Blocker-AiO.git
cd AI-Router-Blocker-AiO

# 2. Create a virtual environment
python -m venv .venv

# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

# 3. Install development dependencies
pip install -e ".[dev]"

# 4. Run the tests to make sure everything works
python -m pytest tests/ -v

# 5. Run the linter
python -m ruff check .
```

### Running the Application

```bash
# On Windows (auto-elevates via UAC):
python ai_blocker.py

# On Linux/macOS (requires sudo):
sudo python3 ai_blocker.py
```

> **Note:** The application requires Administrator/root privileges to modify the hosts file. For development, you can test most features without elevation — the app will show an error dialog if it can't write to the hosts file.

---

## 🤖 AI-Assisted Development Standard

AI DevSec Gateway is a security tool built *for* the AI era, and we believe in using AI safely to build it. We actively encourage contributors to use AI coding assistants, provided they adhere to our zero-trust principles:

1. **AI-Generated Fuzzing:** We highly encourage using AI (e.g., Claude, ChatGPT, GitHub Copilot) to generate robust edge-case regression tests and fuzzing suites for your PRs, especially when modifying network interception or firewall logic.
2. **Self-Review:** Use AI to review your own pull requests for unsafe subprocess usage or cross-platform vulnerabilities before submitting.
3. **No Blind Commits:** AI-generated code must be fully understood by the contributor. You are responsible for the security implications of the code you submit.
4. **Dogfooding:** If you are running local autonomous agents to help write code for this repository, ensure your traffic is being routed and audited through the Gateway to prevent accidental leaks.

---

## 📐 Coding Standards

- **Language**: Python 3.10+ compatible
- **Linter**: [Ruff](https://docs.astral.sh/ruff/) — run `ruff check .` before committing
- **Comments**: Bilingual comments (English and Spanish) are a project convention. New code should include both where practical
- **Docstrings**: Every function must have a docstring in both English and Spanish
- **Type hints**: Encouraged for new code; not required for existing code modifications
- **Line length**: 120 characters maximum
- **Imports**: Standard library → third-party → local, separated by blank lines

---

## 📝 Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/). Every commit message must follow this format:

```
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting, missing semicolons, etc. (no code change) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `test` | Adding or updating tests |
| `ci` | Changes to CI configuration files and scripts |
| `chore` | Maintenance tasks (dependencies, build scripts) |
| `security` | Security-related changes |
| `i18n` | Internationalization/translation updates |

### Examples

```
feat(blocklist): add Cohere AI domains
fix(hosts): prevent duplicate entries when re-blocking
docs(readme): update domain count table
test(config): add tests for custom domain persistence
ci(actions): add CodeQL security scanning
i18n(translations): improve Japanese translation accuracy
```

---

## 🔀 Pull Request Process

### Branch Naming

Create a branch from `main` using this convention:

```
<type>/<short-description>
```

Examples: `feat/add-cohere-domains`, `fix/hosts-duplicate-entries`, `docs/update-readme`

### Before Submitting

1. ✅ Run the full test suite: `python -m pytest tests/ -v`
2. ✅ Run the linter: `ruff check .`
3. ✅ Ensure no binary files (`.exe`, `.dll`) are included
4. ✅ Update documentation if your change affects user-facing behavior
5. ✅ Add tests for new functionality
6. ✅ Rebase your branch on the latest `main`

### PR Guidelines

- **One PR, one concern**: Keep PRs focused on a single change
- **Fill out the PR template**: It exists for a reason
- **Link related issues**: Use `Closes #123` or `Fixes #123`
- **Be responsive**: Address review feedback promptly
- **Be patient**: Maintainers review PRs as time permits

### Review Process

1. A maintainer will review your PR within **72 hours**
2. You may be asked to make changes — this is normal and expected
3. Once approved, a maintainer will merge your PR
4. Your contribution will be credited in the next release's CHANGELOG

---

## 🙏 Recognition

All contributors are recognized in our release notes. Significant contributions are highlighted in the CHANGELOG. We believe every contribution matters, no matter how small.

---

Thank you for making AI DevSec Gateway better! 🛡️
