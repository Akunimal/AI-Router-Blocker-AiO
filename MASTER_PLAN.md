# Master Plan ? AI DevSec Gateway v1.5 ? v2.0

> Plan integral de mejoras, organizado en oleadas (waves) con commits at?micos y pushes individuales.
> Cada wave termina con `git commit` + `git push` contra `main`.
> Fecha de inicio: 2026-07-16 | Versi?n objetivo: **1.5.0**

---

## Wave 0 ? Preparaci?n y baseline

Antes de tocar c?digo, aseguramos un punto de partida limpio.

| # | Tarea | Archivos | Commit msg |
|---|---|---|---|
| 0.1 | Verificar working tree limpio y main actualizada con origin/main | ? | ? |
| 0.2 | Limpiar `.tmp.driveupload/` y caches (`.mypy_cache`, `.pytest_cache`, `.ruff_cache`) | ? | `chore: cleanup temp and cache dirs before starting v1.5` |
| 0.3 | Ejecutar test suite completa y registrar baseline de cobertura (60.77%) | ? | ? |

**Push**: s? (commit 0.2)

---

## Wave 1 ? Bugfixes de code quality (commit + push individual)

Corregir los defectos concretos detectados en el an?lisis, sin cambiar comportamiento.

| # | Tarea | Archivos | Commit msg |
|---|---|---|---|
| 1.1 | Fix mypy gateway.py:17 ? tipado incorrecto de generate_leaf_cert | ai_blocker/gateway.py | `fix: correct mypy type for generate_leaf_cert in gateway (Callable|None)` |
| 1.2 | Fix mypy gateway.py:51 ? reemplazar truthy check por is not None | ai_blocker/gateway.py | `fix: replace truthy check on get_or_generate_leaf_cert with explicit is not None` |
| 1.3 | Fix ResourceWarning en test_config.py ? cerrar sqlite connections en mock | tests/test_config.py | `fix: close sqlite connections in test_config mock to suppress ResourceWarning` |
| 1.4 | Agregar logging.warning cuando tls_manager no puede importarse | ai_blocker/__init__.py | `fix: warn when tls_manager import fails instead of silent fallback` |
| 1.5 | Marcar kernel_backends.py stubs como experimental con raise NotImplementedError | ai_blocker/kernel_backends.py | `fix: raise NotImplementedError in WFP/EBPF stubs with clear message` |

**Push**: despu?s de cada commit (5 pushes)

---

## Wave 2 ? Cobertura de tests: m?dulos cr?ticos (1 tema por commit)

Cada commit agrega tests para un m?dulo espec?fico, >70% en cada uno.

| # | M?dulo | Cobertura actual | Cobertura target | Archivos | Commit msg |
|---|---|---|---|---|---|
| 2.1 | tls_manager.py | 4% | >75% | tests/test_tls_manager.py | `test: comprehensive TLS manager tests (root CA, leaf certs, trust store)` |
| 2.2 | gateway.py - CoreHandler (CONNECT, GET, POST) | 27% | >50% | tests/test_gateway.py | `test: GatewayHandler HTTP proxy tests (CONNECT, GET, POST)` |
| 2.3 | gateway.py - rate limiting, token checks, audit | 27% | >65% | tests/test_gateway.py | `test: gateway rate limiting, token monitor and audit log tests` |
| 2.4 | gateway.py - DPI/guardrail integration | 27% | >75% | tests/test_gateway.py | `test: gateway DPI rule enforcement and guardrail block response tests` |
| 2.5 | system_utils.py | 41% | >80% | tests/test_system_utils.py | `test: system_utils edge cases (flush_dns, hosts status, is_admin)` |
| 2.6 | config.py | 36% | >80% | tests/test_config.py | `test: config edge cases, autostart, sensitive key filtering` |
| 2.7 | block_actions.py | 65% | >85% | tests/test_blocklist.py | `test: block_actions edge cases (force_close, detect_editors)` |
| 2.8 | kernel_backends.py | 0% | >80% | tests/test_kernel_backends.py | `test: kernel_backend stubs tests (dry-run planning, status)` |

**Push**: despu?s de cada commit (8 pushes)
**Checkpoint**: `coverage run --fail-under=70` debe pasar al final.

---

## Wave 3 ? Integraci?n de Phase 3: DLP pipeline en gateway

Conectar los m?dulos existentes (dlp_engine.py, guardrails.py, token_monitor.py, dpi_rules.py) al flujo real del proxy HTTP.

