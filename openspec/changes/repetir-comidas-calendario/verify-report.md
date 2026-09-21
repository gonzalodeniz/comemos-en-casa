```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:57d5fcb8b0f8dd74c0f8124e4551e4e28614fc5bc1e11ce8e82a1dadcab875c5
verdict: fail
blockers: 9
critical_findings: 9
requirements: 0/13
scenarios: 0/28
test_command: make test
test_exit_code: 0
test_output_hash: sha256:e7213b2c5904c0d5a30005681981b9765bfe0fb9d68a3726d7fb3048926ea850
build_command: npm --prefix frontend run build
build_exit_code: 0
build_output_hash: sha256:bd4629f6327265245b7c5190a2d8cf1fadf49f2fea80d60463047dab1fa259e1
```

# Verification: repetir-comidas-calendario — slice 1

## Status

**Overall change verdict: FAIL / not archive-ready.** The required task-checkbox policy makes the nine remaining implementation tasks critical completeness blockers. This is expected for the approved first chained slice and does **not** indicate a defect in its implemented boundary.

**Slice 1 verdict: PASS.** Commits `da21d9c` and `32da760` implement only persistence/domain foundations and their focused tests. The next apply slice is safe to begin at Task 4 (backend repository/API RED), provided it remains within the approved stacked boundary. Native SDD status remains authoritative: `ready`, `nextRecommended: apply`; verification does not alter that recommendation.

## Structured status and action context

- Change: `repetir-comidas-calendario`; artifact store: `openspec`.
- Native state: `ready`; `nextRecommended: apply`; no native blockers.
- Action context: `repo-local`; workspace root `/opt/apps/comemos-en-casa`; allowed edit root `/opt/apps/comemos-en-casa`.
- All inspected implementation ownership is inside the authoritative workspace and user-provided allowed surfaces.

## Slice scope and migration allowlist

The two-commit range `da21d9c^..32da760` changes only:

- migration `0007` and its README documentation;
- meal-calendar schemas and pure date expansion service;
- recurrence/time tests and the migration-foundation allowlist test;
- OpenSpec task/progress artifacts.

No repository implementation, HTTP/API handler, frontend file, occurrence materialization, recipe linkage, or unrelated product area was changed. The correction in `32da760` adds `0007_meal_calendar_recurrence.sql` to `test_historical_sql_migrations_are_not_rewritten_as_alembic_revisions`; it is compatible with the migration allowlist and passed in the focused and full suites.

`0007_meal_calendar_recurrence.sql` is additive: it defines exactly `meal_recurrence_rules`, a shared-calendar FK, allowed slots, trimmed one-to-100-character free text, recurrence intervals 1–4, and the `(calendar_key, initial_date)` index. It does not define generated-occurrence storage or recipe linkage.

## Spec coverage

The specification contains **13 requirements and 28 scenarios**. No requirement is fully complete at the whole-change level because repository/API/frontend work is deliberately deferred; envelope coverage is therefore **0/13 requirements and 0/28 scenarios**.

Slice evidence covers the persistence/domain portions of Tasks 1–3: migration shape and constraints, free-text-only domain validation, interval validation, and inclusive civil-date expansion. The remaining specifications depend on the unimplemented repository/API/frontend tasks, especially combined weekly reads, stable response identity, series CRUD, idempotency, conversion, confirmations, ordering, and UI flows.

## Task completion and exact blockers

Tasks 1–3 are checked complete. The following unchecked implementation tasks are critical completeness and archive blockers under the SDD checkbox policy:

- [ ] Extender primero las pruebas de `backend/tests/meal_calendar/test_calendar_repository.py` y `backend/tests/meal_calendar/test_api_contract.py` para exigir listado de reglas candidatas compartidas, expansión combinada, orden por fecha/franja/texto/identidad, identidad estable `(seriesId, occurrenceDate)`, creación idempotente, conflicto `409`, conversión ordinaria atómica, `PATCH /series/{series_id}`, `DELETE /series/{series_id}?confirmed=true` y rechazos no mutantes. Incluir coexistencia de varias series/ordinarias en la misma celda, slot inmutable, `No repetir` destructivo confirmado y compatibilidad con receta heredada. Ejecutar ambos archivos y registrar los fallos esperados. <!-- sdd-owner: implementation -->
- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/repository.py` con `find_rule_by_id`, inserción idempotente, actualización, borrado y listado de candidatas `calendar_key = "shared"`; modificar `list_week` para combinar asignaciones existentes (incluido `LEFT JOIN recipes`) con ocurrencias virtuales, derivar el identificador estable y aplicar un único orden determinista. Verificar con `backend/tests/meal_calendar/test_calendar_repository.py` y los tests de compatibilidad de `backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/api.py` para aceptar `recurrenceWeeks: 0|1|2|3|4` con ausencia equivalente a `0`, devolver `entryType` discriminado y añadir `PATCH /series/{series_id}` y `DELETE /series/{series_id}?confirmed=true`; ejecutar creación/actualización/borrado y conversión de asignación libre dentro de transacciones, con UUID reutilizable, conflicto de idempotencia, `422` para receta/intervalo/fecha/franja/texto inválidos, confirmación obligatoria de reanclaje y borrado confirmado idempotente. No ofrecer rutas por `occurrenceDate`. Verificar con `pytest backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar y ajustar únicamente las pruebas backend necesarias en `backend/tests/meal_calendar/test_time_text.py`, `test_calendar_repository.py`, `test_api_contract.py` y `test_recurrence_migration.py` para triangular errores de límites de semana, retries, fallos simulados de inserción, reanclaje no confirmado, borrado repetido, coexistencia, calendario compartido y recetas históricas; verificar con `pytest` y después `make test-backend`. <!-- sdd-owner: implementation -->
- [ ] Ampliar `frontend/src/App.test.tsx` con pruebas fallidas para la unión `entryType`, frecuencias `0..4`, payload con UUID estable de creación, conversión mediante `assignmentId`, apertura de ocurrencia con `initialDate`, franja deshabilitada, confirmación de reanclaje, confirmación destructiva de `No repetir`, `deleteSeries` en vez de `deleteAssignment`, refetch posterior, coexistencia y receta heredada sin controles recurrentes. Añadir casos de reducer solo si la cobertura de la interfaz no permite observar el estado; ejecutar `cd frontend && npm test`. <!-- sdd-owner: implementation -->
- [ ] Implementar en `frontend/src/types.ts` `RecurrenceWeeks`, la unión `CalendarAssignment`/`RecurringCalendarOccurrence` y payloads de serie; en `frontend/src/api.ts` conservar contratos ordinarios y añadir `updateSeries`/`deleteSeries(seriesId, confirmed)`; en `frontend/src/calendarReducer.ts` modelar editor discriminado, `seriesId`, `occurrenceDate`, `initialDate`, intervalo, UUID retenido desde apertura y refresco posterior a mutación. Verificar con los tests RED y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Modificar `frontend/src/App.tsx` y los estilos mínimos de `frontend/src/styles.css` para altas de texto libre con selector `No repetir`/`Cada semana`/`Cada 2–4 semanas`, conversión explícita de asignación, edición de serie sobre `initialDate`, slot visible deshabilitado, advertencia confirmada de reanclaje, borrado confirmado de serie y etiqueta accesible de frecuencia; mantener las tarjetas de receta heredadas legibles y sin controles recurrentes. Verificar con `cd frontend && npm test` y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar la suite de `frontend/src/App.test.tsx` junto con `cd frontend && npm run build`, y ajustar casos deterministas para relectura de semana tras crear, convertir, editar o borrar, identidad estable en reintento, series en una misma celda, confirmaciones canceladas y presentación de recetas disponibles/no disponibles. No modificar el layout semanal fuera de los estilos estrictamente necesarios. <!-- sdd-owner: implementation -->
- [ ] Revisar los archivos modificados del backend y frontend para eliminar duplicación entre asignaciones y ocurrencias, mantener nombres `camelCase`/`PascalCase` y PEP 8, conservar consultas parametrizadas, mensajes de confirmación específicos y documentación de rollback; ejecutar `make test`, `cd frontend && npm run typecheck` y `cd frontend && npm run build`, y documentar la evidencia antes de solicitar revisión. <!-- sdd-owner: implementation -->