| # | Tarea | Archivos | Commit msg |
|---|---|---|---|
| 3.1 | Integrar DLPEngine en GatewayHandler.do_POST/do_PUT | ai_blocker/gateway.py, ai_blocker/dlp_engine.py | `feat: integrate DLPEngine into gateway proxy for real-time body redaction` |
| 3.2 | Integrar PromptGuardrail en proxy | ai_blocker/gateway.py, ai_blocker/guardrails.py | `feat: integrate PromptGuardrail into gateway to classify and reject threats` |
| 3.3 | Conectar TokenMonitor al gateway | ai_blocker/gateway.py, ai_blocker/token_monitor.py | `feat: wire TokenMonitor into gateway to track per-request token usage` |
| 3.4 | Flags --dlp / --guardrails al CLI + config toggle | ai_blocker/config.py, ai_blocker/__main__.py | `feat: add --dlp and --guardrails CLI flags with config persistence` |
| 3.5 | Toggles DLP/Guardrails en UI + log panel | ai_blocker/ui.py | `feat: add DLP and guardrail toggles to GUI with live finding display` |
| 3.6 | Tests de integraci?n gateway+DLP+guardrails+token | tests/test_gateway.py | `test: integration tests for DLP+guardrails+token chain in gateway` |

**Push**: despu?s de cada commit (6 pushes)

---

## Wave 4 ? Token Traffic Monitor Dashboard

| # | Tarea | Archivos | Commit msg |
|---|---|---|---|
| 4.1 | Endpoint /stats en gateway con JSON de TokenMonitor | ai_blocker/gateway.py | `feat: expose /stats endpoint in gateway for live token metrics` |
| 4.2 | Dashboard en UI: panel token in/out, l?mites, gasto | ai_blocker/ui.py | `feat: add token usage dashboard panel to GUI with real-time stats` |
| 4.3 | Tests para dashboard y /stats endpoint | tests/test_token_monitor.py | `test: token dashboard data flow and /stats endpoint tests` |

**Push**: despu?s de cada commit (3 pushes)

---

## Wave 5 ? Mejoras de UX e infraestructura

| # | Tarea | Archivos | Commit msg |
|---|---|---|---|
| 5.1 | Dry-run mode visual en GUI | ai_blocker/ui.py | `feat: add dry-run mode toggle to GUI with visual plan preview` |
| 5.2 | Limpiar build artifacts obsoletos | ? | `chore: remove stale coverage.xml and unreferenced build artifacts` |
| 5.3 | Bump version a 1.5.0 | pyproject.toml, ai_blocker/__init__.py | `chore: bump version to 1.5.0` |
| 5.4 | Actualizar CHANGELOG.md | CHANGELOG.md | `docs: update changelog for v1.5.0` |

**Push**: despu?s de cada commit (4 pushes)

---

## Wave 6 ? Verificaci?n final

| # | Tarea | Commit msg |
|---|---|---|
| 6.1 | ruff check . ? 0 errores | `chore: post-v1.5 ruff lint pass` |
| 6.2 | mypy ai_blocker ? 0 errores | `chore: post-v1.5 mypy type check pass` |
| 6.3 | Test suite + coverage >70% general, >80% target | `chore: post-v1.5 full test suite and coverage verification` |
| 6.4 | Push final y tag v1.5.0 | ? |

**Push**: push de 6.1/6.2/6.3 (squash), luego tag + push tags

---

## Resumen de commits

| Wave | Commits | Descripci?n |
|---|---|---|
| Wave 0 | 1 | Cleanup preparatorio |
| Wave 1 | 5 | Bugfixes de code quality |
| Wave 2 | 8 | Cobertura de tests (~30 nuevos) |
| Wave 3 | 6 | Integraci?n Phase 3 (DLP + Guardrails + TokenMonitor en gateway) |
| Wave 4 | 3 | Dashboard de tokens en UI |
| Wave 5 | 4 | UX, cleanup, release prep |
| Wave 6 | 4 | Verificaci?n final + tag |
| **Total** | **31** | **31 commits + 31 pushes** |

---

## C?mo ejecutar

Cada commit se hace con:

```
git add <files>
git commit -m "<msg>"
git push origin main
```

Cada wave tiene un checkpoint de verificaci?n antes de avanzar.
El plan se ejecuta secuencialmente, wave por wave.

---

## Tracking

| Wave | Status | Commits | Push |
|---|---|---|---|
| Wave 0 | Pendiente | 0/1 | 0/1 |
| Wave 1 | Pendiente | 0/5 | 0/5 |
| Wave 2 | Pendiente | 0/8 | 0/8 |
| Wave 3 | Pendiente | 0/6 | 0/6 |
| Wave 4 | Pendiente | 0/3 | 0/3 |
| Wave 5 | Pendiente | 0/4 | 0/4 |
| Wave 6 | Pendiente | 0/4 | 0/4 |