## Commands and results

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py backend/tests/test_alembic_foundation.py` | PASS — `20 passed in 0.46s`; output SHA-256 `1486e7c36f400bea3b7391d78be22c4a0b3367bfbf5f045b0fa70e488b65fe0a`. |
| `make test` | PASS — `108 passed, 2 warnings in 3.60s`; it also ran frontend typecheck and production build. Output SHA-256 `e7213b2c5904c0d5a30005681981b9765bfe0fb9d68a3726d7fb3048926ea850`. The warnings are third-party Starlette/httpx deprecations. |
| `npm --prefix frontend run build` | PASS — TypeScript check and Vite production build completed. Output SHA-256 `bd4629f6327265245b7c5190a2d8cf1fadf49f2fea80d60463047dab1fa259e1`. |

Coverage analysis was skipped because the configured verification capabilities provide no coverage command. No standalone linter is configured. The configured typecheck passed as part of `make test` and the explicit build command.

## Strict TDD compliance

Strict TDD is active in `openspec/config.yaml`. `apply-progress.md` contains the required `TDD Cycle Evidence` table for Tasks 1–3. Its referenced tests exist and the current focused execution is GREEN.

| Check | Result | Details |
|---|---|---|
| TDD evidence reported | PASS | Table present for all three completed tasks. |
| Test files exist | PASS | `test_recurrence_migration.py` and `test_time_text.py` exist. |
| GREEN confirmed | PASS | Current focused run passed all 20 selected recurrence/time/allowlist tests. |
| Triangulation | PASS | Tests cover validation failures, intervals 1–4, both week boundaries, empty adjacent week, future anchor, month/year crossing, migration checks, index, FK, coexistence, and no occurrence table. |
| Safety net | PASS | Apply-progress records the pre-change 15-test safety run; this historical command result is recorded rather than independently reproducible after the change. |

TDD compliance: **5/5 checks passed** for the completed slice.

### Test layer distribution

| Layer | Tests | Files | Tools |
|---|---:|---:|---|
| Unit | 19 | 3 | pytest |
| Integration | 1 | 1 | pytest + PostgreSQL via Docker Compose |
| E2E | 0 | 0 | Not configured |
| **Total** | **20** | **3** | |

### Assertion quality

`test_recurrence_migration.py`, `test_time_text.py`, and `test_alembic_foundation.py` were inspected. Assertions exercise migration SQL, a live isolated PostgreSQL transaction, domain constructors, or the pure expansion function. No tautologies, ghost loops, type-only-only checks, smoke-only tests, or CSS/implementation-detail assertions were found.

**Assertion quality: 0 CRITICAL, 0 WARNING.**

## Review workload and PR boundary

The two commits have `483` added and `5` removed lines across code, tests, docs, and OpenSpec artifacts (`488` changed lines). The implementation/test/migration-documentation portion is `389` added and `2` removed lines (`391` changed lines). No scope crept into repository/API/frontend work, so the committed boundary matches slice 1 of the stacked-to-main plan.

The current-session preflight records user acceptance of the size exception. `tasks.md` still says `Chain strategy: pending`, while `apply-progress.md` says `stacked-to-main` and says no exception was used. Treat the session preflight as current authority; reconcile those stale historical planning statements in the next progress record, without changing this slice.

## Risks and next apply safety

- **Critical archive blockers:** the nine unchecked tasks above leave all end-to-end recurrence requirements incomplete. This report is not a clean whole-change pass and is not archive-ready.
- **Safe next slice:** yes. Begin only Task 4 RED tests for repository/API behavior, then proceed through its approved backend slice. Do not implement frontend work or widen into recipe flows.
- **Residual implementation risk:** the current migration/domain code has no repository or API wiring yet, so it cannot itself persist/read/serve rules in the product; this is intentional for the chain boundary.
- **Migration risk:** allowlist compatibility is verified; deployment still requires PostgreSQL migrations in lexical order through `0007`.

## Slice 2 RED update — Task 4

Task 4 RED was applied as the start of the stacked-to-main backend repository/API slice. Only the two allowed test files were extended; no production code was changed. The persisted Task 4 checkbox is now checked in `tasks.md`.

Focused command:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_calendar_repository.py backend/tests/meal_calendar/test_api_contract.py
```

Expected RED evidence: `10 failed, 5 passed, 2 warnings`. The failures expose the absent recurrence repository methods, combined weekly expansion, series HTTP routes, recurrence write fields, and the newly required ordinary `entryType`; collection completed without syntax errors. Production implementation remains intentionally deferred to Tasks 5–6.
